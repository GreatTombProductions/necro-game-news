#!/usr/bin/env python3
"""
Recovery script to find and add missing candidates from batch discovery.

This script identifies games that:
1. Were processed (in processed_appids.txt)
2. Have necromancy-related keywords in their name
3. Are NOT in the candidates or games tables

It then re-evaluates these games and adds qualifying ones to the candidates table.

Usage:
    python scripts/recover_missing_candidates.py --scan      # Find missing candidates
    python scripts/recover_missing_candidates.py --recover   # Add missing candidates
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.schema import get_connection
from backend.scrapers.steam_api import SteamAPI
from scripts.discover_games import calculate_necromancy_score

# Necromancy-related keywords to look for in game names
NECRO_KEYWORDS = [
    'necromancer', 'necromancy', 'necromantic',
    'undead', 'zombie', 'skeleton', 'lich', 'bone',
    'corpse', 'graveyard', 'crypt', 'tomb',
]


def load_data():
    """Load all required data files."""
    # Load Steam app list
    with open('data/discovery_cache/steam_applist.json') as f:
        apps = json.load(f)
    apps_dict = {a['appid']: a['name'] for a in apps}

    # Load processed IDs
    with open('data/discovery_cache/processed_appids.txt') as f:
        processed_ids = [int(line.strip()) for line in f if line.strip()]

    # Get IDs already in database
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT steam_id FROM games WHERE steam_id IS NOT NULL")
    games_ids = {row[0] for row in cursor.fetchall()}

    cursor.execute("SELECT steam_id FROM candidates WHERE steam_id IS NOT NULL")
    candidates_ids = {row[0] for row in cursor.fetchall()}

    conn.close()

    return apps_dict, processed_ids, games_ids, candidates_ids


def find_missing_candidates():
    """Find processed games with necro keywords that aren't in the database."""
    apps_dict, processed_ids, games_ids, candidates_ids = load_data()

    existing_ids = games_ids | candidates_ids

    missing = []
    for appid in processed_ids:
        name = apps_dict.get(appid, '').lower()

        # Check if it has necro keywords
        has_keyword = any(kw in name for kw in NECRO_KEYWORDS)

        # Check if it's not in the database
        not_in_db = appid not in existing_ids

        if has_keyword and not_in_db:
            missing.append({
                'appid': appid,
                'name': apps_dict.get(appid, 'Unknown')
            })

    return missing


def scan_missing():
    """Scan and report missing candidates."""
    print("\n" + "="*80)
    print("SCANNING FOR MISSING CANDIDATES")
    print("="*80)

    missing = find_missing_candidates()

    print(f"\nFound {len(missing)} processed games with necro keywords not in database:")
    print("-" * 80)

    for game in missing[:50]:  # Show first 50
        print(f"  {game['appid']}: {game['name']}")

    if len(missing) > 50:
        print(f"  ... and {len(missing) - 50} more")

    print("-" * 80)
    print(f"\nTo recover these candidates, run:")
    print(f"  python scripts/recover_missing_candidates.py --recover")
    print("="*80 + "\n")

    return missing


def recover_candidates(limit=None, min_score=5, rate_limit_delay=3.0):
    """Re-evaluate and add missing candidates to database."""
    print("\n" + "="*80)
    print("RECOVERING MISSING CANDIDATES")
    print("="*80)

    missing = find_missing_candidates()

    if limit:
        missing = missing[:limit]
        print(f"\nLimited to {limit} games for testing")

    print(f"\nRe-evaluating {len(missing)} games...")
    print(f"Minimum score threshold: {min_score}")
    print(f"Rate limit delay: {rate_limit_delay}s between requests")
    print("-" * 80)

    steam_api = SteamAPI(rate_limit_delay=rate_limit_delay)
    conn = get_connection()
    cursor = conn.cursor()

    stats = {
        'evaluated': 0,
        'qualified': 0,
        'added': 0,
        'errors': 0,
        'rate_limited': 0,
        'skipped_not_game': 0,
    }

    import time
    consecutive_rate_limits = 0

    for i, game in enumerate(missing, 1):
        appid = game['appid']
        name = game['name']

        if i % 10 == 0:
            print(f"Progress: {i}/{len(missing)} | Qualified: {stats['qualified']} | Rate limited: {stats['rate_limited']} | Errors: {stats['errors']}")

        try:
            # Fetch current details with retry on rate limit
            details = None
            for attempt in range(3):
                details = steam_api.get_app_details(appid)
                if details is not None:
                    consecutive_rate_limits = 0
                    break
                # Check if it was a rate limit (API returns None but we can infer from pattern)
                consecutive_rate_limits += 1
                if consecutive_rate_limits >= 3:
                    # Likely rate limited, back off
                    backoff = min(60, 10 * consecutive_rate_limits)
                    print(f"  Rate limit detected, backing off for {backoff}s...")
                    stats['rate_limited'] += 1
                    time.sleep(backoff)
                    consecutive_rate_limits = 0
                elif attempt < 2:
                    time.sleep(5)  # Brief pause before retry

            if not details:
                stats['errors'] += 1
                continue

            # Skip non-games
            if details.get('type') != 'game':
                stats['skipped_not_game'] += 1
                continue

            # Parse and score
            parsed = steam_api.parse_app_details(details, fetch_tags=False)
            score, matches = calculate_necromancy_score(parsed)

            stats['evaluated'] += 1

            if score >= min_score:
                stats['qualified'] += 1

                # Check if already exists
                cursor.execute("SELECT id FROM candidates WHERE steam_id = ?", (appid,))
                if cursor.fetchone():
                    continue

                # Create justification
                justification = f"Recovery - Score: {score}\n"
                justification += f"Matches: {', '.join(matches[:5])}\n\n"
                justification += f"Description: {parsed['short_description']}\n\n"
                justification += f"Genres: {', '.join(parsed['genres'] or [])}\n"
                if parsed['price_usd'] is not None:
                    justification += f"Price: ${parsed['price_usd']:.2f}" if parsed['price_usd'] > 0 else "Price: Free"

                # Insert
                cursor.execute("""
                    INSERT INTO candidates (
                        steam_id, game_name, source, justification,
                        status, date_submitted
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    appid,
                    parsed['name'],
                    'auto_discovery',
                    justification,
                    'pending',
                    datetime.now()
                ))

                stats['added'] += 1
                print(f"  ✓ ADDED ({score}): {parsed['name']}")

        except Exception as e:
            print(f"  Error processing {appid}: {e}")
            stats['errors'] += 1

    conn.commit()
    conn.close()

    print("-" * 80)
    print(f"\nRECOVERY COMPLETE")
    print(f"  Evaluated: {stats['evaluated']}")
    print(f"  Qualified (score >= {min_score}): {stats['qualified']}")
    print(f"  Added to database: {stats['added']}")
    print(f"  Skipped (not games): {stats['skipped_not_game']}")
    print(f"  Errors: {stats['errors']}")
    print("="*80 + "\n")

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Recover missing candidates from batch discovery"
    )

    parser.add_argument('--scan', action='store_true',
                       help="Scan for missing candidates")
    parser.add_argument('--recover', action='store_true',
                       help="Recover and add missing candidates")
    parser.add_argument('--limit', type=int,
                       help="Limit number of games to process")
    parser.add_argument('--min-score', type=int, default=5,
                       help="Minimum score threshold (default: 5)")

    args = parser.parse_args()

    if args.scan:
        scan_missing()
    elif args.recover:
        recover_candidates(limit=args.limit, min_score=args.min_score)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
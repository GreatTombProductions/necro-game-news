#!/usr/bin/env python3
"""
Comprehensive batch game discovery for Necro Game News.

Downloads ALL Steam app IDs (~200k), evaluates them for necromancy content,
and saves high-scoring candidates. Tracks processed IDs for incremental updates.

Usage:
    python scripts/batch_discover.py --download        # Download app list
    python scripts/batch_discover.py --discover        # Run discovery
    python scripts/batch_discover.py --continue        # Continue interrupted run
    python scripts/batch_discover.py --stats          # Show progress stats

Process:
    1. Download full Steam app list (~200k apps)
    2. Filter out already-tracked and already-processed apps
    3. Batch evaluate with rate limiting
    4. Save high-scoring candidates to database
    5. Track processed IDs for future incremental runs
"""

import sys
import os
import json
import logging
import argparse
import requests
import time
from datetime import datetime
from pathlib import Path
from typing import Set

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.schema import get_connection
from backend.scrapers.steam_api import SteamAPI, RateLimitError
from scripts.discover_games import calculate_necromancy_score

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/batch_discovery.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# File paths
CACHE_DIR = Path('data/discovery_cache')
APPLIST_FILE = CACHE_DIR / 'steam_applist.json'
PROCESSED_IDS_FILE = CACHE_DIR / 'processed_appids.txt'
CANDIDATES_CACHE_FILE = CACHE_DIR / 'candidates_batch.json'

# Ensure cache directory exists
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def download_steam_applist() -> list[dict]:
    """
    Download the complete list of Steam apps.

    Uses Steam's IStoreService API with pagination to get ALL apps.

    Returns:
        List of dicts with {'appid': int, 'name': str}
    """
    logger.info("Downloading complete Steam app list...")

    # Get Steam API key from environment
    from dotenv import load_dotenv
    load_dotenv()
    steam_api_key = os.getenv('STEAM_API_KEY')

    if not steam_api_key:
        logger.error("STEAM_API_KEY not found in environment")
        logger.error("Please add STEAM_API_KEY to your .env file")
        return []

    # Method 1: Try IStoreService endpoint with pagination (BEST - complete list)
    logger.info("Trying Steam IStoreService API with pagination...")
    try:
        all_apps = []
        last_appid = 0
        page = 1
        max_results_per_page = 50000

        while True:
            url = "https://api.steampowered.com/IStoreService/GetAppList/v1/"
            params = {
                'key': steam_api_key,
                'max_results': max_results_per_page,
                'last_appid': last_appid
            }

            logger.info(f"  Fetching page {page} (starting from app ID {last_appid})...")
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()

            # Extract apps from response
            apps_data = data.get('response', {}).get('apps', [])

            if not apps_data:
                logger.info("  No more apps returned - download complete")
                break

            # Convert to our format
            for app in apps_data:
                all_apps.append({
                    'appid': app.get('appid'),
                    'name': app.get('name', '')
                })

            # Update last_appid for next page
            last_appid = apps_data[-1].get('appid')
            page += 1

            logger.info(f"  Retrieved {len(apps_data):,} apps (total: {len(all_apps):,})")

            # If we got fewer results than max, we're done
            if len(apps_data) < max_results_per_page:
                logger.info("  Reached end of app list")
                break

            # Small delay between pages
            time.sleep(1)

        if all_apps:
            # Save to cache
            with open(APPLIST_FILE, 'w') as f:
                json.dump(all_apps, f)

            logger.info(f"✓ Downloaded {len(all_apps):,} Steam apps from IStoreService")
            logger.info(f"  Saved to: {APPLIST_FILE}")

            return all_apps

    except Exception as e:
        logger.warning(f"IStoreService API failed: {e}")

    # Method 2: Fallback to SteamSpy (limited to ~1000 apps)
    logger.info("Falling back to SteamSpy API...")
    try:
        url = "https://steamspy.com/api.php?request=all"
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        data = response.json()

        # Convert to list format
        apps = []
        for appid, app_data in data.items():
            try:
                apps.append({
                    'appid': int(appid),
                    'name': app_data.get('name', '')
                })
            except (ValueError, KeyError):
                continue

        if apps:
            # Save to cache
            with open(APPLIST_FILE, 'w') as f:
                json.dump(apps, f)

            logger.info(f"✓ Downloaded {len(apps):,} Steam games from SteamSpy")
            logger.warning(f"  WARNING: SteamSpy returns limited data (~1,000 apps)")
            logger.warning(f"  For complete catalog, add STEAM_API_KEY to .env file")
            logger.info(f"  Saved to: {APPLIST_FILE}")

            return apps

    except Exception as e:
        logger.warning(f"SteamSpy API failed: {e}")

    logger.error("All API endpoints failed")
    logger.error("To download the complete Steam catalog:")
    logger.error("  1. Get a Steam API key from https://steamcommunity.com/dev/apikey")
    logger.error("  2. Add STEAM_API_KEY=your_key_here to your .env file")
    logger.error("  3. Run this command again")
    return []


def load_steam_applist() -> list[dict]:
    """Load Steam app list from cache."""
    if not APPLIST_FILE.exists():
        logger.error(f"App list not found at {APPLIST_FILE}")
        logger.error("Run with --download first")
        return []

    with open(APPLIST_FILE, 'r') as f:
        apps = json.load(f)

    logger.info(f"Loaded {len(apps):,} apps from cache")
    return apps


def load_processed_ids() -> Set[int]:
    """Load set of already-processed app IDs."""
    if not PROCESSED_IDS_FILE.exists():
        return set()

    with open(PROCESSED_IDS_FILE, 'r') as f:
        ids = {int(line.strip()) for line in f if line.strip()}

    logger.info(f"Loaded {len(ids):,} already-processed app IDs")
    return ids


def save_processed_id(appid: int):
    """Append an app ID to the processed list."""
    with open(PROCESSED_IDS_FILE, 'a') as f:
        f.write(f"{appid}\n")


def get_tracked_appids(conn) -> Set[int]:
    """Get app IDs already in games or candidates tables."""
    cursor = conn.cursor()

    # Get from games table
    cursor.execute("SELECT steam_id FROM games")
    games_ids = {row[0] for row in cursor.fetchall()}

    # Get from candidates table
    cursor.execute("SELECT steam_id FROM candidates WHERE steam_id IS NOT NULL")
    candidate_ids = {row[0] for row in cursor.fetchall()}

    all_ids = games_ids | candidate_ids

    logger.info(f"Found {len(games_ids)} tracked games, {len(candidate_ids)} candidates")
    logger.info(f"Total to exclude: {len(all_ids):,} app IDs")

    return all_ids


def filter_applist(apps: list[dict], exclude_ids: Set[int]) -> list[dict]:
    """
    Filter app list to only include games worth evaluating.

    Filters out:
    - Apps in exclude_ids (already tracked/processed)
    - Obvious non-games (DLC, soundtracks, demos, tools)
    """
    filtered = []

    skip_keywords = [
        'soundtrack', 'ost', 'artbook', 'art book',
        ' dlc', 'demo', 'beta', 'test',
        'trailer', 'wallpaper', 'avatar',
        'tool', 'sdk', 'editor', 'server',
        'content creator pack', 'upgrade pack'
    ]

    for app in apps:
        appid = app.get('appid')
        name = app.get('name', '').lower()

        # Skip if already processed/tracked
        if appid in exclude_ids:
            continue

        # Skip obvious non-games
        if any(keyword in name for keyword in skip_keywords):
            continue

        filtered.append(app)

    logger.info(f"Filtered to {len(filtered):,} apps to evaluate")
    logger.info(f"  Excluded: {len(apps) - len(filtered):,} apps")

    return filtered


def evaluate_and_save(apps: list[dict], min_score: int = 5, batch_size: int = 1000) -> dict:
    """
    Evaluate apps and save high-scoring candidates.

    Args:
        apps: List of apps to evaluate
        min_score: Minimum score to save as candidate
        batch_size: Save to DB every N apps

    Returns:
        Statistics dictionary
    """
    steam_api = SteamAPI(rate_limit_delay=2.0)  # 2s between requests = ~1800/hour
    conn = get_connection()

    stats = {
        'total': len(apps),
        'processed': 0,
        'candidates_found': 0,
        'candidates_saved': 0,
        'errors': 0,
        'rate_limited': 0,
        'start_time': datetime.now()
    }

    candidates_batch = []

    try:
        for i, app in enumerate(apps, 1):
            appid = app['appid']
            name = app['name']

            # Progress logging
            if i % 10 == 0:
                elapsed = (datetime.now() - stats['start_time']).total_seconds()
                rate = i / elapsed if elapsed > 0 else 0
                eta_seconds = (stats['total'] - i) / rate if rate > 0 else 0
                eta_hours = eta_seconds / 3600

                logger.info(
                    f"Progress: {i:,}/{stats['total']:,} ({i/stats['total']*100:.1f}%) | "
                    f"Candidates: {stats['candidates_found']} | "
                    f"Rate limited: {stats['rate_limited']} | "
                    f"Rate: {rate:.1f}/s | "
                    f"ETA: {eta_hours:.1f}h"
                )

            try:
                # Fetch app details
                app_details = steam_api.get_app_details(appid)

                if not app_details:
                    stats['errors'] += 1
                    save_processed_id(appid)
                    continue

                # Only process actual games
                if app_details.get('type') != 'game':
                    save_processed_id(appid)
                    continue

                # Parse and score
                parsed = steam_api.parse_app_details(app_details)
                score, matches = calculate_necromancy_score(parsed)

                # Mark as processed
                save_processed_id(appid)
                stats['processed'] += 1

                # Save if high-scoring
                if score >= min_score:
                    candidate = {
                        'steam_id': appid,
                        'name': parsed['name'],
                        'score': score,
                        'matches': matches,
                        'short_description': parsed['short_description'],
                        'genres': parsed['genres'],
                        'price_usd': parsed['price_usd'],
                    }

                    candidates_batch.append(candidate)
                    stats['candidates_found'] += 1

                    logger.info(f"  ✓ CANDIDATE ({score}): {parsed['name']}")

                # Batch save to database
                if len(candidates_batch) >= batch_size:
                    saved = save_candidates_batch(candidates_batch, conn)
                    stats['candidates_saved'] += saved
                    candidates_batch = []

            except KeyboardInterrupt:
                logger.info("\n\nInterrupted by user")
                # Save pending candidates before exiting
                if candidates_batch:
                    logger.info(f"Saving {len(candidates_batch)} pending candidates...")
                    saved = save_candidates_batch(candidates_batch, conn)
                    stats['candidates_saved'] += saved
                    candidates_batch = []
                raise

            except RateLimitError as e:
                # Don't mark as processed - will retry on next run
                logger.warning(f"  Rate limited for {appid} ({name}): {e}")
                stats['rate_limited'] += 1
                # Don't save_processed_id - leave for retry
                continue

            except Exception as e:
                logger.error(f"  Error evaluating {appid} ({name}): {e}")
                stats['errors'] += 1
                save_processed_id(appid)
                continue

        # Save any remaining candidates
        if candidates_batch:
            saved = save_candidates_batch(candidates_batch, conn)
            stats['candidates_saved'] += saved

    finally:
        # Save any remaining candidates (in case of unexpected exit)
        if candidates_batch:
            logger.info(f"Saving {len(candidates_batch)} pending candidates in finally block...")
            try:
                saved = save_candidates_batch(candidates_batch, conn)
                stats['candidates_saved'] += saved
            except Exception as e:
                logger.error(f"Failed to save candidates in finally: {e}")
        conn.close()

    stats['end_time'] = datetime.now()
    stats['duration'] = stats['end_time'] - stats['start_time']

    return stats


def save_candidates_batch(candidates: list[dict], conn) -> int:
    """Save a batch of candidates to database."""
    cursor = conn.cursor()
    saved = 0

    for candidate in candidates:
        # Check if already exists
        cursor.execute(
            "SELECT id FROM candidates WHERE steam_id = ?",
            (candidate['steam_id'],)
        )
        if cursor.fetchone():
            continue

        # Create justification
        justification = f"Batch discovery - Score: {candidate['score']}\n"
        justification += f"Matches: {', '.join(candidate['matches'][:5])}\n\n"
        justification += f"Description: {candidate['short_description']}\n\n"
        justification += f"Genres: {', '.join(candidate['genres'] or [])}\n"
        if candidate['price_usd'] is not None:
            justification += f"Price: ${candidate['price_usd']:.2f}" if candidate['price_usd'] > 0 else "Price: Free"

        # Insert
        cursor.execute("""
            INSERT INTO candidates (
                steam_id, game_name, source, justification,
                status, date_submitted
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            candidate['steam_id'],
            candidate['name'],
            'auto_discovery',
            justification,
            'pending',
            datetime.now()
        ))

        saved += 1

    conn.commit()
    logger.info(f"  💾 Saved {saved} candidates to database")

    return saved


def show_stats():
    """Display discovery progress statistics."""
    print("\n" + "="*80)
    print("BATCH DISCOVERY STATISTICS")
    print("="*80)

    # Load processed IDs
    processed_ids = load_processed_ids()
    print(f"\nProcessed app IDs: {len(processed_ids):,}")

    # Load app list
    if APPLIST_FILE.exists():
        apps = load_steam_applist()
        print(f"Total Steam apps: {len(apps):,}")
        print(f"Remaining: {len(apps) - len(processed_ids):,}")
        print(f"Progress: {len(processed_ids)/len(apps)*100:.1f}%")
    else:
        print("\nApp list not downloaded yet. Run with --download")

    # Database stats
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM candidates WHERE source = 'auto_discovery'")
    auto_candidates = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM candidates WHERE status = 'pending'")
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM games")
    tracked = cursor.fetchone()[0]

    conn.close()

    print(f"\nCandidates from auto-discovery: {auto_candidates:,}")
    print(f"Pending review: {pending:,}")
    print(f"Games tracked: {tracked:,}")

    print("="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Batch game discovery across all Steam apps",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Workflow:
    1. Download app list: python scripts/batch_discover.py --download
    2. Run discovery:     python scripts/batch_discover.py --discover
    3. Check progress:    python scripts/batch_discover.py --stats
    4. Review results:    python scripts/review_candidates.py

The process is resumable - interrupted runs can continue where they left off.
Processed app IDs are tracked in data/discovery_cache/processed_appids.txt
        """
    )

    parser.add_argument('--download', action='store_true',
                       help="Download complete Steam app list")
    parser.add_argument('--discover', action='store_true',
                       help="Run batch discovery on all apps")
    parser.add_argument('--continue', dest='continue_run', action='store_true',
                       help="Continue interrupted discovery run")
    parser.add_argument('--stats', action='store_true',
                       help="Show discovery progress statistics")
    parser.add_argument('--min-score', type=int, default=5,
                       help="Minimum score threshold (default: 5)")
    parser.add_argument('--limit', type=int,
                       help="Limit number of apps to process (for testing)")
    parser.add_argument('--yes', '-y', action='store_true',
                       help="Skip confirmation prompt (for background runs)")

    args = parser.parse_args()

    # Download app list
    if args.download:
        apps = download_steam_applist()
        if apps:
            print(f"\n✓ Successfully downloaded {len(apps):,} Steam apps")
            print(f"  Run with --discover to begin evaluation")
        return

    # Show stats
    if args.stats:
        show_stats()
        return

    # Run discovery
    if args.discover or args.continue_run:
        # Load app list
        apps = load_steam_applist()
        if not apps:
            return

        # Get exclusion sets
        conn = get_connection()
        try:
            tracked_ids = get_tracked_appids(conn)
        finally:
            conn.close()

        processed_ids = load_processed_ids()
        exclude_ids = tracked_ids | processed_ids

        # Filter apps
        apps_to_process = filter_applist(apps, exclude_ids)

        if args.limit:
            apps_to_process = apps_to_process[:args.limit]
            logger.info(f"Limited to {args.limit:,} apps for testing")

        if not apps_to_process:
            print("\n✓ No apps left to process!")
            print("  All apps have been evaluated.")
            show_stats()
            return

        # Estimate time
        rate = 0.5  # apps per second (conservative with 2s rate limit)
        est_hours = len(apps_to_process) / rate / 3600

        print(f"\n{'='*80}")
        print(f"BATCH DISCOVERY")
        print(f"{'='*80}")
        print(f"Apps to process: {len(apps_to_process):,}")
        print(f"Minimum score: {args.min_score}")
        print(f"Estimated time: {est_hours:.1f} hours")
        print(f"{'='*80}\n")

        # Confirm for large runs (unless --yes flag is used)
        if len(apps_to_process) > 1000 and not args.limit and not args.yes:
            response = input("This will take several hours. Continue? [y/N] ").strip().lower()
            if response != 'y':
                print("Cancelled.")
                return

        # Run discovery
        logger.info("Starting batch discovery...")
        stats = evaluate_and_save(apps_to_process, min_score=args.min_score)

        # Print summary
        print(f"\n{'='*80}")
        print(f"DISCOVERY COMPLETE")
        print(f"{'='*80}")
        print(f"Duration: {stats['duration']}")
        print(f"Apps processed: {stats['processed']:,}/{stats['total']:,}")
        print(f"Candidates found: {stats['candidates_found']:,}")
        print(f"Candidates saved: {stats['candidates_saved']:,}")
        print(f"Errors: {stats['errors']:,}")
        print(f"{'='*80}\n")

        if stats['candidates_saved'] > 0:
            print(f"✓ Run 'python scripts/review_candidates.py' to review candidates")

        return

    # No action specified
    parser.print_help()


if __name__ == "__main__":
    main()
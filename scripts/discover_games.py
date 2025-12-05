#!/usr/bin/env python3
"""
Automated game discovery for Necro Game News.

Searches Steam for necromancy-related games and adds high-scoring candidates
to the database for manual review.

Usage:
    python scripts/discover_games.py --search     # Run discovery search
    python scripts/discover_games.py --limit 50   # Limit results
    python scripts/discover_games.py --min-score 5  # Set minimum score threshold
"""

import sys
import os
import logging
import argparse
import requests
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.schema import get_connection
from backend.scrapers.steam_api import SteamAPI

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# KEYWORD STRATEGY
# ============================================================================

NECROMANCY_KEYWORDS = {
    # Primary keywords (high confidence)
    'primary': [
        'necromancer', 'necromancy', 'necromantic',
        'raise dead', 'summon undead', 'summon skeleton',
        'death magic', 'dark magic',
    ],

    # Secondary keywords (moderate confidence - need context)
    'secondary': [
        'skeleton', 'undead', 'zombie', 'lich', 'bone',
        'corpse', 'graveyard', 'crypt', 'tomb',
        'minion', 'summoner', 'summoning',
        'reanimation', 'resurrection',
    ],

    # Genre/tag filters (must be present for secondary keywords)
    'required_genres': [
        'RPG', 'Action RPG', 'Strategy', 'Indie',
        'Fantasy', 'Dark Fantasy', 'Action',
        'Roguelike', 'Roguelite', 'Card Game',
        'Turn-Based', 'Tactical', 'Dungeon Crawler'
    ]
}


def calculate_necromancy_score(game_data: dict) -> tuple[int, list[str]]:
    """
    Calculate a necromancy relevance score for a game.

    Score calculation:
    - Primary keyword in name: +10 points
    - Primary keyword in description: +5 points
    - Secondary keyword in name: +3 points
    - Secondary keyword in description: +2 points
    - Has relevant genre/tag: +1 point

    Args:
        game_data: Parsed Steam app details

    Returns:
        Tuple of (score, list of matched keywords)
    """
    score = 0
    matches = []

    # Get searchable text (lowercase)
    name = (game_data.get('name') or '').lower()
    description = (game_data.get('short_description') or '').lower()
    genres = [g.lower() for g in (game_data.get('genres') or [])]
    categories = [c.lower() for c in (game_data.get('categories') or [])]

    # Combine all text for searching
    all_text = f"{name} {description}"
    all_genres = ' '.join(genres + categories)

    # Check primary keywords
    for keyword in NECROMANCY_KEYWORDS['primary']:
        keyword_lower = keyword.lower()
        if keyword_lower in name:
            score += 10
            matches.append(f"PRIMARY in name: '{keyword}'")
        elif keyword_lower in description:
            score += 5
            matches.append(f"PRIMARY in desc: '{keyword}'")

    # Check secondary keywords (lower weight)
    for keyword in NECROMANCY_KEYWORDS['secondary']:
        keyword_lower = keyword.lower()
        if keyword_lower in name:
            score += 3
            matches.append(f"SECONDARY in name: '{keyword}'")
        elif keyword_lower in description:
            score += 2
            matches.append(f"SECONDARY in desc: '{keyword}'")

    # Bonus for relevant genres
    for genre in NECROMANCY_KEYWORDS['required_genres']:
        if genre.lower() in all_genres:
            score += 1
            matches.append(f"Genre: {genre}")
            break  # Only count once

    return score, matches


def search_steam_store(query: str, max_results: int = 50) -> list[dict]:
    """
    Search Steam store using Steam's store API.

    Args:
        query: Search query string
        max_results: Maximum number of results to return

    Returns:
        List of dictionaries with basic app info
    """
    # Try the suggest API first (autocomplete endpoint)
    suggest_url = "https://store.steampowered.com/search/suggest"
    params = {
        'term': query,
        'f': 'games',
        'cc': 'US',
        'l': 'english',
        'v': '23482983'  # Version param
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(suggest_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse HTML response for app IDs and names
        import re
        html = response.text

        # Extract app IDs and names from the HTML
        # Format: data-ds-appid="APPID">Game Name</div>
        pattern = r'data-ds-appid="(\d+)"[^>]*>([^<]+)</div>'
        matches = re.findall(pattern, html)

        apps = []
        for appid, name in matches:
            # Basic filter: name shouldn't be a soundtrack/dlc
            name_lower = name.lower().strip()
            if not any(skip in name_lower for skip in ['soundtrack', 'ost', 'artbook', 'dlc', 'demo']):
                apps.append({
                    'steam_id': int(appid),
                    'name': name.strip()
                })

        return apps[:max_results]

    except Exception as e:
        logger.warning(f"Steam suggest API failed for '{query}': {e}")

        # Fallback: try the community search endpoint
        try:
            url = "https://steamcommunity.com/actions/SearchApps/"
            params = {'q': query}
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            results = response.json()

            apps = []
            for item in results:
                name_lower = item.get('name', '').lower()
                if not any(skip in name_lower for skip in ['soundtrack', 'ost', 'artbook']):
                    apps.append({
                        'steam_id': int(item.get('appid')),
                        'name': item.get('name')
                    })

            return apps[:max_results]

        except Exception as e2:
            logger.error(f"Both Steam search methods failed for '{query}': {e2}")
            return []


def discover_games(min_score: int = 5, limit: int = 100) -> list[dict]:
    """
    Run automated game discovery.

    Searches Steam for necromancy-related games and scores them.

    Args:
        min_score: Minimum score to be considered a candidate
        limit: Maximum number of games to process

    Returns:
        List of candidate games with scores
    """
    logger.info("Starting game discovery...")
    logger.info(f"Minimum score threshold: {min_score}")

    steam_api = SteamAPI()
    candidates = []
    seen_appids = set()

    # Search for each primary keyword
    search_queries = NECROMANCY_KEYWORDS['primary'][:5]  # Top 5 keywords

    for query in search_queries:
        logger.info(f"Searching Steam for: '{query}'")

        search_results = search_steam_store(query, max_results=20)
        logger.info(f"  Found {len(search_results)} results")

        for app in search_results:
            appid = app['steam_id']

            # Skip if already processed
            if appid in seen_appids:
                continue
            seen_appids.add(appid)

            # Skip if we've hit the limit
            if len(candidates) >= limit:
                break

            # Get detailed app info
            logger.info(f"  Analyzing: {app['name']} ({appid})")
            app_details = steam_api.get_app_details(appid)

            if not app_details:
                logger.warning(f"    Could not fetch details for {appid}")
                continue

            # Only process games (not DLC, soundtracks, etc.)
            if app_details.get('type') != 'game':
                logger.info(f"    Skipping: not a game (type: {app_details.get('type')})")
                continue

            # Parse and score
            parsed = steam_api.parse_app_details(app_details)
            score, matches = calculate_necromancy_score(parsed)

            if score >= min_score:
                candidate = {
                    'steam_id': appid,
                    'name': parsed['name'],
                    'score': score,
                    'matches': matches,
                    'short_description': parsed['short_description'],
                    'genres': parsed['genres'],
                    'price_usd': parsed['price_usd'],
                    'release_date': parsed['release_date'],
                }
                candidates.append(candidate)
                logger.info(f"    ✓ CANDIDATE (score: {score}): {parsed['name']}")
                logger.info(f"      Matches: {', '.join(matches[:3])}")
            else:
                logger.info(f"    ✗ Score too low ({score})")

        # Rate limiting between searches
        time.sleep(2)

    # Sort by score (highest first)
    candidates.sort(key=lambda x: x['score'], reverse=True)

    logger.info(f"\n{'='*60}")
    logger.info(f"Discovery complete: Found {len(candidates)} candidates")
    logger.info(f"{'='*60}")

    return candidates


def save_candidates_to_db(candidates: list[dict], conn) -> int:
    """
    Save discovered candidates to the database.

    Args:
        candidates: List of candidate games
        conn: Database connection

    Returns:
        Number of new candidates added
    """
    cursor = conn.cursor()
    added = 0
    skipped = 0

    for candidate in candidates:
        # Check if already exists (in candidates or games table)
        cursor.execute("""
            SELECT id FROM candidates WHERE steam_id = ?
        """, (candidate['steam_id'],))

        if cursor.fetchone():
            logger.info(f"Skipping {candidate['name']}: already in candidates")
            skipped += 1
            continue

        cursor.execute("""
            SELECT id FROM games WHERE steam_id = ?
        """, (candidate['steam_id'],))

        if cursor.fetchone():
            logger.info(f"Skipping {candidate['name']}: already tracked")
            skipped += 1
            continue

        # Create justification text
        justification = f"Auto-discovered with score {candidate['score']}\n"
        justification += f"Matches: {', '.join(candidate['matches'][:5])}\n\n"
        justification += f"Description: {candidate['short_description']}\n\n"
        justification += f"Genres: {', '.join(candidate['genres'])}\n"
        justification += f"Price: ${candidate['price_usd']:.2f}" if candidate['price_usd'] else "Price: Free"

        # Insert into candidates table
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

        added += 1
        logger.info(f"✓ Added to candidates: {candidate['name']}")

    conn.commit()

    logger.info(f"\nSaved {added} new candidates to database")
    logger.info(f"Skipped {skipped} duplicates")

    return added


def main():
    parser = argparse.ArgumentParser(description="Discover necromancy games on Steam")
    parser.add_argument('--search', action='store_true', help="Run discovery search")
    parser.add_argument('--min-score', type=int, default=5,
                       help="Minimum necromancy score (default: 5)")
    parser.add_argument('--limit', type=int, default=100,
                       help="Maximum number of games to process (default: 100)")
    parser.add_argument('--save', action='store_true',
                       help="Save candidates to database")

    args = parser.parse_args()

    if not args.search:
        parser.print_help()
        print("\nExample usage:")
        print("  python scripts/discover_games.py --search --min-score 5 --limit 50 --save")
        return

    # Run discovery
    candidates = discover_games(min_score=args.min_score, limit=args.limit)

    if not candidates:
        print("\nNo candidates found matching criteria.")
        return

    # Display results
    print(f"\n{'='*80}")
    print(f"TOP CANDIDATES (sorted by score)")
    print(f"{'='*80}")

    for i, candidate in enumerate(candidates[:10], 1):
        print(f"\n{i}. {candidate['name']} (Score: {candidate['score']})")
        print(f"   Steam ID: {candidate['steam_id']}")
        print(f"   Matches: {', '.join(candidate['matches'][:3])}")
        if candidate['genres']:
            print(f"   Genres: {', '.join(candidate['genres'][:3])}")

    # Save to database if requested
    if args.save:
        print(f"\n{'='*80}")
        print("Saving candidates to database...")
        print(f"{'='*80}\n")

        conn = get_connection()
        try:
            added = save_candidates_to_db(candidates, conn)
            print(f"\n✓ Successfully added {added} candidates to database")
            print(f"  Run 'python scripts/review_candidates.py' to review them")
        finally:
            conn.close()
    else:
        print(f"\n💡 Run with --save to add these candidates to the database")


if __name__ == "__main__":
    main()
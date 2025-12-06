#!/usr/bin/env python3
"""
Check for new game updates from multiple platforms.

This is the main automation script that checks all tracked games
for new updates/news and stores them in the database.

Supports:
- Steam (via SteamAPI)
- Battle.net (placeholder for future implementation)
- Other platforms as they are added

Usage:
    python scripts/check_updates.py                    # Check all games
    python scripts/check_updates.py --game-id 1        # Check specific game
    python scripts/check_updates.py --limit 5          # Check only 5 games
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.scrapers.steam_api import SteamAPI, SteamAPIError, RateLimitError
from backend.database.schema import get_connection

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Platforms that have update checking implemented
SUPPORTED_UPDATE_PLATFORMS = {'steam'}  # Add 'battlenet' when implemented


def check_steam_updates(cursor, db_id: int, name: str, steam_id: int, steam_api: SteamAPI, max_news: int = 5) -> tuple:
    """
    Check for new updates for a game on Steam.

    Returns:
        Tuple of (new_count, skipped_count, external_count)
    """
    # Fetch news from Steam
    news_items = steam_api.get_app_news(steam_id, count=max_news)

    if not news_items:
        logger.info(f"  No news items found for {name} on Steam")
        return 0, 0, 0

    logger.info(f"  Found {len(news_items)} news items on Steam")

    new_count = 0
    skipped_count = 0
    external_count = 0

    for news_item in news_items:
        # Filter out external press sources (PC Gamer, PCGamesN, etc.)
        if not steam_api.is_steam_official(news_item):
            external_count += 1
            continue

        parsed = steam_api.parse_news_item(news_item, steam_id)
        gid = parsed['gid']

        # Check if this update already exists
        cursor.execute(
            "SELECT id FROM updates WHERE gid = ?",
            (gid,)
        )

        if cursor.fetchone():
            skipped_count += 1
            continue

        # Add new update with source_platform
        cursor.execute("""
            INSERT INTO updates
            (game_id, update_type, title, content, url, gid, date, source_platform)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'steam')
        """, (
            db_id,
            parsed['update_type'],
            parsed['title'],
            parsed['contents'],
            parsed['url'],
            gid,
            parsed['date']
        ))

        new_count += 1
        logger.info(f"  + [{parsed['update_type']}] {parsed['title'][:50]}...")

    return new_count, skipped_count, external_count


def check_game_updates(game_id: int, steam_api: SteamAPI, max_news: int = 5) -> int:
    """
    Check for new updates for a specific game.

    Routes to the appropriate platform scraper based on primary_platform.

    Args:
        game_id: Database ID of the game
        steam_api: SteamAPI instance
        max_news: Maximum number of news items to fetch

    Returns:
        Number of new updates added
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Get game info including platform data
        cursor.execute("""
            SELECT id, name, steam_id, primary_platform, battlenet_id
            FROM games WHERE id = ?
        """, (game_id,))
        row = cursor.fetchone()

        if not row:
            logger.error(f"Game with ID {game_id} not found")
            return 0

        db_id, name, steam_id, primary_platform, battlenet_id = row
        logger.info(f"Checking updates for: {name} (platform: {primary_platform})")

        new_count = 0
        skipped_count = 0
        external_count = 0

        # Route to appropriate platform scraper
        if primary_platform == 'steam' and steam_id:
            new_count, skipped_count, external_count = check_steam_updates(
                cursor, db_id, name, steam_id, steam_api, max_news
            )
        elif primary_platform == 'battlenet' and battlenet_id:
            # TODO: Implement Battle.net update checking
            logger.info(f"  ⏳ Battle.net update checking not yet implemented for {name}")
        elif primary_platform == 'manual':
            logger.info(f"  ⊙ Manual platform - no automated updates for {name}")
        else:
            # Fall back to Steam if we have steam_id
            if steam_id:
                logger.info(f"  Falling back to Steam for {name}")
                new_count, skipped_count, external_count = check_steam_updates(
                    cursor, db_id, name, steam_id, steam_api, max_news
                )
            else:
                logger.warning(f"  ⚠ No supported platform for {name} (primary: {primary_platform})")

        # Update last_checked timestamp
        cursor.execute(
            "UPDATE games SET last_checked = ? WHERE id = ?",
            (datetime.now(), db_id)
        )

        conn.commit()

        if new_count > 0:
            logger.info(f"  ✓ Added {new_count} new updates ({skipped_count} existing, {external_count} external filtered)")
        elif primary_platform in SUPPORTED_UPDATE_PLATFORMS or steam_id:
            logger.info(f"  ⊙ No new updates ({skipped_count} existing, {external_count} external filtered)")

        return new_count

    except Exception as e:
        logger.error(f"Error checking updates for game {game_id}: {e}")
        conn.rollback()
        return 0

    finally:
        conn.close()


def check_all_games(limit: int = None, max_news: int = 5):
    """
    Check for updates for all active games.

    Routes each game to the appropriate platform scraper based on primary_platform.

    Args:
        limit: Maximum number of games to check (None for all)
        max_news: Maximum number of news items to fetch per game
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT id, name, steam_id, primary_platform, last_checked
        FROM games
        WHERE is_active = 1
        ORDER BY
            CASE
                WHEN last_checked IS NULL THEN 0
                ELSE 1
            END,
            last_checked ASC
    """

    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    games = cursor.fetchall()
    conn.close()

    if not games:
        logger.info("No active games in database")
        return

    # Count games by platform
    platform_counts = {}
    for _, _, _, platform, _ in games:
        platform_counts[platform] = platform_counts.get(platform, 0) + 1

    logger.info(f"Checking {len(games)} game(s) for updates")
    logger.info(f"  Platforms: {', '.join(f'{p}={c}' for p, c in sorted(platform_counts.items()))}")
    print()

    steam_api = SteamAPI()

    total_new = 0
    success_count = 0
    fail_count = 0
    skipped_count = 0

    for db_id, name, steam_id, primary_platform, last_checked in games:
        try:
            # Skip games without a supported update platform
            if primary_platform not in SUPPORTED_UPDATE_PLATFORMS and not steam_id:
                logger.info(f"Skipping {name} (platform: {primary_platform}, no Steam fallback)")
                skipped_count += 1
                continue

            new_updates = check_game_updates(db_id, steam_api, max_news)
            total_new += new_updates
            success_count += 1
        except Exception as e:
            logger.error(f"Unexpected error with {name}: {e}")
            fail_count += 1

        print()  # Blank line between games

    # Summary
    print("=" * 60)
    print(f"Summary:")
    print(f"  Games checked: {success_count}")
    if skipped_count > 0:
        print(f"  Games skipped (no API): {skipped_count}")
    print(f"  Games failed: {fail_count}")
    print(f"  New updates found: {total_new}")
    print("=" * 60)

    if total_new > 0:
        print(f"\n💀 Found {total_new} new necromantic game update(s)!")


def main():
    parser = argparse.ArgumentParser(
        description='Check for new game updates from multiple platforms'
    )
    
    parser.add_argument('--game-id', type=int,
                       help='Check specific game by database ID')
    parser.add_argument('--limit', type=int,
                       help='Maximum number of games to check')
    parser.add_argument('--max-news', type=int, default=5,
                       help='Maximum news items to fetch per game (default: 5)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Necro Game News - Update Checker")
    print("=" * 60)
    print()
    
    if args.game_id:
        # Check single game
        steam_api = SteamAPI()
        new_count = check_game_updates(args.game_id, steam_api, args.max_news)
        print()
        print(f"✓ Found {new_count} new update(s)")
        return 0
    else:
        # Check all games (or limited set)
        check_all_games(args.limit, args.max_news)
        return 0


if __name__ == "__main__":
    sys.exit(main())

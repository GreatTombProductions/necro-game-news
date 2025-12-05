#!/usr/bin/env python3
"""
Check for new game updates from Steam.

This is the main automation script that checks all tracked games
for new updates/news and stores them in the database.

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

from backend.scrapers.steam_api import SteamAPI, SteamAPIError
from backend.database.schema import get_connection

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_game_updates(game_id: int, steam_api: SteamAPI, max_news: int = 5) -> int:
    """
    Check for new updates for a specific game.
    
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
        # Get game info
        cursor.execute(
            "SELECT id, name, steam_id FROM games WHERE id = ?",
            (game_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            logger.error(f"Game with ID {game_id} not found")
            return 0
        
        db_id, name, steam_id = row
        logger.info(f"Checking updates for: {name}")
        
        # Fetch news from Steam
        news_items = steam_api.get_app_news(steam_id, count=max_news)
        
        if not news_items:
            logger.info(f"  No news items found for {name}")
            return 0
        
        logger.info(f"  Found {len(news_items)} news items on Steam")
        
        # Check which ones are new
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

            # Add new update
            cursor.execute("""
                INSERT INTO updates
                (game_id, update_type, title, content, url, gid, date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
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
        
        # Update last_checked timestamp
        cursor.execute(
            "UPDATE games SET last_checked = ? WHERE id = ?",
            (datetime.now(), db_id)
        )
        
        conn.commit()
        
        if new_count > 0:
            logger.info(f"  ✓ Added {new_count} new updates ({skipped_count} existing, {external_count} external filtered)")
        else:
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

    Args:
        limit: Maximum number of games to check (None for all)
        max_news: Maximum number of news items to fetch per game
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT id, name, steam_id, last_checked
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
    
    logger.info(f"Checking {len(games)} game(s) for updates")
    print()
    
    steam_api = SteamAPI()
    
    total_new = 0
    success_count = 0
    fail_count = 0
    
    for db_id, name, steam_id, last_checked in games:
        try:
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
    print(f"  Games failed: {fail_count}")
    print(f"  New updates found: {total_new}")
    print("=" * 60)
    
    if total_new > 0:
        print(f"\n💀 Found {total_new} new necromantic game update(s)!")


def main():
    parser = argparse.ArgumentParser(
        description='Check for new game updates from Steam'
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

#!/usr/bin/env python3
"""
Fetch and update game details from Steam.

This script fetches detailed information from Steam for all games
in the database and updates their metadata fields.

Usage:
    python scripts/fetch_game_details.py              # Update all games
    python scripts/fetch_game_details.py --game-id 1  # Update specific game
"""

import sys
import argparse
import json
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


def fetch_and_update_game(game_id: int, steam_api: SteamAPI) -> bool:
    """
    Fetch details from Steam and update database.
    
    Args:
        game_id: Database ID of the game
        steam_api: SteamAPI instance
        
    Returns:
        True if successful, False otherwise
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Get game info from database
        cursor.execute(
            "SELECT id, name, steam_id FROM games WHERE id = ?",
            (game_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            logger.error(f"Game with ID {game_id} not found in database")
            return False
        
        db_id, name, steam_id = row
        logger.info(f"Fetching details for: {name} (Steam ID: {steam_id})")
        
        # Fetch from Steam
        details = steam_api.get_app_details(steam_id)
        
        if not details:
            logger.warning(f"Could not fetch details for {name}")
            return False
        
        # Parse details
        parsed = steam_api.parse_app_details(details)
        
        # Update database
        cursor.execute("""
            UPDATE games SET
                name = ?,
                app_type = ?,
                short_description = ?,
                header_image_url = ?,
                developer = ?,
                publisher = ?,
                release_date = ?,
                steam_tags = ?,
                genres = ?,
                last_checked = ?
            WHERE id = ?
        """, (
            parsed['name'],
            parsed['app_type'],
            parsed['short_description'],
            parsed['header_image'],
            parsed['developer'],
            parsed['publisher'],
            parsed['release_date'],
            json.dumps(parsed['categories']),  # Store as JSON
            json.dumps(parsed['genres']),      # Store as JSON
            datetime.now(),
            db_id
        ))
        
        conn.commit()
        logger.info(f"✓ Updated: {parsed['name']}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating game {game_id}: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()


def fetch_all_games():
    """Fetch and update details for all active games"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, steam_id 
        FROM games 
        WHERE is_active = 1
        ORDER BY name
    """)
    
    games = cursor.fetchall()
    conn.close()
    
    if not games:
        logger.info("No active games in database")
        return
    
    logger.info(f"Found {len(games)} active games to update")
    
    steam_api = SteamAPI()
    success_count = 0
    fail_count = 0
    
    for db_id, name, steam_id in games:
        try:
            if fetch_and_update_game(db_id, steam_api):
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            logger.error(f"Unexpected error with {name}: {e}")
            fail_count += 1
    
    print("\n" + "=" * 60)
    print(f"Summary:")
    print(f"  ✓ Successfully updated: {success_count}")
    print(f"  ✗ Failed: {fail_count}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Fetch game details from Steam and update database'
    )
    
    parser.add_argument('--game-id', type=int,
                       help='Update specific game by database ID')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Fetching game details from Steam")
    print("=" * 60)
    print()
    
    if args.game_id:
        # Update single game
        steam_api = SteamAPI()
        success = fetch_and_update_game(args.game_id, steam_api)
        return 0 if success else 1
    else:
        # Update all games
        fetch_all_games()
        return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Load games from games_list.yaml into the database.

This script reads the curated games list and adds any new games
to the database. With --update flag, it also updates classification
for existing games. With --sync flag, it deletes games from the
database that are no longer in the YAML file.

Usage:
    python scripts/load_games_from_yaml.py              # Add new games only
    python scripts/load_games_from_yaml.py --update     # Add new + update existing
    python scripts/load_games_from_yaml.py --sync       # Also delete removed games
    python scripts/load_games_from_yaml.py -us          # Full sync (update + delete)
"""

import sys
import json
import yaml
import logging
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.schema import get_connection
from backend.scrapers.steam_api import SteamAPI

# Number of news items to fetch for newly added games (higher than daily checks
# to capture "Last Updated" date even for games not recently updated)
INITIAL_NEWS_COUNT = 50

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_steam_details(game_id: int, steam_id: int, name: str, steam_api: SteamAPI, cursor) -> bool:
    """
    Fetch details from Steam API and update the database.

    Args:
        game_id: Database ID of the game
        steam_id: Steam App ID
        name: Game name for logging
        steam_api: SteamAPI instance
        cursor: Database cursor

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"  Fetching Steam details for: {name}")

        details = steam_api.get_app_details(steam_id)
        if not details:
            logger.warning(f"  Could not fetch details for {name}")
            return False

        parsed = steam_api.parse_app_details(details)

        cursor.execute("""
            UPDATE games SET
                name = ?,
                app_type = ?,
                short_description = ?,
                header_image_url = ?,
                screenshot_url = ?,
                developer = ?,
                publisher = ?,
                release_date = ?,
                price_usd = ?,
                steam_tags = ?,
                genres = ?,
                last_checked = ?
            WHERE id = ?
        """, (
            parsed['name'],
            parsed['app_type'],
            parsed['short_description'],
            parsed['header_image'],
            parsed.get('screenshot_url'),
            parsed['developer'],
            parsed['publisher'],
            parsed['release_date'],
            parsed.get('price_usd'),
            json.dumps(parsed.get('tags', [])),
            json.dumps(parsed['genres']),
            datetime.now(),
            game_id
        ))

        logger.info(f"  ✓ Fetched details: {parsed['developer']} | {', '.join(parsed['genres'][:3])}")
        return True

    except Exception as e:
        logger.error(f"  Error fetching details for {name}: {e}")
        return False


def fetch_initial_updates(game_id: int, steam_id: int, name: str, steam_api: SteamAPI, cursor) -> int:
    """
    Fetch initial updates/news for a newly added game.

    Uses a higher count than daily checks to capture "Last Updated" date
    even for games that haven't been updated recently.

    Args:
        game_id: Database ID of the game
        steam_id: Steam App ID
        name: Game name for logging
        steam_api: SteamAPI instance
        cursor: Database cursor

    Returns:
        Number of updates added
    """
    try:
        logger.info(f"  Fetching initial updates for: {name}")

        news_items = steam_api.get_app_news(steam_id, count=INITIAL_NEWS_COUNT)
        if not news_items:
            logger.info(f"    No news items found")
            return 0

        new_count = 0
        external_count = 0

        for news_item in news_items:
            # Filter out external press sources
            if not steam_api.is_steam_official(news_item):
                external_count += 1
                continue

            parsed = steam_api.parse_news_item(news_item, steam_id)
            gid = parsed['gid']

            # Check if this update already exists (shouldn't for new games, but be safe)
            cursor.execute("SELECT id FROM updates WHERE gid = ?", (gid,))
            if cursor.fetchone():
                continue

            # Add update
            cursor.execute("""
                INSERT INTO updates
                (game_id, update_type, title, content, url, gid, date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                game_id,
                parsed['update_type'],
                parsed['title'],
                parsed['contents'],
                parsed['url'],
                gid,
                parsed['date']
            ))
            new_count += 1

        logger.info(f"    ✓ Added {new_count} updates ({external_count} external filtered)")
        return new_count

    except Exception as e:
        logger.error(f"  Error fetching updates for {name}: {e}")
        return 0


def load_games_from_yaml(yaml_path='data/games_list.yaml', update_existing=False, sync_deletes=False):
    """
    Load games from YAML file and add/update in database.
    
    Args:
        yaml_path: Path to games_list.yaml file
        update_existing: If True, update classification for existing games
        sync_deletes: If True, delete games from DB that aren't in YAML
    """
    yaml_file = Path(yaml_path)
    
    if not yaml_file.exists():
        print(f"✗ Games list not found: {yaml_path}")
        return 0
    
    # Read YAML
    with open(yaml_file, 'r') as f:
        data = yaml.safe_load(f)
    
    games = data.get('games', [])
    
    if not games:
        print("✗ No games found in YAML file")
        return 0
    
    print(f"Found {len(games)} games in {yaml_path}")
    mode_parts = ["Add new games"]
    if update_existing:
        mode_parts.append("update existing")
    if sync_deletes:
        mode_parts.append("delete removed")
    print(f"Mode: {' + '.join(mode_parts)}")
    print()
    
    # Connect to database
    conn = get_connection()
    cursor = conn.cursor()
    
    added = 0
    updated = 0
    skipped = 0
    deleted = 0
    errors = 0
    details_fetched = 0
    details_failed = 0
    updates_fetched = 0

    # Track newly added games for Steam API fetch
    newly_added_games = []

    # Get steam_ids from YAML for sync check
    yaml_steam_ids = {game['steam_id'] for game in games}
    
    for game in games:
        name = game['name']
        steam_id = game['steam_id']
        classification = game['classification']
        notes = game.get('notes', '')
        
        try:
            # Check if game already exists
            cursor.execute(
                "SELECT id, dimension_1, dimension_2, dimension_3, classification_notes FROM games WHERE steam_id = ?",
                (steam_id,)
            )
            
            existing = cursor.fetchone()
            
            if existing:
                if update_existing:
                    # Check if classification changed
                    db_id, old_dim1, old_dim2, old_dim3, old_notes = existing
                    new_dim1 = classification['dimension_1']
                    new_dim2 = classification['dimension_2']
                    new_dim3 = classification['dimension_3']
                    
                    if (old_dim1 != new_dim1 or 
                        old_dim2 != new_dim2 or 
                        old_dim3 != new_dim3 or
                        old_notes != notes):
                        
                        # Update classification
                        cursor.execute("""
                            UPDATE games SET
                                dimension_1 = ?,
                                dimension_2 = ?,
                                dimension_3 = ?,
                                classification_notes = ?
                            WHERE id = ?
                        """, (new_dim1, new_dim2, new_dim3, notes, db_id))
                        
                        # Show what changed
                        changes = []
                        if old_dim1 != new_dim1:
                            changes.append(f"dim1: {old_dim1}→{new_dim1}")
                        if old_dim2 != new_dim2:
                            changes.append(f"dim2: {old_dim2}→{new_dim2}")
                        if old_dim3 != new_dim3:
                            changes.append(f"dim3: {old_dim3}→{new_dim3}")
                        if old_notes != notes:
                            changes.append("notes updated")
                        
                        print(f"↻ Updated: {name} ({', '.join(changes)})")
                        updated += 1
                    else:
                        print(f"⊙ Unchanged: {name}")
                        skipped += 1
                else:
                    print(f"⊙ Skipped (already exists): {name}")
                    skipped += 1
                continue
            
            # Add new game
            cursor.execute("""
                INSERT INTO games 
                (steam_id, name, dimension_1, dimension_2, dimension_3, 
                 classification_notes, date_added)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                steam_id,
                name,
                classification['dimension_1'],
                classification['dimension_2'],
                classification['dimension_3'],
                notes,
                datetime.now()
            ))
            
            # Get the newly inserted game's ID
            game_id = cursor.lastrowid
            newly_added_games.append((game_id, steam_id, name))

            print(f"✓ Added: {name} ({classification['dimension_1']}, "
                  f"{classification['dimension_2']}, {classification['dimension_3']})")
            added += 1

        except Exception as e:
            print(f"✗ Error processing {name}: {e}")
            errors += 1
    
    # Delete games that are in DB but not in YAML (if sync mode)
    if sync_deletes:
        print()
        print("Checking for games to remove...")
        
        cursor.execute("SELECT id, steam_id, name FROM games")
        db_games = cursor.fetchall()
        
        for game_id, steam_id, name in db_games:
            if steam_id not in yaml_steam_ids:
                try:
                    # Get update count before deletion
                    cursor.execute(
                        "SELECT COUNT(*) FROM updates WHERE game_id = ?",
                        (game_id,)
                    )
                    update_count = cursor.fetchone()[0]
                    
                    # Delete game (CASCADE will delete updates automatically)
                    cursor.execute("DELETE FROM games WHERE id = ?", (game_id,))
                    
                    print(f"🗑  Deleted: {name} (steam_id: {steam_id}, {update_count} updates)")
                    deleted += 1
                    
                except Exception as e:
                    print(f"✗ Error deleting {name}: {e}")
                    errors += 1

    # Fetch Steam details and initial updates for newly added games
    if newly_added_games:
        print()
        print(f"Fetching Steam data for {len(newly_added_games)} new games...")
        steam_api = SteamAPI()

        for game_id, steam_id, name in newly_added_games:
            # Fetch game details (description, images, etc.)
            if fetch_steam_details(game_id, steam_id, name, steam_api, cursor):
                details_fetched += 1
            else:
                details_failed += 1

            # Fetch initial updates (uses higher count to capture Last Updated date)
            updates_fetched += fetch_initial_updates(game_id, steam_id, name, steam_api, cursor)

    conn.commit()
    conn.close()

    # Summary
    print()
    print("=" * 60)
    print(f"Summary:")
    print(f"  ✓ Added: {added}")
    if update_existing:
        print(f"  ↻ Updated: {updated}")
    if sync_deletes:
        print(f"  🗑  Deleted: {deleted}")
    print(f"  ⊙ Skipped (unchanged): {skipped}")
    if details_fetched or details_failed or updates_fetched:
        print(f"  Steam API: {details_fetched} details fetched, {details_failed} failed")
        if updates_fetched:
            print(f"  Initial updates: {updates_fetched}")
    print(f"  ✗ Errors: {errors}")
    print("=" * 60)
    
    return added + updated + deleted


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Load games from YAML into database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add new games only (default)
  python scripts/load_games_from_yaml.py
  
  # Add new games AND update existing classifications
  python scripts/load_games_from_yaml.py --update
  
  # Full sync: add, update, and delete games not in YAML
  python scripts/load_games_from_yaml.py --update --sync
  
  # Or use short form
  python scripts/load_games_from_yaml.py -us

Use --update when you've changed classifications in games_list.yaml.
Use --sync to remove games from DB that aren't in the YAML file.
WARNING: --sync will DELETE games and all their updates!
        """
    )
    
    parser.add_argument('--yaml', default='data/games_list.yaml',
                       help='Path to games YAML file (default: data/games_list.yaml)')
    parser.add_argument('-u', '--update', action='store_true',
                       help='Update existing games (not just add new ones)')
    parser.add_argument('-s', '--sync', action='store_true',
                       help='Delete games from DB that are not in YAML (destructive!)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Loading games from games_list.yaml")
    print("=" * 60)
    print()
    
    try:
        count = load_games_from_yaml(args.yaml, args.update, args.sync)
        return 0 if count >= 0 else 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
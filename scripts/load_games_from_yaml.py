#!/usr/bin/env python3
"""
Load games from games_list.yaml into the database.

This script reads the curated games list and adds any new games
to the database. With --update flag, it also updates classification
for existing games. With --sync flag, it deletes games from the
database that are no longer in the YAML file.

Supports multi-platform games with:
- steam_id, battlenet_id, gog_id, epic_id, itchio_id
- platforms: list of platforms the game is on
- primary_platform: where to fetch updates from

Supports multiple registries:
- necromancy (default): data/games_list.yaml
- blood: data/blood_games_list.yaml (use --blood flag)

Usage:
    python scripts/load_games_from_yaml.py              # Add new games only
    python scripts/load_games_from_yaml.py --update     # Add new + update existing
    python scripts/load_games_from_yaml.py --sync       # Also delete removed games
    python scripts/load_games_from_yaml.py -us          # Full sync (update + delete)
    python scripts/load_games_from_yaml.py --blood      # Load blood registry games
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

# Platform identifiers
VALID_PLATFORMS = {'steam', 'battlenet', 'gog', 'epic', 'itchio', 'manual'}

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_game_identifier(game: dict) -> str:
    """
    Get a unique identifier for a game from YAML.
    Uses steam_id if available, otherwise uses name + primary_platform.
    """
    if game.get('steam_id'):
        return f"steam:{game['steam_id']}"
    if game.get('battlenet_id'):
        return f"battlenet:{game['battlenet_id']}"
    if game.get('gog_id'):
        return f"gog:{game['gog_id']}"
    if game.get('epic_id'):
        return f"epic:{game['epic_id']}"
    if game.get('itchio_id'):
        return f"itchio:{game['itchio_id']}"
    # Fall back to name for manual entries
    return f"name:{game['name']}"


def find_existing_game(cursor, game: dict):
    """
    Find an existing game in the database by various identifiers.
    Returns (id, ...) tuple if found, None otherwise.
    """
    # Common SELECT fields for all queries
    select_fields = """SELECT id, dimension_1, dimension_2, dimension_3, dimension_4,
               dimension_1_notes, dimension_2_notes, dimension_3_notes, dimension_4_notes,
               platforms, primary_platform, battlenet_id, battlenet_store_id, gog_id, epic_id, itchio_id, aliases, date_updated,
               registry, vampirism, vampirism_notes, hemomancy, hemomancy_notes, app_type
               FROM games"""

    # Try steam_id first (most common)
    if game.get('steam_id'):
        cursor.execute(f"{select_fields} WHERE steam_id = ?", (game['steam_id'],))
        result = cursor.fetchone()
        if result:
            return result

    # Try other platform IDs
    for platform_id, field in [
        ('battlenet_id', 'battlenet_id'),
        ('gog_id', 'gog_id'),
        ('epic_id', 'epic_id'),
        ('itchio_id', 'itchio_id'),
    ]:
        if game.get(platform_id):
            cursor.execute(f"{select_fields} WHERE {field} = ?", (game[platform_id],))
            result = cursor.fetchone()
            if result:
                return result

    # Fall back to name for manual entries
    if not any(game.get(k) for k in ['steam_id', 'battlenet_id', 'gog_id', 'epic_id', 'itchio_id']):
        cursor.execute(
            f"{select_fields} WHERE name = ? AND primary_platform = 'manual'",
            (game['name'],)
        )
        return cursor.fetchone()

    return None


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


def load_games_from_yaml(yaml_path='data/games_list.yaml', update_existing=False, sync_deletes=False, registry='necromancy'):
    """
    Load games from YAML file and add/update in database.

    Supports multi-platform games with steam_id, battlenet_id, gog_id, etc.
    Supports multiple registries (necromancy, blood).

    Args:
        yaml_path: Path to games_list.yaml file
        update_existing: If True, update classification for existing games
        sync_deletes: If True, delete games from DB that aren't in YAML
        registry: Which registry to load for ('necromancy' or 'blood')
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

    # Track newly added games for API fetch (platform, game_id, platform_id, name)
    newly_added_games = []

    # Track game identifiers from YAML for sync check
    yaml_game_ids = {get_game_identifier(game) for game in games}

    is_blood = registry == 'blood'

    for game in games:
        name = game['name']
        steam_id = game.get('steam_id')
        classification = game['classification']

        # For blood registry, map classification fields differently
        if is_blood:
            # Blood-specific fields
            vampirism = classification.get('vampirism')
            hemomancy = classification.get('hemomancy')
            vampirism_notes = game.get('vampirism_notes', '')
            hemomancy_notes = game.get('hemomancy_notes', '')
            # Shared fields with different YAML keys
            dimension_2 = classification.get('pov', 'character')  # POV
            dimension_4 = classification.get('availability', 'unknown')
            # Necromancy-specific fields not used
            dimension_1 = None
            dimension_3 = None
            dimension_1_notes = ''
            dimension_2_notes = game.get('pov_notes', '')
            dimension_3_notes = ''
            dimension_4_notes = game.get('availability_notes', '')
        else:
            # Necromancy registry (original behavior)
            dimension_1_notes = game.get('dimension_1_notes', '')
            dimension_2_notes = game.get('dimension_2_notes', '')
            dimension_3_notes = game.get('dimension_3_notes', '')
            dimension_4 = classification.get('dimension_4', 'unknown')
            dimension_4_notes = game.get('dimension_4_notes', '')
            dimension_1 = classification.get('dimension_1')
            dimension_2 = classification.get('dimension_2')
            dimension_3 = classification.get('dimension_3')
            # Blood-specific fields not used
            vampirism = None
            hemomancy = None
            vampirism_notes = ''
            hemomancy_notes = ''

        # Extract platform information
        platforms = game.get('platforms', ['steam'] if steam_id else ['manual'])
        primary_platform = game.get('primary_platform', 'steam' if steam_id else 'manual')
        battlenet_id = game.get('battlenet_id')
        battlenet_store_id = game.get('battlenet_store_id')  # Store page slug if different from API slug
        gog_id = game.get('gog_id')
        epic_id = game.get('epic_id')
        itchio_id = game.get('itchio_id')
        external_url = game.get('external_url')

        # Manual metadata for non-Steam games
        short_description = game.get('short_description')
        genres = game.get('genres', [])
        price_notes = game.get('price_notes')
        aliases = game.get('aliases', [])
        date_updated = game.get('date_updated')  # Manual override for last update date
        app_type = game.get('app_type')  # Manual app_type (e.g., 'mod')

        # Validate primary_platform
        if primary_platform not in VALID_PLATFORMS:
            print(f"⚠ Invalid primary_platform '{primary_platform}' for {name}, defaulting to steam")
            primary_platform = 'steam' if steam_id else 'manual'

        try:
            # Check if game already exists using multi-platform lookup
            existing = find_existing_game(cursor, game)

            if existing:
                db_id = existing[0]
                old_dim1, old_dim2, old_dim3, old_dim4 = existing[1:5]
                old_dim1_notes, old_dim2_notes, old_dim3_notes, old_dim4_notes = existing[5:9]
                old_platforms = existing[9]
                old_primary = existing[10]
                old_battlenet = existing[11]
                old_battlenet_store = existing[12]
                old_gog = existing[13]
                old_epic = existing[14]
                old_itchio = existing[15]
                old_aliases = existing[16]
                old_date_updated = existing[17]
                old_registry = existing[18] or 'necromancy'
                old_vampirism = existing[19]
                old_vampirism_notes = existing[20]
                old_hemomancy = existing[21]
                old_hemomancy_notes = existing[22]
                old_app_type = existing[23]

                # Check if this game exists in a different registry - upgrade to 'both'
                if old_registry != registry and old_registry != 'both':
                    new_registry = 'both'
                    registry_upgrade = True
                else:
                    new_registry = old_registry if old_registry == 'both' else registry
                    registry_upgrade = False

                if update_existing or registry_upgrade:
                    # For blood registry, use blood-specific classification
                    if is_blood:
                        new_vampirism = vampirism
                        new_hemomancy = hemomancy
                        new_vampirism_notes = vampirism_notes
                        new_hemomancy_notes = hemomancy_notes
                        # Keep existing necromancy dimensions
                        new_dim1 = old_dim1
                        new_dim2 = dimension_2  # POV is shared, update it
                        new_dim3 = old_dim3
                    else:
                        new_dim1 = dimension_1
                        new_dim2 = dimension_2
                        new_dim3 = dimension_3
                        # Keep existing blood dimensions
                        new_vampirism = old_vampirism
                        new_hemomancy = old_hemomancy
                        new_vampirism_notes = old_vampirism_notes or ''
                        new_hemomancy_notes = old_hemomancy_notes or ''

                    new_platforms_json = json.dumps(platforms)
                    new_aliases_json = json.dumps(aliases) if aliases else None

                    classification_changed = (
                        old_dim1 != new_dim1 or
                        old_dim2 != new_dim2 or
                        old_dim3 != new_dim3 or
                        old_dim4 != dimension_4 or
                        old_dim1_notes != dimension_1_notes or
                        old_dim2_notes != dimension_2_notes or
                        old_dim3_notes != dimension_3_notes or
                        old_dim4_notes != dimension_4_notes or
                        old_vampirism != new_vampirism or
                        old_hemomancy != new_hemomancy or
                        (old_vampirism_notes or '') != new_vampirism_notes or
                        (old_hemomancy_notes or '') != new_hemomancy_notes
                    )

                    platform_changed = (
                        old_platforms != new_platforms_json or
                        old_primary != primary_platform or
                        old_battlenet != battlenet_id or
                        old_battlenet_store != battlenet_store_id or
                        old_gog != gog_id or
                        old_epic != epic_id or
                        old_itchio != itchio_id
                    )

                    aliases_changed = old_aliases != new_aliases_json

                    # Normalize date_updated for comparison (handle both string and datetime)
                    old_date_str = str(old_date_updated)[:10] if old_date_updated else None
                    new_date_str = str(date_updated) if date_updated else None
                    date_updated_changed = old_date_str != new_date_str

                    app_type_changed = old_app_type != app_type

                    if classification_changed or platform_changed or aliases_changed or date_updated_changed or app_type_changed or registry_upgrade:
                        # Update classification, platform info, aliases, registry, and date_updated
                        cursor.execute("""
                            UPDATE games SET
                                dimension_1 = ?,
                                dimension_2 = ?,
                                dimension_3 = ?,
                                dimension_4 = ?,
                                dimension_1_notes = ?,
                                dimension_2_notes = ?,
                                dimension_3_notes = ?,
                                dimension_4_notes = ?,
                                registry = ?,
                                vampirism = ?,
                                vampirism_notes = ?,
                                hemomancy = ?,
                                hemomancy_notes = ?,
                                platforms = ?,
                                primary_platform = ?,
                                battlenet_id = ?,
                                battlenet_store_id = ?,
                                gog_id = ?,
                                epic_id = ?,
                                itchio_id = ?,
                                external_url = ?,
                                aliases = ?,
                                date_updated = ?,
                                app_type = ?
                            WHERE id = ?
                        """, (
                            new_dim1, new_dim2, new_dim3, dimension_4,
                            dimension_1_notes if not is_blood else old_dim1_notes,
                            dimension_2_notes,
                            dimension_3_notes if not is_blood else old_dim3_notes,
                            dimension_4_notes,
                            new_registry,
                            new_vampirism, new_vampirism_notes,
                            new_hemomancy, new_hemomancy_notes,
                            new_platforms_json, primary_platform,
                            battlenet_id, battlenet_store_id, gog_id, epic_id, itchio_id,
                            external_url, new_aliases_json, date_updated, app_type, db_id
                        ))

                        # Show what changed
                        changes = []
                        if registry_upgrade:
                            changes.append(f"registry: {old_registry}→{new_registry}")
                        if old_dim1 != new_dim1:
                            changes.append(f"dim1: {old_dim1}→{new_dim1}")
                        if old_dim2 != new_dim2:
                            changes.append(f"dim2: {old_dim2}→{new_dim2}")
                        if old_dim3 != new_dim3:
                            changes.append(f"dim3: {old_dim3}→{new_dim3}")
                        if old_dim4 != dimension_4:
                            changes.append(f"dim4: {old_dim4}→{dimension_4}")
                        if old_vampirism != new_vampirism:
                            changes.append(f"vampirism: {old_vampirism}→{new_vampirism}")
                        if old_hemomancy != new_hemomancy:
                            changes.append(f"hemomancy: {old_hemomancy}→{new_hemomancy}")
                        if platform_changed:
                            changes.append("platforms")
                        if aliases_changed:
                            changes.append("aliases")
                        if date_updated_changed:
                            changes.append(f"date_updated: {old_date_str}→{new_date_str}")

                        print(f"↻ Updated: {name} ({', '.join(changes)})")
                        updated += 1
                    else:
                        skipped += 1
                else:
                    skipped += 1
                continue

            # Add new game with full platform support
            cursor.execute("""
                INSERT INTO games
                (steam_id, battlenet_id, battlenet_store_id, gog_id, epic_id, itchio_id,
                 platforms, primary_platform, external_url,
                 name, dimension_1, dimension_2, dimension_3, dimension_4,
                 dimension_1_notes, dimension_2_notes, dimension_3_notes, dimension_4_notes,
                 registry, vampirism, vampirism_notes, hemomancy, hemomancy_notes,
                 short_description, genres, price_notes, aliases, date_updated, app_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                steam_id,
                battlenet_id,
                battlenet_store_id,
                gog_id,
                epic_id,
                itchio_id,
                json.dumps(platforms),
                primary_platform,
                external_url,
                name,
                dimension_1,
                dimension_2,
                dimension_3,
                dimension_4,
                dimension_1_notes,
                dimension_2_notes,
                dimension_3_notes,
                dimension_4_notes,
                registry,
                vampirism,
                vampirism_notes,
                hemomancy,
                hemomancy_notes,
                short_description,
                json.dumps(genres) if genres else None,
                price_notes,
                json.dumps(aliases) if aliases else None,
                date_updated,  # Use YAML value if present, otherwise None
                app_type  # Manual app_type (e.g., 'mod')
            ))

            # Get the newly inserted game's ID
            game_id = cursor.lastrowid

            # Track for API fetch based on primary platform
            if primary_platform == 'steam' and steam_id:
                newly_added_games.append(('steam', game_id, steam_id, name))
            elif primary_platform == 'battlenet' and battlenet_id:
                newly_added_games.append(('battlenet', game_id, battlenet_id, name))
            # Other platforms would be added here as we implement their APIs

            platform_str = f"[{', '.join(platforms)}]" if len(platforms) > 1 else platforms[0]
            if is_blood:
                print(f"✓ Added: {name} ({vampirism}, {hemomancy}, {dimension_2}) - {platform_str} [blood]")
            else:
                print(f"✓ Added: {name} ({dimension_1}, {dimension_2}, {dimension_3}) - {platform_str}")
            added += 1

        except Exception as e:
            print(f"✗ Error processing {name}: {e}")
            import traceback
            traceback.print_exc()
            errors += 1

    # Delete games that are in DB but not in YAML (if sync mode)
    # Only delete games that belong to this registry (not games from other registries)
    if sync_deletes:
        print()
        print(f"Checking for {registry} games to remove...")

        # Only consider games that belong to this registry
        # - For necromancy: registry IS NULL, 'necromancy', or 'both'
        # - For blood: registry is 'blood' or 'both'
        if registry == 'necromancy':
            registry_filter = "COALESCE(registry, 'necromancy') IN ('necromancy', 'both')"
        else:
            registry_filter = "registry IN ('blood', 'both')"

        cursor.execute(f"""
            SELECT id, steam_id, battlenet_id, gog_id, epic_id, itchio_id,
                   name, primary_platform, registry
            FROM games
            WHERE {registry_filter}
        """)
        db_games = cursor.fetchall()

        for row in db_games:
            db_id, steam_id, battlenet_id, gog_id, epic_id, itchio_id, name, primary_platform, db_registry = row

            # Build identifier for this DB game
            if steam_id:
                db_identifier = f"steam:{steam_id}"
            elif battlenet_id:
                db_identifier = f"battlenet:{battlenet_id}"
            elif gog_id:
                db_identifier = f"gog:{gog_id}"
            elif epic_id:
                db_identifier = f"epic:{epic_id}"
            elif itchio_id:
                db_identifier = f"itchio:{itchio_id}"
            else:
                db_identifier = f"name:{name}"

            if db_identifier not in yaml_game_ids:
                try:
                    # If game is in 'both' registries, downgrade to the other registry instead of deleting
                    if db_registry == 'both':
                        other_registry = 'blood' if registry == 'necromancy' else 'necromancy'
                        cursor.execute(
                            "UPDATE games SET registry = ? WHERE id = ?",
                            (other_registry, db_id)
                        )
                        print(f"↓ Downgraded: {name} (removed from {registry}, kept in {other_registry})")
                        updated += 1
                        continue

                    # Get update count before deletion
                    cursor.execute(
                        "SELECT COUNT(*) FROM updates WHERE game_id = ?",
                        (db_id,)
                    )
                    update_count = cursor.fetchone()[0]

                    # Delete game (CASCADE will delete updates automatically)
                    cursor.execute("DELETE FROM games WHERE id = ?", (db_id,))

                    print(f"🗑  Deleted: {name} ({db_identifier}, {update_count} updates)")
                    deleted += 1

                except Exception as e:
                    print(f"✗ Error deleting {name}: {e}")
                    errors += 1

    # Fetch details and initial updates for newly added games
    if newly_added_games:
        print()

        # Group by platform
        steam_games = [(g[1], g[2], g[3]) for g in newly_added_games if g[0] == 'steam']
        battlenet_games = [(g[1], g[2], g[3]) for g in newly_added_games if g[0] == 'battlenet']

        if steam_games:
            print(f"Fetching Steam data for {len(steam_games)} new games...")
            steam_api = SteamAPI()

            for game_id, steam_id, name in steam_games:
                # Fetch game details (description, images, etc.)
                if fetch_steam_details(game_id, steam_id, name, steam_api, cursor):
                    details_fetched += 1
                else:
                    details_failed += 1

                # Fetch initial updates (uses higher count to capture Last Updated date)
                updates_fetched += fetch_initial_updates(game_id, steam_id, name, steam_api, cursor)

        if battlenet_games:
            print(f"Battle.net games ({len(battlenet_games)}) - API integration pending")
            # TODO: Implement Battle.net API fetching when available

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

  # Load blood registry games
  python scripts/load_games_from_yaml.py --blood

  # Load blood games with update
  python scripts/load_games_from_yaml.py --blood --update

Use --update when you've changed classifications in games_list.yaml.
Use --sync to remove games from DB that aren't in the YAML file.
Use --blood to load from blood_games_list.yaml instead of games_list.yaml.
WARNING: --sync will DELETE games and all their updates!
        """
    )
    
    parser.add_argument('--yaml', default=None,
                       help='Path to games YAML file (default: auto-detect based on registry)')
    parser.add_argument('-u', '--update', action='store_true',
                       help='Update existing games (not just add new ones)')
    parser.add_argument('-s', '--sync', action='store_true',
                       help='Delete games from DB that are not in YAML (destructive!)')
    parser.add_argument('-b', '--blood', action='store_true',
                       help='Load blood registry games from blood_games_list.yaml')

    args = parser.parse_args()

    # Determine registry and yaml path
    registry = 'blood' if args.blood else 'necromancy'
    if args.yaml:
        yaml_path = args.yaml
    else:
        yaml_path = 'data/blood_games_list.yaml' if args.blood else 'data/games_list.yaml'

    print("=" * 60)
    print(f"Loading games from {yaml_path}")
    print(f"Registry: {registry}")
    print("=" * 60)
    print()

    try:
        count = load_games_from_yaml(yaml_path, args.update, args.sync, registry)
        return 0 if count >= 0 else 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
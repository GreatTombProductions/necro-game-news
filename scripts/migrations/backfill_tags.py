#!/usr/bin/env python3
"""
Migration script to backfill Steam tags for existing games.

This script fetches tags from Steamspy for all games that don't have tags yet.

Usage:
    python scripts/migrations/backfill_tags.py
    python scripts/migrations/backfill_tags.py --force  # Re-fetch even if tags exist
"""

import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.scrapers.steam_api import SteamAPI
from backend.database.schema import get_connection

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def backfill_tags(force: bool = False):
    """
    Backfill tags for all games in the database.

    Args:
        force: If True, re-fetch tags even if they already exist
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Get all active games
    if force:
        query = """
            SELECT id, name, steam_id
            FROM games
            WHERE is_active = 1
            ORDER BY name
        """
    else:
        query = """
            SELECT id, name, steam_id
            FROM games
            WHERE is_active = 1
            AND (steam_tags IS NULL OR steam_tags = '' OR steam_tags = '[]')
            ORDER BY name
        """

    cursor.execute(query)
    games = cursor.fetchall()
    conn.close()

    if not games:
        logger.info("No games need tag backfilling")
        return

    logger.info(f"Backfilling tags for {len(games)} games...")
    print()

    steam_api = SteamAPI()
    success_count = 0
    fail_count = 0

    for db_id, name, steam_id in games:
        try:
            logger.info(f"Fetching tags for: {name} (Steam ID: {steam_id})")

            # Fetch tags from Steamspy
            tags = steam_api.get_app_tags(steam_id, max_tags=10)

            if tags:
                # Update database
                conn = get_connection()
                cursor = conn.cursor()

                cursor.execute("""
                    UPDATE games
                    SET steam_tags = ?,
                        last_checked = ?
                    WHERE id = ?
                """, (
                    json.dumps(tags),
                    datetime.now(),
                    db_id
                ))

                conn.commit()
                conn.close()

                logger.info(f"  ✓ Updated with {len(tags)} tags: {', '.join(tags[:3])}...")
                success_count += 1
            else:
                logger.warning(f"  ✗ No tags found for {name}")
                fail_count += 1

        except Exception as e:
            logger.error(f"  ✗ Error fetching tags for {name}: {e}")
            fail_count += 1

    print()
    print("=" * 60)
    print("Migration Summary:")
    print(f"  ✓ Successfully updated: {success_count}")
    print(f"  ✗ Failed: {fail_count}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Backfill Steam tags for existing games'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Re-fetch tags even if they already exist'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Backfilling Steam Tags from Steamspy")
    print("=" * 60)
    print()

    backfill_tags(force=args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())

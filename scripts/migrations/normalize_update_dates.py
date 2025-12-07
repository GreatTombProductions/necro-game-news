#!/usr/bin/env python3
"""
Migration script to normalize date formats in the updates table.

Previously, Battle.net updates used ISO 8601 format (2025-11-21T18:00:00+00:00)
while Steam updates used simple format (2025-11-21 18:00:00). This caused
sorting issues on the frontend.

This script normalizes all dates to: YYYY-MM-DD HH:MM:SS

Usage:
    python scripts/migrations/normalize_update_dates.py
    python scripts/migrations/normalize_update_dates.py --dry-run  # Preview changes
"""

import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database.schema import get_connection

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def normalize_date(date_str: str) -> str:
    """
    Convert various date formats to YYYY-MM-DD HH:MM:SS.

    Handles:
    - ISO 8601: 2025-11-21T18:00:00+00:00
    - Simple: 2025-11-21 18:00:00 (no change needed)
    """
    if not date_str:
        return date_str

    # Already in correct format
    if len(date_str) == 19 and 'T' not in date_str:
        return date_str

    # ISO 8601 format with T and timezone
    if 'T' in date_str:
        try:
            # Parse ISO format
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            pass

    return date_str


def migrate_dates(dry_run: bool = False):
    """
    Normalize all date formats in the updates table.

    Args:
        dry_run: If True, only show what would change without updating
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Find all updates with ISO 8601 format dates (contain 'T')
    cursor.execute("""
        SELECT id, date, title
        FROM updates
        WHERE date LIKE '%T%'
        ORDER BY id
    """)

    updates = cursor.fetchall()

    if not updates:
        logger.info("No dates need normalization - all dates are already in correct format")
        conn.close()
        return

    logger.info(f"Found {len(updates)} updates with ISO 8601 date format")
    print()

    updated_count = 0
    error_count = 0

    for update_id, old_date, title in updates:
        new_date = normalize_date(old_date)

        if new_date != old_date:
            if dry_run:
                logger.info(f"  Would update #{update_id}: {old_date} -> {new_date} ({title[:40]}...)")
            else:
                try:
                    cursor.execute("""
                        UPDATE updates SET date = ? WHERE id = ?
                    """, (new_date, update_id))
                    logger.info(f"  Updated #{update_id}: {old_date} -> {new_date}")
                    updated_count += 1
                except Exception as e:
                    logger.error(f"  Failed to update #{update_id}: {e}")
                    error_count += 1

    if not dry_run:
        conn.commit()

    conn.close()

    print()
    print("=" * 60)
    if dry_run:
        print(f"Dry run complete - {len(updates)} updates would be normalized")
    else:
        print("Migration Summary:")
        print(f"  ✓ Successfully updated: {updated_count}")
        if error_count > 0:
            print(f"  ✗ Failed: {error_count}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Normalize date formats in updates table'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without updating database'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Normalizing Update Date Formats")
    print("=" * 60)
    print()

    migrate_dates(dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())

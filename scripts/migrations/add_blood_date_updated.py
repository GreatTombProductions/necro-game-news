#!/usr/bin/env python3
"""
Migration: Add blood_date_updated column

Adds a separate date_updated column for blood registry games:
- blood_date_updated: Date blood entry was last updated (independent from necromancy date_updated)

This allows necromancy and blood registries to track their own update dates independently.
"""

import sqlite3
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database.schema import get_db_path


def migrate():
    db_path = get_db_path()
    print(f"Migrating database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check current schema
    cursor.execute("PRAGMA table_info(games)")
    columns = {row[1] for row in cursor.fetchall()}
    print(f"Current columns: {sorted(columns)}")

    changes_made = []

    # Add blood_date_updated column
    if 'blood_date_updated' not in columns:
        print("Adding blood_date_updated column...")
        cursor.execute("ALTER TABLE games ADD COLUMN blood_date_updated TIMESTAMP")
        changes_made.append("Added blood_date_updated column")
    else:
        print("blood_date_updated already exists, skipping")

    conn.commit()

    # Verify changes
    cursor.execute("PRAGMA table_info(games)")
    new_columns = {row[1] for row in cursor.fetchall()}
    print(f"\nNew columns: {sorted(new_columns)}")

    conn.close()

    if changes_made:
        print(f"\n✓ Migration complete! Changes made:")
        for change in changes_made:
            print(f"  - {change}")
    else:
        print("\n✓ No changes needed - schema already up to date")

    return True


if __name__ == "__main__":
    migrate()

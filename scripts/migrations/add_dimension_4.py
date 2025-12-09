#!/usr/bin/env python3
"""
Migration: Add dimension_4 (Availability) column

Options:
- instant: necromancer/necromancy available immediately
- gated: necromancer/necromancy takes time to unlock
- unknown: default if not specified
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

    # 1. Add dimension_4 column with default 'unknown'
    if 'dimension_4' not in columns:
        print("Adding dimension_4 column...")
        cursor.execute("ALTER TABLE games ADD COLUMN dimension_4 TEXT DEFAULT 'unknown' CHECK(dimension_4 IN ('instant', 'gated', 'unknown'))")
        changes_made.append("Added dimension_4 column")
    else:
        print("dimension_4 already exists, skipping")

    # 2. Add dimension_4_notes column
    if 'dimension_4_notes' not in columns:
        print("Adding dimension_4_notes column...")
        cursor.execute("ALTER TABLE games ADD COLUMN dimension_4_notes TEXT")
        changes_made.append("Added dimension_4_notes column")
    else:
        print("dimension_4_notes already exists, skipping")

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

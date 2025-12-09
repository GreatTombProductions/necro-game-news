#!/usr/bin/env python3
"""
Migration: Add dimension notes columns and rename fields

Changes:
- Rename classification_notes -> dimension_1_notes
- Add dimension_2_notes column
- Add dimension_3_notes column
- Rename date_added -> date_updated
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

    # 1. Rename classification_notes -> dimension_1_notes
    if 'classification_notes' in columns and 'dimension_1_notes' not in columns:
        print("Renaming classification_notes -> dimension_1_notes...")
        cursor.execute("ALTER TABLE games RENAME COLUMN classification_notes TO dimension_1_notes")
        changes_made.append("Renamed classification_notes -> dimension_1_notes")
    elif 'dimension_1_notes' in columns:
        print("dimension_1_notes already exists, skipping rename")

    # 2. Add dimension_2_notes column
    if 'dimension_2_notes' not in columns:
        print("Adding dimension_2_notes column...")
        cursor.execute("ALTER TABLE games ADD COLUMN dimension_2_notes TEXT")
        changes_made.append("Added dimension_2_notes column")
    else:
        print("dimension_2_notes already exists, skipping")

    # 3. Add dimension_3_notes column
    if 'dimension_3_notes' not in columns:
        print("Adding dimension_3_notes column...")
        cursor.execute("ALTER TABLE games ADD COLUMN dimension_3_notes TEXT")
        changes_made.append("Added dimension_3_notes column")
    else:
        print("dimension_3_notes already exists, skipping")

    # 4. Rename date_added -> date_updated
    if 'date_added' in columns and 'date_updated' not in columns:
        print("Renaming date_added -> date_updated...")
        cursor.execute("ALTER TABLE games RENAME COLUMN date_added TO date_updated")
        changes_made.append("Renamed date_added -> date_updated")
    elif 'date_updated' in columns:
        print("date_updated already exists, skipping rename")

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

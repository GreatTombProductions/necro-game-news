#!/usr/bin/env python3
"""
Migration: Add blood registry support

Adds columns for blood/vampire game classification:
- registry: which registry the game belongs to ('necromancy', 'blood', 'both')
- vampirism: ontological status ('outright', 'implied', 'absent')
- vampirism_notes: editorial notes for vampirism
- hemomancy: blood magic centrality ('a', 'b', 'c', 'd', 'absent')
- hemomancy_notes: editorial notes for hemomancy
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

    # 1. Add registry column with default 'necromancy'
    if 'registry' not in columns:
        print("Adding registry column...")
        cursor.execute("""
            ALTER TABLE games ADD COLUMN registry TEXT DEFAULT 'necromancy'
            CHECK(registry IN ('necromancy', 'blood', 'both'))
        """)
        changes_made.append("Added registry column")
    else:
        print("registry already exists, skipping")

    # 2. Add vampirism column
    if 'vampirism' not in columns:
        print("Adding vampirism column...")
        cursor.execute("""
            ALTER TABLE games ADD COLUMN vampirism TEXT
            CHECK(vampirism IN ('outright', 'implied', 'absent'))
        """)
        changes_made.append("Added vampirism column")
    else:
        print("vampirism already exists, skipping")

    # 3. Add vampirism_notes column
    if 'vampirism_notes' not in columns:
        print("Adding vampirism_notes column...")
        cursor.execute("ALTER TABLE games ADD COLUMN vampirism_notes TEXT")
        changes_made.append("Added vampirism_notes column")
    else:
        print("vampirism_notes already exists, skipping")

    # 4. Add hemomancy column
    if 'hemomancy' not in columns:
        print("Adding hemomancy column...")
        cursor.execute("""
            ALTER TABLE games ADD COLUMN hemomancy TEXT
            CHECK(hemomancy IN ('a', 'b', 'c', 'd', 'absent'))
        """)
        changes_made.append("Added hemomancy column")
    else:
        print("hemomancy already exists, skipping")

    # 5. Add hemomancy_notes column
    if 'hemomancy_notes' not in columns:
        print("Adding hemomancy_notes column...")
        cursor.execute("ALTER TABLE games ADD COLUMN hemomancy_notes TEXT")
        changes_made.append("Added hemomancy_notes column")
    else:
        print("hemomancy_notes already exists, skipping")

    conn.commit()

    # Verify changes
    cursor.execute("PRAGMA table_info(games)")
    new_columns = {row[1] for row in cursor.fetchall()}
    print(f"\nNew columns: {sorted(new_columns)}")

    conn.close()

    if changes_made:
        print("\n✓ Migration complete! Changes made:")
        for change in changes_made:
            print(f"  - {change}")
    else:
        print("\n✓ No changes needed - schema already up to date")

    return True


if __name__ == "__main__":
    migrate()

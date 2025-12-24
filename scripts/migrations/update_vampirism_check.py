#!/usr/bin/env python3
"""
Migration: Update vampirism CHECK constraint to include 'channeled'

SQLite doesn't allow modifying CHECK constraints, so we need to recreate the table.
This migration:
1. Creates a new games table with the updated CHECK constraint
2. Copies all data from the old table
3. Drops the old table
4. Renames the new table
5. Recreates indexes
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

    # Check if 'channeled' is already accepted (test by trying to insert/update)
    # First, let's check the current schema
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='games'")
    result = cursor.fetchone()
    if result:
        schema = result[0]
        if "'channeled'" in schema:
            print("✓ 'channeled' already in CHECK constraint, no migration needed")
            conn.close()
            return True

    print("Recreating games table with updated vampirism CHECK constraint...")

    try:
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")

        # 1. Create new table with updated schema
        cursor.execute("""
            CREATE TABLE games_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                -- Platform identifiers (at least one should be set)
                steam_id INTEGER,
                battlenet_id TEXT,
                battlenet_store_id TEXT,
                gog_id TEXT,
                epic_id TEXT,
                itchio_id TEXT,

                -- Multi-platform metadata
                platforms TEXT DEFAULT '["steam"]',
                primary_platform TEXT DEFAULT 'steam' CHECK(primary_platform IN ('steam', 'battlenet', 'gog', 'epic', 'itchio', 'manual')),
                external_url TEXT,

                -- Game info
                name TEXT NOT NULL,
                app_type TEXT,
                short_description TEXT,
                header_image_url TEXT,

                -- Necromancy classification (NULL allowed for blood-only games)
                dimension_1 TEXT CHECK(dimension_1 IS NULL OR dimension_1 IN ('a', 'b', 'c', 'd')),
                dimension_2 TEXT CHECK(dimension_2 IS NULL OR dimension_2 IN ('character', 'unit')),
                dimension_3 TEXT CHECK(dimension_3 IS NULL OR dimension_3 IN ('explicit', 'implied')),
                dimension_4 TEXT DEFAULT 'unknown' CHECK(dimension_4 IS NULL OR dimension_4 IN ('instant', 'gated', 'unknown')),
                dimension_1_notes TEXT,
                dimension_2_notes TEXT,
                dimension_3_notes TEXT,
                dimension_4_notes TEXT,

                -- Blood registry classification (updated vampirism CHECK)
                registry TEXT DEFAULT 'necromancy' CHECK(registry IS NULL OR registry IN ('necromancy', 'blood', 'both')),
                vampirism TEXT CHECK(vampirism IS NULL OR vampirism IN ('outright', 'implied', 'channeled', 'absent')),
                vampirism_notes TEXT,
                hemomancy TEXT CHECK(hemomancy IS NULL OR hemomancy IN ('a', 'b', 'c', 'd', 'absent')),
                hemomancy_notes TEXT,

                -- Metadata
                steam_tags TEXT,
                genres TEXT,
                release_date TEXT,
                price_usd REAL,
                price_notes TEXT,
                developer TEXT,
                publisher TEXT,
                aliases TEXT,

                -- Tracking metadata
                date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_checked TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """)

        # 2. Copy all data from old table (explicitly list columns)
        cursor.execute("""
            INSERT INTO games_new (
                id, steam_id, battlenet_id, battlenet_store_id, gog_id, epic_id, itchio_id,
                platforms, primary_platform, external_url,
                name, app_type, short_description, header_image_url,
                dimension_1, dimension_2, dimension_3, dimension_4,
                dimension_1_notes, dimension_2_notes, dimension_3_notes, dimension_4_notes,
                registry, vampirism, vampirism_notes, hemomancy, hemomancy_notes,
                steam_tags, genres, release_date, price_usd, price_notes,
                developer, publisher, aliases,
                date_updated, last_checked, is_active
            )
            SELECT
                id, steam_id, battlenet_id, battlenet_store_id, gog_id, epic_id, itchio_id,
                platforms, primary_platform, external_url,
                name, app_type, short_description, header_image_url,
                dimension_1, dimension_2, dimension_3, dimension_4,
                dimension_1_notes, dimension_2_notes, dimension_3_notes, dimension_4_notes,
                registry, vampirism, vampirism_notes, hemomancy, hemomancy_notes,
                steam_tags, genres, release_date, price_usd, price_notes,
                developer, publisher, aliases,
                date_updated, last_checked, is_active
            FROM games
        """)

        rows_copied = cursor.rowcount
        print(f"  Copied {rows_copied} rows to new table")

        # 3. Drop old table
        cursor.execute("DROP TABLE games")
        print("  Dropped old games table")

        # 4. Rename new table
        cursor.execute("ALTER TABLE games_new RENAME TO games")
        print("  Renamed games_new to games")

        # 5. Recreate indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_active ON games(is_active)")
        print("  Recreated indexes")

        # Commit transaction
        conn.commit()
        print("\n✓ Migration complete! 'channeled' is now a valid vampirism value")

    except Exception as e:
        conn.rollback()
        print(f"\n✗ Migration failed: {e}")
        conn.close()
        return False

    conn.close()
    return True


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)

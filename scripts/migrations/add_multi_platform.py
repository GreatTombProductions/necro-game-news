#!/usr/bin/env python3
"""
Migration: Add multi-platform support to games table

Changes:
- Make steam_id nullable (for non-Steam games)
- Add platforms field (JSON array: ["steam", "battlenet", "gog", "epic", "itchio"])
- Add primary_platform field (where to fetch updates from)
- Add platform-specific IDs: battlenet_id, gog_id, epic_id, itchio_id
- Add external_url for manual store links
- Add source_platform to updates table (which platform the update came from)
"""

import sqlite3
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database.schema import get_db_path


def check_migration_needed(conn):
    """Check if migration is needed by looking for new columns"""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(games)")
    columns = [row[1] for row in cursor.fetchall()]
    return 'platforms' not in columns


def migrate_games_table(conn):
    """
    Migrate games table to support multi-platform.
    SQLite doesn't support modifying columns, so we recreate the table.
    """
    cursor = conn.cursor()

    print("Creating new games table with multi-platform support...")

    # Create new table with updated schema
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS games_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- Platform identifiers (at least one should be set)
            steam_id INTEGER,  -- Now nullable for non-Steam games
            battlenet_id TEXT,
            gog_id TEXT,
            epic_id TEXT,
            itchio_id TEXT,

            -- Multi-platform metadata
            platforms TEXT DEFAULT '["steam"]',  -- JSON array of platforms
            primary_platform TEXT DEFAULT 'steam' CHECK(primary_platform IN ('steam', 'battlenet', 'gog', 'epic', 'itchio', 'manual')),
            external_url TEXT,  -- Manual store link if needed

            -- Game info
            name TEXT NOT NULL,
            app_type TEXT,
            short_description TEXT,
            header_image_url TEXT,

            -- Necromancy classification
            dimension_1 TEXT CHECK(dimension_1 IN ('a', 'b', 'c', 'd')),
            dimension_2 TEXT CHECK(dimension_2 IN ('character', 'unit')),
            dimension_3 TEXT CHECK(dimension_3 IN ('explicit', 'implied')),
            classification_notes TEXT,

            -- Metadata (may come from various platforms)
            steam_tags TEXT,
            genres TEXT,
            release_date TEXT,
            price_usd REAL,
            developer TEXT,
            publisher TEXT,

            -- Tracking metadata
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_checked TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    """)

    # Copy data from old table
    print("Copying existing game data...")
    cursor.execute("""
        INSERT INTO games_new (
            id, steam_id, platforms, primary_platform,
            name, app_type, short_description, header_image_url,
            dimension_1, dimension_2, dimension_3, classification_notes,
            steam_tags, genres, release_date, price_usd, developer, publisher,
            date_added, last_checked, is_active
        )
        SELECT
            id, steam_id, '["steam"]', 'steam',
            name, app_type, short_description, header_image_url,
            dimension_1, dimension_2, dimension_3, classification_notes,
            steam_tags, genres, release_date, price_usd, developer, publisher,
            date_added, last_checked, is_active
        FROM games
    """)

    rows_migrated = cursor.rowcount

    # Drop old table and rename new one
    print("Replacing old table...")
    cursor.execute("DROP TABLE games")
    cursor.execute("ALTER TABLE games_new RENAME TO games")

    # Recreate index
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_active ON games(is_active)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_steam_id ON games(steam_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_primary_platform ON games(primary_platform)")

    print(f"✓ Migrated {rows_migrated} games to new schema")
    return rows_migrated


def migrate_updates_table(conn):
    """Add source_platform column to updates table"""
    cursor = conn.cursor()

    # Check if column exists
    cursor.execute("PRAGMA table_info(updates)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'source_platform' in columns:
        print("✓ Updates table already has source_platform column")
        return

    print("Adding source_platform column to updates table...")
    cursor.execute("""
        ALTER TABLE updates ADD COLUMN source_platform TEXT DEFAULT 'steam'
    """)

    # Update existing records
    cursor.execute("UPDATE updates SET source_platform = 'steam' WHERE source_platform IS NULL")

    print("✓ Added source_platform column to updates table")


def migrate_candidates_table(conn):
    """Add platform fields to candidates table"""
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(candidates)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'platform' in columns:
        print("✓ Candidates table already has platform column")
        return

    print("Adding platform column to candidates table...")
    cursor.execute("""
        ALTER TABLE candidates ADD COLUMN platform TEXT DEFAULT 'steam'
    """)
    cursor.execute("""
        ALTER TABLE candidates ADD COLUMN platform_id TEXT
    """)

    print("✓ Added platform columns to candidates table")


def run_migration():
    """Run the full migration"""
    db_path = get_db_path()

    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        print("Run 'python scripts/init_database.py' first.")
        sys.exit(1)

    print(f"Migrating database at: {db_path}")
    print("-" * 50)

    conn = sqlite3.connect(db_path)

    try:
        if not check_migration_needed(conn):
            print("✓ Migration already applied - no changes needed")
            conn.close()
            return

        # Run migrations
        migrate_games_table(conn)
        migrate_updates_table(conn)
        migrate_candidates_table(conn)

        conn.commit()
        print("-" * 50)
        print("✓ Migration completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run_migration()
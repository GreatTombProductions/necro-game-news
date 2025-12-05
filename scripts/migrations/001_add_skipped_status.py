#!/usr/bin/env python3
"""
Migration: Add 'skipped' status to candidates table.

This recreates the candidates table with the updated CHECK constraint.
"""

import sqlite3
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database.schema import get_db_path

def migrate():
    """Migrate the candidates table to include 'skipped' status."""
    db_path = get_db_path()

    print(f"Migrating database at: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")

        # Create new table with updated constraint
        cursor.execute("""
            CREATE TABLE candidates_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                steam_id INTEGER,
                game_name TEXT NOT NULL,
                source TEXT CHECK(source IN ('user_submission', 'auto_discovery', 'manual')),
                submitter_contact TEXT,
                justification TEXT,
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected', 'skipped')),

                -- Review information
                reviewed_by TEXT,
                review_date TIMESTAMP,
                review_notes TEXT,

                date_submitted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(steam_id)
            )
        """)

        # Copy data from old table to new table
        cursor.execute("""
            INSERT INTO candidates_new
            SELECT * FROM candidates
        """)

        # Drop old table
        cursor.execute("DROP TABLE candidates")

        # Rename new table to original name
        cursor.execute("ALTER TABLE candidates_new RENAME TO candidates")

        # Recreate index
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status)
        """)

        # Commit transaction
        conn.commit()

        print("✓ Migration successful!")
        print("  - Added 'skipped' status to candidates table")
        print("  - All existing data preserved")

    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        print("  Database rolled back to previous state")
        raise

    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
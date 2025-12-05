"""
Migration: Add price_usd field to games table

Run this to add the price_usd column to existing databases.
"""

import sqlite3
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database.schema import get_db_path


def migrate():
    """Add price_usd column to games table"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if column already exists
    cursor.execute("PRAGMA table_info(games)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'price_usd' in columns:
        print("✓ price_usd column already exists")
        conn.close()
        return

    # Add the column
    print("Adding price_usd column to games table...")
    cursor.execute("""
        ALTER TABLE games
        ADD COLUMN price_usd REAL
    """)

    conn.commit()
    conn.close()

    print("✓ Migration complete: price_usd column added")
    print("  Note: Run fetch_game_details.py to populate price data")


if __name__ == "__main__":
    migrate()
#!/usr/bin/env python3
"""
Initialize the Necro Game News database.

This script creates the SQLite database with all required tables.
Run this once during initial setup.

Usage:
    python scripts/init_database.py
"""

import sys
from pathlib import Path

# Add backend to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.schema import create_database, verify_schema


def main():
    """Initialize the database"""
    print("=" * 60)
    print("Necro Game News - Database Initialization")
    print("=" * 60)
    print()
    
    try:
        # Create database
        db_path = create_database()
        
        # Verify schema
        print()
        if verify_schema(db_path):
            print()
            print("=" * 60)
            print("✓ Database initialization complete!")
            print("=" * 60)
            print()
            print("Next steps:")
            print("  1. Get a Steam API key: https://steamcommunity.com/dev/apikey")
            print("  2. Add it to .env file")
            print("  3. Add your first game: python scripts/add_game.py --help")
            return 0
        else:
            print("\n⚠ Database created but schema verification failed")
            return 1
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

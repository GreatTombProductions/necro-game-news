#!/usr/bin/env python3
"""
Load games from games_list.yaml into the database.

This script reads the curated games list and adds any new games
to the database. It skips games that already exist.

Usage:
    python scripts/load_games_from_yaml.py
"""

import sys
import yaml
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.schema import get_connection


def load_games_from_yaml(yaml_path='data/games_list.yaml'):
    """
    Load games from YAML file and add to database.
    
    Args:
        yaml_path: Path to games_list.yaml file
    """
    yaml_file = Path(yaml_path)
    
    if not yaml_file.exists():
        print(f"✗ Games list not found: {yaml_path}")
        return 0
    
    # Read YAML
    with open(yaml_file, 'r') as f:
        data = yaml.safe_load(f)
    
    games = data.get('games', [])
    
    if not games:
        print("✗ No games found in YAML file")
        return 0
    
    print(f"Found {len(games)} games in {yaml_path}")
    print()
    
    # Connect to database
    conn = get_connection()
    cursor = conn.cursor()
    
    added = 0
    skipped = 0
    errors = 0
    
    for game in games:
        name = game['name']
        steam_id = game['steam_id']
        classification = game['classification']
        notes = game.get('notes', '')
        
        try:
            # Check if game already exists
            cursor.execute(
                "SELECT id FROM games WHERE steam_id = ?",
                (steam_id,)
            )
            
            if cursor.fetchone():
                print(f"⊙ Skipped (already exists): {name}")
                skipped += 1
                continue
            
            # Add game
            cursor.execute("""
                INSERT INTO games 
                (steam_id, name, dimension_1, dimension_2, dimension_3, 
                 classification_notes, date_added)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                steam_id,
                name,
                classification['dimension_1'],
                classification['dimension_2'],
                classification['dimension_3'],
                notes,
                datetime.now()
            ))
            
            print(f"✓ Added: {name} ({classification['dimension_1']}, "
                  f"{classification['dimension_2']}, {classification['dimension_3']})")
            added += 1
            
        except Exception as e:
            print(f"✗ Error adding {name}: {e}")
            errors += 1
    
    conn.commit()
    conn.close()
    
    # Summary
    print()
    print("=" * 60)
    print(f"Summary:")
    print(f"  ✓ Added: {added}")
    print(f"  ⊙ Skipped (existing): {skipped}")
    print(f"  ✗ Errors: {errors}")
    print("=" * 60)
    
    return added


def main():
    """Main entry point"""
    print("=" * 60)
    print("Loading games from games_list.yaml")
    print("=" * 60)
    print()
    
    try:
        added = load_games_from_yaml()
        return 0 if added >= 0 else 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Load games from games_list.yaml into the database.

This script reads the curated games list and adds any new games
to the database. With --update flag, it also updates classification
for existing games.

Usage:
    python scripts/load_games_from_yaml.py              # Add new games only
    python scripts/load_games_from_yaml.py --update     # Add new + update existing
"""

import sys
import yaml
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.schema import get_connection


def load_games_from_yaml(yaml_path='data/games_list.yaml', update_existing=False):
    """
    Load games from YAML file and add/update in database.
    
    Args:
        yaml_path: Path to games_list.yaml file
        update_existing: If True, update classification for existing games
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
    if update_existing:
        print("Mode: Add new games + update existing classifications")
    else:
        print("Mode: Add new games only (use --update to sync changes)")
    print()
    
    # Connect to database
    conn = get_connection()
    cursor = conn.cursor()
    
    added = 0
    updated = 0
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
                "SELECT id, dimension_1, dimension_2, dimension_3, classification_notes FROM games WHERE steam_id = ?",
                (steam_id,)
            )
            
            existing = cursor.fetchone()
            
            if existing:
                if update_existing:
                    # Check if classification changed
                    db_id, old_dim1, old_dim2, old_dim3, old_notes = existing
                    new_dim1 = classification['dimension_1']
                    new_dim2 = classification['dimension_2']
                    new_dim3 = classification['dimension_3']
                    
                    if (old_dim1 != new_dim1 or 
                        old_dim2 != new_dim2 or 
                        old_dim3 != new_dim3 or
                        old_notes != notes):
                        
                        # Update classification
                        cursor.execute("""
                            UPDATE games SET
                                dimension_1 = ?,
                                dimension_2 = ?,
                                dimension_3 = ?,
                                classification_notes = ?
                            WHERE id = ?
                        """, (new_dim1, new_dim2, new_dim3, notes, db_id))
                        
                        # Show what changed
                        changes = []
                        if old_dim1 != new_dim1:
                            changes.append(f"dim1: {old_dim1}→{new_dim1}")
                        if old_dim2 != new_dim2:
                            changes.append(f"dim2: {old_dim2}→{new_dim2}")
                        if old_dim3 != new_dim3:
                            changes.append(f"dim3: {old_dim3}→{new_dim3}")
                        if old_notes != notes:
                            changes.append("notes updated")
                        
                        print(f"↻ Updated: {name} ({', '.join(changes)})")
                        updated += 1
                    else:
                        print(f"⊙ Unchanged: {name}")
                        skipped += 1
                else:
                    print(f"⊙ Skipped (already exists): {name}")
                    skipped += 1
                continue
            
            # Add new game
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
            print(f"✗ Error processing {name}: {e}")
            errors += 1
    
    conn.commit()
    conn.close()
    
    # Summary
    print()
    print("=" * 60)
    print(f"Summary:")
    print(f"  ✓ Added: {added}")
    if update_existing:
        print(f"  ↻ Updated: {updated}")
    print(f"  ⊙ Skipped (unchanged): {skipped}")
    print(f"  ✗ Errors: {errors}")
    print("=" * 60)
    
    return added + updated


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Load games from YAML into database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add new games only (default)
  python scripts/load_games_from_yaml.py
  
  # Add new games AND update existing classifications
  python scripts/load_games_from_yaml.py --update
  
Use --update when you've changed classifications in games_list.yaml
and want to sync those changes to the database.
        """
    )
    
    parser.add_argument('--yaml', default='data/games_list.yaml',
                       help='Path to games YAML file (default: data/games_list.yaml)')
    parser.add_argument('--update', action='store_true',
                       help='Update existing games (not just add new ones)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Loading games from games_list.yaml")
    print("=" * 60)
    print()
    
    try:
        count = load_games_from_yaml(args.yaml, args.update)
        return 0 if count >= 0 else 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Add a game to the Necro Game News database.

This script allows manual addition of games with their necromancy classification.

Usage:
    python scripts/add_game.py --steam-id 2344520 --dim1 a --dim2 character --dim3 explicit --notes "Necromancer class"
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.schema import get_connection


def add_game(steam_id, name, dim1, dim2, dim3, notes=None):
    """
    Add a game to the database.
    
    Args:
        steam_id: Steam app ID
        name: Game name
        dim1: Dimension 1 classification (a/b/c/d)
        dim2: Dimension 2 classification (character/unit)
        dim3: Dimension 3 classification (explicit/implied)
        notes: Optional classification notes/justification
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO games 
            (steam_id, name, dimension_1, dimension_2, dimension_3, 
             classification_notes, date_added)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            steam_id,
            name,
            dim1,
            dim2,
            dim3,
            notes,
            datetime.now()
        ))
        
        conn.commit()
        game_id = cursor.lastrowid
        
        print(f"✓ Added game: {name}")
        print(f"  Steam ID: {steam_id}")
        print(f"  Classification: 1{dim1}, 2{dim2[0]}, 3{dim3[0]}")
        print(f"  Database ID: {game_id}")
        
        if notes:
            print(f"  Notes: {notes}")
        
        return game_id
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error adding game: {e}")
        if "UNIQUE constraint failed: games.steam_id" in str(e):
            print(f"  Game with Steam ID {steam_id} already exists in database")
        return None
        
    finally:
        conn.close()


def validate_dimensions(dim1, dim2, dim3):
    """Validate dimension values"""
    valid_dim1 = ['a', 'b', 'c', 'd']
    valid_dim2 = ['character', 'unit']
    valid_dim3 = ['explicit', 'implied']
    
    errors = []
    
    if dim1 not in valid_dim1:
        errors.append(f"Dimension 1 must be one of: {', '.join(valid_dim1)}")
    
    if dim2 not in valid_dim2:
        errors.append(f"Dimension 2 must be one of: {', '.join(valid_dim2)}")
    
    if dim3 not in valid_dim3:
        errors.append(f"Dimension 3 must be one of: {', '.join(valid_dim3)}")
    
    return errors


def main():
    parser = argparse.ArgumentParser(
        description='Add a game to the Necro Game News database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Diablo IV - Core necromancer class
  python scripts/add_game.py --steam-id 2344520 --name "Diablo IV" --dim1 a --dim2 character --dim3 explicit --notes "Necromancer playable class"
  
  # V Rising - Necromantic specialization
  python scripts/add_game.py --steam-id 1604030 --name "V Rising" --dim1 b --dim2 character --dim3 implied --notes "Unholy spell school"
  
  # Warcraft 3 - Necromancer units in RTS
  python scripts/add_game.py --steam-id 0 --name "Warcraft III" --dim1 a --dim2 unit --dim3 explicit --notes "Undead faction necromancers"

Classification Guide:
  Dimension 1 (Centrality): a=Core identity, b=Specialization, c=Isolated features, d=Flavor only
  Dimension 2 (POV): character=Play as necromancer, unit=Control necromancer units
  Dimension 3 (Naming): explicit=Called "necromancer", implied=Death magic without term
        """
    )
    
    parser.add_argument('--steam-id', type=int, required=True,
                       help='Steam App ID')
    parser.add_argument('--name', type=str, required=True,
                       help='Game name')
    parser.add_argument('--dim1', choices=['a', 'b', 'c', 'd'], required=True,
                       help='Dimension 1: Centrality (a=core, b=spec, c=isolated, d=flavor)')
    parser.add_argument('--dim2', choices=['character', 'unit'], required=True,
                       help='Dimension 2: POV (character/unit)')
    parser.add_argument('--dim3', choices=['explicit', 'implied'], required=True,
                       help='Dimension 3: Naming (explicit/implied)')
    parser.add_argument('--notes', type=str, default=None,
                       help='Classification notes/justification')
    
    args = parser.parse_args()
    
    # Validate
    errors = validate_dimensions(args.dim1, args.dim2, args.dim3)
    if errors:
        print("Validation errors:")
        for error in errors:
            print(f"  ✗ {error}")
        return 1
    
    # Add game
    game_id = add_game(
        args.steam_id,
        args.name,
        args.dim1,
        args.dim2,
        args.dim3,
        args.notes
    )
    
    return 0 if game_id else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Interactive CLI for reclassifying update types.

Usage:
    python scripts/reclassify_update.py
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.schema import get_connection

# Classification types
CLASSIFICATIONS = {
    'p': 'patch',
    'r': 'release',
    'd': 'dlc',
    'a': 'announcement',
    'e': 'event',
}


def show_update(cursor, update_id: int) -> bool:
    """Show details of an update. Returns True if found."""
    cursor.execute("""
        SELECT u.id, u.title, u.update_type, u.date, g.name
        FROM updates u
        JOIN games g ON u.game_id = g.id
        WHERE u.id = ?
    """, (update_id,))

    row = cursor.fetchone()
    if not row:
        print(f"\n  Update #{update_id} not found.")
        return False

    uid, title, current_type, date, game_name = row
    print(f"\n  Game: {game_name}")
    print(f"  Title: {title}")
    print(f"  Date: {date}")
    print(f"  Current type: {current_type}")
    return True


def main():
    print("=" * 60)
    print("Update Reclassification Tool")
    print("=" * 60)
    print("\nClassification types:")
    for key, value in CLASSIFICATIONS.items():
        print(f"  [{key}] {value}")
    print()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        while True:
            # Ask for update ID
            user_input = input("\nEnter update ID (or 'q' to quit): ").strip().lower()

            if user_input in ('q', 'quit', 'exit'):
                print("\nGoodbye!")
                break

            try:
                update_id = int(user_input)
            except ValueError:
                print("  Invalid input. Please enter a number or 'q' to quit.")
                continue

            # Show update details
            if not show_update(cursor, update_id):
                continue

            # Ask for new classification
            new_type_input = input("\nNew classification [p/r/d/a/e] (or Enter to skip): ").strip().lower()

            if not new_type_input:
                print("  Skipped.")
                continue

            if new_type_input not in CLASSIFICATIONS:
                print(f"  Invalid classification. Use one of: {', '.join(CLASSIFICATIONS.keys())}")
                continue

            new_type = CLASSIFICATIONS[new_type_input]

            # Update the database
            cursor.execute(
                "UPDATE updates SET update_type = ? WHERE id = ?",
                (new_type, update_id)
            )
            conn.commit()

            print(f"  ✓ Updated to '{new_type}'")

    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!")

    finally:
        conn.close()


if __name__ == "__main__":
    main()

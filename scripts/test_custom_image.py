#!/usr/bin/env python3
"""
Test script for custom image composition.

This demonstrates how to:
1. Find an update you want to post about
2. Use a custom image (from anywhere) instead of Steam screenshots
3. Generate the formatted post with overlay

Usage:
    python scripts/test_custom_image.py
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.schema import get_connection

def main():
    print("=" * 80)
    print("Custom Image Composition Test")
    print("=" * 80)
    print()

    # Show available updates
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.id, g.name, u.title, u.update_type, u.date
        FROM updates u
        JOIN games g ON u.game_id = g.id
        WHERE g.is_active = 1
        ORDER BY u.date DESC
        LIMIT 10
    """)

    updates = cursor.fetchall()
    conn.close()

    if not updates:
        print("No updates found in database")
        return

    print("Recent updates:")
    print()
    for update_id, game_name, title, update_type, date in updates:
        print(f"  [{update_id:3}] {game_name}")
        print(f"       {update_type.upper()}: {title[:60]}...")
        print(f"       Date: {date}")
        print()

    print("=" * 80)
    print()
    print("To generate content with a custom image:")
    print()
    print("  1. Pick an update ID from above")
    print("  2. Find an awesome image online or in your files")
    print("  3. Run:")
    print()
    print("     python scripts/generate_social_content.py \\")
    print("       --update-id <ID> \\")
    print("       --image-path /path/to/your/image.jpg")
    print()
    print("Example:")
    print()
    if updates:
        example_id = updates[0][0]
        print(f"  python scripts/generate_social_content.py \\")
        print(f"    --update-id {example_id} \\")
        print(f"    --image-path ~/Downloads/awesome_screenshot.jpg")
    print()
    print("This will create:")
    print("  - 3 caption variants in content/captions/")
    print("  - 1 image with your custom image in content/posts/")
    print()
    print("The image will have the same professional overlay with:")
    print("  - Game name")
    print("  - Steam tags (Action RPG • Hack and Slash • etc)")
    print("  - Update title")
    print("  - Colored badge (UPDATE/ANNOUNCEMENT/DLC/etc)")
    print()

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
View contents of the Necro Game News database.

Utility script to display games, updates, and other data from the database.

Usage:
    python scripts/view_database.py              # View all games
    python scripts/view_database.py --games      # View games
    python scripts/view_database.py --updates    # View recent updates
    python scripts/view_database.py --candidates # View candidate games
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.schema import get_connection


def view_games():
    """Display all games in the database"""
    conn = get_connection()
    conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            id,
            name,
            steam_id,
            dimension_1,
            dimension_2,
            dimension_3,
            classification_notes,
            is_active
        FROM games
        ORDER BY name
    """)
    
    games = cursor.fetchall()
    conn.close()
    
    if not games:
        print("No games in database yet.")
        return
    
    print(f"\nGames in database: {len(games)}")
    print("=" * 80)
    
    for game in games:
        status = "✓" if game['is_active'] else "✗"
        print(f"\n{status} {game['name']} (Steam ID: {game['steam_id']})")
        print(f"   Classification: 1{game['dimension_1']}, "
              f"2{game['dimension_2']}, 3{game['dimension_3']}")
        if game['classification_notes']:
            print(f"   Notes: {game['classification_notes']}")
        print(f"   Database ID: {game['id']}")


def view_updates(limit=20):
    """Display recent updates"""
    conn = get_connection()
    conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            u.id,
            g.name as game_name,
            u.title,
            u.update_type,
            u.date,
            u.processed_for_social
        FROM updates u
        JOIN games g ON u.game_id = g.id
        ORDER BY u.date DESC
        LIMIT ?
    """, (limit,))
    
    updates = cursor.fetchall()
    conn.close()
    
    if not updates:
        print("\nNo updates in database yet.")
        return
    
    print(f"\nRecent updates: (showing {len(updates)})")
    print("=" * 80)
    
    for update in updates:
        processed = "📱" if update['processed_for_social'] else "  "
        print(f"\n{processed} [{update['update_type']}] {update['game_name']}")
        print(f"   {update['title']}")
        print(f"   Date: {update['date']}")


def view_candidates():
    """Display candidate games under review"""
    conn = get_connection()
    conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            id,
            game_name,
            steam_id,
            source,
            status,
            justification,
            date_submitted
        FROM candidates
        ORDER BY 
            CASE status
                WHEN 'pending' THEN 1
                WHEN 'approved' THEN 2
                WHEN 'rejected' THEN 3
            END,
            date_submitted DESC
    """)
    
    candidates = cursor.fetchall()
    conn.close()
    
    if not candidates:
        print("\nNo candidate games in database yet.")
        return
    
    print(f"\nCandidate games: {len(candidates)}")
    print("=" * 80)
    
    for candidate in candidates:
        status_icon = {
            'pending': '⏳',
            'approved': '✓',
            'rejected': '✗'
        }.get(candidate['status'], '?')
        
        print(f"\n{status_icon} [{candidate['status'].upper()}] {candidate['game_name']}")
        print(f"   Steam ID: {candidate['steam_id']}")
        print(f"   Source: {candidate['source']}")
        if candidate['justification']:
            print(f"   Justification: {candidate['justification']}")
        print(f"   Submitted: {candidate['date_submitted']}")


def view_stats():
    """Display database statistics"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Games count
    cursor.execute("SELECT COUNT(*) FROM games WHERE is_active = 1")
    active_games = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM games WHERE is_active = 0")
    inactive_games = cursor.fetchone()[0]
    
    # Updates count
    cursor.execute("SELECT COUNT(*) FROM updates")
    total_updates = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM updates WHERE processed_for_social = 0")
    unprocessed_updates = cursor.fetchone()[0]
    
    # Candidates count
    cursor.execute("SELECT COUNT(*) FROM candidates WHERE status = 'pending'")
    pending_candidates = cursor.fetchone()[0]
    
    # Social media queue
    cursor.execute("SELECT COUNT(*) FROM social_media_queue WHERE status = 'pending'")
    pending_posts = cursor.fetchone()[0]
    
    conn.close()
    
    print("\nDatabase Statistics")
    print("=" * 80)
    print(f"  Games (active): {active_games}")
    print(f"  Games (inactive): {inactive_games}")
    print(f"  Total updates: {total_updates}")
    print(f"  Unprocessed updates: {unprocessed_updates}")
    print(f"  Pending candidates: {pending_candidates}")
    print(f"  Pending social posts: {pending_posts}")


def main():
    parser = argparse.ArgumentParser(
        description='View Necro Game News database contents'
    )
    
    parser.add_argument('--games', action='store_true',
                       help='View all games')
    parser.add_argument('--updates', action='store_true',
                       help='View recent updates')
    parser.add_argument('--candidates', action='store_true',
                       help='View candidate games')
    parser.add_argument('--stats', action='store_true',
                       help='View database statistics')
    parser.add_argument('--limit', type=int, default=20,
                       help='Limit for updates (default: 20)')
    
    args = parser.parse_args()
    
    # If no specific view requested, show stats and games
    if not any([args.games, args.updates, args.candidates, args.stats]):
        view_stats()
        view_games()
    else:
        if args.stats:
            view_stats()
        if args.games:
            view_games()
        if args.updates:
            view_updates(args.limit)
        if args.candidates:
            view_candidates()
    
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

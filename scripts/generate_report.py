#!/usr/bin/env python3
"""
Generate summary reports of game updates.

Creates human-readable reports of recent updates, useful for
review and social media content planning.

Usage:
    python scripts/generate_report.py                    # Last 24 hours
    python scripts/generate_report.py --days 7           # Last 7 days
    python scripts/generate_report.py --game-id 1        # Specific game
    python scripts/generate_report.py --type patch       # Only patches
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.schema import get_connection


def generate_report(days: int = 1, game_id: int = None, update_type: str = None):
    """
    Generate a report of recent updates.
    
    Args:
        days: Number of days to look back
        game_id: Filter by specific game (None for all)
        update_type: Filter by update type (None for all)
    """
    conn = get_connection()
    conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
    cursor = conn.cursor()
    
    # Build query
    query = """
        SELECT 
            u.id,
            g.name as game_name,
            g.steam_id,
            u.title,
            u.update_type,
            u.date,
            u.url,
            u.content,
            u.processed_for_social
        FROM updates u
        JOIN games g ON u.game_id = g.id
        WHERE u.date >= datetime('now', '-' || ? || ' days')
    """
    params = [days]
    
    if game_id:
        query += " AND g.id = ?"
        params.append(game_id)
    
    if update_type:
        query += " AND u.update_type = ?"
        params.append(update_type)
    
    query += " ORDER BY u.date DESC"
    
    cursor.execute(query, params)
    updates = cursor.fetchall()
    conn.close()
    
    if not updates:
        print(f"\nNo updates found in the last {days} day(s)")
        return
    
    # Group by game
    games_dict = {}
    for update in updates:
        game_name = update['game_name']
        if game_name not in games_dict:
            games_dict[game_name] = []
        games_dict[game_name].append(update)
    
    # Print report
    print("\n" + "=" * 80)
    print(f"Update Report - Last {days} Day(s)")
    if update_type:
        print(f"Filter: {update_type.upper()} updates only")
    print("=" * 80)
    
    total_updates = len(updates)
    total_games = len(games_dict)
    
    print(f"\nSummary: {total_updates} update(s) across {total_games} game(s)\n")
    
    for game_name in sorted(games_dict.keys()):
        game_updates = games_dict[game_name]
        print("\n" + "-" * 80)
        print(f"🎮 {game_name} ({len(game_updates)} update(s))")
        print("-" * 80)
        
        for update in game_updates:
            # Status indicator
            status = "📱" if update['processed_for_social'] else "  "
            
            # Format date
            date_str = update['date']
            if isinstance(date_str, str):
                try:
                    date_obj = datetime.fromisoformat(date_str)
                    date_str = date_obj.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            
            print(f"\n{status} [{update['update_type'].upper()}] {update['title']}")
            print(f"   Date: {date_str}")
            print(f"   URL: {update['url']}")
            
            # Show snippet of content
            if update['content']:
                content = update['content'][:200]
                if len(update['content']) > 200:
                    content += "..."
                print(f"   Content: {content}")
    
    print("\n" + "=" * 80)
    
    # Type breakdown
    type_counts = {}
    for update in updates:
        t = update['update_type']
        type_counts[t] = type_counts.get(t, 0) + 1
    
    print("\nUpdate Type Breakdown:")
    for update_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {update_type}: {count}")
    
    # Social media status
    processed = sum(1 for u in updates if u['processed_for_social'])
    unprocessed = total_updates - processed
    print(f"\nSocial Media Status:")
    print(f"  Processed: {processed}")
    print(f"  Unprocessed: {unprocessed}")
    
    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description='Generate update reports'
    )
    
    parser.add_argument('--days', type=int, default=1,
                       help='Number of days to look back (default: 1)')
    parser.add_argument('--game-id', type=int,
                       help='Filter by specific game database ID')
    parser.add_argument('--type', choices=['patch', 'announcement', 'dlc', 'event'],
                       help='Filter by update type')
    
    args = parser.parse_args()
    
    generate_report(args.days, args.game_id, args.type)
    return 0


if __name__ == "__main__":
    sys.exit(main())

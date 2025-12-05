#!/usr/bin/env python3
"""
Export database to JSON for frontend.

Exports games and their metadata to JSON files that the frontend
can load and display.

Usage:
    python scripts/export_for_web.py
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.schema import get_connection


def export_games():
    """Export all active games with their metadata"""
    conn = get_connection()
    conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
    cursor = conn.cursor()
    
    # Get games with update counts and last update info
    # Update = game changes (patch, release, dlc)
    # Announcement = news/promotional posts (announcement, event)
    cursor.execute("""
        SELECT
            g.id,
            g.steam_id,
            g.name,
            g.app_type,
            g.short_description,
            g.header_image_url,
            g.dimension_1,
            g.dimension_2,
            g.dimension_3,
            g.classification_notes,
            g.developer,
            g.publisher,
            g.release_date,
            g.steam_tags,
            g.genres,
            g.last_checked,
            (SELECT COUNT(*) FROM updates WHERE game_id = g.id) as update_count,
            (SELECT date FROM updates WHERE game_id = g.id AND update_type IN ('patch', 'release', 'dlc') ORDER BY date DESC LIMIT 1) as last_update,
            (SELECT url FROM updates WHERE game_id = g.id AND update_type IN ('patch', 'release', 'dlc') ORDER BY date DESC LIMIT 1) as last_update_url,
            (SELECT title FROM updates WHERE game_id = g.id AND update_type IN ('patch', 'release', 'dlc') ORDER BY date DESC LIMIT 1) as last_update_title,
            (SELECT date FROM updates WHERE game_id = g.id AND update_type IN ('announcement', 'event') ORDER BY date DESC LIMIT 1) as last_announcement,
            (SELECT url FROM updates WHERE game_id = g.id AND update_type IN ('announcement', 'event') ORDER BY date DESC LIMIT 1) as last_announcement_url,
            (SELECT title FROM updates WHERE game_id = g.id AND update_type IN ('announcement', 'event') ORDER BY date DESC LIMIT 1) as last_announcement_title
        FROM games g
        WHERE g.is_active = 1
        ORDER BY g.name
    """)
    
    games = cursor.fetchall()
    conn.close()
    
    # Parse JSON fields
    for game in games:
        if game['steam_tags']:
            try:
                game['steam_tags'] = json.loads(game['steam_tags'])
            except:
                game['steam_tags'] = []
        else:
            game['steam_tags'] = []
        
        if game['genres']:
            try:
                game['genres'] = json.loads(game['genres'])
            except:
                game['genres'] = []
        else:
            game['genres'] = []
    
    return games


def export_stats():
    """Export summary statistics"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Total games
    cursor.execute("SELECT COUNT(*) FROM games WHERE is_active = 1")
    total_games = cursor.fetchone()[0]
    
    # Total updates
    cursor.execute("SELECT COUNT(*) FROM updates")
    total_updates = cursor.fetchone()[0]
    
    # By dimension 1
    cursor.execute("""
        SELECT dimension_1, COUNT(*) as count
        FROM games
        WHERE is_active = 1
        GROUP BY dimension_1
    """)
    dim1_counts = {row[0]: row[1] for row in cursor.fetchall()}
    
    # By dimension 2
    cursor.execute("""
        SELECT dimension_2, COUNT(*) as count
        FROM games
        WHERE is_active = 1
        GROUP BY dimension_2
    """)
    dim2_counts = {row[0]: row[1] for row in cursor.fetchall()}
    
    # By dimension 3
    cursor.execute("""
        SELECT dimension_3, COUNT(*) as count
        FROM games
        WHERE is_active = 1
        GROUP BY dimension_3
    """)
    dim3_counts = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Recent updates (last 30 days)
    cursor.execute("""
        SELECT COUNT(*) 
        FROM updates 
        WHERE date >= datetime('now', '-30 days')
    """)
    recent_updates = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total_games': total_games,
        'total_updates': total_updates,
        'recent_updates_30d': recent_updates,
        'dimension_1': dim1_counts,
        'dimension_2': dim2_counts,
        'dimension_3': dim3_counts,
        'last_updated': datetime.now().isoformat()
    }


def main():
    """Export all data for frontend"""
    print("=" * 60)
    print("Exporting data for frontend")
    print("=" * 60)
    print()
    
    # Ensure output directory exists
    output_dir = Path('frontend/public/data')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Export games
    print("Exporting games...")
    games = export_games()
    games_file = output_dir / 'games.json'
    
    with open(games_file, 'w') as f:
        json.dump(games, f, indent=2)
    
    print(f"✓ Exported {len(games)} games to {games_file}")
    
    # Export stats
    print("\nExporting statistics...")
    stats = export_stats()
    stats_file = output_dir / 'stats.json'
    
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"✓ Exported stats to {stats_file}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Export complete!")
    print("=" * 60)
    print(f"\nFiles created:")
    print(f"  • {games_file}")
    print(f"  • {stats_file}")
    print(f"\nStats:")
    print(f"  Games: {stats['total_games']}")
    print(f"  Total updates: {stats['total_updates']}")
    print(f"  Recent updates (30d): {stats['recent_updates_30d']}")
    print("\nFrontend is ready to load this data!")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

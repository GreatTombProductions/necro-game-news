#!/usr/bin/env python3
"""
Export database to JSON for frontend.

Exports games and their metadata to JSON files that the frontend
can load and display. Supports both necromancy and blood registries.

Output files:
- games.json: Necromancy registry games
- stats.json: Necromancy registry stats
- blood_games.json: Blood registry games
- blood_stats.json: Blood registry stats

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


def export_games(registry='necromancy'):
    """Export active games for a specific registry with their metadata.

    Args:
        registry: 'necromancy' or 'blood' - determines which games to export
    """
    conn = get_connection()
    conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
    cursor = conn.cursor()

    # Determine registry filter
    if registry == 'necromancy':
        registry_filter = "COALESCE(g.registry, 'necromancy') IN ('necromancy', 'both')"
    else:
        registry_filter = "g.registry IN ('blood', 'both')"

    # Get games with update counts and last update info
    # Update = actual game changes (patch, release, dlc)
    # Announcement = most recent entry regardless of type (may overlap with update)
    cursor.execute(f"""
        SELECT
            g.id,
            g.steam_id,
            g.battlenet_id,
            g.battlenet_store_id,
            g.gog_id,
            g.epic_id,
            g.itchio_id,
            g.platforms,
            g.primary_platform,
            g.external_url,
            g.name,
            g.app_type,
            g.short_description,
            g.header_image_url,
            g.dimension_1,
            g.dimension_2,
            g.dimension_3,
            g.dimension_4,
            g.dimension_1_notes,
            g.dimension_2_notes,
            g.dimension_3_notes,
            g.dimension_4_notes,
            g.registry,
            g.vampirism,
            g.vampirism_notes,
            g.hemomancy,
            g.hemomancy_notes,
            g.date_updated,
            g.blood_date_updated,
            g.developer,
            g.publisher,
            g.release_date,
            g.price_usd,
            g.price_notes,
            g.steam_tags,
            g.genres,
            g.aliases,
            g.last_checked,
            (SELECT COUNT(*) FROM updates WHERE game_id = g.id) as update_count,
            (SELECT date FROM updates WHERE game_id = g.id AND update_type IN ('patch', 'release', 'dlc') ORDER BY date DESC LIMIT 1) as last_update,
            (SELECT url FROM updates WHERE game_id = g.id AND update_type IN ('patch', 'release', 'dlc') ORDER BY date DESC LIMIT 1) as last_update_url,
            (SELECT title FROM updates WHERE game_id = g.id AND update_type IN ('patch', 'release', 'dlc') ORDER BY date DESC LIMIT 1) as last_update_title,
            (SELECT date FROM updates WHERE game_id = g.id ORDER BY date DESC LIMIT 1) as last_announcement,
            (SELECT url FROM updates WHERE game_id = g.id ORDER BY date DESC LIMIT 1) as last_announcement_url,
            (SELECT title FROM updates WHERE game_id = g.id ORDER BY date DESC LIMIT 1) as last_announcement_title,
            (SELECT content FROM updates WHERE game_id = g.id ORDER BY date DESC LIMIT 1) as last_announcement_content
        FROM games g
        WHERE g.is_active = 1 AND {registry_filter}
        ORDER BY g.name
    """)
    
    games = cursor.fetchall()
    conn.close()

    # Parse JSON fields and add registry-specific mappings
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

        if game['platforms']:
            try:
                game['platforms'] = json.loads(game['platforms'])
            except:
                game['platforms'] = ['steam']
        else:
            game['platforms'] = ['steam']

        if game['aliases']:
            try:
                game['aliases'] = json.loads(game['aliases'])
            except:
                game['aliases'] = []
        else:
            game['aliases'] = []

        # For blood registry, add friendly field aliases and use blood_date_updated
        if registry == 'blood':
            # Map dimension fields to blood-specific names
            game['pov'] = game['dimension_2']
            game['availability'] = game['dimension_4']
            game['pov_notes'] = game['dimension_2_notes']
            game['availability_notes'] = game['dimension_4_notes']
            # Use blood_date_updated as the date_updated for blood registry
            if game.get('blood_date_updated'):
                game['date_updated'] = game['blood_date_updated']

        # Remove internal blood_date_updated field from output (frontend doesn't need it)
        game.pop('blood_date_updated', None)

    return games


def export_stats(registry='necromancy'):
    """Export summary statistics for a specific registry.

    Args:
        registry: 'necromancy' or 'blood' - determines which games to count
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Determine registry filter
    if registry == 'necromancy':
        registry_filter = "COALESCE(registry, 'necromancy') IN ('necromancy', 'both')"
    else:
        registry_filter = "registry IN ('blood', 'both')"

    # Total games in this registry
    cursor.execute(f"SELECT COUNT(*) FROM games WHERE is_active = 1 AND {registry_filter}")
    total_games = cursor.fetchone()[0]

    # Total updates for games in this registry
    cursor.execute(f"""
        SELECT COUNT(*) FROM updates u
        JOIN games g ON u.game_id = g.id
        WHERE g.is_active = 1 AND {registry_filter}
    """)
    total_updates = cursor.fetchone()[0]

    # Recent updates (last 30 days) for this registry
    cursor.execute(f"""
        SELECT COUNT(*) FROM updates u
        JOIN games g ON u.game_id = g.id
        WHERE g.is_active = 1 AND {registry_filter}
        AND u.date >= datetime('now', '-30 days')
    """)
    recent_updates = cursor.fetchone()[0]

    if registry == 'necromancy':
        # By dimension 1 (centrality)
        cursor.execute(f"""
            SELECT dimension_1, COUNT(*) as count
            FROM games
            WHERE is_active = 1 AND {registry_filter}
            GROUP BY dimension_1
        """)
        dim1_counts = {row[0]: row[1] for row in cursor.fetchall()}

        # By dimension 2 (POV)
        cursor.execute(f"""
            SELECT dimension_2, COUNT(*) as count
            FROM games
            WHERE is_active = 1 AND {registry_filter}
            GROUP BY dimension_2
        """)
        dim2_counts = {row[0]: row[1] for row in cursor.fetchall()}

        # By dimension 3 (naming)
        cursor.execute(f"""
            SELECT dimension_3, COUNT(*) as count
            FROM games
            WHERE is_active = 1 AND {registry_filter}
            GROUP BY dimension_3
        """)
        dim3_counts = {row[0]: row[1] for row in cursor.fetchall()}

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
    else:
        # Blood registry stats
        # By vampirism
        cursor.execute(f"""
            SELECT vampirism, COUNT(*) as count
            FROM games
            WHERE is_active = 1 AND {registry_filter}
            GROUP BY vampirism
        """)
        vampirism_counts = {row[0]: row[1] for row in cursor.fetchall() if row[0]}

        # By hemomancy
        cursor.execute(f"""
            SELECT hemomancy, COUNT(*) as count
            FROM games
            WHERE is_active = 1 AND {registry_filter}
            GROUP BY hemomancy
        """)
        hemomancy_counts = {row[0]: row[1] for row in cursor.fetchall() if row[0]}

        # By POV (dimension_2)
        cursor.execute(f"""
            SELECT dimension_2, COUNT(*) as count
            FROM games
            WHERE is_active = 1 AND {registry_filter}
            GROUP BY dimension_2
        """)
        pov_counts = {row[0]: row[1] for row in cursor.fetchall() if row[0]}

        conn.close()

        return {
            'total_games': total_games,
            'total_updates': total_updates,
            'recent_updates_30d': recent_updates,
            'vampirism': vampirism_counts,
            'hemomancy': hemomancy_counts,
            'pov': pov_counts,
            'last_updated': datetime.now().isoformat()
        }


def main():
    """Export all data for frontend (both registries)"""
    print("=" * 60)
    print("Exporting data for frontend")
    print("=" * 60)
    print()

    # Ensure output directory exists
    output_dir = Path('frontend/public/data')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Export necromancy registry
    print("Exporting necromancy registry...")
    necro_games = export_games('necromancy')
    games_file = output_dir / 'games.json'

    with open(games_file, 'w') as f:
        json.dump(necro_games, f, indent=2)

    print(f"✓ Exported {len(necro_games)} necromancy games to {games_file}")

    # Export necromancy stats
    necro_stats = export_stats('necromancy')
    stats_file = output_dir / 'stats.json'

    with open(stats_file, 'w') as f:
        json.dump(necro_stats, f, indent=2)

    print(f"✓ Exported necromancy stats to {stats_file}")

    # Export blood registry
    print("\nExporting blood registry...")
    blood_games = export_games('blood')
    blood_games_file = output_dir / 'blood_games.json'

    with open(blood_games_file, 'w') as f:
        json.dump(blood_games, f, indent=2)

    print(f"✓ Exported {len(blood_games)} blood games to {blood_games_file}")

    # Export blood stats
    blood_stats = export_stats('blood')
    blood_stats_file = output_dir / 'blood_stats.json'

    with open(blood_stats_file, 'w') as f:
        json.dump(blood_stats, f, indent=2)

    print(f"✓ Exported blood stats to {blood_stats_file}")

    # Summary
    print("\n" + "=" * 60)
    print("Export complete!")
    print("=" * 60)
    print("\nFiles created:")
    print(f"  • {games_file}")
    print(f"  • {stats_file}")
    print(f"  • {blood_games_file}")
    print(f"  • {blood_stats_file}")
    print("\nNecromancy Registry:")
    print(f"  Games: {necro_stats['total_games']}")
    print(f"  Total updates: {necro_stats['total_updates']}")
    print(f"  Recent updates (30d): {necro_stats['recent_updates_30d']}")
    print("\nBlood Registry:")
    print(f"  Games: {blood_stats['total_games']}")
    print(f"  Total updates: {blood_stats['total_updates']}")
    print(f"  Recent updates (30d): {blood_stats['recent_updates_30d']}")
    print("\nFrontend is ready to load this data!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())

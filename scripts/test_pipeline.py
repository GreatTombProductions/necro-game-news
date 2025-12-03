#!/usr/bin/env python3
"""
End-to-end test of the Necro Game News data pipeline.

Tests the complete flow:
1. Database connection
2. Steam API access
3. Game details fetching
4. Update checking
5. Data retrieval

Usage:
    python scripts/test_pipeline.py
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.scrapers.steam_api import SteamAPI
from backend.database.schema import get_connection


def test_database():
    """Test database connection and schema"""
    print("\n" + "=" * 60)
    print("TEST 1: Database Connection")
    print("=" * 60)
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        expected = ['candidates', 'games', 'social_media_queue', 'updates']
        missing = set(expected) - set(tables)
        
        if missing:
            print(f"✗ Missing tables: {missing}")
            return False
        
        # Count records
        cursor.execute("SELECT COUNT(*) FROM games WHERE is_active = 1")
        game_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM updates")
        update_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"✓ Database connection successful")
        print(f"  Tables: {', '.join(tables)}")
        print(f"  Active games: {game_count}")
        print(f"  Updates: {update_count}")
        
        return True
        
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False


def test_steam_api():
    """Test Steam API access"""
    print("\n" + "=" * 60)
    print("TEST 2: Steam API Access")
    print("=" * 60)
    
    try:
        api = SteamAPI()
        
        # Test app details
        test_appid = 2344520  # Diablo IV
        details = api.get_app_details(test_appid)
        
        if not details:
            print(f"✗ Could not fetch app details for {test_appid}")
            return False
        
        parsed = api.parse_app_details(details)
        print(f"✓ Successfully fetched app details")
        print(f"  Game: {parsed['name']}")
        print(f"  Type: {parsed['app_type']}")
        print(f"  Developer: {parsed['developer']}")
        
        # Test news
        news = api.get_app_news(test_appid, count=3)
        
        if not news:
            print(f"✗ Could not fetch news for {test_appid}")
            return False
        
        print(f"✓ Successfully fetched news")
        print(f"  News items: {len(news)}")
        
        # Test update classification
        for item in news[:2]:
            parsed_news = api.parse_news_item(item, test_appid)
            print(f"  - [{parsed_news['update_type']}] {parsed_news['title'][:50]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ Steam API test failed: {e}")
        return False


def test_game_in_database():
    """Test that we can fetch details for a game in our database"""
    print("\n" + "=" * 60)
    print("TEST 3: Database + Steam Integration")
    print("=" * 60)
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get first active game
        cursor.execute("""
            SELECT id, name, steam_id 
            FROM games 
            WHERE is_active = 1 
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        
        if not row:
            print("⚠ No active games in database to test")
            print("  Run: python scripts/load_games_from_yaml.py")
            conn.close()
            return None  # Not a failure, just no data yet
        
        game_id, name, steam_id = row
        conn.close()
        
        print(f"Testing with: {name} (Steam ID: {steam_id})")
        
        # Fetch from Steam
        api = SteamAPI()
        details = api.get_app_details(steam_id)
        
        if not details:
            print(f"✗ Could not fetch Steam data for {name}")
            return False
        
        print(f"✓ Successfully fetched Steam data")
        
        # Fetch news
        news = api.get_app_news(steam_id, count=5)
        print(f"✓ Found {len(news)} news items")
        
        return True
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False


def test_update_detection():
    """Test that we can detect and classify updates"""
    print("\n" + "=" * 60)
    print("TEST 4: Update Detection & Classification")
    print("=" * 60)
    
    try:
        api = SteamAPI()
        
        # Test with a known game
        test_appid = 1604030  # V Rising
        news = api.get_app_news(test_appid, count=5)
        
        if not news:
            print(f"⚠ No news items to test classification")
            return None
        
        print(f"Testing classification on {len(news)} news items:")
        
        type_counts = {}
        for item in news:
            parsed = api.parse_news_item(item, test_appid)
            update_type = parsed['update_type']
            type_counts[update_type] = type_counts.get(update_type, 0) + 1
            
            print(f"  [{update_type.upper()}] {parsed['title'][:60]}...")
        
        print(f"\nClassification distribution:")
        for update_type, count in type_counts.items():
            print(f"  {update_type}: {count}")
        
        print(f"✓ Classification working")
        return True
        
    except Exception as e:
        print(f"✗ Update detection test failed: {e}")
        return False


def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "=" * 60)
    print("NECRO GAME NEWS - PIPELINE TEST")
    print("=" * 60)
    
    results = {
        'Database': test_database(),
        'Steam API': test_steam_api(),
        'Integration': test_game_in_database(),
        'Classification': test_update_detection()
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in results.items():
        if result is True:
            print(f"  ✓ {test_name}: PASSED")
        elif result is False:
            print(f"  ✗ {test_name}: FAILED")
        else:
            print(f"  ⚠ {test_name}: SKIPPED (no data)")
    
    failed = [name for name, result in results.items() if result is False]
    skipped = [name for name, result in results.items() if result is None]
    passed = [name for name, result in results.items() if result is True]
    
    print()
    print(f"Passed: {len(passed)}/{len(results)}")
    
    if skipped:
        print(f"Skipped: {len(skipped)} (need data)")
    
    if failed:
        print(f"Failed: {len(failed)}")
        print("\n⚠ Some tests failed. Check errors above.")
        return 1
    
    if len(passed) == len(results):
        print("\n✓ All tests passed! Pipeline is working correctly.")
    else:
        print("\n⚠ Some tests skipped. Add games to database for full testing.")
    
    print("\nNext steps:")
    print("  1. python scripts/load_games_from_yaml.py")
    print("  2. python scripts/fetch_game_details.py")
    print("  3. python scripts/check_updates.py")
    print("  4. python scripts/generate_report.py")
    
    print("\n" + "=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(run_all_tests())

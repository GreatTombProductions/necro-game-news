"""
Database schema for Necro Game News

Tables:
- games: Tracked games with necromancy classification
- updates: Game updates/news from Steam
- candidates: Games under review for addition
- social_media_queue: Posts scheduled for social media
"""

import sqlite3
from pathlib import Path

# Schema definitions
SCHEMA = """
-- ============================================================================
-- GAMES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Platform identifiers (at least one should be set)
    steam_id INTEGER,  -- Nullable for non-Steam games
    battlenet_id TEXT,
    gog_id TEXT,
    epic_id TEXT,
    itchio_id TEXT,

    -- Multi-platform metadata
    platforms TEXT DEFAULT '["steam"]',  -- JSON array of platforms
    primary_platform TEXT DEFAULT 'steam' CHECK(primary_platform IN ('steam', 'battlenet', 'gog', 'epic', 'itchio', 'manual')),
    external_url TEXT,  -- Manual store link if needed

    -- Game info
    name TEXT NOT NULL,
    app_type TEXT,  -- 'game', 'dlc', etc.
    short_description TEXT,
    header_image_url TEXT,

    -- Necromancy classification (highest satisfied per dimension)
    -- dimension_1: degree of necromancy integration
    --   a: central to character/unit identity and gameplay
    --   b: dedicated specialization available
    --   c: some necromancy skills or items present
    --   d: some necromancy technically present, minimal impact on identity/gameplay
    dimension_1 TEXT CHECK(dimension_1 IN ('a', 'b', 'c', 'd')),
    dimension_2 TEXT CHECK(dimension_2 IN ('character', 'unit')),
    dimension_3 TEXT CHECK(dimension_3 IN ('explicit', 'implied')),
    classification_notes TEXT,

    -- Metadata (may come from various platforms)
    steam_tags TEXT,  -- JSON array as string
    genres TEXT,      -- JSON array as string
    release_date TEXT,
    price_usd REAL,   -- Price in USD (NULL for free games)
    subscription TEXT CHECK(subscription IN ('monthly', 'annual')),  -- Subscription type if applicable
    developer TEXT,
    publisher TEXT,

    -- Tracking metadata
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_checked TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- ============================================================================
-- UPDATES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    update_type TEXT CHECK(update_type IN ('patch', 'announcement', 'dlc', 'event', 'release', 'unknown')),
    title TEXT NOT NULL,
    content TEXT,
    url TEXT,
    gid TEXT,  -- Platform's unique identifier for the update
    date TIMESTAMP NOT NULL,
    source_platform TEXT DEFAULT 'steam',  -- Which platform this update came from

    -- Social media processing
    processed_for_social BOOLEAN DEFAULT 0,
    date_posted TIMESTAMP,

    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE,
    UNIQUE(gid)
);

-- ============================================================================
-- CANDIDATES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    steam_id INTEGER,
    game_name TEXT NOT NULL,
    source TEXT CHECK(source IN ('user_submission', 'auto_discovery', 'manual')),
    submitter_contact TEXT,
    justification TEXT,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected', 'skipped')),
    
    -- Review information
    reviewed_by TEXT,
    review_date TIMESTAMP,
    review_notes TEXT,
    
    date_submitted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(steam_id)
);

-- ============================================================================
-- SOCIAL MEDIA QUEUE TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS social_media_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    update_id INTEGER,
    platform TEXT CHECK(platform IN ('instagram', 'youtube', 'twitter', 'other')),
    content_text TEXT NOT NULL,
    image_path TEXT,
    scheduled_time TIMESTAMP,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'posted', 'failed', 'cancelled')),
    
    -- Post tracking
    post_id TEXT,  -- Platform's post ID after successful posting
    error_message TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    posted_at TIMESTAMP,
    
    FOREIGN KEY (update_id) REFERENCES updates(id) ON DELETE SET NULL
);

-- ============================================================================
-- INDEXES for performance
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_updates_game_date ON updates(game_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_updates_type ON updates(update_type);
CREATE INDEX IF NOT EXISTS idx_updates_processed ON updates(processed_for_social);
CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status);
CREATE INDEX IF NOT EXISTS idx_social_queue_status ON social_media_queue(status, scheduled_time);
CREATE INDEX IF NOT EXISTS idx_games_active ON games(is_active);
"""


def get_db_path():
    """Get the database path from environment or use default"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    db_path = os.getenv('DATABASE_PATH', 'data/necro_games.db')
    return Path(db_path)


def create_database(db_path=None):
    """
    Create the database and all tables.
    
    Args:
        db_path: Path to database file. If None, uses default from env/config
    """
    if db_path is None:
        db_path = get_db_path()
    
    # Ensure data directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Connect and create schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Execute schema (supports multiple statements)
    cursor.executescript(SCHEMA)
    
    conn.commit()
    conn.close()
    
    print(f"✓ Database created successfully at: {db_path}")
    print(f"✓ Tables: games, updates, candidates, social_media_queue")
    return db_path


def get_connection(db_path=None):
    """
    Get a connection to the database.
    
    Args:
        db_path: Path to database file. If None, uses default from env/config
        
    Returns:
        sqlite3.Connection
    """
    if db_path is None:
        db_path = get_db_path()
    
    if not db_path.exists():
        raise FileNotFoundError(
            f"Database not found at {db_path}. "
            "Run 'python scripts/init_database.py' first."
        )
    
    return sqlite3.connect(db_path)


def verify_schema(db_path=None):
    """Verify that all expected tables exist"""
    if db_path is None:
        db_path = get_db_path()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        ORDER BY name
    """)
    
    tables = [row[0] for row in cursor.fetchall()]
    expected = ['candidates', 'games', 'social_media_queue', 'updates']
    
    conn.close()
    
    print(f"\nTables in database:")
    for table in tables:
        status = "✓" if table in expected else "?"
        print(f"  {status} {table}")
    
    missing = set(expected) - set(tables)
    if missing:
        print(f"\n⚠ Missing tables: {', '.join(missing)}")
        return False
    
    print(f"\n✓ All expected tables present")
    return True


if __name__ == "__main__":
    # When run directly, create the database
    db_path = create_database()
    verify_schema(db_path)

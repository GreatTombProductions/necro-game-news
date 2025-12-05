# Scripts Directory

This directory contains all operational scripts for Necro Game News.

## Content Generation

### generate_social_content.py
Generate social media content with multiple variants.
- 3 caption variants (standard, punchy, engagement-focused)
- Multiple image variants using different screenshots
- Improved file naming (YYYYMMDD_GameName)
- Steam tags displayed in image banners
- Custom image support
- Default 2-day lookback window (catches anything missed)

```bash
# Generate for last 2 days (default)
python scripts/generate_social_content.py

# Generate for all unprocessed updates
python scripts/generate_social_content.py --all

# Generate for specific update
python scripts/generate_social_content.py --update-id 42

# Use custom image
python scripts/generate_social_content.py --update-id 42 --image-path ~/image.jpg
```

## Database Management

### init_database.py
Initialize database schema.

### fetch_game_details.py
Fetch game details from Steam, including Steam tags from Steamspy.

```bash
# Update all games (including tags)
python scripts/fetch_game_details.py

# Update specific game
python scripts/fetch_game_details.py --game-id 1
```

### load_games_from_yaml.py
Sync games from YAML configuration to database.

### view_database.py
View database contents and statistics.

## Game Discovery

### batch_discover.py
Discover necromancy games from entire Steam catalog.

### review_candidates.py
Interactive CLI to review discovered game candidates.

## Migrations

### migrations/backfill_tags.py
Backfill Steam tags for existing games.

```bash
# Backfill missing tags
python scripts/migrations/backfill_tags.py

# Force re-fetch all tags
python scripts/migrations/backfill_tags.py --force
```

## Updates

### check_updates.py
Check for new Steam updates for tracked games.

## Deployment

### deploy.sh
Automated daily deployment workflow. Runs:
1. Check for updates
2. Export data for web
3. Generate social media content
4. Generate weekly report
5. Commit and push (triggers Vercel deploy)

```bash
./scripts/deploy.sh
```

## See Also
- [IMPLEMENTATION_NOTES.md](../IMPLEMENTATION_NOTES.md) - Details on recent improvements
- [CLAUDE.md](../CLAUDE.md) - Project overview and status

# Content Generation Improvements - Implementation Notes

## Overview
This document summarizes the improvements made to the content generation system, focusing on Steam tags integration, multiple content candidates, improved file naming, and enhanced image customization.

## Changes Implemented

### 1. Steam Tags Collection ✅

**Why**: Steam's official genres (Action, RPG) are broad and don't capture trending microgenres. User-generated tags (Roguelike, Souls-like, Deck Builder) provide much better context.

**Implementation**:
- Added `get_app_tags()` method to `SteamAPI` class that fetches tags from Steamspy API
- Updated `parse_app_details()` to automatically fetch top 10 tags for each game
- Modified `fetch_game_details.py` to store tags in `steam_tags` column (as JSON array)
- Database schema already had `steam_tags` column ready to use

**Files Modified**:
- `backend/scrapers/steam_api.py`: Added Steamspy integration
- `scripts/fetch_game_details.py`: Updated to store tags properly

**New Script**:
- `scripts/migrations/backfill_tags.py`: Backfill tags for existing games

**Usage**:
```bash
# Backfill tags for all games without tags
python scripts/migrations/backfill_tags.py

# Force re-fetch tags for all games
python scripts/migrations/backfill_tags.py --force
```

---

### 2. Improved File Naming ✅

**Before**: `queue_1.jpg`, `queue_1.txt`
**After**: `20251205_DiabloIV_image_1.jpg`, `20251205_DiabloIV_caption_1.txt`

**Why**: Descriptive names make content organization easier and help identify posts at a glance.

**Implementation**:
- New naming pattern: `YYYYMMDD_GameName_type_variant.ext`
- Sanitized game names (remove special characters, limit length)
- Implemented in `generate_social_content.py`

---

### 3. Removed Image Caching System ✅

**Why**: Cached images become stale. For social media, we want fresh screenshots that showcase the latest updates.

**Implementation**:
- Removed `cache_dir` parameter from `ImageCompositor`
- Removed `cache_file` logic from `fetch_game_image()`
- Images now downloaded fresh each time

**Files Modified**:
- `backend/content_gen/image_compositor.py`

---

### 4. Multiple Content Candidates ✅

**Feature**: Generate 3 caption variants and multiple image options for each update.

#### Caption Variants:
1. **Standard**: Current format with AI summary and game stats
2. **Punchy**: Short, enthusiastic single-sentence summary
3. **Engagement**: Question-based to drive player interaction

#### Image Variants:
- Fetches up to 3 different screenshots from Steam
- Each variant shows different gameplay/visuals
- All use the same overlay style with tags

**Implementation**:
- Main script: `scripts/generate_social_content.py`
- Uses Claude API for caption variations
- Fetches multiple screenshots via Steam API

**Usage**:
```bash
# Generate for today's updates (default)
python scripts/generate_social_content.py

# Generate for all unprocessed updates
python scripts/generate_social_content.py --all

# Generate for specific update
python scripts/generate_social_content.py --update-id 42
```

**Output Structure**:
```
content/
├── posts/
│   ├── 20251205_DiabloIV_image_1.jpg
│   ├── 20251205_DiabloIV_image_2.jpg
│   └── 20251205_DiabloIV_image_3.jpg
└── captions/
    ├── 20251205_DiabloIV_caption_1.txt
    ├── 20251205_DiabloIV_caption_2.txt
    └── 20251205_DiabloIV_caption_3.txt
```

---

### 5. Custom Image Support ✅

**Feature**: Format posts using your own images (found online or curated).

**Implementation**:
- Added `local_image_path` parameter to image compositor
- Added `load_local_image()` method
- Supports all standard image formats (JPG, PNG, etc.)

**Usage**:
```bash
# Use custom image for post
python scripts/generate_social_content.py --update-id 42 \
    --image-path /path/to/awesome_screenshot.jpg
```

**Files Modified**:
- `backend/content_gen/image_compositor.py`: Added `local_image_path` support

---

### 6. Tags in Image Banner ✅

**Feature**: Display Steam tags in image overlay (with genre fallback).

**Why**: Tags give viewers immediate context about the game's style and mechanics.

**Implementation**:
- Updated `create_text_overlay()` to accept optional `tags` parameter
- Displays top 3-4 tags between game name and update title
- Falls back to genres if tags unavailable
- Styled subtly with secondary color and bullet separators

**Visual Layout**:
```
[UPDATE Badge]
Game Name                    ← Large, bold
Action RPG • Hack and Slash  ← Tags (subtle)
Update Title Here            ← Medium, wrapped
```

**Files Modified**:
- `backend/content_gen/image_compositor.py`: Added tag display
- `backend/content_gen/content_generator.py`: Fetch tags from database

---

### 7. Streamlined Workflow ✅

**Removed Complexity**:
- Eliminated queue-based system (was overcomplicated for this use case)
- Deleted `generate_social_posts.py` and `preview_social_posts.py`
- Consolidated all functionality into single `generate_social_content.py` script
- Simplified `deploy.sh` workflow

**New Daily Workflow** (`./scripts/deploy.sh`):
1. Check for Steam updates
2. Export data for web
3. Generate social media content (3 captions + multiple images per update)
4. Generate weekly report
5. Git commit/push (triggers Vercel deploy)

**Benefits**:
- One command for everything
- No manual queue management
- Content files saved directly to `content/posts/` and `content/captions/`
- Pick your favorite variants manually before posting

---

## Migration Guide

### For Existing Games

Run the migration to backfill tags:

```bash
python scripts/migrations/backfill_tags.py
```

This will:
- Fetch tags for all games missing tag data
- Store top 10 tags per game in `steam_tags` column
- Update `last_checked` timestamp

### Daily Workflow

Just run the deploy script:

```bash
./scripts/deploy.sh
```

This handles everything:
- Checks for new updates
- Generates content with multiple variants
- Exports data for website
- Commits and deploys

Then manually:
1. Review content in `content/posts/` and `content/captions/`
2. Pick your favorite caption/image combo
3. Post to Instagram

---

## API Dependencies

### Steamspy API
- **Endpoint**: `https://steamspy.com/api.php`
- **Rate Limit**: ~200 requests per hour
- **No Auth Required**: Free public API
- **Purpose**: Fetch user-generated tags

### Steam Store API
- Already used for game details
- No changes to usage

### Claude API
- Used for caption generation
- Now generates 3 variants per update (standard, punchy, engagement)

---

## File Structure Changes

### New Files
```
scripts/
├── generate_social_content.py        # NEW: Streamlined content generator
└── migrations/
    └── backfill_tags.py              # NEW: Tag migration script
```

### Modified Files
```
backend/
├── scrapers/steam_api.py             # Added Steamspy tag fetching
└── content_gen/
    ├── image_compositor.py           # Removed cache, added tags/custom images
    └── content_generator.py          # Fetch steam_tags from DB

scripts/
├── fetch_game_details.py             # Store tags in DB
└── deploy.sh                         # Simplified workflow
```

### Deleted Files
```
scripts/
├── generate_social_posts.py          # REMOVED: Replaced by generate_social_content.py
└── preview_social_posts.py           # REMOVED: Queue management not needed
```

---

## Testing Checklist

Before deploying:

- [ ] Run tag migration: `python scripts/migrations/backfill_tags.py`
- [ ] Test content generation: `python scripts/generate_social_content.py`
- [ ] Verify tags display correctly in images
- [ ] Check file naming follows new pattern
- [ ] Confirm caption variants are distinct
- [ ] Test custom image: `--image-path /path/to/test.jpg`
- [ ] Run full deploy: `./scripts/deploy.sh`

---

## Future Enhancements

Potential improvements to consider:

1. **Automatic Best Selection**: Use engagement metrics to auto-select best caption/image combo
2. **Tag Filtering**: Allow filtering which tags to display
3. **Style Presets**: Different overlay styles for different update types
4. **A/B Testing**: Track which caption style gets most engagement
5. **Batch Processing**: Parallel processing for multiple updates

---

## Questions?

For issues or questions:
- Check logs for API errors (Steamspy, Claude)
- Verify `ANTHROPIC_API_KEY` in `.env` for caption variants
- Ensure Steam API key valid for metadata fetching
- Check file permissions on `content/posts/` and `content/captions/` directories

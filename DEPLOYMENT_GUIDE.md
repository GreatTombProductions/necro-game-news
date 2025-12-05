# Deployment Guide

Quick reference for running Necro Game News deployment workflows.

## Interactive Mode (Default)

Simply run without arguments for an interactive menu:

```bash
./scripts/deploy.sh
```

You'll be prompted to choose:
1. **Full Deploy** - Everything (updates, content, deploy)
2. **Updates + Deploy** - Skip social content generation
3. **Social Content Only** - Just generate content, no deploy

If generating content, you'll also be asked about reprocessing.

## Command Line Mode

Skip the interactive menu with flags:

```bash
# Full deploy (everything)
./scripts/deploy.sh --full

# Updates + deploy (skip content generation)
./scripts/deploy.sh --updates-only

# Social content only (no deploy)
./scripts/deploy.sh --content-only

# Reprocess already-processed updates (for dev/testing)
./scripts/deploy.sh --content-only --reprocess
./scripts/deploy.sh --full --reprocess
```

## Common Workflows

### Daily Production Deploy
```bash
./scripts/deploy.sh --full
```
- Checks for new Steam updates
- Generates social content (3 captions + images)
- Exports data for website
- Commits & deploys to Vercel

### Website Update Only
```bash
./scripts/deploy.sh --updates-only
```
- Checks for new Steam updates
- Exports data for website
- Commits & deploys to Vercel
- Skips social content (generate later manually)

### Dev: Testing Content Generation
```bash
./scripts/deploy.sh --content-only --reprocess
```
- Regenerates content for recent updates
- Ignores "already processed" flag
- No git commit/deploy
- Perfect for iterating on image/caption styling

### Manual Content Generation
```bash
# Generate for specific update with custom image
python scripts/generate_social_content.py \
  --update-id 182 \
  --image-path ~/Downloads/awesome_screenshot.jpg

# Reprocess last 2 days
python scripts/generate_social_content.py --reprocess

# Generate for specific date range
python scripts/generate_social_content.py --since 2025-12-01
```

## Output Locations

After running deploy:

```
content/
├── posts/           # Images (YYYYMMDD_GameName_image_N.jpg)
└── captions/        # Captions (YYYYMMDD_GameName_caption_N.txt)

frontend/public/data/
├── games.json       # Game data for website
└── updates.json     # Update data for website
```

## Flags Reference

### deploy.sh flags:
- `--full` - Full deployment workflow
- `--updates-only` - Skip social content generation
- `--content-only` - Only generate social content
- `--reprocess` - Include already-processed updates

### generate_social_content.py flags:
- `--all` - Process all unprocessed updates
- `--since YYYY-MM-DD` - Process updates from date onwards
- `--reprocess` - Ignore processed status (regenerate everything)
- `--update-id N` - Generate for specific update
- `--image-path PATH` - Use custom image (with --update-id)

## Tips

**Development/Testing:**
- Use `--reprocess` to regenerate content without changing database
- Use `--content-only` to avoid git commits while testing
- Content files are overwritten, so you can iterate quickly

**Production:**
- Run `--full` daily (or via cron)
- Review generated content in `content/` before posting
- Pick your favorite caption/image combo
- Post manually to Instagram

**Custom Images:**
1. Find amazing screenshots online
2. Use `--update-id N --image-path` to format them
3. Same professional overlay, your image choice

## Troubleshooting

**"No updates found":**
- Check if `processed_for_social = 1` in database
- Use `--reprocess` to force regeneration

**Tag data missing:**
- Run `python scripts/migrations/backfill_tags.py`
- Fetches user-defined tags from Steamspy

**Images look wrong:**
- Check image dimensions (works best with 16:9 landscape)
- Will auto-crop to 4:5 for Instagram
- Try different screenshots with `--reprocess`

# Social Media Quick Start Guide

Get your Instagram content pipeline running in 5 minutes.

## Installation

The content generation system is already set up! Just make sure dependencies are installed:

```bash
# If using system Python
pip3 install requests Pillow

# If using virtual environment
source venv/bin/activate
pip install requests Pillow
```

## Daily Workflow (5 Steps)

### 1. Check for New Updates
```bash
python3 scripts/check_updates.py
```

### 2. Generate Social Posts
```bash
# Generate posts from patches only (recommended to start)
python3 scripts/generate_social_posts.py --types patch --limit 5 --generate-images
```

### 3. Preview Your Posts
```bash
# List all pending posts
python3 scripts/preview_social_posts.py

# Preview specific post with full caption
python3 scripts/preview_social_posts.py --id 1

# Export captions to text files for easy copying
python3 scripts/preview_social_posts.py --export-caption
```

### 4. Post to Instagram Manually
- **Image:** Open `content/posts/queue_1.jpg`
- **Caption:** Open `content/captions/queue_1.txt` or copy to clipboard:
  ```bash
  # macOS
  cat content/captions/queue_1.txt | pbcopy
  ```
- Upload to Instagram (app or web)
- Post!

### 5. Mark as Posted
```bash
python3 scripts/preview_social_posts.py --id 1 --mark-posted --post-id "instagram_url"
```

## Content Strategy Tips

### What to Post
✅ **DO POST:**
- Major patches and updates
- DLC announcements
- New game additions to your tracking list

❌ **SKIP:**
- Minor hotfixes
- Sales/promotions (unless major)
- Non-necromancy-related announcements

### Filtering Content
```bash
# Only patches (best for daily content)
python3 scripts/generate_social_posts.py --types patch --generate-images

# Patches and DLC
python3 scripts/generate_social_posts.py --types patch dlc --generate-images

# Check what's available before queueing
python3 scripts/generate_social_posts.py --stats
```

### Posting Frequency
- **Start small:** 1-2 posts per day
- **Build consistency:** Same time each day works best
- **Quality over quantity:** Better to skip a day than post low-quality content

## File Locations

```
content/
├── posts/              # Generated Instagram images (1920x1080 source)
│   └── queue_*.jpg     # Ready to post
├── captions/           # Caption text files (matches images)
│   └── queue_*.txt     # Copy to clipboard
└── cache/              # Cached game screenshots (auto-managed)
```

## Common Commands Cheat Sheet

```bash
# Stats without queueing
python3 scripts/generate_social_posts.py --stats

# Queue specific update by ID
python3 scripts/generate_social_posts.py --update-id 42 --generate-images

# Show all pending posts
python3 scripts/preview_social_posts.py

# Show posted content
python3 scripts/preview_social_posts.py --status posted

# Export single caption to file
python3 scripts/preview_social_posts.py --id 1 --export-caption

# Copy caption to clipboard (macOS)
cat content/captions/queue_1.txt | pbcopy

# Cancel a post
python3 scripts/preview_social_posts.py --id 5 --cancel
```

## Example Session

```bash
# Morning routine
$ python3 scripts/check_updates.py
✓ Found 12 new updates

$ python3 scripts/generate_social_posts.py --stats
Total unprocessed: 155
  patch:         63
  announcement:  53
  dlc:          21
  event:        18

$ python3 scripts/generate_social_posts.py --types patch --limit 3 --generate-images
✓ Queued 3 updates
Generating image for: Diablo IV - Season of Witchcraft Update...
✓ Post image saved: content/posts/queue_2.jpg

$ python3 scripts/preview_social_posts.py --id 2
[Shows caption and post details]

# Review image, post to Instagram, then:
$ python3 scripts/preview_social_posts.py --id 2 --mark-posted
✓ Entry 2 marked as posted
```

## Troubleshooting

**"Module not found" errors:**
```bash
pip3 install requests Pillow
```

**Image generation fails:**
- Check internet connection (downloads game images)
- Verify `content/posts/` directory exists
- Try running with `--preview` flag for debugging

**No updates found:**
- Run `python3 scripts/check_updates.py` first
- Check `--stats` to see what's available
- Some updates may already be processed

## Next Steps

Once you're comfortable with the basics:

1. **Expand content types:**
   - Add `--types dlc` for more variety
   - Experiment with announcements

2. **Automate checking:**
   - Set up daily cron job for `check_updates.py`
   - Review and post manually

3. **Track analytics:**
   - Note which game updates get most engagement
   - Adjust posting strategy accordingly

4. **Scale up:**
   - Increase `--limit` as you build posting rhythm
   - Add more games to track

## Full Documentation

For complete details, see:
- [SOCIAL_MEDIA_WORKFLOW.md](docs/SOCIAL_MEDIA_WORKFLOW.md) - Complete workflow guide
- [PROJECT_VISION.md](docs/PROJECT_VISION.md) - Content philosophy
- [TECHNICAL_ROADMAP.md](docs/TECHNICAL_ROADMAP.md) - Future enhancements

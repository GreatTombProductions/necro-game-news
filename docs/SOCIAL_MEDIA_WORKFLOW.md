# Social Media Content Workflow

Complete guide for generating and posting Instagram content from game updates.

## Quick Start

```bash
# 1. Generate posts from latest updates
python scripts/generate_social_posts.py --limit 5 --generate-images

# 2. Preview pending posts
python scripts/preview_social_posts.py

# 3. Preview specific post with image
python scripts/preview_social_posts.py --id 1 --preview

# 4. Manually post to Instagram (copy caption + upload image)

# 5. Mark as posted
python scripts/preview_social_posts.py --id 1 --mark-posted --post-id "instagram_12345"
```

## Content Generation Pipeline

### Step 1: Queue Updates for Social Media

The `generate_social_posts.py` script processes unprocessed game updates and adds them to the social media queue.

**Basic Usage:**
```bash
# Queue all unprocessed updates
python scripts/generate_social_posts.py

# Queue only patches (skip announcements)
python scripts/generate_social_posts.py --types patch

# Queue patches and DLC only
python scripts/generate_social_posts.py --types patch dlc

# Queue with limit
python scripts/generate_social_posts.py --limit 10

# Queue specific update by database ID
python scripts/generate_social_posts.py --update-id 42

# Generate images immediately (recommended)
python scripts/generate_social_posts.py --generate-images

# Check stats without queueing
python scripts/generate_social_posts.py --stats
```

**Options:**
- `--types`: Filter by update type (patch, announcement, dlc, event)
- `--limit`: Maximum number of updates to queue
- `--update-id`: Queue specific update by database ID
- `--platform`: Platform to queue for (default: instagram)
- `--generate-images`: Generate post images immediately
- `--stats`: Show statistics only

### Step 2: Preview and Review Posts

The `preview_social_posts.py` script lets you review queued posts before posting.

**Basic Usage:**
```bash
# Show all pending posts
python scripts/preview_social_posts.py

# Show specific post with full caption
python scripts/preview_social_posts.py --id 5

# Generate preview image for review
python scripts/preview_social_posts.py --id 5 --preview

# Show posted content
python scripts/preview_social_posts.py --status posted

# Show failed posts
python scripts/preview_social_posts.py --status failed
```

**Options:**
- `--id`: Specific queue entry ID
- `--status`: Filter by status (pending, posted, failed, cancelled)
- `--platform`: Filter by platform
- `--limit`: Maximum entries to show
- `--preview`: Generate preview image
- `--mark-posted`: Mark as posted after manual posting
- `--post-id`: Instagram post ID (for tracking)
- `--cancel`: Cancel a queued post

### Step 3: Manual Posting to Instagram

Currently, posting to Instagram is manual (API access requires approval):

1. **Preview the post:**
   ```bash
   python scripts/preview_social_posts.py --id 5 --preview
   ```

2. **Review generated content:**
   - Image saved to: `content/posts/preview_queue_5.jpg`
   - Caption printed to terminal

3. **Post to Instagram:**
   - Open Instagram app or web interface
   - Upload the generated image
   - Copy and paste the caption
   - Post!

4. **Mark as posted:**
   ```bash
   python scripts/preview_social_posts.py --id 5 --mark-posted --post-id "instagram_post_url_or_id"
   ```

### Step 4: Track Posted Content

```bash
# View recently posted content
python scripts/preview_social_posts.py --status posted --limit 10

# View posting statistics
python scripts/generate_report.py --social-stats
```

## Content Style Guide

### Philosophy
- **Minimal editorialization** - Let developers speak for themselves
- **Direct quotes** - Pull from patch notes and announcements
- **Visual focus** - Game images take center stage
- **Clean information** - Clear, informative text overlays

### Post Format

**Image Composition:**
- 1080x1080 Instagram square format
- Game header image as background (darkened for readability)
- Text overlay on bottom 35% of image:
  - Badge: Update type (UPDATE/ANNOUNCEMENT/DLC/EVENT)
  - Game name: Large, prominent
  - Update title: Medium, wrapped if needed

**Caption Format:**
```
[GAME NAME] - [Update Type]
[Update Title]

[First paragraph or excerpt from patch notes]

Posted: [Date]
Link: [Steam URL]

#necromancy #gaming #[gamename] [other hashtags]
```

### Update Type Handling

**Patches (`type: patch`):**
- Focus on changelog items
- Extract bullet points when available
- Badge color: Purple

**Announcements (`type: announcement`):**
- Use opening paragraph
- Good for sales, events, milestone announcements
- Badge color: Blue

**DLC (`type: dlc`):**
- Highlight new content
- Include pricing if available
- Badge color: Green

**Events (`type: event`):**
- Time-sensitive content
- Include event dates when available
- Badge color: Orange

## File Structure

```
backend/content_gen/
├── post_template.py        # Template generation
├── content_generator.py    # Database integration
└── image_compositor.py     # Image generation

content/
├── posts/                  # Generated post images
│   ├── queue_1.jpg
│   └── preview_queue_5.jpg
└── cache/                  # Cached game header images
    └── Diablo_IV.jpg

scripts/
├── generate_social_posts.py  # Queue updates
└── preview_social_posts.py   # Preview and manage
```

## Database Schema

The social media queue uses the `social_media_queue` table:

```sql
CREATE TABLE social_media_queue (
    id INTEGER PRIMARY KEY,
    update_id INTEGER,              -- Links to updates table
    platform TEXT,                  -- 'instagram', 'twitter', etc.
    content_text TEXT,              -- Generated caption
    image_path TEXT,                -- Path to generated image
    scheduled_time TIMESTAMP,       -- Future: scheduling
    status TEXT,                    -- 'pending', 'posted', 'failed', 'cancelled'
    post_id TEXT,                   -- Platform's post ID
    error_message TEXT,             -- Error details if failed
    created_at TIMESTAMP,
    posted_at TIMESTAMP
);
```

## Common Workflows

### Daily Content Generation
```bash
# Check for new updates
python scripts/check_updates.py

# Generate posts from new updates
python scripts/generate_social_posts.py --types patch dlc --generate-images

# Review pending posts
python scripts/preview_social_posts.py

# Post manually to Instagram
# (review images in content/posts/, copy captions)

# Mark as posted
python scripts/preview_social_posts.py --id <N> --mark-posted
```

### Bulk Content Preparation
```bash
# Queue all unprocessed patches
python scripts/generate_social_posts.py --types patch --generate-images

# Preview all pending
python scripts/preview_social_posts.py --limit 50

# Review images in content/posts/ directory
# Post in batches over several days
```

### Fixing Failed Posts
```bash
# Show failed posts
python scripts/preview_social_posts.py --status failed

# Regenerate image
python scripts/preview_social_posts.py --id <N> --preview

# Try posting again, then mark as posted or cancel
python scripts/preview_social_posts.py --id <N> --cancel
```

## Future Enhancements

### Phase 2.1: Automated Posting
Once Instagram API access is approved:
- Implement Meta Graph API integration
- Add automatic posting with scheduling
- Error handling and retry logic

### Phase 2.2: Content Scheduling
- Schedule posts at optimal times
- Batch scheduling for week/month
- Auto-scheduling based on update importance

### Phase 2.3: Multi-Platform
- Twitter/X support
- YouTube Shorts
- TikTok integration

### Phase 2.4: Analytics
- Track engagement metrics
- A/B testing for caption styles
- Optimal posting time analysis

## Troubleshooting

### Images not generating
- Check Pillow installation: `pip install Pillow`
- Verify image URLs are accessible
- Check `content/posts/` directory permissions

### Caption formatting issues
- Check for special characters in update content
- Verify database encoding (UTF-8)
- Test with `--preview` to see raw output

### Queue entries stuck in pending
- Use `--cancel` to remove
- Check `error_message` field
- Regenerate with `--preview`

### Steam images failing to download
- Check internet connection
- Verify Steam URLs are valid
- Check rate limiting
- Images cached in `content/cache/`

## Best Practices

1. **Review before posting** - Always preview images and captions
2. **Post consistently** - Aim for 1-2 posts per day maximum
3. **Filter content** - Focus on patches and DLC, skip minor announcements
4. **Track engagement** - Note which types of posts perform well
5. **Maintain quality** - Better to skip a post than force poor content
6. **Respect developers** - Keep quotes accurate and in context
7. **Stay on-brand** - Necromancy focus, informative tone

## Questions?

See also:
- [TECHNICAL_ROADMAP.md](TECHNICAL_ROADMAP.md) - Overall project roadmap
- [PROJECT_VISION.md](PROJECT_VISION.md) - Content philosophy
- Backend code documentation in `backend/content_gen/`
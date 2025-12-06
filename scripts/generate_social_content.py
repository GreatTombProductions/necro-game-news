#!/usr/bin/env python3
"""
Generate social media content with multiple variants.

Creates 3 caption variants and multiple image options for each game update,
with descriptive filenames and Steam tags in the image banners.

Usage:
    # Generate content for last 2 days (default)
    python scripts/generate_social_content.py

    # Generate for all unprocessed updates
    python scripts/generate_social_content.py --all

    # Generate for specific date onwards
    python scripts/generate_social_content.py --since 2025-12-01

    # Reprocess already-processed updates (for dev/testing)
    python scripts/generate_social_content.py --reprocess

    # Generate for specific update
    python scripts/generate_social_content.py --update-id 42

    # Use custom image
    python scripts/generate_social_content.py --update-id 42 --image-path ~/image.jpg
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.content_gen.content_generator import ContentGenerator
from backend.content_gen.image_compositor import ImageCompositor
from backend.content_gen.post_template import PostTemplate
from backend.scrapers.steam_api import SteamAPI


def sanitize_filename(text: str) -> str:
    """Convert text to safe filename component"""
    safe = "".join(c if c.isalnum() or c in (' ', '-') else '_' for c in text)
    safe = '_'.join(safe.split())
    return safe[:50]


def generate_caption_variants(template: PostTemplate, num_variants: int = 1) -> List[str]:
    """
    Generate multiple caption variants with different styles.
    """
    captions = []

    # Variant 1: Standard
    captions.append(template.generate_caption())

    # Variant 2: Shorter, punchier
    if template.update_content and num_variants > 1:
        import os
        from anthropic import Anthropic

        api_key = os.getenv('ANTHROPIC_API_KEY')
        if api_key:
            try:
                client = Anthropic(api_key=api_key)
                import re
                clean_content = re.sub(r'<[^>]+>', '', template.update_content)
                clean_content = re.sub(r'\s+', ' ', clean_content).strip()[:1000]

                message = client.messages.create(
                    model="claude-3-5-haiku-20241022",
                    max_tokens=100,
                    messages=[{
                        "role": "user",
                        "content": f"Write a single punchy sentence about this game update. Be enthusiastic and direct:\n\n{clean_content}"
                    }]
                )

                short_summary = message.content[0].text.strip()
                parts = [short_summary, ""]
                game_stats = template._format_game_stats()
                if game_stats:
                    parts.append("Game Info:")
                    parts.extend(game_stats)
                    parts.append("")
                parts.append(template._generate_hashtags())
                captions.append("\n".join(parts))

            except Exception as e:
                print(f"  Warning: Could not generate punchy variant: {e}")
                captions.append(captions[0])
        else:
            captions.append(captions[0])
    else:
        captions.append(captions[0])

    # Variant 3: Question/engagement focused
    if template.update_content and 'client' in locals() and num_variants > 2:
        try:
            message = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=100,
                messages=[{
                    "role": "user",
                    "content": f"Write a question to engage players about this update:\n\n{clean_content}"
                }]
            )

            question = message.content[0].text.strip()
            parts = [question, ""]
            game_stats = template._format_game_stats()
            if game_stats:
                parts.append("Game Info:")
                parts.extend(game_stats)
                parts.append("")
            parts.append(template._generate_hashtags())
            captions.append("\n".join(parts))

        except Exception:
            captions.append(captions[0])
    else:
        captions.append(captions[0])

    return captions[:num_variants]


def fetch_steam_screenshots(steam_id: int, max_screenshots: int = 3) -> List[str]:
    """Fetch multiple screenshot URLs from Steam API dynamically."""
    if not steam_id:
        return []

    api = SteamAPI()
    details = api.get_app_details(steam_id)

    if not details:
        return []

    screenshots = details.get('screenshots', [])
    urls = [s.get('path_full') for s in screenshots if s.get('path_full')]
    return urls[:max_screenshots]


def get_steam_header_image(steam_id: int) -> Optional[str]:
    """Fetch header image URL from Steam API dynamically."""
    if not steam_id:
        return None

    api = SteamAPI()
    details = api.get_app_details(steam_id)

    if not details:
        return None

    return details.get('header_image')


def get_image_urls_for_update(update_data: dict) -> List[str]:
    """
    Get image URLs for an update based on platform.

    For Steam games: Fetches screenshots dynamically from Steam API.
    For Battle.net games: Uses the update's image_url from the news API.
    Falls back to header_image_url if available.

    Returns:
        List of image URLs (may be empty if no images available)
    """
    image_urls = []
    steam_id = update_data.get('steam_id')
    source_platform = update_data.get('source_platform', 'steam')
    primary_platform = update_data.get('primary_platform', 'steam')

    # Determine which platform to use for images
    platform = source_platform or primary_platform

    if platform == 'steam' and steam_id:
        # Fetch screenshots dynamically from Steam API
        screenshots = fetch_steam_screenshots(steam_id)
        if screenshots:
            image_urls.extend(screenshots)

        # Also try to get header image as fallback
        if not image_urls:
            header = get_steam_header_image(steam_id)
            if header:
                image_urls.append(header)

    elif platform == 'battlenet':
        # Use the update's image_url from the Battle.net news API
        update_image = update_data.get('update_image_url')
        if update_image:
            image_urls.append(update_image)

    # Fallback to stored header_image_url if we still have nothing
    if not image_urls and update_data.get('header_image_url'):
        image_urls.append(update_data['header_image_url'])

    return image_urls[:3]  # Limit to 3 images


def generate_content_for_update(update_data: dict, custom_image_path: Optional[Path] = None):
    """Generate content variants for a single update"""

    print(f"  {update_data['game_name']} - {update_data['title'][:60]}...")

    # Generate template
    gen = ContentGenerator()
    template = gen.generate_post(update_data)

    # Parse genres/tags
    tags = []
    if update_data.get('genres'):
        try:
            tags = json.loads(update_data['genres'])
        except (json.JSONDecodeError, TypeError):
            pass

    # Create base filename with update ID for easy regeneration
    date_str = datetime.now().strftime("%Y%m%d")
    game_safe = sanitize_filename(update_data['game_name'])
    update_id = update_data['id']
    base_filename = f"{date_str}_{game_safe}"

    # Ensure directories exist
    posts_dir = Path('content/posts')
    captions_dir = Path('content/captions')
    posts_dir.mkdir(parents=True, exist_ok=True)
    captions_dir.mkdir(parents=True, exist_ok=True)

    # Generate captions
    captions = generate_caption_variants(template, num_variants=3)
    for i, caption in enumerate(captions, 1):
        caption_file = captions_dir / f"{base_filename}_caption_{update_id}_{i}.txt"
        with open(caption_file, 'w', encoding='utf-8') as f:
            f.write(caption)

    # Generate images
    compositor = ImageCompositor(output_dir=posts_dir)
    template_data = template.to_dict()

    if custom_image_path:
        # Use custom image
        output_file = f"{base_filename}_image_{update_id}_1.jpg"
        try:
            compositor.compose_from_template(
                template_data,
                output_filename=output_file,
                tags=tags[:4],
                local_image_path=custom_image_path
            )
        except Exception as e:
            print(f"    ✗ Error with custom image: {e}")
    else:
        # Get image URLs based on platform
        image_urls = get_image_urls_for_update(update_data)

        if not image_urls:
            print(f"    ⚠ No images available for {update_data['game_name']} - skipping image generation")
            print(f"      (Platform: {update_data.get('source_platform', 'unknown')}, "
                  f"Steam ID: {update_data.get('steam_id', 'none')})")
        else:
            for i, image_url in enumerate(image_urls, 1):
                output_file = f"{base_filename}_image_{update_id}_{i}.jpg"
                try:
                    compositor.compose_post_image(
                        image_url=image_url,
                        game_name=update_data['game_name'],
                        text_lines=template_data['image_specs']['overlay_text'],
                        update_type=update_data['update_type'],
                        output_filename=output_file,
                        tags=tags[:4]
                    )
                except Exception as e:
                    print(f"    ✗ Error generating image {i}: {e}")

    # Mark as processed
    gen.conn.execute(
        "UPDATE updates SET processed_for_social = 1 WHERE id = ?",
        (update_data['id'],)
    )
    gen.conn.commit()


def main():
    parser = argparse.ArgumentParser(
        description='Generate social media content with multiple variants'
    )
    parser.add_argument(
        '--update-id',
        type=int,
        help='Generate for specific update ID'
    )
    parser.add_argument(
        '--since',
        type=str,
        help='Generate for updates from this date onwards (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Generate for all unprocessed updates'
    )
    parser.add_argument(
        '--image-path',
        type=Path,
        help='Use custom image file (only with --update-id)'
    )
    parser.add_argument(
        '--reprocess',
        action='store_true',
        help='Reprocess already-processed updates (useful for dev/testing)'
    )

    args = parser.parse_args()

    print("=" * 80)
    print("Generating Social Media Content")
    print("=" * 80)
    print()

    with ContentGenerator() as gen:
        if args.update_id:
            # Single update
            update_data = gen.get_update_by_id(args.update_id)
            if not update_data:
                print(f"✗ Update ID {args.update_id} not found")
                return 1

            generate_content_for_update(update_data, custom_image_path=args.image_path)

        else:
            # Multiple updates
            if args.all:
                since_date = None
                print("Processing all unprocessed updates...")
            elif args.since:
                since_date = args.since
                print(f"Processing updates since {since_date}...")
            else:
                # Default: last 2 days
                from datetime import timedelta
                lookback_date = datetime.now() - timedelta(days=2)
                since_date = lookback_date.strftime('%Y-%m-%d')
                print(f"Processing updates from last 2 days (since {since_date})...")

            if args.image_path:
                print("Warning: --image-path is ignored when processing multiple updates")

            print()

            updates = gen.get_unprocessed_updates(
                since_date=since_date,
                ignore_processed=args.reprocess
            )

            if not updates:
                print("No unprocessed updates found")
                return 0

            print(f"Found {len(updates)} updates to process:")
            print()

            for update_data in updates:
                generate_content_for_update(update_data)

    print()
    print("=" * 80)
    print(f"✓ Content generated in:")
    print(f"  Images:   content/posts/")
    print(f"  Captions: content/captions/")
    print()
    print("💡 To regenerate content for a specific update (optionally with custom image):")
    print("   python scripts/generate_social_content.py --update-id <ID> --reprocess --image-path ~/image.jpg")
    print()
    print("   (Update IDs are in the filename: YYYYMMDD_GameName_type_<ID>_N)")
    print("=" * 80)

    return 0


if __name__ == '__main__':
    sys.exit(main())

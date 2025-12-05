#!/usr/bin/env python3
"""
Preview and manage social media queue

Usage:
    # Show all pending posts
    python scripts/preview_social_posts.py

    # Show specific queue entry
    python scripts/preview_social_posts.py --id 5

    # Show posts by status
    python scripts/preview_social_posts.py --status posted

    # Generate preview for specific entry
    python scripts/preview_social_posts.py --id 5 --preview

    # Mark as posted (after manual posting)
    python scripts/preview_social_posts.py --id 5 --mark-posted --post-id "instagram_12345"

    # Cancel a queued post
    python scripts/preview_social_posts.py --id 5 --cancel
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.content_gen.content_generator import ContentGenerator
from backend.content_gen.image_compositor import ImageCompositor


def main():
    parser = argparse.ArgumentParser(
        description='Preview and manage social media queue'
    )
    parser.add_argument(
        '--id',
        type=int,
        help='Queue entry ID'
    )
    parser.add_argument(
        '--status',
        choices=['pending', 'posted', 'failed', 'cancelled'],
        default='pending',
        help='Filter by status (default: pending)'
    )
    parser.add_argument(
        '--platform',
        default='instagram',
        help='Filter by platform (default: instagram)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=20,
        help='Maximum entries to show (default: 20)'
    )
    parser.add_argument(
        '--preview',
        action='store_true',
        help='Generate preview image (requires --id)'
    )
    parser.add_argument(
        '--mark-posted',
        action='store_true',
        help='Mark as posted (requires --id)'
    )
    parser.add_argument(
        '--post-id',
        help='Platform post ID (for --mark-posted)'
    )
    parser.add_argument(
        '--cancel',
        action='store_true',
        help='Cancel queued post (requires --id)'
    )
    parser.add_argument(
        '--export-caption',
        action='store_true',
        help='Export caption to text file (requires --id or exports all pending)'
    )

    args = parser.parse_args()

    with ContentGenerator() as gen:
        # Actions on specific queue entry
        if args.id:
            if args.mark_posted:
                mark_posted(gen, args.id, args.post_id)
                return
            elif args.cancel:
                cancel_post(gen, args.id)
                return
            elif args.export_caption:
                export_caption(gen, args.id)
                return
            elif args.preview:
                preview_entry(gen, args.id, generate_image=True)
                return
            else:
                # Show specific entry
                preview_entry(gen, args.id)
                return

        # Export all pending captions
        if args.export_caption:
            export_all_captions(gen, args.status, args.platform)
            return

        # List queue entries
        list_queue(gen, args.status, args.platform, args.limit)


def list_queue(gen: ContentGenerator, status: str, platform: str, limit: int):
    """List queue entries"""
    entries = gen.get_queue_entries(
        status=status,
        platform=platform,
        limit=limit
    )

    if not entries:
        print(f"\nNo {status} posts in {platform} queue")
        return

    print(f"\n{'='*80}")
    print(f"{platform.upper()} Queue - {status.upper()} Posts ({len(entries)})")
    print(f"{'='*80}\n")

    for entry in entries:
        print_entry_summary(entry)
        print()


def print_entry_summary(entry: dict):
    """Print summary of queue entry"""
    print(f"Queue ID: {entry['id']}")
    print(f"Game: {entry['game_name']}")
    print(f"Update: {entry['update_title']}")
    print(f"Status: {entry['status']}")

    if entry.get('image_path'):
        image_status = "✓" if Path(entry['image_path']).exists() else "✗"
        print(f"Image: {image_status} {entry['image_path']}")
    else:
        print(f"Image: Not generated")

    if entry.get('posted_at'):
        print(f"Posted: {entry['posted_at']}")
        if entry.get('post_id'):
            print(f"Post ID: {entry['post_id']}")

    if entry.get('error_message'):
        print(f"Error: {entry['error_message']}")

    print(f"Created: {entry['created_at']}")


def preview_entry(gen: ContentGenerator, queue_id: int, generate_image: bool = False):
    """Show detailed preview of queue entry"""
    # Get entry
    entries = gen.get_queue_entries(status='pending')
    entries.extend(gen.get_queue_entries(status='failed'))
    entries.extend(gen.get_queue_entries(status='posted'))

    entry = next((e for e in entries if e['id'] == queue_id), None)

    if not entry:
        print(f"✗ Queue entry {queue_id} not found")
        sys.exit(1)

    print(f"\n{'='*80}")
    print(f"Queue Entry #{queue_id} - Preview")
    print(f"{'='*80}\n")

    print_entry_summary(entry)

    print(f"\n{'='*80}")
    print("Caption Text")
    print(f"{'='*80}\n")
    print(entry['content_text'])

    # Generate image if requested
    if generate_image:
        print(f"\n{'='*80}")
        print("Generating Preview Image")
        print(f"{'='*80}\n")

        update_data = gen.get_update_by_id(entry['update_id'])
        if not update_data:
            print("✗ Update data not found")
            return

        template = gen.generate_post(update_data)
        template_data = template.to_dict()

        try:
            compositor = ImageCompositor()
            image_path = compositor.compose_from_template(
                template_data,
                output_filename=f"preview_queue_{queue_id}.jpg"
            )

            # Update queue with image path
            gen.update_queue_status(
                queue_id,
                status=entry['status'],
                image_path=str(image_path)
            )

            print(f"\n✓ Preview image saved: {image_path}")
            print(f"\nTo post manually:")
            print(f"  1. Review image at: {image_path}")
            print(f"  2. Copy caption (printed above)")
            print(f"  3. Post to Instagram")
            print(f"  4. Mark as posted: python scripts/preview_social_posts.py --id {queue_id} --mark-posted --post-id <instagram_post_id>")

        except Exception as e:
            print(f"✗ Error generating image: {e}")
            gen.update_queue_status(
                queue_id,
                status='failed',
                error_message=str(e)
            )


def mark_posted(gen: ContentGenerator, queue_id: int, post_id: str = None):
    """Mark queue entry as posted"""
    print(f"\nMarking queue entry {queue_id} as posted...")

    if not post_id:
        # Generate default post ID
        post_id = f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    try:
        gen.update_queue_status(
            queue_id,
            status='posted',
            post_id=post_id
        )
        print(f"✓ Entry {queue_id} marked as posted")
        print(f"  Post ID: {post_id}")
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


def cancel_post(gen: ContentGenerator, queue_id: int):
    """Cancel a queued post"""
    print(f"\nCancelling queue entry {queue_id}...")

    try:
        gen.update_queue_status(queue_id, status='cancelled')
        print(f"✓ Entry {queue_id} cancelled")
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


def export_caption(gen: ContentGenerator, queue_id: int):
    """Export caption for a specific queue entry to text file"""
    # Get entry
    entries = gen.get_queue_entries(status='pending')
    entries.extend(gen.get_queue_entries(status='failed'))

    entry = next((e for e in entries if e['id'] == queue_id), None)

    if not entry:
        print(f"✗ Queue entry {queue_id} not found")
        sys.exit(1)

    # Create caption directory if it doesn't exist
    caption_dir = Path('content/captions')
    caption_dir.mkdir(parents=True, exist_ok=True)

    # Create filename matching the image filename
    caption_file = caption_dir / f"queue_{queue_id}.txt"

    # Write caption to file
    with open(caption_file, 'w', encoding='utf-8') as f:
        f.write(entry['content_text'])

    print(f"\n✓ Caption exported to: {caption_file}")
    print(f"\nTo copy to clipboard (macOS):")
    print(f"  cat {caption_file} | pbcopy")
    print(f"\nTo copy to clipboard (Linux):")
    print(f"  cat {caption_file} | xclip -selection clipboard")


def export_all_captions(gen: ContentGenerator, status: str = 'pending',
                       platform: str = 'instagram'):
    """Export all captions matching status to text files"""
    entries = gen.get_queue_entries(status=status, platform=platform)

    if not entries:
        print(f"\nNo {status} posts in {platform} queue to export")
        return

    # Create caption directory
    caption_dir = Path('content/captions')
    caption_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*80}")
    print(f"Exporting {len(entries)} Captions")
    print(f"{'='*80}\n")

    for entry in entries:
        queue_id = entry['id']
        caption_file = caption_dir / f"queue_{queue_id}.txt"

        with open(caption_file, 'w', encoding='utf-8') as f:
            f.write(entry['content_text'])

        print(f"✓ Queue #{queue_id}: {entry['game_name']} - {entry['update_title'][:50]}")
        print(f"  → {caption_file}")

    print(f"\n✓ Exported {len(entries)} captions to {caption_dir}/")
    print(f"\nCaption files are named to match their image files:")
    print(f"  content/posts/queue_3.jpg  →  content/captions/queue_3.txt")


if __name__ == '__main__':
    main()
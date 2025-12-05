#!/usr/bin/env python3
"""
Generate and queue social media posts from unprocessed updates

Usage:
    # Queue all unprocessed updates
    python scripts/generate_social_posts.py

    # Queue only patches
    python scripts/generate_social_posts.py --types patch

    # Queue with limit
    python scripts/generate_social_posts.py --limit 10

    # Queue specific update by ID
    python scripts/generate_social_posts.py --update-id 42

    # Generate images immediately
    python scripts/generate_social_posts.py --generate-images
"""

import sys
import argparse
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.content_gen.content_generator import ContentGenerator
from backend.content_gen.image_compositor import ImageCompositor


def main():
    parser = argparse.ArgumentParser(
        description='Generate and queue social media posts from game updates'
    )
    parser.add_argument(
        '--types',
        nargs='+',
        choices=['patch', 'announcement', 'dlc', 'event'],
        help='Filter by update types'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Maximum number of updates to queue'
    )
    parser.add_argument(
        '--update-id',
        type=int,
        help='Queue specific update by ID'
    )
    parser.add_argument(
        '--platform',
        default='instagram',
        choices=['instagram', 'twitter', 'other'],
        help='Social media platform (default: instagram)'
    )
    parser.add_argument(
        '--generate-images',
        action='store_true',
        help='Generate post images immediately'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show statistics only, do not queue'
    )

    args = parser.parse_args()

    with ContentGenerator() as gen:
        # Stats mode
        if args.stats:
            unprocessed = gen.get_unprocessed_updates()
            print(f"\n{'='*60}")
            print("Unprocessed Updates Statistics")
            print(f"{'='*60}")
            print(f"Total unprocessed: {len(unprocessed)}")

            # Group by type
            by_type = {}
            for update in unprocessed:
                update_type = update['update_type']
                by_type[update_type] = by_type.get(update_type, 0) + 1

            print("\nBy type:")
            for update_type, count in sorted(by_type.items()):
                print(f"  {update_type:15} {count:3}")

            # Show pending queue
            pending = gen.get_queue_entries(status='pending', platform=args.platform)
            print(f"\nPending in {args.platform} queue: {len(pending)}")

            return

        # Queue specific update
        if args.update_id:
            print(f"\nQueueing update ID {args.update_id}...")
            try:
                queue_id = gen.queue_for_social(
                    args.update_id,
                    platform=args.platform
                )
                print(f"✓ Queued as entry #{queue_id}")

                if args.generate_images:
                    generate_image_for_queue_entry(gen, queue_id)

            except ValueError as e:
                print(f"✗ Error: {e}")
                sys.exit(1)

            return

        # Bulk queue
        print(f"\n{'='*60}")
        print("Queueing Unprocessed Updates")
        print(f"{'='*60}")

        if args.types:
            print(f"Types: {', '.join(args.types)}")
        if args.limit:
            print(f"Limit: {args.limit}")
        print(f"Platform: {args.platform}")
        print()

        queue_ids = gen.bulk_queue_unprocessed(
            platform=args.platform,
            limit=args.limit,
            update_types=args.types
        )

        print(f"\n✓ Queued {len(queue_ids)} updates")

        # Generate images if requested
        if args.generate_images and queue_ids:
            print(f"\n{'='*60}")
            print("Generating Images")
            print(f"{'='*60}\n")

            compositor = ImageCompositor()

            for queue_id in queue_ids:
                generate_image_for_queue_entry(gen, queue_id, compositor)


def generate_image_for_queue_entry(gen: ContentGenerator, queue_id: int,
                                   compositor: ImageCompositor = None):
    """Generate image for a specific queue entry"""
    if compositor is None:
        compositor = ImageCompositor()

    # Get queue entry
    entries = gen.get_queue_entries(status='pending')
    entry = next((e for e in entries if e['id'] == queue_id), None)

    if not entry:
        print(f"✗ Queue entry {queue_id} not found")
        return

    # Get update data
    update_data = gen.get_update_by_id(entry['update_id'])
    if not update_data:
        print(f"✗ Update {entry['update_id']} not found")
        return

    # Generate post template
    template = gen.generate_post(update_data)
    template_data = template.to_dict()

    # Generate image
    try:
        print(f"Generating image for: {update_data['game_name']} - {update_data['title'][:50]}...")

        image_path = compositor.compose_from_template(
            template_data,
            output_filename=f"queue_{queue_id}.jpg"
        )

        # Update queue entry with image path
        gen.update_queue_status(
            queue_id,
            status='pending',
            image_path=str(image_path)
        )

        print(f"  ✓ Image saved: {image_path}")

    except Exception as e:
        print(f"  ✗ Error generating image: {e}")
        gen.update_queue_status(
            queue_id,
            status='failed',
            error_message=str(e)
        )


if __name__ == '__main__':
    main()
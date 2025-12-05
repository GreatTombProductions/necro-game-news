#!/usr/bin/env python3
"""Test caption generation for Night Swarm update ID 190"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.content_gen.content_generator import ContentGenerator
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()

    # Check for API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("⚠️  WARNING: ANTHROPIC_API_KEY not set in .env file")
        print("   Caption will use fallback excerpt method instead of AI summaries")
        print("   To enable AI summaries, add your Anthropic API key to .env:")
        print("   ANTHROPIC_API_KEY=your_api_key_here")
        print()

    # Create content generator
    generator = ContentGenerator()

    # Get Night Swarm update (ID 190)
    update_data = generator.get_update_by_id(190)

    if not update_data:
        print("Error: Update ID 190 not found")
        return 1

    print("=" * 70)
    print("Night Swarm Update #190 - Caption Test")
    print("=" * 70)
    print()

    # Generate post
    template = generator.generate_post(update_data)
    caption = template.generate_caption()

    print(caption)
    print()
    print("=" * 70)

    generator.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())

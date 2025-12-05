"""
Image compositor for Instagram posts

Creates Instagram-ready images by:
1. Fetching game header images from Steam
2. Compositing with text overlays
3. Saving in Instagram-optimized format
"""

import io
import requests
from pathlib import Path
from typing import Tuple, Optional, List
from datetime import datetime

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
except ImportError:
    raise ImportError(
        "Pillow is required for image generation. "
        "Install with: pip install Pillow"
    )


class ImageCompositor:
    """Compose Instagram post images with game header + text overlay"""

    # Instagram specifications
    INSTAGRAM_SIZE = (1080, 1080)

    # Design constants
    OVERLAY_BACKGROUND = (0, 0, 0, 200)  # Semi-transparent black
    TEXT_COLOR_PRIMARY = (255, 255, 255)  # White
    TEXT_COLOR_SECONDARY = (200, 200, 200)  # Light gray
    BADGE_COLORS = {
        'UPDATE': (139, 92, 246),  # Purple
        'ANNOUNCEMENT': (59, 130, 246),  # Blue
        'DLC': (34, 197, 94),  # Green
        'EVENT': (251, 146, 60),  # Orange
        'RELEASE': (236, 72, 153),  # Pink
        'NEWS': (148, 163, 184),  # Gray
    }

    def __init__(self, output_dir: Optional[Path] = None,
                 cache_dir: Optional[Path] = None):
        """
        Initialize image compositor.

        Args:
            output_dir: Directory to save generated images (default: content/posts)
            cache_dir: Directory to cache downloaded images (default: content/cache)
        """
        self.output_dir = output_dir or Path('content/posts')
        self.cache_dir = cache_dir or Path('content/cache')

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch_game_image(self, image_url: str, game_name: str) -> Image.Image:
        """
        Fetch game header image from Steam.

        Args:
            image_url: URL to game's header image
            game_name: Game name (for cache filename)

        Returns:
            PIL Image object
        """
        # Create cache filename
        safe_name = "".join(c if c.isalnum() else "_" for c in game_name)
        cache_file = self.cache_dir / f"{safe_name}.jpg"

        # Check cache first
        if cache_file.exists():
            try:
                return Image.open(cache_file)
            except Exception:
                # Cache corrupted, re-download
                cache_file.unlink()

        # Download image
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            img = Image.open(io.BytesIO(response.content))

            # Cache for future use
            img.save(cache_file, 'JPEG', quality=95)

            return img
        except Exception as e:
            raise ValueError(f"Failed to fetch image from {image_url}: {e}")

    def prepare_background(self, game_image: Image.Image) -> Image.Image:
        """
        Prepare game image as background for Instagram post.

        Strategy:
        - Steam headers are typically 460x215
        - Need to create 1080x1080 square
        - Crop to square, zoom/blur edges, or use creative framing

        Args:
            game_image: Original game header image

        Returns:
            1080x1080 PIL Image
        """
        target_size = self.INSTAGRAM_SIZE

        # Strategy: Center crop to square, then scale up
        width, height = game_image.size

        # Calculate crop to square (center)
        if width > height:
            # Landscape: crop width
            crop_size = height
            left = (width - crop_size) // 2
            top = 0
            right = left + crop_size
            bottom = crop_size
        else:
            # Portrait or square: crop height
            crop_size = width
            left = 0
            top = (height - crop_size) // 2
            right = crop_size
            bottom = top + crop_size

        cropped = game_image.crop((left, top, right, bottom))

        # Scale to Instagram size
        scaled = cropped.resize(target_size, Image.Resampling.LANCZOS)

        # Slight darkening to make text more readable
        enhancer = ImageEnhance.Brightness(scaled)
        darkened = enhancer.enhance(0.7)

        return darkened

    def create_text_overlay(self, size: Tuple[int, int],
                           text_lines: List[str],
                           update_type: str) -> Image.Image:
        """
        Create text overlay image.

        Args:
            size: Image size (width, height)
            text_lines: List of [badge_text, game_name, update_title]
            update_type: Update type for badge color

        Returns:
            PIL Image with transparent background and text
        """
        # Create transparent overlay
        overlay = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Load fonts (with fallback to default)
        try:
            # Try to use system fonts
            font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 72)
            font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
            font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
            font_badge = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
        except Exception:
            # Fallback to default font
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
            font_badge = ImageFont.load_default()

        # Calculate overlay area (bottom 25% of image)
        overlay_height = int(size[1] * 0.35)
        overlay_top = size[1] - overlay_height

        # Draw semi-transparent background for text area
        draw.rectangle(
            [(0, overlay_top), (size[0], size[1])],
            fill=self.OVERLAY_BACKGROUND
        )

        # Position for text elements
        margin = 40
        current_y = overlay_top + margin

        # Draw badge (small, colored)
        badge_text = text_lines[0] if text_lines else "NEWS"
        badge_color = self.BADGE_COLORS.get(badge_text, self.BADGE_COLORS['NEWS'])

        # Badge background
        bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
        badge_width = bbox[2] - bbox[0] + 20
        badge_height = bbox[3] - bbox[1] + 10
        badge_x = margin

        draw.rounded_rectangle(
            [(badge_x, current_y), (badge_x + badge_width, current_y + badge_height)],
            radius=8,
            fill=badge_color
        )

        # Badge text
        draw.text(
            (badge_x + 10, current_y + 5),
            badge_text,
            fill=(255, 255, 255),
            font=font_badge
        )

        current_y += badge_height + 20

        # Draw game name (large, bold)
        if len(text_lines) > 1:
            game_name = text_lines[1]
            draw.text(
                (margin, current_y),
                game_name,
                fill=self.TEXT_COLOR_PRIMARY,
                font=font_large
            )
            current_y += 80

        # Draw update title (medium, wrapped if needed)
        if len(text_lines) > 2:
            update_title = text_lines[2]

            # Wrap text if too long
            wrapped_title = self._wrap_text(
                update_title,
                font_medium,
                size[0] - 2 * margin
            )

            for line in wrapped_title[:2]:  # Max 2 lines
                draw.text(
                    (margin, current_y),
                    line,
                    fill=self.TEXT_COLOR_SECONDARY,
                    font=font_medium
                )
                current_y += 55

        return overlay

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont,
                   max_width: int) -> List[str]:
        """
        Wrap text to fit within max_width.

        Args:
            text: Text to wrap
            font: Font to use for measurement
            max_width: Maximum width in pixels

        Returns:
            List of text lines
        """
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            # Use textbbox instead of deprecated textsize
            bbox = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox(
                (0, 0), test_line, font=font
            )
            width = bbox[2] - bbox[0]

            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return lines

    def compose_post_image(self, image_url: str, game_name: str,
                          text_lines: List[str], update_type: str,
                          output_filename: Optional[str] = None) -> Path:
        """
        Create complete Instagram post image.

        Args:
            image_url: URL to game header image
            game_name: Game name
            text_lines: [badge_text, game_name, update_title]
            update_type: Update type for styling
            output_filename: Custom filename (auto-generated if None)

        Returns:
            Path to saved image file
        """
        # Fetch and prepare background
        game_image = self.fetch_game_image(image_url, game_name)
        background = self.prepare_background(game_image)

        # Create text overlay
        overlay = self.create_text_overlay(
            self.INSTAGRAM_SIZE,
            text_lines,
            update_type
        )

        # Composite background + overlay
        final = Image.alpha_composite(
            background.convert('RGBA'),
            overlay
        )

        # Generate filename if not provided
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = "".join(c if c.isalnum() else "_" for c in game_name)
            output_filename = f"{timestamp}_{safe_name}.jpg"

        # Save
        output_path = self.output_dir / output_filename
        final.convert('RGB').save(output_path, 'JPEG', quality=95, optimize=True)

        print(f"✓ Post image saved: {output_path}")
        return output_path

    def compose_from_template(self, template_data: dict,
                             output_filename: Optional[str] = None) -> Path:
        """
        Create post image from template data.

        Args:
            template_data: Dictionary from PostTemplate.to_dict()
            output_filename: Custom filename (auto-generated if None)

        Returns:
            Path to saved image file
        """
        image_specs = template_data['image_specs']

        return self.compose_post_image(
            image_url=image_specs['game_image_url'],
            game_name=template_data['game_name'],
            text_lines=image_specs['overlay_text'],
            update_type=template_data.get('update_type', 'unknown'),
            output_filename=output_filename
        )


def create_post_image(game_image_url: str, game_name: str,
                     update_title: str, update_type: str,
                     output_dir: Optional[Path] = None) -> Path:
    """
    Convenience function to create a post image.

    Args:
        game_image_url: URL to game header image
        game_name: Game name
        update_title: Update title
        update_type: Update type (patch, announcement, etc.)
        output_dir: Output directory (default: content/posts)

    Returns:
        Path to saved image
    """
    compositor = ImageCompositor(output_dir=output_dir)

    type_display = {
        'patch': 'UPDATE',
        'announcement': 'ANNOUNCEMENT',
        'dlc': 'DLC',
        'event': 'EVENT',
        'unknown': 'NEWS'
    }.get(update_type, 'NEWS')

    text_lines = [type_display, game_name, update_title]

    return compositor.compose_post_image(
        image_url=game_image_url,
        game_name=game_name,
        text_lines=text_lines,
        update_type=update_type
    )
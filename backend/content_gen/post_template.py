"""
Instagram post template generator for Necro Game News

Design philosophy:
- Minimal editorialization - let the developers speak
- Use AI-generated summaries instead of direct quotes
- Game images are the visual focus
- Clean, informative text overlay with game stats
"""

import os
import json
from typing import Dict, Optional, List
from datetime import datetime
from anthropic import Anthropic


class PostTemplate:
    """Base template for Instagram posts"""

    # Instagram specifications
    INSTAGRAM_SIZE = (1080, 1350)  # 4:5 aspect ratio (recommended for feed)
    INSTAGRAM_STORY_SIZE = (1080, 1920)  # Story format (future)

    def __init__(self, game_name: str, game_image_url: str,
                 update_title: str, update_date: datetime,
                 update_type: str, update_content: Optional[str] = None,
                 steam_url: Optional[str] = None,
                 game_release_date: Optional[str] = None,
                 game_price_usd: Optional[float] = None,
                 game_genres: Optional[str] = None,
                 game_dimension_1: Optional[str] = None,
                 game_dimension_2: Optional[str] = None,
                 game_dimension_3: Optional[str] = None,
                 game_dimension_4: Optional[str] = None):
        """
        Initialize post template with update information

        Args:
            game_name: Name of the game
            game_image_url: URL to game's header image
            update_title: Title from Steam news
            update_date: Date of the update
            update_type: Type classification (patch, announcement, dlc, event, release)
            update_content: Full content text from Steam
            steam_url: Direct link to Steam news post
            game_release_date: Game's release date
            game_price_usd: Game's price in USD
            game_genres: JSON string of game genres
            game_dimension_1: Necromancy integration dimension
            game_dimension_2: POV dimension (character/unit)
            game_dimension_3: Naming dimension (explicit/implied)
            game_dimension_4: Availability dimension (instant/gated)
        """
        self.game_name = game_name
        self.game_image_url = game_image_url
        self.update_title = update_title
        self.update_date = update_date
        self.update_type = update_type
        self.update_content = update_content or ""
        self.steam_url = steam_url
        self.game_release_date = game_release_date
        self.game_price_usd = game_price_usd
        self.game_genres = game_genres
        self.game_dimension_1 = game_dimension_1
        self.game_dimension_2 = game_dimension_2
        self.game_dimension_3 = game_dimension_3
        self.game_dimension_4 = game_dimension_4

    def generate_caption(self) -> str:
        """
        Generate Instagram caption text.

        New format:
        [AI-generated 1-2 sentence summary]

        Game Info:
        - Release Date: [date]
        - Genres: [genres]
        - Price (US region): [price]
        - Necromancy: [degree description]

        #necromancy #gaming #[gamename]
        """
        # Build caption parts
        parts = []

        # AI-generated summary (1-2 sentences)
        if self.update_content:
            summary = self._generate_summary(self.update_content)
            if summary:
                parts.append(summary)
                parts.append("")

        # Game stats section
        game_stats = self._format_game_stats()
        if game_stats:
            parts.append("Game Info:")
            parts.extend(game_stats)
            parts.append("")

        # Update link
        if self.steam_url:
            parts.append(f"Link: {self.steam_url}")
            parts.append("")

        # Hashtags
        hashtags = self._generate_hashtags()
        parts.append(hashtags)

        return "\n".join(parts)

    def _generate_summary(self, content: str) -> str:
        """
        Use Claude API to generate a 1-2 sentence summary of the update content.

        Args:
            content: Full update content from Steam

        Returns:
            1-2 sentence summary, or fallback to excerpt if Claude fails
        """
        import re

        # Clean HTML tags
        clean_content = re.sub(r'<[^>]+>', '', content)
        clean_content = re.sub(r'\s+', ' ', clean_content).strip()

        # Truncate if too long for prompt (keep first ~2000 chars)
        content_truncated = len(clean_content) > 2000
        if content_truncated:
            clean_content = clean_content[:2000] + "..."

        try:
            # Initialize Anthropic client
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                # Fallback to excerpt if no API key
                return self._extract_excerpt(content, max_length=200)

            client = Anthropic(api_key=api_key)

            # Build prompt with URL fallback if available
            prompt_parts = [
                f"Game: {self.game_name}",
                f"Update Title: {self.update_title}",
                "",
                "Update Content:",
                clean_content,
            ]

            # Include URL for context if content might be insufficient
            if self.steam_url and (content_truncated or len(clean_content) < 100):
                prompt_parts.extend([
                    "",
                    f"Source URL (visit if content above is insufficient): {self.steam_url}"
                ])

            prompt_parts.extend([
                "",
                "Summarize this game update announcement in 1-2 concise sentences. Focus on what's new or changed. Do not use quotes or say 'the announcement says' - just state the facts directly. If the content is too short or unclear, use the game name and update title to write a brief, factual summary."
            ])

            # Generate summary
            message = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=150,
                messages=[{
                    "role": "user",
                    "content": "\n".join(prompt_parts)
                }]
            )

            summary = message.content[0].text.strip()
            return summary

        except Exception as e:
            # Fallback to excerpt if Claude API fails
            print(f"Warning: Claude API failed, using excerpt: {e}")
            return self._extract_excerpt(content, max_length=200)

    def _format_game_stats(self) -> List[str]:
        """
        Format game statistics for Instagram caption.

        Returns:
            List of stat lines (e.g., ["- Release Date: Jan 1, 2024", ...])
        """
        stats = []

        # Release date
        if self.game_release_date:
            stats.append(f"- Release Date: {self.game_release_date}")

        # Genres (parse JSON if needed)
        if self.game_genres:
            try:
                if isinstance(self.game_genres, str):
                    genres_list = json.loads(self.game_genres)
                else:
                    genres_list = self.game_genres

                if genres_list:
                    genres_str = ', '.join(genres_list)
                    stats.append(f"- Genres: {genres_str}")
            except (json.JSONDecodeError, TypeError):
                pass

        # Price
        if self.game_price_usd is not None:
            if self.game_price_usd == 0.0:
                stats.append("- Price (US region): Free")
            else:
                stats.append(f"- Price (US region): ${self.game_price_usd:.2f}")

        # Necromancy degree
        if self.game_dimension_1:
            necro_desc = {
                'a': 'Central to character/unit identity and gameplay',
                'b': 'Dedicated specialization available',
                'c': 'Some necromancy skills or items present',
                'd': 'Necromantic by technicality or lore (minimal impact on identity/gameplay)'
            }.get(self.game_dimension_1, 'Unknown')
            stats.append(f"- Necromancy: {necro_desc}")

        # Availability
        if self.game_dimension_4:
            availability_desc = {
                'instant': 'Available from the start',
                'gated': 'Requires unlocking/luck/progression'
            }.get(self.game_dimension_4, 'Unknown')
            stats.append(f"- Necromancy Availability: {availability_desc}")

        return stats

    def _extract_excerpt(self, content: str, max_length: int = 300) -> str:
        """
        Extract a clean excerpt from update content.

        Strategy:
        1. Try to get first complete paragraph
        2. If too long, truncate at sentence boundary
        3. Remove HTML tags and excessive whitespace
        """
        # Remove HTML tags (basic cleanup)
        import re
        clean = re.sub(r'<[^>]+>', '', content)

        # Normalize whitespace
        clean = re.sub(r'\s+', ' ', clean).strip()

        # Get first paragraph (up to double newline or max length)
        paragraphs = clean.split('\n\n')
        if paragraphs:
            first_para = paragraphs[0].strip()

            # If paragraph is reasonable length, use it
            if len(first_para) <= max_length:
                return first_para

            # Otherwise, truncate at sentence boundary
            sentences = re.split(r'(?<=[.!?])\s+', first_para)
            excerpt = ""
            for sentence in sentences:
                if len(excerpt) + len(sentence) + 1 <= max_length:
                    excerpt += sentence + " "
                else:
                    break

            if excerpt:
                return excerpt.strip()

        # Fallback: hard truncate with ellipsis
        if len(clean) > max_length:
            return clean[:max_length-3].rsplit(' ', 1)[0] + '...'

        return clean

    def _generate_hashtags(self) -> str:
        """Generate relevant hashtags for the post"""
        # Core hashtags
        tags = ['necromancy', 'gaming', 'gamedev', 'indiegames']

        # Add game-specific tag (sanitized)
        game_tag = self.game_name.lower().replace(' ', '').replace(':', '')
        game_tag = ''.join(c for c in game_tag if c.isalnum())
        if game_tag:
            tags.append(game_tag)

        # Add type-specific tags
        type_tags = {
            'patch': ['gameupdate', 'patchnotes'],
            'announcement': ['gamingnews'],
            'dlc': ['dlc', 'expansion'],
            'event': ['gamingevent'],
            'release': ['newgame', 'gamelaunch', 'gamedevelopment']
        }
        tags.extend(type_tags.get(self.update_type, []))

        return ' '.join(f'#{tag}' for tag in tags)

    def get_image_specs(self) -> Dict:
        """
        Get specifications for image generation.

        Returns dict with:
        - size: (width, height) tuple
        - game_image_url: URL to fetch game header image
        - overlay_text: Text to overlay on image (if any)
        - overlay_position: Position for text overlay
        """
        return {
            'size': self.INSTAGRAM_SIZE,
            'game_image_url': self.game_image_url,
            'overlay_text': self._get_overlay_text(),
            'overlay_position': 'bottom',  # 'top', 'bottom', 'center'
            'overlay_height_ratio': 0.25,  # Portion of image for text overlay
        }

    def _get_overlay_text(self) -> List[str]:
        """
        Get text lines to overlay on image.

        Returns list of text lines for overlay:
        - Line 1: Update type badge
        - Line 2: Game name
        - Line 3: Update title (truncated if needed)
        """
        type_display = {
            'patch': 'UPDATE',
            'announcement': 'ANNOUNCEMENT',
            'dlc': 'DLC',
            'event': 'EVENT',
            'release': 'RELEASE',
            'unknown': 'NEWS'
        }.get(self.update_type, 'NEWS')

        # Truncate title if too long
        title = self.update_title
        if len(title) > 60:
            title = title[:57] + '...'

        return [
            type_display,  # Small badge text
            self.game_name,  # Large game name
            title,  # Medium update title
        ]

    def to_dict(self) -> Dict:
        """Export template data as dictionary for database storage"""
        return {
            'caption': self.generate_caption(),
            'image_specs': self.get_image_specs(),
            'game_name': self.game_name,
            'update_title': self.update_title,
            'update_date': self.update_date.isoformat(),
            'steam_url': self.steam_url,
        }


class PatchTemplate(PostTemplate):
    """Template specialized for patch/update posts"""

    def _extract_excerpt(self, content: str, max_length: int = 300) -> str:
        """
        For patches, prioritize finding bullet points or changelog items.
        """
        import re

        # Look for common changelog patterns
        lines = content.split('\n')

        # Try to find bullet points or numbered items
        changelog_lines = []
        for line in lines[:10]:  # Check first 10 lines
            clean_line = line.strip()
            # Match bullet points, dashes, or numbered lists
            if re.match(r'^[\*\-\•]\s+', clean_line) or re.match(r'^\d+[\.\)]\s+', clean_line):
                changelog_lines.append(clean_line)
                if sum(len(l) for l in changelog_lines) > max_length:
                    break

        if changelog_lines:
            excerpt = '\n'.join(changelog_lines[:5])  # Max 5 items
            return excerpt

        # Fall back to parent method
        return super()._extract_excerpt(content, max_length)


class AnnouncementTemplate(PostTemplate):
    """Template for announcements (sales, events, etc)"""

    def _get_overlay_text(self) -> List[str]:
        """Announcements might have different visual style"""
        lines = super()._get_overlay_text()
        # Could customize overlay for announcements
        return lines


class DLCTemplate(PostTemplate):
    """Template for DLC/expansion announcements"""

    def _generate_hashtags(self) -> str:
        """DLC posts get additional relevant hashtags"""
        tags = super()._generate_hashtags()
        # Already includes #dlc #expansion from parent
        return tags


def create_template(game_name: str, game_image_url: str,
                   update_title: str, update_date: datetime,
                   update_type: str, update_content: Optional[str] = None,
                   steam_url: Optional[str] = None,
                   game_release_date: Optional[str] = None,
                   game_price_usd: Optional[float] = None,
                   game_genres: Optional[str] = None,
                   game_dimension_1: Optional[str] = None,
                   game_dimension_2: Optional[str] = None,
                   game_dimension_3: Optional[str] = None,
                   game_dimension_4: Optional[str] = None) -> PostTemplate:
    """
    Factory function to create appropriate template based on update type.

    Args:
        game_name: Name of the game
        game_image_url: URL to game header image
        update_title: Title from Steam news
        update_date: Date of the update
        update_type: Type classification (patch, announcement, dlc, event, release)
        update_content: Full content text from Steam
        steam_url: Direct link to Steam news post
        game_release_date: Game's release date
        game_price_usd: Game's price in USD
        game_genres: JSON string of game genres
        game_dimension_1: Necromancy integration dimension
        game_dimension_2: POV dimension (character/unit)
        game_dimension_3: Naming dimension (explicit/implied)
        game_dimension_4: Availability dimension (instant/gated)

    Returns:
        Appropriate PostTemplate subclass instance
    """
    template_map = {
        'patch': PatchTemplate,
        'dlc': DLCTemplate,
        'announcement': AnnouncementTemplate,
        'event': AnnouncementTemplate,
    }

    template_class = template_map.get(update_type, PostTemplate)

    return template_class(
        game_name=game_name,
        game_image_url=game_image_url,
        update_title=update_title,
        update_date=update_date,
        update_type=update_type,
        update_content=update_content,
        steam_url=steam_url,
        game_release_date=game_release_date,
        game_price_usd=game_price_usd,
        game_genres=game_genres,
        game_dimension_1=game_dimension_1,
        game_dimension_2=game_dimension_2,
        game_dimension_3=game_dimension_3,
        game_dimension_4=game_dimension_4
    )
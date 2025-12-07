"""
Steam API client for Necro Game News.

Handles communication with Steam's Web API for fetching game details,
news, and updates with proper rate limiting and error handling.

API Documentation:
- Store API: https://wiki.teamfortress.com/wiki/User:RJackson/StorefrontAPI
- Steam Web API: https://steamcommunity.com/dev
"""

import os
import time
import requests
import logging
from typing import Optional, Dict, List
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

# API Configuration
STEAM_API_KEY = os.getenv('STEAM_API_KEY')
STORE_API_BASE = "https://store.steampowered.com/api"
STEAM_API_BASE = "https://api.steampowered.com"
STEAMSPY_API_BASE = "https://steamspy.com/api.php"

# Rate limiting: Steam allows ~200 requests per 5 minutes
DEFAULT_RATE_LIMIT_DELAY = 1.5  # seconds between requests


class SteamAPIError(Exception):
    """Base exception for Steam API errors"""
    pass


class RateLimitError(SteamAPIError):
    """Raised when Steam API returns 429 Too Many Requests"""
    pass


class SteamAPI:
    """Steam API client with rate limiting"""
    
    def __init__(self, api_key: Optional[str] = None, rate_limit_delay: float = DEFAULT_RATE_LIMIT_DELAY):
        """
        Initialize Steam API client.
        
        Args:
            api_key: Steam API key (uses env var if not provided)
            rate_limit_delay: Seconds to wait between API calls
        """
        self.api_key = api_key or STEAM_API_KEY
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
        
        if not self.api_key:
            logger.warning("No Steam API key found. Some endpoints may not work.")
    
    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, params: Optional[Dict] = None, timeout: int = 10, retries: int = 3) -> Dict:
        """
        Make a request to Steam API with error handling and retry logic.

        Args:
            url: Full URL to request
            params: Query parameters
            timeout: Request timeout in seconds
            retries: Number of retries for rate limit errors

        Returns:
            JSON response as dict

        Raises:
            RateLimitError: If rate limited after all retries
            SteamAPIError: If request fails for other reasons
        """
        self._rate_limit()

        last_error = None
        for attempt in range(retries):
            try:
                response = requests.get(url, params=params, timeout=timeout)

                # Handle rate limiting with retry
                if response.status_code == 429:
                    backoff = min(60, 5 * (2 ** attempt))  # 5s, 10s, 20s...
                    logger.warning(f"Rate limited (429), backing off {backoff}s (attempt {attempt + 1}/{retries})")
                    time.sleep(backoff)
                    last_error = RateLimitError(f"Rate limited: {url}")
                    continue

                response.raise_for_status()
                return response.json()

            except requests.exceptions.Timeout:
                last_error = SteamAPIError(f"Request timed out: {url}")
                if attempt < retries - 1:
                    time.sleep(2)
                    continue
                raise last_error
            except requests.exceptions.RequestException as e:
                if '429' in str(e):
                    backoff = min(60, 5 * (2 ** attempt))
                    logger.warning(f"Rate limited, backing off {backoff}s (attempt {attempt + 1}/{retries})")
                    time.sleep(backoff)
                    last_error = RateLimitError(f"Rate limited: {e}")
                    continue
                raise SteamAPIError(f"Request failed: {e}")
            except ValueError as e:
                raise SteamAPIError(f"Invalid JSON response: {e}")

        # All retries exhausted
        if last_error:
            raise last_error
        raise SteamAPIError(f"Request failed after {retries} attempts")
    
    def get_app_details(self, appid: int) -> Optional[Dict]:
        """
        Get detailed information about a Steam app.

        Args:
            appid: Steam App ID

        Returns:
            Dictionary with app details, or None if not found/failed

        Raises:
            RateLimitError: If rate limited after all retries (caller should not mark as processed)
        """
        url = f"{STORE_API_BASE}/appdetails"
        params = {'appids': appid, 'l': 'english', 'cc': 'us'}

        try:
            data = self._make_request(url, params)

            # Check if request was successful
            app_data = data.get(str(appid), {})
            if not app_data.get('success', False):
                logger.warning(f"App {appid} not found or request failed")
                return None

            return app_data.get('data', {})

        except RateLimitError:
            # Re-raise rate limit errors so caller can handle them specially
            raise
        except SteamAPIError as e:
            logger.error(f"Error fetching details for app {appid}: {e}")
            return None
    
    def get_app_news(self, appid: int, count: int = 10, max_length: int = 300) -> List[Dict]:
        """
        Get news/updates for a Steam app.

        Args:
            appid: Steam App ID
            count: Number of news items to retrieve (default: 10)
            max_length: Maximum length of news content (default: 300)

        Returns:
            List of news items, each as a dictionary

        Raises:
            RateLimitError: If rate limited after all retries
        """
        url = f"{STEAM_API_BASE}/ISteamNews/GetNewsForApp/v2/"
        params = {
            'appid': appid,
            'count': count,
            'maxlength': max_length
        }

        try:
            data = self._make_request(url, params)
            news_items = data.get('appnews', {}).get('newsitems', [])
            return news_items

        except RateLimitError:
            # Re-raise rate limit errors so caller can handle them
            raise
        except SteamAPIError as e:
            logger.error(f"Error fetching news for app {appid}: {e}")
            return []

    def get_app_tags(self, appid: int, max_tags: int = 10) -> List[str]:
        """
        Get user-generated tags for a Steam app from Steamspy.

        Args:
            appid: Steam App ID
            max_tags: Maximum number of tags to return (default: 10)

        Returns:
            List of tag names, sorted by vote count (most popular first)
        """
        url = STEAMSPY_API_BASE
        params = {
            'request': 'appdetails',
            'appid': appid
        }

        try:
            data = self._make_request(url, params)
            tags = data.get('tags', {})

            # Steamspy sometimes returns an empty list instead of a dict
            if not isinstance(tags, dict):
                return []

            # Sort tags by vote count (descending) and return top N
            sorted_tags = sorted(tags.items(), key=lambda x: x[1], reverse=True)
            return [tag for tag, _ in sorted_tags[:max_tags]]

        except SteamAPIError as e:
            logger.warning(f"Error fetching tags for app {appid}: {e}")
            return []
    
    def parse_app_details(self, app_data: Dict, fetch_tags: bool = True) -> Dict:
        """
        Parse and extract relevant fields from app details response.

        Args:
            app_data: Raw app details from Steam API
            fetch_tags: Whether to fetch tags from Steamspy (default: True)

        Returns:
            Dictionary with cleaned/parsed data
        """
        # Get first screenshot (highest quality for social media)
        screenshots = app_data.get('screenshots', [])
        screenshot_url = screenshots[0].get('path_full') if screenshots else None

        # Parse price (in USD cents, convert to dollars)
        price_usd = None
        price_overview = app_data.get('price_overview')
        if price_overview:
            # Price is in cents (e.g., 1999 = $19.99)
            final_price = price_overview.get('final')
            if final_price is not None:
                price_usd = final_price / 100.0
        elif app_data.get('is_free', False):
            price_usd = 0.0

        # Get tags from Steamspy if requested
        tags = []
        if fetch_tags:
            steam_id = app_data.get('steam_appid')
            if steam_id:
                tags = self.get_app_tags(steam_id)

        return {
            'steam_id': app_data.get('steam_appid'),
            'name': app_data.get('name'),
            'app_type': app_data.get('type'),  # 'game', 'dlc', etc.
            'short_description': app_data.get('short_description'),
            'header_image': app_data.get('header_image'),
            'screenshot_url': screenshot_url,  # High-res 1920x1080 for Instagram
            'developer': ', '.join(app_data.get('developers', [])),
            'publisher': ', '.join(app_data.get('publishers', [])),
            'release_date': app_data.get('release_date', {}).get('date'),
            'price_usd': price_usd,
            'genres': [g.get('description') for g in app_data.get('genres', [])],
            'categories': [c.get('description') for c in app_data.get('categories', [])],
            'tags': tags  # User-generated tags from Steamspy
        }
    
    def is_steam_official(self, news_item: Dict) -> bool:
        """
        Check if a news item is from an official Steam source (not external press).

        Args:
            news_item: News item from Steam API

        Returns:
            True if from official Steam/developer source, False if from external press
        """
        feedlabel = news_item.get('feedlabel', '').lower()
        url = news_item.get('url', '')

        # Known external press sources to exclude
        external_sources = [
            'pc gamer', 'pcgamesn', 'pcgamer', 'ign', 'kotaku', 'polygon',
            'vg247', 'eurogamer', 'gamingonlinux', 'cgmagazine', 'rock paper shotgun',
            'gamespot', 'destructoid', 'gamesradar', 'thegamer'
        ]

        # Check feedlabel for external sources
        if any(source in feedlabel for source in external_sources):
            return False

        # Check URL pattern - external posts have the source name in the URL
        if '/externalpost/' in url:
            # Only steam_community_announcements are official
            if 'steam_community_announcement' not in url.lower():
                return False

        return True

    def classify_update_type(self, news_item: Dict) -> str:
        """
        Classify an update as patch/announcement/dlc/event/release based on content.

        Classification strategy:
        1. First check Steam's tags array (most reliable when present)
        2. Fall back to keyword-based classification (conservative - err toward announcement)

        For our purposes:
        - UPDATE (actual game changes): patch, release, dlc
        - ANNOUNCEMENT (news/promos): announcement, event

        We err on the side of "announcement" since it's easier to manually
        reclassify missed updates than fix false positives.

        Args:
            news_item: News item from Steam API

        Returns:
            Update type: 'patch', 'announcement', 'dlc', 'event', 'release'
        """
        tags = news_item.get('tags', [])
        title = news_item.get('title', '').lower()
        feedlabel = news_item.get('feedlabel', '').lower()

        # =================================================================
        # STEP 1: Check Steam's tags (most reliable when present)
        # =================================================================
        TAG_MAPPING = {
            'patchnotes': 'patch',
            'steam_award_nomination_request': 'announcement',
            'vo_marketing_message': 'announcement',
            'workshop': 'announcement',
        }

        IGNORE_TAGS = {'mod_reviewed', 'mod_require_rereview', 'mod_hide_library_overview', 'hide_store'}

        for tag in tags:
            if tag in IGNORE_TAGS or tag.startswith('ModAct_'):
                continue
            if tag in TAG_MAPPING:
                return TAG_MAPPING[tag]

        # =================================================================
        # STEP 2: Check for announcement indicators (push toward announcement)
        # =================================================================
        # If these keywords appear, it's likely an announcement about future content
        announcement_indicators = [
            'coming soon', 'announced', 'announcing', 'teaser', 'reveal',
            'upcoming', 'sneak peek', 'preview', 'first look', 'trailer',
            'wishlist', 'coming in', 'coming to', 'will be', 'will feature',
            'roadmap', 'dev diary', 'developer update', 'dev update',
            'behind the scenes', 'interview', 'ama', 'q&a'
        ]

        if any(indicator in title for indicator in announcement_indicators):
            return 'announcement'

        # =================================================================
        # STEP 3: Strong update indicators (require high confidence)
        # =================================================================
        # Release indicators - must be in title to count
        release_indicators = [
            'is now live', 'now available', 'out now', 'has launched',
            'launch day', 'release day', 'officially released'
        ]

        if any(indicator in title for indicator in release_indicators):
            # Could be a release or DLC release
            dlc_keywords = ['dlc', 'expansion', 'content pack', 'season pass']
            if any(kw in title for kw in dlc_keywords):
                return 'dlc'
            return 'release'

        # "Season X Now Live" = content release
        if 'season' in title and ('now live' in title or 'is live' in title):
            return 'release'

        # Patch indicators - require strong signals IN TITLE (not just body)
        patch_title_keywords = [
            'patch', 'hotfix', 'bugfix', 'bug fix', 'patch notes',
            'changelog', 'maintenance'
        ]

        if any(keyword in title for keyword in patch_title_keywords):
            return 'patch'

        # Steam's feedlabel is reliable for actual product updates
        if feedlabel == 'product update':
            return 'patch'

        # =================================================================
        # STEP 4: Events (promotional)
        # =================================================================
        event_keywords = [
            'steam awards', 'vote for', 'nominate',
            'contest', 'giveaway', 'tournament',
            'free weekend', 'free to play weekend'
        ]

        if any(keyword in title for keyword in event_keywords):
            return 'event'

        # Sales/discounts (not launches)
        if ('sale' in title or 'discount' in title or '% off' in title):
            if 'launch' not in title and 'release' not in title:
                return 'event'

        # =================================================================
        # STEP 5: Default to announcement (conservative)
        # =================================================================
        return 'announcement'
    
    def parse_news_item(self, news_item: Dict, appid: int) -> Dict:
        """
        Parse a news item into a standardized format.
        
        Args:
            news_item: Raw news item from Steam API
            appid: Steam App ID
            
        Returns:
            Cleaned news item dictionary
        """
        return {
            'steam_appid': appid,
            'gid': news_item.get('gid'),  # Unique identifier
            'title': news_item.get('title'),
            'url': news_item.get('url'),
            'contents': news_item.get('contents'),
            'feedlabel': news_item.get('feedlabel'),
            'date': datetime.fromtimestamp(news_item.get('date', 0)),
            'update_type': self.classify_update_type(news_item)
        }


def test_api():
    """Test the Steam API with a known game"""
    print("Testing Steam API...")
    print("=" * 60)
    
    api = SteamAPI()
    
    # Test with Diablo IV
    appid = 2344520
    print(f"\nFetching details for app {appid}...")
    
    details = api.get_app_details(appid)
    if details:
        parsed = api.parse_app_details(details)
        print(f"✓ Name: {parsed['name']}")
        print(f"  Type: {parsed['app_type']}")
        print(f"  Developer: {parsed['developer']}")
        print(f"  Genres: {', '.join(parsed['genres'])}")
    else:
        print("✗ Failed to fetch app details")
    
    print(f"\nFetching news for app {appid}...")
    news = api.get_app_news(appid, count=5)
    print(f"✓ Found {len(news)} news items")
    
    for item in news[:3]:
        parsed = api.parse_news_item(item, appid)
        print(f"\n  [{parsed['update_type'].upper()}] {parsed['title']}")
        print(f"  Date: {parsed['date']}")
        print(f"  GID: {parsed['gid']}")
    
    print("\n" + "=" * 60)
    print("✓ API test complete")


if __name__ == "__main__":
    # Set up basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    test_api()

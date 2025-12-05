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
    
    def _make_request(self, url: str, params: Optional[Dict] = None, timeout: int = 10) -> Dict:
        """
        Make a request to Steam API with error handling.
        
        Args:
            url: Full URL to request
            params: Query parameters
            timeout: Request timeout in seconds
            
        Returns:
            JSON response as dict
            
        Raises:
            SteamAPIError: If request fails
        """
        self._rate_limit()
        
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise SteamAPIError(f"Request timed out: {url}")
        except requests.exceptions.RequestException as e:
            raise SteamAPIError(f"Request failed: {e}")
        except ValueError as e:
            raise SteamAPIError(f"Invalid JSON response: {e}")
    
    def get_app_details(self, appid: int) -> Optional[Dict]:
        """
        Get detailed information about a Steam app.
        
        Args:
            appid: Steam App ID
            
        Returns:
            Dictionary with app details, or None if not found/failed
        """
        url = f"{STORE_API_BASE}/appdetails"
        params = {'appids': appid}
        
        try:
            data = self._make_request(url, params)
            
            # Check if request was successful
            app_data = data.get(str(appid), {})
            if not app_data.get('success', False):
                logger.warning(f"App {appid} not found or request failed")
                return None
            
            return app_data.get('data', {})
            
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
        2. Fall back to keyword-based classification

        For our purposes:
        - UPDATE (game changes): patch, release, dlc
        - ANNOUNCEMENT (news): announcement, event

        Args:
            news_item: News item from Steam API

        Returns:
            Update type: 'patch', 'announcement', 'dlc', 'event', 'release'
        """
        tags = news_item.get('tags', [])
        title = news_item.get('title', '').lower()
        contents = news_item.get('contents', '').lower()
        feedlabel = news_item.get('feedlabel', '').lower()

        # =================================================================
        # STEP 1: Check Steam's tags (most reliable when present)
        # =================================================================
        # Steam tag -> our classification mapping
        TAG_MAPPING = {
            # Update types (game changes)
            'patchnotes': 'patch',
            # Announcement types (news/promotional)
            'steam_award_nomination_request': 'announcement',
            'vo_marketing_message': 'announcement',
            'workshop': 'announcement',
        }

        # Tags to ignore (moderation-related)
        IGNORE_TAGS = {'mod_reviewed', 'mod_require_rereview', 'mod_hide_library_overview', 'hide_store'}

        for tag in tags:
            # Skip moderation tags and ModAct_* tags
            if tag in IGNORE_TAGS or tag.startswith('ModAct_'):
                continue
            if tag in TAG_MAPPING:
                return TAG_MAPPING[tag]

        # =================================================================
        # STEP 2: Fall back to keyword-based classification
        # =================================================================
        # Combined text for analysis (title weighted more heavily)
        title_text = title * 2  # Title is more important than body
        text = f"{title_text} {contents}"

        # PRIORITY 1: Game releases/launches (highest priority)
        release_title_keywords = [
            'is now live', 'now available', 'out now', 'has launched',
            'launch day', 'release day', 'officially released'
        ]

        # Strong release indicators in title = definite release
        if any(keyword in title for keyword in release_title_keywords):
            return 'release'

        # "Season X Now Live" type announcements are content updates (releases)
        if 'season' in title and ('now live' in title or 'is live' in title):
            return 'release'

        # Release keywords with supporting context
        release_keywords = ['launch', 'release', 'launches', 'released']
        if any(keyword in title for keyword in release_keywords):
            # Make sure it's not about a patch release
            if not any(word in title for word in ['patch', 'hotfix', 'update ', 'version']):
                return 'release'

        # PRIORITY 2: Patches/updates
        patch_keywords = [
            'patch', 'hotfix', 'bugfix', 'bug fix',
            'maintenance', 'changelog', 'fixed',
            'balance change', 'nerf', 'buff', 'patch notes'
        ]

        if any(keyword in text for keyword in patch_keywords):
            return 'patch'

        # "Update X.X" or "Version X.X" patterns (but not "update on" or "latest update")
        if feedlabel == 'product update':
            return 'patch'

        # PRIORITY 3: DLC/Expansions
        dlc_keywords = [
            'dlc', 'expansion', 'content pack', 'season pass',
            'new expansion', 'expansion pack'
        ]

        if any(keyword in text for keyword in dlc_keywords):
            return 'dlc'

        # PRIORITY 4: Events (sales, promotions)
        # Note: "event" for us means promotional, not in-game content events
        event_keywords = [
            'steam awards', 'vote for', 'nominate',
            'contest', 'giveaway', 'tournament',
            'free weekend', 'free to play weekend'
        ]

        if any(keyword in text for keyword in event_keywords):
            return 'event'

        # Sales and discounts
        if ('sale' in text or 'discount' in text or '% off' in text):
            if 'launch' not in text and 'release' not in text:
                return 'event'

        # PRIORITY 5: Default to announcement
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

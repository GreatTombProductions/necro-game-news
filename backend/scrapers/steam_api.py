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
    
    def parse_app_details(self, app_data: Dict) -> Dict:
        """
        Parse and extract relevant fields from app details response.
        
        Args:
            app_data: Raw app details from Steam API
            
        Returns:
            Dictionary with cleaned/parsed data
        """
        return {
            'steam_id': app_data.get('steam_appid'),
            'name': app_data.get('name'),
            'app_type': app_data.get('type'),  # 'game', 'dlc', etc.
            'short_description': app_data.get('short_description'),
            'header_image': app_data.get('header_image'),
            'developer': ', '.join(app_data.get('developers', [])),
            'publisher': ', '.join(app_data.get('publishers', [])),
            'release_date': app_data.get('release_date', {}).get('date'),
            'genres': [g.get('description') for g in app_data.get('genres', [])],
            'categories': [c.get('description') for c in app_data.get('categories', [])]
        }
    
    def classify_update_type(self, news_item: Dict) -> str:
        """
        Classify an update as patch/announcement/dlc/event based on content.
        
        This is a heuristic classification. Improve over time with better rules.
        
        Args:
            news_item: News item from Steam API
            
        Returns:
            Update type: 'patch', 'announcement', 'dlc', 'event', or 'unknown'
        """
        title = news_item.get('title', '').lower()
        contents = news_item.get('contents', '').lower()
        feedlabel = news_item.get('feedlabel', '').lower()
        
        # Combined text for analysis
        text = f"{title} {contents} {feedlabel}"
        
        # Patch/update indicators
        patch_keywords = [
            'patch', 'hotfix', 'update', 'bugfix', 'bug fix',
            'maintenance', 'version', 'changelog', 'fixed',
            'balance', 'nerf', 'buff'
        ]
        
        # DLC indicators
        dlc_keywords = [
            'dlc', 'expansion', 'new content', 'content pack',
            'season pass', 'now available'
        ]
        
        # Event indicators  
        event_keywords = [
            'event', 'sale', 'discount', 'weekend', 'promotion',
            'contest', 'giveaway', 'vote', 'awards', 'tournament'
        ]
        
        # Count keyword matches
        if any(keyword in text for keyword in patch_keywords):
            return 'patch'
        elif any(keyword in text for keyword in dlc_keywords):
            return 'dlc'
        elif any(keyword in text for keyword in event_keywords):
            return 'event'
        elif feedlabel == 'product update':
            return 'patch'
        else:
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

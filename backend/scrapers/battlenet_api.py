#!/usr/bin/env python3
"""
Battle.net news API client for game updates.

Uses the internal Blizzard news API at news.blizzard.com to fetch
game news and updates. This API is used by Blizzard's web components
and returns JSON data.

Supported games (relevant to necromancy):
- Diablo IV (product: diablo-4)
- Diablo III (product: diablo-3)

API endpoint: https://news.blizzard.com/en-us/api/news/{product}
"""

import os
import time
import logging
import requests
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BattlenetAPIError(Exception):
    """Base exception for Battle.net API errors"""
    pass


class BattlenetRateLimitError(BattlenetAPIError):
    """Raised when rate limited by Battle.net API"""
    pass


class BattlenetScraper:
    """
    Battle.net news client using Blizzard's internal news API.

    Fetches news from https://news.blizzard.com/en-us/api/news/{product}
    The product slug (e.g., "diablo-4", "diablo-3") is passed directly
    from the battlenet_id field in games_list.yaml.
    """

    BASE_API_URL = "https://news.blizzard.com/en-us/api/news"

    # User agent for API requests
    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.USER_AGENT,
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Be respectful: 1 request per second

    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def get_game_news(self, product: str, count: int = 10) -> List[Dict]:
        """
        Fetch news/updates for a Battle.net game using Blizzard's news API.

        Args:
            product: Battle.net API slug (e.g., 'diablo-4', 'diablo-3')
            count: Maximum number of news items to fetch

        Returns:
            List of news items with title, url, date, id, category
        """
        url = f"{self.BASE_API_URL}/{product}"
        logger.info(f"Fetching Blizzard news from {url}")

        self._rate_limit()
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code == 429:
                raise BattlenetRateLimitError(f"Rate limited fetching {url}")
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return []

        # Extract content items from the feed
        content_items = data.get('feed', {}).get('contentItems', [])
        if not content_items:
            logger.warning(f"No content items found in response for {product}")
            return []

        news_items = []
        for item in content_items[:count]:
            props = item.get('properties', {})

            # Skip items that aren't from this specific product
            item_product = props.get('cxpProduct', {}).get('segment', '')
            if item_product and item_product != product:
                continue

            # Extract image URL from staticAsset
            static_asset = props.get('staticAsset', {})
            image_url = static_asset.get('imageUrl', '')
            # Ensure URL has protocol (API returns protocol-relative URLs like //bnetcmsus-a.akamaihd.net/...)
            if image_url and image_url.startswith('//'):
                image_url = 'https:' + image_url

            news_item = {
                'id': props.get('newsId', ''),
                'title': props.get('title', ''),
                'summary': props.get('summary', ''),
                'url': props.get('newsUrl', ''),
                'date': props.get('lastUpdated', ''),
                'category': props.get('category', 'News'),
                'product': product,
                'image_url': image_url,
            }

            if news_item['id'] and news_item['title']:
                news_items.append(news_item)

        logger.info(f"Found {len(news_items)} news items for {product}")
        return news_items

    def parse_news_item(self, news_item: Dict, product: str) -> Dict:
        """
        Parse a Battle.net news item into standardized format for database.

        Returns:
            Dict with keys: gid, title, contents, url, date, update_type
        """
        # Generate unique ID
        gid = f"bnet_{product}_{news_item.get('id', '')}"

        # Parse date - API returns ISO format like "2025-12-03T17:55:00Z"
        date_str = news_item.get('date', '')
        if date_str:
            try:
                date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                date_str = date.isoformat()
            except (ValueError, AttributeError):
                date_str = datetime.now().isoformat()
        else:
            date_str = datetime.now().isoformat()

        return {
            'gid': gid,
            'title': news_item.get('title', ''),
            'contents': news_item.get('summary', ''),  # Use summary as content
            'url': news_item.get('url', ''),
            'date': date_str,
            'update_type': self.classify_update_type(news_item),
            'image_url': news_item.get('image_url', ''),
        }

    def classify_update_type(self, news_item: Dict) -> str:
        """
        Classify the type of update based on category and content.

        Returns:
            One of: 'patch', 'announcement', 'dlc', 'event', 'release'
        """
        # Use category from API if available
        category = news_item.get('category', '').lower()
        title = news_item.get('title', '').lower()

        # Map API categories to our types
        if 'patch' in category:
            return 'patch'
        if 'season' in category:
            return 'event'
        if 'developer' in category:
            return 'announcement'
        if 'event' in category or 'limited' in category:
            return 'event'

        # Fall back to title-based classification
        if any(word in title for word in ['patch', 'hotfix', 'update notes', 'patch notes']):
            return 'patch'
        if any(word in title for word in ['season', 'event', 'week', 'limited time']):
            return 'event'
        if any(word in title for word in ['expansion', 'dlc']):
            return 'dlc'
        if any(word in title for word in ['launch', 'release', 'available now']):
            return 'release'

        return 'announcement'


def test_scraper():
    """Test Battle.net news scraper"""
    logging.basicConfig(level=logging.DEBUG)

    scraper = BattlenetScraper()

    print("Testing Blizzard news scraper...")
    print("=" * 60)

    for product in ['diablo-4', 'diablo-3']:
        print(f"\nFetching news for: {product}")
        print("-" * 40)

        news_items = scraper.get_game_news(product, count=5)

        if not news_items:
            print(f"  No news found for {product}")
            continue

        for i, item in enumerate(news_items, 1):
            parsed = scraper.parse_news_item(item, product)
            print(f"\n  {i}. [{parsed['update_type']}] {parsed['title'][:60]}...")
            print(f"     URL: {parsed['url']}")
            print(f"     GID: {parsed['gid']}")

    print("\n" + "=" * 60)
    print("Scraper test complete!")
    return True


# Keep the old API class for OAuth if needed in the future
class BattlenetAPI:
    """Legacy OAuth client - kept for potential future API use."""
    OAUTH_URL = "https://oauth.battle.net/token"

    def __init__(self):
        self.client_id = os.getenv('BLIZZARD_CLIENT_ID') or os.getenv('BATTLENET_CLIENT_ID')
        self.client_secret = os.getenv('BLIZZARD_CLIENT_SECRET') or os.getenv('BATTLENET_CLIENT_SECRET')
        self.access_token = None
        self.token_expires_at = 0

    def get_access_token(self) -> str:
        """Get OAuth2 access token using client credentials flow."""
        if self.access_token and time.time() < self.token_expires_at - 60:
            return self.access_token

        if not self.client_id or not self.client_secret:
            raise BattlenetAPIError("Battle.net API credentials not configured")

        response = requests.post(
            self.OAUTH_URL,
            auth=(self.client_id, self.client_secret),
            data={'grant_type': 'client_credentials'},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        self.access_token = data['access_token']
        self.token_expires_at = time.time() + data.get('expires_in', 3600)
        return self.access_token


if __name__ == "__main__":
    test_scraper()

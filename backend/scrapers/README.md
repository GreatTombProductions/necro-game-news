# Steam Scrapers Module

This module handles all interactions with the Steam Web API for fetching game data and updates.

## Files

### steam_api.py
Core Steam API client with:
- Rate limiting (1.5 seconds between requests)
- Error handling and retries
- Game details fetching
- News/updates fetching
- Update type classification (patch/announcement/dlc/event)

**Usage:**
```python
from backend.scrapers.steam_api import SteamAPI

api = SteamAPI()

# Get game details
details = api.get_app_details(2344520)  # Diablo IV
parsed = api.parse_app_details(details)

# Get news/updates
news = api.get_app_news(2344520, count=10)
for item in news:
    parsed = api.parse_news_item(item, 2344520)
    print(f"[{parsed['update_type']}] {parsed['title']}")
```

## Update Classification

The system classifies updates into 4 types using keyword matching:

1. **patch** - Code changes, bug fixes, balance updates
   - Keywords: patch, hotfix, update, bugfix, fixed, balance, nerf, buff
   
2. **dlc** - New content releases
   - Keywords: dlc, expansion, new content, content pack, season pass
   
3. **event** - Temporary events, sales, promotions
   - Keywords: event, sale, discount, weekend, promotion, contest, giveaway
   
4. **announcement** - Everything else (default)

This classification is heuristic and will improve over time.

## Steam API Endpoints Used

### Store API (No auth required)
- `GET /api/appdetails?appids={id}` - Game details
  - Name, description, images, tags, genres, release date
  
### Steam Web API (API key required)
- `GET /ISteamNews/GetNewsForApp/v2/?appid={id}` - News/updates
  - Title, content, date, URL, unique ID (gid)

## Rate Limiting

Steam's API has rate limits:
- ~200 requests per 5 minutes for most endpoints
- Our default: 1.5 seconds between requests (40/minute)
- Configurable via `rate_limit_delay` parameter

## Error Handling

The module handles:
- Network timeouts
- API errors
- Invalid responses
- Rate limit violations (via delay)

All errors are logged and raised as `SteamAPIError` exceptions.

## Testing

Run the module directly to test:
```bash
python backend/scrapers/steam_api.py
```

Or use the comprehensive test:
```bash
python scripts/test_pipeline.py
```

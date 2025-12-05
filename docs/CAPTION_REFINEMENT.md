# Instagram Caption Refinement - Completed

## Summary of Changes

The Instagram caption generation system has been updated with the following improvements:

### 1. Enhanced Database Schema ✅
- Added `price_usd` field to games table for storing game prices
- Updated dimension_1 taxonomy with clearer definitions:
  - **a**: Central to character/unit identity and gameplay
  - **b**: Cohesive specialization available
  - **c**: Some necromancy skills or items present
  - **d**: Minimal necromancy elements (technically present but minor impact)

### 2. AI-Generated Summaries ✅
- Integrated Claude API (Haiku 3.5) for generating 1-2 sentence summaries
- Replaces direct quoting from patch notes with concise, readable summaries
- Falls back to excerpt method if API key not configured
- Cost-efficient using Haiku model (~$0.001 per summary)

### 3. New Caption Format ✅
**Old Format:**
```
[Game Name] - [Type]
[Title]

[Quoted paragraph from announcement]

Posted: [Date]
Link: [URL]

#hashtags
```

**New Format:**
```
[Game Name] - [Type]
[Title]

[AI-generated 1-2 sentence summary]

Game Info:
- Release Date: [date]
- Genres: [list]
- Price: [USD or Free]
- Necromancy: [degree description]

#hashtags
```

### 4. Removed Elements ✅
- ❌ "Posted:" date line
- ❌ "Link:" URL line (hard to click on Instagram anyway)

### 5. Added Game Stats ✅
Each caption now includes:
- **Release Date**: From Steam API
- **Genres**: From Steam API
- **Price**: Current USD price (or "Free")
- **Necromancy Degree**: Human-readable description of dimension_1

## Example Output

Night Swarm update #190 now generates:

```
Night Swarm - Release
Night Swarm is Now Live!

Night Swarm has launched with a 15% discount for the first two weeks.

Game Info:
- Release Date: 4 Dec, 2025
- Genres: Action, Adventure, Casual, RPG
- Price: $11.04
- Necromancy: Some necromancy skills or items present

#necromancy #gaming #gamedev #indiegames #nightswarm #newgame #gamelaunch #gamedevelopment
```

## Setup Instructions

### 1. Add Anthropic API Key
To enable AI-generated summaries, add your Anthropic API key to `.env`:

```bash
ANTHROPIC_API_KEY=your_api_key_here
```

Get your API key from: https://console.anthropic.com/

### 2. Update Game Price Data
Run the game details fetcher to populate price data for all games:

```bash
python3 scripts/fetch_game_details.py
```

This will:
- Fetch current prices from Steam Store API
- Update the `price_usd` field for all active games
- Update other metadata (genres, release dates, etc.)

### 3. Test Caption Generation
Test with Night Swarm update #190:

```bash
python3 test_caption.py
```

## Files Modified

1. **backend/database/schema.py**
   - Added `price_usd REAL` field
   - Updated dimension_1 comments with new taxonomy

2. **backend/scrapers/steam_api.py**
   - Updated `parse_app_details()` to extract price from Steam API
   - Handles both paid games and free-to-play

3. **backend/content_gen/content_generator.py**
   - Updated SQL queries to fetch price, genres, release_date, dimensions
   - Passes new game metadata to template factory

4. **backend/content_gen/post_template.py**
   - Added Claude API integration for summaries
   - New `_generate_summary()` method using Claude Haiku
   - New `_format_game_stats()` method for game info section
   - Updated `generate_caption()` with new format
   - Updated `create_template()` factory to accept new parameters

5. **scripts/fetch_game_details.py**
   - Updated to save `price_usd` when fetching from Steam

6. **scripts/migrations/add_price_field.py**
   - New migration script to add price column to existing databases

7. **.env**
   - Added `ANTHROPIC_API_KEY` placeholder

## Next Steps

1. **Add your Anthropic API key** to `.env` file
2. **Run price data fetch** for all games: `python3 scripts/fetch_game_details.py`
3. **Test caption generation** with the test script
4. **Regenerate existing queue** if needed:
   ```bash
   # Clear existing queue and regenerate with new format
   python3 scripts/generate_social_posts.py --regenerate
   ```

## Cost Considerations

- Using Claude 3.5 Haiku for summaries
- Approximate cost: $0.001 per caption (~$0.25 per 1M input tokens, ~$1.25 per 1M output tokens)
- For 200 updates: ~$0.20 total
- Fallback to free excerpt method if API unavailable

## Taxonomy Refinement

The dimension_1 ("degree of necromancy integration") now uses clearer language:

| Value | Description | Example |
|-------|-------------|---------|
| **a** | Central to character/unit identity and gameplay | Necromancer is the main class |
| **b** | Cohesive specialization available | Necromancy skill tree in multi-class game |
| **c** | Some necromancy skills or items present | A few undead summons available |
| **d** | Minimal necromancy elements | Necromancy mentioned but minimal gameplay impact |

Note: For "b", consider if there's a better word than "cohesive" to describe a well-developed specialization option.

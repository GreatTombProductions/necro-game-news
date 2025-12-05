# Game Discovery System - User Guide

## Overview

The automated game discovery system helps you find and evaluate necromancy-themed games across Steam's entire catalog (~200k apps). It uses keyword matching and scoring algorithms to identify candidates, then provides an interactive review workflow to quickly approve games for tracking.

## Quick Start

```bash
# 1. Download all Steam app IDs
python3 scripts/batch_discover.py --download

# 2. Run discovery (finds candidates)
python3 scripts/batch_discover.py --discover --limit 100  # Test with 100 apps first

# 3. Review candidates interactively
python3 scripts/review_candidates.py

# 4. Sync approved games to database
python3 scripts/load_games_from_yaml.py --update

# 5. Check for updates and deploy
./scripts/deploy.sh
```

## System Architecture

### 1. Batch Discovery (`scripts/batch_discover.py`)

Downloads and evaluates all Steam games for necromancy content.

**Features:**
- Downloads complete Steam app list (SteamSpy API)
- Filters out DLC, soundtracks, demos, etc.
- Scores each game using keyword matching algorithm
- Saves high-scoring candidates to database
- Tracks processed app IDs for incremental updates
- Resumable (can continue interrupted runs)

**Commands:**
```bash
# Download app list
python3 scripts/batch_discover.py --download

# Run discovery
python3 scripts/batch_discover.py --discover

# Continue interrupted run
python3 scripts/batch_discover.py --continue

# Show progress statistics
python3 scripts/batch_discover.py --stats

# Test with limited apps
python3 scripts/batch_discover.py --discover --limit 100

# Adjust score threshold
python3 scripts/batch_discover.py --discover --min-score 10
```

**Performance:**
- Rate limited: 2 seconds per app (~1,800 apps/hour)
- Resumable: Tracks processed IDs in `data/discovery_cache/processed_appids.txt`
- Full catalog: ~100-200 hours for complete Steam catalog
- Batch saving: Commits to database every 1,000 candidates

### 2. Interactive Review (`scripts/review_candidates.py`)

Fast, keyboard-driven interface to review discovered candidates.

**Features:**
- Color-coded display with game details
- Shows necromancy score and keyword matches
- Quick approve/reject/skip workflow
- Prompts for classification (dimensions 1-3)
- Auto-appends to `games_list.yaml`
- Opens Steam store page in browser

**Commands:**
```bash
# Review all pending candidates
python3 scripts/review_candidates.py

# Review all candidates (including rejected)
python3 scripts/review_candidates.py --all

# Review top 10 only
python3 scripts/review_candidates.py --top 10
```

**Keyboard Controls:**
- `y` - Approve and classify
- `n` - Reject with reason
- `s` - Skip for now
- `o` - Open in browser
- `q` - Quit

**Workflow:**
1. View game details and necromancy score
2. Press `y` to approve
3. Classify using 3-dimension system:
   - **Dimension 1** (Centrality): `a`, `b`, `c`, or `d`
   - **Dimension 2** (POV): `character` or `unit`
   - **Dimension 3** (Naming): `explicit` or `implied`
4. Add optional notes and priority
5. Game is automatically added to `games_list.yaml`

### 3. Scoring Algorithm

Games are scored based on keyword matching:

**Primary Keywords** (+10 in name, +5 in description):
- necromancer, necromancy, necromantic
- raise dead, summon undead, summon skeleton
- death magic, dark magic

**Secondary Keywords** (+3 in name, +2 in description):
- skeleton, undead, zombie, lich, bone
- corpse, graveyard, crypt, tomb
- minion, summoner, summoning
- reanimation, resurrection

**Genre Bonus** (+1 point):
- RPG, Action RPG, Strategy, Roguelike, etc.

**Score Interpretation:**
- **10+** = Excellent candidate (strong necromancy focus)
- **5-9** = Good candidate (moderate necromancy presence)
- **3-4** = Weak candidate (minimal necromancy)
- **< 3** = Not a candidate (no meaningful necromancy)

**Default threshold:** 5 points (adjustable with `--min-score`)

## File Structure

```
data/
├── discovery_cache/
│   ├── steam_applist.json           # All Steam app IDs & names
│   ├── processed_appids.txt         # Tracking file for processed apps
│   └── batch_discovery.log          # Discovery run logs
├── games_list.yaml                  # Master list of approved games
└── necro_games.db                   # SQLite database
    ├── games                        # Tracked games
    ├── updates                      # Game updates
    └── candidates                   # Pending review
```

## Database Schema

### Candidates Table
```sql
- id: Unique identifier
- steam_id: Steam App ID
- game_name: Game title
- source: 'auto_discovery' | 'manual' | 'user_submission'
- justification: Score, matches, description
- status: 'pending' | 'approved' | 'rejected'
- review_notes: Manual review notes
- date_submitted: When discovered
```

## Incremental Discovery

The system tracks processed app IDs, so future runs only evaluate **new games**:

1. Initial run: Process all ~200k Steam apps
2. Later runs: Only process new apps not in `processed_appids.txt`
3. Excluded from processing:
   - Already tracked games (in `games` table)
   - Existing candidates (in `candidates` table)
   - Previously processed apps (in `processed_appids.txt`)

**To reset and reprocess everything:**
```bash
rm data/discovery_cache/processed_appids.txt
```

## Advanced Usage

### Custom Keyword Search

Edit `scripts/discover_games.py` to modify keywords:

```python
NECROMANCY_KEYWORDS = {
    'primary': ['necromancer', 'necromancy', ...],
    'secondary': ['skeleton', 'undead', ...],
    'required_genres': ['RPG', 'Strategy', ...]
}
```

### Adjusting Score Weights

In `calculate_necromancy_score()` function:
```python
# Current weights:
# Primary in name: +10
# Primary in description: +5
# Secondary in name: +3
# Secondary in description: +2
# Genre match: +1
```

### Batch Size Tuning

For faster database commits, reduce batch size:
```python
# In batch_discover.py
evaluate_and_save(apps, batch_size=100)  # Default: 1000
```

### Rate Limiting

Adjust request delay to stay within Steam's limits:
```python
# In batch_discover.py
steam_api = SteamAPI(rate_limit_delay=1.0)  # Default: 2.0 seconds
```

## Workflow Examples

### Example 1: Initial Discovery (Test Run)
```bash
# Download app list
python3 scripts/batch_discover.py --download

# Test with 100 games
python3 scripts/batch_discover.py --discover --limit 100 --min-score 5

# Review results
python3 scripts/review_candidates.py

# If satisfied, run full discovery
python3 scripts/batch_discover.py --discover
```

### Example 2: Weekly Update Check
```bash
# Check for new games only (incremental)
python3 scripts/batch_discover.py --download  # Get latest app list
python3 scripts/batch_discover.py --discover  # Only processes new apps

# Review new candidates
python3 scripts/review_candidates.py --top 20

# Sync to database
python3 scripts/load_games_from_yaml.py --update
```

### Example 3: Emergency Stop & Resume
```bash
# Start discovery
python3 scripts/batch_discover.py --discover

# [CTRL+C to interrupt]

# Later, resume from where it stopped
python3 scripts/batch_discover.py --continue
```

## Monitoring Progress

### Check Discovery Status
```bash
python3 scripts/batch_discover.py --stats
```

Output:
```
================================================================================
BATCH DISCOVERY STATISTICS
================================================================================

Processed app IDs: 45,230
Total Steam apps: 200,000
Remaining: 154,770
Progress: 22.6%

Candidates from auto-discovery: 127
Pending review: 89
Games tracked: 38

================================================================================
```

### View Discovery Logs
```bash
tail -f data/batch_discovery.log
```

### Database Queries
```bash
# Check candidates by score
python3 scripts/view_database.py --candidates

# See all pending reviews
sqlite3 data/necro_games.db \
  "SELECT game_name, justification FROM candidates WHERE status='pending' LIMIT 10"
```

## Troubleshooting

### Problem: App list download fails
**Solution:** SteamSpy API might be down. Try again later or check alternative sources.

### Problem: Too many false positives
**Solution:** Increase minimum score threshold:
```bash
python3 scripts/batch_discover.py --discover --min-score 10
```

### Problem: Missing good games
**Solution:** Lower threshold or add more secondary keywords in `discover_games.py`.

### Problem: Discovery is too slow
**Solution:**
1. Reduce rate limit delay (risky - may get blocked)
2. Run on a server/cloud instance with better connection
3. Use `--limit` for smaller batches

### Problem: Want to reprocess specific games
**Solution:** Remove their app IDs from `processed_appids.txt`:
```bash
# Remove specific app ID
sed -i '' '/219990/d' data/discovery_cache/processed_appids.txt

# Or delete entire file to reprocess everything
rm data/discovery_cache/processed_appids.txt
```

## Tips & Best Practices

1. **Start Small:** Test with `--limit 100` before running full discovery
2. **Adjust Threshold:** Use `--min-score` to balance quantity vs quality
3. **Review Regularly:** Don't let candidates pile up - review weekly
4. **Track Progress:** Use `--stats` to monitor long-running discoveries
5. **Backup Database:** Before major operations, backup `necro_games.db`
6. **Git Commit:** After approving games, commit `games_list.yaml` changes

## Integration with Existing Workflow

After approving games via review tool:

```bash
# 1. Review completed - games added to games_list.yaml
python3 scripts/review_candidates.py

# 2. Sync YAML changes to database
python3 scripts/load_games_from_yaml.py --update

# 3. Check for game updates
python3 scripts/check_updates.py

# 4. Full deployment
./scripts/deploy.sh
```

## Future Enhancements

- [ ] Web-based review interface
- [ ] Machine learning scoring model
- [ ] Multi-platform support (Epic, GOG, itch.io)
- [ ] Automated user submissions
- [ ] Similarity-based recommendations
- [ ] Community voting on candidates

---

**Need help?** Check the logs in `data/batch_discovery.log` or review the source code in `scripts/batch_discover.py` and `scripts/review_candidates.py`.
# Necro Game News

Automated tracking and content platform for games featuring necromancy.

**Live Site:** https://necrotic-realms.vercel.app/

## Features

- Multi-platform update tracking (Steam, Battle.net)
- Searchable, filterable web interface with platform indicators
- Instagram content generation
- Game discovery across Steam's catalog

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+ (for frontend)
- Steam API Key (from https://steamcommunity.com/dev/apikey)

### Setup

```bash
# Clone and enter the repository
git clone <repository-url>
cd necro-game-news

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your Steam API key

# Initialize database
python scripts/init_database.py

# Set up frontend
cd frontend
npm install
```

## Daily Workflow

The main deploy script handles everything:

```bash
./scripts/deploy.sh
```

This runs interactively, offering options for:
1. **Full Deploy** - Updates, content generation, and deploy
2. **Updates + Deploy** - Skip social content
3. **Social Content Only** - Just generate Instagram posts

Or use flags to skip the menu:
```bash
./scripts/deploy.sh --full           # Everything
./scripts/deploy.sh --updates-only   # Skip content generation
./scripts/deploy.sh --content-only   # Only social content
```

## Game Discovery

Find new necromancy games across Steam's catalog:

```bash
# Download Steam app list
python scripts/batch_discover.py --download

# Run discovery (can take many hours for full catalog)
python scripts/batch_discover.py --discover --yes

# Check progress
python scripts/batch_discover.py --stats

# Review discovered candidates interactively
python scripts/review_candidates.py
```

Review controls: `y` approve, `n` reject, `s` skip, `o` open in browser, `q` quit

## Necromancy Classification

Games are classified across three dimensions:

**Dimension 1: Centrality**
- a) Core Identity - Necromancer class/protagonist
- b) Specialization - Necromantic skill tree available
- c) Isolated Features - Necromantic items/skills exist
- d) Flavor Only - Necromancy in lore, minimal gameplay

**Dimension 2: Point of View**
- a) Play AS the necromancer
- b) Control necromancer units

**Dimension 3: Naming**
- a) Explicitly called "necromancer/necromancy"
- b) Implied/thematic death magic

Example: Diablo IV = 1a, 2a, 3a (core necromancer class, you play as them, explicitly named)

## Project Structure

```
necro-game-news/
├── backend/
│   ├── scrapers/          # Platform APIs (Steam, Battle.net)
│   ├── database/          # Database models
│   └── content_gen/       # Social media generation
├── frontend/              # React + Vite web app
├── data/
│   ├── games_list.yaml    # Tracked games (multi-platform)
│   └── necro_games.db     # SQLite database
├── scripts/               # Automation scripts
└── content/               # Generated social posts
```

## Other Useful Scripts

```bash
# Database
python scripts/view_database.py --stats
python scripts/load_games_from_yaml.py --update

# Data collection
python scripts/check_updates.py
python scripts/fetch_game_details.py

# Social media
python scripts/generate_social_content.py
python scripts/generate_social_content.py --reprocess

# Backfill Steam tags for existing games
python scripts/migrations/backfill_tags.py
```

## Development

Always use the virtual environment:

```bash
source venv/bin/activate
python scripts/whatever.py

# Or use venv Python directly
./venv/bin/python scripts/whatever.py
```

Frontend development:
```bash
cd frontend
npm run dev      # Dev server
npm run build    # Production build
```

## Tech Stack

- **Backend:** Python 3.9+, SQLite
- **Data Sources:** Steam Web API, Steamspy API, Blizzard News API
- **Frontend:** React + Vite, TanStack Table, Tailwind CSS
- **Hosting:** Vercel (auto-deploy on push)
- **Social:** Instagram (manual posting)

## Generated Content

After running content generation:

```
content/
├── posts/           # Images (YYYYMMDD_GameName_image_N.jpg)
└── captions/        # Captions (YYYYMMDD_GameName_caption_N.txt)
```

Pick your favorite caption/image combo and post manually to Instagram.

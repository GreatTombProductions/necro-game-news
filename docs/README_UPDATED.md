# Necro Game News

Automated tracking and content platform for games featuring necromancy.

**🌐 Live Site:** https://necrotic-realms.vercel.app/

[![Phase 1 Complete](https://img.shields.io/badge/Phase%201-Complete-success)]()
[![Vercel Deployment](https://img.shields.io/badge/Vercel-Deployed-black)]()
[![Games Tracked](https://img.shields.io/badge/Games-10-purple)]()

## Features

- 🎮 **Automated Game Tracking**: Daily Steam update monitoring
- 🔍 **Searchable Database**: Filterable, sortable web interface
- 📱 **Social Media Pipeline**: Instagram content generation (Phase 2)
- 🏷️ **Necromancy Classification**: Multi-dimensional game taxonomy

## Live Demo

Visit **https://necrotic-realms.vercel.app/** to see the platform in action!

Features:
- Search across games, developers, and genres
- Sort by any column (click headers)
- Color-coded necromancy classifications
- Click any game to open its Steam page
- Dark "necromancer's lair" aesthetic

## Quick Start

### Prerequisites

- Python 3.11+ (3.9+ will work)
- Node.js 18+ (for frontend)
- Steam API Key (get from https://steamcommunity.com/dev/apikey)

### Setup

1. **Clone and enter the repository**
   ```bash
   git clone <repository-url>
   cd necro-game-news
   ```

2. **Set up Python environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your Steam API key
   ```

4. **Initialize database**
   ```bash
   python scripts/init_database.py
   python scripts/load_games_from_yaml.py  # Load starter games
   ```

5. **Fetch initial data**
   ```bash
   python scripts/fetch_game_details.py  # Get game metadata
   python scripts/check_updates.py       # Get latest updates
   ```

6. **Run frontend locally**
   ```bash
   python scripts/export_for_web.py      # Export to JSON
   cd frontend
   npm install
   npm run dev
   ```

Visit http://localhost:5173 to see it running locally!

## Project Structure

```
necro-game-news/
├── backend/
│   ├── scrapers/          # Steam API interactions
│   ├── database/          # Database models and operations
│   ├── content_gen/       # Social media content generation
│   └── config/            # Configuration files
├── frontend/              # React + Vite web application
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── types.ts       # TypeScript definitions
│   │   └── App.tsx        # Main application
│   └── public/data/       # Exported JSON data
├── data/
│   ├── games_list.yaml    # Curated games to track
│   └── necro_games.db     # SQLite database
├── scripts/               # Automation and utility scripts
├── logs/                  # Application logs
└── content/               # Generated social media content
```

## Necromancy Classification System

Games are evaluated across three dimensions:

### Dimension 1: Centrality (a > b > c > d)
- **a)** Core Identity - Necromancer class/protagonist
- **b)** Specialization - Necromantic skill tree available
- **c)** Isolated Features - Necromantic items/skills exist
- **d)** Flavor Only - Necromancy in lore, minimal gameplay

### Dimension 2: Point of View
- **a)** Character Control - Play AS necromancer
- **b)** Unit Control - Control necromancer units

### Dimension 3: Naming
- **a)** Explicit - Called "necromancer/necromancy"
- **b)** Implied - Death magic without explicit terminology

**Example:** V Rising = 1b, 2a, 3b

## Common Commands

### Database Management

```bash
# View all games and stats
python scripts/view_database.py --stats

# Add a new game
python scripts/add_game.py --steam-id 2344520 --name "Diablo IV" \
  --dim1 a --dim2 character --dim3 explicit --notes "Necromancer class"

# Load/sync from YAML
python scripts/load_games_from_yaml.py         # Load new games only
python scripts/load_games_from_yaml.py --update  # Update existing too
```

### Data Collection

```bash
# Fetch game metadata from Steam
python scripts/fetch_game_details.py

# Check for new updates
python scripts/check_updates.py

# Generate human-readable report
python scripts/generate_report.py --days 7

# Test the entire pipeline
python scripts/test_pipeline.py
```

### Frontend & Deployment

```bash
# Export database to JSON for frontend
python scripts/export_for_web.py

# Run frontend dev server
cd frontend
npm run dev

# Build for production
cd frontend
npm run build

# Deploy to Vercel (automatic on push to main)
git add .
git commit -m "Update game data"
git push origin main
```

### Daily Workflow

```bash
# Check for updates and deploy
python scripts/check_updates.py
python scripts/export_for_web.py
git add frontend/public/data/*.json
git commit -m "Update game data: $(date +%Y-%m-%d)"
git push origin main  # Auto-deploys to Vercel
```

## Tech Stack

- **Backend**: Python 3.11+, SQLite, Steam Web API
- **Frontend**: React 18, Vite, TanStack Table, Tailwind CSS
- **Hosting**: Vercel (frontend), Local (automation)
- **Social Media**: Meta Graph API (Instagram) - Phase 2

## Development

### Branch Strategy

- `main` - Production-ready code (auto-deploys to Vercel)
- `develop` - Integration branch
- `feature/*` - Individual features

### Testing

```bash
# Backend tests
pytest

# Test entire pipeline
python scripts/test_pipeline.py

# Frontend tests
cd frontend
npm test
```

## Documentation

- [Project Vision](PROJECT_VISION.md) - Detailed goals and taxonomy
- [Technical Roadmap](TECHNICAL_ROADMAP.md) - Phased implementation plan
- [Progress Tracker](PROGRESS.md) - What's completed, what's next
- [Tech Stack & Deployment](TECH_STACK_DEPLOYMENT.md) - Implementation details

## Current Status

**Phase**: Phase 1 (MVP) Complete ✅
**Live Site**: https://necrotic-realms.vercel.app/
**Games Tracked**: 10+
**Updates Tracked**: 200+
**Next Phase**: Automation & Enhancement

### What's Working
- ✅ Steam API integration with rate limiting
- ✅ Automated update checking
- ✅ Searchable, sortable web interface
- ✅ Necromancy classification system
- ✅ Dark aesthetic design
- ✅ Auto-deployment to Vercel

### Coming Soon (Phase 2)
- [ ] Automated daily cron jobs
- [ ] Instagram content generation
- [ ] User game submissions
- [ ] Expand to 50+ games

## Contributing

Contributions welcome! To suggest a game:
1. Check if it meets the necromancy criteria (see classification system)
2. Open an issue with game details and justification
3. Or submit a PR adding it to `data/games_list.yaml`

## License

TBD

## Acknowledgments

Built with Claude (Anthropic) as implementation partner.
- Phase 1 completion time: 70 minutes
- Traditional estimate: 1-3 weeks

---

**Live Site:** https://necrotic-realms.vercel.app/  
**Status:** Phase 1 Complete, Phase 2 Ready  
**Last Updated:** December 2, 2024

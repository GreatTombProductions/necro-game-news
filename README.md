# Necro Game News

Automated tracking and content platform for games featuring necromancy.

## Features

- 🎮 **Automated Game Tracking**: Daily Steam update monitoring
- 🔍 **Searchable Database**: Filterable, sortable web interface
- 📱 **Social Media Pipeline**: Instagram content generation and posting
- 🏷️ **Necromancy Classification**: Multi-dimensional game taxonomy

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
   ```

5. **Set up frontend** (after Phase 1.2)
   ```bash
   cd frontend
   npm install
   ```

## Project Structure

```
necro-game-news/
├── backend/
│   ├── scrapers/          # Steam API interactions
│   ├── database/          # Database models and operations
│   ├── content_gen/       # Social media content generation
│   └── config/            # Configuration files
├── frontend/              # React + Vite web application
├── data/
│   ├── games_list.yaml    # Curated games to track
│   ├── candidates.yaml    # Games under review
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

### Backend

```bash
# Check for game updates
python scrapers/check_updates.py

# Add a new game
python scripts/add_game.py --steam-id 2344520 --dim1 a --dim2 character --dim3 explicit

# Export data for website
python scripts/export_for_web.py

# Review candidate games
python scripts/review_candidates.py
```

### Frontend

```bash
cd frontend

# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Daily Workflow

```bash
# Automated daily update and deploy
./scripts/update_and_deploy.sh
```

## Development

### Branch Strategy

- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - Individual features

### Testing

```bash
# Backend tests
pytest

# Frontend tests
cd frontend
npm test
```

## Tech Stack

- **Backend**: Python 3.11+, SQLite, Steam Web API
- **Frontend**: React 18, Vite, TanStack Table, Tailwind CSS
- **Hosting**: Vercel (frontend), Local (automation)
- **Social Media**: Meta Graph API (Instagram)

## Documentation

- [Project Vision](PROJECT_VISION.md) - Detailed goals and taxonomy
- [Technical Roadmap](TECHNICAL_ROADMAP.md) - Phased implementation plan
- [Tech Stack & Deployment](TECH_STACK_DEPLOYMENT.md) - Implementation details
- [Quick Start Guide](QUICK_START_GUIDE.md) - Week 1 action plan

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

TBD

## Current Status

**Phase**: Foundation (MVP)
**Progress**: Setting up infrastructure
**Next**: Database schema and Steam scraper implementation

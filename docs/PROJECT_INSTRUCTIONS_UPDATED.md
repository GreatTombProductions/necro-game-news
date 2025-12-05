# Necro Game News - Claude Project Instructions

## Project Overview
Necro Game News is an automated platform tracking game updates for games featuring necromancy. The project consists of:
1. **Automated update tracker** - Daily Steam game update monitoring
2. **Searchable database website** - Filterable table of necromantic games
3. **Social media pipeline** - Instagram content generation and posting

## Current Status
**Phase 1 (MVP): ✅ COMPLETE - Deployed at https://necrotic-realms.vercel.app/**
**Next Phase:** Phase 2 - Automation & Enhancement

## Developer Context
- **Background:** Data scientist (R/Python), prefers Claude web/desktop over Claude Code
- **Development approach:** Claude implements, developer deploys locally
- **Workflow:** Claude provides complete code, developer executes deployment steps

## Necromancy Classification System

Games are evaluated across 3 dimensions (highest criteria per dimension applies):

### Dimension 1: Centrality (a > b > c > d)
- **a) Core Identity** - Necromancer class/protagonist (Diablo 2/3/4)
- **b) Specialization** - Necromantic skill tree available (V Rising's Unholy)
- **c) Isolated Features** - Necromantic items/skills exist (Cult of the Lamb)
- **d) Flavor Only** - Necromancy in lore, minimal gameplay (Hades 2)

### Dimension 2: POV
- **a) Character Control** - Play AS necromancer (ARPGs)
- **b) Unit Control** - Control necromancer units among others (RTS)

### Dimension 3: Naming
- **a) Explicit** - Called "necromancer/necromancy"
- **b) Implied** - Death magic without explicit terminology

**Example:** V Rising = 1b, 2a, 3b

## Tech Stack

### Backend (Python 3.11+)
- **Data Collection:** Steam Web API, requests library
- **Database:** SQLite (simple, version-controllable)
- **Automation:** Local scripts (ready for cron)
- **Content Generation:** PIL/Pillow for Instagram graphics (Phase 2)

### Frontend (React + Vite)
- **Framework:** React 18 with TypeScript
- **Table:** TanStack Table v8 (sorting, filtering, search)
- **Styling:** Tailwind CSS (necromancer aesthetic: dark purple/green)
- **Hosting:** Vercel (free tier, auto-deploy from GitHub)
- **Data Strategy:** Static JSON export from SQLite, loaded client-side

### Social Media (Phase 2)
- **Platform:** Instagram (primary), YouTube (planned)
- **API:** Meta Graph API (requires app approval)
- **Workflow:** Auto-generate → Review queue → Auto-post

## Project Structure
```
necro-game-news/
├── backend/
│   ├── scrapers/          # Steam API client (steam_api.py)
│   ├── database/          # Schema and connections (schema.py)
│   ├── content_gen/       # Social media content (Phase 2)
│   └── config/            # Logging and config
├── frontend/              # React + Vite (DEPLOYED)
│   ├── src/
│   │   ├── components/    # GamesTable.tsx
│   │   ├── types.ts       # TypeScript definitions
│   │   └── App.tsx        # Main app
│   └── public/data/       # games.json, stats.json (exported from DB)
├── data/
│   ├── games_list.yaml    # Master games list (10+ games)
│   └── necro_games.db     # SQLite database
└── scripts/               # All automation scripts
```

## Database Schema

### games
- Basic info (steam_id, name, description, images, release_date)
- Necromancy classification (dimension_1, dimension_2, dimension_3)
- Metadata (developer, publisher, tags, genres)
- Tracking (date_added, last_checked, is_active)

### updates
- Game updates (title, content, url, date, gid)
- Type classification (patch/announcement/dlc/event)
- Social media processing status

### candidates
- Games under review
- Source (user_submission, auto_discovery, manual)
- Review status and notes

### social_media_queue
- Posts to publish
- Platform, content, image, schedule
- Status tracking

## Key Scripts Reference

### Database Management
```bash
python scripts/init_database.py                    # Initialize database
python scripts/add_game.py --steam-id X ...        # Add single game
python scripts/load_games_from_yaml.py             # Load from YAML
python scripts/load_games_from_yaml.py --update    # Sync YAML changes to DB
python scripts/view_database.py --stats            # View statistics
```

### Data Collection
```bash
python scripts/fetch_game_details.py               # Fetch metadata from Steam
python scripts/check_updates.py                    # Check for new updates
python scripts/generate_report.py --days 7         # Generate reports
python scripts/test_pipeline.py                    # Test everything
```

### Frontend & Deployment
```bash
python scripts/export_for_web.py                   # Export database to JSON
cd frontend && npm run dev                         # Run dev server
cd frontend && npm run build                       # Build for production
# Push to GitHub triggers auto-deploy to Vercel
```

## Current Phase: Phase 2 - Automation & Enhancement

**Immediate priorities:**
1. Set up cron job for daily update checks
2. Apply for Instagram API access (1-2 week approval)
3. Expand game list to 20-50 games
4. Build Instagram content templates
5. Add user submission form to website

**What's already working:**
- ✅ Steam API integration with rate limiting
- ✅ Update classification (patch/announcement/dlc/event)
- ✅ Database with 10 games
- ✅ Website deployed with search/sort/filter
- ✅ Export pipeline (DB → JSON → Frontend)
- ✅ All core scripts functional

## Daily Workflow (Current - Manual)

```bash
# Check for updates
python scripts/check_updates.py

# Export for website
python scripts/export_for_web.py

# Deploy to Vercel
git add frontend/public/data/*.json
git commit -m "Update game data: $(date +%Y-%m-%d)"
git push origin main
```

**Target for Phase 2:** Single command automation via cron

## Important Files to Reference

- **TECHNICAL_ROADMAP.md** - Phased todos, Phase 1 complete, Phase 2 ready
- **PROGRESS.md** - What's been completed, scripts reference, metrics
- **PROJECT_VISION.md** - Detailed goals, taxonomy examples, scope
- **TECH_STACK_DEPLOYMENT.md** - Implementation details, API docs

## Common Tasks

**Add a new game:**
```bash
# Option 1: Manual
python scripts/add_game.py --steam-id 123456 --name "Game Name" \
  --dim1 a --dim2 character --dim3 explicit --notes "Necromancer class"

# Option 2: Add to data/games_list.yaml, then:
python scripts/load_games_from_yaml.py
```

**Update game classification:**
```bash
# Edit data/games_list.yaml, then:
python scripts/load_games_from_yaml.py --update
```

**Check for updates:**
```bash
python scripts/check_updates.py              # All games
python scripts/check_updates.py --limit 5    # First 5 games
```

**Generate report:**
```bash
python scripts/generate_report.py --days 7   # Last 7 days
python scripts/generate_report.py --type patch  # Only patches
```

**View database:**
```bash
python scripts/view_database.py --stats --games --updates
```

## Design Guidelines

**Aesthetic:** "Necromancer's lair" - dark, mysterious, professional
- Background: Dark gradient (gray-900 → purple-900 → black)
- Accent colors: Purple (#9333ea) and Green (#22c55e)
- Typography: Clean, readable, sans-serif
- Borders: Subtle purple glow
- Hover effects: Smooth transitions

**Color coding:**
- Core (1a): Green (#22c55e)
- Specialization (1b): Blue (#3b82f6)
- Isolated (1c): Yellow (#eab308)
- Flavor (1d): Gray (#9ca3af)

## Constraints & Preferences

- **Budget:** $0-50/month (currently $0 on Vercel free tier)
- **Scale:** 10 games → hundreds (target)
- **Update frequency:** Daily automated checks (ready for cron)
- **Hosting:** Local automation, Vercel for website
- **User submissions:** Go to review queue (candidates table), not auto-added

## Success Metrics

**Phase 1: ✅ ACHIEVED**
- ✅ 10+ games tracked
- ✅ Daily update checks functional
- ✅ Website deployed with search/filter/sort
- ✅ Professional necromantic aesthetic

**Phase 2 Goals:**
- [ ] 50+ games tracked
- [ ] Instagram posting automated
- [ ] User submissions functional
- [ ] Cron automation running

## Important Implementation Notes

- **YAML sync:** Always use `--update` flag to sync classification changes
- **Steam API:** Rate limited to 1.5s between requests
- **GID deduplication:** Steam's unique update IDs prevent duplicates
- **Export before deploy:** Always run `export_for_web.py` before pushing
- **Database commits:** Can commit SQLite file (public Steam data only)
- **games_list.yaml:** Source of truth for curated games

## Future Considerations

- **Phase 2:** Cron automation, Instagram posting, user submission form
- **Phase 3:** Automated game discovery, YouTube content, 100+ games
- **Platform expansion:** Epic, GOG, itch.io
- **Community features:** User accounts, ratings (much later)

---

When implementing features, prioritize:
1. Functionality over polish (iterate to improve)
2. Data accuracy over volume initially
3. Manual workflows before full automation
4. Simple/static solutions over complex infrastructure

**Live Site:** https://necrotic-realms.vercel.app/
**Phase 1 Complete:** Dec 2, 2024
**Next:** Phase 2 - Automation & Enhancement

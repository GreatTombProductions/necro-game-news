# Necro Game News - Technical Roadmap & Todo List

## Tech Stack Overview

### Data Collection & Automation
- **Language:** Python 3.11+
- **Steam API:** steamwebapi / requests
- **Scheduling:** cron (local) or GitHub Actions (optional)
- **Data Storage:** SQLite
- **Configuration:** YAML/JSON for game lists

### Website/Frontend
- **Framework:** React + Vite
- **Table Library:** TanStack Table (formerly React Table)
- **Styling:** Tailwind CSS
- **Hosting:** Vercel (free tier) or GitHub Pages
- **Build:** Static site generation

### Social Media
- **Instagram:** Meta Graph API (requires app approval)
- **Content Generation:** Python templates
- **Image Generation:** PIL/Pillow for graphics
- **Scheduling:** Local queue system initially

### Development & Deployment
- **Version Control:** Git/GitHub
- **Database Management:** SQLite browser / DB tool
- **Testing:** pytest (Python), Vitest (frontend)
- **CI/CD:** GitHub Actions (optional)

---

## ✅ Phase 1: Foundation & MVP (COMPLETED - Dec 2, 2024)

### 1.1 Project Setup & Infrastructure ✅
**Status: COMPLETE**

- ✅ Initialize Git repository
- ✅ Create .gitignore (Python, Node, SQLite temp files)
- ✅ Set up branch strategy (main + develop)
- ✅ Create README with setup instructions
- ✅ Set up Python environment
- ✅ Create requirements.txt
- ✅ Set up virtual environment
- ✅ Install core dependencies (requests, sqlite3, pyyaml)
- ✅ Design database schema
- ✅ Create project structure
- ✅ Push to GitHub

**Deliverables:**
- Complete project structure
- Version control configured
- Python environment ready
- All configuration files

---

### 1.2 Database Schema & Management ✅
**Status: COMPLETE**

- ✅ Create SQLite schema (4 tables: games, updates, candidates, social_media_queue)
- ✅ Create schema migration script (backend/database/schema.py)
- ✅ Implement database initialization script (scripts/init_database.py)
- ✅ Implement CRUD operations for all tables
- ✅ Create manual game entry tools (scripts/add_game.py)
- ✅ Batch import from YAML (scripts/load_games_from_yaml.py)
- ✅ Add --update flag for syncing YAML changes to database
- ✅ Create database viewing utility (scripts/view_database.py)
- ✅ Seed initial database (10 games in games_list.yaml)
- ✅ Add validation for dimension values
- ✅ Create indexes for performance

**Deliverables:**
- SQLite database with 4 tables
- 10 games initially loaded
- Necromancy classification system implemented
- Full CRUD functionality via CLI tools

---

### 1.3 Steam Data Collection ✅
**Status: COMPLETE**

- ✅ Research Steam Web API
- ✅ Document endpoints (app details, news)
- ✅ Determine rate limits (200 requests/5 min)
- ✅ Get Steam API key
- ✅ Build Steam API client module (backend/scrapers/steam_api.py)
  - ✅ Game details fetcher
  - ✅ News/updates fetcher
  - ✅ Update type classification (patch/announcement/dlc/event)
  - ✅ Error handling and retries
  - ✅ Rate limiting (1.5s between requests)
  - ✅ Logging
- ✅ Create game list management (YAML schema with classification)
- ✅ Add validation for game entries
- ✅ Create helper script to add new games
- ✅ Build data pipeline scripts:
  - ✅ scripts/fetch_game_details.py - Fetch metadata from Steam
  - ✅ scripts/check_updates.py - Main update checker
  - ✅ scripts/generate_report.py - Human-readable reports
  - ✅ scripts/test_pipeline.py - End-to-end testing
- ✅ Implement deduplication logic (using Steam's gid)
- ✅ Create logging configuration (backend/config/logging_config.py)
- ✅ Document Steam API module (backend/scrapers/README.md)

**Deliverables:**
- Complete Steam API integration
- Rate-limited, error-handled scraper
- Update type classification working
- All automation scripts functional
- ~200 updates collected for 10 games

---

### 1.4 Website Foundation ✅
**Status: COMPLETE - LIVE at https://necrotic-realms.vercel.app/**

- ✅ Initialize React project (Vite + React + TypeScript)
- ✅ Configure Tailwind CSS
- ✅ Set up routing (single page for MVP)
- ✅ Implement TanStack Table v8
  - ✅ Install @tanstack/react-table
  - ✅ Create reusable table component (GamesTable.tsx)
  - ✅ Implement column definitions with custom cells
  - ✅ Add global search across all fields
  - ✅ Add column sorting (click headers)
  - ✅ Add pagination (20 per page with First/Previous/Next/Last)
  - ✅ Color-code classifications
- ✅ Design data loading strategy
  - ✅ Create export script (scripts/export_for_web.py)
  - ✅ Export games.json with full metadata
  - ✅ Export stats.json with aggregate statistics
  - ✅ Client-side data loading via fetch
- ✅ Build UI with necromancer aesthetic
  - ✅ Header with gradient text and skull emoji
  - ✅ Main table view with hover effects
  - ✅ Stats dashboard (3 cards at bottom)
  - ✅ Responsive design for mobile
  - ✅ Dark gradient background (gray-900 → purple-900 → black)
  - ✅ Purple/green accent colors
  - ✅ Subtle borders with purple glow
- ✅ Add TypeScript types (types.ts)
- ✅ Add click-to-open Steam page functionality
- ✅ Add last updated timestamp

**Deliverables:**
- React app with TanStack Table
- Dark necromantic aesthetic
- Fully functional search/sort/filter
- Stats dashboard
- Mobile responsive

---

### 1.5 Deployment ✅
**Status: COMPLETE - LIVE at https://necrotic-realms.vercel.app/**

- ✅ Set up Vercel project
- ✅ Configure build settings:
  - ✅ Framework: Vite
  - ✅ Root Directory: frontend
  - ✅ Build Command: npm run build
  - ✅ Output Directory: dist
- ✅ Deploy initial version
- ✅ Configure auto-deploy on push to main
- ✅ Test deployment
- ✅ Verify data loading
- ✅ Test all features in production

**Deliverables:**
- Live site at https://necrotic-realms.vercel.app/
- Auto-deploy configured
- Production tested and verified

---

## 📊 Phase 1 Summary

**Status:** COMPLETE ✅  
**Time:** 70 minutes  
**Live Site:** https://necrotic-realms.vercel.app/

**What We Built:**
- Complete backend infrastructure (Python, SQLite, Steam API)
- Automated update tracking system
- React frontend with professional UI
- Vercel deployment with auto-deploy
- 10 games tracked, ~200 updates collected

**Key Files Created:**
- 5 core backend modules
- 7 automation scripts
- Complete React frontend
- 4 documentation files

---

## Phase 2: Automation & Enhancement (Weeks 4-6)

### 2.1 Automated Update Tracking
**Priority: High**

- [ ] Create update checker script
  - [ ] Check all tracked games for new updates
  - [ ] Compare against last known updates
  - [ ] Store new updates in database
  - [ ] Generate update summary

- [ ] Implement scheduling
  - [ ] Create cron job for daily checks (e.g., 2 AM local time)
  - [ ] Add logging and error notifications
  - [ ] Create manual trigger option
  - [ ] Document scheduling setup

- [ ] Add notification system (optional)
  - [ ] Email notifications for new updates
  - [ ] Summary reports
  - [ ] Error alerts

### 2.2 Social Media Pipeline - Instagram
**Priority: Medium**

- [ ] Research Instagram API
  - [ ] Review Meta Graph API documentation
  - [ ] Understand app review process
  - [ ] Create Meta Developer account
  - [ ] Submit app for Instagram Basic Display API access

- [ ] Design content templates
  - [ ] Patch notes format
  - [ ] Update announcement format
  - [ ] New game addition format
  - [ ] Create visual templates (PNG backgrounds)

- [ ] Build content generation
  - [ ] Template engine for post text
  - [ ] Image generation with PIL/Pillow
  - [ ] Hashtag generation
  - [ ] Link shortening (optional)

- [ ] Implement posting queue
  - [ ] Queue table in database
  - [ ] Staging area for review
  - [ ] Scheduling logic
  - [ ] Manual approval/rejection

- [ ] Create posting automation
  - [ ] Instagram API integration
  - [ ] Post scheduling script
  - [ ] Error handling and retries
  - [ ] Success logging

### 2.3 User Submission System
**Priority: Medium**

- [ ] Design submission form
  - [ ] Game name field
  - [ ] Steam ID/URL field
  - [ ] Necromancy justification (textarea)
  - [ ] Contact info (optional)

- [ ] Implement form on website
  - [ ] Create submission page/modal
  - [ ] Form validation
  - [ ] Submit to backend/API

- [ ] Create submission backend
  - [ ] API endpoint to receive submissions (or form service like Formspree)
  - [ ] Add to candidates table
  - [ ] Send confirmation (optional)

- [ ] Build review workflow
  - [ ] CLI tool or web interface to review candidates
  - [ ] Approve/reject actions
  - [ ] Add approved games to curated list
  - [ ] Update database

---

## Phase 3: Discovery & Expansion (Weeks 7-10)

### 3.1 Automated Game Discovery
**Priority: Low**

- [ ] Design keyword search strategy
  - [ ] Compile list of necromancy-related keywords
  - [ ] Consider Steam tags, descriptions, reviews
  - [ ] Define filtering criteria

- [ ] Build Steam search scraper
  - [ ] Search Steam by keywords
  - [ ] Filter by relevant tags
  - [ ] Extract game details
  - [ ] Score/rank by necromancy likelihood

- [ ] Create candidate pipeline
  - [ ] Run periodic searches
  - [ ] Add high-scoring games to candidates
  - [ ] Remove duplicates
  - [ ] Generate review reports

- [ ] Refine discovery algorithm
  - [ ] Iterate based on false positives/negatives
  - [ ] Add machine learning (optional, future)
  - [ ] Track discovery effectiveness

### 3.2 Advanced Website Features
**Priority: Medium**

- [ ] Enhanced filtering
  - [ ] Filter by necromancy dimensions
  - [ ] Filter by update recency
  - [ ] Filter by game genre/tags
  - [ ] Save filter presets

- [ ] Improved game details
  - [ ] Dedicated game detail pages
  - [ ] Show update history
  - [ ] Display Steam tags/genres
  - [ ] Link to Steam store page

- [ ] Analytics dashboard (optional)
  - [ ] Track update frequency by game
  - [ ] Visualize game additions over time
  - [ ] Show necromancy dimension distributions

- [ ] Performance optimization
  - [ ] Implement virtual scrolling for large tables
  - [ ] Optimize data loading
  - [ ] Add caching strategies

### 3.3 Multi-Platform Expansion
**Priority: Low**

- [ ] YouTube content pipeline
  - [ ] Research YouTube API
  - [ ] Design video template (shorts vs. long-form)
  - [ ] Implement video generation (optional: automated)
  - [ ] Manual posting workflow initially

- [ ] Additional game platforms
  - [ ] Research Epic Games Store API
  - [ ] Research itch.io API
  - [ ] Research GOG API
  - [ ] Implement platform adapters

- [ ] Cross-platform features
  - [ ] Unified game database schema
  - [ ] Platform-specific handling
  - [ ] Multi-platform game linking

---

## Phase 4: Polish & Growth (Ongoing)

### 4.1 Quality & Reliability
**Priority: Ongoing**

- [ ] Testing
  - [ ] Unit tests for core functions
  - [ ] Integration tests for data pipeline
  - [ ] Frontend component tests
  - [ ] End-to-end tests

- [ ] Monitoring
  - [ ] Error tracking
  - [ ] Uptime monitoring
  - [ ] Performance monitoring
  - [ ] Usage analytics

- [ ] Documentation
  - [ ] API documentation
  - [ ] Development setup guide
  - [ ] User guide for website
  - [ ] Contribution guidelines

### 4.2 Community & Engagement
**Priority: Low**

- [ ] Content strategy
  - [ ] Regular posting schedule
  - [ ] Engagement with followers
  - [ ] Cross-promotion

- [ ] Community features (future)
  - [ ] User accounts
  - [ ] Game ratings/reviews
  - [ ] Community submissions
  - [ ] Discussion forums

### 4.3 Maintenance & Iteration
**Priority: Ongoing**

- [ ] Regular curation
  - [ ] Review candidate games weekly
  - [ ] Add new games to tracking
  - [ ] Update classifications as games evolve

- [ ] Database maintenance
  - [ ] Archive old updates
  - [ ] Optimize queries
  - [ ] Backup strategy

- [ ] Feature requests
  - [ ] Collect user feedback
  - [ ] Prioritize enhancements
  - [ ] Iterate on design

---

## Immediate Next Steps (This Week)

1. **Set up Git repository and project structure**
2. **Get Steam API key**
3. **Design and implement database schema**
4. **Build basic Steam scraper for game details**
5. **Create initial games_list.yaml with 10-15 games**
6. **Set up React project with TanStack Table**

## Success Metrics by Phase

**Phase 1 (MVP):**
- 20+ games tracked
- Website deployed with working table
- Daily update checks running

**Phase 2 (Automation):**
- 50+ games tracked
- Instagram posting automated
- User submissions functional

**Phase 3 (Growth):**
- 100+ games tracked
- Automated discovery running
- Multi-platform content

**Phase 4 (Maturity):**
- 200+ games tracked
- Active social media presence
- Community engagement

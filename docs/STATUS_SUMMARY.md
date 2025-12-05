# Necro Game News - Status Summary

**Last Updated:** December 4, 2024
**Current Phase:** Enhancement & Expansion
**Live Site:** https://necrotic-realms.vercel.app/

---

## ✅ What's Live & Working

### Core Platform (Complete)
- **Website:** https://necrotic-realms.vercel.app/
- **Database:** 8 games tracked, 196+ updates
- **Automation:** Daily update checking via Steam API
- **Deployment:** Auto-deploy to Vercel on git push
- **Features:** Search, sort, filter, pagination, mobile-responsive

### Social Media Pipeline (Complete)
- **Instagram Content:** Automated generation (4:5 aspect ratio)
- **Captions:** AI-generated summaries exported to text files
- **Workflow:** Integrated into `deploy.sh` for daily automation
- **Queue:** Ephemeral (clears daily, focuses on recent updates)
- **Posting:** Manual (API access pending account establishment)

### Game Discovery (Complete)
- **Batch Processing:** Processing entire Steam catalog (~149k apps)
- **Scoring Algorithm:** Keyword-based necromancy detection
- **Review Tool:** Interactive CLI for candidate approval
- **Status:** Overnight run in progress (66+ hours ETA)

---

## 🎯 Current Priorities

### 1. User Submission Form (HIGH)
Add web form for community game suggestions
- Design modal or dedicated page
- Form validation (Steam ID, justification)
- Backend integration (Formspree or custom API)
- Wire to candidates database

### 2. Website Improvements (HIGH)
Polish UX and add features
- Advanced filtering (dimensions, genres, recency)
- Game detail view (modal or page)
- Performance optimizations
- Mobile improvements
- Loading states & error boundaries

### 3. YouTube Content Pipeline (MEDIUM)
Expand to video content
- Research YouTube API
- Define video format (Shorts vs. long-form)
- Create templates
- Build generation workflow
- Integrate into daily automation

---

## 📊 Current Statistics

- **Games Tracked:** 8 active
- **Total Updates:** 196+
- **Update Types:** patch, announcement, dlc, event, release
- **Discovery Running:** Yes (processing ~149k Steam apps)
- **Social Media:** Instagram content generated daily (manual posting)

---

## 🔄 Daily Workflow

**Fully Automated via `./scripts/deploy.sh`:**
1. Check for new Steam updates
2. Export data to JSON for website
3. Generate Instagram posts (today's updates, 4:5 images)
4. Export captions to text files
5. Clear social media queue (ephemeral)
6. Generate weekly report
7. Commit and push to GitHub → triggers Vercel deploy

**Manual Steps:**
- Instagram posting (content ready in `content/posts/` and `content/captions/`)
- Review and approve discovered games (`scripts/review_candidates.py`)

---

## 📝 Key Scripts

### Database Management
```bash
scripts/init_database.py                      # Initialize database
scripts/load_games_from_yaml.py --update      # Sync YAML changes
scripts/view_database.py --stats              # View statistics
```

### Data Collection
```bash
scripts/check_updates.py                      # Check for new updates
scripts/fetch_game_details.py                 # Fetch high-res screenshots
```

### Game Discovery
```bash
scripts/batch_discover.py --download          # Download full Steam catalog
scripts/batch_discover.py --discover --yes    # Run discovery (background)
scripts/batch_discover.py --stats             # Show progress
scripts/review_candidates.py                  # Interactive review tool
scripts/review_candidates.py --ignore-skipped # Only pending
```

### Social Media
```bash
scripts/generate_social_posts.py              # Generate posts (today only)
scripts/generate_social_posts.py --since DATE # From specific date
scripts/generate_social_posts.py --all        # All unprocessed
scripts/preview_social_posts.py --export-caption  # Export captions
```

### Complete Workflow
```bash
scripts/deploy.sh                             # Complete daily workflow
```

---

## 🎨 Necromancy Classification

Games evaluated across 3 dimensions (highest satisfied per dimension):

**Dimension 1: Centrality (how central is necromancy?)**
- **a)** Core Identity - Necromancer class/protagonist
- **b)** Specialization - Necromantic skill tree
- **c)** Isolated Features - Necromancy items/skills
- **d)** Flavor Only - Lore only

**Dimension 2: Point of View**
- **a)** Play AS necromancer (ARPGs, first-person)
- **b)** Control necromancer units (RTS, tactics)

**Dimension 3: Naming**
- **a)** Explicit "necromancer/necromancy"
- **b)** Implied/thematic death magic

---

## 🔧 Tech Stack

**Backend:** Python 3.11+, Steam Web API, SQLite
**Frontend:** React + Vite, TanStack Table, Tailwind CSS
**Hosting:** Vercel (auto-deploy on push)
**Social:** Instagram (manual posting), YouTube (planned)
**Automation:** Bash scripts (daily via deploy.sh)

---

## 📈 Completed Milestones

**Phase 1 (Foundation):** ✅ COMPLETE
- ✅ Website deployed and functional
- ✅ 8+ games tracked
- ✅ Daily update checking
- ✅ Search/filter/sort working

**Phase 2 (Social Media):** ✅ COMPLETE
- ✅ Instagram content pipeline
- ✅ Automated generation workflow
- ✅ 4:5 aspect ratio images
- ✅ AI-generated captions
- ✅ Integrated into deploy.sh

**Phase 3 (Discovery):** ✅ COMPLETE
- ✅ Batch discovery system
- ✅ Steam catalog download (149k apps)
- ✅ Keyword-based scoring
- ✅ Interactive review workflow
- ✅ Overnight processing running

---

## 🎯 Next Action Items

**This Week:**
1. Monitor overnight discovery run progress
2. Start reviewing discovered candidates
3. Begin user submission form design
4. Research YouTube API & video formats

**Next Week:**
1. Add 10-20 games from discovered candidates
2. Implement submission form backend
3. Build initial YouTube content templates
4. Set up cron automation for deploy.sh

**Within Month:**
1. 50+ games tracked
2. Submission form live on website
3. First YouTube videos posted
4. Advanced filtering implemented

---

## 📚 Documentation

- [TECHNICAL_ROADMAP.md](TECHNICAL_ROADMAP.md) - Implementation roadmap
- [PROGRESS.md](PROGRESS.md) - Progress tracker
- [GAME_DISCOVERY_GUIDE.md](GAME_DISCOVERY_GUIDE.md) - Discovery system guide
- [SOCIAL_MEDIA_WORKFLOW.md](SOCIAL_MEDIA_WORKFLOW.md) - Instagram workflow
- [PROJECT_VISION.md](PROJECT_VISION.md) - Project vision & goals
- [../README.md](../README.md) - Main project overview
- [../CLAUDE.md](../CLAUDE.md) - Quick reference for Claude Code

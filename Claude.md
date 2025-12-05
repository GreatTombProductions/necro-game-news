Necro Game News tracks game updates for necromantic games via automated Steam scraping, a searchable website, and social media content generation.

CURRENT STATUS: Phase 3 COMPLETE ✅ → Phase 4 (Enhancement & Expansion)
Live Website: https://necrotic-realms.vercel.app/
Game Discovery: Processing full Steam catalog (~149k apps, 66h runtime)

CURRENT PRIORITIES:
1. User submission form (website integration)
2. Website improvements (filtering, game details, polish)
3. YouTube/video content pipeline

NECROMANCY CLASSIFICATION (3 dimensions, highest satisfied per dimension):
- Dim 1 Centrality: a) Core class > b) Specialization > c) Isolated features > d) Flavor only
- Dim 2 POV: a) Play AS necromancer > b) Control necromancer units
- Dim 3 Naming: a) Explicit "necromancer" > b) Implied/thematic

TECH STACK:
- Backend: Python 3.11+, Steam Web API, SQLite
- Frontend: React + Vite, TanStack Table, Tailwind (Vercel deployment)
- Automation: Bash scripts (deploy.sh)
- Social: Instagram (manual), YouTube (planned)

COMPLETED PHASES:

PHASE 1 - Foundation ✅
- Database with 8 games, 196+ updates
- Steam API scraper with rate limiting
- React frontend with search/sort/filter/pagination
- Vercel auto-deploy
- Export pipeline (DB → JSON → Frontend)

PHASE 2 - Social Media ✅
- Instagram content generation (4:5 images, 1080×1350)
- AI caption generation
- Ephemeral queue (daily clearing)
- High-res screenshot support
- Integrated into deploy.sh
- Date filtering (--since, --all flags)

PHASE 3 - Game Discovery ✅
- Batch discovery system (entire Steam catalog)
- Keyword-based scoring algorithm
- Interactive CLI review tool (y/n/s/o/q controls)
- Status tracking (pending/approved/rejected/skipped)
- Database migrations
- Auto-append approved games to YAML
- Overnight processing (146k apps)

KEY SCRIPTS:

Database Management:
- scripts/init_database.py - Initialize database
- scripts/load_games_from_yaml.py --update - Sync YAML to DB
- scripts/view_database.py --stats - View statistics

Data Collection:
- scripts/check_updates.py - Check for new updates
- scripts/fetch_game_details.py - Fetch high-res screenshots

Game Discovery:
- scripts/batch_discover.py --download - Download Steam catalog
- scripts/batch_discover.py --discover --yes - Run discovery (background)
- scripts/batch_discover.py --stats - Show progress
- scripts/review_candidates.py - Interactive review
- scripts/review_candidates.py --ignore-skipped - Only pending

Social Media:
- scripts/generate_social_posts.py - Generate posts (today)
- scripts/generate_social_posts.py --since DATE - From specific date
- scripts/generate_social_posts.py --all - All unprocessed
- scripts/preview_social_posts.py --export-caption - Export captions

Complete Workflow:
- scripts/deploy.sh - Daily automation (updates, social, deploy)

DAILY WORKFLOW (automated via ./scripts/deploy.sh):
1. Check for new Steam updates
2. Export DB to JSON for frontend
3. Generate Instagram posts (today only)
4. Export captions to text files
5. Clear social media queue
6. Generate weekly report
7. Git commit/push (triggers Vercel deploy)

Post content: content/posts/ (images), content/captions/ (text)

NEXT ACTIONS:
- Design user submission form (modal or page)
- Implement advanced filtering UI
- Research YouTube API and video formats
- Review discovered game candidates
- Expand to 50+ tracked games

See docs/TECHNICAL_ROADMAP.md for detailed roadmap.
See docs/STATUS_SUMMARY.md for current status.
See docs/GAME_DISCOVERY_GUIDE.md for discovery system docs.

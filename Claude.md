Necro Game News tracks game updates for necromantic games via automated Steam scraping, a searchable website, and social media content generation.

CURRENT STATUS: Phase 2 COMPLETE ✅ → Phase 3 Starting
Live Website: https://necrotic-realms.vercel.app/
Instagram Content: Daily automated generation (manual posting)

NECROMANCY CLASSIFICATION (3 dimensions, highest satisfied per dimension):
- Dim 1 Centrality: a) Core class > b) Specialization > c) Isolated features > d) Flavor only
- Dim 2 POV: a) Play AS necromancer > b) Control necromancer units
- Dim 3 Naming: a) Explicit "necromancer" > b) Implied/thematic

TECH STACK:
- Backend: Python 3.11+, Steam Web API, SQLite
- Frontend: React + Vite, TanStack Table, Tailwind (DEPLOYED on Vercel)
- Automation: Local scripts (deploy.sh)
- Social: Instagram (manual posting, API pending)

PHASE 1 COMPLETE:
✅ Database schema with 8 games, 196 updates
✅ Steam scraper with rate limiting and update classification
✅ React frontend with search/sort/filter/pagination
✅ Vercel deployment with auto-deploy on push
✅ Export pipeline (DB → JSON → Frontend)

PHASE 2 COMPLETE (Social Media - Manual Workflow):
✅ Instagram post template with AI caption generation
✅ Image compositor (4:5 aspect ratio, 1080×1350 for Instagram feed)
✅ High-resolution screenshots (1920×1080, not 460×215 headers)
✅ Content generator with date filtering (ephemeral, not backlog-focused)
✅ Ephemeral queue system (clears daily, no accumulation)
✅ Clean captions (no header, starts with AI summary)
✅ Improved classification (5 types: patch, announcement, dlc, event, release)
✅ Caption export to text files
✅ Integrated into daily deploy.sh workflow
✅ Date filtering: defaults to today, --since for specific dates, --all for backlog

KEY SCRIPTS:
- scripts/check_updates.py - Check for new game updates
- scripts/export_for_web.py - Export DB to JSON for frontend
- scripts/load_games_from_yaml.py --update - Sync YAML changes to DB
- scripts/view_database.py --stats - View database contents
- scripts/generate_report.py --days 7 - Generate reports
- scripts/fetch_game_details.py - Fetch high-res screenshots from Steam
- scripts/generate_social_posts.py - Generate posts (defaults to today, use --since or --all)
- scripts/preview_social_posts.py - Preview, export captions, manage queue
- scripts/deploy.sh - Complete daily workflow (updates, social, deploy)

DAILY WORKFLOW (automated via ./scripts/deploy.sh):
1. python scripts/check_updates.py
2. python scripts/export_for_web.py
3. python scripts/generate_social_posts.py --generate-images (today's updates only)
4. python scripts/preview_social_posts.py --export-caption
5. Clear social media queue (ephemeral, no accumulation)
6. python scripts/generate_report.py --days 7
7. git add/commit/push (triggers Vercel deploy)

Post content is in content/posts/ (images) and content/captions/ (text files)

PHASE 2.3 - DEFERRED (Instagram API automation):
- Apply for Instagram API access (requires established account)
- Automated posting via Meta Graph API
- NOTE: Manual workflow via deploy.sh is sufficient for now

PHASE 3 PRIORITIES:
1. Set up cron automation for daily deploy.sh
2. Start posting Instagram content manually (build audience)
3. Expand to 20-30 games (then 50+)
4. Add user submission form
5. Advanced filtering on website
6. Email notifications for new updates (optional)

See docs/STATUS_SUMMARY.md, docs/PROGRESS.md, and docs/TECHNICAL_ROADMAP.md for full details.
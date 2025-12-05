Necro Game News tracks game updates for necromantic games via automated Steam scraping, a searchable website, and social media content generation.

CURRENT STATUS: Phase 2.1 - Social Media Pipeline ✅
Live Website: https://necrotic-realms.vercel.app/
Instagram Content: Manual posting workflow ready

NECROMANCY CLASSIFICATION (3 dimensions, highest satisfied per dimension):
- Dim 1 Centrality: a) Core class > b) Specialization > c) Isolated features > d) Flavor only
- Dim 2 POV: a) Play AS necromancer > b) Control necromancer units
- Dim 3 Naming: a) Explicit "necromancer" > b) Implied/thematic

TECH STACK:
- Backend: Python 3.11+, Steam Web API, SQLite
- Frontend: React + Vite, TanStack Table, Tailwind (DEPLOYED on Vercel)
- Automation: Local scripts (ready for cron)
- Social: Instagram (Phase 2 - Meta Graph API)

PHASE 1 COMPLETE:
✅ Database schema with 8 games, 196 updates
✅ Steam scraper with rate limiting and update classification
✅ React frontend with search/sort/filter/pagination
✅ Vercel deployment with auto-deploy on push
✅ Export pipeline (DB → JSON → Frontend)

PHASE 2.1 COMPLETE (Social Media):
✅ Instagram post template system with content philosophy
✅ Image compositor (game screenshots + text overlays)
✅ High-resolution screenshots (1920×1080, not 460×215 headers)
✅ Content generator pulling from database
✅ Queue management system
✅ Improved classification (5 types: patch, announcement, dlc, event, release)
✅ Caption export to text files
✅ Preview and manual posting workflow
✅ 155+ updates ready for content generation

KEY SCRIPTS:
- scripts/check_updates.py - Check for new game updates
- scripts/export_for_web.py - Export DB to JSON for frontend
- scripts/load_games_from_yaml.py --update - Sync YAML changes to DB
- scripts/view_database.py --stats - View database contents
- scripts/generate_report.py --days 7 - Generate reports
- scripts/fetch_game_details.py - Fetch high-res screenshots from Steam
- scripts/generate_social_posts.py - Queue updates for Instagram
- scripts/preview_social_posts.py - Preview, export captions, manage queue

DAILY WORKFLOW (current, all handled by ./scripts/deploy.sh):
1. python scripts/check_updates.py
2. python scripts/export_for_web.py
3. git add/commit/push (triggers Vercel deploy)

PHASE 2 NEXT STEPS:
1. ✅ Instagram content pipeline (DONE!)
2. Start posting content manually (build audience)
3. Apply for Instagram API access (requires established account)
4. Set up cron automation for update checking
5. Expand to 50+ games
6. Add user submission form

See PROGRESS.md, TECHNICAL_ROADMAP.md, and PROJECT_INSTRUCTIONS.md for full details.
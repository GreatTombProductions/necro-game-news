Necro Game News tracks game updates for necromantic games via automated Steam scraping, a searchable website, and social media content generation.

Live Website: https://necrotic-realms.vercel.app/

NECROMANCY CLASSIFICATION (3 dimensions, highest satisfied per dimension):
- Dim 1 Centrality: a) Core class > b) Specialization > c) Isolated features > d) Flavor only
- Dim 2 POV: a) Play AS necromancer > b) Control necromancer units
- Dim 3 Naming: a) Explicit "necromancer" > b) Implied/thematic

TECH STACK:
- Backend: Python 3.9+, Steam Web API, SQLite
- Frontend: React + Vite, TanStack Table, Tailwind (Vercel deployment)
- Automation: Bash scripts (deploy.sh)
- Social: Instagram (manual)

KEY SCRIPTS:

Daily Workflow:
- scripts/deploy.sh - Main automation (updates, content, deploy)
  Flags: --full, --updates-only, --content-only, --reprocess

Game Discovery:
- scripts/batch_discover.py --download - Download Steam catalog
- scripts/batch_discover.py --discover --yes - Run discovery
- scripts/batch_discover.py --stats - Show progress
- scripts/review_candidates.py - Interactive review (y/n/s/o/q)

Database:
- scripts/init_database.py - Initialize database
- scripts/load_games_from_yaml.py --update - Sync YAML to DB
- scripts/view_database.py --stats - View statistics

Data Collection:
- scripts/check_updates.py - Check for new updates
- scripts/fetch_game_details.py - Fetch screenshots/details

Social Media:
- scripts/generate_social_content.py - Generate posts
- scripts/generate_social_content.py --reprocess - Regenerate
- scripts/migrations/backfill_tags.py - Backfill Steam tags

Output: content/posts/ (images), content/captions/ (text)

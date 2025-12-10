Necro Game News tracks game updates for necromantic games via multi-platform scraping (Steam, Battle.net), a searchable website, and social media content generation.

Live Website: https://necrotic-realms.vercel.app/

NECROMANCY CLASSIFICATION (3 dimensions, highest satisfied per dimension):
- Dim 1 Centrality: a) Core class > b) Specialization > c) Isolated features > d) Flavor only
- Dim 2 POV: a) Play AS necromancer > b) Control necromancer units
- Dim 3 Naming: a) Explicit "necromancer" > b) Implied/thematic

TECH STACK:
- Backend: Python 3.9+, SQLite
- Data Sources: Steam Web API, Steamspy API, Blizzard News API
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

Game Editing:
- scripts/browse_games.py - Browse/edit games needing dimension_4 or notes
  Flags: --all (all games), --no-deploy, --search TERM
  Controls: e=edit, s/n=next, p=prev, o=open browser, g=goto, q=quit
  Auto-deploys on exit (option 3: new games only)

Database:
- scripts/init_database.py - Initialize database
- scripts/load_games_from_yaml.py --update - Sync YAML to DB
- scripts/view_database.py --stats - View statistics

Data Collection:
- scripts/check_updates.py - Check for new updates (all platforms)
- scripts/fetch_game_details.py - Fetch screenshots/details (Steam)

Social Media:
- scripts/generate_social_content.py - Generate posts
- scripts/generate_social_content.py --reprocess - Regenerate
- scripts/migrations/backfill_tags.py - Backfill Steam tags

Discord Bot (Admin Approvals):
- scripts/discord_bot.py - Run bot to approve submissions
  Env vars: DISCORD_BOT_TOKEN, DISCORD_CHANNEL_ID (optional)
  Commands:
    - React ✅ on submission embed to approve (if all fields valid)
    - React 🔄 to confirm overwrite of existing game
    - /add <id> [overrides] - Add game with optional field overrides
    - /edit <id> <changes> - Edit existing game entry
    - /check <id> - Check if game exists and show current data
  Override syntax: centrality:a pov:character naming:explicit notes:text
  Identifier formats: 552500 (steam), battlenet:diablo-4, "Game Name"

Output: content/posts/ (images), content/captions/ (text)

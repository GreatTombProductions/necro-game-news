# Necro Game News

Automated tracking and content platform for games featuring necromancy. Tracks updates via multi-platform scraping (Steam, Battle.net), serves a searchable website, generates social media content, and accepts community game submissions.

**Live Website:** https://necrotic-realms.vercel.app/

---

## Classification Taxonomy

> **Authoritative reference:** `docs/TAXONOMY.md` — complete classification guide.
> **YAML schema:** `docs/YAML_SCHEMA.md` — field reference for `games_list.yaml`.

### Quick Reference

Games are classified across 4 dimensions (highest satisfied per dimension):

| Dim | Name | Values | Question |
|-----|------|--------|----------|
| 1 | Centrality | `a` Core / `b` Branch / `c` Isolated / `d` Minimal | How deeply is necromancy integrated? |
| 2 | POV | `character` / `unit` | Play AS necromancer or control them? |
| 3 | Naming | `explicit` / `implied` | Uses "necromancer" term? |
| 4 | Availability | `instant` / `gated` / `unknown` | How accessible is necromantic content? |

**Blood Registry** (separate YAML): vampirism (`outright`/`implied`/`channeled`/`absent`), hemomancy (`a`/`b`/`c`/`d`/`absent`), POV, availability.

---

## Intake Pipeline (Slimeko-Managed)

Community submissions now route through **Slimeko** (community manager) instead of relying solely on Discord reactions. The intake pipeline:

```
Submission Form → Vercel API → Discord Webhook → Discord Bot
                                                    ├──→ Writes local JSON (data/submissions/)
                                                    └──→ (existing approval flow unchanged)
                                          
Local JSON → submission_pickup.py → Slimeko Inbox → Slimeko reviews
                                                       ├──→ steam_lookup.py (find Steam ID)
                                                       ├──→ review_game.py (research + classify)
                                                       ├──→ Report to Ray for approval
                                                       └──→ add_game_to_yaml.py (add + deploy)
```

### Intake Scripts

**Steam Lookup:**
```bash
# Search Steam by game name
./venv/bin/python scripts/steam_lookup.py search "Mewgenics"
./venv/bin/python scripts/steam_lookup.py search "V Rising" --json

# Get full details for a Steam App ID
./venv/bin/python scripts/steam_lookup.py details 2344520
./venv/bin/python scripts/steam_lookup.py details 2344520 --report  # Markdown for Ray
```

**Submission Pickup:**
```bash
# Dry run: see what submissions are pending
python3 scripts/submission_pickup.py

# Write inbox files for Slimeko
python3 scripts/submission_pickup.py --execute
```

**Review Game (main workflow):**
```bash
# Full interactive workflow: search → review → classify → report
./venv/bin/python scripts/review_game.py "Mewgenics"

# From known Steam ID with submitter suggestions
./venv/bin/python scripts/review_game.py --steam-id 2344520 \
    --suggested dim1=b,dim2=unit,dim3=explicit,dim4=gated \
    --notes "Necromancer class in the game" \
    --submitter player

# Generate report only (non-interactive)
./venv/bin/python scripts/review_game.py --steam-id 2344520 --report \
    --suggested dim1=a,dim2=character,dim3=explicit \
    --notes "Core necromancer class"
```

**Add Game to YAML (after Ray approves):**
```bash
./venv/bin/python scripts/add_game_to_yaml.py \
    --name "Mewgenics" --steam-id 1234567 \
    --dim1 b --dim2 unit --dim3 explicit --dim4 gated \
    --notes "Necromancer class" --priority high --deploy
```

---

## Data Model

**Canonical source of truth:** `data/games_list.yaml` (necromancy) and `data/blood_games_list.yaml` (blood). The SQLite DB (`data/necro_games.db`) is a derived cache.

**Data flow:**
```
YAML → load_games_from_yaml.py → SQLite DB → export_for_web.py → frontend JSON → Vercel deploy
```

See `docs/YAML_SCHEMA.md` for the complete field reference and validation checklist.

---

## Tech Stack

- **Backend:** Python 3.9+, SQLite
- **Data Sources:** Steam Web API, Steamspy API, Blizzard News API
- **Frontend:** React + Vite, TanStack Table, Tailwind CSS
- **Hosting:** Vercel (auto-deploy on push)
- **Social:** Instagram (manual posting)
- **Intake:** Discord webhook → bot → local JSON → Slimeko inbox pipeline

---

## Key Scripts

### Daily Workflow
- `scripts/deploy.sh` — Main automation (updates, content, deploy)
  - Flags: `--full`, `--updates-only`, `--content-only`, `--reprocess`

### Game Discovery
- `scripts/batch_discover.py --download` — Download Steam catalog
- `scripts/batch_discover.py --discover --yes` — Run discovery
- `scripts/batch_discover.py --stats` — Show progress
- `scripts/review_candidates.py` — Interactive review (y/n/s/o/q)

### Game Editing
- `scripts/browse_games.py` — Browse/edit games needing dimension_4 or notes
  - Flags: `--all`, `--no-deploy`, `--search TERM`
  - Controls: e=edit, s/n=next, p=prev, o=open browser, g=goto, q=quit

### Database
- `scripts/init_database.py` — Initialize database
- `scripts/load_games_from_yaml.py --update` — Sync YAML to DB
- `scripts/view_database.py --stats` — View statistics

### Data Collection
- `scripts/check_updates.py` — Check for new updates (all platforms)
- `scripts/fetch_game_details.py` — Fetch screenshots/details (Steam)

### Social Media
- `scripts/generate_social_content.py` — Generate posts
- `scripts/generate_social_content.py --reprocess` — Regenerate
- `scripts/migrations/backfill_tags.py` — Backfill Steam tags

### Intake (Slimeko)
- `scripts/steam_lookup.py search/ details` — Steam game research
- `scripts/submission_pickup.py [--execute]` — Route submissions to Slimeko's inbox
- `scripts/review_game.py` — Research, classify, generate Ray review report
- `scripts/add_game_to_yaml.py` — Validated addition to YAML + deploy

### Discord Bot (legacy approval, still active)
- `scripts/discord_bot.py` — Run bot to approve submissions
  - Env vars: `DISCORD_BOT_TOKEN`, `DISCORD_CHANNEL_ID` (optional)
  - Commands: `/add`, `/edit`, `/check` (see `--help`)
  - Now also writes local JSON files for Slimeko intake (on_message webhook catch)

---

## Output

- `content/posts/` — Generated images (Instagram)
- `content/captions/` — Generated captions (Instagram)
- `frontend/public/data/` — JSON exports for website
- `data/submissions/` — Pending community submissions (Slimeko intake)

---

## AI Maintainer Quick Start

**Adding a game from a community submission:**

1. Check for pending submissions: `python3 scripts/submission_pickup.py`
2. If submissions found, run with `--execute` to create inbox files
3. For each game in your inbox:
   a. Search Steam: `./venv/bin/python scripts/steam_lookup.py search "Game Name"`
   b. Research and classify: `./venv/bin/python scripts/review_game.py --steam-id XXXXX --report --suggested ...`
   c. Send the generated Markdown report to Ray for review
   d. After approval: `./venv/bin/python scripts/add_game_to_yaml.py ... --deploy`

**Adding a game from your own research:**

1. Search Steam: `./venv/bin/python scripts/steam_lookup.py search "Game Name"`
2. Get details: `./venv/bin/python scripts/steam_lookup.py details XXXXX`
3. Review the description for necromantic content
4. Classify using docs/TAXONOMY.md as reference
5. Generate report and send to Ray
6. After approval: add_game_to_yaml.py --deploy

**Before committing a new game, verify:**
- [ ] `steam_id` is correct (check store.steampowered.com/app/{id})
- [ ] `name` matches Steam's exact title
- [ ] All 3+1 classification dimensions are valid
- [ ] `dimension_1_notes` explains centrality classification
- [ ] Game is alphabetically ordered in the list
- [ ] No duplicate steam_id
- [ ] YAML is valid (`python3 -c "import yaml; yaml.safe_load(open('data/games_list.yaml'))"`)

---

*This document is the entry point for AI maintainers. For classification details, see `docs/TAXONOMY.md`. For YAML field reference, see `docs/YAML_SCHEMA.md`.*

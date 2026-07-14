# YAML Schema Reference — games_list.yaml

> Complete field reference for the Necromancy Game Registry YAML files. This document is the AI-maintainer's canonical source for what fields exist, what they mean, and how to write them.

---

## File Locations

| Registry | Path | Notes |
|----------|------|-------|
| Necromancy | `data/games_list.yaml` | Primary registry (193+ games) |
| Blood (Vampire) | `data/blood_games_list.yaml` | Vampire/blood magic registry |

Both files use the same top-level structure: a `games:` list of game entries. The blood registry has different classification fields (documented separately below).

---

## Top-Level Structure

```yaml
games:
  - name: "Game Title"
    # ... fields ...
  - name: "Another Game"
    # ... fields ...
```

The file is a single YAML document with one key `games` containing a list of game entry mappings.

---

## Necromancy Registry — Game Entry Fields

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Full game title as it appears on Steam. Use exact Steam name including punctuation. Quote if it contains special YAML characters (`:`, `{`, `}`, `[`, `]`, `,`, `&`, `*`, `?`, `\|`, `-`, `<`, `>`, `=`, `!`, `%`, `@`, `` ` ``). |
| `steam_id` | integer | Steam App ID. This is the canonical identifier. Found in the Steam store URL: `store.steampowered.com/app/{steam_id}/`. |
| `classification` | mapping | Classification dimensions (see below) |
| `priority` | string | One of: `high`, `medium`, `low` |
| `date_updated` | string | ISO date (`YYYY-MM-DD`) when the entry was last modified |

### Classification Sub-Mapping

```yaml
classification:
  dimension_1: a        # required — a, b, c, or d
  dimension_2: character # required — character or unit
  dimension_3: explicit  # required — explicit or implied
  dimension_4: instant   # optional — instant, gated, or unknown (default: unknown)
```

All three required dimensions must be present when adding a game. See `docs/TAXONOMY.md` for the full classification guide.

### Optional Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `aliases` | list of strings | Alternative names for search. Include common abbreviations, alternate punctuation, common misspellings. Example: `["Diablo 4", "D4"]` for "Diablo IV". |
| `dimension_1_notes` | string | Required in practice — justification for centrality classification. See TAXONOMY.md for what makes good notes. |
| `dimension_2_notes` | string | Optional — justification for POV classification when non-obvious |
| `dimension_3_notes` | string | Optional — where the "necromancy" name appears, if notable |
| `dimension_4_notes` | string | Optional — how necromancy is unlocked, if gated |

### Multi-Platform Fields

For games available on platforms other than Steam:

| Field | Type | Description |
|-------|------|-------------|
| `battlenet_id` | string | Battle.net API slug. Example: `diablo-4` |
| `battlenet_store_id` | string | Battle.net store slug if different from API slug. Example: `diablo-iv` |
| `gog_id` | string | GOG game ID |
| `epic_id` | string | Epic Games Store ID |
| `itchio_id` | string | itch.io game ID |
| `platforms` | list of strings | All platforms the game is on. Valid values: `steam`, `battlenet`, `gog`, `epic`, `itchio`, `manual` |
| `primary_platform` | string | Where to fetch updates from. Default: `steam`. Valid: same as `platforms`. |

### Price Fields

| Field | Type | Description |
|-------|------|-------------|
| `price_notes` | string | Pricing caveats. Example: "Requires Crimson Court DLC (~12.99 USD)", "Free to play, necromancer class is paid" |

---

## Blood Registry — Game Entry Fields

The blood registry has different classification dimensions:

### Classification Sub-Mapping (Blood)

```yaml
classification:
  vampirism: outright    # outright, implied, channeled, absent
  hemomancy: a           # a, b, c, d, absent
  pov: character         # character or unit
  availability: instant  # instant, gated, unknown
```

### Blood-Specific Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `vampirism_notes` | string | Justification for vampirism classification |
| `hemomancy_notes` | string | Justification for blood magic classification |
| `pov_notes` | string | POV justification if non-obvious |

The blood registry also has `aliases`, `platforms`, `battlenet_id`, `price_notes`, `date_updated`, and `priority` — same semantics as necromancy registry.

---

## YAML Formatting Rules

### String Quoting

Always quote strings containing YAML special characters. The most common pitfall is colons in game names:

```yaml
# WRONG — YAML treats the colon as a mapping separator
name: Skul: The Hero Slayer

# RIGHT — quoted
name: 'Skul: The Hero Slayer'
```

Other characters that require quoting: `{`, `}`, `[`, `]`, `,`, `&`, `*`, `?`, `|`, `-`, `<`, `>`, `=`, `!`, `%`, `@`, `` ` ``.

**Safe rule:** If the string contains anything other than alphanumerics, spaces, and underscores, quote it.

### Multi-Line Notes

For long `dimension_1_notes`, use YAML folded block scalars (`>`) to wrap:

```yaml
dimension_1_notes: >-
  Melinoe canonically has necromancy abilities as revealed in dialogue,
  but they do not affect gameplay, apart from the "Necromantic Influence"
  incantation and Night Bloom hex ("The dead, be born again!")
```

Or just use a long quoted string — YAML allows it.

### Indentation

Use 2-space indentation. The file was established with this convention and consistency matters.

### Ordering

Games in the list should be kept alphabetically by `name`. When adding a game, find its alphabetical position. The `scripts/add_game_to_yaml.py` script handles this.

---

## Common YAML Patterns from Existing Data

### Minimal Entry (Tier A, no ambiguity)

```yaml
- name: Boneraiser Minions
  steam_id: 1944570
  classification:
    dimension_1: a
    dimension_2: character
    dimension_3: explicit
    dimension_4: instant
  priority: medium
  date_updated: '2025-12-09'
  dimension_1_notes: Entire game centered on "boneraising" which is just necromancy
```

### Entry with Notes and Aliases

```yaml
- name: Diablo IV
  steam_id: 2344520
  battlenet_id: diablo-4
  battlenet_store_id: diablo-iv
  platforms:
  - steam
  - battlenet
  primary_platform: steam
  aliases:
  - Diablo 4
  - D4
  classification:
    dimension_1: a
    dimension_2: character
    dimension_3: explicit
    dimension_4: instant
  priority: high
  date_updated: '2025-12-09'
  dimension_1_notes: Necromancer is one of the core playable classes with full class identity
```

### Tier D Entry (minimal, with detailed justification)

```yaml
- name: Hades II
  steam_id: 1145350
  aliases:
  - Hades 2
  classification:
    dimension_1: d
    dimension_2: character
    dimension_3: explicit
    dimension_4: instant
  priority: low
  date_updated: '2025-12-09'
  dimension_1_notes: >-
    Melinoe canonically has necromancy abilities as revealed in dialogue,
    but they do not affect gameplay, apart from the "Necromantic Influence"
    incantation and Night Bloom hex ("The dead, be born again!")
```

---

## Database Sync

The YAML files are the **canonical source of truth**. The SQLite database (`data/necro_games.db`) is a derived cache for the website and update-checking scripts. Changes flow:

```
YAML → load_games_from_yaml.py → SQLite DB → export_for_web.py → frontend JSON
```

When adding a game:

```bash
# 1. Add to YAML (manually or via script)
# 2. Sync to database
./venv/bin/python scripts/load_games_from_yaml.py --update --sync

# 3. Export for website
./venv/bin/python scripts/export_for_web.py

# 4. Deploy (commits JSON + pushes to trigger Vercel deploy)
git add data/games_list.yaml frontend/public/data/*.json
git commit -m "Add GAME_NAME to necromancy registry"
git push origin main
```

Or use the deploy script for the "new games only" path:
```bash
./scripts/deploy.sh --new-only
```

---

## Validation Checklist (Before Adding a Game)

Before committing a new game entry, verify:

- [ ] `steam_id` is correct (verify on store.steampowered.com/app/{id})
- [ ] `name` matches Steam's exact title (copy-paste from store page)
- [ ] All three classification dimensions are present and valid
- [ ] `dimension_1_notes` explains the centrality classification
- [ ] `date_updated` is today's date in YYYY-MM-DD format
- [ ] Game is inserted in alphabetical order in the list
- [ ] No duplicate `steam_id` (check existing list)
- [ ] YAML is valid (no parse errors)
- [ ] Game has been deployed (YAML synced to DB, JSON exported, pushed)

---

*This document lives at `docs/YAML_SCHEMA.md`. Update it if new fields are added or conventions change.*

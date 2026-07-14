# Necromancy Game Classification Taxonomy

> AI-maintainer reference for classifying games in the Necro Game News registry. This document defines the classification dimensions, their valid values, decision boundaries, and edge cases.

---

## Overview

Games are classified across **four dimensions**, each capturing a different axis of what it means for a game to "have necromancy." The classification answers: **how central, from whose perspective, how explicitly named, and how accessible.**

The four dimensions are orthogonal — a game can be high on one and low on another. There is no composite "necromancy score"; each dimension stands alone.

---

## Dimension 1: Centrality

**Question answered:** How deeply is necromancy integrated into the game's identity and gameplay?

This is the most important dimension. It's a four-tier scale, graded by the highest level satisfied.

### Tier A: Core Identity

**Code:** `a`
**Label:** Core

Necromancy is central to the character, unit, or faction's identity AND gameplay. It's not just an option — it defines who you are or what you do.

**Criteria (any one is sufficient):**
- Necromancer is a playable class/character that is explicitly about raising/commanding the dead
- The game's core loop involves necromantic mechanics (raising dead, commanding undead armies, soul manipulation)
- The protagonist IS a necromancer by default (not optional)

**Examples:**
- Diablo IV — Necromancer is one of the core playable classes with full necromantic identity
- Iratus: Lord of the Dead — You ARE the necromancer, entire game is necromancy
- Boneraiser Minions — Core loop is raising undead minions
- Undead Horde — Play as a necromancer raising armies
- Total War: WARHAMMER — Vampire Counts faction = necromancy as faction identity

**Edge case — "not optional" vs "one of many":** If necromancy is a class among many but the class is fully realized (full skill tree, identity, gameplay fantasy), it's still tier A. The test is: when you play the necromantic option, is necromancy your identity? If yes, tier A.

### Tier B: Specialization / Dedicated Branch

**Code:** `b`
**Label:** Dedicated Branch

Necromancy is a cohesive, named specialization within a broader game. It's not the core identity, but it's a recognized and developed path.

**Criteria:**
- A dedicated necromancy skill tree, school, or specialization exists
- The necromantic path has multiple abilities that form a coherent playstyle
- It's a recognized build/path, not a single skill

**Examples:**
- Baldur's Gate 3 — Necromancy School for wizards with multiple necromancy spells
- Absolum — Ritual of Necromancy school of spells (Galandra)
- Wolcen: Lords of Mayhem — Undead summon skills + Plaguebringer passive branch
- Kingdom Rush Vengeance — Necromancer tower type available
- Nobody Saves the World — Necromancer form with multiple skills

**Decision boundary vs. Tier C:** If there are multiple necromantic abilities that form a coherent set (a "build" or "path"), it's tier B. If there are scattered necromantic elements that don't cohere into a recognized specialization, it's tier C.

### Tier C: Isolated Features

**Code:** `c`
**Label:** Isolated

Necromantic elements exist but are scattered — individual skills, items, or mechanics without a cohesive framework.

**Criteria:**
- Individual necromantic skills/items exist
- No dedicated necromancy specialization or build path
- The necromantic elements don't define any particular playstyle

**Examples:**
- Skul: The Hero Slayer — Grave Digger skull, necromancy inscription (individual items/skulls)
- Lost Ark — Necromancy engraving (single mechanic, summons temporary soldiers)
- SWORN — Cliona blessings have necromancy themes but scattered across different blessings
- Hell Clock — 2 ghost summoning skills, temporary ghost summon
- Solo Leveling: ARISE — Some shadow soldier skills, character has necromancer class lore

**Decision boundary vs. Tier D:** If the necromantic elements have ANY gameplay impact (even minor), it's tier C. If they exist only in lore/description/flavor without gameplay manifestation, it's tier D.

### Tier D: Flavor Only

**Code:** `d`
**Label:** Minimal

Necromancy is present by technicality — lore references, character backstory, aesthetic themes — with minimal or no gameplay impact.

**Criteria:**
- Necromancy referenced in lore, dialogue, or character design
- No meaningful necromantic gameplay mechanics
- Or: a single minor necromantic element with negligible impact

**Examples:**
- Hades II — Melinoe has necromancy abilities in lore but they don't affect gameplay (apart from rare incantations)
- Have a Nice Death — Death has necromantic powers in lore, not used in gameplay
- Overlord: Fellowship of Evil — Character called "necromancer" but only has generic purple magic
- Cubic Cosmos — Necromancer card exists, summons shadow bats (minor impact)
- Deck of Haunts — Play as a Haunted House, some spirit conjuring flavor
- Shadow Gambit: The Cursed Crew — Red Marley reanimates skeletons in cutscene/lore
- Necronator: Dead Wrong — Technically summoning skeletons via cards, but it's flavor-level

**Decision boundary vs. tier C:** The "gameplay impact" test. Does the necromantic element change how the player plays? If yes (even slightly), tier C. If no (purely aesthetic/lore), tier D.

### Classification Heuristics

1. **Start high, justify down.** Default assumption: if a game was submitted or discovered, there's probably real necromancy. Only downgrade if evidence is weak.

2. **The "would a player seeking necromancy be satisfied?" test:** For tier A, the answer should be "yes, this IS a necromancy game." For tier B, "there's a real necromancy path here." For tier C, "there are necromantic elements." For tier D, "it's technically present."

3. **Research before classifying.** Always check the Steam description, tags, and community discussions before finalizing. The Steam store page description is the primary source.

4. **Document your reasoning.** Every classification should have `dimension_1_notes` explaining WHY. This is load-bearing — future maintainers need to see your reasoning.

---

## Dimension 2: Point of View

**Question answered:** Whose perspective does the necromancy operate from?

### Character POV

**Code:** `character`
**Label:** Play AS necromancer

You directly control a necromancer character. The necromancy is channeled through your character.

**Criteria:**
- You play as a specific character who IS a necromancer
- Your character has necromantic abilities they personally use
- Even in party-based games, if one of your controllable characters is a necromancer, this applies

**Examples:**
- Diablo IV (play as Necromancer class)
- Skyrim (your character can be a necromancer)
- Baldur's Gate 3 (your wizard specializes in necromancy)
- Most RPGs with necromancer classes

### Unit POV

**Code:** `unit`
**Label:** Control necromancer units

You command necromancer units or a necromantic faction, but you are not personally the necromancer. Typical of strategy games.

**Criteria:**
- You control units that are necromancers or have necromancy
- You command a faction with necromantic identity
- The "camera" is above/outside individual characters

**Examples:**
- Total War: WARHAMMER (command Vampire Counts with necromancer units)
- Warcraft III (Undead faction with necromancer units)
- Kingdom Rush Vengeance (place necromancer towers)
- Darkest Dungeon (control a party; Flagellant has necromantic abilities)

**Decision boundary:** If the game has both a character you play and units you control, classify by the PRIMARY relationship. In a game where you ARE a necromancer who also summons minions, it's `character` (you are the necromancer, the minions are your tools). In a game where you command multiple independent necromancer units from above, it's `unit`.

---

## Dimension 3: Naming

**Question answered:** Does the game use the word "necromancer" or "necromancy"?

### Explicit

**Code:** `explicit`
**Label:** Explicit

The terms "necromancer," "necromancy," or "necromantic" appear in the game — in class names, skill descriptions, achievement names, or UI text.

**Examples:**
- "Necromancer" class in Diablo IV
- "Necromancy" skill tree in various games
- "Necromantic" as an adjective in item descriptions

### Implied

**Code:** `implied`
**Label:** Implied

The game has death magic, undead-raising, soul manipulation, or corpse-based abilities, but never uses the word "necromancy." The concept is present but the terminology isn't.

**Examples:**
- "Death magic" or "dark magic" instead of "necromancy"
- Skeleton-raising abilities called "Raise Dead" without the necromancy label
- Soul manipulation called something else

**Decision boundary:** If the game uses ANY of the 'n-word' variants (necromancer, necromancy, necromantic, necro-), it's `explicit`. Only classify `implied` if the concept is clearly necromantic but the terminology is entirely absent.

**Search tip:** When reviewing a game on Steam, Ctrl+F the store description for "necro" — if it shows up, it's `explicit`.

---

## Dimension 4: Availability

**Question answered:** How accessible is the necromantic content?

### Instant

**Code:** `instant`
**Label:** Instant

The necromantic content is available immediately or very early. No significant unlock requirements.

**Criteria:**
- Available from game start (character select, starting class)
- Available within the first ~30 minutes of gameplay
- No DLC or expansion required

### Gated

**Code:** `gated`
**Label:** Gated

The necromantic content requires significant progression, unlocking, or purchase.

**Criteria:**
- Must reach a certain level or chapter to unlock
- Requires a DLC or expansion
- Must complete specific quests or challenges
- Not deterministically available (random unlock, gacha, etc.)

### Unknown

**Code:** `unknown`
**Label:** Unknown

Cannot determine from available information. Default for submissions where the submitter didn't specify.

**Default behavior:** When adding from submission without availability info, use `unknown`. When researching yourself, make a best guess based on game structure.

---

## Priority

Not a classification dimension, but a curation signal. Set when adding a game.

| Priority | Meaning | When to use |
|----------|---------|-------------|
| `high` | Core necromancy game | Tier A centrality, well-known title, active development |
| `medium` | Solid necromancy presence | Tier B or strong Tier C, notable game |
| `low` | Borderline inclusion | Tier D, obscure title, or minimal necromantic content |

**Default:** `high` for tier A, `medium` for B/C, `low` for D. Override based on game prominence and update frequency.

---

## Common Classification Patterns

### Pattern 1: The Necromancer Class Game
- Centrality: `a` (one of the playable classes IS a necromancer)
- POV: `character`
- Naming: `explicit`
- Examples: Diablo IV, Path of Exile, Soulstone Survivors, Hero Siege

### Pattern 2: The Necromancy Skill Tree
- Centrality: `b` (necromancy is a specialization within a broader class system)
- POV: `character`
- Naming: Usually `explicit`
- Examples: Baldur's Gate 3 (Necromancy School), Darksiders II (Necromancer tree)

### Pattern 3: The Strategy/Faction Game
- Centrality: `a` or `b` (necromantic faction is a major option)
- POV: `unit`
- Naming: `explicit` or `implied`
- Examples: Total War: WARHAMMER, Warcraft III, Kingdom Rush Vengeance

### Pattern 4: The Scattered Elements Game
- Centrality: `c`
- POV: Usually `character`
- Naming: Usually `implied`
- Examples: Skul: The Hero Slayer, SWORN, Hell Clock

### Pattern 5: The Lore-Only Game
- Centrality: `d`
- POV: Usually `character`
- Naming: Varies
- Examples: Hades II, Have a Nice Death

---

## The Classification Notes Field

Every game should have `dimension_1_notes` explaining the centrality classification. This is load-bearing — it's how future maintainers understand why a game was classified the way it was.

**Good notes:**
- "Necromancer class with bone/curse/blood skill trees"
- "Grave Digger skull + necromancy inscription item"
- "Unholy spell school with 8+ necromantic spells"
- "Melinoe has necromancy in lore/dialogue but no gameplay mechanics"

**Bad notes:**
- "necromancy"
- "yes"
- (empty)

Additional optional notes fields: `dimension_2_notes`, `dimension_3_notes`, `dimension_4_notes` — use these when the classification needs explanation beyond the obvious.

---

## Necromancy vs. Adjacent Concepts

**NOT necromancy (exclude):**
- Generic "dark magic" without undead or soul themes
- Demon summoning (unless the demons are explicitly raised dead)
- Vampire powers (these go in the Blood registry, not Necromancy)
- Resurrection/revival mechanics that are pure gameplay (respawning, checkpoint revival)
- Ghost themes without corpse-raising or soul command
- Druid animal summoning (unless explicitly framed as necromantic)
- Golem/construct creation (unless made from corpses)

**Borderline — classify conservatively:**
- Spirit/soul manipulation that doesn't involve the dead (classify as necromancy only if there's corpse-raising or explicit "necromancy" naming)
- Zombie games where you fight zombies but don't raise them (NOT necromancy — fighting undead ≠ being a necromancer)
- Games with a "death knight" class (check if they raise dead — if yes, it's necromancy; if it's just death-themed melee, classify as `c` or `d`)
- Science-themed undead (Infectonator 3: classified as tier A "if you consider science undead-raising necromancy" — the notes make it work)

---

*This document is the authoritative reference for necromancy game classification. When in doubt, the notes on existing games in `data/games_list.yaml` are precedent. Review similar games before classifying a new one.*

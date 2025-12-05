# Necro Game News - Project Vision

## Overview
Necro Game News is an automated content platform that tracks, catalogs, and shares updates about games featuring necromancy. The project consists of three main components: an automated game update tracker, a searchable database website, and a social media content pipeline.

## What Makes a Game "Necromantic"?

### Necromancy Taxonomy
Games are evaluated across three dimensions to determine their necromantic relevance:

#### Dimension 1: Necromantic Centrality (Gameplay Integration)
From most to least necromantic:

**a) Core Identity** - Necromancy is central to the unit's identity
- The character class is "Necromancer" or clearly necromantic variant
- First-person games where the main character is a necromancer
- Example: Diablo 2/3/4 Necromancer class

**b) Specialization Available** - Possible to specialize into necromantic skills
- Coherent skill trees or build paths focused on necromancy
- Example: V Rising's Unholy spell category

**c) Isolated Features** - Necromantic skills/artifacts exist but aren't grouped
- Individual necromantic abilities without coherent specialization
- Example: Cult of the Lamb's necromantic weapons and scattered spells

**d) Flavor/Technicality Only** - Necromantic by lore but minimal gameplay impact
- Necromancy exists in story/flavor but barely manifests in mechanics
- Example: Hades 2's Melinoe (necromancy in dialogue/achievements but minimal gameplay), Monster Train 2's Orechi

#### Dimension 2: Point of View (Control Level)
**a) Direct Character Control** - You play AS the necromancer
- ARPGs, first-person games where you control a single necromantic character
- Example: Diablo series, V Rising

**b) Unit Control** - You control/recruit necromantic units among others
- RTS games, tactical games where necromancers are one of many units
- Example: Warcraft 3's Necromancer units, Monster Train 2

#### Dimension 3: Explicit Naming
**a) Explicitly Named** - Referred to as "necromancer" or "necromancy"
- Clear, unambiguous necromantic terminology
- Example: Diablo series, Warcraft 3, Cult of the Lamb

**b) Implied/Thematic** - Necromantic in function but not explicitly labeled
- Death magic, undead summoning without "necromancer" terminology
- Example: V Rising's Unholy spells, Hades 2, Monster Train 2

### Classification System
Games are classified by the **highest criteria satisfied** in each dimension:
- Dimension 1: a > b > c > d
- Dimension 2: Character control > Unit control
- Dimension 3: Explicit > Implied

**Example Classifications:**
- **Diablo 2/3/4**: 1a, 2a, 3a (highest tier)
- **V Rising**: 1b, 2a, 3b
- **Warcraft 3**: 1a, 2b, 3a
- **Cult of the Lamb**: 1c, 2a, 3a
- **Hades 2**: 1d, 2a, 3b
- **Monster Train 2**: 1d, 2b, 3b

## Project Goals

### 1. Automated Update Tracking Pipeline
**Primary Scope:** Steam games
- Track game updates on approximately daily basis
- Distinguish between code changes (patches, updates) and non-code announcements (sales, events)
- Manual curation of games to track
- Future expansion to other platforms possible

**Game Discovery & Curation:**
- Separate automated pipelines to identify candidate necromantic games
- Manual review process for candidates before adding to tracked list
- User submission system feeding into review queue

### 2. Searchable Database Website
**Core Features:**
- Filterable, searchable table interface
- Global and column-specific search
- Multi-column sorting
- Clean, functional design

**Data Strategy:**
- Report game attributes directly from source (Steam) without editorialization
- Add necromancy classification fields:
  - Dimension 1 (Centrality): a/b/c/d
  - Dimension 2 (POV): Character/Unit
  - Dimension 3 (Naming): Explicit/Implied
  - Optional: Justification/notes field
- User and developer submission capability

### 3. Social Media Content Pipeline
**Platforms (Priority Order):**
1. Instagram (primary)
2. YouTube (planned)
3. Additional platforms TBD

**Content Strategy:**
- Auto-generate posts from tracked updates
- Posts auto-publish on schedule
- Optional manual review between scheduling and publication
- Failed/poor posts can be removed without blocking system

## Scale & Scope

**Initial Launch:** Dozens of games
**Growth Target:** Hundreds of games
**Total Steam Library:** ~200-300k games/apps (small necromantic subset)

## Technical Constraints & Preferences

- **Budget:** Start free, up to $50/month acceptable
- **Database:** SQLite or DuckDB (appropriate for scale)
- **Automation:** Local execution with scheduled tasks (cron jobs)
- **Development Environment:** Claude web/desktop for implementation
- **Deployment:** Developer can execute local deployment steps
- **Artifact Demos:** Preferred for initial prototypes

## Success Criteria

**Phase 1 (MVP):**
- Tracking 20+ necromantic games
- Daily automated update checks
- Functional website with search/filter/sort
- Manual social media posting workflow

**Phase 2 (Automation):**
- 50+ games tracked
- Automated social media content generation
- User submission system operational
- Automated game discovery pipeline (keyword-based)

**Phase 3 (Growth):**
- 100+ games tracked
- Multi-platform posting (Instagram + YouTube)
- Community engagement features
- Platform expansion beyond Steam

## Out of Scope (Initial Version)

- Real-time update tracking
- User accounts/authentication on website
- Community voting/rating systems
- Game recommendation algorithm
- Mobile apps
- Monetization features
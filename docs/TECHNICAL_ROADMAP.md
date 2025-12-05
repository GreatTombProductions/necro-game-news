# Necro Game News - Technical Roadmap

**Last Updated:** December 4, 2024
**Current Focus:** Website Enhancement & Content Expansion

---

## What's Live

**Website:** https://necrotic-realms.vercel.app/
**Status:** Fully functional MVP with automated daily updates

### Completed Systems
- ✅ **Core Platform** - React frontend with search/filter/sort, auto-deploy to Vercel
- ✅ **Data Pipeline** - Automated Steam update checking and classification
- ✅ **Social Media** - Instagram content generation (manual posting)
- ✅ **Game Discovery** - Automated batch processing of entire Steam catalog (~149k apps)
- ✅ **Review Workflow** - Interactive CLI for candidate approval

**Current Stats:**
- 8 games actively tracked
- 196+ updates in database
- Automated discovery running (66+ hours to process full catalog)

---

## Current Priorities

### 1. User Submission Form 🎯
**Priority:** HIGH
**Goal:** Let users suggest games without GitHub access

**Tasks:**
- [ ] Design submission form UI (modal or dedicated page)
- [ ] Add form validation (Steam ID/URL, justification text)
- [ ] Set up backend endpoint (consider Formspree, Netlify Forms, or custom API)
- [ ] Wire form to candidates database
- [ ] Add confirmation message/email
- [ ] Document review workflow for submissions

**Why:** Opens the platform to community contributions

---

### 2. Website Improvements 🎯
**Priority:** HIGH
**Goal:** Better UX, more features, professional polish

**Immediate Enhancements:**
- [ ] Advanced filtering UI
  - [ ] Filter by necromancy dimensions (1a/1b/1c/1d, character/unit, explicit/implied)
  - [ ] Filter by genre/tags
  - [ ] Filter by update recency (last 7/30/90 days)
  - [ ] Save filter presets
- [ ] Game detail view
  - [ ] Modal or dedicated page per game
  - [ ] Full update history
  - [ ] Steam tags, screenshots, description
  - [ ] Direct link to Steam store
- [ ] Performance & Polish
  - [ ] Loading states for slow connections
  - [ ] Error boundaries
  - [ ] Virtual scrolling for 100+ games
  - [ ] Mobile table improvements
  - [ ] Accessibility (ARIA labels, keyboard nav)

**Nice to Have:**
- [ ] Dark/light mode toggle
- [ ] Export table to CSV
- [ ] Share individual game updates
- [ ] Update notifications (bell icon)
- [ ] Analytics dashboard (update frequency, game additions over time)

---

### 3. YouTube/Video Content Pipeline 🎯
**Priority:** MEDIUM
**Goal:** Expand to video content for broader reach

**Research Phase:**
- [ ] Explore YouTube API for automated uploads
- [ ] Define video format
  - [ ] Shorts (< 60s) vs. long-form
  - [ ] Weekly roundups vs. per-game updates
  - [ ] Voiceover vs. text overlays
- [ ] Video generation approach
  - [ ] Fully automated (ffmpeg, MoviePy)
  - [ ] Semi-automated (templates + manual editing)
  - [ ] Manual with scripted workflow

**Implementation:**
- [ ] Create video templates
- [ ] Build video generation script (if automated)
- [ ] Set up YouTube channel
- [ ] Create posting workflow
- [ ] Integrate into deploy.sh

**Why:** Video content has higher engagement, YouTube is discovery-friendly

---

## Secondary Priorities

### Game Catalog Expansion
**Goal:** Grow from 8 → 50+ games

- [x] Automated discovery system (COMPLETE - running overnight)
- [ ] Review discovered candidates (use `scripts/review_candidates.py`)
- [ ] Add approved games to games_list.yaml
- [ ] Sync to database with `--update` flag
- [ ] Fetch high-res screenshots for new games
- [ ] Document curation criteria

### Automation & Reliability
**Goal:** Hands-off daily operation

- [ ] Set up cron job for `scripts/deploy.sh` (daily at 2 AM)
- [ ] Add error monitoring/alerting
- [ ] Database backup strategy (S3, Google Drive, or GitHub)
- [ ] Uptime monitoring for website
- [ ] Log aggregation/analysis

### Instagram Enhancement
**Goal:** Automated posting workflow

- [ ] Apply for Instagram API access (requires established account first)
- [ ] Implement Meta Graph API integration
- [ ] Automated posting from queue
- [ ] Post scheduling UI
- [ ] Analytics tracking (engagement, reach)

**Note:** Manual posting is working fine - defer until account is more established

---

## Deferred / Future Ideas

### Multi-Platform Expansion
- Epic Games Store integration
- itch.io integration
- GOG integration
- Discord webhook notifications
- RSS feed of updates
- Email newsletter

### Community Features
- User accounts & profiles
- Game ratings/reviews by users
- Discussion forums
- User-curated collections
- Voting on candidate games

### Advanced Discovery
- Machine learning scoring model
- Review sentiment analysis
- Cross-platform game linking
- Automated classification suggestions

---

## Tech Stack

**Backend:** Python 3.11+, Steam Web API, SQLite
**Frontend:** React + Vite, TanStack Table, Tailwind CSS
**Hosting:** Vercel (auto-deploy on git push)
**Social:** Instagram (manual), YouTube (planned)
**Automation:** Bash scripts + cron

---

## Success Metrics

**Phase 1 (Foundation):** ✅ COMPLETE
- Website live and functional
- 8+ games tracked
- Automated update checking

**Phase 2 (Social Media):** ✅ COMPLETE
- Instagram content generation
- Daily workflow automation
- 4:5 aspect ratio images

**Phase 3 (Discovery):** ✅ MOSTLY COMPLETE
- Automated game discovery running
- Review workflow implemented
- Ready to scale to 50+ games

**Phase 4 (Community & Enhancement):** 🎯 IN PROGRESS
- User submission form
- Website improvements
- Video content pipeline
- 50+ games tracked

---

## Development Philosophy

**Move fast, iterate often:**
- Ship early, gather feedback
- Automate repetitive tasks
- Document as you go
- Keep infrastructure simple

**Quality over features:**
- Professional polish on what exists
- Performance matters
- Accessibility matters
- Mobile experience matters

**Community-driven growth:**
- Listen to user suggestions
- Make contributing easy
- Be transparent about roadmap
- Build in public

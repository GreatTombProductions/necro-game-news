# Necro Game News - Status Summary

**Last Updated:** December 4, 2024
**Current Phase:** Phase 2 COMPLETE, Moving to Phase 3
**Live Site:** https://necrotic-realms.vercel.app/

---

## ✅ What's Live & Working

### Core Platform (Phase 1 - COMPLETE)
- **Website:** Fully functional at https://necrotic-realms.vercel.app/
- **Database:** 8 games tracked, 196+ updates
- **Automation:** Daily update checking via Steam API
- **Deployment:** Auto-deploy to Vercel on git push
- **Search/Filter:** Full-featured table with search, sort, pagination

### Social Media Pipeline (Phase 2 - COMPLETE)
- **Content Generation:** Automated daily Instagram content
- **Image Format:** 4:5 aspect ratio (1080×1350) - Instagram feed optimized
- **Caption Style:** AI-generated summaries, no header fluff
- **Date Filtering:** Ephemeral system - defaults to today's updates only
- **Queue System:** Clears daily, no backlog accumulation
- **Integration:** Built into deploy.sh workflow

---

## 📊 Current Statistics

- **Games Tracked:** 8 active games
- **Total Updates:** 196+
- **Update Types:** patch, announcement, dlc, event, release
- **Daily Workflow:** Fully automated via `./scripts/deploy.sh`
- **Manual Steps:** Instagram posting (API access not yet approved)

---

## 🔄 Daily Workflow

Run `./scripts/deploy.sh` which:
1. Checks for new Steam updates
2. Exports data to JSON for website
3. Generates Instagram posts for today's updates (4:5 images)
4. Exports captions to text files
5. Clears social media queue (ephemeral)
6. Generates weekly report
7. Commits and pushes to GitHub (triggers Vercel deploy)

**Content Output:**
- Images: `content/posts/queue_*.jpg`
- Captions: `content/captions/queue_*.txt`

---

## 🎯 Phase 2 Accomplishments

### Completed Features
✅ Instagram post template with AI caption generation
✅ 4:5 aspect ratio images (Instagram feed optimized)
✅ Date-filtered content generation (ephemeral, not backlog-focused)
✅ High-resolution screenshot support (1920×1080)
✅ Caption export to text files
✅ Integrated social media workflow in deploy.sh
✅ Queue management system
✅ Image compositor with text overlays

### Key Design Decisions
- **Ephemeral Queue:** System clears daily, focuses on recent updates
- **Date Filtering:** Defaults to today, can use `--since YYYY-MM-DD` or `--all`
- **Manual Posting:** Instagram API requires established account for approval
- **4:5 Aspect Ratio:** Instagram's recommended feed format (was 1:1 square)
- **Clean Captions:** Start with AI summary, no header lines

---

## 📝 Key Scripts

### Database Management
```bash
scripts/init_database.py                      # Initialize database
scripts/load_games_from_yaml.py --update      # Sync YAML changes
scripts/view_database.py --stats              # View statistics
```

### Data Collection
```bash
scripts/check_updates.py                      # Check for new updates
scripts/fetch_game_details.py                 # Fetch high-res screenshots
```

### Social Media
```bash
scripts/generate_social_posts.py              # Generate posts (today only)
scripts/generate_social_posts.py --since 2025-12-01  # From specific date
scripts/generate_social_posts.py --all        # All unprocessed (backlog)
scripts/preview_social_posts.py               # Preview/manage queue
scripts/preview_social_posts.py --export-caption  # Export all captions
```

### Complete Workflow
```bash
scripts/deploy.sh                             # Complete daily workflow
```

---

## 🚀 Phase 3 Priorities

### Immediate (Week of Dec 4)
1. **Test deploy.sh workflow end-to-end**
2. **Start manual Instagram posting** (build audience)
3. **Document posting workflow** (for consistency)

### Short Term (Weeks 1-2)
1. **Set up cron automation** for daily deploy.sh
2. **Expand game list** to 20-30 games
3. **Refine content strategy** based on engagement

### Medium Term (Weeks 3-6)
1. **Expand to 50+ games**
2. **Add user submission form** to website
3. **Apply for Instagram API access** (requires established account)
4. **Advanced website filtering** (by dimension, genre, etc.)

### Deferred
- **Instagram API Automation** (Phase 2.3) - Manual workflow is sufficient
- **Multi-platform expansion** (YouTube, TikTok)
- **Automated game discovery**

---

## 🎨 Necromancy Classification

Games evaluated across 3 dimensions:

**Dimension 1: Centrality**
- a) Core Identity - Necromancer class/protagonist
- b) Specialization - Necromantic skill tree
- c) Isolated Features - Necromancy items/skills
- d) Flavor Only - Lore only

**Dimension 2: Point of View**
- a) Play AS necromancer
- b) Control necromancer units

**Dimension 3: Naming**
- a) Explicit "necromancer/necromancy"
- b) Implied/thematic

---

## 🔧 Tech Stack

**Backend:** Python 3.11+, Steam Web API, SQLite
**Frontend:** React + Vite, TanStack Table, Tailwind CSS
**Hosting:** Vercel (auto-deploy on push)
**Social:** Instagram (manual posting, API pending)
**Automation:** Local scripts + deploy.sh

---

## 📈 Success Metrics

**Phase 1 Goals:** ALL ACHIEVED ✅
- ✅ Website deployed and functional
- ✅ 8+ games tracked
- ✅ Daily update checking
- ✅ Search/filter/sort working

**Phase 2 Goals:** ALL ACHIEVED ✅
- ✅ Instagram content pipeline
- ✅ Automated generation workflow
- ✅ 4:5 aspect ratio images
- ✅ AI-generated captions
- ✅ Ephemeral queue system

**Phase 3 Goals:** IN PROGRESS
- [ ] 50+ games tracked
- [ ] Cron automation running
- [ ] Instagram posting regular
- [ ] User submissions functional

---

## 💡 Recent Changes (Dec 4, 2024)

### Instagram Content Refinements
1. **Caption Template:** Removed header lines, starts with AI summary
2. **Image Aspect Ratio:** Changed from 1:1 (square) to 4:5 (portrait)
3. **Date Filtering:** Added `--since` flag, defaults to today
4. **Ephemeral Queue:** Clears daily, no accumulation
5. **Deploy Integration:** Social media steps added to deploy.sh

### New Flags & Options
- `generate_social_posts.py --since YYYY-MM-DD` - From specific date
- `generate_social_posts.py --all` - All unprocessed updates
- Default behavior now: only today's updates

---

## 📚 Documentation

- [PROGRESS.md](PROGRESS.md) - Detailed progress tracker
- [TECHNICAL_ROADMAP.md](TECHNICAL_ROADMAP.md) - Phased implementation plan
- [SOCIAL_MEDIA_WORKFLOW.md](SOCIAL_MEDIA_WORKFLOW.md) - Instagram workflow guide
- [README.md](../README.md) - Main project overview
- [CLAUDE.md](../CLAUDE.md) - Quick reference for Claude Code

---

## 🎯 Next Action Items

1. **Today:** Test complete deploy.sh workflow
2. **This Week:** Start posting Instagram content manually
3. **Next Week:** Set up cron for daily automation
4. **Within 2 Weeks:** Expand game list to 20-30 games
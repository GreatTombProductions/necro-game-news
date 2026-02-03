# Automation Setup for Scheduled Deploys

This directory contains scripts for automating necro-game-news deployments via macOS launchd.

## Schedule

- **Daily (12:00 PM)**: Full deployment
  - Checks for game updates from Steam/Battle.net
  - Exports database to JSON
  - Generates social media content
  - Pushes to GitHub (triggers Vercel deploy)

- **Weekly (Friday 6:00 PM)**: Metadata refresh deployment
  - Refreshes game metadata from Steam API
  - Checks for updates
  - Exports and deploys

## Installation (launchd - Recommended)

launchd is Apple's native scheduler and works reliably even when the Mac wakes from sleep.

1. **Verify the scripts work manually:**
   ```bash
   cd /Users/rayheberer/Documents/greattomb/community-tools/necro-game-news
   ./scripts/cron_deploy.sh full    # Test full deployment
   ./scripts/cron_deploy.sh refresh  # Test refresh deployment
   ```

2. **Symlink the plist files to LaunchAgents:**
   ```bash
   ln -sf /Users/rayheberer/Documents/greattomb/community-tools/necro-game-news/scripts/launchd/com.greattomb.necrogamenews.daily.plist ~/Library/LaunchAgents/
   ln -sf /Users/rayheberer/Documents/greattomb/community-tools/necro-game-news/scripts/launchd/com.greattomb.necrogamenews.weekly.plist ~/Library/LaunchAgents/
   ```

3. **Load the agents:**
   ```bash
   launchctl load ~/Library/LaunchAgents/com.greattomb.necrogamenews.daily.plist
   launchctl load ~/Library/LaunchAgents/com.greattomb.necrogamenews.weekly.plist
   ```

4. **Verify installation:**
   ```bash
   launchctl list | grep necro
   ```

## Files

- **[cron_deploy.sh](cron_deploy.sh)**: Wrapper script that handles logging and calls deploy.sh
- **[launchd/](launchd/)**: launchd plist files for daily and weekly schedules
- **[crontab.txt](crontab.txt)**: (Deprecated) Cron schedule template

## Logs

- Main logs: `logs/cron/deploy_{mode}_{timestamp}.log`
- launchd stdout/stderr: `logs/launchd/daily.out.log`, `logs/launchd/weekly.out.log`
- Retention: Automatically deletes logs older than 30 days

## Manual Runs

```bash
# Full deployment (same as daily schedule)
./scripts/cron_deploy.sh full

# Metadata refresh (same as weekly schedule)
./scripts/cron_deploy.sh refresh

# Check recent logs
ls -lt logs/cron/
tail -f logs/cron/deploy_full_*.log  # Follow latest full deploy log
```

## Managing launchd Agents

```bash
# Check status
launchctl list | grep necro

# Unload (stop scheduling)
launchctl unload ~/Library/LaunchAgents/com.greattomb.necrogamenews.daily.plist

# Reload after changes
launchctl unload ~/Library/LaunchAgents/com.greattomb.necrogamenews.daily.plist
launchctl load ~/Library/LaunchAgents/com.greattomb.necrogamenews.daily.plist

# Run immediately (for testing)
launchctl start com.greattomb.necrogamenews.daily
```

## Troubleshooting

**Agent not running?**
- Check it's loaded: `launchctl list | grep necro`
- Check launchd logs: `logs/launchd/daily.err.log`
- Ensure scripts are executable: `ls -l scripts/cron_deploy.sh`

**Deployment failures?**
- Check latest log in `logs/cron/`
- Verify .env file has required API keys
- Test manual run: `./scripts/deploy.sh --full`

## Why launchd instead of cron?

macOS requires Full Disk Access for cron to run scripts, which causes "Operation not permitted" errors. launchd is Apple's native solution and works without these security restrictions.

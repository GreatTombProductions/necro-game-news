# Cron Setup for Automated Deploys

This directory contains scripts for automating necro-game-news deployments via cron.

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

## Installation

1. **Verify the scripts work manually:**
   ```bash
   cd /Users/rayheberer/Documents/greattomb/necro-game-news
   ./scripts/cron_deploy.sh full    # Test full deployment
   ./scripts/cron_deploy.sh refresh  # Test refresh deployment
   ```

2. **Add to crontab:**
   ```bash
   crontab -e
   ```

   Then paste the contents of `crontab.txt` (or just the two cron lines).

3. **Verify installation:**
   ```bash
   crontab -l  # List current cron jobs
   ```

## Files

- **[cron_deploy.sh](cron_deploy.sh)**: Wrapper script that handles logging and calls deploy.sh
- **[crontab.txt](crontab.txt)**: Cron schedule template (copy/paste into `crontab -e`)

## Logs

- Location: `/Users/rayheberer/Documents/greattomb/necro-game-news/logs/cron/`
- Format: `deploy_{mode}_{timestamp}.log`
- Retention: Automatically deletes logs older than 30 days

## Manual Runs

You can manually trigger deployments anytime:

```bash
# Full deployment (same as daily cron)
./scripts/cron_deploy.sh full

# Metadata refresh (same as weekly cron)
./scripts/cron_deploy.sh refresh

# Check recent logs
ls -lt logs/cron/
tail -f logs/cron/deploy_full_*.log  # Follow latest full deploy log
```

## Troubleshooting

**Cron not running?**
- Check cron is enabled: `sudo launchctl list | grep cron`
- Check system logs: `grep CRON /var/log/system.log`
- Ensure scripts are executable: `ls -l scripts/cron_deploy.sh`

**Deployment failures?**
- Check latest log in `logs/cron/`
- Verify .env file has required API keys
- Test manual run: `./scripts/deploy.sh --full`

**Missing logs?**
- Logs directory auto-created on first run
- Check script has write permissions: `ls -ld logs/cron/`

## Customization

To change schedule, edit the cron times in your crontab:

```bash
# Cron format: MIN HOUR DAY MONTH WEEKDAY COMMAND
# Examples:
0 8 * * *    # Daily at 8 AM
0 0 * * 0    # Weekly on Sundays at midnight
0 */6 * * *  # Every 6 hours
```

Then run:
```bash
crontab -e  # Edit
crontab -l  # Verify changes
```

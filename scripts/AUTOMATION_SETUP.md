# Automation Setup for Scheduled Deploys

Daily game data updates run via the greattomb central-heartbeat system.

## Current Mechanism

**[heartbeat-deploy.sh](heartbeat-deploy.sh)** is invoked by `central-heartbeat` on the schedule defined in `schedule.yaml`. It:

1. Syncs game lists from YAML sources
2. Checks for game updates from Steam/Battle.net
3. Exports database to JSON
4. Commits and pushes to GitHub (triggers Vercel deploy)

Weekly (Friday 18:00): also refreshes all game metadata from Steam API.

## Manual Runs

```bash
cd /home/ray/greattomb/community-tools/necro-game-news
./scripts/heartbeat-deploy.sh
```

## Logs

- Heartbeat logs: `logs/heartbeat/daily.out.log`, `logs/heartbeat/daily.err.log`

## Troubleshooting

**Deployment failures?**
- Check latest heartbeat log: `tail logs/heartbeat/daily.out.log`
- Verify .env file has required API keys
- Verify venv exists: `ls venv/bin/python`

## Superseded Files

The following files are from a previous macOS launchd-based automation setup and are no longer active:

- `crontab.txt` — macOS cron schedule template
- `install_crontab.sh` — crontab installer
- `cron_deploy.sh` — wrapper for the old deploy mechanism
- `launchd/` — macOS launchd plist files

These remain for reference but are not used since the Linux migration (April 2026).

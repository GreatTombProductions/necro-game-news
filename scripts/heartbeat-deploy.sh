#!/bin/bash
#
# Necro Game News -- daily data update + deploy
# Invoked by central-heartbeat via schedule.yaml (or manually)
# Updates-only: syncs YAML, checks for game updates, exports JSON, pushes to GitHub (triggers Vercel)
# Does NOT generate social media content
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Self-managed logging
LOG_DIR="$PROJECT_ROOT/logs/heartbeat"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/daily.out.log"
ERR_FILE="$LOG_DIR/daily.err.log"
exec >> "$LOG_FILE" 2>> "$ERR_FILE"

echo "=== $(date -Iseconds) Necro Game News heartbeat deploy ==="

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

PYTHON="./venv/bin/python"

if [ ! -f "$PYTHON" ]; then
    echo "ERROR: Virtual environment not found at $PYTHON"
    exit 1
fi

# Friday 18:00 tick includes a full metadata refresh from Steam
if [[ "$HEARTBEAT_REASON" == *"18:00"* ]]; then
    echo "--- Refreshing all game metadata from Steam (weekly) ---"
    $PYTHON scripts/fetch_game_details.py
fi

echo "--- Syncing game lists from YAML ---"
$PYTHON scripts/load_games_from_yaml.py --update --sync
$PYTHON scripts/load_games_from_yaml.py --blood --update

echo "--- Checking for game updates ---"
$PYTHON scripts/check_updates.py

echo "--- Exporting data for web ---"
$PYTHON scripts/export_for_web.py

echo "--- Committing and pushing ---"
git add frontend/public/data/*.json
git commit -m "Update game data: $(date +%Y-%m-%d)" || echo "No changes to commit"
git push origin main || echo "Push failed (offline or auth issue)"

echo "=== Done ==="

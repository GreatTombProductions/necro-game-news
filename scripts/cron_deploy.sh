#!/bin/bash
# Cron wrapper for necro-game-news deployments
# Usage: ./cron_deploy.sh [full|refresh]

set -e

# Get project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOGS_DIR="$PROJECT_ROOT/logs/cron"

# Create logs directory if it doesn't exist
mkdir -p "$LOGS_DIR"

# Deployment mode (full or refresh)
MODE="${1:-full}"

# Log file with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOGS_DIR/deploy_${MODE}_${TIMESTAMP}.log"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Start deployment
log "========================================"
log "Starting ${MODE} deployment"
log "========================================"

cd "$PROJECT_ROOT"

# Run the appropriate deploy command
if [ "$MODE" = "full" ]; then
    log "Running full deployment (updates + export + social + deploy)"
    "$SCRIPT_DIR/deploy.sh" --full >> "$LOG_FILE" 2>&1
elif [ "$MODE" = "refresh" ]; then
    log "Running refresh deployment (refresh metadata + updates + deploy)"
    "$SCRIPT_DIR/deploy.sh" --refresh-data >> "$LOG_FILE" 2>&1
else
    log "ERROR: Unknown mode '$MODE'. Use 'full' or 'refresh'"
    exit 1
fi

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    log "✅ Deployment completed successfully"
else
    log "❌ Deployment failed with exit code $EXIT_CODE"
    log "Check log file for details: $LOG_FILE"
fi

log "========================================"
log "Log saved to: $LOG_FILE"

# Keep only last 30 days of logs
find "$LOGS_DIR" -name "*.log" -mtime +30 -delete 2>/dev/null || true

exit $EXIT_CODE

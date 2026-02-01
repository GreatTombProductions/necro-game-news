#!/bin/bash
# Install necro-game-news cron jobs
# This script merges new cron entries with existing crontab

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Installing necro-game-news cron jobs..."
echo ""

# Save current crontab (if any)
TMP_CRONTAB=$(mktemp)
crontab -l > "$TMP_CRONTAB" 2>/dev/null || echo "# Crontab for $(whoami)" > "$TMP_CRONTAB"

# Check if entries already exist
if grep -q "necro-game-news/scripts/cron_deploy.sh" "$TMP_CRONTAB"; then
    echo "⚠️  Necro Game News cron jobs already exist in crontab!"
    echo ""
    echo "Current entries:"
    grep "necro-game-news" "$TMP_CRONTAB"
    echo ""
    read -p "Remove existing entries and reinstall? (y/N) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Remove old entries
        grep -v "necro-game-news" "$TMP_CRONTAB" > "${TMP_CRONTAB}.new"
        mv "${TMP_CRONTAB}.new" "$TMP_CRONTAB"
    else
        echo "Installation cancelled."
        rm "$TMP_CRONTAB"
        exit 0
    fi
fi

# Append new entries
cat >> "$TMP_CRONTAB" << EOF

# ============================================
# Necro Game News Automated Deployments
# ============================================
# Daily full deploy at 12:00 PM (noon)
0 12 * * * $PROJECT_ROOT/scripts/cron_deploy.sh full

# Weekly metadata refresh on Fridays at 6:00 PM
0 18 * * 5 $PROJECT_ROOT/scripts/cron_deploy.sh refresh
EOF

# Install the new crontab
crontab "$TMP_CRONTAB"

# Clean up
rm "$TMP_CRONTAB"

echo ""
echo "✅ Cron jobs installed successfully!"
echo ""
echo "Installed schedule:"
echo "  • Daily at 12:00 PM - Full deploy"
echo "  • Friday at 6:00 PM - Metadata refresh"
echo ""
echo "To verify:"
echo "  crontab -l"
echo ""
echo "Logs will be saved to:"
echo "  $PROJECT_ROOT/logs/cron/"

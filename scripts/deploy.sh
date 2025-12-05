#!/bin/bash
# Quick deploy script for Necro Game News

set -e  # Exit on error

# Use the virtual environment's Python directly
PYTHON="./venv/bin/python"

# Check if venv exists
if [ ! -f "$PYTHON" ]; then
    echo "❌ Virtual environment not found at $PYTHON"
    echo "Please create it with: python3 -m venv venv"
    exit 1
fi

echo "🔍 Checking for updates..."
$PYTHON scripts/check_updates.py

echo "📤 Exporting data for web..."
$PYTHON scripts/export_for_web.py

echo "📊 Generating report..."
$PYTHON scripts/generate_report.py --days 7

echo "📝 Committing changes..."
git add frontend/public/data/*.json
git commit -m "Update game data: $(date +%Y-%m-%d)" || echo "No changes to commit"

echo "🚀 Pushing to GitHub (will trigger Vercel deploy)..."
git push origin main

echo "✅ Deployment complete!"
echo "🌐 Check status at: https://necrotic-realms.vercel.app/"
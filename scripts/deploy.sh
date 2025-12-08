#!/bin/bash
# Deployment script for Necro Game News with interactive options

set -e  # Exit on error

# Get project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root to ensure relative paths work
cd "$PROJECT_ROOT"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Use the virtual environment's Python directly
PYTHON="./venv/bin/python"

# Check if venv exists
if [ ! -f "$PYTHON" ]; then
    echo "❌ Virtual environment not found at $PYTHON"
    echo "Please create it with: python3.9 -m venv venv"
    exit 1
fi

# Use DATABASE_PATH from .env or default
DB_PATH="${DATABASE_PATH:-data/necro_games.db}"

# Parse command line arguments
MODE=""
REPROCESS=""
REFRESH_DATA=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --full)
            MODE="full"
            shift
            ;;
        --updates-only)
            MODE="updates"
            shift
            ;;
        --new-only)
            MODE="new"
            shift
            ;;
        --content-only)
            MODE="content"
            shift
            ;;
        --reprocess)
            REPROCESS="--reprocess"
            shift
            ;;
        --refresh-data)
            REFRESH_DATA="yes"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--full|--updates-only|--new-only|--content-only] [--reprocess] [--refresh-data]"
            exit 1
            ;;
    esac
done

# Interactive menu if no mode specified
if [ -z "$MODE" ]; then
    echo "=================================================="
    echo "Necro Game News - Deployment Options"
    echo "=================================================="
    echo ""
    echo "Choose deployment mode:"
    echo ""
    echo "  1) Full Deploy"
    echo "     - Check for Steam updates"
    echo "     - Export data for web"
    echo "     - Generate social media content"
    echo "     - Create weekly report"
    echo "     - Commit & deploy to Vercel"
    echo ""
    echo "  2) Updates + Deploy (skip social content)"
    echo "     - Check for Steam updates"
    echo "     - Export data for web"
    echo "     - Create weekly report"
    echo "     - Commit & deploy to Vercel"
    echo ""
    echo "  3) New Games Only + Deploy"
    echo "     - Load newly added games from YAML"
    echo "     - Skip update checking for existing games"
    echo "     - Export data for web"
    echo "     - Create weekly report"
    echo "     - Commit & deploy to Vercel"
    echo ""
    echo "  4) Social Content Only"
    echo "     - Generate social media content"
    echo "     - (no git commit/deploy)"
    echo ""
    echo -n "Enter choice [1-4]: "
    read -r choice

    case $choice in
        1)
            MODE="full"
            ;;
        2)
            MODE="updates"
            ;;
        3)
            MODE="new"
            ;;
        4)
            MODE="content"
            ;;
        *)
            echo "Invalid choice. Exiting."
            exit 1
            ;;
    esac

    # Ask about reprocessing if generating content
    if [ "$MODE" = "full" ] || [ "$MODE" = "content" ]; then
        echo ""
        echo -n "Reprocess already-processed updates? [y/N]: "
        read -r reprocess_choice
        if [ "$reprocess_choice" = "y" ] || [ "$reprocess_choice" = "Y" ]; then
            REPROCESS="--reprocess"
        fi
    fi

    # Ask about refreshing game data
    if [ "$MODE" = "full" ] || [ "$MODE" = "updates" ]; then
        echo ""
        echo -n "Refresh all game data from Steam (genres, descriptions, etc.)? [y/N]: "
        read -r refresh_choice
        if [ "$refresh_choice" = "y" ] || [ "$refresh_choice" = "Y" ]; then
            REFRESH_DATA="yes"
        fi
    fi

    echo ""
fi

echo "=================================================="
echo "Starting deployment: $MODE"
if [ -n "$REPROCESS" ]; then
    echo "Mode: Reprocessing enabled"
fi
if [ -n "$REFRESH_DATA" ]; then
    echo "Mode: Refresh game data enabled"
fi
echo "=================================================="
echo ""

# Refresh all game data if requested (runs before main flow)
if [ -n "$REFRESH_DATA" ]; then
    echo "🔄 Refreshing all game data from Steam..."
    $PYTHON scripts/fetch_game_details.py
    echo ""
fi

# Execute based on mode
case $MODE in
    full)
        echo "🔍 Checking for updates..."
        $PYTHON scripts/load_games_from_yaml.py --update --sync
        $PYTHON scripts/check_updates.py

        echo ""
        echo "📤 Exporting data for web..."
        $PYTHON scripts/export_for_web.py

        echo ""
        echo "📱 Generating social media content..."
        $PYTHON scripts/generate_social_content.py $REPROCESS

        echo ""
        echo "📊 Generating report..."
        $PYTHON scripts/generate_report.py --days 7

        echo ""
        echo "📝 Committing changes..."
        git add frontend/public/data/*.json
        git commit -m "Update game data: $(date +%Y-%m-%d)" || echo "No changes to commit"

        echo ""
        echo "🚀 Pushing to GitHub (will trigger Vercel deploy)..."
        git push origin main

        echo ""
        echo "✅ Full deployment complete!"
        ;;

    updates)
        echo "🔍 Checking for updates..."
        $PYTHON scripts/load_games_from_yaml.py --update --sync
        $PYTHON scripts/check_updates.py

        echo ""
        echo "📤 Exporting data for web..."
        $PYTHON scripts/export_for_web.py

        echo ""
        echo "📊 Generating report..."
        $PYTHON scripts/generate_report.py --days 7

        echo ""
        echo "📝 Committing changes..."
        git add frontend/public/data/*.json
        git commit -m "Update game data: $(date +%Y-%m-%d)" || echo "No changes to commit"

        echo ""
        echo "🚀 Pushing to GitHub (will trigger Vercel deploy)..."
        git push origin main

        echo ""
        echo "✅ Updates deployment complete!"
        echo "💡 Remember to generate social content separately if needed"
        ;;

    new)
        echo "🆕 Loading new games from YAML..."
        $PYTHON scripts/load_games_from_yaml.py --update --sync
        echo "   (Skipping update check for existing games)"

        echo ""
        echo "📤 Exporting data for web..."
        $PYTHON scripts/export_for_web.py

        echo ""
        echo "📊 Generating report..."
        $PYTHON scripts/generate_report.py --days 7

        echo ""
        echo "📝 Committing changes..."
        git add frontend/public/data/*.json
        git commit -m "Update game data: $(date +%Y-%m-%d)" || echo "No changes to commit"

        echo ""
        echo "🚀 Pushing to GitHub (will trigger Vercel deploy)..."
        git push origin main

        echo ""
        echo "✅ New games deployment complete!"
        echo "💡 Run --full or --updates-only later to check for updates on all games"
        ;;

    content)
        echo "📱 Generating social media content..."
        $PYTHON scripts/generate_social_content.py $REPROCESS

        echo ""
        echo "✅ Social content generation complete!"
        echo "📁 Check content/posts/ and content/captions/ for generated files"
        ;;
esac

echo ""
echo "🌐 Website: https://necroticrealms.com/"

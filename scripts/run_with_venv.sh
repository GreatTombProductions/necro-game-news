#!/bin/bash
# Helper script to run Python scripts with the virtual environment
# Usage: ./scripts/run_with_venv.sh scripts/check_updates.py

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PYTHON="$PROJECT_ROOT/venv/bin/python"

# Check if venv exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ Virtual environment not found at $VENV_PYTHON"
    echo "Please create it with: python3.9 -m venv venv"
    exit 1
fi

# Run the script with venv Python
exec "$VENV_PYTHON" "$@"

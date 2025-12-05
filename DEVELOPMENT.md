# Development Guide

## Python Environment Setup

This project uses Python 3.9+ with a virtual environment to ensure consistent dependencies.

### Initial Setup

```bash
# Create virtual environment (one-time setup)
python3.9 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

### Daily Usage

**IMPORTANT:** Always activate the virtual environment before running scripts:

```bash
# Activate venv
source venv/bin/activate

# Now run any script
python scripts/check_updates.py
python scripts/review_candidates.py
```

### Running Scripts Without Activating venv

If you prefer not to activate venv manually, you can:

1. **Use the helper script:**
   ```bash
   ./scripts/run_with_venv.sh scripts/check_updates.py
   ```

2. **Use venv Python directly:**
   ```bash
   ./venv/bin/python scripts/check_updates.py
   ```

3. **Use deploy.sh** (automatically uses venv):
   ```bash
   ./scripts/deploy.sh
   ```

### Why This Matters

- **System Python:** `/usr/local/bin/python3` (3.13.7)
- **venv Python:** `./venv/bin/python` (3.9.6)

The project dependencies are installed in the venv, not system-wide. Running scripts with system Python will fail due to missing packages.

### Verifying Your Environment

```bash
# Check which Python you're using
which python
# Should show: /path/to/necro-game-news/venv/bin/python

# Check Python version
python --version
# Should show: Python 3.9.6 (or whichever version venv uses)
```

### Troubleshooting

**Problem:** `ModuleNotFoundError` when running scripts

**Solution:** Make sure you've activated the venv:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Problem:** Scripts use wrong Python version

**Solution:** Use `./venv/bin/python` directly or activate venv first.

---

## Database Configuration

Database path is configured in `.env`:

```bash
DATABASE_PATH=data/necro_games.db
```

All scripts automatically use this path. The database is created in the `data/` directory relative to the project root.

---

## Running Background Tasks

For long-running tasks (like batch discovery), use the venv Python directly:

```bash
./venv/bin/python scripts/batch_discover.py --discover --yes &
```

Or use the helper:

```bash
nohup ./scripts/run_with_venv.sh scripts/batch_discover.py --discover --yes > logs/discovery.log 2>&1 &
```

---

## Deploy Script

The `deploy.sh` script handles everything automatically:

- ✅ Uses venv Python
- ✅ Loads `.env` variables
- ✅ Runs from project root
- ✅ All paths are relative

Just run:

```bash
./scripts/deploy.sh
```

No need to activate venv manually!

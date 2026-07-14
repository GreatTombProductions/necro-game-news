#!/usr/bin/env python3
"""
Add Game to YAML — Validated game addition to the Necromancy Registry.

Adds a game entry to games_list.yaml (or blood_games_list.yaml), validates
all required fields, inserts in alphabetical order, and syncs to the database.

This is the script that actually writes to the canonical YAML files. It's
called after review_game.py generates a classification that Ray approves.

Usage:
  # Add a necromancy game
  ./venv/bin/python scripts/add_game_to_yaml.py \\
      --name "Mewgenics" \\
      --steam-id 1234567 \\
      --dim1 b --dim2 unit --dim3 explicit --dim4 gated \\
      --notes "Necromancer class in the game" \\
      --priority high

  # Add a blood registry game
  ./venv/bin/python scripts/add_game_to_yaml.py \\
      --blood \\
      --name "V Rising" \\
      --steam-id 1604030 \\
      --vampirism outright --hemomancy a --pov character \\
      --availability instant \\
      --priority high \\
      --notes "Play as a vampire building your dark empire"

  # Dry-run (validate only, don't write)
  ./venv/bin/python scripts/add_game_to_yaml.py --dry-run --name "Test" --steam-id 9999 --dim1 a --dim2 character --dim3 explicit

  # Deploy after adding
  ./venv/bin/python scripts/add_game_to_yaml.py ... --deploy
"""

import sys
import argparse
from pathlib import Path
from datetime import date
from typing import Optional

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GAMES_YAML_PATH = PROJECT_ROOT / "data" / "games_list.yaml"
BLOOD_YAML_PATH = PROJECT_ROOT / "data" / "blood_games_list.yaml"
SUBMISSIONS_DIR = PROJECT_ROOT / "data" / "submissions"

VALID_DIM1 = {"a", "b", "c", "d"}
VALID_DIM2 = {"character", "unit"}
VALID_DIM3 = {"explicit", "implied"}
VALID_DIM4 = {"instant", "gated", "unknown"}
VALID_PRIORITY = {"high", "medium", "low"}
VALID_VAMPIRISM = {"outright", "implied", "channeled", "absent"}
VALID_HEMOMANCY = {"a", "b", "c", "d", "absent"}


def load_yaml(path: Path) -> dict:
    """Load a YAML file, returning {'games': []} if empty or missing."""
    if not path.exists():
        return {"games": []}
    with open(path) as f:
        data = yaml.safe_load(f)
    if data is None:
        return {"games": []}
    if "games" not in data:
        data["games"] = []
    return data


def save_yaml(data: dict, path: Path) -> None:
    """Save to YAML with consistent formatting."""
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def find_by_steam_id(games: list, steam_id: int) -> tuple[Optional[dict], Optional[int]]:
    """Find a game by steam_id. Returns (game_dict, index) or (None, None)."""
    for i, game in enumerate(games):
        if game.get("steam_id") == steam_id:
            return game, i
    return None, None


def build_entry_necromancy(args) -> dict:
    """Build a necromancy registry game entry."""
    entry = {
        "name": args.name,
        "steam_id": args.steam_id,
        "classification": {
            "dimension_1": args.dim1,
            "dimension_2": args.dim2,
            "dimension_3": args.dim3,
            "dimension_4": args.dim4 or "unknown",
        },
        "priority": args.priority or "medium",
        "date_updated": date.today().isoformat(),
    }

    if args.notes:
        entry["dimension_1_notes"] = args.notes
    if args.aliases:
        entry["aliases"] = [a.strip() for a in args.aliases.split(",")]

    return entry


def build_entry_blood(args) -> dict:
    """Build a blood registry game entry."""
    entry = {
        "name": args.name,
        "steam_id": args.steam_id,
        "classification": {
            "vampirism": args.vampirism,
            "hemomancy": args.hemomancy,
            "pov": args.pov,
            "availability": args.availability or "unknown",
        },
        "priority": args.priority or "medium",
        "date_updated": date.today().isoformat(),
    }

    if args.notes:
        entry["vampirism_notes"] = args.notes
    if args.aliases:
        entry["aliases"] = [a.strip() for a in args.aliases.split(",")]

    return entry


def insert_alphabetical(games: list, entry: dict) -> list:
    """Insert a game entry into the list, maintaining alphabetical order by name."""
    entry_name_lower = entry["name"].lower()
    for i, game in enumerate(games):
        if game["name"].lower() > entry_name_lower:
            games.insert(i, entry)
            return games
    games.append(entry)
    return games


def validate_necromancy(args) -> list[str]:
    """Validate necromancy classification fields. Returns list of error messages."""
    errors = []

    if not args.name:
        errors.append("--name is required")
    if not args.steam_id:
        errors.append("--steam-id is required")

    if args.dim1 not in VALID_DIM1:
        errors.append(f"--dim1 must be one of {VALID_DIM1}, got '{args.dim1}'")
    if args.dim2 not in VALID_DIM2:
        errors.append(f"--dim2 must be one of {VALID_DIM2}, got '{args.dim2}'")
    if args.dim3 not in VALID_DIM3:
        errors.append(f"--dim3 must be one of {VALID_DIM3}, got '{args.dim3}'")
    if args.dim4 and args.dim4 not in VALID_DIM4:
        errors.append(f"--dim4 must be one of {VALID_DIM4}, got '{args.dim4}'")
    if args.priority and args.priority not in VALID_PRIORITY:
        errors.append(f"--priority must be one of {VALID_PRIORITY}, got '{args.priority}'")

    return errors


def validate_blood(args) -> list[str]:
    """Validate blood registry classification fields."""
    errors = []

    if not args.name:
        errors.append("--name is required")
    if not args.steam_id:
        errors.append("--steam-id is required")

    if args.vampirism not in VALID_VAMPIRISM:
        errors.append(f"--vampirism must be one of {VALID_VAMPIRISM}, got '{args.vampirism}'")
    if args.hemomancy not in VALID_HEMOMANCY:
        errors.append(f"--hemomancy must be one of {VALID_HEMOMANCY}, got '{args.hemomancy}'")
    if args.pov not in VALID_DIM2:
        errors.append(f"--pov must be one of {VALID_DIM2}, got '{args.pov}'")
    if args.availability and args.availability not in VALID_DIM4:
        errors.append(f"--availability must be one of {VALID_DIM4}, got '{args.availability}'")
    if args.priority and args.priority not in VALID_PRIORITY:
        errors.append(f"--priority must be one of {VALID_PRIORITY}, got '{args.priority}'")

    return errors


def sync_to_database():
    """Sync YAML changes to the SQLite database."""
    import subprocess
    venv_python = str(PROJECT_ROOT / "venv" / "bin" / "python")
    load_script = str(PROJECT_ROOT / "scripts" / "load_games_from_yaml.py")

    try:
        result = subprocess.run(
            [venv_python, load_script, "--update", "--sync"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            print(f"WARNING: Database sync had errors:\n{result.stderr}", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"WARNING: Database sync failed: {e}", file=sys.stderr)
        return False


def deploy():
    """Export for web and push to trigger Vercel deploy."""
    import subprocess
    venv_python = str(PROJECT_ROOT / "venv" / "bin" / "python")
    export_script = str(PROJECT_ROOT / "scripts" / "export_for_web.py")

    print("Exporting data for web...")
    try:
        subprocess.run([venv_python, export_script], cwd=str(PROJECT_ROOT), check=True, timeout=30)
    except Exception as e:
        print(f"ERROR: Export failed: {e}", file=sys.stderr)
        return False

    print("Committing and pushing...")
    try:
        subprocess.run(
            ["git", "add", "data/games_list.yaml", "data/blood_games_list.yaml",
             "frontend/public/data/necro_games.json", "frontend/public/data/blood_games.json"],
            cwd=str(PROJECT_ROOT), check=True
        )
        subprocess.run(
            ["git", "commit", "-m", f"Add {date.today().isoformat()} game registry update"],
            cwd=str(PROJECT_ROOT), check=False  # May fail if nothing to commit
        )
        subprocess.run(["git", "push", "origin", "main"], cwd=str(PROJECT_ROOT), check=True)
    except Exception as e:
        print(f"ERROR: Git push failed: {e}", file=sys.stderr)
        return False

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Add a game to the Necromancy or Blood Registry YAML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Necromancy registry
  %(prog)s --name "Mewgenics" --steam-id 1234567 --dim1 b --dim2 unit --dim3 explicit --dim4 gated --notes "Necromancer class"

  # Blood registry
  %(prog)s --blood --name "V Rising" --steam-id 1604030 --vampirism outright --hemomancy a --pov character --availability instant

  # Dry run (validate only)
  %(prog)s --dry-run --name "Test" --steam-id 9999 --dim1 a --dim2 character --dim3 explicit
        """
    )

    # Game identification
    parser.add_argument("--name", type=str, required=True, help="Game name (exact Steam title)")
    parser.add_argument("--steam-id", type=int, required=True, help="Steam App ID")
    parser.add_argument("--aliases", type=str, help="Comma-separated aliases (e.g. 'D4,Diablo 4')")

    # Registry selection
    parser.add_argument("--blood", action="store_true", help="Add to blood registry instead of necromancy")

    # Necromancy classification
    parser.add_argument("--dim1", type=str, choices=list(VALID_DIM1), help="Centrality: a=Core, b=Branch, c=Isolated, d=Minimal")
    parser.add_argument("--dim2", type=str, choices=list(VALID_DIM2), help="POV: character or unit")
    parser.add_argument("--dim3", type=str, choices=list(VALID_DIM3), help="Naming: explicit or implied")
    parser.add_argument("--dim4", type=str, choices=list(VALID_DIM4), help="Availability: instant, gated, unknown")

    # Blood classification
    parser.add_argument("--vampirism", type=str, choices=list(VALID_VAMPIRISM), help="Vampirism: outright, implied, channeled, absent")
    parser.add_argument("--hemomancy", type=str, choices=list(VALID_HEMOMANCY), help="Blood magic: a=Core, b=Branch, c=Isolated, d=Minimal, absent")
    parser.add_argument("--pov", type=str, choices=list(VALID_DIM2), help="POV: character or unit")
    parser.add_argument("--availability", type=str, choices=list(VALID_DIM4), help="Availability: instant, gated, unknown")

    # Shared
    parser.add_argument("--notes", type=str, help="Classification justification notes")
    parser.add_argument("--priority", type=str, choices=list(VALID_PRIORITY), help="Priority: high, medium, low")
    parser.add_argument("--dry-run", action="store_true", help="Validate only, don't write")
    parser.add_argument("--deploy", action="store_true", help="Sync DB, export, commit, and push to deploy")
    parser.add_argument("--force", action="store_true", help="Overwrite existing game with same Steam ID")

    args = parser.parse_args()

    # --- Validate ---
    if args.blood:
        errors = validate_blood(args)
    else:
        errors = validate_necromancy(args)

    if errors:
        print("Validation errors:")
        for e in errors:
            print(f"  ✗ {e}")
        return 1

    # --- Determine paths ---
    yaml_path = BLOOD_YAML_PATH if args.blood else GAMES_YAML_PATH
    registry_label = "Blood" if args.blood else "Necromancy"

    # --- Load existing ---
    data = load_yaml(yaml_path)
    games = data["games"]

    # --- Check for duplicates ---
    existing, idx = find_by_steam_id(games, args.steam_id)
    if existing and not args.force:
        print(f"✗ Game with Steam ID {args.steam_id} already exists:")
        print(f"  Name: {existing['name']}")
        print(f"  Use --force to overwrite")
        return 1

    # --- Build entry ---
    if args.blood:
        entry = build_entry_blood(args)
    else:
        entry = build_entry_necromancy(args)

    # --- Insert or replace ---
    if existing and args.force:
        games[idx] = entry
        action = "Updated"
    else:
        games = insert_alphabetical(games, entry)
        data["games"] = games
        action = "Added"

    if args.dry_run:
        print(f"DRY RUN — Would {action.lower()}:")
        print(yaml.dump(entry, default_flow_style=False, allow_unicode=True, sort_keys=False))
        return 0

    # --- Write ---
    save_yaml(data, yaml_path)
    print(f"✓ {action} {args.name} to {registry_label} registry")
    print(f"  Steam ID: {args.steam_id}")
    if not args.blood:
        print(f"  Classification: 1{args.dim1}, 2{args.dim2[0]}, 3{args.dim3[0]}, 4{args.dim4 or 'unknown'}")
    print(f"  Priority: {args.priority or 'medium'}")

    # --- DB Sync ---
    if args.deploy:
        print()
        if sync_to_database():
            print("✓ Database synced")
        if deploy():
            print("✓ Deployed — https://necrotic-realms.vercel.app/")

    return 0


if __name__ == "__main__":
    sys.exit(main())

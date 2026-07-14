#!/usr/bin/env python3
"""
Review Game — Research, classify, and surface a game for Ray's review.

The core workflow for adding a game to the Necromancy Registry. Takes a game
name or Steam ID, looks up details, helps classify, and generates a report.

Usage:
  # Full interactive workflow (search → review → classify → report)
  ./venv/bin/python scripts/review_game.py "Mewgenics"

  # From known Steam ID (skip search)
  ./venv/bin/python scripts/review_game.py --steam-id 2344520

  # Generate report only (for pasting to Ray)
  ./venv/bin/python scripts/review_game.py --steam-id 2344520 --report

  # With suggested classification from a submission
  ./venv/bin/python scripts/review_game.py --steam-id 2344520 --suggested dim1=a,dim2=character,dim3=explicit,dim4=instant --notes "Necromancer class"

Output:
  --report: Markdown report for Ray review (the key artifact)
  Default: Interactive classification then report
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import date

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.scrapers.steam_api import SteamAPI
import steam_lookup

# --- Constants ---
GAMES_YAML_PATH = PROJECT_ROOT / "data" / "games_list.yaml"
BLOOD_YAML_PATH = PROJECT_ROOT / "data" / "blood_games_list.yaml"

# Classification labels for display
CENTRALITY_LABELS = {
    "a": "Core — Necromancy is central to identity and gameplay",
    "b": "Dedicated Branch — Cohesive necromantic specialization",
    "c": "Isolated — Scattered necromantic features exist",
    "d": "Minimal — Necromancy by technicality or lore only",
}

POV_LABELS = {
    "character": "Character — Play AS the necromancer",
    "unit": "Unit — Control necromancer units/faction",
}

NAMING_LABELS = {
    "explicit": "Explicit — 'Necromancer' or variant used in game",
    "implied": "Implied — Death magic without the term",
}

AVAILABILITY_LABELS = {
    "instant": "Instant — Available from start or very early",
    "gated": "Gated — Requires progression, unlocking, or purchase",
    "unknown": "Unknown — Cannot determine",
}

PRIORITY_LABELS = {
    "high": "High — Core necromancy game, active development",
    "medium": "Medium — Solid necromancy presence",
    "low": "Low — Borderline inclusion",
}


def find_existing(steam_id: int, yaml_path: Path = GAMES_YAML_PATH) -> dict | None:
    """Check if a Steam ID already exists in the YAML file."""
    if not yaml_path.exists():
        return None
    import yaml
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    games = data.get("games", [])
    for game in games:
        if game.get("steam_id") == steam_id:
            return game
    return None


def classify_interactive(details: dict, suggested: dict | None = None) -> dict:
    """Interactive classification of a game across all dimensions."""
    print(f"\n{'='*60}")
    print(f"Classifying: {details['name']}")
    print(f"{'='*60}")
    print(f"\nDescription: {details.get('short_description', 'N/A')[:300]}...")
    print(f"Genres: {', '.join(details.get('genres', []))}")
    print(f"Tags: {', '.join(details.get('tags', []))}")
    print()

    # Dimension 1: Centrality
    print("--- Dimension 1: Centrality ---")
    for k, v in CENTRALITY_LABELS.items():
        marker = " ← SUGGESTED" if suggested and suggested.get("dim1") == k else ""
        print(f"  {k}) {v}{marker}")
    dim1 = input("Centrality [a/b/c/d]: ").strip().lower()
    while dim1 not in ("a", "b", "c", "d"):
        if dim1 == "" and suggested and suggested.get("dim1"):
            dim1 = suggested["dim1"]
            break
        dim1 = input("  Must be a, b, c, or d: ").strip().lower()

    # Dimension 2: POV
    print("\n--- Dimension 2: Point of View ---")
    for k, v in POV_LABELS.items():
        marker = " ← SUGGESTED" if suggested and suggested.get("dim2") == k else ""
        print(f"  {k}) {v}{marker}")
    dim2 = input("POV [character/unit]: ").strip().lower()
    while dim2 not in ("character", "unit"):
        if dim2 == "" and suggested and suggested.get("dim2"):
            dim2 = suggested["dim2"]
            break
        dim2 = input("  Must be character or unit: ").strip().lower()

    # Dimension 3: Naming
    print("\n--- Dimension 3: Naming ---")
    for k, v in NAMING_LABELS.items():
        marker = " ← SUGGESTED" if suggested and suggested.get("dim3") == k else ""
        print(f"  {k}) {v}{marker}")
    dim3 = input("Naming [explicit/implied]: ").strip().lower()
    while dim3 not in ("explicit", "implied"):
        if dim3 == "" and suggested and suggested.get("dim3"):
            dim3 = suggested["dim3"]
            break
        dim3 = input("  Must be explicit or implied: ").strip().lower()

    # Dimension 4: Availability
    print("\n--- Dimension 4: Availability ---")
    for k, v in AVAILABILITY_LABELS.items():
        marker = " ← SUGGESTED" if suggested and suggested.get("dim4") == k else ""
        print(f"  {k}) {v}{marker}")
    dim4 = input("Availability [instant/gated/unknown]: ").strip().lower()
    while dim4 not in ("instant", "gated", "unknown"):
        if dim4 == "":
            dim4 = "unknown"
            break
        dim4 = input("  Must be instant, gated, or unknown: ").strip().lower()

    # Notes
    print("\n--- Classification Notes ---")
    default_notes = suggested.get("notes", "") if suggested else ""
    notes = input(f"dimension_1_notes [{default_notes}]: ").strip()
    if not notes:
        notes = default_notes

    # Priority
    print("\n--- Priority ---")
    for k, v in PRIORITY_LABELS.items():
        print(f"  {k}) {v}")
    priority = input("Priority [high/medium/low]: ").strip().lower()
    while priority not in ("high", "medium", "low"):
        if priority == "":
            # Default based on centrality
            priority = {"a": "high", "b": "medium", "c": "medium", "d": "low"}.get(dim1, "medium")
            break
        priority = input("  Must be high, medium, or low: ").strip().lower()

    return {
        "dim1": dim1,
        "dim2": dim2,
        "dim3": dim3,
        "dim4": dim4,
        "notes": notes,
        "priority": priority,
    }


def generate_report(details: dict, classification: dict, submitter_context: dict | None = None) -> str:
    """Generate a Markdown report for Ray review."""
    name = details["name"]
    steam_id = details["steam_id"]
    store_url = f"https://store.steampowered.com/app/{steam_id}/"

    lines = []
    lines.append(f"# Necro Game News — Game Review: {name}")
    lines.append(f"")
    lines.append(f"**Date:** {date.today().isoformat()}")
    lines.append(f"**Reviewer:** Slimeko (community manager)")
    lines.append(f"")

    # Submission context
    if submitter_context:
        lines.append(f"## Submission Context")
        lines.append(f"")
        lines.append(f"- **Submitted by:** {submitter_context.get('submitter', 'unknown')}")
        lines.append(f"- **Suggested:** Centrality={submitter_context.get('dim1', '?')}, POV={submitter_context.get('dim2', '?')}, Naming={submitter_context.get('dim3', '?')}")
        lines.append(f"- **Submitter notes:** {submitter_context.get('notes', '(none)')}")
        lines.append(f"")

    # Game info
    lines.append(f"## Game Info")
    lines.append(f"")
    lines.append(f"- **Name:** {name}")
    lines.append(f"- **Steam ID:** `{steam_id}`")
    lines.append(f"- **Store:** {store_url}")
    lines.append(f"- **Developer:** {details.get('developer', 'unknown')}")
    lines.append(f"- **Publisher:** {details.get('publisher', 'unknown')}")
    lines.append(f"- **Release Date:** {details.get('release_date', 'unknown')}")
    price = details.get('price_usd')
    if price is not None:
        lines.append(f"- **Price:** ${price:.2f}")
    else:
        lines.append(f"- **Price:** Free or TBD")
    lines.append(f"- **Genres:** {', '.join(details.get('genres', []))}")
    lines.append(f"- **Tags:** {', '.join(details.get('tags', []))}")
    lines.append(f"")

    # Description
    lines.append(f"## Description")
    lines.append(f"")
    lines.append(details.get('short_description', 'No description available.'))
    lines.append(f"")

    # Classification
    dim1 = classification["dim1"]
    dim2 = classification["dim2"]
    dim3 = classification["dim3"]
    dim4 = classification.get("dim4", "unknown")
    priority = classification.get("priority", "medium")

    lines.append(f"## Classification")
    lines.append(f"")
    lines.append(f"| Dimension | Value | Meaning |")
    lines.append(f"|-----------|-------|---------|")
    lines.append(f"| Centrality | `{dim1}` | {CENTRALITY_LABELS.get(dim1, dim1)} |")
    lines.append(f"| POV | `{dim2}` | {POV_LABELS.get(dim2, dim2)} |")
    lines.append(f"| Naming | `{dim3}` | {NAMING_LABELS.get(dim3, dim3)} |")
    lines.append(f"| Availability | `{dim4}` | {AVAILABILITY_LABELS.get(dim4, dim4)} |")
    lines.append(f"| Priority | `{priority}` | {PRIORITY_LABELS.get(priority, priority)} |")
    lines.append(f"")

    # Notes
    lines.append(f"## Classification Notes")
    lines.append(f"")
    lines.append(classification.get("notes", "(none)"))
    lines.append(f"")

    # YAML preview
    lines.append(f"## Proposed YAML Entry")
    lines.append(f"")
    lines.append(f"```yaml")
    lines.append(f"- name: '{name}'")
    lines.append(f"  steam_id: {steam_id}")
    lines.append(f"  classification:")
    lines.append(f"    dimension_1: {dim1}")
    lines.append(f"    dimension_2: {dim2}")
    lines.append(f"    dimension_3: {dim3}")
    lines.append(f"    dimension_4: {dim4}")
    lines.append(f"  priority: {priority}")
    lines.append(f"  date_updated: '{date.today().isoformat()}'")
    if classification.get("notes"):
        notes_str = classification["notes"].replace("'", "''")
        lines.append(f"  dimension_1_notes: '{notes_str}'")
    lines.append(f"```")
    lines.append(f"")

    # Header image
    if details.get("header_image"):
        lines.append(f"## Header Image")
        lines.append(f"")
        lines.append(f"![{name}]({details['header_image']})")
        lines.append(f"")

    # Review actions
    lines.append(f"## Review Actions")
    lines.append(f"")
    lines.append(f"- [ ] **Approve** — Add to registry with this classification")
    lines.append(f"- [ ] **Reclassify** — Change dimensions (specify):")
    lines.append(f"  - Centrality: [a/b/c/d]")
    lines.append(f"  - POV: [character/unit]")
    lines.append(f"  - Naming: [explicit/implied]")
    lines.append(f"  - Availability: [instant/gated/unknown]")
    lines.append(f"- [ ] **Reject** — Does not belong in registry (reason):")
    lines.append(f"- [ ] **Defer** — Need more information")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Review a game for the Necromancy Registry",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search + review
  %(prog)s "Mewgenics"

  # From known Steam ID
  %(prog)s --steam-id 2344520

  # With submission context
  %(prog)s --steam-id 2344520 --suggested dim1=a,dim2=character,dim3=explicit,dim4=instant --notes "Necromancer class" --submitter player

  # Report only (non-interactive)
  %(prog)s --steam-id 2344520 --report --suggested dim1=b,dim2=character,dim3=explicit --notes "Necromancy skill tree"
        """
    )
    parser.add_argument("query", nargs="?", type=str, help="Game name to search for")
    parser.add_argument("--steam-id", type=int, help="Steam App ID (skip search)")
    parser.add_argument("--report", action="store_true", help="Generate report only (non-interactive)")
    parser.add_argument("--suggested", type=str, help="Suggested classification: dim1=a,dim2=character,dim3=explicit,dim4=instant")
    parser.add_argument("--notes", type=str, help="Classification notes")
    parser.add_argument("--submitter", type=str, default="player", help="Who submitted (player/developer)")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of Markdown report")
    parser.add_argument("--blood", action="store_true", help="Blood registry instead of necromancy")

    args = parser.parse_args()

    if not args.query and not args.steam_id:
        parser.print_help()
        return 1

    # --- Resolve Steam ID ---
    steam_id = args.steam_id
    game_name = args.query

    if not steam_id:
        # Search for the game
        print(f"Searching Steam for '{game_name}'...", file=sys.stderr)
        results = steam_lookup.search_steam(game_name, limit=5)
        if not results:
            print(f"ERROR: No results for '{game_name}'", file=sys.stderr)
            return 1

        if args.report:
            # Non-interactive: pick first result
            steam_id = results[0]["id"]
            print(f"Auto-selected: {results[0]['name']} ({steam_id})", file=sys.stderr)
        else:
            # Interactive: let user pick
            selected = steam_lookup.search_and_pick(game_name)
            if selected is None:
                print("Search cancelled.", file=sys.stderr)
                return 1
            steam_id = selected["id"]

    # --- Fetch details ---
    print(f"Fetching details for app {steam_id}...", file=sys.stderr)
    details = steam_lookup.fetch_details(steam_id)
    if details is None:
        print(f"ERROR: Could not fetch details for app {steam_id}", file=sys.stderr)
        return 1

    print(f"Found: {details['name']}", file=sys.stderr)

    # --- Check if already exists ---
    yaml_path = BLOOD_YAML_PATH if args.blood else GAMES_YAML_PATH
    existing = find_existing(steam_id, yaml_path)
    if existing:
        print(f"\n⚠️  WARNING: This Steam ID already exists in the registry!")
        print(f"   Existing entry: {existing['name']}")
        print(f"   Classification: 1{existing['classification'].get('dimension_1','?')}, "
              f"2{existing['classification'].get('dimension_2','?')[0] if existing['classification'].get('dimension_2') else '?'}, "
              f"3{existing['classification'].get('dimension_3','?')[0] if existing['classification'].get('dimension_3') else '?'}")
        if not args.report:
            cont = input("\nContinue anyway? [y/N]: ").strip().lower()
            if cont != 'y':
                return 0

    # --- Parse suggested classification ---
    suggested = None
    if args.suggested:
        suggested = {}
        for part in args.suggested.split(","):
            if "=" in part:
                k, v = part.split("=", 1)
                suggested[k.strip()] = v.strip()
        if args.notes:
            suggested["notes"] = args.notes

    # --- Classify ---
    if args.report:
        # Use suggested classification (must be provided in report mode)
        if not suggested:
            print("ERROR: --report requires --suggested with classification", file=sys.stderr)
            return 1
        classification = {
            "dim1": suggested.get("dim1", "?"),
            "dim2": suggested.get("dim2", "?"),
            "dim3": suggested.get("dim3", "?"),
            "dim4": suggested.get("dim4", "unknown"),
            "notes": suggested.get("notes", ""),
            "priority": "medium",
        }
    else:
        classification = classify_interactive(details, suggested)

    # --- Build submitter context ---
    submitter_context = None
    if args.submitter or suggested:
        submitter_context = {
            "submitter": args.submitter,
            "dim1": suggested.get("dim1", "") if suggested else "",
            "dim2": suggested.get("dim2", "") if suggested else "",
            "dim3": suggested.get("dim3", "") if suggested else "",
            "notes": args.notes or "",
        }

    # --- Generate report ---
    if args.json:
        output = {
            "game": details,
            "classification": classification,
            "existing": existing is not None,
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        report = generate_report(details, classification, submitter_context)
        print(report)

    return 0


if __name__ == "__main__":
    sys.exit(main())

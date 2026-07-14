#!/usr/bin/env python3
"""
Steam Game Lookup — Search Steam by game name and retrieve app details.

Used by Slimeko (community manager) to research submitted games, find their
proper Steam IDs, and verify that a game matches its submission description.

Two modes:
  search  — Search Steam by name, return candidate matches
  details — Fetch full app details for a specific Steam App ID

Usage:
  # Search for a game by name
  ./venv/bin/python scripts/steam_lookup.py search "Mewgenics"
  ./venv/bin/python scripts/steam_lookup.py search "V Rising" --limit 5 --json

  # Get full details for a Steam App ID
  ./venv/bin/python scripts/steam_lookup.py details 2344520
  ./venv/bin/python scripts/steam_lookup.py details 2344520 --json

Output:
  Default: human-readable table
  --json:  JSON to stdout (for piping to other scripts)
  --report: Markdown report suitable for Ray review
"""

import sys
import json
import time
import argparse
from pathlib import Path
from typing import Optional

import requests

# Project root for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.scrapers.steam_api import SteamAPI

# --- Store Search API (no API key required) ---
STORE_SEARCH_URL = "https://store.steampowered.com/api/storesearch/"


def search_steam(query: str, limit: int = 10) -> list[dict]:
    """
    Search Steam store by game name.

    Uses the public store search API (no key required).
    Returns list of {appid, name} dicts sorted by relevance.
    """
    params = {"term": query, "l": "english", "cc": "us"}
    try:
        resp = requests.get(STORE_SEARCH_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        return [
            {"id": item["id"], "name": item["name"]}
            for item in items[:limit]
        ]
    except Exception as e:
        print(f"ERROR: Steam search failed: {e}", file=sys.stderr)
        return []


def fetch_details(appid: int, api: Optional[SteamAPI] = None) -> Optional[dict]:
    """
    Fetch full app details for a Steam App ID.

    Returns parsed dict with: steam_id, name, app_type, short_description,
    header_image, screenshot_url, developer, publisher, release_date,
    price_usd, genres, categories, tags.
    """
    if api is None:
        api = SteamAPI()
    raw = api.get_app_details(appid)
    if raw is None:
        return None
    return api.parse_app_details(raw, fetch_tags=True)


def format_candidates_table(results: list[dict]) -> str:
    """Format search results as a human-readable table."""
    lines = []
    lines.append(f"{'#':<3} {'App ID':<10} {'Name'}")
    lines.append("-" * 60)
    for i, r in enumerate(results, 1):
        name = r["name"][:45]
        lines.append(f"{i:<3} {r['id']:<10} {name}")
    return "\n".join(lines)


def format_details_report(details: dict) -> str:
    """Format app details as a Markdown report for Ray review."""
    lines = []
    lines.append(f"## {details['name']}")
    lines.append(f"")
    lines.append(f"- **Steam ID:** `{details['steam_id']}`")
    lines.append(f"- **Store URL:** https://store.steampowered.com/app/{details['steam_id']}/")
    lines.append(f"- **Type:** {details.get('app_type', 'unknown')}")
    lines.append(f"- **Developer:** {details.get('developer', 'unknown')}")
    lines.append(f"- **Publisher:** {details.get('publisher', 'unknown')}")
    lines.append(f"- **Release Date:** {details.get('release_date', 'unknown')}")
    lines.append(f"- **Price:** ${details.get('price_usd', 'N/A')}" if details.get('price_usd') is not None else "- **Price:** Free or unknown")
    lines.append(f"- **Genres:** {', '.join(details.get('genres', []))}")
    lines.append(f"- **Tags:** {', '.join(details.get('tags', []))}")
    lines.append(f"")
    lines.append(f"### Description")
    lines.append(f"")
    desc = details.get('short_description', 'No description available.')
    lines.append(desc)
    lines.append(f"")
    if details.get('header_image'):
        lines.append(f"### Header Image")
        lines.append(f"")
        lines.append(f"![{details['name']}]({details['header_image']})")
        lines.append(f"")
    return "\n".join(lines)


def search_and_pick(query: str, auto_pick: bool = False) -> Optional[dict]:
    """
    Search Steam and interactively pick the correct match.

    If auto_pick is True and there's exactly one result, return it.
    Otherwise, present candidates and let the user select.
    In non-interactive (--auto) mode, returns the first match if unambiguous.

    Returns the selected {id, name} dict or None.
    """
    results = search_steam(query, limit=10)

    if not results:
        print(f"No results found for '{query}'", file=sys.stderr)
        return None

    if auto_pick and len(results) == 1:
        return results[0]

    if auto_pick:
        # In auto mode, return first result with a warning
        print(f"AUTO: Picking first of {len(results)} results for '{query}'", file=sys.stderr)
        return results[0]

    # Interactive mode
    print(f"\nSearch results for '{query}':")
    print(format_candidates_table(results))
    print(f"\nEnter # to select, 's' to skip, or 'q' to quit:")

    while True:
        try:
            choice = input("> ").strip().lower()
            if choice == 'q':
                return None
            if choice == 's':
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(results):
                return results[idx]
            print(f"Enter 1-{len(results)}, 's', or 'q'")
        except (ValueError, EOFError):
            print(f"Enter 1-{len(results)}, 's', or 'q'")


def main():
    parser = argparse.ArgumentParser(
        description="Steam Game Lookup — search by name or fetch app details",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s search "Mewgenics"
  %(prog)s search "V Rising" --json
  %(prog)s search "Diablo" --report
  %(prog)s details 2344520
  %(prog)s details 2344520 --json
  %(prog)s details 2344520 --report
        """
    )
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search Steam by game name")
    search_parser.add_argument("query", type=str, help="Game name to search for")
    search_parser.add_argument("--limit", type=int, default=10, help="Max results (default: 10)")
    search_parser.add_argument("--json", action="store_true", help="Output JSON")
    search_parser.add_argument("--report", action="store_true", help="Output Markdown report")
    search_parser.add_argument("--auto", action="store_true", help="Auto-pick first/best match (non-interactive)")

    # Details command
    details_parser = subparsers.add_parser("details", help="Fetch app details by Steam ID")
    details_parser.add_argument("appid", type=int, help="Steam App ID")
    details_parser.add_argument("--json", action="store_true", help="Output JSON")
    details_parser.add_argument("--report", action="store_true", help="Output Markdown report")

    args = parser.parse_args()

    if args.command == "search":
        results = search_steam(args.query, limit=args.limit)

        if args.json:
            print(json.dumps(results, indent=2))
        elif args.report:
            if not results:
                print(f"*No results found for '{args.query}'*")
                return 1
            print(f"# Steam Search: {args.query}\n")
            print(f"Found {len(results)} result(s):\n")
            for i, r in enumerate(results, 1):
                print(f"{i}. **{r['name']}** — `{r['id']}` — [Store](https://store.steampowered.com/app/{r['id']}/)")
        else:
            if not results:
                print(f"No results found for '{args.query}'")
                return 1
            print(format_candidates_table(results))

    elif args.command == "details":
        details = fetch_details(args.appid)

        if details is None:
            print(f"ERROR: Could not fetch details for app {args.appid}", file=sys.stderr)
            return 1

        if args.json:
            print(json.dumps(details, indent=2, default=str))
        elif args.report:
            print(format_details_report(details))
        else:
            print(format_details_report(details))

    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

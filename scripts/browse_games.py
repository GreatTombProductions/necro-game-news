#!/usr/bin/env python3
"""
Interactive game browser for Necro Game News.

Browse and edit games in games_list.yaml, prioritized by missing info.

Usage:
    python scripts/browse_games.py           # Browse games needing attention
    python scripts/browse_games.py --all     # Browse all games
    python scripts/browse_games.py --search  # Search by name

Controls:
    e - Edit game
    s - Skip
    o - Open Steam store page
    n - Next
    p - Previous
    q - Quit
"""

import sys
import os
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
import yaml

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def load_games() -> dict:
    """Load games from YAML file."""
    yaml_path = Path('data/games_list.yaml')
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)


def save_games(data: dict):
    """Save games to YAML file."""
    yaml_path = Path('data/games_list.yaml')
    with open(yaml_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def calculate_priority_score(game: dict) -> tuple:
    """
    Calculate priority score for sorting.
    Returns a tuple for sorting (lower = higher priority).

    Priority factors (in order):
    1. Missing dimension_4 (highest priority)
    2. Missing dimension_1_notes
    3. Missing dimension_2_notes or dimension_3_notes
    4. Older date_updated (older = higher priority)
    """
    classification = game.get('classification', {})

    # Check what's missing
    has_dim4 = classification.get('dimension_4') is not None
    has_dim1_notes = bool(game.get('dimension_1_notes'))
    has_dim2_notes = bool(game.get('dimension_2_notes'))
    has_dim3_notes = bool(game.get('dimension_3_notes'))

    # Score components (0 = missing = higher priority)
    dim4_score = 1 if has_dim4 else 0
    dim1_notes_score = 1 if has_dim1_notes else 0
    other_notes_score = 1 if (has_dim2_notes and has_dim3_notes) else 0

    # Date score (older = lower score = higher priority)
    date_str = game.get('date_updated', '1970-01-01')
    try:
        date_val = datetime.strptime(date_str, '%Y-%m-%d')
    except (ValueError, TypeError):
        date_val = datetime(1970, 1, 1)

    # Return tuple for sorting
    # Lower values = higher priority
    return (dim4_score, dim1_notes_score, other_notes_score, date_val)


def get_completeness_indicator(game: dict) -> str:
    """Get a visual indicator of how complete the game's info is."""
    classification = game.get('classification', {})

    indicators = []

    # dimension_4
    if classification.get('dimension_4'):
        indicators.append(f"{Colors.GREEN}D4{Colors.END}")
    else:
        indicators.append(f"{Colors.RED}D4{Colors.END}")

    # dimension_1_notes
    if game.get('dimension_1_notes'):
        indicators.append(f"{Colors.GREEN}N1{Colors.END}")
    else:
        indicators.append(f"{Colors.RED}N1{Colors.END}")

    # dimension_2_notes
    if game.get('dimension_2_notes'):
        indicators.append(f"{Colors.GREEN}N2{Colors.END}")
    else:
        indicators.append(f"{Colors.DIM}N2{Colors.END}")

    # dimension_3_notes
    if game.get('dimension_3_notes'):
        indicators.append(f"{Colors.GREEN}N3{Colors.END}")
    else:
        indicators.append(f"{Colors.DIM}N3{Colors.END}")

    return " ".join(indicators)


def display_game(game: dict, index: int, total: int):
    """Display a game with all relevant information."""
    print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}Game {index}/{total}{Colors.END}  [{get_completeness_indicator(game)}]")
    print(f"{Colors.BOLD}{'='*80}{Colors.END}\n")

    print(f"{Colors.CYAN}{Colors.BOLD}{game['name']}{Colors.END}")

    # IDs
    if game.get('steam_id'):
        print(f"{Colors.BLUE}Steam ID:{Colors.END} {game['steam_id']}")
    if game.get('battlenet_id'):
        print(f"{Colors.BLUE}Battle.net ID:{Colors.END} {game['battlenet_id']}")

    # Classification
    classification = game.get('classification', {})
    print(f"\n{Colors.YELLOW}Classification:{Colors.END}")
    print(f"  Dimension 1 (Centrality): {Colors.BOLD}{classification.get('dimension_1', '?')}{Colors.END}")
    print(f"  Dimension 2 (POV):        {Colors.BOLD}{classification.get('dimension_2', '?')}{Colors.END}")
    print(f"  Dimension 3 (Naming):     {Colors.BOLD}{classification.get('dimension_3', '?')}{Colors.END}")

    dim4 = classification.get('dimension_4')
    dim4_color = Colors.GREEN if dim4 else Colors.RED
    print(f"  Dimension 4 (Availability): {dim4_color}{Colors.BOLD}{dim4 or 'NOT SET'}{Colors.END}")

    # Notes
    print(f"\n{Colors.YELLOW}Notes:{Colors.END}")
    dim1_notes = game.get('dimension_1_notes')
    dim1_color = Colors.GREEN if dim1_notes else Colors.RED
    print(f"  D1 Notes: {dim1_color}{dim1_notes or 'NOT SET'}{Colors.END}")

    dim2_notes = game.get('dimension_2_notes')
    dim2_color = Colors.DIM if not dim2_notes else Colors.END
    print(f"  D2 Notes: {dim2_color}{dim2_notes or '(not set)'}{Colors.END}")

    dim3_notes = game.get('dimension_3_notes')
    dim3_color = Colors.DIM if not dim3_notes else Colors.END
    print(f"  D3 Notes: {dim3_color}{dim3_notes or '(not set)'}{Colors.END}")

    # Other info
    if game.get('short_description'):
        print(f"\n{Colors.YELLOW}Description:{Colors.END}")
        print(f"  {game['short_description'][:200]}...")

    print(f"\n{Colors.BLUE}Date Updated:{Colors.END} {game.get('date_updated', 'unknown')}")

    # Links
    if game.get('steam_id'):
        print(f"{Colors.BLUE}Steam Store:{Colors.END} https://store.steampowered.com/app/{game['steam_id']}/")


def edit_game(game: dict) -> bool:
    """
    Interactive game editor.

    Returns True if changes were made.
    """
    print(f"\n{Colors.BOLD}{Colors.GREEN}EDIT MODE{Colors.END}")
    print(f"{Colors.BOLD}{'='*80}{Colors.END}")
    print("Press Enter to keep current value, or type new value.")
    print("Type 'x' to clear a field.\n")

    changes_made = False
    classification = game.setdefault('classification', {})

    # Dimension 4
    print(f"{Colors.YELLOW}Dimension 4 - Availability:{Colors.END}")
    print("  instant - Necromancy available from start or very early")
    print("  gated   - Necromancy requires unlock/DLC/progression")
    print("  unknown - Not sure yet")
    current_dim4 = classification.get('dimension_4', '')
    new_dim4 = input(f"{Colors.CYAN}[{current_dim4 or 'not set'}]:{Colors.END} ").strip().lower()

    if new_dim4 == 'x':
        if 'dimension_4' in classification:
            del classification['dimension_4']
            changes_made = True
    elif new_dim4 in ['instant', 'gated', 'unknown']:
        if new_dim4 != current_dim4:
            classification['dimension_4'] = new_dim4
            changes_made = True
    elif new_dim4:
        print(f"{Colors.RED}Invalid value. Must be instant/gated/unknown{Colors.END}")

    # Dimension 1 Notes
    print(f"\n{Colors.YELLOW}Dimension 1 Notes (centrality justification):{Colors.END}")
    current_d1_notes = game.get('dimension_1_notes', '')
    new_d1_notes = input(f"{Colors.CYAN}[{current_d1_notes or 'not set'}]:{Colors.END} ").strip()

    if new_d1_notes == 'x':
        if 'dimension_1_notes' in game:
            del game['dimension_1_notes']
            changes_made = True
    elif new_d1_notes and new_d1_notes != current_d1_notes:
        game['dimension_1_notes'] = new_d1_notes
        changes_made = True

    # Ask if they want to edit more
    edit_more = input(f"\n{Colors.CYAN}Edit other fields? [y/N]:{Colors.END} ").strip().lower()

    if edit_more == 'y':
        # Dimension 1
        print(f"\n{Colors.YELLOW}Dimension 1 - Centrality:{Colors.END}")
        print("  a - Core identity (necromancer class/protagonist)")
        print("  b - Specialization available (necromantic skill tree)")
        print("  c - Isolated features (necromantic items/skills exist)")
        print("  d - Flavor only (necromancy in lore, minimal gameplay)")
        current_d1 = classification.get('dimension_1', '')
        new_d1 = input(f"{Colors.CYAN}[{current_d1}]:{Colors.END} ").strip().lower()
        if new_d1 in ['a', 'b', 'c', 'd'] and new_d1 != current_d1:
            classification['dimension_1'] = new_d1
            changes_made = True

        # Dimension 2
        print(f"\n{Colors.YELLOW}Dimension 2 - POV:{Colors.END}")
        print("  character - Play AS the necromancer")
        print("  unit      - Control necromancer units among others")
        current_d2 = classification.get('dimension_2', '')
        new_d2 = input(f"{Colors.CYAN}[{current_d2}]:{Colors.END} ").strip().lower()
        if new_d2 in ['character', 'unit'] and new_d2 != current_d2:
            classification['dimension_2'] = new_d2
            changes_made = True

        # Dimension 3
        print(f"\n{Colors.YELLOW}Dimension 3 - Naming:{Colors.END}")
        print("  explicit - Referred to as 'necromancer/necromancy'")
        print("  implied  - Death magic without explicit terminology")
        current_d3 = classification.get('dimension_3', '')
        new_d3 = input(f"{Colors.CYAN}[{current_d3}]:{Colors.END} ").strip().lower()
        if new_d3 in ['explicit', 'implied'] and new_d3 != current_d3:
            classification['dimension_3'] = new_d3
            changes_made = True

        # Dimension 2 Notes
        print(f"\n{Colors.YELLOW}Dimension 2 Notes (POV justification):{Colors.END}")
        current_d2_notes = game.get('dimension_2_notes', '')
        new_d2_notes = input(f"{Colors.CYAN}[{current_d2_notes or 'not set'}]:{Colors.END} ").strip()
        if new_d2_notes == 'x':
            if 'dimension_2_notes' in game:
                del game['dimension_2_notes']
                changes_made = True
        elif new_d2_notes and new_d2_notes != current_d2_notes:
            game['dimension_2_notes'] = new_d2_notes
            changes_made = True

        # Dimension 3 Notes
        print(f"\n{Colors.YELLOW}Dimension 3 Notes (naming justification):{Colors.END}")
        current_d3_notes = game.get('dimension_3_notes', '')
        new_d3_notes = input(f"{Colors.CYAN}[{current_d3_notes or 'not set'}]:{Colors.END} ").strip()
        if new_d3_notes == 'x':
            if 'dimension_3_notes' in game:
                del game['dimension_3_notes']
                changes_made = True
        elif new_d3_notes and new_d3_notes != current_d3_notes:
            game['dimension_3_notes'] = new_d3_notes
            changes_made = True

    # Update date_updated if changes were made
    if changes_made:
        game['date_updated'] = datetime.now().strftime('%Y-%m-%d')
        print(f"\n{Colors.GREEN}✓ Changes saved, date_updated set to {game['date_updated']}{Colors.END}")
    else:
        print(f"\n{Colors.YELLOW}No changes made{Colors.END}")

    return changes_made


def browse_games(games: list, data: dict, save_on_edit: bool = True):
    """
    Main browsing loop.

    Args:
        games: Sorted list of games to browse
        data: Full YAML data dict (for saving)
        save_on_edit: Whether to save after each edit
    """
    total = len(games)
    current_idx = 0
    changes_made = False

    while True:
        if current_idx < 0:
            current_idx = 0
        if current_idx >= total:
            current_idx = total - 1

        game = games[current_idx]
        display_game(game, current_idx + 1, total)

        print(f"\n{Colors.BOLD}Actions:{Colors.END}")
        print(f"  {Colors.GREEN}[e]{Colors.END} Edit game")
        print(f"  {Colors.YELLOW}[s/n]{Colors.END} Skip / Next")
        print(f"  {Colors.CYAN}[p]{Colors.END} Previous")
        print(f"  {Colors.BLUE}[o]{Colors.END} Open in browser")
        print(f"  {Colors.BLUE}[g]{Colors.END} Go to game # / search")
        print(f"  [q] Quit")

        choice = input(f"\n{Colors.BOLD}Choice:{Colors.END} ").strip().lower()

        if choice == 'e':
            if edit_game(game):
                changes_made = True
                if save_on_edit:
                    save_games(data)
                    print(f"{Colors.GREEN}✓ Saved to games_list.yaml{Colors.END}")
            current_idx += 1

        elif choice in ['s', 'n', '']:
            current_idx += 1

        elif choice == 'p':
            current_idx -= 1

        elif choice == 'o':
            if game.get('steam_id'):
                import webbrowser
                url = f"https://store.steampowered.com/app/{game['steam_id']}/"
                webbrowser.open(url)
                print(f"\n{Colors.BLUE}Opened in browser{Colors.END}")
            else:
                print(f"\n{Colors.RED}No Steam ID for this game{Colors.END}")
            continue  # Don't advance

        elif choice == 'g':
            search = input(f"{Colors.CYAN}Game # or search term:{Colors.END} ").strip()
            if search.isdigit():
                new_idx = int(search) - 1
                if 0 <= new_idx < total:
                    current_idx = new_idx
                else:
                    print(f"{Colors.RED}Invalid game number{Colors.END}")
            else:
                # Search by name
                for i, g in enumerate(games):
                    if search.lower() in g['name'].lower():
                        current_idx = i
                        break
                else:
                    print(f"{Colors.RED}No game found matching '{search}'{Colors.END}")

        elif choice == 'q':
            return changes_made

        # Check if we've gone through all games
        if current_idx >= total:
            print(f"\n{Colors.GREEN}Reached end of list!{Colors.END}")
            restart = input(f"{Colors.CYAN}Start over? [y/N]:{Colors.END} ").strip().lower()
            if restart == 'y':
                current_idx = 0
            else:
                return changes_made


def run_deploy():
    """Run deploy.sh with option 3 (new games only)."""
    print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}DEPLOYING CHANGES{Colors.END}")
    print(f"{Colors.BOLD}{'='*80}{Colors.END}\n")

    script_dir = Path(__file__).parent.parent
    deploy_script = script_dir / 'scripts' / 'deploy.sh'

    # Run with --new-only flag
    result = subprocess.run(
        ['bash', str(deploy_script), '--new-only'],
        cwd=str(script_dir)
    )

    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(
        description="Browse and edit games in games_list.yaml",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Controls:
  e - Edit game (dimension_4, notes, etc.)
  s/n - Skip / Next game
  p - Previous game
  o - Open in browser
  g - Go to game # or search
  q - Quit

Games are sorted by priority:
  1. Missing dimension_4 (highest)
  2. Missing dimension_1_notes
  3. Missing dimension_2/3_notes
  4. Older date_updated
        """
    )
    parser.add_argument('--all', action='store_true',
                       help="Show all games, not just ones needing attention")
    parser.add_argument('--no-deploy', action='store_true',
                       help="Don't run deploy on exit")
    parser.add_argument('--search', metavar='TERM',
                       help="Search for games by name")

    args = parser.parse_args()

    # Load games
    data = load_games()
    games = data.get('games', [])

    if not games:
        print(f"{Colors.RED}No games found in games_list.yaml{Colors.END}")
        return

    # Filter by search if specified
    if args.search:
        games = [g for g in games if args.search.lower() in g['name'].lower()]
        if not games:
            print(f"{Colors.RED}No games found matching '{args.search}'{Colors.END}")
            return

    # Sort by priority
    games.sort(key=calculate_priority_score)

    # If not --all, filter to only games needing attention
    if not args.all and not args.search:
        def needs_attention(game):
            classification = game.get('classification', {})
            return (
                not classification.get('dimension_4') or
                not game.get('dimension_1_notes')
            )

        filtered_games = [g for g in games if needs_attention(g)]
        if filtered_games:
            games = filtered_games
            print(f"\n{Colors.CYAN}Showing {len(games)} games needing attention{Colors.END}")
            print(f"{Colors.DIM}(Use --all to see all games){Colors.END}")
        else:
            print(f"\n{Colors.GREEN}All games have dimension_4 and dimension_1_notes!{Colors.END}")
            show_all = input(f"{Colors.CYAN}Show all games anyway? [y/N]:{Colors.END} ").strip().lower()
            if show_all != 'y':
                return

    # Stats
    total = len(games)
    missing_dim4 = sum(1 for g in games if not g.get('classification', {}).get('dimension_4'))
    missing_d1_notes = sum(1 for g in games if not g.get('dimension_1_notes'))

    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}NECRO GAME NEWS - GAME BROWSER{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"\n{Colors.BOLD}{total}{Colors.END} games to review")
    print(f"  {Colors.RED}Missing dimension_4:{Colors.END} {missing_dim4}")
    print(f"  {Colors.RED}Missing dimension_1_notes:{Colors.END} {missing_d1_notes}")

    # Browse
    changes_made = browse_games(games, data)

    # Summary and deploy
    print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}SESSION COMPLETE{Colors.END}")
    print(f"{Colors.BOLD}{'='*80}{Colors.END}")

    if changes_made:
        print(f"{Colors.GREEN}✓ Changes were saved to games_list.yaml{Colors.END}")

        if not args.no_deploy:
            deploy = input(f"\n{Colors.CYAN}Deploy changes now? [Y/n]:{Colors.END} ").strip().lower()
            if deploy != 'n':
                run_deploy()
    else:
        print(f"{Colors.YELLOW}No changes were made{Colors.END}")


if __name__ == "__main__":
    main()

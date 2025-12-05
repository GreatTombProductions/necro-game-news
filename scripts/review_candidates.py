#!/usr/bin/env python3
"""
Interactive candidate review tool for Necro Game News.

Provides a fast, keyboard-driven interface to review discovered games
and add approved ones to games_list.yaml.

Usage:
    python scripts/review_candidates.py              # Review pending candidates
    python scripts/review_candidates.py --all        # Review all candidates
    python scripts/review_candidates.py --top 10     # Review top 10 by score

Controls:
    y - Approve and classify
    n - Reject with reason
    s - Skip for now
    q - Quit
    ? - Show help
"""

import sys
import os
import logging
import argparse
import re
from datetime import datetime
from pathlib import Path
import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.schema import get_connection
from backend.scrapers.steam_api import SteamAPI

# Set up logging
logging.basicConfig(
    level=logging.WARNING,  # Quiet during interactive mode
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def parse_justification_for_score(justification: str) -> int:
    """Extract score from justification text if present."""
    match = re.search(r'score\s+(\d+)', justification, re.IGNORECASE)
    return int(match.group(1)) if match else 0


def get_pending_candidates(conn, include_statuses: list[str] = None, limit: int = None) -> list[dict]:
    """
    Get candidates from database.

    Args:
        conn: Database connection
        include_statuses: List of statuses to include (e.g., ['pending', 'skipped'])
        limit: Maximum number to retrieve

    Returns:
        List of candidate dictionaries
    """
    cursor = conn.cursor()
    cursor.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))

    query = "SELECT * FROM candidates"

    if include_statuses:
        # Build WHERE clause for multiple statuses
        status_conditions = [f"status = '{s}'" for s in include_statuses]
        query += f" WHERE ({' OR '.join(status_conditions)})"

    # Try to order by score if available in justification
    query += " ORDER BY date_submitted DESC"

    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    candidates = cursor.fetchall()

    # Sort by score if we can extract it
    for candidate in candidates:
        candidate['_score'] = parse_justification_for_score(candidate.get('justification', ''))

    candidates.sort(key=lambda x: x['_score'], reverse=True)

    return candidates


def display_candidate(candidate: dict, index: int, total: int):
    """Display a candidate game with all relevant information."""
    print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}Candidate {index}/{total}{Colors.END}")
    print(f"{Colors.BOLD}{'='*80}{Colors.END}\n")

    print(f"{Colors.CYAN}{Colors.BOLD}{candidate['game_name']}{Colors.END}")
    print(f"{Colors.BLUE}Steam ID:{Colors.END} {candidate['steam_id']}")
    print(f"{Colors.BLUE}Source:{Colors.END} {candidate['source']}")

    # Show current status with color
    status = candidate.get('status', 'unknown')
    status_colors = {
        'pending': Colors.CYAN,
        'skipped': Colors.YELLOW,
        'rejected': Colors.RED,
        'approved': Colors.GREEN
    }
    status_color = status_colors.get(status, Colors.END)
    print(f"{Colors.BLUE}Status:{Colors.END} {status_color}{status.upper()}{Colors.END}")

    if candidate.get('_score'):
        print(f"{Colors.BLUE}Discovery Score:{Colors.END} {Colors.GREEN}{candidate['_score']}{Colors.END}")

    print(f"\n{Colors.YELLOW}Justification:{Colors.END}")
    print(candidate.get('justification', 'No justification provided'))

    # Show Steam store link
    print(f"\n{Colors.BLUE}Steam Store:{Colors.END} https://store.steampowered.com/app/{candidate['steam_id']}/")


def prompt_classification() -> dict:
    """
    Prompt user for necromancy classification.

    Returns:
        Dictionary with dimension_1, dimension_2, dimension_3, and notes
    """
    print(f"\n{Colors.BOLD}{Colors.GREEN}CLASSIFICATION{Colors.END}")
    print(f"{Colors.BOLD}{'='*80}{Colors.END}")

    print(f"\n{Colors.YELLOW}Dimension 1 - Centrality (how central is necromancy?):{Colors.END}")
    print("  a - Core identity (necromancer class/protagonist)")
    print("  b - Specialization available (necromantic skill tree)")
    print("  c - Isolated features (necromantic items/skills exist)")
    print("  d - Flavor only (necromancy in lore, minimal gameplay)")

    while True:
        dim1 = input(f"\n{Colors.CYAN}Dimension 1 [a/b/c/d]:{Colors.END} ").strip().lower()
        if dim1 in ['a', 'b', 'c', 'd']:
            break
        print(f"{Colors.RED}Invalid choice. Please enter a, b, c, or d{Colors.END}")

    print(f"\n{Colors.YELLOW}Dimension 2 - Player POV:{Colors.END}")
    print("  character - Play AS the necromancer (ARPGs, first-person)")
    print("  unit - Control necromancer units among others (RTS, tactics)")

    while True:
        dim2 = input(f"\n{Colors.CYAN}Dimension 2 [character/unit]:{Colors.END} ").strip().lower()
        if dim2 in ['character', 'unit']:
            break
        print(f"{Colors.RED}Invalid choice. Please enter 'character' or 'unit'{Colors.END}")

    print(f"\n{Colors.YELLOW}Dimension 3 - Naming:{Colors.END}")
    print("  explicit - Referred to as 'necromancer/necromancy'")
    print("  implied - Death magic without explicit terminology")

    while True:
        dim3 = input(f"\n{Colors.CYAN}Dimension 3 [explicit/implied]:{Colors.END} ").strip().lower()
        if dim3 in ['explicit', 'implied']:
            break
        print(f"{Colors.RED}Invalid choice. Please enter 'explicit' or 'implied'{Colors.END}")

    notes = input(f"\n{Colors.CYAN}Classification notes (optional):{Colors.END} ").strip()

    priority = input(f"\n{Colors.CYAN}Priority [high/medium/low] (default: medium):{Colors.END} ").strip().lower()
    if priority not in ['high', 'medium', 'low']:
        priority = 'medium'

    return {
        'dimension_1': dim1,
        'dimension_2': dim2,
        'dimension_3': dim3,
        'notes': notes or None,
        'priority': priority
    }


def add_to_yaml(game_data: dict, classification: dict):
    """
    Add approved game to games_list.yaml.

    Args:
        game_data: Dictionary with game info (name, steam_id)
        classification: Classification dictionary from prompt_classification()
    """
    yaml_path = Path('data/games_list.yaml')

    # Read existing YAML
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)

    if 'games' not in data:
        data['games'] = []

    # Create new game entry
    new_game = {
        'name': game_data['game_name'],
        'steam_id': game_data['steam_id'],
        'classification': {
            'dimension_1': classification['dimension_1'],
            'dimension_2': classification['dimension_2'],
            'dimension_3': classification['dimension_3'],
        },
        'date_added': datetime.now().strftime('%Y-%m-%d')
    }

    if classification.get('notes'):
        new_game['notes'] = classification['notes']

    if classification.get('priority'):
        new_game['priority'] = classification['priority']

    # Add to games list
    data['games'].append(new_game)

    # Write back to file
    with open(yaml_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"\n{Colors.GREEN}✓ Added to games_list.yaml{Colors.END}")


def update_candidate_status(conn, candidate_id: int, status: str, notes: str = None):
    """
    Update candidate status in database.

    Args:
        conn: Database connection
        candidate_id: Candidate ID
        status: New status ('approved', 'rejected', 'pending')
        notes: Review notes
    """
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE candidates
        SET status = ?,
            review_notes = ?,
            review_date = ?
        WHERE id = ?
    """, (status, notes, datetime.now(), candidate_id))
    conn.commit()


def review_candidate(candidate: dict, index: int, total: int, conn) -> str:
    """
    Review a single candidate interactively.

    Args:
        candidate: Candidate dictionary
        index: Current index (1-based)
        total: Total number of candidates
        conn: Database connection

    Returns:
        Action taken: 'approved', 'rejected', 'skipped', 'quit'
    """
    display_candidate(candidate, index, total)

    print(f"\n{Colors.BOLD}Actions:{Colors.END}")
    print(f"  {Colors.GREEN}[y]{Colors.END} Approve and classify")
    print(f"  {Colors.RED}[n]{Colors.END} Reject")
    print(f"  {Colors.YELLOW}[s]{Colors.END} Skip for now")
    print(f"  {Colors.BLUE}[o]{Colors.END} Open in browser")
    print(f"  [q] Quit")

    while True:
        choice = input(f"\n{Colors.BOLD}Your choice:{Colors.END} ").strip().lower()

        if choice == 'y':
            # Approve
            classification = prompt_classification()

            # Add to YAML
            add_to_yaml(candidate, classification)

            # Update database
            update_candidate_status(
                conn,
                candidate['id'],
                'approved',
                f"Approved with classification: {classification}"
            )

            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ APPROVED{Colors.END}")
            return 'approved'

        elif choice == 'n':
            # Reject
            reason = input(f"\n{Colors.CYAN}Rejection reason (optional):{Colors.END} ").strip()

            update_candidate_status(
                conn,
                candidate['id'],
                'rejected',
                reason or 'Rejected during review'
            )

            print(f"\n{Colors.RED}{Colors.BOLD}✗ REJECTED{Colors.END}")
            return 'rejected'

        elif choice == 's':
            # Skip - mark as skipped in database
            update_candidate_status(
                conn,
                candidate['id'],
                'skipped',
                'Skipped during review'
            )

            print(f"\n{Colors.YELLOW}→ SKIPPED{Colors.END}")
            return 'skipped'

        elif choice == 'o':
            # Open in browser
            import webbrowser
            url = f"https://store.steampowered.com/app/{candidate['steam_id']}/"
            webbrowser.open(url)
            print(f"\n{Colors.BLUE}Opened in browser{Colors.END}")
            # Don't return - let them make another choice
            continue

        elif choice == 'q':
            return 'quit'

        else:
            print(f"{Colors.RED}Invalid choice. Please enter y, n, s, o, or q{Colors.END}")


def main():
    parser = argparse.ArgumentParser(
        description="Review game candidates interactively",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Controls:
  y - Approve and classify
  n - Reject with reason
  s - Skip for now
  o - Open in browser
  q - Quit

Examples:
  python scripts/review_candidates.py                     # Review pending only
  python scripts/review_candidates.py --ignore-skipped    # Review pending, skip skipped
  python scripts/review_candidates.py --review-rejected   # Review rejected candidates
  python scripts/review_candidates.py --all               # Review everything
  python scripts/review_candidates.py --top 10            # Review top 10
        """
    )
    parser.add_argument('--all', action='store_true',
                       help="Review all candidates regardless of status")
    parser.add_argument('--ignore-skipped', action='store_true',
                       help="Don't show skipped candidates (only pending)")
    parser.add_argument('--review-rejected', action='store_true',
                       help="Review rejected candidates for reconsideration")
    parser.add_argument('--top', type=int, metavar='N',
                       help="Review only top N candidates by score")

    args = parser.parse_args()

    # Determine which statuses to include
    if args.all:
        # Show everything
        include_statuses = None  # No filter
    elif args.review_rejected:
        # Only show rejected
        include_statuses = ['rejected']
    elif args.ignore_skipped:
        # Only pending, exclude skipped
        include_statuses = ['pending']
    else:
        # Default: pending and skipped (not approved/rejected)
        include_statuses = ['pending', 'skipped']

    # Get candidates
    conn = get_connection()
    try:
        candidates = get_pending_candidates(conn, include_statuses=include_statuses, limit=args.top)

        if not candidates:
            print(f"\n{Colors.YELLOW}No candidates to review.{Colors.END}")
            print(f"Run {Colors.CYAN}python scripts/discover_games.py --search --save{Colors.END} to find games")
            return

        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}NECRO GAME NEWS - CANDIDATE REVIEW{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
        print(f"\nFound {Colors.BOLD}{len(candidates)}{Colors.END} candidates to review")

        # Review loop
        stats = {'approved': 0, 'rejected': 0, 'skipped': 0}

        for i, candidate in enumerate(candidates, 1):
            result = review_candidate(candidate, i, len(candidates), conn)

            if result == 'quit':
                print(f"\n{Colors.YELLOW}Review session ended.{Colors.END}")
                break

            if result in stats:
                stats[result] += 1

            # Brief pause between candidates
            if result != 'quit' and i < len(candidates):
                input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.END}")

        # Summary
        print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}REVIEW SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{'='*80}{Colors.END}")
        print(f"{Colors.GREEN}Approved:{Colors.END} {stats['approved']}")
        print(f"{Colors.RED}Rejected:{Colors.END} {stats['rejected']}")
        print(f"{Colors.YELLOW}Skipped:{Colors.END}  {stats['skipped']}")

        if stats['approved'] > 0:
            print(f"\n{Colors.GREEN}✓ {stats['approved']} game(s) added to games_list.yaml{Colors.END}")
            print(f"\nNext steps:")
            print(f"  1. Run: {Colors.CYAN}python scripts/load_games_from_yaml.py --update{Colors.END}")
            print(f"  2. Run: {Colors.CYAN}python scripts/check_updates.py{Colors.END}")
            print(f"  3. Run: {Colors.CYAN}python scripts/export_for_web.py{Colors.END}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
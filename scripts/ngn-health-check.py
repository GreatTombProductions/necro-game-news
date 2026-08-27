#!/usr/bin/env python3
"""NGN deployment health check — automated monitoring bridge.

Detects silent breakage of the Necro Game News deploy pipeline. The nightly
data-update cron (~19:36 UTC) pushes to main; Vercel auto-deploys. The pipeline
has broken silently four times (S25 env vars, S27 SDK, S31 client-side filter,
S34 cache-incremental install) — each discovered reactively after serving stale
data for days. This bridge converts the manual S35 verification into a daily
automated check.

Checks:
  1. Latest GitHub deployment for GreatTombProductions/necro-game-news
     has state == success
  2. Live https://necrotic-realms.vercel.app/data/games.json sha256 ==
     committed frontend/public/data/games.json sha256

On failure: writes a report-framed inbox file to agents/slimeko/workspace/inbox/
(provenance header, deployment id, ref, state, hashes, timestamp) and prints
FAIL to stdout. Does NOT attempt any fix — classification and routing stay with
Slimeko (the inbox item is the alert; Ray gates NGN classification decisions).

Exit code: always 0 when the check ran (alert written = the deliverable), so a
failure here does not abort sibling sections of feedback-pickup-all.sh under
`set -e`. Use --fail-test to exercise the alert path.

Usage:
  python3 ngn-health-check.py              # real check
  python3 ngn-health-check.py --fail-test  # simulated failure (writes alert)
"""

import argparse
import datetime
import hashlib
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

REPO = "GreatTombProductions/necro-game-news"
LIVE_GAMES_URL = "https://necrotic-realms.vercel.app/data/games.json"
COMMITTED_GAMES = Path(
    "/home/ray/greattomb/0th-floor-exterior/east-mausoleum/necro-game-news/frontend/public/data/games.json"
)
INBOX_DIR = Path("/home/ray/greattomb/agents/slimeko/workspace/inbox")


def gh_api(*args: str) -> dict:
    """Run `gh api` with args, return parsed JSON."""
    result = subprocess.run(
        ["gh", "api", *args], capture_output=True, text=True, check=True
    )
    return json.loads(result.stdout)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_bytes(url: str, timeout: int = 30) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return resp.read()


def write_alert(meta: dict, problems: list) -> Path:
    """Write a report-framed inbox file. Returns the path written."""
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    fname = f"from-ngn-health-check-{ts.replace(':', '').replace('-', '').replace('T', '-').split('+')[0]}.md"
    path = INBOX_DIR / fname

    lines = [
        "---",
        "from: ngn-health-check-bridge",
        "signal_type: deploy_health",
        "source: necro-game-news",
        "priority: high",
        f"requested: {ts}",
        "---",
        "",
        "# NGN Deployment Health Check — FAILURE",
        "",
        "The automated NGN health bridge detected a deployment health problem.",
        "Investigate before the site serves stale data any longer.",
        "",
        "## Problems",
    ]
    for p in problems:
        lines.append(f"- {p}")
    lines += [
        "",
        "## Metadata",
        f"- Deployment ID: {meta.get('deployment_id', 'n/a')}",
        f"- Ref: {meta.get('ref', 'n/a')}",
        f"- Environment: {meta.get('environment', 'n/a')}",
        f"- Deployment state: {meta.get('state', 'n/a')}",
        f"- Deployment created: {meta.get('deployment_created_at', 'n/a')}",
        f"- Status created: {meta.get('status_created_at', 'n/a')}",
        f"- Live games.json sha256: {meta.get('live_sha256', 'n/a')}",
        f"- Committed games.json sha256: {meta.get('committed_sha256', 'n/a')}",
        f"- Checked at: {ts}",
        "",
        "**No fix attempted** — this bridge only alerts. Classification and",
        "routing stay with Slimeko; Ray gates NGN classification decisions.",
        "",
    ]
    path.write_text("\n".join(lines))
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="NGN deployment health check bridge.")
    parser.add_argument(
        "--fail-test",
        action="store_true",
        help="Simulate a failure: write an alert without real checks (test the alert path).",
    )
    args = parser.parse_args()

    problems: list = []
    meta: dict = {}

    if args.fail_test:
        problems.append("SIMULATED FAILURE (--fail-test) — test of the alert path, not a real problem")
        meta = {
            "deployment_id": "TEST",
            "ref": "test-ref",
            "environment": "Production",
            "state": "simulated-failure",
            "deployment_created_at": "n/a",
            "status_created_at": "n/a",
            "live_sha256": "test-live-sha",
            "committed_sha256": "test-committed-sha",
        }
    else:
        # Check 1: latest deployment state
        try:
            dep = gh_api(f"repos/{REPO}/deployments", "--jq", ".[0]")
            dep_id = dep.get("id")
            meta["deployment_id"] = dep_id
            meta["ref"] = dep.get("sha") or dep.get("ref")
            meta["environment"] = dep.get("environment")
            meta["deployment_created_at"] = dep.get("created_at")
            status = gh_api(
                f"repos/{REPO}/deployments/{dep_id}/statuses", "--jq", ".[0]"
            )
            meta["state"] = status.get("state")
            meta["status_created_at"] = status.get("created_at")
            if meta["state"] != "success":
                problems.append(
                    f"Latest deployment {dep_id} state={meta['state']} (expected success)"
                )
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError, ValueError) as exc:
            problems.append(f"GitHub API check failed: {exc}")

        # Check 2: live games.json == committed games.json
        try:
            live_sha = sha256_bytes(fetch_bytes(LIVE_GAMES_URL))
            committed_sha = sha256_bytes(COMMITTED_GAMES.read_bytes())
            meta["live_sha256"] = live_sha
            meta["committed_sha256"] = committed_sha
            if live_sha != committed_sha:
                problems.append(
                    f"games.json hash mismatch — live {live_sha[:12]}… vs committed {committed_sha[:12]}…"
                )
        except (urllib.error.URLError, OSError) as exc:
            problems.append(f"games.json fetch/compare failed: {exc}")

    if problems:
        path = write_alert(meta, problems)
        print(f"NGN health: FAIL — {len(problems)} problem(s); alert -> {path}")
        return 0

    print(
        f"NGN health: OK — deployment {meta.get('deployment_id')} state=success; "
        f"live sha {meta.get('live_sha256', '')[:12]}… matches committed"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

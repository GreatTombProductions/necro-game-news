#!/usr/bin/env python3
"""
Necro Game News — release recon sweep.

Finds necromancy-relevant Steam releases missing from the registry (and the
pending-candidate backlog edges). Read-only: never writes to the registry,
candidates DB, or YAML.

Method (proven 2026-09-26, S49):
  1. Steam store search, sorted by release date, across the necromancy term set.
  2. Dedupe; drop noise (demos, soundtracks, DLC-name patterns).
  3. Diff against registry (both YAMLs) + candidates DB -> unknowns.
  4. Optionally verify unknowns via the appdetails API (type / redirect / blurb).

Usage:
    ./venv/bin/python scripts/recon_releases.py                 # released sweep, table
    ./venv/bin/python scripts/recon_releases.py --verify 12     # + details for top 12 unknowns
    ./venv/bin/python scripts/recon_releases.py --mode comingsoon
    ./venv/bin/python scripts/recon_releases.py --json /tmp/recon.json
    ./venv/bin/python scripts/recon_releases.py --ids 1898610,633580   # appdetails for an explicit id list (research pass)
    ./venv/bin/python scripts/recon_releases.py --ids 1898610 --deep   # richer pull for classification (full desc + genres)

Notes:
  - Steam appdetails may REDIRECT an appid (store moves); the response key wins.
    re-check_registry is reported when the canonical id differs from the requested one.
  - Registry scope: the player raises/commands the dead. "Fight the undead" titles
    are triage noise; verify with the description before proposing a game.
"""

import argparse
import html
import json
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) recon_releases.py"}

PRIMARY_TERMS = ["necromancer", "necromancy", "necromantic", "raise dead",
                 "summon skeleton", "summon undead", "death magic"]
SECONDARY_TERMS = ["undead", "zombie", "skeleton", "lich", "bone", "corpse",
                   "graveyard", "crypt", "tomb", "summon", "reanimat", "resurrect"]
SEARCH_TERMS = PRIMARY_TERMS + ["lich", "dark magic"]

NOISE_PATTERNS = ["demo", "soundtrack", " ost", "artbook", "art book", " dlc",
                  "season pass", "upgrade pack", "content pack", "expansion",
                  "prologue", "companion", "- skins", "skins +", "+ skins",
                  "career pack", "fantasy grounds", "module", "supporter pack",
                  "editor", "sdk", " wallpaper", "avatar", " pack"]


def fetch_search(term: str, start: int, mode: str) -> list:
    params = {"query": "", "start": start, "count": 100, "term": term, "infinite": 1}
    if mode == "comingsoon":
        params["filter"] = "comingsoon"
        params["sort_by"] = "Released_ASC"
    else:
        params["sort_by"] = "Released_DESC"
    url = "https://store.steampowered.com/search/results/?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    rows = []
    for chunk in data.get("results_html", "").split("<a href=")[1:]:
        m = re.search(r"store\.steampowered\.com/app/(\d+)/", chunk)
        n = re.search(r'<span class="title">([^<]+)</span>', chunk)
        rel = re.search(r'search_released responsive_secondrow">\s*([^<]+?)</div>', chunk)
        if m and n:
            rows.append({"appid": int(m.group(1)), "name": n.group(1).strip(),
                         "released": (rel.group(1).strip() if rel else "?")})
    return rows


def sweep(terms: list, pages: int, mode: str, delay: float) -> dict:
    found = {}
    for term in terms:
        for pg in range(pages):
            try:
                rows = fetch_search(term, pg * 100, mode)
            except urllib.error.HTTPError as exc:
                if exc.code != 429:
                    print(f"  ! {term} p{pg}: {exc}", file=sys.stderr)
                    continue
                wait = max(delay * 5, 12)
                print(f"  ! {term} p{pg}: 429, retrying in {wait:.0f}s", file=sys.stderr)
                time.sleep(wait)
                try:
                    rows = fetch_search(term, pg * 100, mode)
                except Exception as exc2:  # noqa: BLE001 - recon should be resilient
                    print(f"  ! {term} p{pg}: {exc2}", file=sys.stderr)
                    continue
            except Exception as exc:  # noqa: BLE001 - recon should be resilient
                print(f"  ! {term} p{pg}: {exc}", file=sys.stderr)
                continue
            for row in rows:
                a = row["appid"]
                if a in found:
                    found[a]["terms"].add(term)
                else:
                    row["terms"] = {term}
                    found[a] = row
            time.sleep(delay)
    return found


def load_tracked() -> tuple:
    reg_ids, cand_ids = set(), set()
    for fname in ("data/games_list.yaml", "data/blood_games_list.yaml"):
        try:
            import yaml  # noqa: PLC0415 - venv dependency
            with open(PROJECT_ROOT / fname) as fh:
                data = yaml.safe_load(fh) or {}
            for g in data.get("games", []):
                if g.get("steam_id"):
                    reg_ids.add(int(g["steam_id"]))
        except Exception as exc:  # noqa: BLE001
            print(f"  ! registry load {fname}: {exc}", file=sys.stderr)
    db = PROJECT_ROOT / "data/necro_games.db"
    if db.exists():
        conn = sqlite3.connect(db)
        cand_ids = {r[0] for r in conn.execute(
            "SELECT steam_id FROM candidates WHERE steam_id IS NOT NULL")}
        conn.close()
    return reg_ids, cand_ids


def is_noise(name: str) -> bool:
    n = name.lower()
    return any(p in n for p in NOISE_PATTERNS)


def year_of(released: str):
    m = re.search(r"(19|20)\d{2}", released)
    return int(m.group(0)) if m else None


def relevance(row: dict) -> str:
    n = row["name"].lower()
    if any(t in n for t in PRIMARY_TERMS):
        return "strong"
    if any(t in n for t in SECONDARY_TERMS):
        return "weak"
    return "search-only"


def verify(appid: int, delay: float) -> dict:
    url = ("https://store.steampowered.com/api/appdetails?"
           + urllib.parse.urlencode({"appids": appid, "cc": "us", "l": "en"}))
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    time.sleep(delay)
    for key, val in data.items():
        if not val.get("success"):
            return {"status": "appdetails-fail"}
        d = val["data"]
        return {
            "status": "ok",
            "canonical_id": int(key),
            "redirected": int(key) != int(appid),
            "type": d.get("type"),
            "name": d.get("name"),
            "released": d.get("release_date", {}).get("date", "?"),
            "desc": (d.get("short_description") or "")[:220].replace("\n", " "),
        }
    return {"status": "empty"}


def verify_deep(appid: int, delay: float) -> dict:
    """Richer appdetails pull for the classification pass: full description + genres."""
    url = ("https://store.steampowered.com/api/appdetails?"
           + urllib.parse.urlencode({"appids": appid, "cc": "us", "l": "en"}))
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    time.sleep(delay)
    for key, val in data.items():
        if not val.get("success"):
            return {"status": "appdetails-fail"}
        d = val["data"]
        desc = d.get("detailed_description") or d.get("short_description") or ""
        desc = re.sub(r"<br\s*/?>", " ", desc)
        desc = re.sub(r"<[^>]+>", " ", desc)
        desc = html.unescape(desc)
        desc = re.sub(r"\s+", " ", desc).strip()
        return {
            "status": "ok",
            "canonical_id": int(key),
            "redirected": int(key) != int(appid),
            "type": d.get("type"),
            "name": d.get("name"),
            "released": d.get("release_date", {}).get("date", "?"),
            "genres": [g.get("description") for g in (d.get("genres") or [])],
            "desc": desc[:550],
        }
    return {"status": "empty"}


def main() -> int:
    ap = argparse.ArgumentParser(description="NGN release recon sweep")
    ap.add_argument("--mode", choices=["released", "comingsoon"], default="released")
    ap.add_argument("--pages", type=int, default=2, help="search pages per term (100/page)")
    ap.add_argument("--terms", help="comma-separated override of search terms")
    ap.add_argument("--verify", type=int, default=0, metavar="N",
                    help="fetch appdetails for top N new candidates")
    ap.add_argument("--ids", help="comma-separated appids: appdetails-verify each (research pass)")
    ap.add_argument("--deep", action="store_true",
                    help="with --ids: richer pull for classification (full desc + genres)")
    ap.add_argument("--json", help="write full results to this path")
    ap.add_argument("--delay", type=float, default=1.0)
    args = ap.parse_args()

    if args.ids:
        ids = [int(x) for x in args.ids.split(",") if x.strip()]
        out = []
        fetcher = verify_deep if args.deep else verify
        print(f"== appdetails verify: {len(ids)} ids{' (deep)' if args.deep else ''} ==")
        for appid in ids:
            v = fetcher(appid, args.delay)
            out.append({"requested_id": appid, **v})
            if v.get("status") == "ok":
                flag = f" -> {v['canonical_id']} REDIRECT" if v.get("redirected") else ""
                extra = f" | {', '.join(v['genres'])}" if v.get("genres") else ""
                print(f"  {appid}{flag} | {v['type']} | {v['name']} | {v['released']}{extra}")
                print(f"      {v['desc']}")
            else:
                print(f"  {appid} | {v.get('status')}")
        if args.json:
            Path(args.json).write_text(json.dumps(out, indent=1))
            print(f"\nwrote {args.json}")
        return 0

    terms = args.terms.split(",") if args.terms else SEARCH_TERMS
    print(f"== recon sweep | mode={args.mode} | terms={len(terms)} | pages={args.pages} ==")

    found = sweep(terms, args.pages, args.mode, args.delay)
    reg_ids, cand_ids = load_tracked()
    tracked = reg_ids | cand_ids
    print(f"   search rows (unique apps): {len(found)}")
    print(f"   registry ids: {len(reg_ids)} | candidates: {len(cand_ids)}")

    unknown = [r for a, r in found.items() if a not in tracked]
    clean = [r for r in unknown if not is_noise(r["name"])]
    noisy = len(unknown) - len(clean)
    for r in clean:
        r["relevance"] = relevance(r)
    strong = [r for r in clean if r["relevance"] == "strong"]
    weak = [r for r in clean if r["relevance"] == "weak" and
            (args.mode == "comingsoon" or (year_of(r["released"]) or 0) >= 2025)]
    print(f"   unknown: {len(unknown)} | noise-filtered: {noisy} | "
          f"strong: {len(strong)} | weak (recent): {len(weak)}")

    def show(rows, label):
        if not rows:
            return
        print(f"\n-- {label} --")
        rows = sorted(rows, key=lambda r: r["appid"], reverse=True)
        for r in rows:
            terms_s = ",".join(sorted(r["terms"]))[:40]
            print(f"  {r['appid']:>9} | {r['released'][:16]:<16} | {r['name'][:64]:<64} | {terms_s}")
        return rows

    strong_s = show(strong, "STRONG — primary necromancy term in name (verify each)")
    weak_s = show(weak, "WEAK — secondary term in name, recent (triage)")

    verified = []
    if args.verify and (strong_s or weak_s):
        pool = (strong_s or []) + (weak_s or [])
        print(f"\n== appdetails verify: top {min(args.verify, len(pool))} ==")
        for r in pool[:args.verify]:
            v = verify(r["appid"], args.delay)
            r["verify"] = v
            if v.get("status") == "ok":
                flag = "REDIRECT" if v["redirected"] else ""
                in_new = " [canonical id ALSO untracked]" if (
                    v["redirected"] and v["canonical_id"] not in tracked) else ""
                if v["redirected"]:
                    print(f"  {r['appid']} -> {v['canonical_id']} {flag}{in_new} | {v['type']} | {v['name']} | {v['released']}")
                else:
                    print(f"  {r['appid']} | {v['type']} | {v['name']} | {v['released']}")
                print(f"      {v['desc']}")
            else:
                print(f"  {r['appid']} | {v.get('status')}")
            verified.append(r)

    if args.json:
        out = {"mode": args.mode, "terms": terms, "strong": strong_s, "weak": weak_s,
               "unknown_total": len(unknown), "verified": verified}
        # sets are not JSON-serializable
        Path(args.json).write_text(json.dumps(out, indent=1, default=list))
        print(f"\nwrote {args.json}")

    print("\nTriage reminder: keep only games where the player RAISES/COMMANDS the dead; "
          "check type=dlc (skip), and the description (store text is the primary source).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Offline regressions for S55 recon evidence and safe approved-add publication.

Run: ./venv/bin/python -m unittest discover -s scripts -p test_recon_contract.py
"""
import io
import json
import subprocess
import unittest
from unittest.mock import patch

import add_game_to_yaml as add
import recon_releases as recon


class EvidenceTests(unittest.TestCase):
    # Regression: S55 found --deep silently cut evidence at 550 characters;
    # date labels also could not prove whether a watchlisted game had released.
    def response(self, **overrides):
        data = {
            "type": "game", "name": "Fixture",
            "release_date": {"date": "October 2026", "coming_soon": True},
            "detailed_description": "<p>" + "A" * 600 + "</p>Raise the dead &amp; command them.",
        }
        data.update(overrides)
        return io.BytesIO(json.dumps({"42": {"success": True, "data": data}}).encode())

    def test_deep_retains_tail_and_release_gate(self):
        with patch.object(recon.urllib.request, "urlopen", return_value=self.response()), \
                patch.object(recon.time, "sleep"):
            result = recon.verify_deep(42, 1)
        self.assertIn("Raise the dead & command them.", result["desc"])
        self.assertGreater(len(result["desc"]), 550)
        self.assertTrue(result["coming_soon"])
        self.assertEqual(result["canonical_id"], 42)

    # Invariant: DLC triage needs the parent id; absent release evidence stays
    # unknown, not false/released. Both modes must preserve these API facts.
    def test_dlc_parent_and_unknown_release(self):
        for fetcher in (recon.verify, recon.verify_deep):
            with self.subTest(fetcher=fetcher.__name__), \
                    patch.object(recon.urllib.request, "urlopen", return_value=self.response(
                        type="dlc", release_date={}, fullgame={"appid": "7", "name": "Base"})), \
                    patch.object(recon.time, "sleep"):
                result = fetcher(42, 1)
            self.assertEqual(result["fullgame"]["appid"], "7")
            self.assertIsNone(result["coming_soon"])


class PublishTests(unittest.TestCase):
    # Invariant: shared-index sibling work cannot enter an approved registry
    # update, and a failed commit cannot be followed by a push/success claim.
    def test_publish_uses_isolated_commit_with_stats(self):
        with patch.object(subprocess, "run") as run:
            self.assertTrue(add.deploy())
        commands = [call.args[0] for call in run.call_args_list]
        commit = commands[1]
        self.assertEqual(commit[:2], ["greattomb", "git-commit-isolated"])
        self.assertIn("./frontend/public/data/stats.json", commit)
        self.assertIn("./frontend/public/data/blood_stats.json", commit)
        self.assertEqual(commands[2], ["git", "push", "origin", "main"])
        self.assertTrue(run.call_args_list[1].kwargs["check"])

    def test_failed_commit_stops_before_push(self):
        with patch.object(subprocess, "run", side_effect=[
            subprocess.CompletedProcess([], 0), subprocess.CalledProcessError(1, "commit")
        ]) as run:
            self.assertFalse(add.deploy())
        self.assertEqual(run.call_count, 2)


if __name__ == "__main__":
    unittest.main()

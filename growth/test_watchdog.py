#!/usr/bin/env python3
"""Tests for the watchdog's snapshot-freshness check.

These exist because of what happened on 2026-08-21. The 06:00 run went all the
way through: it measured, it built, it rebuilt the sitemap, and
`publish_state.sh` pushed a commit. But `snapshot.write()` raised, and because
`cmd_daily` wraps it in a try/except so a snapshot bug cannot take down the
site build, the run logged one line and carried on. The published commit
touched `sitemap.xml` alone — no `growth/snapshot.json`, no `growth/JOURNAL.md`
— for the first time in the engine's history.

Nobody was told. The 11:00 watchdog checked build staleness, failed build
steps and Search Console, found the engine perfectly alive, and stayed quiet.
The cloud review agent, whose only view of this machine is that one file, spent
the morning reviewing the previous day's numbers.

The check compares the snapshot against the build that should have produced it,
not against the calendar, so it fires on exactly that shape and stays silent
when the engine simply did not run — the build-staleness check owns that case.

Run: python3 -m growth.test_watchdog   (from the repo root)
"""
import json
import os
import tempfile
import unittest
from unittest import mock

import growth_daily as G
from . import snapshot


class SnapshotFreshnessTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, "snapshot.json")
        p = mock.patch.object(snapshot, "SNAPSHOT_PATH", self.path)
        p.start()
        self.addCleanup(p.stop)

    def _write(self, date):
        with open(self.path, "w") as f:
            json.dump({"date": date, "site": "nemoseamlessgutter.com"}, f)

    def test_fresh_snapshot_alongside_todays_build_is_silent(self):
        self._write("2026-08-20")
        self.assertEqual(G._snapshot_problems("2026-08-20", 0), [])

    def test_the_2026_08_21_failure_is_caught(self):
        """The build completed today; the snapshot still reads yesterday."""
        self._write("2026-08-20")
        problems = G._snapshot_problems("2026-08-21", 0)
        self.assertEqual(len(problems), 1)
        self.assertIn("2026-08-20", problems[0])
        self.assertIn("2026-08-21", problems[0])
        self.assertIn("nemo-growth.log", problems[0])

    def test_a_missing_snapshot_file_is_caught(self):
        problems = G._snapshot_problems("2026-08-21", 0)
        self.assertEqual(len(problems), 1)
        self.assertIn("no date", problems[0])

    def test_unreadable_snapshot_is_reported_not_raised(self):
        with open(self.path, "w") as f:
            f.write("{ this is not json")
        problems = G._snapshot_problems("2026-08-21", 0)
        self.assertEqual(len(problems), 1)
        self.assertIn("cannot be read", problems[0])

    def test_stays_quiet_when_the_engine_did_not_run_at_all(self):
        """A dead cron is the build check's alarm to raise, not this one.

        Otherwise every morning of an outage mails two problems describing one
        cause, and the snapshot line is the less accurate of the pair."""
        self._write("2026-08-14")
        self.assertEqual(G._snapshot_problems("2026-08-14", 7), [])

    def test_stays_quiet_when_the_build_date_is_unknown(self):
        """`when` is None before the engine has ever recorded a build; the
        build check already says so in plainer words."""
        self._write("2026-08-20")
        self.assertEqual(G._snapshot_problems(None, None), [])


if __name__ == "__main__":
    unittest.main()

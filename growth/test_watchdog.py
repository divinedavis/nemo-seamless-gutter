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

`WatchdogStalenessTest` covers that build-staleness check, and exists because
of 2026-10-13. That morning the engine produced nothing at all: no snapshot was
written, so `publish_state.sh` found nothing changed and exited 0 without a
commit, and the repository's newest state stayed dated 2026-10-12. The watchdog
ran and said "ok — last build 2026-10-12", because its threshold was two days
and only one had passed. One missed morning is the whole failure, so one missed
morning is now the alarm.

Run: python3 -m growth.test_watchdog   (from the repo root)
"""
import datetime
import json
import os
import tempfile
import unittest
from unittest import mock

import growth_daily as G
from . import ledger, snapshot


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


class WatchdogStalenessTest(unittest.TestCase):
    """`cmd_watchdog`'s build-staleness branch, end to end.

    These assert on the alert text and not only on the exit code, because the
    exit code goes to a log nobody reads and the text is what the person who
    has to fix it gets.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, "snapshot.json")
        p = mock.patch.object(snapshot, "SNAPSHOT_PATH", self.path)
        p.start()
        self.addCleanup(p.stop)
        self.lines = []
        p2 = mock.patch.object(G, "log", self.lines.append)
        p2.start()
        self.addCleanup(p2.stop)

    def _run(self, last_build, snap_date=None, gsc_last=None, today=None):
        """Run cmd_watchdog with a fake ledger and a fake calendar."""
        today = today or "2026-10-13"
        if snap_date:
            with open(self.path, "w") as f:
                json.dump({"date": snap_date}, f)
        state = {"last_build": last_build, "gsc_last": gsc_last}
        args = mock.Mock(email=None, dry_run=True)
        real_date = datetime.date

        class FakeDate(real_date):
            @classmethod
            def today(cls):
                return real_date.fromisoformat(today)

        with mock.patch.object(ledger, "get_state",
                               lambda k, default=None: state.get(k, default)), \
             mock.patch.object(datetime, "date", FakeDate):
            rc = G.cmd_watchdog(args)
        return rc, [str(x) for x in self.lines]

    def test_a_healthy_morning_is_silent(self):
        """The 06:00 run completed today and wrote a matching snapshot."""
        rc, lines = self._run({"date": "2026-10-13", "log": [{"slug": "a", "ok": True}]},
                              snap_date="2026-10-13")
        self.assertEqual(rc, 0)
        self.assertEqual(len(lines), 1)
        self.assertIn("ok — last build 2026-10-13", lines[0])

    def test_the_2026_10_13_failure_is_caught_on_the_first_morning(self):
        """No build today, last build yesterday: one day of silence alarms.

        Under the old `>= 2` threshold this returned 0 and logged "ok".
        """
        rc, lines = self._run({"date": "2026-10-12", "log": []},
                              snap_date="2026-10-12")
        self.assertEqual(rc, 1)
        body = " ".join(lines)
        self.assertIn("No completed build today", body)
        self.assertIn("2026-10-12", body)

    def test_the_one_day_alert_carries_the_diagnostic(self):
        """Three causes produce this same silence and need different
        responses, and the alert is where the reader learns to tell them
        apart: a crash before snapshot.write(), a cron that never ran, and a
        push that failed with the state here intact."""
        _, lines = self._run({"date": "2026-10-12"}, snap_date="2026-10-12")
        body = " ".join(lines)
        self.assertIn("nemo-growth.log", body)
        self.assertIn("publish: nothing changed", body)
        self.assertIn("Traceback", body)
        self.assertIn("only the push to GitHub failed", body)

    def test_one_missed_morning_reports_one_problem_not_two(self):
        """The snapshot check stays out of it: `_snapshot_problems` is silent
        unless the build completed today, so an outage mails one line about one
        cause rather than two about the same one."""
        _, lines = self._run({"date": "2026-10-12"}, snap_date="2026-10-12")
        self.assertEqual(len(lines), 1)

    def test_a_longer_outage_keeps_the_multi_day_wording(self):
        rc, lines = self._run({"date": "2026-10-06"}, snap_date="2026-10-06")
        self.assertEqual(rc, 1)
        body = " ".join(lines)
        self.assertIn("7 days", body)
        self.assertIn("not producing runs", body)
        self.assertNotIn("No completed build today", body)

    def test_a_never_run_engine_says_so_in_plainer_words(self):
        rc, lines = self._run({})
        self.assertEqual(rc, 1)
        self.assertIn("never recorded a completed build", " ".join(lines))

    def test_todays_failed_steps_are_still_reported(self):
        """The dead-balance mornings: the run completed, a technique did not."""
        rc, lines = self._run(
            {"date": "2026-10-13",
             "log": [{"slug": "strengthen_pages", "ok": False,
                      "detail": "credit balance is too low"}]},
            snap_date="2026-10-13")
        self.assertEqual(rc, 1)
        body = " ".join(lines)
        self.assertIn("strengthen_pages", body)
        self.assertIn("credit balance", body)

    def test_a_failing_search_console_sync_is_reported(self):
        rc, lines = self._run({"date": "2026-10-13"}, snap_date="2026-10-13",
                              gsc_last={"ok": False, "detail": "token expired"})
        self.assertEqual(rc, 1)
        self.assertIn("token expired", " ".join(lines))


if __name__ == "__main__":
    unittest.main()

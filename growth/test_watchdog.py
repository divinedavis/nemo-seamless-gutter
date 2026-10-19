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
        git step that failed with the state here intact."""
        _, lines = self._run({"date": "2026-10-12"}, snap_date="2026-10-12")
        body = " ".join(lines)
        self.assertIn("nemo-growth.log", body)
        self.assertIn("publish: nothing changed", body)
        self.assertIn("snapshot: FAILED", body)
        self.assertIn("Traceback", body)
        self.assertIn("permission denied", body)

    def test_the_alert_does_not_describe_a_log_shape_that_cannot_occur(self):
        """Until 2026-10-19 the alert told the reader to look for "a git or
        ssh error after a 'publish:' line", which no credential failure can
        produce: `publish_state.sh` is `set -euo pipefail` and its only
        success echo is the line after the push, so a failed push — and a
        dead deploy key, which dies at the `git fetch` ahead of every echo —
        both leave no `publish:` line at all. growth/README.md was corrected
        on 2026-10-18; this alert, which is the copy the reader actually
        gets, kept the repudiated version for a day longer. This test is what
        keeps the two from drifting again."""
        for last_build in ("2026-10-12", "2026-10-06"):
            with self.subTest(last_build=last_build):
                _, lines = self._run({"date": last_build}, snap_date=last_build)
                body = " ".join(lines)
                self.assertNotIn("after a 'publish:' line means", body)
                self.assertIn("Do not expect git's error to follow a "
                              "'publish:' line", body)

    def test_neither_alert_claims_the_frozen_file_shape_separates_the_causes(self):
        """A frozen snapshot.json beside engine-run journal entries that stop
        on the same day fits both the snapshot-FAILED case and the raised-
        before-the-snapshot-block case, because the second never calls either
        write. The alert has to say so, because that shape is the only thing
        visible from outside the droplet and reading it as the first case
        skips a backfill the second case needs."""
        _, lines = self._run({"date": "2026-10-06"}, snap_date="2026-10-06")
        body = " ".join(lines)
        self.assertIn("fits (1) and (2)", body)
        self.assertIn("only rules out (2)", body)

    def test_one_missed_morning_reports_one_problem_not_two(self):
        """The snapshot check stays out of it: `_snapshot_problems` is silent
        unless the build completed today, so an outage mails one line about one
        cause rather than two about the same one."""
        _, lines = self._run({"date": "2026-10-12"}, snap_date="2026-10-12")
        self.assertEqual(len(lines), 1)

    def test_a_longer_outage_keeps_its_own_wording_and_the_day_count(self):
        rc, lines = self._run({"date": "2026-10-06"}, snap_date="2026-10-06")
        self.assertEqual(rc, 1)
        body = " ".join(lines)
        self.assertIn("7 days", body)
        self.assertIn("2026-10-06", body)
        self.assertNotIn("No completed build today", body)

    def test_a_longer_outage_carries_the_diagnostic_too(self):
        """The branch that fires on day 2 and after is the one that fires on
        every morning of a real outage, and the only one `--email` will mail
        once the flag is back on the 11:00 cron entry. Until 2026-10-19 it
        dropped the diagnostic entirely — so the alert got terser exactly as
        the outage got long enough for somebody to act on it."""
        _, lines = self._run({"date": "2026-10-06"}, snap_date="2026-10-06")
        body = " ".join(lines)
        self.assertIn("publish: nothing changed", body)
        self.assertIn("snapshot: FAILED", body)
        self.assertIn("Traceback", body)
        self.assertIn("permission denied", body)
        self.assertIn("systemctl status cron", body)

    def test_a_longer_outage_does_not_assert_the_cron_as_the_cause(self):
        """The old multi-day wording was "The 06:00 cron is not producing
        runs." That is one of three indistinguishable causes stated as fact,
        and it is the one that sends the reader to `systemctl status cron`
        for what may be a dead deploy key or a full disk — the same
        misattribution growth/README.md was corrected for on 2026-10-18."""
        _, lines = self._run({"date": "2026-10-06"}, snap_date="2026-10-06")
        body = " ".join(lines)
        self.assertNotIn("The 06:00 cron is not producing runs", body)

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

"""Tests for the GitHub-side state-freshness check."""
import datetime
import io
import json
import os
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from growth import freshness  # noqa: E402

TODAY = datetime.date(2026, 10, 21)


def _snapshot(tmpdir, body):
    path = os.path.join(tmpdir, "snapshot.json")
    with open(path, "w") as f:
        f.write(body)
    return path


class StaleDaysTests(unittest.TestCase):
    def test_counts_whole_days(self):
        self.assertEqual(freshness.stale_days("2026-10-12", TODAY), 9)
        self.assertEqual(freshness.stale_days("2026-10-21", TODAY), 0)

    def test_unreadable_date_is_none_not_zero(self):
        # None has to mean "cannot tell" rather than "fresh" — an unreadable
        # date is the state a frozen file is in.
        for bad in (None, "", "yesterday", "2026-13-40", 20261012):
            self.assertIsNone(freshness.stale_days(bad, TODAY), bad)


class CheckTests(unittest.TestCase):
    def test_today_is_ok(self):
        with tempfile.TemporaryDirectory() as d:
            p = _snapshot(d, json.dumps({"date": "2026-10-21"}))
            ok, msg = freshness.check(p, TODAY)
        self.assertTrue(ok)
        self.assertIn("2026-10-21", msg)

    def test_one_missed_morning_fails(self):
        # Same bar as cmd_watchdog: one missed morning is already the alarm,
        # because the review agent spends it reading stale numbers.
        with tempfile.TemporaryDirectory() as d:
            p = _snapshot(d, json.dumps({"date": "2026-10-20"}))
            ok, msg = freshness.check(p, TODAY)
        self.assertFalse(ok)
        self.assertIn("1 day(s) stale", msg)
        self.assertIn("1 morning", msg)

    def test_long_outage_reports_its_length(self):
        with tempfile.TemporaryDirectory() as d:
            p = _snapshot(d, json.dumps({"date": "2026-10-12"}))
            ok, msg = freshness.check(p, TODAY)
        self.assertFalse(ok)
        self.assertIn("9 day(s) stale", msg)
        self.assertIn("9 consecutive mornings", msg)

    def test_future_date_is_not_an_alarm(self):
        # A snapshot dated ahead of the runner's clock still arrived.
        with tempfile.TemporaryDirectory() as d:
            p = _snapshot(d, json.dumps({"date": "2026-10-22"}))
            ok, _ = freshness.check(p, TODAY)
        self.assertTrue(ok)

    def test_missing_file_fails(self):
        with tempfile.TemporaryDirectory() as d:
            ok, msg = freshness.check(os.path.join(d, "nope.json"), TODAY)
        self.assertFalse(ok)
        self.assertIn("never published", msg)

    def test_unparsable_file_fails(self):
        with tempfile.TemporaryDirectory() as d:
            p = _snapshot(d, "{not json")
            ok, msg = freshness.check(p, TODAY)
        self.assertFalse(ok)
        self.assertIn("cannot be read", msg)

    def test_missing_date_field_fails(self):
        with tempfile.TemporaryDirectory() as d:
            p = _snapshot(d, json.dumps({"site": "nemoseamlessgutter.com"}))
            ok, msg = freshness.check(p, TODAY)
        self.assertFalse(ok)
        self.assertIn("no readable date", msg)

    def test_stale_message_carries_the_watchdog_diagnostic(self):
        # The three-cause text is growth_daily's, imported rather than copied,
        # so that this check and the 11:00 alert cannot drift apart.
        import growth_daily
        with tempfile.TemporaryDirectory() as d:
            p = _snapshot(d, json.dumps({"date": "2026-10-12"}))
            _, msg = freshness.check(p, TODAY)
        self.assertIn(growth_daily._UNPUBLISHED_MORNING_DIAGNOSTIC, msg)


class PerishableTests(unittest.TestCase):
    """The one fact in the alarm that expires.

    Rank history survives an outage (Search Console backfills ~16 months);
    nginx traffic history does not, because `measure` records yesterday only
    and the series is accumulated. These assert the arithmetic of that loss,
    which three journal entries got wrong by a day before it was written down.
    """

    DAY25 = datetime.date(2026, 11, 6)

    def test_first_missing_day_is_the_snapshot_date_not_the_day_after(self):
        # A snapshot dated D holds data through D-1, because the D run records
        # yesterday. Counting from D+1 undercounts the hole by a morning.
        msg = freshness.perishable("2026-10-12", self.DAY25)
        self.assertIn("25 mornings", msg)
        self.assertIn("2026-10-12 to 2026-11-05", msg)

    def test_splits_lost_from_still_recoverable(self):
        msg = freshness.perishable("2026-10-12", self.DAY25)
        self.assertIn("about 11 of them are already past recovery", msg)
        self.assertIn("14 are still recoverable today", msg)

    def test_long_outage_states_a_per_morning_deadline_not_a_cutoff(self):
        # Replaces test_names_the_date_the_whole_hole_expires, which asserted
        # "After 2026-11-19 none of this hole can be recovered by anything".
        # That sentence was true of the hole as it stood that day and false as
        # a deadline: see test_the_stated_expiry_recedes_one_day_per_day. The
        # behaviour it pinned was deliberately removed, so the test is replaced
        # rather than skipped.
        msg = freshness.perishable("2026-10-12", self.DAY25)
        self.assertIn("no single cutoff to plan around", msg)
        self.assertIn("2026-11-19 is when the newest missing morning ages out",
                      msg)
        self.assertIn("moves a day later for every day", msg)
        # The oldest morning still readable, which is the day actually at risk.
        self.assertIn("2026-10-23 is the oldest still readable", msg)
        self.assertNotIn("none of this hole", msg)

    def test_the_stated_expiry_recedes_one_day_per_day(self):
        # The defect this file now pins. `expires` is the NEWEST missing
        # morning plus the window, so while the outage continues it advances
        # with the calendar and can never be reached: a reader who treats it as
        # a date to act by has been handed permanent slack. Checked across a
        # quarter rather than at two points.
        prev = None
        for d in range(20, 110):
            today = datetime.date(2026, 10, 12) + datetime.timedelta(days=d)
            msg = freshness.perishable("2026-10-12", today)
            m = re.search(r"(\d{4}-\d{2}-\d{2}) is when the newest missing "
                          r"morning ages out", msg)
            self.assertIsNotNone(m, msg)
            got = datetime.date.fromisoformat(m.group(1))
            self.assertEqual(
                got, today + datetime.timedelta(
                    days=freshness.ASSUMED_LOG_RETENTION_DAYS - 1),
                f"day {d}")
            if prev is not None:
                self.assertEqual((got - prev).days, 1, f"day {d}")
            prev = got

    def test_long_outage_says_waiting_changes_which_days_not_how_many(self):
        # Past the retention window `recoverable` is pinned at the window, so
        # the only thing delay changes is the identity of the mornings. An
        # alarm that reports a constant 14 without saying so reads as stable
        # when it is in fact a conveyor belt.
        for d in (25, 40, 90):
            msg = freshness.perishable(
                "2026-10-12",
                datetime.date(2026, 10, 12) + datetime.timedelta(days=d))
            self.assertIn("capped by the window", msg)
            self.assertIn("only which ones", msg)
            self.assertIn(
                f"({freshness.ASSUMED_LOG_RETENTION_DAYS}, capped", msg)

    def test_short_outage_keeps_its_genuine_cutoff(self):
        # Before the window closes the whole hole really does have one date
        # after which none of it survives, and that date does not recede while
        # nothing has been lost yet. The wording stays there.
        msg = freshness.perishable("2026-10-12", datetime.date(2026, 10, 20))
        self.assertIn("After 2026-11-02 none of this hole", msg)
        self.assertNotIn("no single cutoff", msg)

    def test_carries_a_runnable_backfill_command(self):
        msg = freshness.perishable("2026-10-12", self.DAY25)
        self.assertIn("measure --days 25", msg)

    def test_says_the_retention_figure_is_an_estimate(self):
        # It is the packaged default, not a reading off the droplet's disk, and
        # the alarm has to say so or the deadline reads as measured.
        msg = freshness.perishable("2026-10-12", self.DAY25)
        self.assertIn("ls -la /var/log/nginx/nemo-access.log*", msg)
        self.assertIn("packaged default, not a measurement", msg)

    def test_short_outage_has_lost_nothing_yet(self):
        msg = freshness.perishable("2026-10-12", datetime.date(2026, 10, 13))
        self.assertIn("1 mornings", msg)
        self.assertNotIn("past recovery", msg)
        self.assertIn("all 1 are still recoverable", msg)
        self.assertIn("start expiring one per day from 2026-10-26", msg)

    def test_loss_begins_exactly_one_retention_window_in(self):
        # On the boundary day nothing is lost yet; the next day loses one.
        on = freshness.perishable("2026-10-12", datetime.date(2026, 10, 26))
        self.assertNotIn("past recovery", on)
        after = freshness.perishable("2026-10-12", datetime.date(2026, 10, 27))
        self.assertIn("about 1 of them are already past recovery", after)

    def test_lost_count_never_falls_and_recoverable_never_exceeds_window(self):
        # Two invariants worth pinning, because both would be wrong in the
        # direction that reassures: a loss count that can fall would let the
        # alarm walk back a permanent loss, and a recoverable count above the
        # retention window would promise a backfill that cannot deliver.
        start = datetime.date(2026, 10, 12)
        seen_lost = 0
        for d in range(1, 120):
            msg = freshness.perishable(
                "2026-10-12", start + datetime.timedelta(days=d))
            self.assertTrue(msg)
            m = re.search(r"about (\d+) of them are already past", msg)
            lost = int(m.group(1)) if m else 0
            self.assertGreaterEqual(lost, seen_lost, f"day {d}: {lost}")
            seen_lost = lost
            r = re.search(r"(?:all )?(\d+) are still recoverable", msg)
            self.assertIsNotNone(r, msg)
            self.assertLessEqual(
                int(r.group(1)), freshness.ASSUMED_LOG_RETENTION_DAYS,
                f"day {d}: {msg}")

    def test_nothing_missing_yields_no_sentence(self):
        # Defensive: check() only calls this when the file is stale.
        self.assertEqual(
            freshness.perishable("2026-11-06", datetime.date(2026, 11, 6)), "")

    def test_stale_message_carries_the_perishable_deadline(self):
        # The point of the change: the delivered channel states the deadline.
        with tempfile.TemporaryDirectory() as d:
            p = _snapshot(d, json.dumps({"date": "2026-10-12"}))
            _, msg = freshness.check(p, self.DAY25)
        self.assertIn("being deleted", msg)
        self.assertIn("no single cutoff to plan around", msg)
        self.assertIn("is the oldest still readable", msg)


class MainTests(unittest.TestCase):
    def setUp(self):
        self._env = os.environ.get("GITHUB_ACTIONS")
        self._path = freshness.SNAPSHOT_PATH
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.addCleanup(setattr, freshness, "SNAPSHOT_PATH", self._path)
        self.addCleanup(self._restore_env)

    def _restore_env(self):
        if self._env is None:
            os.environ.pop("GITHUB_ACTIONS", None)
        else:
            os.environ["GITHUB_ACTIONS"] = self._env

    def _run(self, body):
        freshness.SNAPSHOT_PATH = _snapshot(self._dir.name, body)
        out = io.StringIO()
        with redirect_stdout(out):
            code = freshness.main([])
        return code, out.getvalue()

    def test_stale_exits_non_zero_with_an_annotation(self):
        os.environ["GITHUB_ACTIONS"] = "true"
        code, out = self._run(json.dumps({"date": "2026-01-01"}))
        self.assertEqual(code, 1)
        self.assertTrue(out.startswith("::error::state-freshness:"), out[:60])

    def test_no_annotation_prefix_outside_actions(self):
        os.environ.pop("GITHUB_ACTIONS", None)
        code, out = self._run(json.dumps({"date": "2026-01-01"}))
        self.assertEqual(code, 1)
        self.assertTrue(out.startswith("state-freshness:"), out[:60])

    def test_fresh_exits_zero(self):
        os.environ.pop("GITHUB_ACTIONS", None)
        code, out = self._run(json.dumps(
            {"date": datetime.date.today().isoformat()}))
        self.assertEqual(code, 0)
        self.assertIn("ok", out)


if __name__ == "__main__":
    unittest.main()

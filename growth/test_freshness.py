"""Tests for the GitHub-side state-freshness check."""
import datetime
import io
import json
import os
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

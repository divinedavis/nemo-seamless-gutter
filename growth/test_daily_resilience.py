#!/usr/bin/env python3
"""Tests that a crash in one build step cannot cost the morning its outputs.

These exist because of 2026-10-13 and 2026-10-14. On both mornings the engine
published nothing at all — no `Publish growth state for <date>` commit, and a
`growth/snapshot.json` still dated 2026-10-12 more than five hours past a
window that had held to within eight minutes for the previous eighteen days.

The mechanism was two silences meeting. `cmd_daily` called `seed.run()`,
`cmd_measure`, `cmd_review` and `cmd_build` unwrapped, so a raise in any of the
four returned before `snapshot.write()`; and `publish_state.sh` exits 0 printing
"nothing changed" when the clone has no diff, so the push that would have
carried the bad news had nothing to carry. The cloud review agent's only view of
this machine is those two files, so it read 2026-10-12's numbers twice and could
not see why.

The engine had already learned this once, at a different point in the same
function: on 2026-08-21 an unwrapped `scout.run()` raised and the morning wrote
pages for a week without ever writing a snapshot. That crash is wrapped. These
tests cover the other four steps, so a failure becomes a recorded `FAILED` row
the next run can act on rather than a day with no numbers in it.

Run: python3 -m growth.test_daily_resilience   (from the repo root)
"""
import argparse
import unittest
from unittest import mock

import growth_daily as G


def _args():
    return argparse.Namespace(command="daily", docroot="/nonexistent", days=1,
                              email=None, owner_email=None, dry_run=True)


class DailyStepFailureTest(unittest.TestCase):
    """Each wrapped step fails alone; the snapshot and report still happen."""

    def setUp(self):
        # Everything downstream of the four steps is stubbed: these tests are
        # about control flow through cmd_daily, not about what the steps do.
        for name, ret in (("cmd_measure", None), ("cmd_review", {"actions": []}),
                          ("cmd_build", [{"ok": True, "slug": "area_pages"}]),
                          ("cmd_scout", {"ok": True}),
                          ("cmd_report", "report text")):
            p = mock.patch.object(G, name, mock.Mock(return_value=ret))
            setattr(self, name, p.start())
            self.addCleanup(p.stop)
        for mod, attr in (("seed", "run"), ("keywords", "check_coverage")):
            p = mock.patch.object(getattr(G, mod), attr, mock.Mock())
            p.start()
            self.addCleanup(p.stop)

    def _run_log(self):
        """The run_log cmd_daily handed the report."""
        return self.cmd_report.call_args.kwargs["run_log"]

    def test_a_healthy_run_reports_the_build_log_unchanged(self):
        self.assertEqual(G.cmd_daily(_args()), 0)
        self.assertEqual(self._run_log(), [{"ok": True, "slug": "area_pages"}])

    def test_measure_crashing_still_reaches_the_report(self):
        self.cmd_measure.side_effect = RuntimeError("no nginx log")
        self.assertEqual(G.cmd_daily(_args()), 0)
        self.cmd_report.assert_called_once()
        rows = self._run_log()
        self.assertIn({"ok": False, "slug": "measure",
                       "detail": "aborted the morning: no nginx log"}, rows)
        # The build still ran: one failure must not cascade.
        self.cmd_build.assert_called_once()
        self.assertIn({"ok": True, "slug": "area_pages"}, rows)

    def test_build_crashing_still_reaches_the_report(self):
        self.cmd_build.side_effect = RuntimeError("coverage blew up")
        self.assertEqual(G.cmd_daily(_args()), 0)
        self.cmd_report.assert_called_once()
        self.assertEqual(self._run_log(),
                         [{"ok": False, "slug": "build",
                           "detail": "aborted the morning: coverage blew up"}])

    def test_review_crashing_leaves_review_out_none(self):
        self.cmd_review.side_effect = RuntimeError("ledger unreadable")
        self.assertEqual(G.cmd_daily(_args()), 0)
        self.assertIsNone(self.cmd_report.call_args.kwargs["review_out"])
        self.assertIn({"ok": False, "slug": "review",
                       "detail": "aborted the morning: ledger unreadable"},
                      self._run_log())

    def test_seed_crashing_is_recorded_and_the_morning_continues(self):
        G.seed.run.side_effect = RuntimeError("disk full")
        self.assertEqual(G.cmd_daily(_args()), 0)
        self.assertIn({"ok": False, "slug": "seed",
                       "detail": "aborted the morning: disk full"},
                      self._run_log())

    def test_every_step_crashing_still_produces_a_report(self):
        """The worst case: the reader still gets four named failures."""
        G.seed.run.side_effect = RuntimeError("a")
        self.cmd_measure.side_effect = RuntimeError("b")
        self.cmd_review.side_effect = RuntimeError("c")
        self.cmd_build.side_effect = RuntimeError("d")
        self.assertEqual(G.cmd_daily(_args()), 0)
        self.cmd_report.assert_called_once()
        self.assertEqual([r["slug"] for r in self._run_log()],
                         ["seed", "measure", "review", "build"])
        self.assertTrue(all(r["ok"] is False for r in self._run_log()))


class LastBuildDateTest(unittest.TestCase):
    """A crashed build must not stamp last_build with today's date.

    The 11:00 watchdog decides a morning went missing by comparing
    `last_build.date` against today. If cmd_daily wrote a fresh date on the way
    past a crash, that check would read a healthy engine on exactly the morning
    it is meant to catch — so cmd_daily leaves the date to cmd_build, which
    only reaches `ledger.set_state` when the build actually finished.
    """

    def test_cmd_daily_never_writes_last_build_itself(self):
        import inspect
        code = "\n".join(l for l in inspect.getsource(G.cmd_daily).splitlines()
                         if not l.lstrip().startswith("#"))
        self.assertNotIn("last_build", code)


if __name__ == "__main__":
    unittest.main()

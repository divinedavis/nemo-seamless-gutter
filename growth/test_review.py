#!/usr/bin/env python3
"""Tests for the grace-period clock in review.py.

These exist because of a real state in the ledger on 2026-08-02: T014
(geo_answer_first_content_pass) had status "active" and `activated: null`. It
had been building pages every morning since 07-27, and `_days_active` read the
missing field as zero, so `evaluate` returned "only 0d active — under the 30d
grace period" and would have returned that forever. A technique that can never
leave the grace period can never be judged, retired, or found redundant, which
is the entire purpose of this module.

`set_status` stamps `activated`, so the normal path was never broken; the hole
was for techniques that arrive active by some other route.

Run: python3 -m growth.test_review   (from the repo root)
"""
import datetime
import unittest

from . import review as R


def _tech(**kw):
    t = {"id": "T999", "slug": "some_technique", "name": "Some technique",
         "status": "active", "added": None, "activated": None,
         "prefixes": [], "metric": "organic_visitors"}
    t.update(kw)
    return t


def _iso(days_ago):
    return (datetime.date.today() - datetime.timedelta(days=days_ago)).isoformat()


class DaysActiveTest(unittest.TestCase):
    def test_uses_activated_when_present(self):
        self.assertEqual(R._days_active(_tech(activated=_iso(40), added=_iso(90))), 40)

    def test_falls_back_to_added_when_activated_is_missing(self):
        """The T014 case: running, but nothing ever stamped `activated`."""
        self.assertEqual(R._days_active(_tech(activated=None, added=_iso(40))), 40)

    def test_zero_when_neither_date_exists(self):
        self.assertEqual(R._days_active(_tech(activated=None, added=None)), 0)

    def test_unparseable_date_does_not_raise(self):
        self.assertEqual(R._days_active(_tech(activated="soon")), 0)

    def test_activated_wins_over_added(self):
        """A candidate added in March and switched on in July is 30d old, not 150."""
        self.assertEqual(R._days_active(_tech(added=_iso(150), activated=_iso(30))), 30)


class GracePeriodTest(unittest.TestCase):
    def test_an_undated_active_technique_no_longer_sits_in_grace_forever(self):
        t = _tech(activated=None, added=_iso(365))
        self.assertNotIn("grace period", R.evaluate(t)["why"])

    def test_a_genuinely_new_technique_is_still_protected(self):
        t = _tech(activated=None, added=_iso(3))
        res = R.evaluate(t)
        self.assertEqual(res["action"], "keep")
        self.assertIn("grace period", res["why"])

    def test_t014_as_it_actually_stood_on_2026_08_02(self):
        """Six days old on the day the bug was found — still inside grace, but
        for the right reason, and with a clock that will run out."""
        t = _tech(id="T014", slug="geo_answer_first_content_pass",
                  status="active", added="2026-07-27", activated=None)
        as_of = datetime.date(2026, 8, 2)
        days = (as_of - datetime.date.fromisoformat(t["added"])).days
        self.assertEqual(days, 6)
        self.assertLess(days, R.GRACE_DAYS)

    def test_non_active_status_is_skipped_before_the_clock_matters(self):
        res = R.evaluate(_tech(status="candidate", activated=None, added=_iso(365)))
        self.assertEqual(res["action"], "skip")


class SinceTest(unittest.TestCase):
    def test_since_prefers_activated(self):
        self.assertEqual(R._since(_tech(added="2026-01-01", activated="2026-06-01")),
                         "2026-06-01")

    def test_since_falls_back_to_added(self):
        self.assertEqual(R._since(_tech(added="2026-01-01", activated=None)),
                         "2026-01-01")

    def test_since_is_none_when_nothing_is_known(self):
        self.assertIsNone(R._since(_tech(added=None, activated=None)))


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Tests for the county-only view of Search Console.

These exist because of what the 2026-08-04 snapshot showed. Between the
2026-08-03 and 2026-08-04 runs, site-wide impressions for the 28-day window
went from 1,677 to 20,196 while clicks stayed at 7 and the site-wide average
position went from 21.0 to 25.0. None of it was York County: the new rows were
searches like "seamless gutter contractors glenside pa" — Montgomery County,
about ninety miles away — at positions 10 to 35 with no clicks.

Site-wide numbers are still worth having, but they stopped describing the
business the day Google started showing the site in somebody else's market, and
the goal ("more than 50% of York County gutter searches") is a claim about the
county. `tracked_totals` is the county-side number: the same window, restricted
to the curated keyword universe.

No network. These call the pure function with rows shaped the way
`fetch_queries` returns them.

Run: python3 -m growth.test_gsc   (from the repo root)
"""
import unittest

from . import gsc as G


def _row(query, position, impressions, clicks=0):
    return {"query": query, "position": position,
            "impressions": impressions, "clicks": clicks}


TRACKED = {"gutter installation york pa", "gutter repair dover pa",
           "seamless gutters hanover pa"}


class TrackedTotalsTest(unittest.TestCase):

    def test_out_of_area_rows_are_excluded(self):
        rows = [
            _row("gutter installation york pa", 8.0, 100, 2),
            _row("seamless gutter contractors glenside pa", 10.8, 530, 0),
            _row("seamless gutter company wayne pa", 17.2, 497, 0),
        ]
        t = G.tracked_totals(rows, TRACKED)
        self.assertEqual(t["rows"], 1)
        self.assertEqual(t["impressions"], 100)
        self.assertEqual(t["clicks"], 2)
        self.assertEqual(t["avg_position"], 8.0)

    def test_position_is_weighted_by_impressions(self):
        # Unweighted this would be 20.0. One query with three impressions must
        # not outvote one with three hundred, which is the whole reason the
        # site-wide average went to pieces this week.
        rows = [_row("gutter installation york pa", 5.0, 300),
                _row("gutter repair dover pa", 35.0, 3)]
        t = G.tracked_totals(rows, TRACKED)
        self.assertEqual(t["impressions"], 303)
        self.assertEqual(t["avg_position"], 5.3)

    def test_matching_is_case_and_space_insensitive(self):
        rows = [_row("  Gutter Installation York PA  ", 4.0, 10, 1)]
        t = G.tracked_totals(rows, TRACKED)
        self.assertEqual(t["rows"], 1)
        self.assertEqual(t["clicks"], 1)

    def test_rows_without_a_position_still_count_their_impressions(self):
        # A row Search Console returns with no position must not be silently
        # dropped from the impression count, and must not divide by zero.
        rows = [_row("gutter installation york pa", None, 40),
                _row("gutter repair dover pa", 6.0, 60)]
        t = G.tracked_totals(rows, TRACKED)
        self.assertEqual(t["impressions"], 100)
        self.assertEqual(t["avg_position"], 6.0)

    def test_no_tracked_rows_reports_none_not_zero(self):
        # Position 0.0 would read as "ranking first everywhere". The honest
        # answer when nothing matched is that there is no answer.
        t = G.tracked_totals([_row("seamless gutter devon pa", 29.4, 273)],
                             TRACKED)
        self.assertEqual(t["rows"], 0)
        self.assertEqual(t["impressions"], 0)
        self.assertIsNone(t["avg_position"])

    def test_empty_universe_matches_nothing(self):
        t = G.tracked_totals([_row("gutter installation york pa", 8.0, 100)],
                             set())
        self.assertEqual(t["rows"], 0)
        self.assertIsNone(t["avg_position"])

    def test_the_real_08_04_shape(self):
        # The county number must survive the flood rather than be averaged into
        # it: 3 tracked rows at 630 impressions alongside 2,000 out-of-market
        # impressions should report the county's position, not 24-ish.
        rows = [_row("gutter installation york pa", 8.0, 400, 3),
                _row("gutter repair dover pa", 9.0, 200, 1),
                _row("seamless gutters hanover pa", 12.0, 30, 0)]
        rows += [_row(f"seamless gutter contractors town{i} pa", 30.0, 500)
                 for i in range(4)]
        t = G.tracked_totals(rows, TRACKED)
        self.assertEqual(t["rows"], 3)
        self.assertEqual(t["impressions"], 630)
        self.assertEqual(t["clicks"], 4)
        self.assertLess(t["avg_position"], 10)


if __name__ == "__main__":
    unittest.main()

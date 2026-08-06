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


class SelectDiscoveriesTest(unittest.TestCase):
    """The second slate, added 2026-08-05.

    `discover()` returned the top 40 untracked rows by impressions. That was
    fine until 2026-08-04, when forty out-of-market rows at 186-530
    impressions arrived at once and evicted every quiet row underneath them —
    including `gutters` at 46 impressions and position 3.7, which was the only
    row on the whole site that had been improving.
    """

    FLOOD = [_row(f"seamless gutter contractors town{i} pa", 30.0, 500 - i)
             for i in range(45)]

    def test_loud_rows_still_come_back_ranked_by_impressions(self):
        got = G._select_discoveries(self.FLOOD, TRACKED)
        self.assertEqual(got[0]["query"], "seamless gutter contractors town0 pa")
        self.assertEqual(got[0]["impressions"], 500)

    def test_a_flood_cannot_evict_a_well_ranked_quiet_row(self):
        rows = self.FLOOD + [_row("gutters", 3.7, 46)]
        got = G._select_discoveries(rows, TRACKED)
        picked = {r["query"] for r in got}
        # It loses on impressions to all 45 of them and would have been cut.
        self.assertIn("gutters", picked)

    def test_the_second_slate_is_ordered_by_position(self):
        rows = self.FLOOD + [_row("gutter contractor", 1.0, 46),
                             _row("gutters", 3.7, 46),
                             _row("gutter guard installer", 12.0, 14)]
        got = [r["query"] for r in G._select_discoveries(rows, TRACKED)]
        # The five flood rows the first slate could not hold rank behind them,
        # at position 30.
        self.assertEqual(got[G.TOP_BY_IMPRESSIONS:G.TOP_BY_IMPRESSIONS + 3],
                         ["gutter contractor", "gutters",
                          "gutter guard installer"])

    def test_tracked_queries_are_never_returned(self):
        rows = [_row("gutter installation york pa", 2.0, 40),
                _row("gutters", 3.7, 46)]
        got = {r["query"] for r in G._select_discoveries(rows, TRACKED)}
        self.assertEqual(got, {"gutters"})

    def test_min_impressions_still_applies_to_the_quiet_slate(self):
        rows = self.FLOOD + [_row("gutter installer somewhere", 1.0, 1)]
        got = {r["query"] for r in G._select_discoveries(rows, TRACKED)}
        self.assertNotIn("gutter installer somewhere", got)

    def test_a_row_with_no_position_is_not_promoted(self):
        rows = self.FLOOD + [{"query": "gutters", "position": None,
                              "impressions": 46, "clicks": 0}]
        got = {r["query"] for r in G._select_discoveries(rows, TRACKED)}
        self.assertNotIn("gutters", got)

    def test_no_row_appears_twice(self):
        rows = self.FLOOD + [_row("gutters", 3.7, 46)]
        got = [r["query"] for r in G._select_discoveries(rows, TRACKED)]
        self.assertEqual(len(got), len(set(got)))

    def test_a_mid_volume_well_ranked_row_survives_a_flood(self):
        # The real 2026-08-05 row: `gutter installer`, 214 impressions at
        # position 1. Loud enough to be cut by forty rows at ~500, and the
        # first version of this function also excluded it from the second
        # slate for being too loud, so it disappeared entirely.
        rows = self.FLOOD + [_row("gutter installer", 1.0, 214)]
        got = [r["query"] for r in G._select_discoveries(rows, TRACKED)]
        self.assertEqual(got.count("gutter installer"), 1)


class ClassifyPagesTest(unittest.TestCase):
    """Make a no-op from `improve_ctr` auditable.

    On 2026-08-06 that technique reported "no page is due a snippet rewrite"
    for the fourth morning running, while the homepage held position 1 for
    `gutter installer` over 436 impressions for zero clicks. The snapshot
    carried no way to tell whether the technique had looked at the homepage
    and passed on it, or never saw it at all.
    """

    HOME = "https://nemoseamlessgutter.com/"

    def _page(self, page, position, impressions, clicks=0, ctr=0.0):
        return {"page": page, "position": position, "impressions": impressions,
                "clicks": clicks, "ctr": ctr}

    def test_a_well_ranked_unclicked_page_is_a_candidate(self):
        rows = G._classify_pages([self._page(self.HOME, 2.0, 400)])
        self.assertTrue(rows[0]["ctr_candidate"])
        self.assertEqual(rows[0]["skipped_because"], [])

    def test_an_out_of_market_flood_hides_the_page_from_the_rewriter(self):
        # The homepage ranks 1st in York County and 10-35 across Montgomery
        # County; Search Console reports one average over both. 24.8 was the
        # site-wide figure on 2026-08-06.
        rows = G._classify_pages([self._page(self.HOME, 24.8, 21729)])
        self.assertFalse(rows[0]["ctr_candidate"])
        self.assertEqual(rows[0]["skipped_because"],
                         ["average position below the cutoff"])

    def test_a_page_people_do_click_is_left_alone(self):
        rows = G._classify_pages([self._page(self.HOME, 3.0, 500, 40, 0.08)])
        self.assertFalse(rows[0]["ctr_candidate"])
        self.assertIn("click-through already above the floor",
                      rows[0]["skipped_because"])

    def test_every_failing_clause_is_named_not_just_the_first(self):
        rows = G._classify_pages([self._page("/quiet.html", 40.0, 3, 1, 0.33)])
        self.assertEqual(len(rows[0]["skipped_because"]), 3)

    def test_a_page_with_no_position_is_not_silently_promoted(self):
        rows = G._classify_pages([self._page(self.HOME, None, 400)])
        self.assertFalse(rows[0]["ctr_candidate"])

    def test_the_verdict_agrees_with_underperformers_clause_for_clause(self):
        # If these two ever disagree the report is worse than useless, so the
        # filters are asserted against each other rather than restated.
        pages = [self._page(self.HOME, 24.8, 21729),
                 self._page("/a.html", 2.0, 400),
                 self._page("/b.html", 3.0, 500, 40, 0.08),
                 self._page("/c.html", 1.0, 4)]
        kept = {p["page"] for p in pages
                if p["impressions"] >= 10
                and (p["position"] or 99) <= 15.0
                and p["ctr"] <= 0.02}
        flagged = {r["page"] for r in G._classify_pages(pages)
                   if r["ctr_candidate"]}
        self.assertEqual(flagged, kept)

    def test_biggest_wasted_audience_is_reported_first(self):
        rows = G._classify_pages([self._page("/small.html", 2.0, 20),
                                  self._page(self.HOME, 2.0, 400)])
        self.assertEqual(rows[0]["page"], self.HOME)


if __name__ == "__main__":
    unittest.main()

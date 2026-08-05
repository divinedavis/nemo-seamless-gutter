#!/usr/bin/env python3
"""Tests for the per-query rank rows in `keywords.summary()`.

Added 2026-08-05. The snapshot published `top3`, `top10` and `ranked_known`
and nothing underneath them. On 2026-08-05 the top-3 count went 2 -> 1 — the
first movement in the goal metric in nine measured days — and the review agent
could not say which query fell out, because the only rank data it could see
was a total and a list of *untracked* queries. `ranked` is that missing row
list: every tracked query Search Console returns a position for.

No network, no droplet state — `load()` is patched with a fixture.

Run: python3 -m growth.test_keywords   (from the repo root)
"""
import unittest
from unittest import mock

from . import keywords as K


def _kw(query, position=None, town="county", intent="hire", covered=True,
        impressions=None, clicks=None, target="/"):
    return {"query": query, "town": town, "intent": intent, "target": target,
            "covered": covered, "position": position,
            "impressions": impressions, "clicks": clicks}


FIXTURE = [
    _kw("gutter installation york pa", 2.0, impressions=120, clicks=3),
    _kw("seamless gutters hanover pa", 3.0, town="hanover", impressions=40),
    _kw("gutter repair dover pa", 8.5, town="dover", impressions=60),
    _kw("gutter guard cost pa", 41.0, intent="price", covered=False, target=""),
    # Never returned by Search Console — tracked, but not ranked.
    _kw("gutter cleaning cost red lion pa", None, town="red-lion",
        intent="price", covered=False, target=""),
]


class RankedRowsTest(unittest.TestCase):

    def _summary(self, kws=None):
        with mock.patch.object(K, "load", return_value=kws or FIXTURE):
            return K.summary()

    def test_only_queries_with_a_position_appear(self):
        s = self._summary()
        self.assertEqual(len(s["ranked"]), 4)
        self.assertNotIn("gutter cleaning cost red lion pa",
                         {r["query"] for r in s["ranked"]})

    def test_ranked_matches_the_aggregate_it_explains(self):
        s = self._summary()
        self.assertEqual(len(s["ranked"]), s["ranked_known"])
        self.assertEqual(sum(1 for r in s["ranked"] if r["position"] <= 3),
                         s["top3"])
        self.assertEqual(sum(1 for r in s["ranked"] if r["position"] <= 10),
                         s["top10"])

    def test_best_position_first(self):
        s = self._summary()
        self.assertEqual([r["position"] for r in s["ranked"]],
                         [2.0, 3.0, 8.5, 41.0])

    def test_a_row_carries_what_a_reader_needs_to_act_on_it(self):
        # Which town it belongs to and whether a page targets it, so "this one
        # fell" can be followed by "and here is the page that lost it".
        row = self._summary()["ranked"][0]
        self.assertEqual(row["town"], "county")
        self.assertEqual(row["intent"], "hire")
        self.assertEqual(row["target"], "/")
        self.assertIs(row["covered"], True)
        self.assertEqual(row["impressions"], 120)
        self.assertEqual(row["clicks"], 3)

    def test_an_uncovered_ranked_query_is_reported_as_uncovered(self):
        row = [r for r in self._summary()["ranked"]
               if r["query"] == "gutter guard cost pa"][0]
        self.assertIs(row["covered"], False)

    def test_no_rank_data_at_all_gives_an_empty_list_not_an_error(self):
        s = self._summary([_kw("gutter installation york pa", None)])
        self.assertEqual(s["ranked"], [])
        self.assertIsNone(s["share_pct"])

    def test_a_dropped_query_is_visible_between_two_days(self):
        # The 2026-08-05 case: top3 goes 2 -> 1 with top10 flat, because one
        # query fell from the top three into the rest of the first page. The
        # aggregates alone cannot name it; two ranked lists can.
        before = self._summary()
        after = self._summary([_kw("gutter installation york pa", 2.0),
                               _kw("seamless gutters hanover pa", 5.0,
                                   town="hanover"),
                               _kw("gutter repair dover pa", 8.5, town="dover"),
                               _kw("gutter guard cost pa", 41.0)])
        self.assertEqual((before["top3"], after["top3"]), (2, 1))
        self.assertEqual((before["top10"], after["top10"]), (3, 3))
        fell = {r["query"] for r in before["ranked"] if r["position"] <= 3} - \
               {r["query"] for r in after["ranked"] if r["position"] <= 3}
        self.assertEqual(fell, {"seamless gutters hanover pa"})


if __name__ == "__main__":
    unittest.main()

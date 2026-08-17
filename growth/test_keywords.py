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
import os
import shutil
import tempfile
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


class UnassignedTargetCoverageTest(unittest.TestCase):
    """Coverage for a query the scout added and nobody assigned a page to.

    `add()` defaults `target` to "", the scout supplies nothing, and only
    `strengthen_pages` ever fills it — one query a day, as a side effect of
    writing a section. So on 2026-08-17 "copper gutters york pa cost" read
    "no page targets this query" while the copper guide was live. See
    keywords._find_host().
    """

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        os.makedirs(os.path.join(self.root, "guides"))
        os.makedirs(os.path.join(self.root, "services"))
        os.makedirs(os.path.join(self.root, "areas"))
        # Titles copied from the live pages as of 2026-08-17.
        self._page("guides/copper-gutters-historic-home-york-pa.html",
                   "Copper Gutters for Historic Homes | York PA Cost Guide "
                   "| NEMO Seamless Gutter",
                   h1="Copper Gutters for Historic Homes in York County, PA",
                   # In the body only, so the h1-only rule can be tested.
                   body="half round gutters cost per foot varies by house")
        self._page("services/gutter-soffit-fascia-replacement.html",
                   "Gutter, Soffit &amp; Fascia Replacement in York, PA",
                   body="We replace rotted fascia board and soffit.")
        self._page("index.html", "Seamless Gutters in York, PA",
                   body="Free estimates across York County.")

    def _page(self, rel, title, h1=None, body=""):
        path = os.path.join(self.root, rel)
        with open(path, "w") as f:
            f.write(f"<html><head><title>{title}</title></head>"
                    f"<body><h1>{h1 or title}</h1><p>{body}</p>"
                    f"</body></html>")

    def _check(self, kws):
        saved = []
        with mock.patch.object(K, "load", return_value=kws), \
             mock.patch.object(K, "save", side_effect=lambda k: saved.append(k)), \
             mock.patch.object(K.ledger, "today", return_value="2026-08-17"):
            return K.check_coverage(self.root)[0]

    def test_unassigned_query_is_credited_to_the_page_that_targets_it(self):
        k = _kw("copper gutters york pa cost", covered=False, target="",
                intent="price")
        got = self._check([k])[0]
        self.assertTrue(got["covered"])
        self.assertIn("copper-gutters-historic-home-york-pa.html",
                      got["coverage_detail"])

    def test_one_distinguishing_token_is_not_enough(self):
        # 'replace' alone matched the soffit-and-fascia page on 2026-08-17,
        # which is the wrong page for this query. Two tokens or nothing.
        got = self._check([_kw("how much to replace gutters on a house",
                               covered=False, target="")])[0]
        self.assertFalse(got["covered"])
        self.assertEqual(got["coverage_detail"], "no page targets this query")

    def test_body_copy_alone_does_not_count(self):
        # The words are in the copper page's body, not its title or h1.
        got = self._check([_kw("half round gutters cost per foot",
                               covered=False, target="")])[0]
        self.assertFalse(got["covered"])

    def test_genuinely_uncovered_query_stays_uncovered(self):
        got = self._check([_kw("gutter guard installation red lion pa",
                               covered=False, target="")])[0]
        self.assertFalse(got["covered"])

    def test_an_assigned_target_still_wins(self):
        # A keyword whose target resolves must be judged on that page, not on
        # whatever else the site happens to say — the fallback is for the
        # unassigned case only.
        got = self._check([_kw("copper gutters york pa cost", covered=False,
                               target="/services/gutter-soffit-fascia-replacement.html")])[0]
        self.assertFalse(got["covered"])
        self.assertIn("missing", got["coverage_detail"])

    def test_missing_docroot_does_not_credit_anything(self):
        with mock.patch.object(K, "load",
                               return_value=[_kw("copper gutters york pa cost",
                                                 covered=False, target="")]), \
             mock.patch.object(K, "save"), \
             mock.patch.object(K.ledger, "today", return_value="2026-08-17"):
            got = K.check_coverage("/no/such/docroot")[0][0]
        self.assertFalse(got["covered"])

    def test_index_is_built_once_not_per_keyword(self):
        kws = [_kw(f"query number {i} gutters", covered=False, target="")
               for i in range(25)]
        with mock.patch.object(K, "_headline_index",
                               wraps=K._headline_index) as spy, \
             mock.patch.object(K, "load", return_value=kws), \
             mock.patch.object(K, "save"), \
             mock.patch.object(K.ledger, "today", return_value="2026-08-17"):
            K.check_coverage(self.root)
        self.assertEqual(spy.call_count, 1)


if __name__ == "__main__":
    unittest.main()

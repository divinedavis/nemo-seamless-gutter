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


class LeakedTitleCoverageTest(unittest.TestCase):
    """A title that belongs to another page must not credit coverage.

    Added 2026-09-28 after the real thing. `seo/gen_article.py` copied a source
    guide's whole head block — its <title> included — into every article it
    generated, so /guides/5-vs-6-inch-gutters-right-size-for-york-county-homes.html
    shipped carrying "Seamless vs. Sectional Gutters: Which Is Better?" as a
    second title. `check_coverage` matched against every title on the page and
    credited two "5 inch vs 6 inch gutters which ..." queries to it on the
    strength of the word "which", which appears only in the borrowed heading.
    Both sat `covered` until the leak was stripped on 2026-09-27 (ce84002).
    """

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        os.makedirs(os.path.join(self.root, "guides"))

    def _write(self, rel, head_html, h1):
        with open(os.path.join(self.root, rel), "w") as f:
            f.write(f"<html><head>{head_html}</head>"
                    f"<body><h1>{h1}</h1><p>Free estimates in York County.</p>"
                    f"</body></html>")

    def _check(self, kws):
        with mock.patch.object(K, "load", return_value=kws), \
             mock.patch.object(K, "save"), \
             mock.patch.object(K.ledger, "today", return_value="2026-09-28"):
            return K.check_coverage(self.root)[0]

    # The page as it shipped: its own title, plus the one gen_article.py leaked.
    LEAKED = ("<title>5 vs 6 Inch Gutters: Right Size for York County Homes"
              " | NEMO Seamless Gutter</title>"
              "<title>Seamless vs. Sectional Gutters: Which Is Better?"
              " | NEMO Seamless Gutter</title>")
    CLEAN = ("<title>5 vs 6 Inch Gutters: Right Size for York County Homes"
             " | NEMO Seamless Gutter</title>")
    H1 = "5 vs 6 Inch Gutters: Right Size for York County Homes"
    REL = "guides/5-vs-6-inch-gutters-right-size-for-york-county-homes.html"

    def test_a_leaked_second_title_does_not_credit_coverage(self):
        self._write(self.REL, self.LEAKED, self.H1)
        got = self._check([_kw("5 inch vs 6 inch gutters which is better",
                               covered=False, target=f"/{self.REL}")])[0]
        self.assertFalse(got["covered"])

    def test_the_pages_own_title_still_counts(self):
        self._write(self.REL, self.CLEAN, self.H1)
        got = self._check([_kw("6 inch gutters right size york",
                               covered=False, target=f"/{self.REL}")])[0]
        self.assertTrue(got["covered"])

    def test_the_fallback_index_ignores_a_leaked_title_too(self):
        # Unassigned target, so coverage goes through _find_host(): the
        # borrowed heading must not make this page the host either.
        self._write(self.REL, self.LEAKED, self.H1)
        index = K._headline_index(self.root)
        self.assertNotIn("sectional", index[f"/{self.REL}"])
        self.assertIn("inch", index[f"/{self.REL}"])

    def test_a_term_only_in_json_ld_does_not_credit_weak_coverage(self):
        # The old check asked whether the term was anywhere in the file, so a
        # word appearing only inside a schema blob or an inline script counted
        # as body copy. It is not something a reader can read.
        self._write(self.REL,
                    self.CLEAN + '<meta name="description" content="sectional">'
                    '<script type="application/ld+json">'
                    '{"name": "which is better sectional"}</script>',
                    self.H1)
        got = self._check([_kw("5 inch vs 6 inch gutters which is better",
                               covered=False, target=f"/{self.REL}")])[0]
        self.assertFalse(got["covered"])

    def test_real_body_copy_still_counts_as_weak_coverage(self):
        self._write(self.REL, self.CLEAN, self.H1)
        path = os.path.join(self.root, self.REL)
        html = open(path).read().replace(
            "<p>Free estimates in York County.</p>",
            "<p>Which is better for a York County roof? Usually 6 inch.</p>")
        open(path, "w").write(html)
        got = self._check([_kw("5 inch vs 6 inch gutters which is better",
                               covered=False, target=f"/{self.REL}")])[0]
        self.assertTrue(got["covered"])
        self.assertIn("weak", got["coverage_detail"])



class WordBoundaryMatchingTest(unittest.TestCase):
    """Short tokens survive tokenisation, so matching must respect words.

    Added 2026-09-29. `_tokens()` used to discard every token of two characters
    or fewer, which quietly made "5 inch vs 6 inch gutters" and "seamless
    gutters vs sectional gutters" permanently uncoverable — both had pages live
    and titled for them, and both stayed in `strengthen_pages`' build queue.
    Lifting the cutoff on its own would have been worse than the bug: matching
    was raw substring containment, and "6" is a substring of "2026", so every
    page whose title carries the year would have handed out coverage for every
    6-inch query on the site. The cutoff is gone and matching is on words.
    """

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        os.makedirs(os.path.join(self.root, "guides"))

    def _write(self, rel, title, h1, body="Free estimates in York County."):
        with open(os.path.join(self.root, rel), "w") as f:
            f.write(f"<html><head><title>{title}</title></head>"
                    f"<body><h1>{h1}</h1><p>{body}</p></body></html>")

    def _check(self, kws):
        with mock.patch.object(K, "load", return_value=kws), \
             mock.patch.object(K, "save"), \
             mock.patch.object(K.ledger, "today", return_value="2026-09-29"):
            return K.check_coverage(self.root)[0]

    SIZE = "5 vs 6 Inch Gutters: Right Size for York County Homes"
    SIZE_REL = "guides/5-vs-6-inch-gutters-right-size-for-york-county-homes.html"

    def test_a_digit_token_survives_tokenisation(self):
        self.assertIn("5", K._tokens("5 inch vs 6 inch gutters"))
        self.assertIn("6", K._tokens("5 inch vs 6 inch gutters"))

    def test_vs_is_kept_because_it_is_the_whole_comparison(self):
        self.assertNotIn("vs", K.STOP)
        self.assertIn("vs", K._tokens("seamless gutters vs sectional gutters"))

    def test_the_state_abbreviation_distinguishes_nothing(self):
        self.assertIn("pa", K.GENERIC)

    def test_a_digit_does_not_match_inside_a_year(self):
        self.assertFalse(K._has({"2026", "gutters"}, "6"))
        self.assertFalse(K._has({"2025", "prices"}, "5"))

    def test_a_digit_matches_the_same_digit_as_a_word(self):
        self.assertTrue(K._has({"6", "inch", "gutters"}, "6"))

    def test_a_longer_token_still_matches_a_plural(self):
        self.assertTrue(K._has({"installers"}, "installer"))
        self.assertTrue(K._has({"cleaning"}, "clean"))

    def test_a_short_token_must_match_a_whole_word(self):
        self.assertFalse(K._has({"versus"}, "vs"))
        self.assertTrue(K._has({"vs", "sectional"}, "vs"))

    def test_the_size_page_now_hosts_its_own_query(self):
        self._write(self.SIZE_REL, self.SIZE, self.SIZE)
        index = K._headline_index(self.root)
        host = K._find_host(["5", "inch", "vs", "6"], index)
        self.assertEqual(host, f"/{self.SIZE_REL}")

    def test_a_page_titled_for_the_year_does_not_host_a_6_inch_query(self):
        self._write("guides/gutter-cost-2026.html",
                    "Gutter Cost in York County 2026",
                    "Gutter Cost in York County 2026")
        index = K._headline_index(self.root)
        self.assertIsNone(K._find_host(["6", "inch"], index))

    def test_company_is_not_generic_and_hosts_the_page_written_for_it(self):
        """money_pages published the page on 2026-07-28; the query stayed in
        the build queue until 2026-09-29 because "company" sat in GENERIC."""
        self.assertNotIn("company", K.GENERIC)
        self._write("guides/best-gutter-company-york-county-pa.html",
                    "Best Gutter Company in York County PA | NEMO Seamless",
                    "The Best Gutter Company in York County, PA")
        index = K._headline_index(self.root)
        self.assertEqual(
            K._find_host(["best", "company"], index),
            "/guides/best-gutter-company-york-county-pa.html")

    def test_company_alone_still_cannot_host_a_query(self):
        self._write("guides/best-gutter-company-york-county-pa.html",
                    "Best Gutter Company in York County PA",
                    "The Best Gutter Company in York County, PA")
        index = K._headline_index(self.root)
        self.assertIsNone(K._find_host(["company"], index))

    def test_coverage_of_an_assigned_page_uses_words_not_characters(self):
        self._write("guides/gutter-cost-2026.html",
                    "Gutter Cost in York County 2026",
                    "Gutter Cost in York County 2026",
                    body="Prices held steady through 2026.")
        got = self._check([_kw("6 inch gutter cost york pa", covered=False,
                               target="/guides/gutter-cost-2026.html")])[0]
        self.assertFalse(got["covered"])



class TownCoverage(unittest.TestCase):
    """Every town the engine publishes a page for must be scoreable.

    Added 2026-10-04. `techniques.TOWN_QUEUE` had published all ten of its
    towns -- Dillsburg through Jacobus -- and none of them were in
    `keywords.TOWNS`, so `add()` silently refused any query for them (the
    `town not in TOWNS` guard) and `summary()["by_town"]` had no bucket to put
    them in. Ten of the fifteen live area pages were therefore invisible to
    the one metric the whole engine is pointed at: `top3`. The engine could
    publish a page and never be told whether it worked.
    """

    def test_every_queued_town_has_a_bucket(self):
        from . import techniques
        missing = sorted({t[0] for t in techniques.TOWN_QUEUE} - set(K.TOWNS))
        self.assertEqual(missing, [], f"TOWN_QUEUE towns absent from TOWNS: {missing}")

    def test_every_queued_town_has_at_least_one_seed_query(self):
        from . import techniques
        seeded = {town for town, _q, _i, _t in K.SEED}
        missing = sorted({t[0] for t in techniques.TOWN_QUEUE} - seeded)
        self.assertEqual(missing, [], f"queued towns with no tracked query: {missing}")

    def test_a_seed_query_points_at_the_page_that_exists_for_it(self):
        """A town seed aimed at /areas/ must name that town's own page.

        A copy-paste that left the previous town's filename in place would
        credit coverage to the wrong page and send strengthen_pages after a
        gap that is not there.
        """
        for town, query, _intent, target in K.SEED:
            if not target.startswith("/areas/"):
                continue
            self.assertEqual(target, f"/areas/seamless-gutters-{town}-pa.html",
                             f"{query!r} targets {target}")


if __name__ == "__main__":
    unittest.main()

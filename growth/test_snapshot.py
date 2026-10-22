#!/usr/bin/env python3
"""Tests for the snapshot's engine-version stamp and its indexing block.

Added 2026-08-09. The docroot is not a git checkout, so a commit on main is not
running until somebody copies it across, and nothing in the snapshot said which
version had produced it. Three consecutive reviews deduced the deployed version
from which optional keys were missing, and on 2026-08-09 that inference had to
untangle a *partial* deploy: techniques.py and templates.py were live from the
night before, while snapshot.py, gsc.py, metrics.py and scout.py were still the
2026-08-04 copies. Absence-of-a-key cannot see that, because it only exists
where a change happened to add a key.

`_code_fingerprint()` hashes the engine's own source so the reviewer can hash
the same files in its checkout and diff. These tests pin the properties that
comparison depends on: it changes when a source file changes, it does not
change when a test file does, it names growth_daily.py because that file has
its own way of being left behind, and it never raises — a snapshot that fails
to publish tells the reviewer nothing at all, which is worse than a snapshot
with no stamp on it.

No network and no droplet state.

Run: python3 -m growth.test_snapshot   (from the repo root)
"""
import os
import unittest
from unittest import mock

from . import snapshot as S


class CodeFingerprintTest(unittest.TestCase):

    def test_names_the_engine_modules_and_omits_tests(self):
        fp = S._code_fingerprint()
        self.assertIn("snapshot.py", fp["modules"])
        self.assertIn("techniques.py", fp["modules"])
        self.assertIn("gsc.py", fp["modules"])
        self.assertIn("metrics.py", fp["modules"])
        # Tests never run on the droplet, so their hashes would differ between
        # the two sides for reasons that mean nothing.
        self.assertNotIn("test_snapshot.py", fp["modules"])
        self.assertFalse([k for k in fp["modules"] if k.startswith("test_")])
        # Only Python. snapshot.json and JOURNAL.md live in this directory and
        # change every single morning; including them would make the stamp
        # differ on every run and say nothing about the code.
        self.assertFalse([k for k in fp["modules"] if not k.endswith(".py")])

    def test_includes_the_cli_that_sits_outside_the_package(self):
        fp = S._code_fingerprint()
        self.assertIn("../growth_daily.py", fp["modules"])

    def test_hashes_are_the_content_of_the_files(self):
        """The reviewer computes the other side of this comparison itself."""
        import hashlib
        fp = S._code_fingerprint()
        with open(os.path.join(S.HERE, "keywords.py"), "rb") as fh:
            expected = hashlib.sha256(fh.read()).hexdigest()[:12]
        self.assertEqual(fp["modules"]["keywords.py"], expected)

    def test_combined_moves_when_any_module_moves(self):
        first = S._code_fingerprint()
        real = S.os.listdir

        def one_fewer(path):
            names = real(path)
            return [n for n in names if n != "keywords.py"]

        with mock.patch.object(S.os, "listdir", one_fewer):
            second = S._code_fingerprint()
        self.assertNotIn("keywords.py", second["modules"])
        self.assertNotEqual(first["combined"], second["combined"])

    def test_combined_is_stable_across_calls(self):
        self.assertEqual(S._code_fingerprint()["combined"],
                         S._code_fingerprint()["combined"])

    def test_an_unreadable_file_is_skipped_rather_than_fatal(self):
        """Never take the bridge down over the diagnostic bolted to it."""
        real_open = open

        def deny_one(path, *a, **kw):
            if str(path).endswith("keywords.py"):
                raise OSError("permission denied")
            return real_open(path, *a, **kw)

        with mock.patch("builtins.open", deny_one):
            fp = S._code_fingerprint()
        self.assertNotIn("keywords.py", fp["modules"])
        self.assertIn("snapshot.py", fp["modules"])

    def test_a_missing_cli_is_skipped_rather_than_fatal(self):
        real_open = open

        def deny_cli(path, *a, **kw):
            if str(path).endswith("growth_daily.py"):
                raise OSError("no such file")
            return real_open(path, *a, **kw)

        with mock.patch("builtins.open", deny_cli):
            fp = S._code_fingerprint()
        self.assertNotIn("../growth_daily.py", fp["modules"])
        self.assertTrue(fp["combined"])

    def test_survives_the_pii_scrub_unchanged(self):
        """A 12-hex digest must not look like anything scrub() redacts."""
        fp = S._code_fingerprint()
        clean, found = S.scrub({"code_version": fp})
        self.assertEqual(clean["code_version"], fp)
        self.assertEqual(found, [])


class IndexingBlockTest(unittest.TestCase):
    """`indexing` has to reach the published file, and must cost no API call.

    Added 2026-10-10. `indexstatus.run()` already executed every morning
    inside `cmd_measure` and wrote its verdict to /var/log/nemo-growth.log —
    a file the review agent cannot read, because it reads snapshot.json and
    nothing else. So the measurement existed and the judgment layer still
    could not see it, which is the same failure `call_taps` and
    `log_visitors` were added to fix. It matters because "Google dropped the
    page" and "Google kept it, nobody searched" are the same zero from here
    and need opposite responses: the first needs links and crawl signals, the
    second needs a different query target.
    """

    CACHE = {
        "ok": True,
        "updated": "2026-10-10T06:02:11+00:00",
        "sitemap_urls": 46,
        "inspected": 46,
        "buckets": {"indexed": 40, "crawled_not_indexed": 4,
                    "discovered_not_indexed": 1, "unknown_to_google": 1},
        "accept_pct": 87.0,
        "accept_of_fetched": 90.9,
        "errors": [],
    }

    def _build(self, cache):
        """build() with every droplet-owned source stubbed out.

        No network, no ledger, no docroot — this pins the published *shape*,
        which is the only thing the review agent ever sees.
        """
        stubs = {
            "keywords": mock.Mock(**{"summary.return_value": {
                "share_pct": 0.0, "coverage_pct": 42.4, "total": 238,
                "top3": 0, "top10": 21, "ranked_known": 57, "covered": 101,
                "by_town": {}, "by_intent": {}, "gaps": [], "ranked": [],
                # Added 2026-10-11 with keywords._out_of_area. build() reads
                # this key unguarded on purpose: the audit trail for a shrunk
                # denominator must fail loudly rather than go missing.
                "excluded_out_of_area": {"count": 10, "queries": [
                    "gutter cleaner york springs pa"]}}}),
            "review": mock.Mock(**{"scoreboard.return_value": {
                "works": [], "does_not_work": [], "not_yet_judged": []}}),
            "ledger": mock.Mock(**{"load_techniques.return_value": [],
                                   "get_state.return_value": None,
                                   "today.return_value": "2026-10-10",
                                   "series.return_value": []}),
            "metrics": mock.Mock(**{"lead_totals.return_value": {}}),
            "gsc": mock.Mock(**{"discover.return_value": []}),
            # The real summary() over a stubbed cache, so the published shape
            # is the one indexstatus actually produces rather than a fixture
            # that could drift away from it.
            "indexstatus": mock.Mock(**{
                "summary.return_value": _real_summary(cache)}),
        }
        with mock.patch.multiple(S, **stubs), \
             mock.patch.object(S, "_page_inventory", return_value={}):
            return S.build("/nonexistent")

    def test_build_publishes_the_indexing_summary(self):
        snap = self._build(self.CACHE)
        self.assertIn("indexing", snap)
        ix = snap["indexing"]
        self.assertTrue(ix["measured"])
        self.assertEqual(ix["indexed"], 40)
        self.assertEqual(ix["inspected"], 46)
        self.assertEqual(ix["unknown_to_google"], 1)
        self.assertEqual(ix["crawled_not_indexed"], 4)
        self.assertEqual(ix["accept_pct"], 87.0)

    def test_build_publishes_what_the_goal_declined_to_score(self):
        """A denominator that shrank must say which rows left it.

        `keywords.summary()` stopped scoring out-of-area queries on 2026-10-11,
        which moves `tracked_queries` and `coverage_pct` on the morning it
        deploys. Unless the excluded rows reach the snapshot, that step is
        indistinguishable from progress — the one misreading
        `growth_daily.py` forbids.
        """
        snap = self._build(self.CACHE)
        x = snap["keywords"]["excluded_out_of_area"]
        self.assertEqual(x["count"], 10)
        self.assertIn("gutter cleaner york springs pa", x["queries"])

    def test_an_unreadable_cache_publishes_the_reason_not_a_missing_key(self):
        """A dead instrument must read as dead, not as a quiet success."""
        snap = self._build({})
        self.assertIn("indexing", snap)
        self.assertFalse(snap["indexing"]["measured"])

    def test_reads_the_morning_cache_rather_than_calling_the_api(self):
        """Publishing must not spend quota or depend on Search Console being up.

        `summary()` takes the cache `cmd_measure` already wrote. If this ever
        starts calling `run()`, the 6am publish gains a network dependency and
        a second pass over the URL Inspection quota.
        """
        with mock.patch.object(S.indexstatus, "run",
                               side_effect=AssertionError("called run()")):
            out = S.indexstatus.summary(self.CACHE)
        self.assertTrue(out["measured"])

    def test_survives_the_pii_scrub_unchanged(self):
        """Counts and an ISO timestamp must not look like anything redacted."""
        ix = _real_summary(self.CACHE)
        clean, found = S.scrub({"indexing": ix})
        self.assertEqual(clean["indexing"], ix)
        self.assertEqual(found, [])


class GscSeriesBlockTest(unittest.TestCase):
    """The rank history has to reach the published file, not just the ledger.

    Added 2026-10-22, for the same reason as the `indexing` block above: a
    measurement the engine keeps but does not publish is a measurement the
    judgment layer cannot use. `gsc_last` is one row, overwritten every
    morning, and the review agent reads snapshot.json and nothing else — which
    is how ten consecutive entries came to compare the prompt's 2026-07-28
    baseline against "the latest row" across a 76-day window containing two
    confirmed Google spam updates, with no way to date anything inside it.
    """

    GSC_LAST = {"date": "2026-10-22", "ok": True, "connected": True,
                "rows": 759, "matched": 54, "clicks": 11,
                "impressions": 5281, "avg_position": 26.1}

    def _build(self, gsc_last):
        def series(technique, metric, *a, **kw):
            assert technique == "__site__", technique
            return [("2026-10-20", 1), ("2026-10-21", 2), ("2026-10-22", 3)]

        return self._build_with_series(gsc_last, series)

    def _build_with_series(self, gsc_last, series):
        """build() with every droplet-owned source stubbed; see IndexingBlockTest."""
        stubs = {
            "keywords": mock.Mock(**{"summary.return_value": {
                "share_pct": 0.0, "coverage_pct": 42.3, "total": 239,
                "top3": 0, "top10": 22, "ranked_known": 58, "covered": 101,
                "by_town": {}, "by_intent": {}, "gaps": [], "ranked": [],
                "excluded_out_of_area": {"count": 0, "queries": []}}}),
            "review": mock.Mock(**{"scoreboard.return_value": {
                "works": [], "does_not_work": [], "not_yet_judged": []}}),
            "ledger": mock.Mock(**{"load_techniques.return_value": [],
                                   "get_state.return_value": gsc_last,
                                   "today.return_value": "2026-10-22",
                                   "series.side_effect": series}),
            "metrics": mock.Mock(**{"lead_totals.return_value": {}}),
            "gsc": mock.Mock(**{"discover.return_value": [],
                                "page_report.return_value": []}),
            "indexstatus": mock.Mock(**{"summary.return_value": {}}),
        }
        with mock.patch.multiple(S, **stubs), \
             mock.patch.object(S, "_page_inventory", return_value={}):
            return S.build("/nonexistent")

    def test_build_publishes_a_dated_row_per_rank_metric(self):
        snap = self._build(dict(self.GSC_LAST))
        series = snap["gsc"]["series"]
        self.assertEqual(set(series), set(S.GSC_SERIES))
        self.assertEqual(series["gsc_position"][-1],
                         {"date": "2026-10-22", "value": 3})

    def test_the_goal_metric_is_one_of_them(self):
        # The owner's goal is a top-3 share. A history of everything except
        # the goal would be the same gap in a longer file.
        snap = self._build(dict(self.GSC_LAST))
        self.assertIn("goal_top3", snap["gsc"]["series"])
        self.assertIn("goal_share_pct", snap["gsc"]["series"])

    def test_the_single_row_is_still_published_beside_the_series(self):
        snap = self._build(dict(self.GSC_LAST))
        self.assertEqual(snap["gsc"]["avg_position"], 26.1)
        self.assertEqual(snap["gsc"]["impressions"], 5281)

    def test_no_gsc_state_still_publishes_null_not_an_empty_report(self):
        """"gsc": null has to keep meaning "no rank data has ever existed"."""
        snap = self._build(None)
        self.assertIsNone(snap["gsc"])

    def test_the_window_is_longer_than_the_traffic_window_and_is_applied(self):
        # Google's confirmed ranking updates are weeks apart; a window shorter
        # than the gap between them cannot tell one from the other. Asserted
        # by publishing a longer history than the cap, so this fails if the
        # days argument is ever dropped at the call site.
        self.assertGreater(S.GSC_SERIES_DAYS, 45)
        long_history = [(f"2026-{m:02d}-{d:02d}", d)
                        for m in (6, 7, 8, 9, 10) for d in range(1, 29)]
        self.assertGreater(len(long_history), S.GSC_SERIES_DAYS)
        with mock.patch.object(S, "_series", wraps=S._series) as spy:
            stubs_series = long_history

            def series(technique, metric, *a, **kw):
                return stubs_series

            snap = self._build_with_series(dict(self.GSC_LAST), series)
        self.assertEqual(len(snap["gsc"]["series"]["gsc_position"]),
                         S.GSC_SERIES_DAYS)
        self.assertTrue(spy.called)

    def test_survives_the_pii_scrub_unchanged(self):
        """Dates and counts must not look like anything redacted."""
        block = {"series": {"gsc_position": [{"date": "2026-10-22",
                                              "value": 26.1}]}}
        clean, found = S.scrub({"gsc": block})
        self.assertEqual(clean["gsc"], block)
        self.assertEqual(found, [])


def _real_summary(cache):
    """indexstatus.summary() itself — imported here so the stub above cannot
    be mistaken for a hand-written copy of the block's shape."""
    from . import indexstatus
    return indexstatus.summary(cache)


if __name__ == "__main__":
    unittest.main()

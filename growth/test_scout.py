#!/usr/bin/env python3
"""Tests for what the scout is told about the site it is scouting for.

Added 2026-08-08. `build_prompt()` hardcoded "four service pages, five town
service-area pages, three guides" from the day the engine was seeded. Twelve
days later the real figures were 7, 15 and 15, so every scout run since had
been reasoning about a site a third of the real size — which is how you get
proposals to write a page that already exists.

The same run found the other half of the problem: the docstring called new
tracked queries "pure upside", while `keywords.py:296` makes every one of them
the denominator of the goal metric and `strengthen_pages` covers exactly one a
day. Intake ran at ~5.4/day against a drain of 1, so the uncovered backlog went
64 -> 92 in a week. The prompt now states that depth so the model can weigh it.

No network and no droplet state — the page counts come from a tmpdir and the
keyword summary is patched.

Run: python3 -m growth.test_scout   (from the repo root)
"""
import os
import shutil
import tempfile
import unittest
from unittest import mock

from . import scout as S


def _make_site(root, areas=0, guides=0, services=0):
    for sub, n in (("areas", areas), ("guides", guides), ("services", services)):
        d = os.path.join(root, sub)
        os.makedirs(d, exist_ok=True)
        for i in range(n):
            with open(os.path.join(d, f"page-{i}.html"), "w") as f:
                f.write("<html></html>")
    return root


SUMMARY = {"total": 146, "covered": 54, "coverage_pct": 37.0, "ranked_known": 23,
           "top3": 1, "top10": 8, "share_pct": 0.7, "by_town": {}, "by_intent": {},
           "ranked": []}


class PageCountsTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)

    def test_counts_what_is_on_disk(self):
        _make_site(self.root, areas=15, guides=15, services=7)
        self.assertEqual(S._page_counts(self.root),
                         {"areas": 15, "guides": 15, "services": 7})

    def test_only_html_counts(self):
        _make_site(self.root, areas=2)
        # A backup or a stray asset in areas/ is not a page.
        for name in ("seamless-gutters-dover-pa.html.bak", "hero.jpg"):
            open(os.path.join(self.root, "areas", name), "w").close()
        self.assertEqual(S._page_counts(self.root)["areas"], 2)

    def test_missing_directory_reads_zero_not_crash(self):
        # A fresh docroot, or a wrong --docroot, must not take the scout down.
        self.assertEqual(S._page_counts(self.root),
                         {"areas": 0, "guides": 0, "services": 0})
        self.assertEqual(S._page_counts("/no/such/path")["guides"], 0)

    def test_none_docroot_is_survivable(self):
        self.assertEqual(S._page_counts(None), {"areas": 0, "guides": 0, "services": 0})


class PromptTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        _make_site(self.root, areas=15, guides=15, services=7)
        for p, v in (("ledger.load_techniques", []),
                     ("review.scoreboard", {"works": [], "does_not_work": [],
                                            "not_yet_judged": []}),
                     ("keywords.summary", SUMMARY),
                     ("ledger.series", []),
                     ("ledger.today", "2026-08-08")):
            mod, attr = p.split(".")
            patcher = mock.patch.object(getattr(S, mod), attr,
                                        return_value=v if not isinstance(v, str) else v)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_prompt_names_the_real_page_counts(self):
        text = S.build_prompt(self.root)
        self.assertIn("7 service pages", text)
        self.assertIn("15 town service-area pages", text)
        self.assertIn("15 guides", text)
        # The figures that were frozen in since 2026-07-27 are gone.
        self.assertNotIn("four service pages", text)
        self.assertNotIn("five town", text)

    def test_prompt_states_the_backlog_depth(self):
        text = S.build_prompt(self.root)
        # 146 tracked - 54 covered = 92 uncovered, drained at one a day.
        self.assertIn("92 tracked queries are already", text)
        self.assertIn("ONE of them per day", text)

    def test_prompt_still_states_the_goal(self):
        # The backlog warning must not have displaced the goal line.
        self.assertIn("0.7% of 146 tracked queries in the top 3",
                      S.build_prompt(self.root))


if __name__ == "__main__":
    unittest.main()

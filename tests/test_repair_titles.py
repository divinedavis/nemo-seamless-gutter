#!/usr/bin/env python3
"""Tests for deploy/repair_titles.py.

Run:  scripts/test.sh            (everything)
      python3 -m unittest tests.test_repair_titles

This script rewrites live pages in the docroot, so the tests that matter most
are the ones about what it refuses to do: never edit the words of a title to
make it fit, never touch anything but the <title> element, never write without
--apply, and never mangle an entity while counting characters.
"""
import contextlib
import importlib.util
import io
import os
import shutil
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "deploy", "repair_titles.py")

# deploy/ is not a package (the scripts run standalone on the droplet, where
# there is no repo layout to import through), so load it by path.
_spec = importlib.util.spec_from_file_location("repair_titles", SCRIPT)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)


def page(title, h1="A Heading", extra=""):
    return (
        "<!doctype html><html><head><title>%s</title>"
        '<meta name="description" content="A description that is its own problem '
        'and is much longer than sixty-five characters on purpose.">'
        '<meta property="og:title" content="%s — NEMO Seamless Gutter">'
        "</head><body><h1>%s</h1>%s</body></html>" % (title, h1, h1, extra))


class StripBrand(unittest.TestCase):
    def test_strips_the_full_brand(self):
        self.assertEqual(
            mod.strip_brand("Ice Dam Removal in York, PA | NEMO Seamless Gutter"),
            "Ice Dam Removal in York, PA")

    def test_strips_the_short_brand(self):
        self.assertEqual(mod.strip_brand("Gutter Guards York PA | NEMO"),
                         "Gutter Guards York PA")

    def test_loops_until_stable(self):
        # The live bug: the old generator appended " | NEMO Seamless Gutter" to
        # a model title that already ended " | NEMO Seamless". One sub() leaves
        # a brand behind and the refit would then bolt a third one on.
        self.assertEqual(
            mod.strip_brand(
                "Commercial Gutter Installation York PA | NEMO Seamless "
                "| NEMO Seamless Gutter"),
            "Commercial Gutter Installation York PA")

    def test_a_title_that_is_only_the_brand_becomes_empty(self):
        self.assertEqual(mod.strip_brand("NEMO Seamless Gutter"), "")
        self.assertEqual(mod.strip_brand("NEMO"), "")

    def test_a_york_phrase_is_not_mistaken_for_the_brand(self):
        self.assertEqual(mod.strip_brand("Seamless Gutters in York, PA"),
                         "Seamless Gutters in York, PA")


class FitTitle(unittest.TestCase):
    def test_keeps_the_full_brand_when_it_fits(self):
        self.assertEqual(mod.fit_title("York Gutters | NEMO Seamless Gutter"),
                         "York Gutters | NEMO Seamless Gutter")

    def test_falls_back_to_the_short_brand(self):
        out = mod.fit_title(
            "Gutter Services in York County PA: Costs & What to Expect "
            "| NEMO Seamless Gutter")
        self.assertEqual(
            out,
            "Gutter Services in York County PA: Costs & What to Expect | NEMO")
        self.assertLessEqual(len(out), mod.TITLE_MAX)

    def test_refuses_to_cut_words_when_the_phrase_alone_is_over(self):
        # growth.techniques._page_title truncates here because at generation
        # time something has to ship. There is already a live title doing its
        # job, so this returns None and the caller reports it for a human.
        long_phrase = "A" * (mod.TITLE_MAX + 5)
        self.assertIsNone(mod.fit_title(long_phrase))

    def test_falls_back_to_the_h1_when_the_title_is_only_the_brand(self):
        self.assertEqual(mod.fit_title("NEMO Seamless Gutter", "Ice Dams in PA"),
                         "Ice Dams in PA | NEMO Seamless Gutter")

    def test_is_idempotent(self):
        once = mod.fit_title(
            "Gutter Pulling Away From House: Causes & Repair Costs "
            "| NEMO Seamless Gutter")
        self.assertEqual(mod.fit_title(once), once)


class RepairMarkup(unittest.TestCase):
    def test_length_is_measured_on_the_rendered_text_not_the_markup(self):
        # "&amp;" is five characters of markup and one of title. Measuring the
        # markup would call this 68 and shorten a title that already fits.
        title = "Gutter Guards &amp; Leaf Protection York | NEMO"
        src = page(title)
        new, old, fitted, note = mod.repair_markup(src)
        self.assertIsNone(note)
        self.assertEqual(len(old), 43)
        self.assertEqual(fitted, old)
        self.assertEqual(new, src)

    def test_a_fitting_title_is_left_alone_even_when_the_refit_differs(self):
        # setup.html: 44 characters, an em-dash separator, perfectly fine.
        # fit_title would rewrite it to " | " for no reason but house style.
        src = page("Connect your calendar — NEMO Seamless Gutter")
        self.assertEqual(
            mod.fit_title("Connect your calendar — NEMO Seamless Gutter"),
            "Connect your calendar | NEMO Seamless Gutter")
        new, old, fitted, note = mod.repair_markup(src)
        self.assertIsNone(note)
        self.assertEqual(new, src)
        self.assertEqual(fitted, old)

    def test_a_short_title_branded_twice_is_still_repaired(self):
        # Under the limit, so the length test alone would skip it.
        src = page("Gutters | NEMO | NEMO")
        new, old, fitted, note = mod.repair_markup(src)
        self.assertIsNone(note)
        self.assertLess(len(old), mod.TITLE_MAX)
        self.assertEqual(fitted, "Gutters | NEMO Seamless Gutter")
        self.assertNotEqual(new, src)

    def test_the_entity_survives_a_rewrite(self):
        title = ("Gutter Guys Near Me | York County PA Costs &amp; Hiring "
                 "| NEMO Seamless Gutter")
        new, _old, fitted, note = mod.repair_markup(page(title))
        self.assertIsNone(note)
        self.assertIn("Costs &amp; Hiring | NEMO</title>", new)
        self.assertIn("&", fitted)

    def test_nothing_but_the_title_element_is_touched(self):
        src = page("Ice Dams and Gutters in PA: Causes and 2026 Costs "
                   "| NEMO Seamless Gutter")
        new, _old, _fitted, _note = mod.repair_markup(src)
        self.assertNotEqual(new, src)
        for survivor in ('<meta name="description"', '<meta property="og:title"',
                         "<h1>A Heading</h1>"):
            self.assertIn(survivor, new)
        # The over-long description is a different problem with a different
        # limit (165), and this script does not have an opinion about it.
        self.assertEqual(src.count("much longer than sixty-five"),
                         new.count("much longer than sixty-five"))

    def test_an_unshortenable_title_is_reported_and_left_alone(self):
        title = "%s | NEMO Seamless Gutter" % ("Word " * 20).strip()
        src = page(title)
        new, old, fitted, note = mod.repair_markup(src)
        self.assertEqual(new, src)
        self.assertIsNone(fitted)
        self.assertIn("human", note)
        self.assertGreater(len(old), mod.TITLE_MAX)

    def test_a_page_with_no_title_is_reported_not_crashed(self):
        new, _old, _fitted, note = mod.repair_markup("<html><body>x</body></html>")
        self.assertEqual(note, "no <title> element")
        self.assertEqual(new, "<html><body>x</body></html>")

    def test_an_empty_title_is_reported(self):
        _new, _old, _fitted, note = mod.repair_markup(page(""))
        self.assertEqual(note, "<title> is empty")


class MainOnDisk(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        os.mkdir(os.path.join(self.root, "guides"))
        self.rel = "guides/long.html"
        self.path = os.path.join(self.root, self.rel)
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write(page("Seamless Gutter Cost in York County, PA (2026 Guide) "
                          "| NEMO Seamless Gutter"))
        # A root-level page, to pin that the docroot itself is scanned and not
        # only areas/ guides/ services/ — index.html lives there.
        with open(os.path.join(self.root, "index.html"), "w",
                  encoding="utf-8") as fh:
            fh.write(page("Gutter Repair & Installation in York County PA "
                          "| NEMO Seamless Gutter"))

    def run_main(self, *argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = mod.main(["--root", self.root] + list(argv))
        return rc, buf.getvalue()

    def read(self):
        with open(self.path, encoding="utf-8") as fh:
            return fh.read()

    def test_report_only_writes_nothing(self):
        before = self.read()
        rc, out = self.run_main()
        self.assertEqual(rc, 0)
        self.assertEqual(self.read(), before)
        self.assertIn("Report only", out)
        self.assertFalse(os.path.exists(self.path + mod.BACKUP_SUFFIX))

    def test_apply_rewrites_and_backs_up(self):
        before = self.read()
        rc, out = self.run_main("--apply")
        self.assertEqual(rc, 0)
        self.assertIn("backed up", out)
        self.assertIn("(2026 Guide) | NEMO</title>", self.read())
        with open(self.path + mod.BACKUP_SUFFIX, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), before)

    def test_a_second_apply_is_a_noop(self):
        self.run_main("--apply")
        after_first = self.read()
        rc, out = self.run_main("--apply")
        self.assertEqual(rc, 0)
        self.assertIn("Nothing to do", out)
        self.assertEqual(self.read(), after_first)

    def test_the_root_level_page_is_scanned(self):
        _rc, out = self.run_main()
        self.assertIn("2 page(s) read", out)
        self.assertIn("index.html", out)


class AgainstTheLiveRepoCopies(unittest.TestCase):
    """The repo holds a read-only mirror of the live pages, so the script can
    be measured against the real thing rather than only against fixtures.

    This is the number the journal quotes. If it drifts, one of two things
    happened — growth/ was deployed and the generator now fits its own titles,
    or someone ran the repair on the droplet — and either way the journal's
    claim needs re-measuring rather than the test needs relaxing.
    """

    def test_every_over_long_live_title_is_refittable(self):
        found = mod.scan(ROOT)
        # 45 search-landing pages plus privacy.html and setup.html, which the
        # scan sees because it reads the docroot root and which it then leaves
        # alone because their titles are not broken.
        self.assertEqual(len(found), 47, "page count changed — re-measure")
        over = [f for f in found if f[3] and len(f[3]) > mod.TITLE_MAX]
        blocked = [f for f in found if f[5]]
        changed = [f for f in found if f[2] != f[1]]
        self.assertEqual(len(over), 25)
        self.assertEqual(blocked, [], "a live title now needs a human")
        self.assertEqual(len(changed), 25, "a fitting title would be churned")
        for _rel, _markup, _new, _old, fitted, _note in found:
            self.assertLessEqual(len(fitted), mod.TITLE_MAX)

    def test_the_double_branded_titles_end_with_one_brand(self):
        found = {f[0]: f[4] for f in mod.scan(ROOT)}
        doubled = ("services/commercial-gutters.html",
                   "guides/best-gutter-company-york-county-pa.html",
                   "guides/gutter-installer-near-me.html")
        for rel in doubled:
            self.assertEqual(found[rel].upper().count("NEMO"), 1, rel)


if __name__ == "__main__":
    unittest.main()

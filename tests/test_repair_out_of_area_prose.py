#!/usr/bin/env python3
"""Tests for deploy/repair_out_of_area_prose.py.

Run:  scripts/test.sh            (everything)
      python3 -m unittest tests.test_repair_out_of_area_prose

This script rewrites live pages in the docroot, so the tests that matter most
are the ones about what it refuses to do: skip a phrase that has drifted, leave
a trailing section alone rather than truncate the page at a guess, and report a
surviving place name instead of letting a partial repair look clean.
"""
import contextlib
import importlib.util
import io
import os
import shutil
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "deploy", "repair_out_of_area_prose.py")

# deploy/ is not a package (the scripts run standalone on the droplet, where
# there is no repo layout to import through), so load it by path.
_spec = importlib.util.spec_from_file_location("repair_out_of_area_prose", SCRIPT)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)


SCHUYLKILL = """\
      <h2>Gutter Replacement Near You in York County, PA</h2>
      <p>Good copy that must survive.</p>

      <h2>Seamless Gutter Installation in Schuylkill County, PA</h2>
      <p>We cover Pottsville, Tamaqua and the coal region.</p>
      <h3>Do you actually service Schuylkill County?</h3>
      <p>We service both.</p>

      <h2>What to Ask Gutter Installers in York County Before You Hire</h2>
      <p>Also good copy.</p>
"""


class OffAreaName(unittest.TestCase):
    def test_york_county_is_not_off_area(self):
        self.assertIsNone(mod.off_area_name("We work across York County, PA."))

    def test_another_county_is_off_area(self):
        self.assertEqual(
            mod.off_area_name("the same work travels to Schuylkill County"),
            "Schuylkill County")

    def test_named_town_is_off_area(self):
        self.assertEqual(mod.off_area_name("homes in Akron, PA"), "akron")

    def test_word_boundaries_keep_a_york_neighborhood(self):
        # "york ne" is in OUT_OF_AREA for York, Nebraska; a substring test
        # would reject this perfectly good sentence.
        self.assertIsNone(mod.off_area_name("a York neighborhood we serve"))

    def test_lowercase_the_county_is_not_a_county_name(self):
        self.assertIsNone(mod.off_area_name("anywhere in the county"))

    def test_schema_area_served_is_not_read_as_prose(self):
        markup = ('<script type="application/ld+json">'
                  '{"areaServed": "Lancaster County"}</script>'
                  "<p>We work in York County.</p>")
        self.assertIsNone(mod.off_area_name(mod._visible_text(markup)))


class SectionCut(unittest.TestCase):
    def test_cuts_the_offending_section_only(self):
        new, changed, blocked = mod.repair_markup("services/x.html", SCHUYLKILL)
        self.assertEqual(blocked, [])
        self.assertEqual(len(changed), 1)
        self.assertNotIn("Schuylkill", new)
        self.assertNotIn("Pottsville", new)
        self.assertIn("Gutter Replacement Near You in York County", new)
        self.assertIn("What to Ask Gutter Installers", new)
        self.assertIn("Also good copy.", new)

    def test_repair_is_idempotent(self):
        once, _, _ = mod.repair_markup("services/x.html", SCHUYLKILL)
        twice, changed, blocked = mod.repair_markup("services/x.html", once)
        self.assertEqual((changed, blocked), ([], []))
        self.assertEqual(once, twice)

    def test_trailing_section_is_refused_not_truncated(self):
        markup = ("      <h2>Good heading</h2>\n      <p>Keep me.</p>\n"
                  "      <h2>Work in Schuylkill County, PA</h2>\n"
                  "      <p>Bad.</p>\n    </article>\n  </body>\n</html>\n")
        new, changed, blocked = mod.repair_markup("services/x.html", markup)
        self.assertEqual(changed, [])
        self.assertEqual(len(blocked), 1)
        self.assertIn("no following", blocked[0])
        self.assertEqual(new, markup)

    def test_two_offending_sections_both_go(self):
        markup = ("<h2>Akron, PA Gutters</h2><p>a</p>"
                  "<h2>Schuylkill County Gutters</h2><p>b</p>"
                  "<h2>York County Gutters</h2><p>c</p>")
        new, changed, blocked = mod.repair_markup("services/x.html", markup)
        self.assertEqual(blocked, [])
        self.assertEqual(len(changed), 2)
        self.assertEqual(new, "<h2>York County Gutters</h2><p>c</p>")

    def test_heading_is_what_counts_not_a_passing_mention(self):
        markup = ("<h2>Gutter guards in York County</h2>"
                  "<p>We once worked a job near Akron.</p>"
                  "<h2>Next</h2>")
        new, changed, blocked = mod.repair_markup("services/x.html", markup)
        self.assertEqual((changed, blocked), ([], []))
        self.assertEqual(new, markup)


class PhraseSwap(unittest.TestCase):
    def setUp(self):
        self.rel, self.old, self.new = mod.PHRASES[0]

    def test_the_table_matches_the_live_page(self):
        # The whole point of an exact-match table is that it rots silently.
        # If this fails, the page's copy changed and PHRASES needs re-checking
        # against it — do not just delete the assertion.
        path = os.path.join(ROOT, *self.rel.split("/"))
        if not os.path.exists(path):
            self.skipTest("%s is not in this checkout" % self.rel)
        self.assertIn(self.old, read(path))

    def test_swap_removes_the_place_names_and_keeps_the_rest(self):
        markup = ('<p class="lead">%s More copy. Call (717) 578-0073.</p>'
                  % self.old)
        out, changed, blocked = mod.repair_markup(self.rel, markup)
        self.assertEqual(blocked, [])
        self.assertEqual(len(changed), 1)
        self.assertIsNone(mod.off_area_name(mod._visible_text(out)))
        self.assertIn("More copy. Call (717) 578-0073.", out)

    def test_swap_text_itself_is_in_area(self):
        self.assertIsNone(mod.off_area_name(self.new))

    def test_drifted_copy_is_skipped_not_mangled(self):
        markup = '<p class="lead">Gutter guards on homes in Akron, PA.</p>'
        out, changed, blocked = mod.repair_markup(self.rel, markup)
        self.assertEqual(changed, [])
        self.assertEqual(len(blocked), 1)
        self.assertIn("byte-for-byte", blocked[0])
        self.assertEqual(out, markup)

    def test_swap_does_not_apply_to_another_page(self):
        markup = "<p>%s</p>" % self.old
        out, changed, blocked = mod.repair_markup("services/other.html", markup)
        self.assertEqual((changed, blocked), ([], []))
        self.assertEqual(out, markup)


def run_main(argv):
    """main() with its report swallowed — these tests assert on files, and the
    report is several screens of noise in the middle of a passing suite."""
    with contextlib.redirect_stdout(io.StringIO()):
        return mod.main(argv)


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


class ScanAndApply(unittest.TestCase):
    def _docroot(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root, True)
        os.makedirs(os.path.join(root, "services"))
        with open(os.path.join(root, "services", "a.html"), "w",
                  encoding="utf-8") as fh:
            fh.write(SCHUYLKILL)
        with open(os.path.join(root, "services", "clean.html"), "w",
                  encoding="utf-8") as fh:
            fh.write("<h2>York County Gutters</h2><p>Fine.</p>")
        return root

    def test_scan_reports_only_the_offending_page(self):
        root = self._docroot()
        found = mod.scan(root)
        self.assertEqual([f[0] for f in found], ["services/a.html"])
        self.assertIsNone(found[0][5], "nothing should be left over")

    def test_report_mode_writes_nothing(self):
        root = self._docroot()
        path = os.path.join(root, "services", "a.html")
        before = read(path)
        self.assertEqual(run_main(["--root", root]), 0)
        self.assertEqual(read(path), before)
        self.assertFalse(os.path.exists(path + mod.BACKUP_SUFFIX))

    def test_apply_rewrites_and_backs_up(self):
        root = self._docroot()
        path = os.path.join(root, "services", "a.html")
        before = read(path)
        self.assertEqual(run_main(["--root", root, "--apply"]), 0)
        after = read(path)
        self.assertNotIn("Schuylkill", after)
        self.assertIn("Also good copy.", after)
        self.assertEqual(read(path + mod.BACKUP_SUFFIX), before)

    def test_second_apply_is_a_no_op(self):
        root = self._docroot()
        run_main(["--root", root, "--apply"])
        path = os.path.join(root, "services", "a.html")
        after = read(path)
        self.assertEqual(run_main(["--root", root, "--apply"]), 0)
        self.assertEqual(read(path), after)

    def test_clean_docroot_reports_nothing(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root, True)
        os.makedirs(os.path.join(root, "guides"))
        with open(os.path.join(root, "guides", "g.html"), "w",
                  encoding="utf-8") as fh:
            fh.write("<p>Gutters across York County, PA.</p>")
        self.assertEqual(mod.scan(root), [])
        self.assertEqual(run_main(["--root", root, "--apply"]), 0)


if __name__ == "__main__":
    unittest.main()

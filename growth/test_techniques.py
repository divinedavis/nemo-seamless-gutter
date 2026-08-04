#!/usr/bin/env python3
"""Tests for the two routing guards added after the 2026-08-01 review.

Both exist because the engine did the wrong thing on a real morning and the
build log said "ok":

  - improve_ctr rewrote the homepage title to "Gutter Installer & Contractor"
    on 2026-07-27, dropping "York, PA" from the site's strongest page.
  - money_pages published /guides/york-gutters.html on 2026-08-01, one day
    after /guides/gutters-york-pa.html, for the same question.

Run: python3 -m growth.test_techniques   (from the repo root)
"""
import json
import os
import re
import tempfile
import unittest

from . import techniques as T


class GeoAnchorTest(unittest.TestCase):
    def test_rejects_the_title_that_shipped(self):
        self.assertIsNone(
            T.GEO_ANCHOR.search("Gutter Installer & Contractor | NEMO Seamless Gutter"))

    def test_accepts_the_title_it_replaced(self):
        self.assertTrue(
            T.GEO_ANCHOR.search("Seamless Gutters in York, PA | NEMO Seamless Gutter"))

    def test_pa_is_bounded(self):
        # "repair" and "page" contain "pa" and must not count as a place name.
        self.assertIsNone(T.GEO_ANCHOR.search("Gutter repair on every page"))

    def test_county_and_state_spellings_count(self):
        self.assertTrue(T.GEO_ANCHOR.search("Serving York County"))
        self.assertTrue(T.GEO_ANCHOR.search("Gutters across Pennsylvania"))


class _Ctx:
    """Just enough Context to route against a throwaway docroot."""

    def __init__(self, docroot):
        self.docroot = docroot

    def read(self, relpath):
        p = os.path.join(self.docroot, relpath.lstrip("/"))
        return open(p).read() if os.path.isfile(p) else None


class TopicGuideTest(unittest.TestCase):
    GUIDES = ("gutters-york-pa.html",
              "5-vs-6-inch-gutters-right-size-for-york-county-homes.html",
              "best-gutter-company-york-county-pa.html")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        os.makedirs(os.path.join(self.tmp.name, "guides"))
        for f in self.GUIDES:
            open(os.path.join(self.tmp.name, "guides", f), "w").write("<html>")
        self.ctx = _Ctx(self.tmp.name)

    def test_the_duplicate_that_shipped_now_routes(self):
        # "york gutters" the morning after "gutters york pa" got its own page.
        self.assertEqual(T._topic_guide(self.ctx, "york gutters"),
                         "/guides/gutters-york-pa.html")

    def test_size_phrasings_join_the_size_guide(self):
        for q in ("5 inch vs 6 inch gutters",
                  "5 inch vs 6 inch gutters which is better",
                  "what size gutters do i need"):
            self.assertEqual(
                T._topic_guide(self.ctx, q),
                "/guides/5-vs-6-inch-gutters-right-size-for-york-county-homes.html",
                msg=q)

    def test_a_genuinely_new_topic_still_gets_its_own_page(self):
        for q in ("gutter pulling away from house",
                  "ice dams gutters pennsylvania",
                  "do i need gutters on my house"):
            self.assertIsNone(T._topic_guide(self.ctx, q), msg=q)

    def test_tightest_guide_wins(self):
        # "gutter company york" is contained by two guides; the shorter one is
        # the page actually about it.
        self.assertEqual(T._topic_guide(self.ctx, "gutter company york"),
                         "/guides/best-gutter-company-york-county-pa.html")

    def test_one_content_word_is_too_thin_to_match(self):
        self.assertIsNone(T._topic_guide(self.ctx, "gutters"))

    def test_no_guides_directory_is_not_an_error(self):
        blank = tempfile.TemporaryDirectory()
        self.addCleanup(blank.cleanup)
        self.assertIsNone(T._topic_guide(_Ctx(blank.name), "york gutters"))


class JsonLdEscapingTest(unittest.TestCase):
    """Model text lands in JSON-LD, which sits inside a <script> block.

    json.dumps escapes quotes but not '/', so before _ld() a model that wrote
    "</script>" anywhere in an FAQ answer closed the block and everything after
    it became live HTML on an auto-published page.
    """

    EVIL = 'Twice a year.</script><script>alert(1)</script>'

    def test_faq_answer_cannot_close_the_script_block(self):
        out = T._faq_ld([{"q": "How often?", "a": self.EVIL}])
        self.assertNotIn("</script>", out)
        self.assertNotIn("<script", out)

    def test_faq_question_cannot_close_the_script_block(self):
        out = T._faq_ld([{"q": self.EVIL, "a": "Twice a year."}])
        self.assertNotIn("</script>", out)

    def test_escaping_is_invisible_to_a_json_ld_consumer(self):
        # Google must still read the real text — < is a JSON escape, not a
        # content change. If this breaks, the schema is silently wrong.
        out = T._faq_ld([{"q": "How often?", "a": self.EVIL}])
        back = json.loads(out)
        self.assertEqual(
            back["mainEntity"][0]["acceptedAnswer"]["text"], self.EVIL)

    def test_html_comment_open_is_escaped_too(self):
        out = T._ld({"description": "<!--"})
        self.assertNotIn("<!--", out)

    def test_no_ld_call_site_passes_indent(self):
        """_ld sets its own indent. The three page builders were converted from
        json.dumps(..., indent=2), and leaving that argument behind is a
        TypeError that only fires when a technique actually runs — which the
        unit tests do not do, because those paths need a live model call. This
        catches it in the source instead."""
        src = open(os.path.join(os.path.dirname(__file__), "techniques.py")).read()
        # Every _ld( ... ) call, brace-matched to its closing paren.
        for m in re.finditer(r"\b_ld\(", src):
            depth, i = 0, m.end() - 1
            while i < len(src):
                if src[i] in "([{":
                    depth += 1
                elif src[i] in ")]}":
                    depth -= 1
                    if depth == 0:
                        break
                i += 1
            self.assertNotIn("indent=", src[m.end():i],
                             msg=f"_ld() call near offset {m.start()} still passes indent=")


class OffAreaProseTest(unittest.TestCase):
    """The answer-first block is the passage an AI engine quotes verbatim.

    `_names_other_market` filters the query going in. Until 2026-08-03 nothing
    checked what came back out, and what came back out on 2026-07-29 is still
    live on /services/gutter-guards.html.
    """

    SHIPPED = ("NEMO Seamless Gutter installs gutter guards on homes in Akron, "
               "PA and the surrounding Lancaster and York County area. We fit "
               "micro-mesh and screen-style covers over existing or new seamless "
               "gutters, matched to your roof pitch and the trees around the house.")

    def test_rejects_the_paragraph_that_shipped(self):
        self.assertEqual(T._off_area_prose(self.SHIPPED), "akron")

    def test_rejects_a_neighbouring_county_on_its_own(self):
        # The dangerous shape: grammatical, plausible, and no banned town in it.
        self.assertEqual(
            T._off_area_prose("We install seamless gutters across Lancaster "
                              "County and the surrounding area."),
            "Lancaster County")

    def test_accepts_the_copy_it_should_have_written(self):
        self.assertIsNone(T._off_area_prose(
            "NEMO Seamless Gutter installs gutter guards on homes across York "
            "County, Pennsylvania. We fit micro-mesh and screen-style covers "
            "over existing or new seamless gutters."))

    def test_york_county_itself_is_never_the_offender(self):
        self.assertIsNone(T._off_area_prose("Serving all of York County, PA."))

    def test_a_lowercase_county_is_not_a_place_name(self):
        # "the county" and "your county" must not read as somebody else's.
        self.assertIsNone(T._off_area_prose("Prices vary across the county."))

    def test_york_nebraska_does_not_reject_a_york_neighborhood(self):
        # OUT_OF_AREA holds "york ne"; a substring test fails this sentence.
        self.assertIsNone(T._off_area_prose(
            "We work in every York neighborhood, from Fireside to Springdale."))

    def test_new_york_is_still_out_of_area(self):
        self.assertEqual(T._off_area_prose("Serving New York and beyond."),
                         "new york")

    def test_the_guard_is_wired_into_the_answer_first_pass(self):
        """A guard nothing calls is a guard that does not exist — and this one
        cannot be reached by a unit test, because the path around it needs a
        live model call."""
        src = open(os.path.join(os.path.dirname(__file__), "techniques.py")).read()
        body = src[src.index("def geo_answer_first_content_pass"):]
        body = body[:body.index('return {"ok": True')]
        self.assertIn("_off_area_prose(answer)", body)
        self.assertIn("_off_area_prose(f\"{f['q']} {f['a']}\")", body)


class DuplicateBusinessNodeTest(unittest.TestCase):
    """local_schema appended a second business node instead of noticing one.

    index.html shipped with a hand-written RoofingContractor carrying
    @id .../#business. local_schema looked only for its own `data-growth`
    marker, found none on 2026-07-27, and added a second node with the same
    @id — then reported "LocalBusiness schema already current" every morning
    for the eight days since. The two disagree about opening hours: the
    hand-written one says Mon-Fri 07:30-18:00 and Saturday 08:00-14:00, the
    generated one says Mon-Fri 07:00-18:00 and no Saturday at all.
    """

    HAND_WRITTEN = (
        '<script type="application/ld+json">\n'
        '{"@context":"https://schema.org","@type":"RoofingContractor",'
        '"@id":"https://nemoseamlessgutter.com/#business",'
        '"openingHoursSpecification":[{"opens":"07:30","closes":"18:00"}]}\n'
        '</script>\n')

    def _docroot(self, index_html):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        with open(os.path.join(tmp.name, "index.html"), "w") as f:
            f.write(index_html)
        return _Ctx(tmp.name)

    def test_finds_the_node_that_shipped(self):
        lines = T._foreign_ld_nodes(
            "<head>\n" + self.HAND_WRITTEN + "</head>",
            "https://nemoseamlessgutter.com/#business")
        self.assertEqual(lines, [2])

    def test_our_own_block_is_not_a_conflict_with_itself(self):
        src = ("<head>\n  " + T.LB_MARKER + "\n"
               '{"@id":"https://nemoseamlessgutter.com/#business"}\n'
               "  </script>\n</head>")
        self.assertEqual(
            T._foreign_ld_nodes(src, "https://nemoseamlessgutter.com/#business"),
            [])

    def test_an_unrelated_ld_block_is_not_a_conflict(self):
        src = ('<head>\n<script type="application/ld+json">\n'
               '{"@type":"FAQPage","@id":"https://nemoseamlessgutter.com/#faq"}\n'
               '</script>\n</head>')
        self.assertEqual(
            T._foreign_ld_nodes(src, "https://nemoseamlessgutter.com/#business"),
            [])

    def test_local_schema_refuses_to_add_a_second_node(self):
        ctx = self._docroot("<head>\n" + self.HAND_WRITTEN + "</head><body></body>")
        r = T.local_schema(ctx)
        self.assertFalse(r["ok"])
        self.assertIn("#business", r["detail"])
        self.assertIn("openingHoursSpecification", r["detail"])

    def test_the_refusal_writes_nothing(self):
        ctx = self._docroot("<head>\n" + self.HAND_WRITTEN + "</head><body></body>")
        before = ctx.read("index.html")
        T.local_schema(ctx)
        # _Ctx has no write(); reaching it at all would raise AttributeError.
        self.assertEqual(ctx.read("index.html"), before)

    def test_a_clean_page_is_still_writable(self):
        """The guard must not block the case it was always meant to serve."""
        ctx = self._docroot("<head>\n<title>x</title>\n</head><body></body>")
        self.assertEqual(
            T._foreign_ld_nodes(ctx.read("index.html"),
                                "https://nemoseamlessgutter.com/#business"),
            [])

    def test_conflict_is_reported_before_anything_is_written(self):
        src = open(os.path.join(os.path.dirname(__file__), "techniques.py")).read()
        body = src[src.index("def local_schema"):]
        body = body[:body.index("ctx.write")]
        self.assertLess(body.index("_foreign_ld_nodes"), body.index("blob = _ld("))


if __name__ == "__main__":
    unittest.main()

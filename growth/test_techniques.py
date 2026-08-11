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


class StrengthenPagesGeoGuardTest(unittest.TestCase):
    """strengthen_pages read the uncovered queue without the geo filter.

    On 2026-08-10 it took 'schuylkill county seamless gutter' — adopted before
    `_names_other_market` existed, so the intake filter never saw it — off the
    front of the queue and wrote three paragraphs about Pottsville, Frackville
    and Mahanoy City onto /services/seamless-gutter-installation.html, the
    site's main money page. The build log said "ok".

    Both halves are tested here because they fail differently: the queue filter
    stops an out-of-area *query* being chosen, and the prose filter stops an
    in-area query whose *answer* wanders. Neither can be reached end to end by a
    unit test — the path between them is a live model call — so the wiring is
    asserted against the source, the way the answer-first guard already is.
    """

    def _body(self):
        src = open(os.path.join(os.path.dirname(__file__), "techniques.py")).read()
        body = src[src.index("def strengthen_pages"):]
        return body[:body.index("# ----------------------------------------------------------- service pages")]

    def test_the_query_that_shipped_is_rejected_by_the_queue_filter(self):
        self.assertTrue(T._names_other_market("schuylkill county seamless gutter"))

    def test_york_county_queries_still_pass_the_queue_filter(self):
        for q in ("gutter repair dover pa", "seamless gutter installation york pa",
                  "half round gutter installation york county",
                  "how much to replace gutters on a 1500 sq ft house"):
            self.assertFalse(T._names_other_market(q), msg=q)

    def test_the_queue_filter_is_wired_into_the_build_queue(self):
        self.assertIn('_names_other_market(k["query"])', self._body())

    def test_the_prose_guard_is_wired_into_the_generated_section(self):
        body = self._body()
        self.assertIn("_off_area_prose", body)
        # The heading is the part that becomes an <h2> and gets quoted; a check
        # that only read the paragraphs would have passed the section that
        # shipped, whose h2 was "Seamless Gutter Installation in Schuylkill
        # County, PA".
        self.assertIn('data["h2"]', body[body.index("_off_area_prose"):])

    def test_the_heading_that_shipped_is_caught_by_the_prose_guard(self):
        self.assertEqual(
            T._off_area_prose("Seamless Gutter Installation in Schuylkill County, PA"),
            "Schuylkill County")

    def test_the_faq_that_shipped_is_caught_by_the_prose_guard(self):
        self.assertEqual(
            T._off_area_prose(
                "Do you actually service Schuylkill County, or just the York area? "
                "We service both."),
            "Schuylkill County")

    def test_a_clean_york_county_section_survives_both_guards(self):
        text = ("What Gutter Repair in Dover Looks Like, Start to Finish "
                "We re-hang sagging runs across York County with hidden hangers "
                "spaced to the roof pitch.")
        self.assertIsNone(T._off_area_prose(text))
        self.assertFalse(T._names_other_market("gutter repair dover pa"))


class WholePageGeoGuardTest(unittest.TestCase):
    """The 2026-08-11 audit of the three techniques that build whole pages.

    2026-08-10 fixed `strengthen_pages`, which writes a *section*. The entry
    that day promised to check whether the same hole existed in the techniques
    that write *pages*, and it did:

      - `money_pages` read `keywords.load()` with only a "does this query need
        its own page" filter — no `_names_other_market` on the queue and no
        `_off_area_prose` on the reply. It was noop that morning only because
        no gap happened to qualify, which is luck, not a guard. It is the worse
        of the two failures: it writes a whole guide and records it as the
        query's target.
      - `area_pages` and `service_pages` read hand-written queues, so their
        input was never at risk — but neither checked what came back, and what
        comes back is what put Akron, PA on /services/gutter-guards.html.

    None of the three can be driven end to end by a unit test, because the step
    between the two guards is a live model call. So the guard functions are
    tested against the strings that actually shipped, and the wiring is
    asserted against the source — a guard nothing calls is a guard that does
    not exist, which is precisely how `_off_area_prose` passed its own tests
    for eleven days while the caller that needed it did not have it.
    """

    SRC = open(os.path.join(os.path.dirname(__file__), "techniques.py")).read()

    def _body(self, start, end):
        body = self.SRC[self.SRC.index(start):]
        return body[:body.index(end)]

    # --- the flattener the three pages share ---------------------------------

    def test_generated_prose_reads_headings_not_only_paragraphs(self):
        data = {"h1": "Seamless Gutters in Pottsville, PA",
                "sections": [{"h2": "Serving Schuylkill County, PA",
                              "paragraphs": ["We work across the region."]}]}
        self.assertEqual(T._off_area_prose(T._generated_prose(data)),
                         "Schuylkill County")

    def test_generated_prose_reads_bullets_and_faqs(self):
        for data in ({"sections": [{"h2": "Areas", "bullets": ["Akron, PA"]}]},
                     {"sections": [], "faqs": [{"q": "Do you cover Berks County?",
                                                "a": "We do."}]}):
            self.assertIsNotNone(T._off_area_prose(T._generated_prose(data)),
                                 msg=repr(data))

    def test_generated_prose_survives_a_malformed_reply(self):
        # The model returns a bare string or a number where a dict belongs
        # often enough that a guard which raises on it is a guard that takes
        # the build down instead of rejecting one page.
        data = {"title": None, "h1": 7, "sections": ["not a dict", {"h2": "Ok"}],
                "faqs": ["nope", {"q": "Q", "a": None}]}
        self.assertEqual(T._generated_prose(data), "Ok Q")

    def test_a_clean_york_county_page_passes_the_flattener(self):
        data = {"title": "Gutter Replacement Cost in York County, PA",
                "h1": "What New Gutters Cost in York County",
                "lede": "Honest ranges for a York, PA home.",
                "sections": [{"h2": "What drives the number",
                              "paragraphs": ["Roof pitch and linear feet."],
                              "bullets": ["Free on-site estimate"]}],
                "faqs": [{"q": "Do you serve Dover?", "a": "Yes, and Red Lion."}]}
        self.assertIsNone(T._off_area_prose(T._generated_prose(data)))

    # --- money_pages: the contaminable queue ---------------------------------

    def _money(self):
        return self._body("def money_pages", "# ------------------------------------------------------------- the link mesh")

    def test_money_pages_filters_its_queue(self):
        body = self._money()
        self.assertIn('_names_other_market(k["query"])', body)
        # The filter has to sit on the comprehension that builds `gaps`, not
        # somewhere later — `strengthen_pages` shipped with `_off_area_prose`
        # defined and uncalled, and this is the same mistake one line over.
        self.assertIn("_needs_its_own_page(k) and not _names_other_market", body)

    def test_money_pages_checks_what_comes_back(self):
        self.assertIn("_off_area_prose(_generated_prose(", self._money())

    def test_money_pages_rejects_a_candidate_without_losing_the_day(self):
        # A rejection must `continue` to the next gap. Returning would hand a
        # bad model reply the power to stop the only technique that can open a
        # new ranking page.
        body = self._money()
        after = body[body.index("_off_area_prose(_generated_prose("):]
        self.assertIn("continue", after[:400])
        self.assertNotIn("return", after[:after.index("continue")])

    def test_the_query_that_shipped_would_not_reach_money_pages(self):
        self.assertTrue(T._names_other_market("schuylkill county seamless gutter"))

    def test_the_fall_price_queue_still_passes_the_money_filter(self):
        # A filter that quietly emptied this queue would be a worse bug than
        # the one it fixes, and these are the queries the autumn season needs.
        for q in ("gutter cleaning cost per foot pennsylvania",
                  "gutter guard installation cost york pa",
                  "gutter replacement cost per foot york pa",
                  "how much do new gutters cost in pa",
                  "when should gutters be cleaned in pennsylvania"):
            self.assertFalse(T._names_other_market(q), msg=q)


    # --- area_pages and service_pages: safe queue, unchecked reply -----------

    def test_area_pages_checks_what_comes_back(self):
        body = self._body("def area_pages", "# ------------------------------------------------------------------ money pages")
        self.assertIn("_off_area_prose(_generated_prose(", body)

    def test_service_pages_checks_what_comes_back(self):
        body = self._body("def service_pages", "# ------------------------------------------------------------ click-through")
        self.assertIn("_off_area_prose(_generated_prose(", body)

    def test_the_akron_sentence_is_caught_wherever_it_appears(self):
        # Still live on /services/gutter-guards.html at the time of writing;
        # this asserts the guard would now stop it being written again.
        data = {"sections": [{"h2": "Gutter Guards", "paragraphs": [
            "NEMO Seamless Gutter installs gutter guards on homes in Akron, PA "
            "and the surrounding Lancaster and York County area."]}]}
        self.assertEqual(T._off_area_prose(T._generated_prose(data)), "akron")

class StatewideQueryTest(unittest.TestCase):
    """"Names Pennsylvania, names none of our towns" was not out of area.

    The rule read: a query that bothers to name a state and names none of our
    towns names someone else's. That is true of "seamless gutters perkasie pa"
    and false of "how much do new gutters cost in pa", because York County is
    *in* Pennsylvania.

    Found on 2026-08-11 by the test above, which was written to check that the
    filter being added to `money_pages` did not empty its own queue. It did:
    19 of the 104 queries in the live uncovered queue were being rejected as
    somebody else's market, 13 of them price-intent, including nearly the whole
    autumn cleaning-and-guards cluster. `strengthen_pages` picked the same
    filter up on 2026-08-10, so the regression was already written and waiting
    on a deploy — its own "does the filter empty the queue" test happened to
    choose four queries that all named a York County town.
    """

    STATEWIDE = ("how much do new gutters cost in pa",
                 "gutter guard cost pa",
                 "when should gutters be cleaned in pennsylvania",
                 "gutter cleaning cost per foot pennsylvania",
                 "seamless gutter cost per linear foot pa",
                 "copper half round gutters pennsylvania",
                 "ice dam gutter damage repair pa",
                 "gutter guards worth it pennsylvania leaves",
                 "cost to replace gutters on a ranch house pa",
                 "how much does it cost to replace gutters on a house in pa")

    ELSEWHERE = ("seamless gutters perkasie pa",
                 "seamless gutter contractors glenside pa",
                 "seamless gutter company royersford pa",
                 "seamless gutter contractor upper merion pa",
                 "seamless gutter contractors willow grove pa",
                 "seamless gutter company spring city pa",
                 "seamless gutter installation companies radnor pa",
                 "gutter installer new hope pa",
                 "schuylkill county seamless gutter",
                 "gutter repair lancaster county pa")

    def test_a_statewide_shopping_search_is_ours_to_answer(self):
        for q in self.STATEWIDE:
            self.assertFalse(T._names_other_market(q), msg=q)

    def test_naming_the_state_and_a_place_is_still_somebody_elses(self):
        for q in self.ELSEWHERE:
            self.assertTrue(T._names_other_market(q), msg=q)

    def test_spring_grove_is_ours_but_spring_city_is_not(self):
        # The near-miss that makes a plain town-name substring test dangerous:
        # "spring grove" is in SERVICE_AREA_WORDS and "spring city" is 80 miles
        # away, and they share their first word.
        self.assertFalse(T._names_other_market("gutter repair spring grove pa"))
        self.assertTrue(T._names_other_market("gutter repair spring city pa"))

    def test_a_geo_neutral_search_is_untouched(self):
        # The site's largest single source of impressions names no place at
        # all, and the rule must not start reading "no place" as "wrong place".
        for q in ("gutter installer", "gutter guys near me",
                  "seamless vs sectional gutters", "are gutter guards worth it"):
            self.assertFalse(T._names_other_market(q), msg=q)

    def test_an_unknown_word_fails_towards_rejection(self):
        # The documented failure mode, asserted so it stays deliberate: a trade
        # word missing from STATEWIDE_WORDS costs one query from a build queue
        # rather than letting an unrecognised town through.
        self.assertTrue(T._names_other_market("zincalume gutters pa"))


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

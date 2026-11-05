#!/usr/bin/env python3
"""Static-site checks: the pages the deploy ships are well-formed enough to serve.

Run:  scripts/test.sh            (everything)
      python3 -m unittest tests.test_site

These are the checks a visitor would notice first and a reviewer would miss:
a page without a viewport meta renders as a zoomed-out desktop page on every
phone (and iframe harnesses hide it), a relative link to a file that was never
committed is a 404 the growth engine then links to from everywhere, and a
booking mount point that lost its script is a homepage with no way to book.
"""
import json
import os
import re
import unittest
from urllib.parse import urljoin, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE_DIRS = ("", "areas", "services", "guides")
# Routes nginx proxies to the Node app or that analytics.js beacons to — they
# have no file on disk by design.
DYNAMIC = ("/api/", "/booking/", "/owner/", "/e/")


def pages():
    out = []
    for d in PAGE_DIRS:
        base = os.path.join(ROOT, d)
        for name in sorted(os.listdir(base)):
            if name.endswith(".html"):
                out.append(os.path.join(d, name) if d else name)
    return out


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def resolve(page_rel, ref):
    """Map an href/src on page_rel to a repo path, or None if not a local file.

    Resolved the way a browser does (urljoin), so "../styles.css" on a root
    page clamps to /styles.css rather than escaping the docroot.
    """
    if ref.startswith(("#", "mailto:", "tel:", "data:", "javascript:")):
        return None
    u = urlparse(ref)
    if u.scheme or u.netloc:
        return None
    path = urlparse(urljoin("https://site/" + page_rel, ref)).path
    if path.startswith(DYNAMIC):
        return None
    rel = path.lstrip("/")
    if rel == "" or rel.endswith("/"):
        rel += "index.html"
    return rel


LD_JSON = re.compile(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', re.S)
# schema.org has no gutter-specific type; the generator uses RoofingContractor.
BUSINESS_TYPES = {"RoofingContractor", "LocalBusiness",
                  "HomeAndConstructionBusiness", "GeneralContractor"}
PHONE_E164 = "+1-717-578-0073"


def _ld_nodes(block):
    """Every dict in a JSON-LD block, including nested ones (about/provider)."""
    try:
        doc = json.loads(block)
    except ValueError:
        return []
    out, stack = [], [doc]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            out.append(cur)
            stack.extend(cur.values())
        elif isinstance(cur, list):
            stack.extend(cur)
    return out


class PagesTest(unittest.TestCase):
    def test_there_are_pages_to_check(self):
        self.assertGreater(len(pages()), 30)

    def test_every_page_has_a_viewport_meta(self):
        missing = [p for p in pages() if not re.search(r'<meta[^>]+name="viewport"', read(p))]
        self.assertEqual(missing, [], "pages render zoomed-out on phones without it")

    def test_every_page_has_a_title_and_canonical(self):
        bad = []
        for p in pages():
            if p == "setup.html":  # owner-only setup link, never indexed
                continue
            s = read(p)
            if not re.search(r"<title>[^<]{5,}</title>", s) or 'rel="canonical"' not in s:
                bad.append(p)
        self.assertEqual(bad, [])

    def test_every_json_ld_block_is_valid_json(self):
        """A JSON-LD block with a syntax error is silently ignored by Google.

        It is also the exact damage a hand-edit to these pages does, and no
        other check here would notice: the page renders, the links resolve and
        the structured data is simply gone.
        """
        bad = []
        for p in pages():
            for block in LD_JSON.findall(read(p)):
                try:
                    json.loads(block)
                except ValueError as e:
                    bad.append(f"{p}: {e}")
        self.assertEqual(bad, [])

    def test_every_content_page_names_the_business_in_structured_data(self):
        """Every page a searcher can land on carries the NAP node in JSON-LD.

        growth/techniques.py::_provider_ld emits this on every page the engine
        generates, so the 40 generated pages have always had it. The four
        hand-built guides predate that function and were never backfilled —
        found 2026-11-05, four of forty-four content pages carrying the phone
        in visible HTML and tel: links but not in structured data. This is the
        invariant rather than a one-time fix, because the gap arose from pages
        being written outside the generator and will arise again the same way.

        privacy.html and setup.html are exempt: neither is a landing page, and
        setup.html is owner-only and never indexed.
        """
        exempt = {"privacy.html", "setup.html"}
        missing = []
        for p in pages():
            if p in exempt:
                continue
            s = read(p)
            nodes = [n for block in LD_JSON.findall(s) for n in _ld_nodes(block)]
            if not any(n.get("@type") in BUSINESS_TYPES
                       and PHONE_E164 in json.dumps(n) for n in nodes):
                missing.append(p)
        self.assertEqual(missing, [], "no business NAP node in this page's JSON-LD")

    def test_local_links_and_assets_exist(self):
        broken = []
        for p in pages():
            for ref in re.findall(r'(?:href|src)="([^"]+)"', read(p)):
                rel = resolve(p, ref)
                if rel and not os.path.exists(os.path.join(ROOT, rel)):
                    broken.append(f"{p} -> {ref}")
        self.assertEqual(broken, [])

    def test_sitemap_urls_are_real_files(self):
        locs = re.findall(r"<loc>https://nemoseamlessgutter\.com(/[^<]*)</loc>", read("sitemap.xml"))
        self.assertGreater(len(locs), 10)
        missing = [l for l in locs if not os.path.exists(os.path.join(ROOT, resolve("index.html", l) or "x"))]
        self.assertEqual(missing, [])


class BookingWidgetTest(unittest.TestCase):
    """The homepage booking widget is a mount point + a script that fills it."""

    def test_homepage_mounts_the_booking_widget(self):
        s = read("index.html")
        self.assertIn('<div id="booking"', s)
        self.assertRegex(s, r'<script src="booking\.js(\?v=\d+)?"')
        self.assertRegex(s, r'href="booking\.css(\?v=\d+)?"')

    def test_widget_talks_to_the_same_origin_api(self):
        js = read("booking.js")
        self.assertIn("var API = ''", js, "cross-origin API would break under the CSP")
        for route in ("/api/services", "/api/availability", "/api/book"):
            self.assertIn(route, js)

    def test_widget_validates_before_posting(self):
        js = read("booking.js")
        submit = js[js.index("function submit()"):js.index("fetch(API + '/api/book'")]
        for msg in ("Please enter your name.", "Please enter a valid phone number.",
                    "Please enter the job address for your visit."):
            self.assertIn(msg, submit)


class RobotsTest(unittest.TestCase):
    PRIVATE = ("/booking/", "/owner/", "/api/", "/seo/", "/growth/", "/setup.html")

    def groups(self):
        """robots.txt groups: consecutive User-agent lines share the rules after them."""
        out, agents, rules, last = [], [], [], None
        for raw in read("robots.txt").splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line or ":" not in line:
                continue
            key, val = (x.strip() for x in line.split(":", 1))
            if key.lower() == "user-agent":
                if last == "rule":
                    out.append((agents, rules))
                    agents, rules = [], []
                agents.append(val)
                last = "agent"
            elif key.lower() in ("allow", "disallow"):
                rules.append(f"{key.title()}: {val}")
                last = "rule"
        if agents:
            out.append((agents, rules))
        return out

    def test_every_crawler_is_kept_out_of_private_paths(self):
        # A crawler obeys only the most specific group naming it, so a
        # Disallow written under the last group (as it once was) binds that
        # one bot and leaves Googlebot free to crawl /api/ and /setup.html.
        groups = self.groups()
        self.assertTrue(groups)
        for agents, rules in groups:
            for d in self.PRIVATE:
                self.assertIn(f"Disallow: {d}", rules, f"{agents} may crawl {d}")

    def test_sitemap_is_advertised(self):
        self.assertIn("Sitemap: https://nemoseamlessgutter.com/sitemap.xml", read("robots.txt"))


if __name__ == "__main__":
    unittest.main()

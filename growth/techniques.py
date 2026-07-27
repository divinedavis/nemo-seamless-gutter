#!/usr/bin/env python3
"""The techniques themselves — the things that actually run each morning.

Each function takes a Context and returns {"ok": bool, "detail": str}. The
ledger decides which ones run; this module only says how. A technique that is
`candidate` or `retired` in techniques.json is never called, which is what lets
the review loop switch something off without a deploy.

Rules every technique here obeys:

  * Never delete. Pages are written and updated, never removed — the monthly
    auto-published guides live only on the server (see seo/README.md), and a
    technique that deleted files would eventually eat one.
  * Write atomically, and back up any hand-built page before editing it. A
    half-written page served to Googlebot at 6am is worse than no page.
  * One new page per run. A hundred thin town pages appearing overnight is the
    exact pattern Google's scaled-content policy targets; one genuinely useful
    page a day is both safer and better.
  * Ask the model for facts about the place, not adjectives about the company.
    The content has to be worth reading or it will not hold a ranking.
"""
import html
import json
import os
import re
import shutil
import subprocess
import urllib.request

from . import ledger, llm, templates

SITE = "https://nemoseamlessgutter.com"
PHONE = "(717) 578-0073"
PHONE_E164 = "+1-717-578-0073"
BRAND = "NEMO Seamless Gutter"
GA_ID = "G-JWSK5E1ZRZ"

# York County municipalities not yet covered by an area page, with the
# coordinates used for the geo meta tags. Ordered roughly by size, since a
# bigger town is a bigger query. `angle` is the honest local hook the page gets
# built around — it is what stops ten town pages being one page with the name
# swapped, which is what gets a site filtered.
TOWN_QUEUE = [
    ("dillsburg", "Dillsburg", 40.1112, -77.0364,
     "northern York County, older borough housing plus newer developments toward Carroll Township"),
    ("shrewsbury", "Shrewsbury", 39.7679, -76.6797,
     "southern York County commuter belt, heavily wooded lots along I-83"),
    ("stewartstown", "Stewartstown", 39.7534, -76.5941,
     "rural southeastern county, long farmhouse rooflines and detached outbuildings"),
    ("new-freedom", "New Freedom", 39.7376, -76.6994,
     "Maryland-line borough, steep older roofs and mature tree cover"),
    ("glen-rock", "Glen Rock", 39.7929, -76.7311,
     "narrow valley borough, Victorian housing stock with complex roof geometry"),
    ("manchester", "Manchester", 40.0623, -76.7205,
     "northern county near the Susquehanna, mix of borough rowhomes and township ranchers"),
    ("mount-wolf", "Mount Wolf", 40.0631, -76.7047,
     "small northern borough, compact lots and older half-round gutter installs"),
    ("wrightsville", "Wrightsville", 40.0273, -76.5308,
     "river town on the Susquehanna, wind exposure off the water"),
    ("hallam", "Hallam", 40.0026, -76.6008,
     "eastern county borough along Route 462, post-war housing stock"),
    ("jacobus", "Jacobus", 39.8626, -76.7108,
     "small southern borough on the Route 214 ridge, compact lots and steep gables"),
]


class Context:
    def __init__(self, docroot, dry_run=False, log=print):
        self.docroot = docroot
        self.dry_run = dry_run
        self.log = log
        self.new_urls = []
        self.changed_urls = []

    def path(self, relpath):
        return os.path.join(self.docroot, relpath.lstrip("/"))

    def read(self, relpath):
        p = self.path(relpath)
        if not os.path.exists(p):
            return None
        with open(p, errors="replace") as f:
            return f.read()

    def backup(self, relpath):
        """Keep one copy before the first edit to a hand-built page, so a bad
        edit at 6am is a one-line restore rather than an archaeology project."""
        p = self.path(relpath)
        if os.path.exists(p) and not self.dry_run:
            bak = p + ".growth-bak"
            if not os.path.exists(bak):
                shutil.copy2(p, bak)

    def write(self, relpath, content):
        """Atomic write into the docroot. Records the URL for IndexNow."""
        p = self.path(relpath)
        existed = os.path.exists(p)
        if self.dry_run:
            self.log(f"      [dry-run] would write {relpath} ({len(content)} bytes)")
        else:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            tmp = p + ".tmp"
            with open(tmp, "w") as f:
                f.write(content)
            os.replace(tmp, p)
        url = f"{SITE}/{relpath.lstrip('/')}"
        (self.changed_urls if existed else self.new_urls).append(url)
        return p


# ---------------------------------------------------------------- rendering

def _esc(s):
    """Escape for a text node. quote=False on purpose: these strings land
    between tags, not inside attributes, and escaping apostrophes there turns
    every "Dillsburg's" in the copy into "Dillsburg&#x27;s" in the source."""
    return html.escape(str(s or ""), quote=False)


def _attr(s):
    """Escape for an attribute value — meta descriptions, titles, alt text."""
    return html.escape(str(s or ""), quote=True)


def _render_sections(sections):
    """Body copy as it appears inside div.container.prose on the real pages:
    headings and paragraphs directly, no extra wrapper divs."""
    out = []
    for s in sections or []:
        if s.get("h2"):
            out.append(f'      <h2>{_esc(s["h2"])}</h2>')
        for p in s.get("paragraphs") or []:
            out.append(f"      <p>{_esc(p)}</p>")
        if s.get("bullets"):
            out.append("      <ul>")
            for b in s["bullets"]:
                out.append(f"        <li>{_esc(b)}</li>")
            out.append("      </ul>")
    return "\n".join(out)


def _render_faqs(faqs):
    if not faqs:
        return ""
    out = ["      <h2>Common questions</h2>"]
    for f in faqs:
        out.append(f'      <h3>{_esc(f.get("q", ""))}</h3>')
        out.append(f'      <p>{_esc(f.get("a", ""))}</p>')
    return "\n".join(out)


def _faq_ld(faqs):
    return json.dumps({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": f.get("q", ""),
                        "acceptedAnswer": {"@type": "Answer", "text": f.get("a", "")}}
                       for f in (faqs or [])]}, indent=2)


def _provider_ld():
    return {
        "@type": "RoofingContractor", "name": BRAND, "telephone": PHONE_E164,
        "url": f"{SITE}/",
        "areaServed": {"@type": "AdministrativeArea",
                       "name": "York County, Pennsylvania"},
        "address": {"@type": "PostalAddress", "streetAddress": "808 W Mason Ave",
                    "addressLocality": "York", "addressRegion": "PA",
                    "postalCode": "17401", "addressCountry": "US"},
    }


def _area_slugs(ctx):
    d = os.path.join(ctx.docroot, "areas")
    if not os.path.isdir(d):
        return set()
    return {f for f in os.listdir(d) if f.endswith(".html")}


def _all_area_pages(ctx):
    """(town label, href) for every area page on the site, for the link mesh."""
    out = []
    for f in sorted(_area_slugs(ctx)):
        m = re.match(r"seamless-gutters-(.+)-pa\.html$", f)
        if not m:
            continue
        out.append((m.group(1).replace("-", " ").title(), f"/areas/{f}"))
    return out


def _nearby_block(pages, exclude_href):
    near = [(l, h) for (l, h) in pages if h != exclude_href][:6]
    if not near:
        return ""
    links = "\n".join(
        f'          <a href="{h}">Seamless Gutters in {_esc(l)}, PA →</a>'
        for l, h in near)
    return templates.NEARBY_BLOCK.format(links=links)


# ------------------------------------------------------------------ area pages

AREA_SYSTEM = """You write local service-area pages for a real seamless gutter \
contractor in York County, Pennsylvania. The owner is Eric; the business is NEMO \
Seamless Gutter.

These pages have to be worth reading. A page that just repeats "we serve <town>, call us \
today" three times will not rank and will make the site look like every other contractor's \
doorway page. Write about the actual place: its housing stock, roof shapes, tree cover, \
weather exposure, and what those specifically mean for gutters — sizing, hanger spacing, \
downspout placement, guard choice, cleaning frequency.

Constraints:
- Never invent a review, testimonial, customer name, job count, year founded, award, or \
certification. You do not know them.
- Never invent a price. You may describe what drives cost (linear footage, stories, roof \
pitch, guard type) but never quote a number.
- No exclamation marks. Plain, competent tradesman's voice — the owner's, not a marketer's.
- Facts about the town must be things you are confident are true. If unsure, write about \
housing and roof characteristics generally rather than naming a landmark you are guessing at.
- Link naturally to /services/seamless-gutter-installation.html, /services/gutter-guards.html, \
/services/gutter-cleaning-repair.html and /services/half-round-gutters.html where relevant, \
by mentioning the service — do not write raw HTML.

Return ONLY valid JSON:
{
  "lede": "one sentence under 220 chars for the hero",
  "meta_desc": "under 155 chars, ends with a call to action including (717) 578-0073",
  "sections": [
    {"h2": "section heading", "paragraphs": ["...", "..."], "bullets": ["optional"]}
  ],
  "faqs": [{"q": "question a homeowner in this town would actually ask", "a": "2-4 sentences"}]
}
Write 3-4 sections and 3-4 FAQs."""


def area_pages(ctx):
    """One new York County town page per run, until the queue is exhausted.

    Local service-area pages are the highest-leverage thing a contractor site
    can own: "gutter installation <town> pa" has unambiguous buying intent, low
    competition, and a searcher one tap from the phone number.
    """
    done = _area_slugs(ctx)
    todo = [t for t in TOWN_QUEUE if f"seamless-gutters-{t[0]}-pa.html" not in done]
    if not todo:
        return {"ok": True, "detail": "every queued town already has a page"}

    slug, town, lat, lon, angle = todo[0]
    filename = f"seamless-gutters-{slug}-pa.html"
    canonical = f"{SITE}/areas/{filename}"

    try:
        data = llm.call_json(AREA_SYSTEM, (
            f"Write the service-area page for {town}, Pennsylvania (York County).\n\n"
            f"What makes this town's gutter work distinctive: {angle}.\n\n"
            f"The company installs seamless aluminum gutter formed on site, plus "
            f"half-round aluminum and copper for historic homes, gutter guards, and "
            f"cleaning and repair. Free on-site estimates. Phone {PHONE}."),
            max_tokens=3000)
    except Exception as e:
        return {"ok": False, "detail": f"content generation failed for {town}: {e}"}
    if not data.get("sections"):
        return {"ok": False, "detail": f"model returned no sections for {town}"}

    service_ld = json.dumps({
        "@context": "https://schema.org", "@type": "Service",
        "serviceType": "Seamless Gutter Installation",
        "name": f"Seamless Gutters in {town}, PA",
        "description": (data.get("lede") or "")[:300],
        "provider": _provider_ld(),
        "areaServed": {"@type": "City", "name": f"{town}, PA"},
        "url": canonical,
        "offers": {"@type": "Offer", "priceCurrency": "USD",
                   "description": f"Free seamless gutter estimate in {town}, PA"},
    }, indent=2)

    body = _render_sections(data["sections"])
    faqs = _render_faqs(data.get("faqs"))
    if faqs:
        body += "\n" + faqs

    pages = _all_area_pages(ctx) + [(town, f"/areas/{filename}")]
    page = templates.HEAD.format(
        ga=GA_ID,
        title=f"Seamless Gutters in {town}, PA | {BRAND}",
        meta_desc=_attr((data.get("meta_desc") or "")[:158]),
        canonical=canonical,
        geo=templates.GEO_META.format(town=_esc(town), lat=lat, lon=lon),
        og_title=f"Seamless Gutters in {town}, PA — {BRAND}",
        og_type="website",
        primary_ld=service_ld, faq_ld=_faq_ld(data.get("faqs")),
        crumb_href="/#areas", crumb_label="Service Areas",
        crumb_here=f"{_esc(town)}, PA",
        eyebrow=f"Seamless Gutters · {_esc(town)}, PA",
        h1=f"Seamless Gutters in {_esc(town)}, PA",
        lede=_esc(data.get("lede", "")),
        body=body,
        cta_heading=f"Serving {_esc(town)}, PA",
        nearby=_nearby_block(pages, f"/areas/{filename}"))

    ctx.write(f"areas/{filename}", page)
    return {"ok": True,
            "detail": f"published {town} ({len(page):,} bytes; "
                      f"{len(todo) - 1} town(s) left in the queue)"}


# ------------------------------------------------------------------ money pages

MONEY_SYSTEM = """You write cost and buying-guide pages for a real seamless gutter \
contractor in York County, Pennsylvania (NEMO Seamless Gutter, owner Eric).

Cost queries are the most valuable traffic a contractor can get: the searcher has decided \
to spend money and is working out how much. Most contractors refuse to discuss price, which \
is why national lead-gen sites outrank them and then sell the lead back. Beat them by being \
genuinely useful about what drives the number, using honest ranges for south-central \
Pennsylvania, and being clear that the only real answer is a measured estimate.

Constraints:
- Ranges must be plausible for York County PA in 2026, always presented as ranges with the \
factors that move them. Never state a single price as if it were this company's quote.
- Never invent a review, testimonial, customer, job count, award, or certification.
- No exclamation marks. Plain, competent voice.
- Be explicit that the free on-site estimate is how you get a real number.

Return ONLY valid JSON:
{
  "title": "page title under 60 chars",
  "meta_desc": "under 155 chars",
  "h1": "the on-page headline",
  "lede": "one sentence under 220 chars",
  "sections": [{"h2": "...", "paragraphs": ["..."], "bullets": ["..."]}],
  "faqs": [{"q": "...", "a": "..."}]
}
Write 4-5 sections and 4-5 FAQs."""


def money_pages(ctx):
    """One page per run against the highest-intent uncovered query.

    Reads the gap list straight out of the tracked universe, so this technique
    is always working on the query the goal metric says is missing — rather than
    on whatever seemed like a good idea when the code was written.
    """
    from . import keywords
    # Score coverage against what is on disk right now, including anything an
    # earlier technique wrote this morning. Without this the gap list is
    # yesterday's, or on a fresh install is every query at once.
    keywords.check_coverage(ctx.docroot)
    kws = keywords.load()

    # Only build where NO page exists for the query. A query whose declared
    # target page exists but ranks weakly needs that page improved, not a second
    # page competing with it — writing /guides/seamless-gutters-york-pa.html
    # when the homepage already targets that query splits the site against
    # itself for its single most valuable search.
    gaps = [k for k in kws
            if not k.get("covered")
            and keywords._page_text(ctx.docroot, k.get("target")) is None]
    if not gaps:
        return {"ok": True,
                "detail": "no uncovered queries without an existing page — "
                          "remaining gaps need their current page improved, not a new one"}

    # hire converts hardest, then price, then the diagnostic and research queries
    # that earn links and AI citations.
    order = {"hire": 0, "price": 1, "check": 2, "diy": 3}
    gaps.sort(key=lambda k: order.get(k.get("intent"), 9))
    target = gaps[0]
    query = target["query"]

    slug = re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-")[:70]
    filename = f"{slug}.html"
    if ctx.read(f"guides/{filename}") is not None:
        return {"ok": True, "detail": f"'{query}' already has a page at /guides/{filename}"}

    canonical = f"{SITE}/guides/{filename}"
    try:
        data = llm.call_json(MONEY_SYSTEM, (
            f'Write the page that should rank for the search query: "{query}".\n\n'
            f"Search intent: {target.get('intent')}. Service area: York County, "
            f"Pennsylvania. Phone {PHONE}."), max_tokens=4000)
    except Exception as e:
        return {"ok": False, "detail": f"content generation failed for '{query}': {e}"}
    if not data.get("sections"):
        return {"ok": False, "detail": f"model returned no sections for '{query}'"}

    h1 = data.get("h1") or query.title()
    article_ld = json.dumps({
        "@context": "https://schema.org", "@type": "Article",
        "headline": h1[:110],
        "description": (data.get("meta_desc") or "")[:300],
        "datePublished": ledger.today(), "dateModified": ledger.today(),
        "author": {"@type": "Organization", "name": BRAND, "url": f"{SITE}/"},
        "publisher": {"@type": "Organization", "name": BRAND,
                      "logo": {"@type": "ImageObject",
                               "url": f"{SITE}/assets/logo-4k.png"}},
        "about": _provider_ld(),
        "mainEntityOfPage": canonical}, indent=2)

    body = _render_sections(data["sections"])
    faqs = _render_faqs(data.get("faqs"))
    if faqs:
        body += "\n" + faqs

    page = templates.HEAD.format(
        ga=GA_ID,
        title=f"{data.get('title') or h1} | {BRAND}",
        meta_desc=_attr((data.get("meta_desc") or "")[:158]),
        canonical=canonical, geo="",
        og_title=f"{h1} — {BRAND}", og_type="article",
        primary_ld=article_ld, faq_ld=_faq_ld(data.get("faqs")),
        crumb_href="/#guides", crumb_label="Guides", crumb_here=_esc(h1[:48]),
        eyebrow="Gutter Guide · York County, PA",
        h1=_esc(h1), lede=_esc(data.get("lede", "")),
        body=body,
        cta_heading="Get a real number for your house",
        nearby=_nearby_block(_all_area_pages(ctx), ""))

    ctx.write(f"guides/{filename}", page)
    if not ctx.dry_run:
        target["target"] = f"/guides/{filename}"
        keywords.save(kws)
    return {"ok": True, "detail": f"published '{query}' → /guides/{filename}"}


# ------------------------------------------------------------- the link mesh

def internal_links(ctx):
    """Keep a nearby-areas block current on every area page.

    New town pages are orphans until something links to them, and Google finds
    orphaned pages slowly and ranks them badly. The block is anchored by
    data-growth="nearby" so refreshing it replaces rather than accumulates.
    """
    pages = _all_area_pages(ctx)
    if len(pages) < 2:
        return {"ok": True, "detail": "not enough area pages to interlink yet"}

    updated = 0
    for label, href in pages:
        rel = href.lstrip("/")
        src = ctx.read(rel)
        if src is None:
            continue
        block = _nearby_block(pages, href)
        if not block:
            continue
        existing = re.search(
            r'\n?\s*<div class="related" data-growth="nearby">.*?</div>\s*</div>',
            src, re.S)
        if existing:
            if existing.group(0).strip() == block.strip():
                continue
            out = src[:existing.start()] + block + src[existing.end():]
        else:
            # Insert after the hand-built "Related" services block, which every
            # area page has, keeping the services links first.
            m = re.search(r'<div class="related">.*?</div>\s*</div>', src, re.S)
            if not m:
                continue
            out = src[:m.end()] + block + src[m.end():]
        ctx.backup(rel)
        ctx.write(rel, out)
        updated += 1
    return {"ok": True, "detail": f"refreshed nearby-links on {updated} page(s)"}


# ----------------------------------------------------------------- local schema

def local_schema(ctx):
    """Put LocalBusiness schema with the real NAP on the homepage.

    The map pack is where "gutter installation york pa" is actually won, and
    consistent name/address/phone in structured data is the part of that Eric
    controls from his own site.
    """
    src = ctx.read("index.html")
    if src is None:
        return {"ok": False, "detail": "no index.html in the docroot"}

    blob = json.dumps({
        "@context": "https://schema.org", "@type": "RoofingContractor",
        "@id": f"{SITE}/#business", "name": BRAND, "url": f"{SITE}/",
        "telephone": PHONE_E164, "email": "enemo@nemoseamlessgutter.com",
        "image": f"{SITE}/assets/logo-4k.png", "logo": f"{SITE}/assets/logo-4k.png",
        "priceRange": "$$",
        "address": {"@type": "PostalAddress", "streetAddress": "808 W Mason Ave",
                    "addressLocality": "York", "addressRegion": "PA",
                    "postalCode": "17401", "addressCountry": "US"},
        "areaServed": [{"@type": "AdministrativeArea",
                        "name": "York County, Pennsylvania"}],
        "openingHoursSpecification": [{
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "opens": "07:00", "closes": "18:00"}],
        "hasOfferCatalog": {
            "@type": "OfferCatalog", "name": "Gutter services",
            "itemListElement": [
                {"@type": "Offer",
                 "itemOffered": {"@type": "Service", "name": n, "url": f"{SITE}{u}"}}
                for n, u in (
                    ("Seamless gutter installation",
                     "/services/seamless-gutter-installation.html"),
                    ("Gutter guards", "/services/gutter-guards.html"),
                    ("Gutter cleaning and repair",
                     "/services/gutter-cleaning-repair.html"),
                    ("Half-round gutters", "/services/half-round-gutters.html"))]},
    }, indent=2)

    marker = '<script type="application/ld+json" data-growth="localbusiness">'
    block = f"  {marker}\n{blob}\n  </script>\n"

    if marker in src:
        out = re.sub(re.escape(marker) + r".*?</script>\n?", block.strip() + "\n",
                     src, count=1, flags=re.S)
        verb = "refreshed"
    else:
        if "</head>" not in src:
            return {"ok": False, "detail": "index.html has no </head>"}
        out = src.replace("</head>", block + "</head>", 1)
        verb = "added"
    if out == src:
        return {"ok": True, "detail": "LocalBusiness schema already current"}
    ctx.backup("index.html")
    ctx.write("index.html", out)
    return {"ok": True, "detail": f"{verb} LocalBusiness schema on the homepage"}


# -------------------------------------------------------------------- indexing

def rebuild_sitemap(ctx):
    """Re-run the existing sitemap generator so new pages are discoverable."""
    if ctx.dry_run:
        return {"ok": True, "detail": "[dry-run] would rebuild sitemap.xml"}
    script = os.path.join(ctx.docroot, "seo", "gen_sitemap.py")
    if not os.path.exists(script):
        return {"ok": False, "detail": "seo/gen_sitemap.py not found"}
    try:
        p = subprocess.run(["python3", script],
                           env=dict(os.environ, WEB_ROOT=ctx.docroot),
                           cwd=ctx.docroot, capture_output=True, text=True, timeout=120)
    except Exception as e:
        return {"ok": False, "detail": f"sitemap rebuild failed: {e}"}
    tail = (p.stdout or p.stderr or "").strip().splitlines()
    return {"ok": p.returncode == 0, "detail": tail[-1] if tail else "rebuilt"}


def ping_indexnow(ctx):
    """Push the URLs this run touched to IndexNow.

    seo/indexnow_submit.py already submits the whole sitemap daily at 03:05;
    this submits just this morning's pages, so something written at 6am is
    queued for Bing within minutes instead of the next day.
    """
    urls = list(dict.fromkeys(ctx.new_urls + ctx.changed_urls))
    if not urls:
        return {"ok": True, "detail": "nothing new to submit"}
    if ctx.dry_run:
        return {"ok": True, "detail": f"[dry-run] would submit {len(urls)} URL(s)"}

    try:
        key = open(os.path.join(ctx.docroot, "seo", "indexnow_key.txt")).read().strip()
    except Exception:
        return {"ok": False, "detail": "no seo/indexnow_key.txt"}

    body = json.dumps({"host": "nemoseamlessgutter.com", "key": key,
                       "keyLocation": f"{SITE}/{key}.txt",
                       "urlList": urls[:10000]}).encode()
    req = urllib.request.Request(
        "https://api.indexnow.org/indexnow", data=body,
        headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            code = r.status
    except Exception as e:
        return {"ok": False, "detail": f"IndexNow submit failed: {e}"}
    return {"ok": code in (200, 202), "detail": f"submitted {len(urls)} URL(s), HTTP {code}"}


REGISTRY = {
    "area_pages": area_pages,
    "money_pages": money_pages,
    "internal_links": internal_links,
    "local_schema": local_schema,
    "rebuild_sitemap": rebuild_sitemap,
    "ping_indexnow": ping_indexnow,
}

# Order matters: write pages, wire them together, then tell search engines.
ORDER = ["area_pages", "money_pages", "internal_links", "local_schema",
         "rebuild_sitemap", "ping_indexnow"]

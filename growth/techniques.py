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

# A step that generates per item moves to the next candidate when one fails,
# instead of losing the morning to a single bad reply. Bounded so a broken key
# or an exhausted balance cannot turn one step into a whole queue of paid
# retries — after this many failures the step gives up and reports.
MAX_ITEM_FAILURES = 3

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
        # A keyword target of "/" resolves to the docroot itself. Read the
        # index there rather than blowing up on a directory.
        if os.path.isdir(p):
            p = os.path.join(p, "index.html")
        if not os.path.isfile(p):
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
        return {"ok": True, "noop": True,
                "detail": "every queued town already has a page"}

    # A town that fails to generate should cost that town, not the day — the
    # next one in the queue is just as worth publishing, and the one skipped
    # stays queued for tomorrow.
    data = slug = town = lat = lon = None
    errors = []
    for cand in todo[:MAX_ITEM_FAILURES]:
        c_slug, c_town, c_lat, c_lon, angle = cand
        try:
            data = llm.call_json(AREA_SYSTEM, (
                f"Write the service-area page for {c_town}, Pennsylvania (York County).\n\n"
                f"What makes this town's gutter work distinctive: {angle}.\n\n"
                f"The company installs seamless aluminum gutter formed on site, plus "
                f"half-round aluminum and copper for historic homes, gutter guards, and "
                f"cleaning and repair. Free on-site estimates. Phone {PHONE}."),
                max_tokens=3000)
        except Exception as e:
            errors.append(f"content generation failed for {c_town}: {e}")
            data = None
            continue
        if not data.get("sections"):
            errors.append(f"model returned no sections for {c_town}")
            data = None
            continue
        slug, town, lat, lon = c_slug, c_town, c_lat, c_lon
        break

    if data is None:
        return {"ok": False,
                "detail": f"{len(errors)} town(s) failed, last: {errors[-1]}"}

    filename = f"seamless-gutters-{slug}-pa.html"
    canonical = f"{SITE}/areas/{filename}"

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
    def _needs_its_own_page(k):
        if k.get("covered"):
            return False
        if keywords._page_text(ctx.docroot, k.get("target")) is not None:
            return False
        # If a specific page already exists that this query belongs on — the
        # town's area page, the matching service page — then strengthen_pages
        # will add a section there. Writing a separate guide as well puts two
        # of our own pages in front of the same searcher and splits the
        # authority between them. Only build where the homepage is the sole
        # fallback, which means the query genuinely has nowhere to live.
        host = _host_page(ctx, k)
        return host in (None, "/index.html")

    gaps = [k for k in kws if _needs_its_own_page(k)]
    if not gaps:
        return {"ok": True, "noop": True,
                "detail": "no query needs its own page — the remaining gaps all "
                          "belong on pages that exist, which strengthen_pages handles"}

    # hire converts hardest, then price, then the diagnostic and research queries
    # that earn links and AI citations.
    order = {"hire": 0, "price": 1, "check": 2, "diy": 3}
    gaps.sort(key=lambda k: order.get(k.get("intent"), 9))
    target = gaps[0]
    query = target["query"]

    slug = re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-")[:70]
    filename = f"{slug}.html"
    if ctx.read(f"guides/{filename}") is not None:
        return {"ok": True, "noop": True,
                "detail": f"'{query}' already has a page at /guides/{filename}"}

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
        return {"ok": True, "noop": True,
                "detail": "not enough area pages to interlink yet"}

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
    return {"ok": True, "noop": not updated,
            "detail": f"refreshed nearby-links on {updated} page(s)"}


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
        return {"ok": True, "noop": True,
                "detail": "LocalBusiness schema already current"}
    ctx.backup("index.html")
    ctx.write("index.html", out)
    return {"ok": True, "detail": f"{verb} LocalBusiness schema on the homepage"}


# -------------------------------------------------------------------- indexing

def rebuild_sitemap(ctx):
    """Re-run the existing sitemap generator so new pages are discoverable."""
    if ctx.dry_run:
        return {"ok": True, "noop": True, "detail": "[dry-run] would rebuild sitemap.xml"}
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
        return {"ok": True, "noop": True, "detail": "nothing new to submit"}
    if ctx.dry_run:
        return {"ok": True, "noop": True,
                "detail": f"[dry-run] would submit {len(urls)} URL(s)"}

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





# ------------------------------------------------------- strengthen existing

# Where a query belongs when no target is declared. Order matters: the most
# specific service wins, and the town only decides between area pages.
SERVICE_HINTS = [
    (("half round", "half-round", "copper"), "/services/half-round-gutters.html"),
    (("guard", "leaf protection", "leafguard", "leaf guard"),
     "/services/gutter-guards.html"),
    # Ahead of the repair/replace lines below, which would otherwise swallow
    # "soffit and fascia repair york pa" onto the cleaning page and
    # "gutter soffit and fascia replacement" onto the installation page —
    # away from the dedicated page the site already ranks 1.8 for.
    (("soffit", "fascia"), "/services/gutter-soffit-fascia-replacement.html"),
    (("clean", "repair", "downspout", "overflow", "clog", "sagging"),
     "/services/gutter-cleaning-repair.html"),
    (("install", "replace", "new gutters", "seamless"),
     "/services/seamless-gutter-installation.html"),
]

STRENGTHEN_SYSTEM = """You write one focused section to add to an existing page on a real \
seamless gutter contractor's website (NEMO Seamless Gutter, York County, Pennsylvania, \
owner Eric).

The page already exists and already ranks for related searches. Your section has to earn \
the specific search below without repeating what the page already says. Write the section \
a homeowner searching that exact phrase would want to find.

Constraints:
- The h2 must read naturally to a human AND contain the distinguishing words of the search. \
Do not keyword-stuff; "Gutter Replacement in York, PA" is right, "Gutter Replacement York PA \
Gutter Replacement" is not.
- Never invent a review, testimonial, customer, job count, year founded, award, certification, \
or a specific price. You may describe what drives cost.
- No exclamation marks. Plain, competent tradesman's voice.
- 2-3 paragraphs. Add bullets only if they genuinely help.
- Do not repeat the page's existing headings, which are listed below.

Return ONLY valid JSON:
{"h2": "the section heading",
 "paragraphs": ["...", "..."],
 "bullets": ["optional"],
 "faq": {"q": "a question this searcher would ask", "a": "2-4 sentences"}}"""


def _host_page(ctx, kw):
    """The page a query should live on, if one already exists."""
    target = kw.get("target")
    if target in ("/", ""):
        target = "/index.html" if target == "/" else target
    if target and ctx.read(target.lstrip("/")) is not None:
        return target
    q = kw["query"].lower()
    # a town in the query points at that town's area page
    for slug in sorted({t[0] for t in TOWN_QUEUE} |
                       {re.sub(r"[^a-z]+", "-", t.strip()) for t in
                        ("hanover", "dover", "red lion", "dallastown", "spring grove")}):
        label = slug.replace("-", " ")
        if label and label in q:
            cand = f"/areas/seamless-gutters-{slug}-pa.html"
            if ctx.read(cand.lstrip("/")) is not None:
                return cand
    for words, page in SERVICE_HINTS:
        if any(w in q for w in words) and ctx.read(page.lstrip("/")) is not None:
            return page
    guide = _provider_guide(ctx, q) or _topic_guide(ctx, q)
    if guide:
        return guide
    return "/index.html" if ctx.read("index.html") is not None else None


# Words that name a *firm* rather than a *job*. A query built out of these and
# nothing else — "gutter company york pa", "gutter contractors york pa" — has no
# town and no service to route on, so it used to fall through to /index.html,
# which money_pages reads as "nowhere to live, write it a guide". Five guides
# went up in five days that way: gutter-guys-near-me, gutter-installer-near-me,
# gutter-services-near-me, gutters-york-pa and best-gutter-company-york-county-pa,
# each 1,100-1,600 words answering the same question, and three more of the same
# shape are queued behind them. Routing them at the guide that already exists is
# what strengthen_pages' own docstring says the engine is supposed to do:
# concentrate authority instead of splitting it across near-duplicates.
PROVIDER_WORDS = ("company", "companies", "contractor", "contractors",
                  "gutter guys", "crew")

# Most general first — whichever of these exists is the one such a query joins.
PROVIDER_GUIDES = ("/guides/best-gutter-company-york-county-pa.html",
                   "/guides/gutters-york-pa.html",
                   "/guides/gutter-installer-near-me.html")


def _provider_guide(ctx, q):
    """The existing 'who should I hire' guide, for queries that only ask that."""
    if not any(w in q for w in PROVIDER_WORDS):
        return None
    for page in PROVIDER_GUIDES:
        if ctx.read(page.lstrip("/")) is not None:
            return page
    return None


# Words that carry no topic. Stripped from both sides before comparing a query
# against a guide, so "what size gutters do i need" and "5 inch vs 6 inch
# gutters" reduce to the same handful of words the existing size guide is about.
TOPIC_STOP = frozenset((
    "a", "an", "and", "are", "be", "best", "better", "can", "cost", "costs",
    "do", "does", "for", "from", "get", "good", "how", "i", "in", "is", "it",
    "long", "many",
    "me", "much", "my", "near", "need", "of", "often", "on", "or", "pa",
    "pennsylvania", "per", "price", "prices", "should", "the", "to", "vs",
    "what", "when", "which", "who", "why", "with", "worth", "you", "your"))


def _topic_words(text):
    """Content words of a query or a slug, singularised crudely."""
    out = set()
    for w in re.split(r"[^a-z0-9]+", (text or "").lower()):
        if not w or w in TOPIC_STOP:
            continue
        out.add(w[:-1] if len(w) > 3 and w.endswith("s") else w)
    return out


def _topic_guide(ctx, q):
    """The existing guide that already answers this query, if there is one.

    _provider_guide, added 2026-07-31, caught queries built out of firm words
    ("gutter company york pa"). It did not catch the next morning's duplicate:
    "york gutters" routed nowhere, so money_pages wrote
    /guides/york-gutters.html the day after it wrote /guides/gutters-york-pa.html
    for "gutters york pa" — the same question, the words reversed, six shared
    headings. Three "5 inch vs 6 inch gutters" phrasings plus "what size gutters
    do i need" were queued behind it, against a size guide the site already has.

    A word list cannot keep up with that; the test has to be about topic. A
    query whose content words are all already in a guide's slug belongs on that
    guide, and strengthen_pages will add the section there instead.
    """
    want = _topic_words(q)
    if len(want) < 2:            # too thin to match on without false positives
        return None
    d = os.path.join(ctx.docroot, "guides")
    if not os.path.isdir(d):
        return None
    best = None
    for f in sorted(os.listdir(d)):
        if not f.endswith(".html"):
            continue
        have = _topic_words(f[:-5])
        if want <= have and (best is None or len(have) < best[0]):
            # Prefer the tightest guide: a query about gutter size belongs on
            # the size guide, not on whichever longer page happens to contain
            # those words too.
            best = (len(have), f"/guides/{f}")
    return best[1] if best else None


def _existing_headings(src):
    heads = re.findall(r"<h[123][^>]*>(.*?)</h[123]>", src or "", re.S)
    return [re.sub(r"<[^>]+>", " ", h).strip()[:80] for h in heads]


def strengthen_pages(ctx):
    """Add a targeted section to a page that already exists but does not rank.

    This is the technique that actually moves the goal. Most uncovered queries
    are not missing a page — they are missing a heading. "gutter replacement
    york pa" points at the installation page, which never uses the word
    "replacement"; "gutter repair dover pa" belongs on the Dover area page,
    which only talks about installation.

    Writing a new page for those would split the site against itself, so this
    strengthens the page that should already be winning instead. That also
    concentrates authority rather than diluting it across near-duplicates.
    """
    from . import keywords
    keywords.check_coverage(ctx.docroot)
    kws = keywords.load()

    order = {"hire": 0, "price": 1, "check": 2, "diy": 3}
    todo = sorted((k for k in kws if not k.get("covered")),
                  key=lambda k: order.get(k.get("intent"), 9))

    done = set(ledger.get_state("strengthened", []))
    # One unusable reply used to end the step for the day. The queue is 47
    # queries deep and any of them is worth writing, so a failure moves to the
    # next candidate and only the last one is reported if none succeed.
    errors = []
    for kw in todo:
        if kw["query"] in done:
            continue
        host = _host_page(ctx, kw)
        if not host:
            continue
        src = ctx.read(host.lstrip("/"))
        if src is None or '<div class="cta-band">' not in src:
            continue

        try:
            data = llm.call_json(STRENGTHEN_SYSTEM, (
                f'The search to win: "{kw["query"]}"\n'
                f'Search intent: {kw.get("intent")}\n'
                f'The page: {host}\n'
                f'Headings already on that page: '
                f'{"; ".join(_existing_headings(src)[:12])}\n\n'
                f"Phone {PHONE}. Free on-site estimates across York County."),
                max_tokens=1600)
        except Exception as e:
            errors.append(f"generation failed for '{kw['query']}': {e}")
            if len(errors) >= MAX_ITEM_FAILURES:
                break
            continue
        if not data.get("h2") or not data.get("paragraphs"):
            errors.append(f"model returned nothing usable for '{kw['query']}'")
            if len(errors) >= MAX_ITEM_FAILURES:
                break
            continue

        block = _render_sections([{
            "h2": data["h2"], "paragraphs": data["paragraphs"],
            "bullets": data.get("bullets")}])
        faq = data.get("faq") or {}
        if faq.get("q"):
            block += (f'\n      <h3>{_esc(faq["q"])}</h3>'
                      f'\n      <p>{_esc(faq.get("a", ""))}</p>')

        marker = '      <div class="cta-band">'
        idx = src.find(marker)
        if idx < 0:
            idx = src.find('<div class="cta-band">')
        out = src[:idx] + block + "\n\n" + src[idx:]

        ctx.backup(host.lstrip("/"))
        ctx.write(host.lstrip("/"), out)

        if not ctx.dry_run:
            kw["target"] = host
            keywords.save(kws)
            ledger.set_state("strengthened", sorted(done | {kw["query"]}))
        return {"ok": True,
                "detail": f"added \"{data['h2'][:60]}\" to {host} for '{kw['query']}'"}

    if errors:
        return {"ok": False,
                "detail": f"{len(errors)} candidate(s) failed, last: {errors[-1]}"}
    return {"ok": True, "noop": True,
            "detail": "no uncovered query has an existing page to strengthen"}


# ----------------------------------------------------------- service pages

# Services the site does not have a page for. Ordered by evidence: soffit and
# fascia is first because Search Console already shows the site ranking 1.7 for
# "gutter soffit and fascia replacement" with nothing to send that click to.
SERVICE_QUEUE = [
    ("gutter-soffit-fascia-replacement", "Soffit &amp; Fascia Replacement",
     "gutter soffit and fascia replacement",
     "Rotten fascia board is the most common reason a gutter pulls away from a "
     "house, so this work is usually sold alongside a gutter replacement. Cover "
     "what rotten fascia looks like from the ground, why gutters fail when the "
     "board behind them fails, aluminum wrap versus replacing the board, and "
     "how soffit ventilation matters for the roof."),
    ("emergency-gutter-repair", "Emergency Gutter Repair",
     "emergency gutter repair after storm york pa",
     "Storm damage in York County: gutters torn loose by wind, downspouts "
     "crushed by ice or a limb, water pouring behind the gutter into the "
     "basement. Cover what to do immediately, what can wait, what a temporary "
     "fix looks like, and how insurance claims usually treat gutter damage."),
    ("commercial-gutters", "Commercial Gutters",
     "commercial gutter installation york pa",
     "Commercial and agricultural buildings in York County: box gutters on "
     "warehouses, long runs on barns and pole buildings, heavier gauge and "
     "larger downspouts, and why sizing matters far more on a big roof."),
]


def service_pages(ctx):
    """One new service page per run, for work the site does but cannot be found for."""
    todo = [s for s in SERVICE_QUEUE
            if ctx.read(f"services/{s[0]}.html") is None]
    if not todo:
        return {"ok": True, "noop": True,
                "detail": "every queued service already has a page"}

    slug, title, query, brief = todo[0]
    filename = f"{slug}.html"
    canonical = f"{SITE}/services/{filename}"

    try:
        data = llm.call_json(MONEY_SYSTEM, (
            f'Write the service page that should rank for: "{query}".\n\n'
            f"What this page must cover: {brief}\n\n"
            f"This is a service page for the business, not a general guide — it "
            f"should end with the reader wanting an estimate. Service area: York "
            f"County, Pennsylvania. Phone {PHONE}."), max_tokens=4000)
    except Exception as e:
        return {"ok": False, "detail": f"generation failed for {title}: {e}"}
    if not data.get("sections"):
        return {"ok": False, "detail": f"model returned no sections for {title}"}

    h1 = data.get("h1") or title
    service_ld = json.dumps({
        "@context": "https://schema.org", "@type": "Service",
        "serviceType": title.replace("&amp;", "and"),
        "name": h1, "description": (data.get("lede") or "")[:300],
        "provider": _provider_ld(),
        "areaServed": {"@type": "AdministrativeArea",
                       "name": "York County, Pennsylvania"},
        "url": canonical,
        "offers": {"@type": "Offer", "priceCurrency": "USD",
                   "description": "Free on-site estimate in York County, PA"},
    }, indent=2)

    body = _render_sections(data["sections"])
    faqs = _render_faqs(data.get("faqs"))
    if faqs:
        body += "\n" + faqs

    page = templates.HEAD.format(
        ga=GA_ID, title=f"{data.get('title') or h1} | {BRAND}",
        meta_desc=_attr((data.get("meta_desc") or "")[:158]),
        canonical=canonical, geo="",
        og_title=f"{h1} — {BRAND}", og_type="website",
        primary_ld=service_ld, faq_ld=_faq_ld(data.get("faqs")),
        crumb_href="/#services", crumb_label="Services", crumb_here=_esc(title),
        eyebrow=f"{title} · York County, PA",
        h1=_esc(h1), lede=_esc(data.get("lede", "")),
        body=body, cta_heading="Get a free estimate",
        nearby=_nearby_block(_all_area_pages(ctx), ""))

    ctx.write(f"services/{filename}", page)
    return {"ok": True, "detail": f"published /services/{filename} ({len(page):,} bytes; "
                                  f"{len(todo) - 1} service(s) left in the queue)"}


# ------------------------------------------------------------ click-through

CTR_SYSTEM = """You write the <title> and meta description for one page of a real seamless \
gutter contractor's website (NEMO Seamless Gutter, York County, Pennsylvania).

Google already shows this page to people. They are not clicking it. Your job is the snippet \
that earns the click from the searches listed — not a prettier version of what is there now.

Rules:
- Title: 60 characters maximum, and it must fit the actual searches below. Lead with what \
the searcher typed, then append " | NEMO Seamless Gutter" if it still fits in 60 — dropping \
the business name entirely costs the branded searches, where someone already looking for \
this company needs to recognise it in the results.
- The title or the description must name the place — York, York County, or PA. Many of the \
searches below are national wording ("gutter installer", "gutter contractor") that a \
homeowner two states away types too. A snippet with no place in it gives a York homeowner \
nothing to recognise, and tells Google this page belongs to no particular town.
- Description: 155 characters maximum, active voice, gives a concrete reason to click \
(free on-site estimate, formed on site, same-week scheduling) and ends with the phone number.
- Never invent a review count, star rating, years in business, award, certification, \
guarantee, or price. You do not know them and a false claim in a search snippet is worse \
than a dull one.
- No exclamation marks, no ALL CAPS, no clickbait.
- Plain American English, tradesman's voice.

Return ONLY valid JSON: {"title": "...", "description": "...", "why": "one sentence on what \
you changed and why"}"""

# The words that tell a searcher in Hallam that this contractor can reach their
# house. "pa" is bounded so it does not match inside "page" or "repair".
GEO_ANCHOR = re.compile(r"\byork\b|\bpennsylvania\b|\bpa\b", re.I)

# Long enough to see whether a rewrite moved anything before touching it again.
# Rewriting a title every morning would make the effect unmeasurable and would
# look to Google like a page that cannot decide what it is about.
CTR_COOLDOWN_DAYS = 21


def _url_to_relpath(url):
    """Map a Search Console URL back to a file in the docroot."""
    u = re.sub(r"^https?://", "", url or "").split("#")[0].split("?")[0]
    if "/" not in u:
        return "index.html"
    path = u.split("/", 1)[1]
    if not path or path.endswith("/"):
        return os.path.join(path, "index.html") if path else "index.html"
    return path


def improve_ctr(ctx):
    """Rewrite the title and description of a page Google shows but nobody clicks.

    The cheapest win available: ranking is the hard part and it is already done.
    The homepage sits at position 1 for "gutter contractor" and "gutter guard
    installer" and collects almost no clicks.

    One honest caveat, recorded here so nobody later reads a flat result as a
    failed rewrite: much of that is probably the local pack absorbing the tap.
    On a "near me" search the map listing offers a call button and directions
    right there, and a searcher who calls from it never reaches the website at
    all. A better snippet should still help, but it cannot recover a click that
    was spent inside Google.
    """
    from . import gsc
    if not gsc.available():
        return {"ok": True, "noop": True,
                "detail": "no Search Console key — nothing to optimise against"}

    history = ledger.get_state("ctr_rewrites", {})
    today = ledger.today()

    try:
        candidates = gsc.underperformers()
    except Exception as e:
        return {"ok": False, "detail": f"could not read Search Console: {e}"}

    for page in candidates:
        rel = _url_to_relpath(page["page"])
        src = ctx.read(rel)
        if src is None or "<title>" not in src:
            continue
        last = history.get(rel)
        if last:
            try:
                import datetime as _dt
                age = (_dt.date.fromisoformat(today) - _dt.date.fromisoformat(last)).days
                if age < CTR_COOLDOWN_DAYS:
                    continue
            except Exception:
                pass

        try:
            queries = gsc.queries_for_page(page["page"])
        except Exception:
            queries = []
        if not queries:
            continue
        qlist = "\n".join(f'- "{q["query"]}" — {q["impressions"]} impressions, '
                           f'position {q["position"]:.1f}' for q in queries[:15])
        current_title = re.search(r"<title>(.*?)</title>", src, re.S)
        current_desc = re.search(r'<meta name="description" content="(.*?)"', src, re.S)

        try:
            data = llm.call_json(CTR_SYSTEM, (
                f"Page: {page['page']}\n"
                f"Over the last 28 days: {page['impressions']} impressions, "
                f"{page['clicks']} clicks, average position {page['position']:.1f}.\n\n"
                f"Current title: {current_title.group(1) if current_title else '(none)'}\n"
                f"Current description: "
                f"{current_desc.group(1)[:200] if current_desc else '(none)'}\n\n"
                f"The searches Google shows this page for:\n{qlist}\n\n"
                f"Phone {PHONE}."), max_tokens=900)
        except Exception as e:
            return {"ok": False, "detail": f"generation failed for {rel}: {e}"}

        title = (data.get("title") or "").strip()
        desc = (data.get("description") or "").strip()
        if not title or not desc:
            return {"ok": False, "detail": f"model returned no snippet for {rel}"}
        # Google truncates past these; a title that gets cut mid-word reads as
        # careless in the one place every searcher sees it.
        if len(title) > 65 or len(desc) > 165:
            return {"ok": False,
                    "detail": f"rejected over-long snippet for {rel} "
                              f"(title {len(title)}, desc {len(desc)})"}
        # On 2026-07-27 this technique rewrote the homepage from "Seamless
        # Gutters in York, PA | NEMO Seamless Gutter" to "Gutter Installer &
        # Contractor | NEMO Seamless Gutter" — obeying the rule above to lead
        # with what the searcher typed, on a page whose top queries are the
        # geo-agnostic "gutter installer" and "gutter contractor". It has held
        # position 1 on those ever since, over 258 impressions, for zero
        # clicks. A snippet naming no place is the one thing this technique can
        # do that actively costs the business something, so it is refused here
        # as well as discouraged in the prompt.
        if not (GEO_ANCHOR.search(title) or GEO_ANCHOR.search(desc)):
            return {"ok": False,
                    "detail": f"rejected placeless snippet for {rel} — neither "
                              f"title nor description names York or PA "
                              f"(title: {title!r})"}

        out = src
        if current_title:
            out = out[:current_title.start(1)] + _esc(title) + out[current_title.end(1):]
        if current_desc:
            c = re.search(r'<meta name="description" content="(.*?)"', out, re.S)
            out = out[:c.start(1)] + _attr(desc) + out[c.end(1):]
        if out == src:
            continue

        ctx.backup(rel)
        ctx.write(rel, out)
        if not ctx.dry_run:
            history[rel] = today
            ledger.set_state("ctr_rewrites", history)
        return {"ok": True,
                "detail": f"rewrote title/description on /{rel} "
                          f"({page['impressions']} impressions, {page['clicks']} clicks, "
                          f"pos {page['position']:.1f}) — {data.get('why', '')[:110]}"}

    return {"ok": True, "noop": True, "detail": "no page is due a snippet rewrite"}


# --------------------------------------------------------- tracked universe

# Only adopt a discovered query if it is plausibly this business's work in this
# service area. Without this the denominator fills with "seamless gutters
# perkasie pa" (90 miles away) and the 50% goal quietly becomes unreachable.
SERVICE_AREA_WORDS = ("york", "hanover", "dover", "red lion", "dallastown",
                      "spring grove", "dillsburg", "shrewsbury", "stewartstown",
                      "new freedom", "glen rock", "manchester", "mount wolf",
                      "wrightsville", "hallam", "jacobus", "seven valleys",
                      "emigsville", "windsor", "yoe")
TRADE_WORDS = ("gutter", "downspout", "soffit", "fascia", "leaf guard",
               "leafguard", "eavestrough")
# Places that are emphatically not York County, seen in the real data.
OUT_OF_AREA = ("perkasie", "yorkville", "york sc", "york ne", "york me",
               "new york", "yorktown", "york uk", "york maine",
               "akron", "essington", "crum lynne", "myerstown", "newmanstown")


def _names_other_market(query):
    """True if a search explicitly names somewhere this business does not serve.

    Deliberately weaker than the test `adopt_queries` applies. That one needs a
    positive in-area signal because it decides the goal's denominator; this one
    only needs to reject searches that name somewhere else, so a geo-neutral
    search like "gutter installer" — the site's single largest source of
    impressions — still counts as usable.

    Rather than maintain a list of every Pennsylvania town that is not ours,
    read the shape of the query. One that bothers to name a state or a county
    is location-qualified, so if it names none of ours it names someone else's.
    """
    q = query.lower()
    if any(bad in q for bad in OUT_OF_AREA):
        return True
    ours = any(w in q for w in SERVICE_AREA_WORDS)
    if not ours and re.search(r"\b(pa|penna|pennsylvania)\b", q):
        return True
    # "county" alone used to count as in-area, which let "schuylkill county
    # seamless gutter" into the tracked universe and the goal's denominator.
    if "county" in q and "york county" not in q:
        return True
    return False


def adopt_queries(ctx):
    """Add real searches to the tracked universe, filtered to this business.

    Search Console reports what people actually type, which beats anything
    guessed at a desk. But the goal is a percentage, so its denominator is a
    judgement — adopting everything would stuff it with out-of-area junk and
    make 50% both harder and meaningless. Adopt only trade searches that carry
    service-area intent, and leave the rest visible in the report for a human
    to argue about.
    """
    from . import gsc, keywords
    if not gsc.available():
        return {"ok": True, "noop": True, "detail": "no Search Console key"}
    try:
        found = gsc.discover(min_impressions=2)
    except Exception as e:
        return {"ok": False, "detail": f"could not read Search Console: {e}"}

    added = []
    for d in found:
        q = d["query"].lower()
        if any(bad in q for bad in OUT_OF_AREA):
            continue
        if not any(w in q for w in TRADE_WORDS):
            continue
        # Either it names a place we serve, or it is an unmodified/near-me
        # search which Google localises to the searcher anyway.
        local = any(w in q for w in SERVICE_AREA_WORDS) or "near me" in q
        if not local:
            continue
        town = "county"
        for slug in ("hanover", "dover", "red-lion", "dallastown", "spring-grove"):
            if slug.replace("-", " ") in q:
                town = slug
                break
        intent = "hire"
        if any(w in q for w in ("cost", "price", "how much", "per foot")):
            intent = "price"
        elif any(w in q for w in ("why", "how often", "vs", "worth it", "what size")):
            intent = "diy"
        if ctx.dry_run:
            added.append(q)
        elif keywords.add(q, town, intent, source=f"gsc:{ledger.today()}",
                          note=f"{d['impressions']} impressions, position {d['position']}"):
            added.append(q)

    if not added:
        return {"ok": True, "noop": True,
                "detail": "no new in-area searches worth tracking"}
    return {"ok": True,
            "detail": f"adopted {len(added)} real search(es) into the tracked "
                      f"universe: {', '.join(added[:5])}"
                      + ("…" if len(added) > 5 else "")}


# ------------------------------------------------- answer-first / GEO pass

# An HTML comment, not a new CSS class, is what makes this idempotent. The
# visible markup reuses p.lead, which styles.css already defines (.prose .lead)
# and the area pages already use — inventing an .answer-first class would
# render unstyled, which is the mistake the area templates were built to avoid.
GEO_MARKER = "<!-- geo:answer-first -->"

# Answers shorter than this are not answers; longer than this and the extract
# stops being quotable, which is the entire point of the block.
GEO_MIN_WORDS, GEO_MAX_WORDS = 35, 75

GEO_SYSTEM = """You write the opening answer for one page of a real seamless gutter \
contractor's website: NEMO Seamless Gutter, serving York County, Pennsylvania.

The page already ranks for the search below but opens with a section heading, so a \
reader — or an AI answer engine summarising the page — has to work to find the \
actual answer. Your job is the direct answer that should sit at the very top.

Return ONLY valid JSON with keys:
  answer  — 40-60 words. A complete, self-contained answer to the search, written so
            it still makes sense quoted on its own with no surrounding page. Lead with
            the answer itself, not with a restatement of the question. Plain sentences.
  faqs    — 3 to 5 objects with keys q and a. Each q is a real follow-up question a
            York County homeowner would ask next; each a is 30-60 words.

Hard rules. Do NOT invent prices, dollar figures, ranges, reviews, ratings, star \
counts, years in business, licence numbers, certifications or warranty terms. Cost \
questions are answered by explaining what drives the price and pointing to a free \
written on-site estimate. Do not claim awards or "best in York County" status. No \
marketing superlatives. Write the way an experienced installer explains something \
standing in a driveway. Phone is (717) 578-0073."""


def geo_answer_first_content_pass(ctx):
    """Put a quotable direct answer at the top of pages that already rank.

    This is the one tactic from the AI-search playbook that fits a local
    contractor. It is not a volume play — nothing new is published, and no
    near-duplicate page is created. It rewrites the opening of a page that is
    already earning impressions so the answer is extractable.

    Why the top of the page specifically: the guides currently open straight
    into an <h2>, so the first thing a summariser meets is a section heading
    rather than a claim it can lift. 386 impressions against 3 clicks says most
    of this audience never reaches the page at all, which makes being quoted
    inside the answer worth more than being clicked through to.

    One honest limitation, recorded so a flat result is not misread later:
    Google restricted FAQ rich results to a narrow set of site types, so the
    FAQPage block added here is very unlikely to produce visible rich snippets.
    It is here because it marks question/answer pairs unambiguously for the
    engines that do parse it, not because it will decorate the SERP.
    """
    from . import gsc

    done = set(ledger.get_state("geo_answered", []))

    # Highest-impression pages first: the block is only worth writing where
    # there is already an audience to be quoted in front of.
    candidates = []
    if gsc.available():
        try:
            for p in sorted(gsc.fetch_pages(), key=lambda p: -p["impressions"]):
                if p["impressions"] >= 5:
                    candidates.append((_url_to_relpath(p["page"]), p["page"],
                                       p["impressions"]))
        except Exception as e:
            ctx.log(f"    geo: Search Console unavailable ({e}); using page order")

    # Without GSC there is still useful work — the money pages are the ones an
    # AI answer would be asked to summarise.
    if not candidates:
        for rel in ("guides/how-much-do-seamless-gutters-cost.html",
                    "guides/gutter-installer-near-me.html",
                    "index.html"):
            candidates.append((rel, f"{SITE}/{rel}", 0))

    errors = []
    for rel, url, impressions in candidates:
        if rel in done:
            continue
        src = ctx.read(rel)
        if src is None or GEO_MARKER in src:
            continue
        anchor = src.find('<div class="container prose">')
        if anchor < 0:
            continue

        queries = []
        if gsc.available():
            try:
                queries = gsc.queries_for_page(url)
            except Exception:
                queries = []

        # A page picks up impressions from well outside York County, and the
        # top row is whichever of those Google sent most of. Answering one of
        # those puts the wrong county at the top of the page — on 2026-07-29
        # /services/gutter-guards.html was given an opening that told readers
        # NEMO serves "Akron, PA and the surrounding Lancaster and York County
        # area", written once and permanent, and it is the exact passage an AI
        # answer engine lifts. Drop them before choosing, and before showing
        # the model what the page ranks for.
        queries = [q for q in queries if not _names_other_market(q["query"])]

        headline = queries[0]["query"] if queries else None
        if not headline:
            # Fall back to the page's own <h1>, which is what it is about.
            m = re.search(r"<h1[^>]*>(.*?)</h1>", src, re.S)
            headline = re.sub(r"<[^>]+>", " ", m.group(1)).strip() if m else None
        if not headline:
            continue

        qlist = "\n".join(f'- "{q["query"]}" — {q["impressions"]} impressions, '
                          f'position {q["position"]:.1f}' for q in queries[:10])
        has_faq = "FAQPage" in src
        try:
            data = llm.call_json(GEO_SYSTEM, (
                f"Page: {url}\n"
                f"The search to answer: \"{headline}\"\n"
                + (f"Everything Google shows this page for:\n{qlist}\n" if qlist else "")
                + (f"\nThis page already has FAQ markup, so the faqs you return will "
                   f"be used as visible copy only.\n" if has_faq else "")),
                max_tokens=2000)
        except Exception as e:
            errors.append(f"generation failed for /{rel}: {e}")
            if len(errors) >= MAX_ITEM_FAILURES:
                break
            continue

        answer = (data.get("answer") or "").strip()
        words = len(answer.split())
        if not answer or not (GEO_MIN_WORDS <= words <= GEO_MAX_WORDS):
            errors.append(f"rejected answer for /{rel}: {words} words "
                          f"(want {GEO_MIN_WORDS}-{GEO_MAX_WORDS})")
            if len(errors) >= MAX_ITEM_FAILURES:
                break
            continue

        block = (f"\n      {GEO_MARKER}"
                 f'\n      <p class="lead">{_esc(answer)}</p>')
        cut = anchor + len('<div class="container prose">')
        head, tail = src[:cut], src[cut:]

        # Most area pages already open with their own p.lead. Two stacked lead
        # paragraphs read as a formatting mistake — same oversized muted type
        # twice before the first heading. The answer becomes the lead and the
        # page's original intro stays as ordinary body copy directly under it.
        demoted = re.match(r'(\s*)<p class="lead">', tail)
        if demoted:
            tail = tail[:demoted.start()] + demoted.group(1) + "<p>" + \
                tail[demoted.end():]
        out = head + block + tail

        # Only add FAQ markup where the page has none. Two FAQPage blocks on one
        # page is worse than none — the engines pick one and the other is noise.
        faqs = [f for f in (data.get("faqs") or []) if f.get("q") and f.get("a")]
        added_faq = False
        if faqs and not has_faq:
            cta = out.find('      <div class="cta-band">')
            if cta < 0:
                cta = out.find('<div class="cta-band">')
            if cta >= 0:
                out = (out[:cta] + _render_faqs(faqs) + "\n\n" + out[cta:])
                ld = f'<script type="application/ld+json">\n{_faq_ld(faqs)}\n</script>'
                body_end = out.rfind("</body>")
                if body_end >= 0:
                    out = out[:body_end] + "  " + ld + "\n" + out[body_end:]
                added_faq = True

        ctx.backup(rel)
        ctx.write(rel, out)
        if not ctx.dry_run:
            ledger.set_state("geo_answered", sorted(done | {rel}))
        return {"ok": True,
                "detail": f"answer-first opening on /{rel} for '{headline}' "
                          f"({words} words{', + FAQ schema' if added_faq else ''}"
                          + (f", {impressions} impressions" if impressions else "")
                          + ")"}

    if errors:
        return {"ok": False,
                "detail": f"{len(errors)} page(s) failed, last: {errors[-1]}"}
    return {"ok": True, "noop": True,
            "detail": "every ranking page already opens with a direct answer"}


REGISTRY = {
    "geo_answer_first_content_pass": geo_answer_first_content_pass,
    "improve_ctr": improve_ctr,
    "adopt_queries": adopt_queries,
    "area_pages": area_pages,
    "service_pages": service_pages,
    "strengthen_pages": strengthen_pages,
    "money_pages": money_pages,
    "internal_links": internal_links,
    "local_schema": local_schema,
    "rebuild_sitemap": rebuild_sitemap,
    "ping_indexnow": ping_indexnow,
}

# Order matters: write pages, wire them together, then tell search engines.
# Strengthening an existing page beats writing a new one, so it runs first and
# gets the pick of the uncovered queries. New pages only get what is left.
# adopt_queries runs first so the day's build queue reflects what people are
# really searching. improve_ctr is next because fixing a page that already
# ranks is worth more than writing one that does not exist yet.
# geo_answer_first_content_pass sits with improve_ctr, not with the builders:
# both make a page that ALREADY ranks work harder, which beats publishing
# another one. It runs second because a page is worth more answering the
# question well than being clicked into and disappointing the reader.
ORDER = ["adopt_queries", "improve_ctr", "geo_answer_first_content_pass",
         "strengthen_pages", "service_pages", "area_pages", "money_pages",
         "internal_links", "local_schema", "rebuild_sitemap", "ping_indexnow"]

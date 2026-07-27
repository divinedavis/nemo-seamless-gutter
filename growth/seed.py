#!/usr/bin/env python3
"""Seed the ledger: the techniques we start with, and the goals we measure against.

Idempotent — `add()` returns the existing record if the slug is already known,
so this runs every morning without duplicating anything. Deliberately small:
six techniques that can be judged, not thirty that cannot.

Anything requiring a human — Business Profile access, a Search Console key, a
budget — is seeded as a `candidate` with the first step written down, so it
surfaces in the daily report's "waiting on you" block instead of silently
never happening.
"""
from . import keywords, ledger

SEED_TECHNIQUES = [
    # ---- running from day one ---------------------------------------------
    dict(slug="area_pages", name="York County town pages", kind="content",
         status="active", prefixes=["/areas/"], metric="owned_visitors",
         hypothesis=(
             "'gutter installation <town> pa' has buying intent, low competition, and "
             "almost no local contractor has a real page for it. One well-written town "
             "page a day builds a moat across the county that a competitor would have to "
             "spend months matching."),
         evidence="The five existing area pages are the site's only town-level coverage; "
                  "York County has 70+ municipalities."),
    dict(slug="strengthen_pages", name="Strengthen pages that should already rank",
         kind="content", status="active", prefixes=[], metric="organic_visitors",
         hypothesis=(
             "Most uncovered queries are not missing a page, they are missing a "
             "heading. 'gutter replacement york pa' points at the installation page, "
             "which never uses the word replacement; 'gutter repair dover pa' belongs "
             "on the Dover page, which only talks about installation. Adding the "
             "section to the page that should already be winning concentrates "
             "authority instead of splitting the site against itself."),
         evidence="Search Console: 5 hire-intent queries sit on pages missing only "
                  "the distinguishing term; 27 more have a natural host page."),
    dict(slug="service_pages", name="Pages for services we rank for but cannot sell",
         kind="content", status="active", prefixes=["/services/"],
         metric="owned_visitors",
         hypothesis=(
             "Search Console shows the site ranking 1.7 for 'gutter soffit and fascia "
             "replacement' with no soffit or fascia page anywhere on it. Visibility "
             "already exists for work with nowhere to send the click."),
         evidence="GSC 28-day query report, 2026-07-27."),
    dict(slug="money_pages", name="Cost and buying guides", kind="content",
         status="active", prefixes=["/guides/"], metric="owned_visitors",
         hypothesis=(
             "Cost queries are the highest-intent traffic a contractor can get, and most "
             "contractors refuse to discuss price — which is why Angi and HomeAdvisor "
             "outrank them and then sell the lead back. Answering the price question "
             "honestly should win the click and the call."),
         evidence="Uncovered price-intent queries in the tracked universe."),
    dict(slug="internal_links", name="Area-page link mesh", kind="indexing",
         status="active", prefixes=[], metric="organic_visitors",
         hypothesis=(
             "New town pages are orphans until something links to them. A nearby-areas "
             "mesh gets them crawled in days instead of weeks and passes local relevance "
             "between them."),
         evidence="Standard internal-linking practice; costs nothing to run."),
    dict(slug="local_schema", name="LocalBusiness structured data", kind="conversion",
         status="active", prefixes=[], metric="local_visitors",
         hypothesis=(
             "The map pack is where the money queries are actually won. Consistent "
             "name/address/phone in structured data on the site is the part of that "
             "Eric controls directly."),
         evidence="NAP consistency is a documented local-pack ranking factor."),
    dict(slug="rebuild_sitemap", name="Sitemap refresh", kind="indexing",
         status="active", prefixes=[], metric="organic_visitors",
         hypothesis="New pages are not crawled until they are in the sitemap.",
         evidence="Existing seo/gen_sitemap.py, re-run after each build."),
    dict(slug="ping_indexnow", name="Same-morning IndexNow push", kind="indexing",
         status="active", prefixes=[], metric="organic_visitors",
         hypothesis=(
             "Submitting only the URLs written this morning gets them into Bing and "
             "Copilot within minutes rather than waiting for the 03:05 full-sitemap run "
             "the following day."),
         evidence="IndexNow is supported by Bing, Yandex, Seznam and Naver."),

    # ---- need a human before they can run ----------------------------------
    dict(slug="review_engine", name="Ask finished jobs for a Google review",
         kind="lifecycle", status="candidate", prefixes=[], metric="local_visitors",
         hypothesis=(
             "Review count and recency are the strongest lever on map-pack rank for a "
             "service business. The profile sits at 13 reviews; competitors ranking above "
             "it have dozens. Every completed booking in the database is a customer who "
             "was never asked."),
         evidence="Google's own local-ranking guidance names review count and score.",
         notes=("first step: confirm with Eric that customers may be emailed a review "
                "request after a completed job, then flip this to active. It emails real "
                "customers, so it stays off until a human says yes.")),
    dict(slug="gbp_posts", name="Weekly Business Profile posts", kind="distribution",
         status="candidate", prefixes=[], metric="local_visitors",
         hypothesis=(
             "Business Profile posts keep the listing active and surface seasonal offers "
             "directly in the pack, where the hire-intent searches land."),
         evidence="GBP is live with ~300 monthly views and 4.2 stars.",
         notes=("first step: OAuth access to the Business Profile API for "
                "enemo@nemoseamlessgutter.com — the engine cannot post without it.")),
    dict(slug="citations", name="NAP citations on local directories",
         kind="distribution", status="candidate", prefixes=[], metric="referral_visitors",
         hypothesis=(
             "Consistent citations across the directories Google cross-checks raise "
             "local-pack confidence, and several of them rank for the money queries "
             "themselves."),
         evidence="Standard local-SEO practice; NAP already verified consistent on-site.",
         notes=("first step: most directories need a captcha or a phone verification, so "
                "this produces a submission pack for Eric rather than auto-submitting. "
                "Flip to active once the pack format is agreed.")),
    dict(slug="gsc_connect", name="Connect Search Console", kind="indexing",
         status="candidate", prefixes=[], metric="organic_visitors",
         hypothesis=(
             "The >50% top-3 goal is not measurable without Search Console. Until it is "
             "connected the engine reports coverage as a proxy and cannot tell whether it "
             "is actually winning."),
         evidence="seo/weekly_digest.py already contains a working GSC client.",
         notes=("first step: create a Google Cloud service account, grant it read access "
                "to the nemoseamlessgutter.com Search Console property, and drop the JSON "
                "at seo/gsc-service-account.json (chmod 600).")),
]

GOALS = {
    # The owner's stated goal, made measurable. `metric` names the series the
    # report reads; `proxy` is what it falls back to while GSC is missing.
    "search_share_pct": {
        "target": 50,
        "definition": "share of the tracked York County gutter queries holding a top-3 position",
        "proxy": "keyword coverage %",
    },
    "leads_per_month": {
        "target": None,
        "definition": "bookings + phone-agent leads per month; no target set by the owner yet",
    },
}


def run():
    for t in SEED_TECHNIQUES:
        ledger.add(slug=t["slug"], name=t["name"], hypothesis=t["hypothesis"],
                   kind=t["kind"], prefixes=t.get("prefixes"),
                   metric=t.get("metric", "organic_visitors"),
                   source="seed", evidence=t.get("evidence", ""),
                   status=t.get("status", "candidate"), notes=t.get("notes", ""))
    if not ledger.get_state("goals"):
        ledger.set_state("goals", GOALS)
    keywords.seed()
    return ledger.load_techniques()

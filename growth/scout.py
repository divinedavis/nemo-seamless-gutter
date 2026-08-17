#!/usr/bin/env python3
"""The 6am scout: find techniques we are not running yet.

Once a day it asks a model with live web search what is currently working for
local home-service contractors — local search, the map pack, AI answer engines,
and getting the phone to ring — then filters the answers against the ledger so
it proposes ideas we have not already tried and rejected.

What it will and will not do:

  proposes   new techniques, written into the ledger as `candidate` with a
             hypothesis and a source. A candidate does not run. Turning one on
             is a deliberate act, which is what keeps a bad idea from deploying
             itself at 6am on a Sunday.
  expands    the tracked keyword universe — the thing the >50% goal is measured
             against. This used to say "pure upside and cost nothing". That is
             false, and the 2026-08-08 review showed why. A new query is the
             DENOMINATOR of the goal (`keywords.py:296` — share_pct is
             top3/total over the whole universe), so adding one lowers the goal
             number even on a day the site got better. And an uncovered query
             joins a write queue that `strengthen_pages` drains at exactly one
             a day by design (BUDGET.md rule 2, which exists because looping
             the queue is both a billing risk and what Google calls scaled
             content abuse). Intake has run at ~5.4 queries/day against that
             drain of 1, so the backlog went 64 -> 92 in the week to 08-08 and
             has grown every single day. Propose queries because they are real
             demand worth knowing about, not because they are free. They are
             not free.
  will NOT   write code, spend money, contact customers, or activate itself.

The techniques that DO change the live site are the ones in techniques.py, which
were reviewed by a human before they were seeded as active.
"""
import json
import os

from . import keywords, ledger, llm, review

MAX_NEW_PER_DAY = 3          # a trickle of well-formed ideas beats a firehose
MAX_KEYWORDS_PER_DAY = 12

SYSTEM = """You are the growth scout for NEMO Seamless Gutter — a one-owner seamless \
gutter contractor in York, Pennsylvania, serving York County. The owner is Eric. The \
business installs seamless aluminum gutter formed on site, half-round aluminum and copper \
for historic homes, gutter guards, and does cleaning and repair.

Your job each day: search the web for growth techniques that are working RIGHT NOW for \
local home-service contractors, and propose ones this business is not already running.

This is a real small business, not a startup. Judge every idea against these rules and \
discard it if it fails any:
- Legal, and within the terms of service of Google, Bing, Yelp, Nextdoor, Meta and any \
other platform involved. NEVER propose fake or incentivised reviews, review gating, \
bought links, private blog networks, cloaking, doorway pages, scraped or AI-spun filler, \
keyword-stuffed location pages, or unsolicited bulk email or SMS. A Google Business \
Profile suspension would cost this business more than any technique could earn it.
- Affordable and executable by one owner with a truck and a brake, plus an automated \
site. If it needs a marketing department or a five-figure budget, it is the wrong idea.
- Honest. Never anything that fabricates credentials, experience, reviews, or prices.
- Judged on the phone ringing. Traffic that does not become an estimate is worthless \
to a contractor. Prefer techniques that reach people in York County who need gutters in \
the next 30 days.
- Seasonal awareness matters: gutter demand in Pennsylvania spikes in autumn leaf-fall \
and after ice-dam season, and drops mid-winter.

Return ONLY valid JSON, no prose:
{
  "techniques": [
    {"slug": "snake_case_id", "name": "short label",
     "kind": "content|indexing|distribution|lifecycle|conversion",
     "hypothesis": "why this should make the phone ring HERE, specifically",
     "evidence": "what you found that suggests it works, with a URL",
     "effort": "hours|days|weeks",
     "cost": "free|under $100/mo|more",
     "expected": "what success would look like in numbers",
     "first_step": "the single concrete first action"}
  ],
  "keywords": [
    {"query": "lowercase search query",
     "town": "york|hanover|dover|red-lion|dallastown|spring-grove|county",
     "intent": "hire|price|diy|check", "why": "why this query matters"}
  ],
  "notes": "anything the owner should know, including ideas you considered and rejected"
}"""


DEFAULT_DOCROOT = os.environ.get("WEB_ROOT", "/var/www/nemo-seamless-gutter")


def _page_names(docroot):
    """Which pages the site actually has, named rather than counted.

    The BUSINESS block used to hardcode "four service pages, five town
    service-area pages, three guides". By 2026-08-08 the real figures were 7,
    15 and 15 — so for twelve days the scout proposed against a site a third
    of the real size, which is a good way to get told to write a page that
    already exists.

    Counting fixed the size and not the problem. On 2026-08-17 the scout
    proposed T071, "Copper & half-round gutter page for York's historic homes",
    whose hypothesis states in as many words "there is no page for it" — while
    /guides/copper-gutters-historic-home-york-pa.html and
    /services/half-round-gutters.html were both live, the second carrying its
    own "Copper Half-Round Gutters for Historic Homes in York, PA" section and
    a historic-district FAQ. A count cannot prevent that: "16 guides" tells a
    writer the site is substantial, not which sixteen subjects are taken. The
    slugs can, so send the slugs.

    Returned per directory so the prompt can keep its shape, and sorted so the
    prompt is stable day to day — a reordering diff would look like a change to
    the site when nothing had changed.
    """
    out = {}
    for sub in ("areas", "guides", "services"):
        # An empty docroot must NOT fall through to a relative path — that
        # lists whatever happens to sit in the cwd, which on the developer's
        # machine is this repo's own copy of the site and looks entirely
        # plausible in the prompt. Empty is the honest answer.
        d = os.path.join(docroot, sub) if docroot else None
        out[sub] = (sorted(f[:-5] for f in os.listdir(d) if f.endswith(".html"))
                    if d and os.path.isdir(d) else [])
    return out


def _page_block(pages):
    """The pages, as prompt text. Names, with counts kept alongside them."""
    lines = []
    for sub in ("services", "areas", "guides"):
        names = pages[sub]
        lines.append(f"{sub} ({len(names)}): "
                     + (", ".join(names) if names else "none"))
    return "\n".join(lines)


def build_prompt(docroot=None):
    techs = ledger.load_techniques()
    running = [f"- {t['name']} [{t['status']}] — {t['hypothesis'][:150]}" for t in techs]
    sb = review.scoreboard()
    tried = [f"- {r['name']}: DID NOT WORK — {r['why']}" for r in sb["does_not_work"]]
    won = [f"- {r['name']}: WORKS — {r['why']}" for r in sb["works"]]
    kw = keywords.summary()

    def last(m):
        s = ledger.series("__site__", m)
        return s[-1][1] if s else "unknown"

    share = (f"{kw['share_pct']}% of {kw['total']} tracked queries in the top 3"
             if kw["share_pct"] is not None else
             f"UNMEASURED (no Search Console). Coverage proxy: {kw['coverage_pct']}% "
             f"of {kw['total']} tracked queries have a page targeting them")

    pages = _page_names(docroot or DEFAULT_DOCROOT)
    backlog = kw["total"] - kw["covered"]

    return f"""Today is {ledger.today()}.

BUSINESS
NEMO Seamless Gutter, nemoseamlessgutter.com — seamless gutter contractor in York, PA.
Google Business Profile is live: 4.2 stars, 13 reviews, roughly 300 profile views a month.
The site has a homepage with an online booking widget, an AI phone agent that answers
calls and captures leads when Eric is on a roof, and these pages already published:

{_page_block(pages)}

Do NOT propose writing a page whose subject is already in that list. If an existing
page covers the subject but covers it badly, say so and propose strengthening that
named page instead of creating a new one.

CURRENT NUMBERS (yesterday unless noted)
- visitors: {last('visitors')}
- organic search visitors: {last('organic_visitors')}
- visitors from Google Maps / directories: {last('local_visitors')}
- AI answer engine visitors: {last('ai_visitors')}
- online bookings: {last('bookings')}
- phone-agent leads: {last('phone_leads')}
- bookings all time: {last('bookings_all_time')}

THE GOAL
More than 50% of gutter searches in York County landing on this business.
Currently: {share}

TECHNIQUES ALREADY IN THE LEDGER (do not re-propose these)
{chr(10).join(running) if running else '(none)'}

ALREADY MEASURED AS WORKING
{chr(10).join(won) if won else '(nothing judged yet)'}

ALREADY MEASURED AS NOT WORKING — do not propose these again
{chr(10).join(tried) if tried else '(nothing retired yet)'}

TASK
1. Search for what is working in 2026 for local home-service contractors specifically:
   Google Business Profile / map-pack ranking, local service-area SEO, getting cited by
   AI answer engines for local trade queries, and converting site visits into phone calls.
   Prefer sources from the last 6 months.
2. Propose at most {MAX_NEW_PER_DAY} techniques NOT already in the ledger. Fewer, better.
3. Propose up to {MAX_KEYWORDS_PER_DAY} search queries to add to the tracked universe —
   real things York County homeowners type about gutters. Propose FEWER than the
   maximum unless they are genuinely good. {backlog} tracked queries are already
   uncovered, and the engine writes content for exactly ONE of them per day, so a
   query added today joins the back of a queue roughly {max(1, backlog)} days long.
   Every query you add also enlarges the denominator of the goal number above, which
   means a weak query makes the business look worse without helping it. Add a query
   because a York County homeowner really types it and it is worth winning — never to
   fill the quota.

The weakest number is the phone ringing, so at least one technique must target calls or
booked estimates directly rather than traffic."""


def run(dry_run=False, docroot=None):
    try:
        key = llm.load_key()
    except Exception:
        key = None
    if not key:
        msg = ("no Anthropic key — expected ANTHROPIC_API_KEY or seo/.env. Scout skipped.")
        print(f"  {msg}")
        ledger.set_state("scout_last", {"date": ledger.today(), "ok": False, "detail": msg})
        return {"ok": False, "detail": msg}

    try:
        data = llm.call_json(SYSTEM, build_prompt(docroot), max_tokens=8000,
                             tools=llm.WEB_SEARCH, key=key)
    except Exception as e:
        print(f"  scout call failed: {e}")
        ledger.set_state("scout_last", {"date": ledger.today(), "ok": False, "detail": str(e)})
        return {"ok": False, "detail": str(e)}

    known = {t["slug"] for t in ledger.load_techniques()}
    added_t, added_k = [], []

    for t in (data.get("techniques") or [])[:MAX_NEW_PER_DAY]:
        slug = (t.get("slug") or "").strip().lower().replace("-", "_")
        if not slug or slug in known:
            continue
        kind = t.get("kind") if t.get("kind") in ledger.VALID_KIND else "distribution"
        notes = "\n".join(filter(None, [
            f"first step: {t.get('first_step')}" if t.get("first_step") else None,
            f"effort: {t.get('effort')}" if t.get("effort") else None,
            f"cost: {t.get('cost')}" if t.get("cost") else None,
            f"expected: {t.get('expected')}" if t.get("expected") else None,
        ]))
        if not dry_run:
            ledger.add(slug=slug, name=t.get("name") or slug,
                       hypothesis=t.get("hypothesis") or "", kind=kind,
                       prefixes=[], metric="organic_visitors",
                       source=f"scout:{ledger.today()}",
                       evidence=t.get("evidence") or "",
                       status="candidate", notes=notes)
        added_t.append(slug)

    for k in (data.get("keywords") or [])[:MAX_KEYWORDS_PER_DAY]:
        q = (k.get("query") or "").strip().lower()
        town = k.get("town") if k.get("town") in keywords.TOWNS else "county"
        if not q:
            continue
        if dry_run:
            added_k.append(q)
        elif keywords.add(q, town, k.get("intent") or "hire",
                          source=f"scout:{ledger.today()}", note=k.get("why", "")):
            added_k.append(q)

    out = {"ok": True, "techniques_added": added_t, "keywords_added": added_k,
           "notes": data.get("notes", "")}
    ledger.set_state("scout_last", {"date": ledger.today(), **out})
    print(f"  proposed {len(added_t)} technique(s), added {len(added_k)} keyword(s)")
    for s in added_t:
        print(f"    + {s}")
    return out

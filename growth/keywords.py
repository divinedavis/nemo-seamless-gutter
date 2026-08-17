#!/usr/bin/env python3
"""The tracked query universe — what ">50% of gutter searches in York PA" means.

You cannot own half of a market you have not defined, so this file defines it:
the queries a York County homeowner actually types when their gutters are
overflowing, sagging, or missing. Share of that universe is the goal metric.

Three things get measured against each query:

  covered   does a page on this site target the query at all? Computable today
            from the docroot; it drives the content roadmap.
  position  where do we actually rank? Only Google Search Console can answer
            that truthfully — scraping the SERP violates Google's terms, gets
            blocked, and returns personalised nonsense anyway. Until a Search
            Console service account is wired up (see seo/weekly_digest.py, which
            already knows how to read one), `position` stays null.
  local     does the query carry local intent? Those are the ones the map pack
            answers, where a Business Profile outranks any amount of content.

THE GOAL, precisely: >50% of these queries holding a top-3 position. With GSC
connected that is measured. Without it, coverage is the honest stand-in and the
daily report says so rather than quietly reporting coverage as if it were rank.

The scout expands this list over time. Entries are never deleted, so the
year-end review can show which queries were won and which were never cracked.
"""
import json
import os
import re

from . import ledger

HERE = os.path.dirname(os.path.abspath(__file__))
KEYWORDS_PATH = os.path.join(HERE, "keywords.json")

# The service area. Queries are tracked per town because "gutter installation
# york pa" and "gutter installation hanover pa" are different SERPs with
# different competitors, and the map pack radius means winning one does not
# win the other.
TOWNS = {
    "york": "York",
    "hanover": "Hanover",
    "dover": "Dover",
    "red-lion": "Red Lion",
    "dallastown": "Dallastown",
    "spring-grove": "Spring Grove",
    "county": "York County",     # county-wide / no town modifier
}

# intent drives what kind of page wins:
#   hire    — ready to buy; map pack + service page. These are the money queries.
#   price   — comparison shopping; cost guides convert well and earn links.
#   diy     — research; guides that build topical authority and AI citations.
#   check   — diagnostic ("why do my gutters overflow"); top of funnel.
SEED = [
    # ---- core hire intent, county + York city -------------------------------
    ("county", "seamless gutters york pa", "hire", "/"),
    ("county", "gutter installation york pa", "hire", "/services/seamless-gutter-installation.html"),
    ("county", "gutter installers york pa", "hire", "/"),
    ("county", "gutter company york pa", "hire", "/"),
    ("county", "gutter contractors york pa", "hire", "/"),
    ("county", "seamless gutter installation york county pa", "hire", "/services/seamless-gutter-installation.html"),
    ("county", "gutter replacement york pa", "hire", "/services/seamless-gutter-installation.html"),
    ("county", "new gutters york pa", "hire", "/services/seamless-gutter-installation.html"),
    ("county", "rain gutters york pa", "hire", "/services/seamless-gutter-installation.html"),
    ("county", "gutter repair york pa", "hire", "/services/gutter-cleaning-repair.html"),
    ("county", "gutter cleaning york pa", "hire", "/services/gutter-cleaning-repair.html"),
    ("county", "gutter guards york pa", "hire", "/services/gutter-guards.html"),
    ("county", "gutter guard installation york pa", "hire", "/services/gutter-guards.html"),
    ("county", "leaf guard york pa", "hire", "/services/gutter-guards.html"),
    ("county", "half round gutters york pa", "hire", "/services/half-round-gutters.html"),
    ("county", "copper gutters york pa", "hire", "/services/half-round-gutters.html"),
    ("county", "downspout repair york pa", "hire", "/services/gutter-cleaning-repair.html"),
    ("county", "gutter services near me york pa", "hire", "/"),
    ("county", "best gutter company york pa", "hire", "/"),
    ("county", "free gutter estimate york pa", "hire", "/"),
    # ---- the five existing area pages ---------------------------------------
    ("hanover", "seamless gutters hanover pa", "hire", "/areas/seamless-gutters-hanover-pa.html"),
    ("hanover", "gutter installation hanover pa", "hire", "/areas/seamless-gutters-hanover-pa.html"),
    ("hanover", "gutter cleaning hanover pa", "hire", "/areas/seamless-gutters-hanover-pa.html"),
    ("dover", "seamless gutters dover pa", "hire", "/areas/seamless-gutters-dover-pa.html"),
    ("dover", "gutter installation dover pa", "hire", "/areas/seamless-gutters-dover-pa.html"),
    ("red-lion", "seamless gutters red lion pa", "hire", "/areas/seamless-gutters-red-lion-pa.html"),
    ("red-lion", "gutter installation red lion pa", "hire", "/areas/seamless-gutters-red-lion-pa.html"),
    ("dallastown", "seamless gutters dallastown pa", "hire", "/areas/seamless-gutters-dallastown-pa.html"),
    ("dallastown", "gutter installation dallastown pa", "hire", "/areas/seamless-gutters-dallastown-pa.html"),
    ("spring-grove", "seamless gutters spring grove pa", "hire", "/areas/seamless-gutters-spring-grove-pa.html"),
    ("spring-grove", "gutter installation spring grove pa", "hire", "/areas/seamless-gutters-spring-grove-pa.html"),
    # ---- price intent: high-converting, and nobody local has good pages ------
    ("county", "gutter installation cost york pa", "price", "/guides/gutter-cleaning-cost-york-pa.html"),
    ("county", "how much do seamless gutters cost", "price", ""),
    ("county", "gutter cleaning cost york pa", "price", "/guides/gutter-cleaning-cost-york-pa.html"),
    ("county", "cost to replace gutters on a house", "price", ""),
    ("county", "gutter guard cost pa", "price", ""),
    ("county", "how much does a gutter guard cost per foot", "price", ""),
    # ---- research / diagnostic: authority + AI answer-engine citations -------
    ("county", "seamless vs sectional gutters", "diy", "/guides/seamless-vs-sectional-gutters.html"),
    ("county", "signs your gutters need replacing", "check", "/guides/signs-your-gutters-need-replacing-york-county-pa.html"),
    ("county", "how often should gutters be cleaned in pa", "diy", ""),
    ("county", "why do my gutters overflow when it rains", "check", ""),
    ("county", "gutter pulling away from house", "check", ""),
    ("county", "what size gutters do i need", "diy", ""),
    ("county", "5 inch vs 6 inch gutters", "diy", ""),
    ("county", "are gutter guards worth it", "diy", ""),
    ("county", "ice dams gutters pennsylvania", "check", ""),
    ("county", "do i need gutters on my house", "diy", ""),
]

VALID_INTENT = ("hire", "price", "diy", "check")

# A top-3 position is the goal. Anything in the map pack counts as top-3 too —
# for "hire" queries the pack sits above the organic results, so a #1 organic
# link under a three-competitor pack is not actually winning the click.
TOP_N = 3


def load():
    try:
        with open(KEYWORDS_PATH) as f:
            return json.load(f)
    except Exception:
        return []


def save(kws):
    tmp = KEYWORDS_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(kws, f, indent=2)
        f.write("\n")
    os.replace(tmp, KEYWORDS_PATH)


def seed():
    """Create the universe if absent. Idempotent — never clobbers added queries."""
    kws = load()
    have = {k["query"] for k in kws}
    for town, query, intent, target in SEED:
        if query in have:
            continue
        kws.append({"query": query, "town": town, "intent": intent,
                    "target": target, "source": "seed", "added": ledger.today(),
                    "covered": None, "position": None,
                    "impressions": None, "clicks": None})
    save(kws)
    return kws


def add(query, town, intent, target="", source="scout", note=""):
    kws = load()
    q = query.strip().lower()
    if any(k["query"] == q for k in kws):
        return None
    if town not in TOWNS:
        return None
    if intent not in VALID_INTENT:
        intent = "hire"
    kws.append({"query": q, "town": town, "intent": intent, "target": target,
                "source": source, "added": ledger.today(), "note": note,
                "covered": None, "position": None,
                "impressions": None, "clicks": None})
    save(kws)
    return q


def _tokens(s):
    return [t for t in re.split(r"[^a-z0-9]+", (s or "").lower()) if len(t) > 2]


STOP = {"the", "and", "for", "how", "what", "out", "much", "can", "you", "your",
        "are", "that", "does", "should", "need", "near", "not", "with", "when",
        "why", "have", "will", "per"}

# Words that appear in the header, footer, title or nav of every page on this
# site. They carry no targeting signal: if "gutter" and "york" were enough to
# call a query covered, the homepage would "cover" all 47 of them and the gap
# list — which is the build queue — would always come back empty.
GENERIC = {"gutter", "gutters", "york", "pennsylvania", "seamless", "nemo",
           "service", "services", "home", "house", "company"}


def _page_text(docroot, target):
    """Read a target page. Targets are explicit file paths on this site
    (/services/foo.html), or "" meaning we have not decided where it should live —
    which is itself the finding the content roadmap acts on."""
    if not target:
        return None
    rel = target.strip("/")
    path = os.path.join(docroot, rel) if rel else os.path.join(docroot, "index.html")
    if os.path.isdir(path):
        path = os.path.join(path, "index.html")
    if not os.path.exists(path):
        return None
    try:
        with open(path, errors="replace") as f:
            return f.read(300_000).lower()
    except Exception:
        return None


# How many distinguishing tokens a query must share with a page's title/h1
# before an unassigned query may be credited to that page. See _find_host().
FALLBACK_MIN_TOKENS = 2


def _headline_index(docroot):
    """{relative path: title + h1 text} for every page on the site.

    Only the title and h1 — deliberately not h2. `strengthen_pages` appends an
    h2 section per run, so the area pages have accumulated dozens of headings
    between them, and matching on h2 credits queries to whichever town page
    happened to receive a section mentioning the words. Measured on
    2026-08-17's uncovered list: h2 matching flipped 43 of 128 queries and its
    picks included "best gutter company york pa" -> the Dallastown page.
    Title and h1 are what the page is *about*.
    """
    index = {}
    if not docroot or not os.path.isdir(docroot):
        return index
    roots = [("", docroot)] + [(sub, os.path.join(docroot, sub))
                               for sub in ("areas", "guides", "services")]
    for sub, d in roots:
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if not name.endswith(".html"):
                continue
            rel = f"/{sub}/{name}" if sub else f"/{name}"
            html = _page_text(docroot, rel)
            if html is None:
                continue
            heads = re.findall(r"<title[^>]*>(.*?)</title>", html, re.S)
            heads += re.findall(r"<h1[^>]*>(.*?)</h1>", html, re.S)
            index[rel] = re.sub(r"<[^>]+>", " ", " ".join(heads))
    return index


def _find_host(key_toks, index):
    """Which existing page already targets this query, if any.

    Coverage is checked against the one page in a keyword's `target`. Nothing
    fills `target` in: `add()` defaults it to "", the scout supplies nothing,
    and only `strengthen_pages` ever sets it — as a side effect of writing a
    new section, at one query a day. So every scout-added query was permanently
    "no page targets this query" no matter what the site actually said. On
    2026-08-17 that was 128 uncovered queries against 190 tracked, while
    /guides/copper-gutters-historic-home-york-pa.html sat live and
    "copper gutters york pa cost" sat in the build queue.

    Three consequences, all observed: `coverage_pct` drifted down as the scout
    added queries faster than one-a-day could cover them (33.5 -> 32.6 that
    morning); `by_intent.price.covered` froze at 3 while price rose 35 -> 46,
    because every new price query arrived uncoverable; and `strengthen_pages`
    spent its single daily write appending sections to pages that already
    answered the query.

    Requiring FALLBACK_MIN_TOKENS distinguishing tokens is what keeps this
    honest. One token is not aboutness: on 2026-08-17 the single-token matches
    were "how much to replace gutters on a house" -> the soffit-and-fascia
    page (wrong), and "gutter cleaning near me york pa" -> three pages at once.
    At two tokens every match was defensible and the wrong ones were excluded.
    Deliberately conservative: a missed match leaves a query in the build
    queue, which costs a day of writing, while a false one marks the goal
    metric covered when nothing covers it.
    """
    want = set(key_toks)
    if len(want) < FALLBACK_MIN_TOKENS:
        return None
    for rel, head in sorted(index.items()):
        if all(t in head for t in want):
            return rel
    return None


def check_coverage(docroot):
    """For each query, does a page exist whose title/h1 actually targets it?

    Deliberately shallow. It catches the real failure mode — a query nobody
    wrote a page for — without pretending to predict rank. A page that merely
    mentions the words in body copy is marked covered-but-weak, which is a
    different (and lesser) thing than a page built for the query.

    A query with no usable `target` falls back to searching the whole site for
    a page whose title/h1 already targets it — see _find_host() for why that
    is not the same as guessing, and what it was fixing.
    """
    kws = load()
    changed = 0
    index = _headline_index(docroot)
    for k in kws:
        html = _page_text(docroot, k.get("target"))
        covered, detail = False, "no page targets this query"
        if html is None:
            # No page assigned, or the assignment points at a file that is not
            # there. Ask the site rather than the (usually empty) target field.
            toks = [t for t in _tokens(k["query"]) if t not in STOP]
            host = _find_host([t for t in toks if t not in GENERIC], index)
            if host:
                covered = True
                detail = f"targeted by title/h1 of {host} (unassigned target)"
        if html is not None:
            heads = re.findall(r"<title[^>]*>(.*?)</title>", html, re.S)
            heads += re.findall(r"<h1[^>]*>(.*?)</h1>", html, re.S)
            heads += re.findall(r"<h2[^>]*>(.*?)</h2>", html, re.S)
            head = re.sub(r"<[^>]+>", " ", " ".join(heads))
            toks = [t for t in _tokens(k["query"]) if t not in STOP]
            # What actually decides coverage: the terms that distinguish this
            # query from every other gutter query on the site.
            key_toks = [t for t in toks if t not in GENERIC]
            miss_head = [t for t in key_toks if t not in head]
            miss_body = [t for t in key_toks if t not in html]
            if not key_toks:
                # A purely generic query ("seamless gutters york pa") — the
                # homepage genuinely is the answer, so require the generic
                # terms in a heading and leave it at that.
                covered = all(t in head for t in toks)
                detail = ("targeted by title/heading" if covered
                          else "generic query, no heading carries it")
            elif not miss_head:
                covered, detail = True, "targeted by title/heading"
            elif not miss_body:
                covered = True
                detail = (f"weak — {', '.join(miss_head)} only in body copy, "
                          f"no heading targets it")
            else:
                detail = f"page exists but missing: {', '.join(miss_body)}"
        if k.get("covered") != covered:
            changed += 1
        k["covered"] = covered
        k["coverage_detail"] = detail
        k["coverage_checked"] = ledger.today()
    save(kws)
    return kws, changed


def apply_gsc(rows):
    """Fold Search Console rows ({query, position, impressions, clicks}) into the
    universe. This is what turns the goal from a proxy into a measurement."""
    if not rows:
        return 0
    by_q = {r["query"].strip().lower(): r for r in rows if r.get("query")}
    kws = load()
    n = 0
    for k in kws:
        r = by_q.get(k["query"])
        if not r:
            continue
        k["position"] = round(float(r.get("position") or 0), 1) or None
        k["impressions"] = int(r.get("impressions") or 0)
        k["clicks"] = int(r.get("clicks") or 0)
        k["gsc_checked"] = ledger.today()
        n += 1
    save(kws)
    return n


def summary():
    kws = load()
    total = len(kws)
    covered = sum(1 for k in kws if k.get("covered"))
    ranked = [k for k in kws if k.get("position")]
    top3 = sum(1 for k in ranked if (k.get("position") or 99) <= TOP_N)
    top10 = sum(1 for k in ranked if (k.get("position") or 99) <= 10)

    by_town, by_intent = {}, {}
    for k in kws:
        t = by_town.setdefault(k.get("town", "county"), {"total": 0, "covered": 0, "top3": 0})
        t["total"] += 1
        t["covered"] += 1 if k.get("covered") else 0
        t["top3"] += 1 if (k.get("position") or 99) <= TOP_N else 0
        i = by_intent.setdefault(k.get("intent", "hire"), {"total": 0, "covered": 0})
        i["total"] += 1
        i["covered"] += 1 if k.get("covered") else 0

    return {
        "total": total,
        "covered": covered,
        "coverage_pct": round(100.0 * covered / total, 1) if total else 0.0,
        "ranked_known": len(ranked),
        "top3": top3,
        "top10": top10,
        # The goal number. None means Search Console is not connected, and the
        # report must say "unmeasured" rather than dressing coverage up as rank.
        "share_pct": round(100.0 * top3 / total, 1) if total and ranked else None,
        "by_town": by_town,
        "by_intent": by_intent,
        # Every tracked query Search Console returns a position for, best
        # first. The aggregates above say the top-3 count went 2 -> 1; only
        # this says which query fell, and "which one" is the difference
        # between a fact and a shrug. Cheap to carry — `ranked_known` has
        # been 17-22 since Search Console was connected.
        "ranked": [{"query": k["query"], "town": k.get("town"),
                    "intent": k.get("intent"), "target": k.get("target"),
                    "covered": bool(k.get("covered")),
                    "position": k.get("position"),
                    "impressions": k.get("impressions"),
                    "clicks": k.get("clicks")}
                   for k in sorted(ranked, key=lambda x: float(x["position"]))],
        # Uncovered "hire" queries first — those are the ones that pay.
        "gaps": [k["query"] for k in
                 sorted(kws, key=lambda x: (x.get("intent") != "hire", x["query"]))
                 if not k.get("covered")],
    }

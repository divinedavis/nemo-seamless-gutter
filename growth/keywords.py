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
    # The ten towns `techniques.TOWN_QUEUE` has published an area page for.
    # They were absent here until 2026-10-04, which meant ten of the fifteen
    # live area pages had no tracked query at all: `by_town` could not show
    # them, `top3` could not count them, and nothing in the goal metric could
    # say whether any of those pages ranked for the town it was written for.
    # A page the engine publishes has to be measurable, or publishing it is
    # unfalsifiable. See `test_keywords.TownCoverage`.
    "dillsburg": "Dillsburg",
    "shrewsbury": "Shrewsbury",
    "stewartstown": "Stewartstown",
    "new-freedom": "New Freedom",
    "glen-rock": "Glen Rock",
    "manchester": "Manchester",
    "mount-wolf": "Mount Wolf",
    "wrightsville": "Wrightsville",
    "hallam": "Hallam",
    "jacobus": "Jacobus",
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
    # ---- the ten area pages TOWN_QUEUE published, so they can be scored ----
    ("dillsburg", "seamless gutters dillsburg pa", "hire", "/areas/seamless-gutters-dillsburg-pa.html"),
    ("dillsburg", "gutter installation dillsburg pa", "hire", "/areas/seamless-gutters-dillsburg-pa.html"),
    ("shrewsbury", "seamless gutters shrewsbury pa", "hire", "/areas/seamless-gutters-shrewsbury-pa.html"),
    ("shrewsbury", "gutter installation shrewsbury pa", "hire", "/areas/seamless-gutters-shrewsbury-pa.html"),
    ("stewartstown", "seamless gutters stewartstown pa", "hire", "/areas/seamless-gutters-stewartstown-pa.html"),
    ("stewartstown", "gutter installation stewartstown pa", "hire", "/areas/seamless-gutters-stewartstown-pa.html"),
    ("new-freedom", "seamless gutters new freedom pa", "hire", "/areas/seamless-gutters-new-freedom-pa.html"),
    ("new-freedom", "gutter installation new freedom pa", "hire", "/areas/seamless-gutters-new-freedom-pa.html"),
    ("glen-rock", "seamless gutters glen rock pa", "hire", "/areas/seamless-gutters-glen-rock-pa.html"),
    ("glen-rock", "gutter installation glen rock pa", "hire", "/areas/seamless-gutters-glen-rock-pa.html"),
    ("manchester", "seamless gutters manchester pa", "hire", "/areas/seamless-gutters-manchester-pa.html"),
    ("manchester", "gutter installation manchester pa", "hire", "/areas/seamless-gutters-manchester-pa.html"),
    ("mount-wolf", "seamless gutters mount wolf pa", "hire", "/areas/seamless-gutters-mount-wolf-pa.html"),
    ("mount-wolf", "gutter installation mount wolf pa", "hire", "/areas/seamless-gutters-mount-wolf-pa.html"),
    ("wrightsville", "seamless gutters wrightsville pa", "hire", "/areas/seamless-gutters-wrightsville-pa.html"),
    ("wrightsville", "gutter installation wrightsville pa", "hire", "/areas/seamless-gutters-wrightsville-pa.html"),
    ("hallam", "seamless gutters hallam pa", "hire", "/areas/seamless-gutters-hallam-pa.html"),
    ("hallam", "gutter installation hallam pa", "hire", "/areas/seamless-gutters-hallam-pa.html"),
    ("jacobus", "seamless gutters jacobus pa", "hire", "/areas/seamless-gutters-jacobus-pa.html"),
    ("jacobus", "gutter installation jacobus pa", "hire", "/areas/seamless-gutters-jacobus-pa.html"),
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
    """Every alphanumeric token, however short.

    This used to drop anything of two characters or fewer, which was a cheap
    way of throwing out "the", "in" and "pa" — and it threw out "5", "6" and
    "vs" with them. Measured on 2026-09-29 against the live tracked universe,
    that cutoff left 16 of the 131 uncovered queries with fewer than
    FALLBACK_MIN_TOKENS distinguishing tokens, so _find_host() could never
    credit them no matter what the site said. Two of those queries had pages
    live and titled for them:

        5 inch vs 6 inch gutters        -> guides/5-vs-6-inch-gutters-…
        seamless gutters vs sectional   -> guides/seamless-vs-sectional-gutters

    strengthen_pages therefore kept both in its build queue, which is exactly
    the waste _find_host() exists to stop. Short words that really are noise
    are now named in STOP and GENERIC, where the reason for dropping them is
    written down, instead of being silently removed by a length.
    """
    return [t for t in re.split(r"[^a-z0-9]+", (s or "").lower()) if t]


STOP = {"the", "and", "for", "how", "what", "out", "much", "can", "you", "your",
        "are", "that", "does", "should", "need", "near", "not", "with", "when",
        "why", "have", "will", "per",
        # Two characters and under. These were removed by the old length cutoff
        # in _tokens(); they are listed explicitly so that lifting the cutoff
        # does not re-admit them. "vs" is deliberately absent — it is the whole
        # distinguishing content of a comparison query.
        "a", "an", "as", "at", "be", "by", "do", "i", "if", "in", "is", "it",
        "my", "me", "no", "of", "on", "or", "so", "to", "up", "us", "we"}

# Words that appear in the header, footer, title or nav of every page on this
# site. They carry no targeting signal: if "gutter" and "york" were enough to
# call a query covered, the homepage would "cover" all 47 of them and the gap
# list — which is the build queue — would always come back empty.
#
# Membership is a claim about this site, and it has to be checked against it.
# "company" sat here until 2026-09-29 and was never true: counted over all 44
# live pages, it appears in exactly one title or h1 —
# /guides/best-gutter-company-york-county-pa.html, which money_pages published
# on 2026-07-28 for precisely that query. Calling it generic discarded the one
# token that told the two apart, left "best gutter company york pa" with a
# single distinguishing token, and so kept a query in strengthen_pages' build
# queue for two months while the page written for it sat live.
GENERIC = {"gutter", "gutters", "york", "pennsylvania", "seamless", "nemo",
           "service", "services", "home", "house",
           # The state abbreviations. Every page on this site is in
           # Pennsylvania, so "pa" distinguishes nothing — it was removed by
           # _tokens()' old length cutoff and belongs here now that short
           # tokens survive.
           "pa", "penna"}


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


def _word_set(text):
    """The tokens of a heading or a body, for matching query tokens against."""
    return {t for t in re.split(r"[^a-z0-9]+", (text or "").lower()) if t}


# A short token has to match a whole word; a longer one may match the start of
# one, so "installer" still matches "installers" and "clean" still matches
# "cleaning". Four is where that stops being a plural rule and starts being a
# coincidence.
PREFIX_MIN = 4


def _has(words, token):
    """Does this set of words carry this query token, on word boundaries?

    Matching used to be raw substring containment against the joined heading
    string, which was safe only because _tokens() threw away everything of two
    characters or fewer. Now that "5", "6" and "vs" survive, substring matching
    is a bug waiting to fire: "6" is a substring of "2026", which appears in
    several live page titles, so every page carrying the year would hand out
    coverage for every 6-inch query on the site. That is the same false-credit
    failure as the leaked <title> fixed on 2026-09-28, arriving by a different
    door. Match words, not characters.
    """
    if token in words:
        return True
    if len(token) >= PREFIX_MIN:
        return any(w.startswith(token) for w in words)
    return False


def _missing(text, tokens):
    """The query tokens this text does not carry."""
    words = _word_set(text)
    return [t for t in tokens if not _has(words, t)]


# How many distinguishing tokens a query must share with a page's title/h1
# before an unassigned query may be credited to that page. See _find_host().
FALLBACK_MIN_TOKENS = 2


def _titles(html):
    """The page's own <title>, and only the first one.

    A page has exactly one title. Two means something leaked, and on
    2026-09-27 that cost the goal metric two queries' worth of honesty:
    `seo/gen_article.py` copied everything from a source guide's Google tag
    to `</head>` when it generated a new article, which carried that guide's
    *title* along with the tag block. `5-vs-6-inch-gutters-...html` therefore
    shipped with a second title reading "Seamless vs. Sectional Gutters:
    Which Is Better?", and `check_coverage` — matching against every title it
    found — credited "5 inch vs 6 inch gutters which do i need" and
    "...which is better" to that page on the strength of a heading belonging
    to a different page. Both read `covered` for weeks. Divine fixed the
    generator and stripped the leaked block on 2026-09-27 (ce84002) and
    `covered` fell 94 -> 92 the next morning: the drop was the metric getting
    more honest, not the site getting worse.

    The generator bug is fixed. This is the guard that stops the next one
    being invisible: coverage is a claim about what a page is *about*, and a
    borrowed title is not that. Deliberately not extended to h1 — a second h1
    is bad HTML but it is still this page's own words.
    """
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S)
    return [m.group(1)] if m else []


def _visible_text(html):
    """What the page actually says to a reader, with the machinery removed.

    The weak-coverage branch of check_coverage() used to ask whether a term
    appeared anywhere in the raw file, which is not the same question. A raw
    file also contains the meta description, the JSON-LD blocks, the inline
    analytics and consent scripts, every tag attribute, and — until
    2026-09-27 — a whole leaked <title> belonging to another page. On that
    file, "5 inch vs 6 inch gutters which is better" was credited weak
    coverage because "which" and "better" appeared in the borrowed title,
    thirty lines above the <body>. Dropping the leaked title from the head
    check alone did not fix it: the raw-file check let it back in.

    So this is the pair to _titles(). Coverage means the page says the thing.
    Body text, scripts and templates removed, tags removed with their
    attributes — a term surviving in here is a term a reader could have read.
    """
    m = re.search(r"<body[^>]*>(.*)</body>", html, re.S)
    body = m.group(1) if m else html
    body = re.sub(r"<(script|style|template|noscript)\b[^>]*>.*?</\1>",
                  " ", body, flags=re.S)
    body = re.sub(r"<[^>]+>", " ", body)
    return re.sub(r"\s+", " ", body)


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
            heads = _titles(html)
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
        if not _missing(head, want):
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
            heads = _titles(html)
            heads += re.findall(r"<h1[^>]*>(.*?)</h1>", html, re.S)
            heads += re.findall(r"<h2[^>]*>(.*?)</h2>", html, re.S)
            head = re.sub(r"<[^>]+>", " ", " ".join(heads))
            toks = [t for t in _tokens(k["query"]) if t not in STOP]
            # What actually decides coverage: the terms that distinguish this
            # query from every other gutter query on the site.
            key_toks = [t for t in toks if t not in GENERIC]
            miss_head = _missing(head, key_toks)
            visible = _visible_text(html)
            miss_body = _missing(visible, key_toks)
            if not key_toks:
                # A purely generic query ("seamless gutters york pa") — the
                # homepage genuinely is the answer, so require the generic
                # terms in a heading and leave it at that.
                covered = not _missing(head, toks)
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

#!/usr/bin/env python3
"""Is Google actually indexing these pages, and if not, how far did it get?

The rank goal this engine chases is measured from impressions, and an
impression needs two independent things: the page is in Google's index, AND
somebody typed a query it could answer. When a page earns nothing, those two
causes look identical and have opposite responses — a page Google never
fetched needs links and crawl signals, a page it fetched and declined needs to
be better, and a page it indexed that nobody searched for needs a different
query target entirely.

The URL Inspection API returns Google's own coverage state per URL, which is
the direct measurement. Find A Crib has had this since 2026-08-17 against a
47,600-page corpus and needed stratified sampling to afford it. This sitemap is
41 URLs against a 2,000/day quota, so every URL is read every run and there is
no sampling to reason about.

Auth and property resolution come from gsc.py rather than being rebuilt here —
including the Domain-vs-URL-prefix resolution, which is the mistake that reads
as a permissions error. This is a `sc-domain:` property and the inspect call
needs that exact string as siteUrl.
"""
import datetime
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from . import gsc

SITEMAP = os.environ.get("NEMO_SITEMAP",
                         "https://nemoseamlessgutter.com/sitemap.xml")
INSPECT_API = "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect"

HERE = os.path.dirname(os.path.abspath(__file__))
STATUS_PATH = os.path.join(HERE, "index_status.json")

MAX_URLS = int(os.environ.get("NEMO_INDEX_MAX", "300"))
PACE_SECONDS = 0.4        # ~150/min against a 600/min ceiling

# Google's coverageState strings are prose and have changed wording before, so
# match on the substring that carries the meaning rather than on equality.
# Vocabulary and the lesson behind `unknown_to_google` both come from Find A
# Crib's indexstatus.py: without that needle the single most decision-relevant
# state falls into a catch-all bucket and cannot be seen at all.
_STATE_BUCKETS = (
    ("indexed", ("submitted and indexed", "indexed, not submitted")),
    ("crawled_not_indexed", ("crawled - currently not indexed",
                             "crawled — currently not indexed")),
    ("discovered_not_indexed", ("discovered - currently not indexed",
                                "discovered — currently not indexed")),
    # Never fetched at all, not merely un-indexed. The discriminator is that a
    # never-seen URL carries no lastCrawlTime and an unspecified fetch state;
    # Google has been observed relabelling long-known URLs "unknown" while they
    # keep their crawl time.
    ("unknown_to_google", ("unknown to google",)),
    ("duplicate", ("duplicate", "alternate page")),
    ("excluded_noindex", ("noindex",)),
    ("blocked", ("blocked", "robots.txt")),
    ("redirect", ("redirect",)),
    ("not_found", ("not found", "404", "soft 404")),
)
BUCKETS = [b for b, _ in _STATE_BUCKETS] + ["other", "unknown"]


def bucket(state):
    if not state:
        return "unknown"
    s = state.strip().lower()
    for name, needles in _STATE_BUCKETS:
        if any(nd in s for nd in needles):
            return name
    return "other"


def sitemap_urls(url=None, timeout=20):
    req = urllib.request.Request(url or SITEMAP,
                                 headers={"User-Agent": "nemo-growth/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        root = ET.fromstring(r.read())
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    return [e.text.strip() for e in root.iter(ns + "loc") if e.text]


def inspect(token, prop, url, timeout=30):
    """One URL Inspection call. Returns (record, error_string)."""
    body = json.dumps({"inspectionUrl": url, "siteUrl": prop,
                       "languageCode": "en-US"}).encode()
    req = urllib.request.Request(
        INSPECT_API, data=body,
        headers={"Authorization": "Bearer " + token,
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            payload = json.loads(r.read())
    except urllib.error.HTTPError as e:
        return None, "HTTP %d: %s" % (e.code, e.read().decode("utf-8", "replace")[:200])
    except Exception as e:
        return None, "%s: %s" % (type(e).__name__, e)
    idx = ((payload.get("inspectionResult") or {}).get("indexStatusResult") or {})
    state = idx.get("coverageState")
    rec = {
        "state": state,
        "bucket": bucket(state),
        "verdict": idx.get("verdict"),
        "crawled": (idx.get("lastCrawlTime") or "")[:10] or None,
        "fetch": idx.get("pageFetchState"),
        "checked": datetime.date.today().isoformat(),
    }
    gc = idx.get("googleCanonical")
    if gc and gc.rstrip("/") != url.rstrip("/"):
        rec["google_canonical"] = gc
    return rec, None


def load():
    try:
        with open(STATUS_PATH) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def run(limit=None, dry_run=False):
    """Inspect every sitemap URL. Never raises — a Search Console outage must
    not take down the 6am run, same contract as gsc.sync()."""
    if not gsc.available():
        return {"ok": False, "connected": False,
                "detail": "no key at %s" % os.path.abspath(gsc.SA_KEY)}
    try:
        with open(gsc.SA_KEY) as f:
            sa = json.load(f)
        token = gsc._token(sa)
        prop, seen = gsc.resolve_property(token)
    except Exception as e:
        return {"ok": False, "connected": False,
                "detail": "%s: %s" % (type(e).__name__, str(e)[:160])}

    try:
        urls = sitemap_urls()
    except Exception as e:
        return {"ok": False, "connected": True,
                "detail": "sitemap unreadable: %s" % e}
    capped = len(urls) > (limit or MAX_URLS)
    total = len(urls)
    urls = urls[: (limit or MAX_URLS)]

    pages, errors = {}, []
    for i, u in enumerate(urls):
        rec, err = inspect(token, prop, u)
        if err:
            errors.append({"url": u, "error": err})
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                errors.append({"url": "(stopped)", "error": "quota exhausted"})
                break
        else:
            pages[u] = rec
        if i + 1 < len(urls):
            time.sleep(PACE_SECONDS)

    counts = {b: 0 for b in BUCKETS}
    for rec in pages.values():
        counts[rec["bucket"]] = counts.get(rec["bucket"], 0) + 1
    read = len(pages)
    fetched = sum(counts[b] for b in
                  ("indexed", "crawled_not_indexed", "duplicate",
                   "excluded_noindex", "redirect", "not_found"))
    doc = {
        "ok": True,
        "connected": True,
        "updated": datetime.date.today().isoformat(),
        "property": prop,
        "sitemap_urls": total,
        "inspected": read,
        "buckets": counts,
        # Two denominators, two questions. accept_pct is "of everything we
        # published"; accept_of_fetched is "of what Google actually looked at".
        # The second says whether the pages are good enough; the first mixes
        # that up with whether Google has got round to them yet.
        "accept_pct": round(100.0 * counts["indexed"] / read, 1) if read else None,
        "accept_of_fetched": round(100.0 * counts["indexed"] / fetched, 1) if fetched else None,
        "capped": capped,
        "errors": errors[:10],
        "pages": pages,
    }
    if not dry_run:
        tmp = STATUS_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump(doc, f, indent=1, sort_keys=True)
        os.replace(tmp, STATUS_PATH)
    return doc


def summary(doc=None):
    d = doc or load()
    if not d or not d.get("ok"):
        return {"measured": False, "detail": (d or {}).get("detail")}
    b = d.get("buckets") or {}
    return {
        "measured": True,
        "updated": d.get("updated"),
        "sitemap_urls": d.get("sitemap_urls"),
        "inspected": d.get("inspected"),
        "indexed": b.get("indexed", 0),
        "crawled_not_indexed": b.get("crawled_not_indexed", 0),
        "discovered_not_indexed": b.get("discovered_not_indexed", 0),
        "unknown_to_google": b.get("unknown_to_google", 0),
        "accept_pct": d.get("accept_pct"),
        "accept_of_fetched": d.get("accept_of_fetched"),
        "errors": len(d.get("errors") or []),
    }


if __name__ == "__main__":
    print(json.dumps(summary(run()), indent=2))

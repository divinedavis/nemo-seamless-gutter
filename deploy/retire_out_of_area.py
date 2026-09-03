#!/usr/bin/env python3
"""Find — and on request retire — live pages and tracked keywords for towns
NEMO does not serve.

Why this exists, and why it is here rather than in growth/
---------------------------------------------------------
On 2026-09-03 `money_pages` published

    /guides/5-inch-gutter-service-york-springs-pa.html

York Springs is in Adams County. The page says, in its own words, that NEMO
"works York Springs and the surrounding Adams and northern York County area" —
a service-area claim nobody at the business made — while its breadcrumb still
reads "York County, PA".

Two guards in `growth/techniques.py` would each have stopped it on its own:

    >>> _names_other_market('5 inch gutter service york springs pa')
    True                       # intake guard, added 2026-09-01
    >>> _off_area_prose(<the page's visible text>)
    'york springs'             # output guard, added 2026-08-13

Neither is on the droplet. Nothing under `growth/` has been deployed since
early August, so the fixes sit in git while the bug runs daily. Deploying
`growth/` stops the *next* one; it does not remove the page already on disk,
and it does not delete the rows `adopt_queries` has already written into the
live `growth/keywords.json` (six York Springs queries as of 2026-09-02, which
is why `tracked_queries` climbed 195 -> 202 and `coverage_pct` fell — the goal's
denominator filled up with searches NEMO cannot serve).

Repairing any of this in the git repo does not work: `growth/publish_state.sh`
rsyncs `areas/`, `guides/`, `services/` and the state files **docroot -> repo**
each morning, so the repo's copies are a read-only mirror. The only place the
change can land is the docroot. Hence a script that runs there, against the
live files, importing nothing from the growth package.

Usage, on the droplet
---------------------
    cd /var/www/nemo-seamless-gutter
    python3 deploy/retire_out_of_area.py            # report only, writes nothing
    python3 deploy/retire_out_of_area.py --apply    # retire + back up

Safe to re-run: once a page is retired and its rows are gone, a second run
reports nothing to do. Nothing is deleted — a retired page is *renamed* to
`<name>.retired-bak` (so nginx serves 404 and Google drops it) and every file
rewritten is copied to `<name>.bak` first.

What it deliberately will NOT do
--------------------------------
It only retires a page whose **slug** names an out-of-area town — a page that
is wholly about somewhere NEMO does not work. A page with a good slug that
merely *mentions* an out-of-area place in its copy is reported and left alone:
`/services/gutter-guards.html` has opened with "homes in Akron, PA and the
surrounding Lancaster and York County area" since 2026-07-29, and that page
needs its paragraph rewritten, not its URL deleted. Deleting it would throw
away a real service page over one bad sentence.

This is a judgement call, not a bug fix
---------------------------------------
Whether York Springs is out of area is Eric's to decide, not this script's.
York Springs is roughly 25 minutes from York city; if Eric will drive it, the
right response is the opposite of this script — keep the page, add York Springs
to the Business Profile service area, and drop it from `OUT_OF_AREA` in
`growth/techniques.py`. Run this only if the answer is that he will not. Either
way the site and the profile should tell the same geographic story; what cannot
stand is the current state, where an unreviewed page claims a county the
profile does not.
"""

import argparse
import html
import json
import os
import re
import shutil
import sys

# A copy of growth.techniques.OUT_OF_AREA as of 2026-09-03, deliberately
# duplicated rather than imported: this script's whole reason to exist is that
# the droplet's growth/ package is older than the repo's, so importing the
# filter from it would get the stale list — the very list that let the page
# through. Re-sync by hand if OUT_OF_AREA changes.
OUT_OF_AREA = (
    "perkasie", "yorkville", "york sc", "york ne", "york me", "york maine",
    "york uk", "yorktown", "new york", "akron", "myerstown", "newmanstown",
    "essington", "crum lynne", "york springs",
)

# "Somewhere County" where somewhere is not York. Matched case-sensitively
# against the original text: lowering first would make "the county" match.
OFF_AREA_COUNTY = re.compile(r"\b([A-Z][a-z]+)\s+County\b")

PAGE_DIRS = ("areas", "guides", "services")
KEYWORDS = os.path.join("growth", "keywords.json")
SITEMAP = "sitemap.xml"


def _visible_text(markup):
    """The page's human-readable text: tags and scripts stripped.

    Scripts go first and for a reason — the JSON-LD block carries
    "York County, Pennsylvania" as `areaServed` on every page, so leaving it in
    would make the county check fire on pages that are perfectly fine.
    """
    body = re.sub(r"<script.*?</script>", " ", markup, flags=re.S | re.I)
    body = re.sub(r"<style.*?</style>", " ", body, flags=re.S | re.I)
    return html.unescape(re.sub(r"<[^>]+>", " ", body))


def _off_area(text):
    """The place this text names that NEMO does not serve, or None.

    Word boundaries matter: OUT_OF_AREA holds "york ne" for York, Nebraska, and
    a plain substring test would reject the sentence "a York neighborhood".
    """
    low = text.lower()
    for bad in OUT_OF_AREA:
        if re.search(r"\b%s\b" % re.escape(bad), low):
            return bad
    for m in OFF_AREA_COUNTY.finditer(text):
        if m.group(1).lower() != "york":
            return m.group(0)
    return None


def _slug_off_area(path):
    """The out-of-area town this page's URL is about, or None.

    Reads the slug only. Hyphens become spaces so "york-springs-pa" matches the
    "york springs" entry, and the check is anchored on word boundaries so
    "yorktown" does not match a file named "york-town-hall".
    """
    slug = os.path.basename(path).rsplit(".", 1)[0].replace("-", " ").lower()
    for bad in OUT_OF_AREA:
        if re.search(r"\b%s\b" % re.escape(bad), slug):
            return bad
    return None


def scan_pages(root):
    """(pages whose slug is out of area, pages that merely name one)."""
    by_slug, by_prose = [], []
    for d in PAGE_DIRS:
        full = os.path.join(root, d)
        if not os.path.isdir(full):
            continue
        for name in sorted(os.listdir(full)):
            if not name.endswith(".html"):
                continue
            rel = os.path.join(d, name)
            bad = _slug_off_area(name)
            if bad:
                by_slug.append((rel, bad))
                continue
            try:
                with open(os.path.join(full, name), encoding="utf-8") as fh:
                    markup = fh.read()
            except OSError as e:
                print("  ! could not read %s: %s" % (rel, e), file=sys.stderr)
                continue
            named = _off_area(_visible_text(markup))
            if named:
                by_prose.append((rel, named))
    return by_slug, by_prose


def scan_keywords(root):
    """(all rows, rows naming somewhere out of area). Empty if unreadable."""
    path = os.path.join(root, KEYWORDS)
    try:
        with open(path, encoding="utf-8") as fh:
            rows = json.load(fh)
    except (OSError, ValueError) as e:
        print("  ! could not read %s: %s" % (KEYWORDS, e), file=sys.stderr)
        return [], []
    if not isinstance(rows, list):
        print("  ! %s is not a list — leaving it alone" % KEYWORDS, file=sys.stderr)
        return [], []
    bad = []
    for r in rows:
        q = r.get("query") if isinstance(r, dict) else r
        if isinstance(q, str) and _off_area(q):
            bad.append(r)
    return rows, bad


def _backup(path):
    shutil.copy2(path, path + ".bak")


def retire_pages(root, pages):
    for rel, _bad in pages:
        src = os.path.join(root, rel)
        dst = src + ".retired-bak"
        if os.path.exists(dst):
            print("  · %s already retired" % rel)
            continue
        os.rename(src, dst)
        print("  - retired %s -> %s" % (rel, os.path.basename(dst)))


def prune_keywords(root, rows, bad):
    path = os.path.join(root, KEYWORDS)
    _backup(path)
    keep = [r for r in rows if r not in bad]
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(keep, fh, indent=1)
        fh.write("\n")
    os.replace(tmp, path)
    print("  - %s: %d rows -> %d" % (KEYWORDS, len(rows), len(keep)))


def prune_sitemap(root, pages):
    """Drop the retired URLs from sitemap.xml.

    Strictly optional — `rebuild_sitemap` regenerates it from what is on disk
    every morning, so it self-heals within a day. Doing it here makes the
    removal take effect on the next crawl instead of the one after.
    """
    path = os.path.join(root, SITEMAP)
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        lines = fh.readlines()
    slugs = [rel.replace(os.sep, "/") for rel, _ in pages]
    keep = [l for l in lines if not any("/%s<" % s in l for s in slugs)]
    if len(keep) == len(lines):
        return
    _backup(path)
    with open(path, "w", encoding="utf-8") as fh:
        fh.writelines(keep)
    print("  - %s: %d URL lines removed" % (SITEMAP, len(lines) - len(keep)))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=".",
                    help="site docroot (default: current directory)")
    ap.add_argument("--apply", action="store_true",
                    help="actually retire; without it, nothing is written")
    args = ap.parse_args(argv)
    root = os.path.abspath(args.root)

    by_slug, by_prose = scan_pages(root)
    rows, bad_rows = scan_keywords(root)

    print("Scanning %s" % root)
    print("\nPages whose URL is about a town NEMO does not serve: %d" % len(by_slug))
    for rel, bad in by_slug:
        print("  %-64s names %r" % (rel, bad))
    print("\nPages that merely mention one — REPORT ONLY, never retired here: %d"
          % len(by_prose))
    for rel, bad in by_prose:
        print("  %-64s names %r" % (rel, bad))
    print("\nTracked keyword rows out of area: %d of %d" % (len(bad_rows), len(rows)))
    for r in bad_rows:
        print("  %s" % (r.get("query") if isinstance(r, dict) else r))

    if not by_slug and not bad_rows:
        print("\nNothing to retire.")
        return 0
    if not args.apply:
        print("\nReport only. Re-run with --apply to retire the pages above,"
              "\nprune the keyword rows, and drop the URLs from sitemap.xml."
              "\nEvery file touched is backed up first; nothing is deleted.")
        return 0

    print("\nApplying:")
    retire_pages(root, by_slug)
    if bad_rows:
        prune_keywords(root, rows, bad_rows)
    prune_sitemap(root, by_slug)
    print("\nDone. The pages above now 404. Deploy growth/ as well, or"
          "\n`adopt_queries` and `money_pages` will put them straight back.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Repair — not delete — live pages whose copy claims towns NEMO does not serve.

Why this exists, and why it is here rather than in growth/
---------------------------------------------------------
Two service pages in the docroot have been telling the public since 2026-07-29
that NEMO works a ninety-mile footprint it does not work:

    services/gutter-guards.html:207
        "...installs gutter guards on homes in Akron, PA and the surrounding
         Lancaster and York County area."
    services/seamless-gutter-installation.html:271-281
        An entire <h2> section — three paragraphs, a bullet list and an FAQ
        pair — headed "Seamless Gutter Installation in Schuylkill County, PA",
        whose FAQ answers "Do you actually service Schuylkill County, or just
        the York area?" with "We service both."

Meanwhile `index.html`'s LocalBusiness schema declares `areaServed` as "York
County, Pennsylvania" and nothing else. The site argues both sides of its own
service area in public, and since Google replaced Business Profile Q&A with
Ask Maps the website is a direct input to Google's generated answer to "do they
serve my town?" — an answer the owner can no longer correct by hand.

`retire_out_of_area.py` finds both pages and deliberately leaves them alone:
its rule is that it only retires a page whose *slug* names an out-of-area town,
because deleting a real service page over one bad sentence throws away the
good page with the bad copy. That is the right rule. This script is the other
half of it — the repair path that rule implies and that nothing has provided,
which is why these two blocks have outlived four written recommendations.

The generation-time guards in `growth/techniques.py` (`OUT_OF_AREA`,
`_names_other_market`, `_off_area_prose`) stop the *next* such block and only
once `growth/` is deployed. They cannot rewrite text already on disk.

Repairing the pages in the git repo does not work: `growth/publish_state.sh`
rsyncs `areas/`, `guides/` and `services/` **docroot -> repo** every morning at
06:05, so the repo's copies are a read-only mirror and a commit here is
reverted by the next publish. The only place a page repair can land is the
docroot. Hence a script that runs there, against the live files, importing
nothing from the growth package — the same shape as
`repair_placeholder_paragraphs.py` and `repair_letter_paragraphs.py`, and for
the same reason.

Usage, on the droplet
---------------------
    cd /var/www/nemo-seamless-gutter
    python3 deploy/repair_out_of_area_prose.py            # report only
    python3 deploy/repair_out_of_area_prose.py --apply    # repair + back up

Safe to re-run: a repaired page has no out-of-area copy left to match, so a
second run reports nothing to do. Every file rewritten is copied to
`<name>.outofarea-bak` first and nothing is deleted.

What it deliberately will NOT do
--------------------------------
It will not invent copy. There are exactly two kinds of repair here and both
are subtractive:

  * **Section cut** — an `<h2>` whose own heading names a place NEMO does not
    serve takes the whole section with it, up to the next `<h2>`. A heading
    that names the subject of the section is the one place a place-name is
    unambiguously what the section is *about*, so cutting to the next heading
    removes exactly that subject and nothing else. If there is no following
    `<h2>` the section's end cannot be established, so the file is reported and
    left alone rather than truncated at a guess.

  * **Exact phrase swap** — a hand-checked table of literal old/new strings,
    below. The new text only ever removes a place claim; it never adds a claim,
    a price, a promise or a phone number. If the old string is not present
    byte-for-byte the swap is reported as not-applicable and skipped, so a
    page that has drifted is never silently mangled.

Anything else it finds — an out-of-area name loose in a paragraph with no
matching rule — is reported as needing a human and left alone. After a repair
the page is re-scanned and any surviving name is printed, so a partial repair
cannot be mistaken for a clean one.

Whether a town is out of area is Eric's call, not this script's. The point is
only that the site, the schema and the Business Profile should tell one story.
"""

import argparse
import html
import os
import re
import shutil
import sys

# A copy of growth.techniques.OUT_OF_AREA as of 2026-10-03, deliberately
# duplicated rather than imported, for the same reason retire_out_of_area.py
# duplicates it: the droplet's growth/ package is older than the repo's, so
# importing the filter from there would get the stale list — the very list
# that let this copy through. Re-sync by hand if OUT_OF_AREA changes.
OUT_OF_AREA = (
    "perkasie", "yorkville", "york sc", "york ne", "york me", "york maine",
    "york uk", "yorktown", "new york", "akron", "myerstown", "newmanstown",
    "essington", "crum lynne", "york springs",
)

# "Somewhere County" where somewhere is not York. Matched case-sensitively
# against the original text: lowering first would make "the county" match.
OFF_AREA_COUNTY = re.compile(r"\b([A-Z][a-z]+)\s+County\b")

H2 = re.compile(r"[ \t]*<h2\b[^>]*>(.*?)</h2>", re.S | re.I)

PAGE_DIRS = ("areas", "guides", "services")

BACKUP_SUFFIX = ".outofarea-bak"

# Literal one-sentence swaps, each checked by hand against the live file.
# Keyed by the page's path relative to the docroot, with forward slashes.
#
# The gutter-guards lead is the page's answer-first opening paragraph (it sits
# under a `<!-- geo:answer-first -->` marker that `geo_answer_first_content_pass`
# looks for), so it is rewritten rather than cut: deleting it would strip the
# page's direct answer to get rid of two place names. The replacement names
# the real towns the rest of the site names, keeps the sentence doing its job,
# and leaves the remainder of the paragraph — including the phone number —
# untouched.
PHRASES = (
    (
        "services/gutter-guards.html",
        "NEMO Seamless Gutter installs gutter guards on homes in Akron, PA "
        "and the surrounding Lancaster and York County area.",
        "NEMO Seamless Gutter installs gutter guards on homes in York, Dover, "
        "Dallastown, Red Lion, Spring Grove, Hanover and across York County, PA.",
    ),
)


def _visible_text(markup):
    """The page's human-readable text: tags, scripts and styles stripped.

    Scripts go first and for a reason — the JSON-LD block carries
    "York County, Pennsylvania" as `areaServed` on every page, so leaving it in
    would make the county check fire on pages that are perfectly fine.
    """
    body = re.sub(r"<script.*?</script>", " ", markup, flags=re.S | re.I)
    body = re.sub(r"<style.*?</style>", " ", body, flags=re.S | re.I)
    return html.unescape(re.sub(r"<[^>]+>", " ", body))


def off_area_name(text):
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


def find_sections(markup):
    """[(start, end, heading text, offending name)] for off-area <h2> sections.

    `end` is the start of the following <h2>, so the slice covers the heading
    and everything under it. A trailing off-area section — one with no <h2>
    after it — has no establishable end and is returned with `end` None; the
    caller reports it and leaves the file alone rather than cutting to EOF,
    which would take the page's closing markup with it.
    """
    heads = list(H2.finditer(markup))
    out = []
    for i, m in enumerate(heads):
        text = html.unescape(re.sub(r"<[^>]+>", " ", m.group(1))).strip()
        bad = off_area_name(text)
        if not bad:
            continue
        end = heads[i + 1].start() if i + 1 < len(heads) else None
        out.append((m.start(), end, text, bad))
    return out


def repair_markup(rel, markup):
    """(new markup, [what changed], [what could not be done automatically]).

    Sections are cut back-to-front so earlier offsets stay valid.
    """
    changed, blocked = [], []

    sections = find_sections(markup)
    for start, end, head, bad in reversed(sections):
        if end is None:
            blocked.append(
                "last <h2> on the page names %r (%r) and has no following "
                "<h2>, so its end cannot be established — cut it by hand"
                % (bad, head))
            continue
        markup = markup[:start] + markup[end:]
        changed.append("cut section %r (names %r)" % (head, bad))

    for path, old, new in PHRASES:
        if path != rel:
            continue
        if old not in markup:
            blocked.append(
                "the expected phrase for this page is not present "
                "byte-for-byte — the copy has changed, so the swap was "
                "skipped; re-check PHRASES against the live file")
            continue
        markup = markup.replace(old, new)
        changed.append("rewrote the lead sentence naming %r"
                       % off_area_name(old))

    return markup, changed, blocked


def scan(root):
    """[(rel, markup, new markup, changed, blocked, leftover)] for pages at issue."""
    found = []
    for d in PAGE_DIRS:
        full = os.path.join(root, d)
        if not os.path.isdir(full):
            continue
        for name in sorted(os.listdir(full)):
            if not name.endswith(".html"):
                continue
            rel = "%s/%s" % (d, name)
            try:
                with open(os.path.join(full, name), encoding="utf-8") as fh:
                    markup = fh.read()
            except OSError as e:
                print("  ! could not read %s: %s" % (rel, e), file=sys.stderr)
                continue
            if not off_area_name(_visible_text(markup)):
                continue
            new, changed, blocked = repair_markup(rel, markup)
            leftover = off_area_name(_visible_text(new))
            found.append((rel, markup, new, changed, blocked, leftover))
    return found


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=".",
                    help="site docroot (default: current directory)")
    ap.add_argument("--apply", action="store_true",
                    help="actually rewrite; without it, nothing is written")
    args = ap.parse_args(argv)
    root = os.path.abspath(args.root)

    print("Scanning %s" % root)
    found = scan(root)
    if not found:
        print("\nNo page names a town NEMO does not serve. Nothing to do.")
        return 0

    repairable = [f for f in found if f[3]]
    for rel, _old, _new, changed, blocked, leftover in found:
        print("\n%s" % rel)
        for c in changed:
            print("  - %s" % c)
        for b in blocked:
            print("  ! %s" % b)
        if changed and leftover:
            print("  ! %r would still be named after the repairs above — "
                  "this page needs a human" % leftover)
        if not changed and not blocked:
            print("  ! names %r and no rule here matches. A page whose slug "
                  "is the out-of-area town belongs to retire_out_of_area.py;"
                  "\n    anything else needs a human." % leftover)

    if not repairable:
        print("\nNothing this script can repair automatically.")
        return 0
    if not args.apply:
        print("\nReport only. Re-run with --apply to make the changes above."
              "\nEvery file rewritten is copied to <name>%s first."
              % BACKUP_SUFFIX)
        return 0

    print("\nApplying:")
    for rel, _old, new, changed, _blocked, _leftover in repairable:
        path = os.path.join(root, rel)
        shutil.copy2(path, path + BACKUP_SUFFIX)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(new)
        print("  - %s (%d change(s), backed up)" % (rel, len(changed)))
    print("\nDone. Deploy growth/ as well, or the generation-time guards that"
          "\nstop the next such block stay undeployed and this comes back.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

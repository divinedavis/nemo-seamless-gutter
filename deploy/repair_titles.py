#!/usr/bin/env python3
"""Refit live <title> tags to the length Google will actually show.

Why this exists, and why it is here rather than in growth/
---------------------------------------------------------
`growth/techniques.py` sets `TITLE_MAX = 65` and runs every generated title
through `_page_title()`, which strips a brand the model already appended and
then fits the suffix to what is left: the full name, else " | NEMO", else
nothing. That is the correct behaviour and it is in git.

It is not on the droplet. Nothing under `growth/` has been deployed since early
August, so 25 of the 45 live pages shipped between 66 and 80 characters — from
generators that appended " | NEMO Seamless Gutter" to a model title with no
limit at all, while `improve_ctr` next door refused exactly that length. Two
of those pages carry the brand twice:

    Commercial Gutter Installation York PA | NEMO Seamless | NEMO Seamless Gutter

Deploying `growth/` fixes the *next* page written. It does not touch the 25
already on disk, and `growth/publish_state.sh` rsyncs `areas/`, `guides/` and
`services/` **docroot -> repo** each morning, so the repo's copies are a
read-only mirror and editing them there would be overwritten by the next run.
The only place the change can land is the docroot. Hence a script that runs
there, against the live files, importing nothing from the growth package.

This spends nothing. `improve_ctr` would rewrite these snippets, but it needs
`llm.call_json`, so it does nothing on a morning with an empty API balance —
which has been every morning since 2026-10-09. Counting characters needs no
model.

Usage, on the droplet
---------------------
    cd /var/www/nemo-seamless-gutter
    python3 deploy/repair_titles.py            # report only, writes nothing
    python3 deploy/repair_titles.py --apply    # refit + back up

Safe to re-run: the fit is idempotent, so a second run reports nothing to do.
Every file rewritten is copied to `<name>.title-bak` first.

What it deliberately will NOT do
--------------------------------
It only rewrites the `<title>` element. It does not touch `og:title` (Google
does not truncate that, and it is built from the `<h1>` with an em dash, so
"fixing" it would just desynchronise it from the heading), the `<h1>` itself,
or the meta description — a short title and a long description are separate
problems and the description limit is 165, not 65.

It will not touch a title that is not broken. "Broken" means one of exactly
two things: longer than `TITLE_MAX`, or carrying the brand more than once. A
title that already fits is left byte-for-byte alone even where the refit would
return something different — see `needs_repair`.

It will not shorten a title by editing the words. The only lever it pulls is
the brand suffix, exactly as `_page_title()` does: full name, then " | NEMO",
then none. If the search phrase alone is still over the limit the title is
reported as needing a human and left alone, because deciding which words of
"Does Homeowners Insurance Cover Gutter Damage?" to drop is an editorial
judgement, not a character count.

It is a CTR change, not a rank change. Google rewrites titles when it feels
like it, and a snippet that fits is worth something only against the site's
current site-wide CTR of roughly 0.2%. Do not expect positions to move.
"""

import argparse
import html
import os
import re
import shutil
import sys

# Copies of growth.techniques.{TITLE_MAX, BRAND, BRAND_SHORT, _TRAILING_BRAND}
# as of 2026-10-12, deliberately duplicated rather than imported, for the same
# reason retire_out_of_area.py duplicates OUT_OF_AREA: the droplet's growth/
# package is older than the repo's, so importing from there would get the stale
# code — the very code that wrote these titles. Re-sync by hand if they change.
TITLE_MAX = 65
BRAND = "NEMO Seamless Gutter"
BRAND_SHORT = "NEMO"
_TRAILING_BRAND = re.compile(
    r"\s*[|–—-]\s*NEMO(?:\s+Seamless(?:\s+Gutter)?)?\s*$", re.I)

TITLE = re.compile(r"(<title>)(.*?)(</title>)", re.S | re.I)
H1 = re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.S | re.I)

PAGE_DIRS = ("areas", "guides", "services")

BACKUP_SUFFIX = ".title-bak"


def _text(markup):
    """Tags stripped, entities resolved, whitespace collapsed.

    Length has to be measured on what a searcher sees: the live titles hold
    `&amp;`, which is five characters of markup and one of title.
    """
    flat = re.sub(r"<[^>]+>", "", str(markup or ""))
    return " ".join(html.unescape(flat).split())


def strip_brand(text):
    """`text` with every trailing brand suffix removed.

    `_TRAILING_BRAND` is anchored at the end, so one `sub()` removes one
    suffix. That is enough at generation time, where the input is the model's
    title and the code has not appended anything yet. It is not enough here:
    this script reads titles the old generator already appended to, so
    "… | NEMO Seamless | NEMO Seamless Gutter" needs two passes or it keeps a
    brand and then gets a third one bolted on. Loop until it stops changing.
    """
    out = str(text or "").strip()
    while True:
        stripped = _TRAILING_BRAND.sub("", out).strip(" |-–—")
        if stripped == out:
            break
        out = stripped
    # A title that is nothing but the brand survives the regex untouched (it
    # needs a separator in front of the name) and would take a suffix on top
    # of itself.
    return "" if out.upper() in (BRAND.upper(), BRAND_SHORT.upper()) else out


def fit_title(raw, fallback=""):
    """The refitted title, or None when the phrase alone is already over.

    Mirrors growth.techniques._page_title with one deliberate difference: that
    function truncates an over-long phrase on a word boundary, because at
    generation time something has to ship. Here there is already a live title
    doing its job, and silently deleting the end of a human-readable sentence
    is worse than leaving it long, so this returns None and the caller reports
    it for a human instead.
    """
    head = strip_brand(raw) or strip_brand(fallback)
    if not head:
        return None
    for suffix in (" | %s" % BRAND, " | %s" % BRAND_SHORT, ""):
        if len(head) + len(suffix) <= TITLE_MAX:
            return head + suffix
    return None


def read_title(markup):
    """(match, current title text) for the page's <title>, or (None, None)."""
    m = TITLE.search(markup)
    if not m:
        return None, None
    return m, _text(m.group(2))


def needs_repair(current):
    """Is this title actually broken?

    Two faults, and only these two: it is longer than Google will show, or it
    carries the brand more than once. Everything else is left alone even when
    the refit would return something different — `setup.html` reads "Connect
    your calendar — NEMO Seamless Gutter", which fits at 44 characters and
    which `fit_title` would rewrite to use " | " instead of " — " purely
    because that is the separator the generator happens to use. Churning a
    page that is not broken is how a repair script loses the right to be
    trusted on 45 others.
    """
    return (len(current) > TITLE_MAX
            or current.upper().count(BRAND_SHORT.upper()) > 1)


def repair_markup(markup):
    """(new markup, old title, new title, note).

    `note` is None when something was done, and a sentence when it was not.
    """
    m, current = read_title(markup)
    if m is None:
        return markup, None, None, "no <title> element"
    if not current:
        return markup, current, None, "<title> is empty"
    if not needs_repair(current):
        return markup, current, current, None

    h1 = _text(H1.search(markup).group(1)) if H1.search(markup) else ""
    fitted = fit_title(current, h1)

    if fitted is None:
        return markup, current, None, (
            "the search phrase alone is %d characters with no brand at all — "
            "shortening it means dropping words, which is a human's call"
            % len(strip_brand(current) or current))
    if fitted == current:
        return markup, current, current, None
    new = markup[:m.start(2)] + html.escape(fitted, quote=False) + markup[m.end(2):]
    return new, current, fitted, None


def scan(root):
    """[(rel, markup, new, old title, new title, note)] for every page read."""
    found = []
    names = [n for n in sorted(os.listdir(root))
             if n.endswith(".html")] if os.path.isdir(root) else []
    targets = [(n, n) for n in names]
    for d in PAGE_DIRS:
        full = os.path.join(root, d)
        if not os.path.isdir(full):
            continue
        for name in sorted(os.listdir(full)):
            if name.endswith(".html"):
                targets.append(("%s/%s" % (d, name), os.path.join(d, name)))

    for rel, path in targets:
        try:
            with open(os.path.join(root, path), encoding="utf-8") as fh:
                markup = fh.read()
        except OSError as e:
            print("  ! could not read %s: %s" % (rel, e), file=sys.stderr)
            continue
        new, old, fitted, note = repair_markup(markup)
        found.append((rel, markup, new, old, fitted, note))
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
    changed = [f for f in found if f[2] != f[1]]
    blocked = [f for f in found if f[5]]
    over = [f for f in found if f[3] and len(f[3]) > TITLE_MAX]
    doubled = [f for f in found if f[3]
               and f[3].upper().count(BRAND_SHORT.upper()) > 1]

    print("\n%d page(s) read · %d over %d characters · %d branded twice · "
          "%d refittable · %d need a human"
          % (len(found), len(over), TITLE_MAX, len(doubled),
             len(changed), len(blocked)))

    for rel, _markup, _new, old, fitted, note in found:
        if note:
            print("\n%s\n  ! %s\n    %d: %s" % (rel, note, len(old or ""), old))
        elif fitted != old:
            print("\n%s\n  - %d: %s\n  + %d: %s"
                  % (rel, len(old), old, len(fitted), fitted))

    if not changed:
        print("\nEvery title already fits. Nothing to do.")
        return 0
    if not args.apply:
        print("\nReport only. Re-run with --apply to make the changes above."
              "\nEvery file rewritten is copied to <name>%s first."
              % BACKUP_SUFFIX)
        return 0

    print("\nApplying:")
    for rel, _markup, new, old, fitted, _note in changed:
        path = os.path.join(root, rel)
        shutil.copy2(path, path + BACKUP_SUFFIX)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(new)
        print("  - %s (%d -> %d, backed up)" % (rel, len(old), len(fitted)))
    print("\nDone. Deploy growth/ as well, or the generator that wrote these"
          "\ntitles stays undeployed and the next page written comes back long.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Remove elements whose entire visible text is an unrendered template token.

Why this exists, and why it is here rather than in growth/
---------------------------------------------------------
`areas/seamless-gutters-dover-pa.html` has been serving the literal string

    <p>paragraphs2_placeholder</p>

to the public since 2026-09-07. It sits between two perfectly good paragraphs
on the "Who Installs Gutters in Dover, PA" section of a town page for one of
the six tracked towns. The model returned nothing for that field and the
template rendered its own field name instead of the copy.

The generator bug is fixed in `growth/techniques.py` (commit 797b723, "Stop the
model's own field names being published as page copy"), but that fix only stops
the *next* occurrence, and only once the `growth/` package is deployed — which
has not happened since early August. It does not repair a page already on disk.

Repairing the page in the git repo does not work either. `growth/publish_state.sh`
rsyncs `areas/`, `guides/` and `services/` **docroot -> repo** every morning at
06:05, so the repo's copy of those directories is a read-only mirror of the
droplet and any edit committed here is overwritten the next morning. The only
place a page repair can land is the docroot. Hence a script that runs there,
against the live files, importing nothing from the growth package — the same
shape as `repair_letter_paragraphs.py` and for the same reason.

Usage, on the droplet
---------------------
    cd /var/www/nemo-seamless-gutter
    python3 deploy/repair_placeholder_paragraphs.py            # report only
    python3 deploy/repair_placeholder_paragraphs.py --apply    # repair + back up

Safe to re-run: a repaired page has no template tokens left, so a second run
reports nothing to do. Every file it rewrites is copied to
`<name>.placeholder-bak` first, and it never deletes a file.

What it deliberately will NOT do
--------------------------------
It removes the element; it does not try to invent replacement copy. A
`*_placeholder` token means the model returned nothing for that field, so there
is no content to recover — the honest repair is to close the gap, and the
paragraphs on either side already read as continuous prose without it.

It also will not touch a one-word element that could be real copy. The match is
deliberately narrow: the element's whole text, entities decoded and trimmed,
must contain no whitespace AND either contain "placeholder" or be a bare
snake_case identifier (`[a-z][a-z0-9]*(_[a-z0-9]+)+`). English copy does not
look like that; template field names do. A single ordinary word such as
"Yes" or "Seamless" is left alone.
"""

import argparse
import html
import os
import re
import sys

# The elements a rendered section can put a field name into. Headings and list
# items are here because the same template renders all of them from the same
# model response, so the same miss can land in any of them.
TAGS = ("p", "li", "h2", "h3", "h4")

ELEMENT = re.compile(
    r"[ \t]*<(%s)\b[^>]*>(.*?)</\1>[ \t]*\n?" % "|".join(TAGS), re.S | re.I)

SNAKE_CASE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)+$")

DEFAULT_DIRS = ("areas", "guides", "services")


def _is_template_token(inner):
    """True if this element's whole text is an unrendered template field name."""
    text = html.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
    if not text or re.search(r"\s", text):
        return False
    low = text.lower()
    return "placeholder" in low or bool(SNAKE_CASE.match(low))


def repair_text(src):
    """Return (new_text, [tokens removed])."""
    out = []
    pos = 0
    removed = []
    for m in ELEMENT.finditer(src):
        if not _is_template_token(m.group(2)):
            continue
        out.append(src[pos:m.start()])
        pos = m.end()
        removed.append(html.unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip())
    out.append(src[pos:])
    return "".join(out), removed


def iter_pages(root, dirs):
    for d in dirs:
        full = os.path.join(root, d)
        if not os.path.isdir(full):
            continue
        for name in sorted(os.listdir(full)):
            if name.endswith(".html"):
                yield os.path.join(full, name)
    index = os.path.join(root, "index.html")
    if os.path.isfile(index):
        yield index


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=os.environ.get("WEB_ROOT", "."),
                    help="site docroot (default: $WEB_ROOT, else cwd)")
    ap.add_argument("--apply", action="store_true",
                    help="write the repairs; without it, report only")
    args = ap.parse_args(argv)

    touched = 0
    for path in iter_pages(args.root, DEFAULT_DIRS):
        with open(path, encoding="utf-8") as f:
            src = f.read()
        new, removed = repair_text(src)
        if not removed:
            continue
        touched += 1
        rel = os.path.relpath(path, args.root)
        print("%s: %d unrendered token(s): %s"
              % (rel, len(removed), ", ".join(repr(t) for t in removed)))
        if args.apply:
            bak = path + ".placeholder-bak"
            if not os.path.exists(bak):
                with open(bak, "w", encoding="utf-8") as f:
                    f.write(src)
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(new)
            os.replace(tmp, path)
            print("  repaired (original kept at %s)" % os.path.basename(bak))

    if not touched:
        print("no unrendered template tokens found")
        return 0
    if not args.apply:
        print("\nreport only — re-run with --apply to repair")
    return 0


if __name__ == "__main__":
    sys.exit(main())

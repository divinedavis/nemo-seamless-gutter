#!/usr/bin/env python3
"""Repair pages where one paragraph was published one character per <p>.

Why this exists, and why it is here rather than in growth/
---------------------------------------------------------
On 2026-08-16 `strengthen_pages` asked the model for
`{"paragraphs": ["...", "..."]}` and got a bare string back. `_render_sections`
did `for p in s.get("paragraphs")`, which iterates a string character by
character, and wrote 1,254 single-letter <p> elements into
`services/half-round-gutters.html`. The page has been live in that state since.

The generator bug is fixed in `growth/techniques.py` (`_strlist`, added
2026-08-27), but that fix only stops the *next* occurrence and only once the
`growth/` package is deployed. It does not repair a page already on disk.

Repairing the page in the git repo does not work either, and that was tried on
2026-08-27 and undone the next morning: `growth/publish_state.sh` rsyncs
`areas/`, `guides/` and `services/` **docroot -> repo** every morning at 06:05,
so the repo's copy of those directories is a read-only mirror of the droplet.
The only place a page repair can land is the docroot. Hence a script that runs
there, against the live files, with no dependency on the growth package.

Usage, on the droplet
---------------------
    cd /var/www/nemo-seamless-gutter
    python3 deploy/repair_letter_paragraphs.py            # report only
    python3 deploy/repair_letter_paragraphs.py --apply    # repair + back up

Safe to re-run: a repaired page has no single-character runs left, so a second
run reports nothing to do. Every file it rewrites is copied to
`<name>.repair-bak` first, and it never deletes anything.
"""

import argparse
import html
import os
import re
import sys

# A <p> block, non-greedy, allowed to span lines: the damage encodes a literal
# newline as "<p>\n</p>", so a line-oriented match misses the paragraph breaks
# and would join three paragraphs into one run-on.
P_BLOCK = re.compile(r"[ \t]*<p>(.*?)</p>[ \t]*\n?", re.S)

DEFAULT_DIRS = ("areas", "guides", "services")

# Below this, a run of one-character paragraphs is more likely to be real copy
# (an initial, a stray "A") than the iterate-a-string bug.
MIN_RUN = 8


def _one_char(inner):
    """True if this <p> holds exactly one character once entities are decoded."""
    return len(html.unescape(inner)) == 1


def _rebuild(chars, indent):
    """Turn the characters of a shredded paragraph back into <p> elements.

    The original string carried its own paragraph breaks as newlines, which the
    bug preserved as one-character <p> blocks. Splitting on blank lines recovers
    the paragraphs the model actually wrote; nothing else about the text is
    touched.
    """
    text = "".join(chars)
    parts = [p.strip() for p in re.split(r"\n\s*\n", text)]
    parts = [p for p in parts if p]
    if not parts:  # whitespace only — drop the run rather than emit empty tags
        return ""
    return "".join(f"{indent}<p>{html.escape(p, quote=False)}</p>\n" for p in parts)


def repair_text(src):
    """Return (new_text, runs_repaired, chars_recovered)."""
    out = []
    pos = 0
    runs = chars_total = 0

    blocks = list(P_BLOCK.finditer(src))
    i = 0
    while i < len(blocks):
        if not _one_char(blocks[i].group(1)):
            i += 1
            continue
        j = i
        while j < len(blocks) and _one_char(blocks[j].group(1)):
            # Only extend across blocks that are genuinely adjacent; a run that
            # stops at a heading has ended, even if a stray <p>A</p> follows it.
            if j > i and src[blocks[j - 1].end():blocks[j].start()].strip():
                break
            j += 1
        run = blocks[i:j]
        if len(run) < MIN_RUN:
            i = j
            continue

        indent = re.match(r"[ \t]*", run[0].group(0)).group(0)
        out.append(src[pos:run[0].start()])
        out.append(_rebuild([html.unescape(b.group(1)) for b in run], indent))
        pos = run[-1].end()
        runs += 1
        chars_total += len(run)
        i = j

    out.append(src[pos:])
    return "".join(out), runs, chars_total


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
        new, runs, chars = repair_text(src)
        if not runs:
            continue
        touched += 1
        rel = os.path.relpath(path, args.root)
        before = src.count("\n") + 1
        after = new.count("\n") + 1
        print(f"{rel}: {runs} shredded paragraph(s), {chars} single-character "
              f"<p> elements, {before} -> {after} lines")
        if args.apply:
            bak = path + ".repair-bak"
            if not os.path.exists(bak):
                with open(bak, "w", encoding="utf-8") as f:
                    f.write(src)
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(new)
            os.replace(tmp, path)
            print(f"  repaired (original kept at {os.path.basename(bak)})")

    if not touched:
        print("no shredded paragraphs found")
        return 0
    if not args.apply:
        print("\nreport only — re-run with --apply to repair")
    return 0


if __name__ == "__main__":
    sys.exit(main())

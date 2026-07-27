#!/usr/bin/env python3
"""Merge the droplet's local JOURNAL.md into the GitHub clone without losing
entries that only exist on GitHub.

Why this exists: the engine (growth_daily.py, via snapshot.append_journal)
appends its own entry to the docroot's local copy of this file. The daily
review agent runs in the cloud and appends its entry with a direct commit to
GitHub — it never touches the docroot. Those are two different files that
diverge every day. publish_state.sh used to `cp` the docroot's copy straight
over the clone's, which silently deleted every review-agent entry the moment
the next day's publish ran (confirmed: commit 93ff2a222 erased the entry added
in 75cd2d917 within six hours). This script takes the clone's current content
(the trusted full history) and appends only the entries from the docroot's
copy that aren't already present, so neither side's entries are lost.

Usage: merge_journal.py <clone_journal> <docroot_journal> > merged_output
"""
import re
import sys

ENTRY_RE = re.compile(r"^## ", re.M)


def split_entries(text):
    """(preamble, [entry_text, ...]) — an entry starts at each '## ' heading
    line and runs to the next one (or EOF)."""
    starts = [m.start() for m in ENTRY_RE.finditer(text)]
    if not starts:
        return text, []
    preamble = text[:starts[0]]
    entries = []
    for i, s in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(text)
        entries.append(text[s:end].rstrip("\n"))
    return preamble, entries


def merge(clone_text, docroot_text):
    preamble, clone_entries = split_entries(clone_text)
    _, docroot_entries = split_entries(docroot_text)
    have = set(clone_entries)
    new = [e for e in docroot_entries if e not in have]
    out = preamble.rstrip("\n") + "\n"
    for e in clone_entries + new:
        out += "\n" + e.rstrip("\n") + "\n"
    return out


def main():
    clone_path, docroot_path = sys.argv[1], sys.argv[2]
    clone_text = open(clone_path).read() if _exists(clone_path) else ""
    docroot_text = open(docroot_path).read()
    sys.stdout.write(merge(clone_text, docroot_text))


def _exists(path):
    import os
    return os.path.exists(path)


if __name__ == "__main__":
    main()

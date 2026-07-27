#!/usr/bin/env bash
# Publish growth state to GitHub so the daily cloud review agent can read it.
#
# The growth engine runs here on the droplet; the agent that reviews its work
# runs in Anthropic's cloud and cannot reach this machine. The git repository is
# the bridge — this pushes the metrics snapshot, the journal, and any pages the
# engine generated overnight.
#
# The docroot is deliberately NOT a git repository. It holds .env files, the
# bookings database, and server-only auto-published guides; a stray `git reset`
# or `git clean` in there would be destructive. Instead this keeps a separate
# clone and copies specific paths into it. Nothing here ever writes back into
# the docroot.
#
# Runs from /etc/cron.d/nemo-growth right after the 06:00 engine run.
set -euo pipefail

DOCROOT="${WEB_ROOT:-/var/www/nemo-seamless-gutter}"
CLONE="${NEMO_CLONE:-/root/nemo-repo}"
REMOTE="github-nemo:divinedavis/nemo-seamless-gutter.git"
BRANCH=main

if [ ! -d "$CLONE/.git" ]; then
  echo "publish: cloning $REMOTE -> $CLONE"
  git clone --quiet --branch "$BRANCH" "$REMOTE" "$CLONE"
fi

cd "$CLONE"
git config user.email "growth@nemoseamlessgutter.com"
git config user.name "NEMO growth engine"

# Discard any local drift and take the remote as truth. Safe here precisely
# because this clone is a publishing staging area and never a source of record —
# everything it publishes is re-copied from the docroot on the next line.
git fetch --quiet origin "$BRANCH"
git reset --quiet --hard "origin/$BRANCH"

copy() {  # copy <relative path> if it exists in the docroot
  if [ -e "$DOCROOT/$1" ]; then
    mkdir -p "$(dirname "$CLONE/$1")"
    cp -a "$DOCROOT/$1" "$CLONE/$1"
  fi
}

copy growth/snapshot.json
copy sitemap.xml
copy index.html

# JOURNAL.md is NOT a plain copy like the files above. The docroot's local
# copy only ever grows with this engine's own entries — the cloud review
# agent commits its entries straight to GitHub and never touches this
# machine, so the two files diverge every day. A blind copy here overwrites
# the clone (and then the remote) with the docroot's version and silently
# deletes every review-agent entry since the last publish. Merge instead: keep
# the clone's current content (the trusted full history) and append only the
# docroot entries not already present in it.
if [ -e "$DOCROOT/growth/JOURNAL.md" ]; then
  mkdir -p "$CLONE/growth"
  python3 "$DOCROOT/growth/merge_journal.py" \
    "$CLONE/growth/JOURNAL.md" "$DOCROOT/growth/JOURNAL.md" \
    > "$CLONE/growth/JOURNAL.md.tmp"
  mv "$CLONE/growth/JOURNAL.md.tmp" "$CLONE/growth/JOURNAL.md"
fi

# Pages the engine wrote overnight. rsync rather than cp so a directory that
# gained a file is picked up, and --exclude keeps the engine's backup copies
# of hand-built pages out of the repo.
for dir in areas guides services; do
  if [ -d "$DOCROOT/$dir" ]; then
    mkdir -p "$CLONE/$dir"
    rsync -a --exclude='*.growth-bak' --exclude='*.tmp' \
      "$DOCROOT/$dir/" "$CLONE/$dir/"
  fi
done

if git diff --quiet && git diff --cached --quiet && [ -z "$(git status --porcelain)" ]; then
  echo "publish: nothing changed"
  exit 0
fi

git add -A
CHANGED=$(git diff --cached --name-only | wc -l | tr -d ' ')
git commit --quiet -m "Publish growth state for $(date +%Y-%m-%d)

Metrics snapshot, journal, and any pages the engine generated this morning.
Pushed by the droplet so the daily review agent, which runs in the cloud with
no access to this machine, has something to review.

$CHANGED file(s) changed.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
git push --quiet origin "$BRANCH"
echo "publish: pushed $CHANGED file(s)"

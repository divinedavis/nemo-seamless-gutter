#!/usr/bin/env bash
# Ship the static site (pages, CSS/JS, assets) to the nemoseamlessgutter.com
# docroot — committed files only, and never over a page the droplet changed.
#
#   scripts/deploy_web.sh               # test -> drift check -> snapshot -> copy -> verify
#   scripts/deploy_web.sh --dry-run     # everything up to the copy; prints the plan
#   scripts/deploy_web.sh --skip-tests  # only when you know why
#
# WHY IT IS SHAPED LIKE THIS
#
# The docroot (/var/www/nemo-seamless-gutter) is not a git checkout, and the
# 6am growth engine and the monthly SEO cron WRITE pages there (areas/,
# guides/, services/, index.html, sitemap.xml), then growth/publish_state.sh
# pushes them back to GitHub. Between those two moments the docroot is AHEAD
# of the repo, and a plain rsync of the repo would silently revert the
# engine's work (it nearly did on 2026-07-28). So, per file:
#   - live identical to HEAD            -> skipped;
#   - live absent                       -> shipped (new file);
#   - live equals some committed version of that path -> shipped (live is
#     merely older than the repo);
#   - live content was NEVER committed  -> the deploy STOPS and lists it.
#     Pull the live copy down (scp/rsync) and commit it, or let the next
#     publish_state.sh run do it, then deploy again.
# Only what is committed at HEAD ships (git archive), so another session's
# uncommitted edits can't ride along. Nothing is ever deleted from the docroot.
#
# Gates: scripts/test.sh first; the files about to be replaced are snapshotted
# to $BACKUPS/<timestamp> on the box (15 kept); after the copy, live content
# checks run (homepage text, booking widget, booking API answering a
# deliberately invalid booking with a 400 — nothing is ever created — and the
# private paths still 404). Any failure restores the snapshot via
# scripts/rollback.sh and exits 1.
#
# Engine code (growth/*.py) has its own path: deploy/deploy_growth.sh. The
# booking API (server/) has scripts/deploy_api.sh.
set -euo pipefail
cd "$(dirname "$0")/.."
HOST=${NEMO_HOST:-root@104.236.120.144}
DOC=${NEMO_DOC:-/var/www/nemo-seamless-gutter}
BACKUPS=/var/backups/nemo-web
DRY=0; SKIP=0
for a in "$@"; do
  case "$a" in
    --dry-run) DRY=1 ;;
    --skip-tests) SKIP=1 ;;
    *) echo "unknown argument: $a" >&2; exit 2 ;;
  esac
done

# Everything this script may ship: the committed files at these paths.
SHIP_PATHS=(index.html privacy.html setup.html styles.css script.js analytics.js
  booking.css booking.js robots.txt sitemap.xml site.webmanifest favicon.ico
  9c4b009616d21c1ca44569b51cc49b60.txt assets areas services guides)

if [ "$SKIP" = 0 ]; then
  echo "== tests"
  scripts/test.sh >/dev/null 2>&1 || { echo "!! scripts/test.sh failed — nothing deployed" >&2; exit 1; }
  echo "   passed"
fi

dirty=$(git status --porcelain -- "${SHIP_PATHS[@]}")
if [ -n "$dirty" ]; then
  echo "note: uncommitted changes under the shipped paths are NOT deployed (HEAD only):"
  echo "$dirty" | sed 's/^/   /'
fi

FILES=$(git ls-files -- "${SHIP_PATHS[@]}")

echo "== comparing HEAD with live"
# Git blob ids of the live files, computed on the box the way git does.
LIVE=$(printf '%s\n' $FILES | ssh "$HOST" "cd $DOC && python3 -c '
import hashlib, os, sys
for p in sys.stdin.read().split():
    if os.path.isfile(p):
        d = open(p, \"rb\").read()
        print(hashlib.sha1(b\"blob %d\\0\" % len(d) + d).hexdigest(), p)
    else:
        print(\"absent\", p)
'")
# Every blob id these paths have ever had in this repo's history.
KNOWN=$(git log --all --raw --no-abbrev --format= -- "${SHIP_PATHS[@]}" | awk '{print $3; print $4}' | sort -u)

CHANGED=(); DRIFT=()
while read -r live_id path; do
  head_id=$(git rev-parse "HEAD:$path")
  if [ "$live_id" = "$head_id" ]; then continue; fi
  if [ "$live_id" = absent ] || grep -qx "$live_id" <<<"$KNOWN"; then
    CHANGED+=("$path")
  else
    DRIFT+=("$path")
  fi
done <<<"$LIVE"

if [ ${#DRIFT[@]} -gt 0 ]; then
  echo "!! live has content that was never committed — refusing to overwrite:" >&2
  printf '   %s\n' "${DRIFT[@]}" >&2
  echo "   Pull it down first:  scp $HOST:$DOC/<file> <file>  (then commit), or wait for growth/publish_state.sh." >&2
  exit 1
fi
if [ ${#CHANGED[@]} -eq 0 ]; then
  echo "   live already matches HEAD for all $(wc -w <<<"$FILES" | tr -d ' ') shipped files — nothing to deploy"
  exit 0
fi
echo "   ${#CHANGED[@]} file(s) to ship:"
printf '     %s\n' "${CHANGED[@]}"
[ "$DRY" = 1 ] && { echo "== dry run: stopping before the snapshot"; exit 0; }

# The engine rewrites pages at 06:00 ET and the SEO cron at 03:00/06:00;
# copying in the middle of a run races it.
if ssh "$HOST" "pgrep -f '[g]rowth_daily\.py|seo/[g]en_article\.py|seo/[g]en_sitemap\.py' >/dev/null"; then
  echo "!! the growth engine or SEO cron is running on the box — try again when it finishes" >&2
  exit 1
fi

SNAP=$(date -u +%Y%m%dT%H%M%SZ)
echo "== snapshotting live to $BACKUPS/$SNAP"
printf '%s\n' "${CHANGED[@]}" | ssh "$HOST" "set -e; mkdir -p $BACKUPS/$SNAP; cd $DOC
  : > $BACKUPS/$SNAP/.new-files
  while read -r f; do
    if [ -e \"\$f\" ]; then cp -a --parents \"\$f\" $BACKUPS/$SNAP/; else echo \"\$f\" >> $BACKUPS/$SNAP/.new-files; fi
  done
  ls -1d $BACKUPS/*/ | head -n -15 | xargs -r rm -rf"
echo "   (undo by hand: scripts/rollback.sh web $SNAP)"

echo "== copying"
if ! git archive --format=tar HEAD -- "${CHANGED[@]}" |
  ssh "$HOST" "set -e; cd $DOC && tar -x --no-same-owner -f - && chown root:root ${CHANGED[*]} && chmod 644 ${CHANGED[*]}"; then
  echo "!! copy failed — restoring $SNAP" >&2
  scripts/rollback.sh web "$SNAP"
  exit 1
fi

echo "== verifying live"
if ! scripts/check_live.sh web "${CHANGED[@]}"; then
  echo "!! live checks failed — restoring $SNAP" >&2
  scripts/rollback.sh web "$SNAP"
  exit 1
fi
echo "== done ($SNAP)"

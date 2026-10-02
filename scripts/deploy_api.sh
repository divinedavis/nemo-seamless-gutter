#!/usr/bin/env bash
# Ship the booking API (server/*.js, server/jobs/*.js, package*.json) to the
# droplet and restart it — with a snapshot, live checks and automatic restore.
#
#   scripts/deploy_api.sh               # test -> drift check -> snapshot -> copy -> restart -> verify
#   scripts/deploy_api.sh --dry-run     # everything up to the snapshot; prints the plan
#   scripts/deploy_api.sh --skip-tests  # only when you know why
#
# Runs as systemd unit nemo-seamless-gutter, user nemo (since 2026-09-26),
# from /var/www/nemo-seamless-gutter/server. Never touched here: server/.env,
# bookings.sqlite* (live customer bookings), node_modules unless
# package-lock.json changed (then `npm ci --omit=dev` on the box, and the old
# node_modules goes into the snapshot so a rollback can put it back).
#
# Like deploy_web.sh: committed files only (git archive HEAD); a live file
# whose content was never committed stops the deploy instead of being
# overwritten; the files about to change are snapshotted to
# /var/backups/nemo-api/<UTC timestamp> (15 kept); after the restart
# scripts/check_live.sh api must pass (unit active, /api/health,
# /api/services, an invalid booking answered with a 400 — nothing stored or
# emailed) or scripts/rollback.sh api <snapshot> restores and this exits 1.
set -euo pipefail
cd "$(dirname "$0")/.."
HOST=${NEMO_HOST:-root@104.236.120.144}
DOC=${NEMO_DOC:-/var/www/nemo-seamless-gutter}
BACKUPS=/var/backups/nemo-api
DRY=0; SKIP=0
for a in "$@"; do
  case "$a" in
    --dry-run) DRY=1 ;;
    --skip-tests) SKIP=1 ;;
    *) echo "unknown argument: $a" >&2; exit 2 ;;
  esac
done
# :(glob) so * stops at /, keeping server/test/ off the box.
SHIP_PATHS=(':(glob)server/*.js' ':(glob)server/jobs/*.js' server/package.json server/package-lock.json)

if [ "$SKIP" = 0 ]; then
  echo "== tests"
  scripts/test.sh >/dev/null 2>&1 || { echo "!! scripts/test.sh failed — nothing deployed" >&2; exit 1; }
  echo "   passed"
fi
dirty=$(git status --porcelain -- "${SHIP_PATHS[@]}")
[ -n "$dirty" ] && { echo "note: uncommitted changes are NOT deployed (HEAD only):"; echo "$dirty" | sed 's/^/   /'; }

FILES=$(git ls-files -- "${SHIP_PATHS[@]}")
echo "== comparing HEAD with live"
LIVE=$(printf '%s\n' $FILES | ssh "$HOST" "cd $DOC && python3 -c '
import hashlib, os, sys
for p in sys.stdin.read().split():
    if os.path.isfile(p):
        d = open(p, \"rb\").read()
        print(hashlib.sha1(b\"blob %d\\0\" % len(d) + d).hexdigest(), p)
    else:
        print(\"absent\", p)
'")
KNOWN=$(git log --all --raw --no-abbrev --format= -- "${SHIP_PATHS[@]}" | awk '{print $3; print $4}' | sort -u)
CHANGED=(); DRIFT=()
while read -r live_id path; do
  [ "$live_id" = "$(git rev-parse "HEAD:$path")" ] && continue
  if [ "$live_id" = absent ] || grep -qx "$live_id" <<<"$KNOWN"; then CHANGED+=("$path"); else DRIFT+=("$path"); fi
done <<<"$LIVE"
if [ ${#DRIFT[@]} -gt 0 ]; then
  echo "!! live has server code that was never committed — refusing to overwrite:" >&2
  printf '   %s\n' "${DRIFT[@]}" >&2
  exit 1
fi
if [ ${#CHANGED[@]} -eq 0 ]; then
  echo "   live already matches HEAD for all $(wc -w <<<"$FILES" | tr -d ' ') API files — nothing to deploy"
  exit 0
fi
echo "   ${#CHANGED[@]} file(s) to ship:"; printf '     %s\n' "${CHANGED[@]}"
DEPS=0; printf '%s\n' "${CHANGED[@]}" | grep -qx 'server/package-lock.json' && DEPS=1
[ "$DEPS" = 1 ] && echo "   package-lock.json changed: npm ci on the box, old node_modules snapshotted"
[ "$DRY" = 1 ] && { echo "== dry run: stopping before the snapshot"; exit 0; }

SNAP=$(date -u +%Y%m%dT%H%M%SZ)
echo "== snapshotting live to $BACKUPS/$SNAP"
printf '%s\n' "${CHANGED[@]}" | ssh "$HOST" "set -e; mkdir -p $BACKUPS/$SNAP; cd $DOC
  : > $BACKUPS/$SNAP/.new-files
  while read -r f; do
    if [ -e \"\$f\" ]; then cp -a --parents \"\$f\" $BACKUPS/$SNAP/; else echo \"\$f\" >> $BACKUPS/$SNAP/.new-files; fi
  done
  [ $DEPS = 1 ] && cp -a --parents server/node_modules $BACKUPS/$SNAP/
  ls -1d $BACKUPS/*/ | head -n -15 | xargs -r rm -rf"
echo "   (undo by hand: scripts/rollback.sh api $SNAP)"

echo "== copying + restarting"
if ! git archive --format=tar HEAD -- "${CHANGED[@]}" |
  ssh "$HOST" "set -e; cd $DOC && tar -x --no-same-owner -f -
  cd server
  [ $DEPS = 1 ] && npm ci --omit=dev --no-audit --no-fund
  find . -name 'bookings.sqlite*' -prune -o -exec chown root:root {} + -exec chmod go-w {} +
  chown root:nemo . && chmod 1770 .
  chown root:nemo .env && chmod 0640 .env
  systemctl restart nemo-seamless-gutter"; then
  echo "!! copy/install/restart failed — restoring $SNAP" >&2
  scripts/rollback.sh api "$SNAP"
  exit 1
fi
sleep 3

echo "== verifying live"
if ! scripts/check_live.sh api; then
  echo "!! live checks failed — restoring $SNAP" >&2
  scripts/rollback.sh api "$SNAP"
  exit 1
fi
echo "== done ($SNAP)"

#!/usr/bin/env bash
# Put live back the way a deploy snapshot found it.
#
#   scripts/rollback.sh web                    # list static-site snapshots, newest last
#   scripts/rollback.sh api                    # list booking-API snapshots
#   scripts/rollback.sh web 20261001T1830Z     # restore one
#   scripts/rollback.sh web --snapshot-only    # take a snapshot of every shipped file, change nothing
#
# deploy_web.sh / deploy_api.sh snapshot exactly the files they are about to
# replace (to /var/backups/nemo-web|nemo-api/<UTC timestamp>, 15 kept) and call
# this on their own when the post-deploy checks fail. A restore copies the
# snapshot's files back with their original owner/mode/mtime (cp -a), deletes
# files the deploy added (.new-files), and for the API re-applies the
# root:nemo ownership and restarts the unit (and puts node_modules back if the
# deploy changed dependencies). Then it runs scripts/check_live.sh.
set -euo pipefail
cd "$(dirname "$0")/.."
HOST=${NEMO_HOST:-root@104.236.120.144}
DOC=/var/www/nemo-seamless-gutter
KIND=${1:-}
SNAP=${2:-}
case "$KIND" in
  web) BACKUPS=/var/backups/nemo-web ;;
  api) BACKUPS=/var/backups/nemo-api ;;
  *) echo "usage: scripts/rollback.sh web|api [SNAPSHOT|--snapshot-only]" >&2; exit 2 ;;
esac

if [ -z "$SNAP" ]; then
  ssh "$HOST" "ls -1 $BACKUPS 2>/dev/null || echo '(no snapshots yet)'"
  exit 0
fi

if [ "$SNAP" = --snapshot-only ]; then
  # Same snapshot a deploy would take, of every file it could ship. Used to
  # prove a snapshot -> restore round trip leaves live byte-identical.
  if [ "$KIND" = web ]; then
    FILES=$(git ls-files -- index.html privacy.html setup.html styles.css script.js analytics.js \
      booking.css booking.js robots.txt sitemap.xml site.webmanifest favicon.ico \
      9c4b009616d21c1ca44569b51cc49b60.txt assets areas services guides)
  else
    FILES=$(git ls-files -- ':(glob)server/*.js' ':(glob)server/jobs/*.js' server/package.json server/package-lock.json)
  fi
  SNAP=$(date -u +%Y%m%dT%H%M%SZ)
  printf '%s\n' $FILES | ssh "$HOST" "set -e; mkdir -p $BACKUPS/$SNAP; cd $DOC; : > $BACKUPS/$SNAP/.new-files
    while read -r f; do [ -e \"\$f\" ] && cp -a --parents \"\$f\" $BACKUPS/$SNAP/; done
    ls -1d $BACKUPS/*/ | head -n -15 | xargs -r rm -rf
    echo \"$BACKUPS/$SNAP: \$(find $BACKUPS/$SNAP -type f ! -name .new-files | wc -l) files\""
  exit 0
fi

echo "== restoring $KIND snapshot $SNAP"
ssh "$HOST" "set -e; S=$BACKUPS/$SNAP; test -d \$S
  cd \$S
  find . -type f ! -name .new-files ! -path './server/node_modules/*' -printf '%P\n' | while read -r f; do
    cmp -s \"\$f\" \"$DOC/\$f\" || echo \"   restored \$f\"
    cp -a --parents \"\$f\" $DOC/
  done
  while read -r f; do [ -n \"\$f\" ] && rm -f \"$DOC/\$f\" && echo \"   removed new file \$f\"; done < .new-files
  if [ '$KIND' = api ]; then
    cd $DOC/server
    if [ -d \$S/server/node_modules ]; then
      rm -rf node_modules.rollback && mv node_modules node_modules.rollback
      cp -a \$S/server/node_modules node_modules && rm -rf node_modules.rollback
      echo '   restored node_modules'
    fi
    # Ownership from README: code root-owned and read-only to the app,
    # server/ root:nemo 1770, .env root:nemo 0640. The live sqlite files are
    # pruned rather than chowned away and back, so the running API never
    # loses write access to them, even for a moment.
    find . -name 'bookings.sqlite*' -prune -o -exec chown root:root {} + -exec chmod go-w {} +
    chown root:nemo . && chmod 1770 .
    chown root:nemo .env && chmod 0640 .env
    systemctl restart nemo-seamless-gutter
    sleep 2
  fi"
NEMO_CHECK_FORCE_FAIL= scripts/check_live.sh "$KIND" && echo "rolled back to $SNAP" || { echo "!! rolled back to $SNAP but live checks still fail" >&2; exit 1; }

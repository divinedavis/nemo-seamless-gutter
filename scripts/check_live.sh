#!/usr/bin/env bash
# Content checks against the live site, run ON the droplet so they go through
# the real nginx + TLS + Node path. Exit 0 only if every check passes.
#
#   scripts/check_live.sh web [changed files...]   # after deploy_web.sh
#   scripts/check_live.sh api                      # after deploy_api.sh
#   scripts/check_live.sh                          # both, read-only health check
#
# Read-only for visitors and the books: the booking check POSTs a deliberately
# INVALID booking (no name), which the API rejects with a 400 before anything
# is stored or emailed. It is rate-limited like any client (4 per 10 minutes,
# 12 a day, keyed on 127.0.0.1 here), so a 429 also passes — it still proves
# the route is up — and says so.
#
# Requests resolve the domain to 127.0.0.1 on the box, so they never touch the
# public IP's rate-limit bucket and never appear as a visitor: analytics
# counts the /e/pv beacon, which only a browser running analytics.js sends.
#
# NEMO_CHECK_FORCE_FAIL=1 makes the run fail after its real checks — the way
# to prove a deploy's automatic restore without breaking anything for real.
# rollback.sh clears it for its own check.
set -euo pipefail
HOST=${NEMO_HOST:-root@104.236.120.144}
MODE=${1:-all}
shift || true
CHANGED_HTML=$(printf '%s\n' "$@" | grep -E '\.html$' | head -40 | tr '\n' ' ' || true)

rc=0
ssh "$HOST" "MODE='$MODE' CHANGED_HTML='$CHANGED_HTML' bash -s" <<'REMOTE' || rc=$?
set -u
SITE=https://nemoseamlessgutter.com
CURL="curl -sS -m 15 --resolve nemoseamlessgutter.com:443:127.0.0.1"
fail=0
ok()  { printf '   ok    %s\n' "$1"; }
bad() { printf '   FAIL  %s\n' "$1"; fail=1; }
get() { $CURL -o /tmp/nemo-check.body -w '%{http_code}' "$SITE$1" 2>/dev/null || echo 000; }
expect() {  # path code [must-contain...]
  local p=$1 want=$2; shift 2
  local code; code=$(get "$p")
  if [ "$code" != "$want" ]; then bad "$p -> $code (want $want)"; return; fi
  for s in "$@"; do
    grep -qF -- "$s" /tmp/nemo-check.body || { bad "$p missing: $s"; return; }
  done
  ok "$p -> $code"
}

if [ "$MODE" = web ] || [ "$MODE" = all ]; then
  expect / 200 'NEMO Seamless Gutter' 'id="booking"' '(717) 578-0073' 'booking.js'
  expect /booking.js 200 "/api/book" "/api/services"
  expect /styles.css 200
  expect /robots.txt 200 'Sitemap: https://nemoseamlessgutter.com/sitemap.xml'
  expect /sitemap.xml 200 '<urlset'
  for f in $CHANGED_HTML; do expect "/$f" 200 '</html>'; done
  # Private files beside the site must stay unreachable.
  for p in /server/.env /server/bookings.sqlite /seo/.env /growth/state.json \
           /reports/ /agent/prompt.md /README.md /index.html.growth-bak /growth_daily.py; do
    expect "$p" 404
  done
fi

if [ "$MODE" = api ] || [ "$MODE" = all ]; then
  systemctl is-active --quiet nemo-seamless-gutter && ok "systemd nemo-seamless-gutter active" \
    || bad "systemd nemo-seamless-gutter not active"
  expect /api/health 200 '"ok":true'
  expect /api/services 200 '"estimate"' '"consult"'
  code=$($CURL -o /tmp/nemo-check.body -w '%{http_code}' -X POST -H 'content-type: application/json' \
         --data '{"service":"estimate","name":"","phone":""}' "$SITE/api/book" 2>/dev/null || echo 000)
  if [ "$code" = 400 ] && grep -q 'Please enter your name' /tmp/nemo-check.body; then
    ok "POST /api/book (invalid, nothing stored) -> 400 validation"
  elif [ "$code" = 429 ]; then
    ok "POST /api/book -> 429 (rate-limited; route is up, validation not re-checked)"
  else
    bad "POST /api/book (invalid) -> $code $(head -c 200 /tmp/nemo-check.body)"
  fi
fi
rm -f /tmp/nemo-check.body
exit $fail
REMOTE
if [ "${NEMO_CHECK_FORCE_FAIL:-}" = 1 ]; then
  echo "   FAIL  forced by NEMO_CHECK_FORCE_FAIL=1"
  rc=1
fi
exit $rc

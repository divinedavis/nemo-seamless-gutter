#!/usr/bin/env bash
# Every fast automated test in the repo, in one command. Exit 0 only if all pass.
#
#   scripts/test.sh
#
# Run by .githooks/pre-push, .github/workflows/ci.yml and both deploy scripts
# before anything is copied. Takes a few seconds.
#
#   1. Python unittest discovery from the repo root: growth/test_*.py (the
#      growth engine) and tests/test_*.py (static-site checks). Every test in
#      these files is a unittest.TestCase — a bare pytest-style `def test_*()`
#      at module level would be silently skipped by discovery, so don't add one.
#   2. node --test server/test/*.test.js: the booking API booted against a
#      temp SQLite file with email, calendars and weather forced off. Needs
#      `npm ci --prefix server` once (better-sqlite3 is native).
#
# Not here (slower, needs browsers): tests/booking_journey.py — see CLAUDE.md.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-python3}

echo "== python (growth engine + site)"
"$PY" -m unittest discover -s . -t . -p 'test_*.py' 2>&1 | tail -3

echo "== node (booking API)"
if [ ! -d server/node_modules ]; then
  echo "server/node_modules missing — run: npm ci --prefix server" >&2
  exit 1
fi
# --test-reporter=spec: node 20 (the droplet, CI) defaults to TAP off a TTY.
if ! out=$(node --test --test-reporter=spec server/test/*.test.js 2>&1); then
  echo "$out" | grep -vE '^\s*(at |ℹ (suites|cancelled|skipped|todo|duration))' >&2
  echo "node tests failed" >&2; exit 1
fi
echo "$out" | grep -E '^ℹ (tests|pass|fail) ' || true
echo "== all tests passed"

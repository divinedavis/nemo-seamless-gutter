# NEMO Seamless Gutter — working notes for Claude

Site + booking API for nemoseamlessgutter.com (droplet 104.236.120.144). Read
README.md first; its Deployment and OWASP LLM sections apply to every change.

## Tests

**Every change adds, updates AND deletes tests in the same commit, and says so in
the commit body** (`Tests: added …, changed …, removed …` — or why none apply).
A test for behaviour that no longer exists is deleted, not skipped.

- `scripts/test.sh` — every fast test, under a second or two. Python unittest
  discovery from the repo root (`growth/test_*.py`, `tests/test_*.py`) plus
  `node --test server/test/*.test.js`. Python tests must be `unittest.TestCase`
  methods: a bare module-level `def test_*()` is silently skipped by discovery.
  Needs `npm ci --prefix server` once.
- `python3 tests/booking_journey.py` — the homepage booking widget in desktop
  Chromium and iPhone WebKit (needs Playwright + browsers). Run it when you touch
  `index.html`, `booking.js`, `booking.css`, `styles.css`, `script.js` or `server/`.
- Tests never book, email or text anyone: the API runs on a temp SQLite file with
  SMTP, calendar feeds, iCloud and weather forced off (single-space env values
  stop `server/.env` filling them), and the browser aborts every POST to
  `/api/book`. Keep it that way — never point a test at the live site's
  `/api/book` with a valid booking.
- Gates: `.githooks/pre-push` (gitleaks over the pushed commits + `scripts/test.sh`;
  enable per checkout with `scripts/install_hooks.sh`, not on the droplet), and
  GitHub Actions — `ci.yml` (gitleaks + `scripts/test.sh`, every push/PR) and
  `journeys.yml` (the browser journey, path-filtered). Public repo, free minutes,
  no secrets in GitHub.

## Deploying

`scripts/deploy_web.sh` (static) and `scripts/deploy_api.sh` (booking API) run the
tests, ship HEAD only, refuse to overwrite live content that was never committed,
snapshot to `/var/backups/nemo-web|nemo-api/`, check live and auto-restore on
failure. `scripts/rollback.sh web|api [ts]`, `scripts/check_live.sh`. Never
`rsync`/`scp` repo HTML over the docroot by hand: the growth engine writes pages
there first. Growth engine code goes through `deploy/deploy_growth.sh`.

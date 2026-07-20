# SEO automation

Server-side automation that runs on the droplet via cron. All scripts are
dependency-free Python 3 (stdlib only) and self-guard so they're harmless until
the domain points at this server.

| Script | What it does | Schedule |
| --- | --- | --- |
| `gen_sitemap.py` | Rebuilds `sitemap.xml` from the live `.html` files with accurate `<lastmod>`. New pages (service areas, guides) are picked up automatically — no manual editing. | daily 03:00 ET + after deploys |
| `indexnow_submit.py` | Pushes all sitemap URLs to **IndexNow** (Bing, Yandex, Seznam, Naver) for near-instant indexing. Self-activates only once `https://nemoseamlessgutter.com/<key>.txt` is live, so it's a safe no-op while the domain is still parked. | daily 03:05 ET |
| `gen_article.py` | Drafts a unique, genuinely-useful local gutter guide with Claude (rotating long-tail topics). **Draft-only by default** (writes to `seo/drafts/`) to stay clear of Google's scaled-content policy; `--publish` moves the newest draft into `/guides/`. Needs `ANTHROPIC_API_KEY` in `seo/.env`. | monthly, 1st 06:00 ET |

`indexnow_key.txt` holds the IndexNow key; the matching `<key>.txt` at the web
root is the public ownership file IndexNow fetches to verify the domain.

The `/seo/` path is denied by nginx and disallowed in robots.txt — scripts and
drafts are never web-served or indexed.

### Manual runs
```bash
cd /var/www/nemo-seamless-gutter
WEB_ROOT=$(pwd) python3 seo/gen_sitemap.py
WEB_ROOT=$(pwd) python3 seo/indexnow_submit.py
WEB_ROOT=$(pwd) python3 seo/gen_article.py            # draft
WEB_ROOT=$(pwd) python3 seo/gen_article.py --publish   # publish newest draft
```

## Mail configuration (added 2026-07-20)

The Workspace **login** is `enemo@nemoseamlessgutter.com`. `eric@` is a working
alias that reaches the same mailbox but **cannot authenticate** — verified by
SMTP AUTH plus an MX `RCPT TO` probe. Anything that logs in must use `enemo@`.

SMTP lives in `server/.env` (mode 600, gitignored) and is shared by the booking
server and `health_check.py`:

    SMTP_HOST=smtp.gmail.com
    SMTP_PORT=587
    SMTP_SECURE=false
    SMTP_USER=enemo@nemoseamlessgutter.com
    SMTP_PASS=<Google app password — macOS keychain: nemo-workspace-app-password>
    FROM_EMAIL=enemo@nemoseamlessgutter.com
    OWNER_EMAIL=eric@nemoseamlessgutter.com,enemo@nemoseamlessgutter.com

The app password requires 2-Step Verification on the account and is created at
myaccount.google.com/apppasswords.

**Gotcha:** `node -e "require('./config')"` reports `smtp: (none)` because it
does not load `.env`. That is a false alarm. The authoritative checks are the
pm2 startup line `smtp: on`, or a real booking returning `"emailed":true`.

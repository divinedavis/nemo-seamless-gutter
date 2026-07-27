# Growth engine

A self-improving daily loop aimed at one goal: **more than half of York County
gutter searches landing on this business**, and the phone ringing because of it.

Runs on the droplet at 06:00 America/New_York from `/etc/cron.d/nemo-growth`:

    growth_daily.py daily --email divinejdavis@gmail.com

which is: **measure → review → build → scout → report**.

## The five steps

| Step | What it does |
| --- | --- |
| `measure` | Yesterday's traffic from `/var/log/nginx/nemo-access.log` (bots and Eric's own IPs excluded) plus bookings and phone-agent leads from `server/bookings.sqlite`. Writes one row per metric into the ledger. |
| `review` | Re-judges every active technique against its own measured series. Retires what isn't earning its keep after a 30-day grace period, and records the verdict forever. |
| `build` | Runs each **active** technique — writes today's page, refreshes the link mesh and schema, rebuilds the sitemap, pings IndexNow. |
| `scout` | Asks a model with live web search what is working now for local contractors, and files new ideas as **candidates**. It never activates anything. |
| `report` | Emails the blunt version: what ran, what it moved, what's blocked. |

## The ledger decides what runs, not the code

`techniques.json` on the droplet is the source of truth. A technique has a
status of `candidate`, `active` or `retired`, and only `active` ones run. That
means switching something off is a one-line edit with no deploy — which is what
lets `review.py` prune autonomously.

Verdicts persist after retirement, so a dead idea can't be re-proposed as if it
were new, and the accumulated history *is* the year-end "what actually worked"
list:

    python3 growth_daily.py status

The runtime files (`techniques.json`, `keywords.json`, `results.jsonl`,
`state.json`) are **gitignored on purpose**. The droplet's copies are the
measurement history; a stale checkout overwriting them would erase it.
`seed.py` and `keywords.py` recreate the baseline on a fresh install.

## What it will and won't do on its own

Writes and deploys pages, structured data, internal links, sitemap and IndexNow
submissions — all to the live site, unattended.

It will **not** spend money, email customers, post as the business, or turn on
its own ideas. Anything in that category is seeded as a `candidate` with the
first step written down, and shows up in the report's **WAITING ON YOU** block.

Guardrails in `techniques.py`: never delete a file, always write atomically,
back up any hand-built page before the first edit (`*.growth-bak`), and publish
at most one new page per run — a hundred thin town pages overnight is the exact
pattern Google's scaled-content policy targets.

## The goal metric, honestly

The target is >50% of the tracked queries in `keywords.json` holding a **top-3**
position. Position can only be known from Search Console, and that is **not
connected yet**, so `share_pct` is `null` and the report says `UNMEASURED`.

Until then it shows *coverage* — does a page exist whose headings target the
query — clearly labelled as a proxy. Coverage is not rank, and the report never
prints one where a reader would read the other. Connecting Search Console
(technique T010) is what turns the goal from a proxy into a measurement.

    python3 growth_daily.py goal    # exits 0 once the goal is met, 1 until then

## Requirements

* **Anthropic API credits.** `area_pages`, `money_pages` and `scout` all call
  the API; without credits they fail cleanly and the rest of the run continues.
  The key is read from `seo/.env` — the same one `seo/gen_article.py` uses.
* **The dedicated nginx access log.** `access_log /var/log/nginx/nemo-access.log`
  in the site config. Without it this site's requests land in the droplet's
  shared catch-all, which has no Host field, and traffic cannot be attributed.
* `/growth/` is denied in nginx and disallowed in robots.txt — the ledger is
  internal business data, never web-served.

## Running it by hand

Every command takes `--dry-run`, which makes the whole thing read-only:

```bash
cd /var/www/nemo-seamless-gutter
WEB_ROOT=$PWD python3 growth_daily.py daily --dry-run   # safe full rehearsal
WEB_ROOT=$PWD python3 growth_daily.py measure           # yesterday's numbers
WEB_ROOT=$PWD python3 growth_daily.py build             # write today's page
WEB_ROOT=$PWD python3 growth_daily.py status            # the scoreboard
```

Logs: `/var/log/nemo-growth.log`.

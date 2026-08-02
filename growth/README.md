# Growth engine

A self-improving daily loop aimed at one goal: **more than half of York County
gutter searches landing on this business**, and the phone ringing because of it.

There are two layers, and they run an hour apart:

| | 06:00 ET — the engine (this droplet) | 07:00 ET — the review agent (cloud) |
| --- | --- | --- |
| Runs | `/etc/cron.d/nemo-growth` | a claude.ai routine |
| Does | measure → review → build → scout → report, then publishes state to GitHub | reads the published state, judges whether prior changes worked, researches, writes the journal |
| Can | write and deploy pages on the live site | read the repo and commit to it — **nothing it commits deploys** |
| Sees | nginx logs, the bookings database, the ledger | only `growth/snapshot.json` and `growth/JOURNAL.md` |

The engine does the mechanical work; the agent is the judgment layer on top. The
agent has no access to this machine, so `snapshot.py` publishes a PII-free state
file and `publish_state.sh` pushes it — the repository is the bridge between them.

The engine step is: **measure → review → build → scout → report**.

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
position. Position can only be known from Search Console, which was connected on
**2026-07-27** (technique T010, now retired as done). `share_pct` has been a real
measurement since 2026-07-28; it is `null` only if the connection breaks.

Read it with its denominator in view. `share_pct` is `top3 / total`, and `total`
is every query in `keywords.json` — including the ones Search Console has never
returned a position for, which is most of them. `adopt_queries` and the scout
both add queries, so the denominator grows on its own and the headline share
falls on mornings when nothing on the site got worse. `ranked_known` in the same
block is the count Search Console can actually rank; compare `top3` against that
when you want to know whether the site moved, and against `total` when you want
to know how far there is left to go.

`coverage_pct` — does a page exist whose headings target the query — is still
reported, clearly labelled as a proxy. Coverage is not rank, and the report never
prints one where a reader would read the other.

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

## The bridge to the review agent

`snapshot.py` writes two files that the cloud agent reads, and
`publish_state.sh` pushes them straight after the 6am run:

* **`snapshot.json`** — yesterday's metrics, the full ledger with hypotheses and
  verdicts, keyword coverage, the uncovered-query build queue, and the last
  build and scout results. **Aggregates only.** The bookings and leads tables
  hold real customers, and `_assert_no_pii` refuses to write the file if
  anything shaped like a phone number, email address or street address appears
  in it. The business's own published contact details are allowed through.
* **`JOURNAL.md`** — append-only. The engine writes what it did; the agent
  writes what it concluded and why. Nothing is ever edited after the fact — a
  decision log is only worth reading if it still shows what was believed at
  the time.

`publish_state.sh` keeps a **separate clone** at `/root/nemo-repo` and copies
specific paths into it. The docroot is deliberately not a git repository: it
holds `.env` files, the bookings database, and server-only auto-published
guides, and a stray `git reset` or `git clean` in there would be destructive.
Pushing uses a write-scoped deploy key (`/root/.ssh/nemo_deploy`, SSH host alias
`github-nemo`).

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

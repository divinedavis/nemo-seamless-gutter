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

## The bridge only runs one way

`publish_state.sh` copies **droplet → repo**, and only these paths:
`growth/snapshot.json`, `growth/JOURNAL.md`, `sitemap.xml`, `index.html`, and
`areas/ guides/ services/`. Nothing copies the other way, ever. Two consequences
that have each cost weeks, so they are written down here rather than rediscovered:

* **Engine code committed here is not running.** The docroot is not a git
  checkout, so a fix to `growth/*.py` or `growth_daily.py` sits in the
  repository doing nothing until a human copies it across. Surviving the 06:00
  publish is not the same as being live. Check, and then close the gap:

      git -C /root/nemo-repo fetch origin main
      git -C /root/nemo-repo reset --hard origin/main
      bash /root/nemo-repo/deploy/deploy_growth.sh           # read-only report
      bash /root/nemo-repo/deploy/deploy_growth.sh --apply   # copy the stale ones

  The report hashes each file and prints `ok` / `STALE` / `MISSING`. It is safe
  to run at any time and is the answer to "is my fix live?".

* **Page edits committed here are reverted.** `index.html`, `sitemap.xml` and
  anything under `areas/ guides/ services/` are overwritten from the docroot at
  the next 06:05 publish. To change live page copy, edit it in the docroot; a
  repo-side edit looks like a fix for one day and then silently disappears.

**The self-check:** a current `snapshot.py` emits a top-level `code_version`
fingerprint block. If the published `snapshot.json` has no `code_version`, the
droplet is running stale engine code and the deploy above has not been run —
which is also why that diagnostic cannot report its own absence.

## When no publish commit arrives

A morning with **no `Publish growth state for <date>` commit at all** is a
different failure from a morning that published a snapshot full of failures,
and it is the one that hides. It happened on 2026-10-13, 10-14 and 10-15, and
the diagnostic was re-derived from scratch each day, so it lives here now.

Why it is silent: `publish_state.sh` exits 0 printing `publish: nothing changed`
when no watched path differs. If `growth_daily.py` dies before
`snapshot.write()`, nothing in the clone *has* changed, so the publisher is
behaving correctly — the one case where "nothing changed" is the alarm is the
case it cannot distinguish.

Three causes, which need opposite responses. One command separates them:

    grep publish /var/log/nemo-growth.log | tail -40

* **`publish: nothing changed` dated that morning** — cron ran, and nothing the
  publisher watches differs. Two different failures land here and they need
  opposite responses, so split them with a second grep before doing anything:

      grep 'snapshot: FAILED' /var/log/nemo-growth.log | tail -5

  * **a `snapshot: FAILED — <error>` line** — the engine ran *to completion* and
    only the snapshot write raised. `snapshot.write()` and
    `snapshot.append_journal()` share one `try` in `cmd_daily`, and its `except`
    logs that line and falls through to `cmd_report`. So the docroot's
    `snapshot.json` and `JOURNAL.md` both freeze at their last good day, the
    publisher re-copies files identical to what GitHub already has, exits 0, and
    Eric's report still arrives every morning. **Nothing is lost** — see the
    backfill note below — and the fix is whatever the error says (a full disk and
    a permissions change are the usual two).
  * **no such line** — the engine raised *before* the snapshot block. Find the
    last `Traceback` in the same log. This is the case that loses data.

  **What does not tell them apart:** a frozen `snapshot.json` whose `date`
  never moves while the engine's own `## <date> — engine run` entries stop dead
  on the same day. An earlier version of this section offered that shape as an
  outside-the-droplet test for the first case, on the grounds that one `try`
  governs both writes. It governs both writes, and that is why the shape proves
  nothing: in the second case neither write is *called*, so both files freeze
  together exactly as they do in the first. The shape is what every
  unpublished morning looks like from the repository — necessary, never
  sufficient — and reading it as the first case is how a morning that needed a
  backfill gets filed as "nothing lost". It has to be the log, or the email
  below.
* **no `publish:` line for that morning at all** — two very different causes
  land here, so check for git or ssh error text in the log that morning before
  concluding anything:

      grep -iE 'permission denied|could not read from remote|publickey|host key|fatal:' \
        /var/log/nemo-growth.log | tail -10

  * **git or ssh error text present** — the droplet's state is fine and only
    the git step broke. **Nothing is lost and no backfill is needed:** the
    engine completed, `snapshot.write()` succeeded, and the docroot and the
    ledger are both current — only GitHub is behind. Fix the credential:
    `git -C /root/nemo-repo fetch origin main` reproduces it by hand.
  * **no git error text either** — cron, python or the droplet never got that
    far. Check `systemctl status cron`, `df -h /var /root` (a full disk fails
    both halves), and whether `/etc/cron.d/nemo-growth` still exists. `cat` it
    rather than only testing for it, and diff it against
    `deploy/cron-nemo-growth`: every published snapshot's `generated` timestamp
    falls at 06:05-06:13 **UTC** (02:05 ET), so the entry that has been running
    is not honouring the `CRON_TZ=America/New_York` the repo's copy sets. A file
    that exists can still be an older copy firing at a different hour, mailing
    nobody, and `crontab -l` may hold a second one. This case
    loses data; backfill.

  **Do not expect the git error to follow a `publish:` line — it cannot.** An
  earlier version of this section said to look for "a git or ssh error after a
  `publish:` line", which no credential failure can produce. The script is
  `set -euo pipefail` (`publish_state.sh:16`) and its only success echo,
  `publish: pushed N file(s)`, is on the line *after* the push
  (`:92-93`), so a failed push exits before printing anything. A dead deploy
  key is worse still: it fails at `git fetch --quiet origin` (`:35`), ahead of
  every echo in the file. Either way the morning's log holds git's stderr and
  no `publish:` line, which is exactly the shape this bullet used to attribute
  to a dead cron.

  Note also what the push case does to the clone, which is harmless but looks
  alarming: the commit is created locally (`:83`), the push fails, and the next
  morning's `git reset --quiet --hard "origin/$BRANCH"` (`:36`) discards it
  before re-copying from the docroot. So the unpushed commits do not pile up
  and there is nothing to salvage from `/root/nemo-repo` — one successful push
  after the fix carries the current state.

**Free first step with no droplet access:** ask Eric whether his daily report
email arrived. `cmd_report` is the last call in `cmd_daily`, after the snapshot
block, so "no email" points at the first two causes. "Email arrived" proves the
run reached its final line, which **narrows the cause to two, not one** — the
`snapshot: FAILED` branch and the push branch both leave `cmd_report` intact,
and they need opposite fixes (a disk or permissions problem on the droplet
versus a git credential). Do not read an arrived email as pointing at the push
on its own; it says only that cron, python and `cmd_daily` are alive. The two
greps above separate them.

**On a Friday, Divine does not have to ask anybody.** `deploy/cron-nemo-growth`
splits the 06:00 run on the day-of-week field, and the `0 6 * * 5` line is the
only one carrying `--email divinejdavis@gmail.com` — the developer's weekly
copy. It is sent by the same `cmd_report` call at the end of the same
`cmd_daily`, so on a Friday the developer's own inbox answers the same question
Eric's inbox answers on the other six days, with no droplet access and nobody
to ask:

* **the weekly developer mail arrived** — cron fired, python started, and
  `cmd_daily` ran all the way to its last line. Causes 1 and 2 are out; the
  failure is at `snapshot.write()` or in the push. Go to the `grep publish`
  table above.
* **it did not arrive** — the run died before `cmd_report`, or cron, python or
  the droplet never started it. Causes 1 and 2 are live.

Both mail diagnostics share one dependency: they are silent if SMTP itself is
broken, which looks identical to a dead run from outside. A no-mail answer is
therefore suggestive and not conclusive, while a mail-arrived answer is
conclusive — it proves the run reached its final line. Check the gap the other
way when it matters: a `publish:` line in the log with no mail is SMTP, not the
engine.

**Back the missing days out of the nginx log before they age away — but check
first whether anything is actually missing.** `measure` records yesterday only,
and the 45-day series in `snapshot.json` is accumulated in the ledger, not
recomputed. The hole is therefore **in the ledger, not in the snapshot**, and
only `measure` failing to run can make one: `snapshot._series()` re-reads
`ledger.series("__site__", metric)` on every write, so if the engine has been
running and only the snapshot write or the push was broken, the ledger already
holds those mornings and the series fills itself in completely on the first
successful publish, with no backfill at all. Decide which case you are in from
the `snapshot: FAILED` grep above before assuming a loss.

Where `measure` genuinely did not run, the morning is a permanent hole unless it
is backfilled while the rotations are still on disk (`rotations()` in
`metrics.py` reads every kept archive, but the log is rotated away after a few
days). Running it in the no-loss case is harmless — it is idempotent — so when
the two cases cannot be told apart, back-fill anyway:

    ls -la /var/log/nginx/nemo-access.log*          # how many days are left
    cd /var/www/nemo-seamless-gutter
    WEB_ROOT=$PWD python3 growth_daily.py measure --days 6   # 5 is exact today

`--days N` measures the N complete days ending **yesterday**, so N must reach
back from yesterday to the first missing day inclusive: with the series ending
`S` and yesterday `Y`, that is `N = Y - S` days. On 2026-10-17 the series ends
10-11 and yesterday is 10-16, so `N = 5` covers 10-12 through 10-16 exactly, and
6 buys a day of margin. Overshooting is free:
re-measuring a day already recorded is idempotent (below), so when in doubt pass
a larger number rather than a precise one.

Safe to re-run: `ledger.record_result` is idempotent per
`(date, technique, metric)` and `read_results` keeps the newest write, so
re-measuring a day already recorded cannot double-count it.

**The watchdog cannot catch the third cause.** `0 11 * * *` lives in the same
`/etc/cron.d/nemo-growth` as the 06:00 run, so anything that kills cron kills
the alarm with it, and the alarm has had no `--email` since 2026-08-27 in any
case. The only check that survives a dead droplet is off it: **the absence of a
publish commit on GitHub**, which is what the 07:00 review agent reads. Restore
the flag (`--email divinejdavis@gmail.com`) for causes 1 and 2; for cause 3 the
repository is the heartbeat.


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


## Standalone docroot repairs (no API credit, no `growth/` deploy)

Five scripts under `deploy/` repair live pages **in place, on the droplet**.
They are listed here because until today they were discoverable only by
grepping a 2.6 MB journal, and they are precisely the class of work that is
still executable when the rest of this engine is not: each one is stdlib-only,
imports nothing from `growth/`, needs no Anthropic balance, and needs no
`growth/` deploy. Through the publish outage that began 2026-10-13 they have
been the only on-site fixes available at all.

```bash
cd /var/www/nemo-seamless-gutter
python3 deploy/<script>.py                     # report only, writes nothing
python3 deploy/<script>.py --apply             # make the change
python3 deploy/<script>.py --root /some/other  # non-default docroot
```

| script | what it fixes |
| --- | --- |
| `repair_titles.py` | `<title>` tags longer than the 65 characters Google shows, and brands appended twice |
| `repair_letter_paragraphs.py` | pages published one character per `<p>` |
| `repair_placeholder_paragraphs.py` | elements whose whole visible text is an unrendered template token |
| `repair_out_of_area_prose.py` | copy claiming towns NEMO does not serve (repairs, does not delete) |
| `retire_out_of_area.py` | whole pages and tracked keywords for towns outside the service area |

Every one is report-only without `--apply`, so running the lot to see what they
would do costs nothing and changes nothing. Read each script's own docstring
before applying it — they explain what they deliberately leave alone.

**They must run against the docroot, not the repo.** `growth/publish_state.sh`
rsyncs `areas/`, `guides/` and `services/` **docroot → repo** every morning, so
the repository's copies of those pages are a read-only mirror: a fix made there
is overwritten by the next publish and never reaches a visitor. Deploying
`growth/` is not a substitute either — `techniques.py` applies `TITLE_MAX` to
the *next* page it writes and does not revisit the pages already on disk.

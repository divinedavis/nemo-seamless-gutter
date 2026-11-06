# Open items — what is waiting on a human

**Rewritten by the review agent on every run. Generated 2026-11-06.**
If the date above is not roughly today's, this file is stale and
[`JOURNAL.md`](JOURNAL.md)'s last entry wins. Nothing here is a decision; every
line is a recommendation Eric or Divine can accept or reject. **The 2026-11-06
run gave the outage an end date** — day 25. Traffic history is no longer merely
being destroyed at one morning per day: **after 2026-11-19 no part of the
current hole (10-12 → 11-05) can be recovered by anything**, because the last of
its still-readable mornings ages out that day. Eleven of the twenty-five are
already gone. The run also moved that fact out of this file and into the
freshness alarm — the only channel here that is provably delivered, sixteen
failing runs, all attributed by GitHub to `divinedavis` — so tomorrow's 13:17
UTC run states the deadline and the backfill command itself, with no deploy.
Detection and delivery remain solved; the gap is twenty-five days of no reply.

Why this file exists: `JOURNAL.md` is append-only and 2.8 MB. That is correct
for a decision log — it shows what was believed at the time — but it means the
*current* ask is buried under ninety-odd entries. Items 1–3 below are free,
take five minutes each, need nobody's permission, and the oldest has been open
for **102 days**.

**It is 6 November, leaf-fall is over, and we are now inside the next window.**
The autumn spike passed end to end with the engine dead. But
**ice-dam season (Jan–Feb) is the second spike**, and the work it needs is still
unfunded. **The 2026-11-03 run corrected this file's own deadline**, in the
loosening direction: the 8–12-week figure it used is a *new-page* timing, and the
engine will not write a new page here — all four uncovered ice-dam queries route
to service pages that already exist, so this is `strengthen_pages` adding a
section to a page Google already indexes. Vendor estimates for that are recrawl
in 1–14 days and movement 2–8 weeks after, so **early December is probably not
fatal where mid-November was stated as a cliff**. Do not read that as room to
wait: it is still the only revenue-relevant window before autumn 2027, and these
remain vendor timings rather than Google's, with a lane that needs a snowy
winter. See the 2026-10-31 and 2026-11-03 entries.

---

## Item 0 — the one that blocks everything else

**The engine has published nothing for twenty-five mornings** (last publish
`0b2c596`, 2026-10-12 06:05 UTC). Every number this project reports is 605
hours old. The GitHub freshness alarm has gone red on **sixteen consecutive
scheduled runs**, 10-21 through 11-05, each one attributed by GitHub to
`divinedavis` — checked in the API, not assumed, so the alarm is reaching an
account that exists and the silence is not a misrouted notification.

**Item 0a, ten seconds, do it first: `ls -la /var/log/nginx/nemo-access.log*`.**
Traffic history is no longer merely frozen, it is being destroyed — and as of
today that destruction has a **final date: 2026-11-19**. That listing answers
**one** question now: how much is left, and whether that date is already past.

`measure` records yesterday only and the series is accumulated, not recomputed,
so each dead morning is a permanent hole; the recovery reads whatever logrotate
kept, and the packaged Debian/Ubuntu nginx policy keeps **~14 days**. On day 25
that puts **10-12 to 10-22 past recovery — eleven mornings** (the series ends
10-11, so the first *missing day* is 10-12, while 10-13 is the first missed
*publish*) — with one more lost daily, and **fourteen still recoverable today**.
**The last of those fourteen ages out on 2026-11-19**: after that date this hole
is permanent whatever anyone runs, and what is lost is the whole of leaf-fall
peak with no traffic data at all. The boundary day is an estimate, not a measurement. The oldest timestamp in the listing is the real deadline and may
prove this wrong. **GSC rank data is safe** (the API backfills ~16 months); nginx
traffic is the perishable half.

*The naming question is closed.* Yesterday this item also asked you to check how
the archives were named, because `rotations()` matched only logrotate's numeric
scheme and would have **silently recovered nothing** on a `dateext` droplet. The
2026-11-02 run fixed that, and the **2026-11-03 run verified the whole command
end to end** — 22 days of synthetic archives, both naming schemes, 22 of 22
mornings recovered, right window
(`growth/test_metrics.py::BackfillAcrossRotations`). So you no longer have to
read the suffixes, and item 9 no longer blocks this.

Backfill with `growth_daily.py measure --days 25`, idempotent per
`(date, technique, metric)`. Only days the `/e/pv` beacon logged come back:
since 2026-08-14 that beacon is the only thing a visitor is counted from.

**This and item 10 are one decision.** Neither half works alone: credit buys
nothing while cron publishes nothing, and a repaired cron writes nothing on an
empty balance. The 2026-11-03 run loosened the deadline from mid-November to
"early December is probably not fatal" (see item 10), but both halves still have
to happen this season or the system idles until autumn 2027.

**Divine — three greps and one `cat` on the droplet, ~10 minutes.** Run these;
the output names the cause:

```
grep publish /var/log/nemo-growth.log | tail -40
grep 'snapshot: FAILED' /var/log/nemo-growth.log | tail -5
grep -iE 'permission denied|could not read from remote|publickey|host key|fatal:' \
  /var/log/nemo-growth.log | tail -10
cat /etc/cron.d/nemo-growth; crontab -l | grep -i nemo; df -h /var /root
```

| What you see | Cause | Data lost |
| --- | --- | --- |
| `snapshot: FAILED` | droplet disk or permissions | none |
| no `publish:` line, but git/ssh error text | the deploy key broke | none — fix the key |
| **neither** | **cron or python died** | **each morning's data, permanently** |

**Cadence recommendation, 2026-10-30, still unactioned on 11-06 (seventh day):** the review
agent has recommended that this daily review drop to **weekly** until a publish
commit lands — **twenty-five entries** have now re-read the same 25-day-old
file (counted from the review-agent headings in `JOURNAL.md`; this line
previously said "ten", which was wrong). The
agent did **not** change the schedule; that is Eric and Divine's call.
Trigger `trig_0188mo2mgq6J6uqw3KE6ZMjd`, one edit to its cron expression.
Revert to daily when publishing resumes.

Longer branch table: [`README.md`](README.md#when-no-publish-commit-arrives).
Note the cron trap: every published snapshot's `generated` timestamp is
06:05–06:13 UTC = 02:05 ET, so whatever has been publishing is *not* honouring
the `CRON_TZ=America/New_York` the repo's copy sets. Compare the live entry
against the repo's; do not just check that a file exists.

---

## Eric — needs a login, no code, no cost

| # | Item | Open | Where |
| --- | --- | --- | --- |
| 1 | **Business Profile → Performance → write down the `Calls` number.** Note the date range used. That report is a rolling ~six-month window, so the summer baseline starts expiring around January 2027 — waiting costs data permanently. (New performance reports are reportedly rolling out, so the screen may have moved.) | 90 d | T049 |
| 2 | **Business Profile audit — pending suggested edits and primary category FIRST.** Third-party reports (2026-11-03 research, **unconfirmed against Google's own docs** — treat as a reason to look, not a fact) say an unreviewed suggested edit to hours, **phone number** or category may publish after about **4 days**. An unattended profile having its phone number edited is the one failure that would cost more than everything else on this list, and nobody has logged in for 102 days. Then: most specific *true* gutter category, hours, services detail, photos, review replies. **Do not touch the business name** — keyword-stuffing it risks suspension, and "NEMO Seamless Gutter" already carries the service term. (T016's Q&A half is dead — Google retired Q&A; the category half is not.) | 102 d | T016 |
| 3 | **Ask every finished job for an honest Google review — and reply to the 13 you already have.** Do *not* ask customers to mention the service or the town. Google's allowance lets a merchant "solicit or encourage the posting of content that does represent a genuine experience, **without offering incentives to do so or attempting to influence the rating or the contents of the review**" — that last clause is general, is about the merchant himself, and predates the April 2026 staff-quota clauses, so coaching the wording is out. Ask for a review, not for words: no incentive, no gating, no pressure in the driveway; a follow-up text or email with a plain link is the safe form, 1–2 a month, every month. **Then get the service and town onto the profile in your own voice:** reply under each of the 13 reviews naming what the work was and which town, non-defensive on the low ones. An owner's reply is his own content in a field Google provides for it, so no solicitation rule touches it. | 102 d / 95 d | T007, T033 |
| 4 | **Link GA4 to the Business Profile: GA4 → Admin → Product links → Google Business Profile links → Link.** One-time, ~5 min, needs one account holding both GBP and GA4 admin. Puts the profile's `calls` metric beside the site's `call_taps`, which `growth/metrics.py` provably cannot see — so item 1 stops needing a monthly login. | 9 d | research 2026-10-26 |
| 5 | **Three real gutter-cleaning prices.** `guides/gutter-cleaning-cost-york-pa.html` promises "Typical price ranges" and prints no dollar figures. The agent will not invent them. | carried | — |
| 6 | **Will you drive York Springs (Adams County, ~25 min)?** Yes → add it to the profile's service area and drop it from `OUT_OF_AREA`. No → `deploy/retire_out_of_area.py --apply`. Either is fine; today's state is a page claiming Adams County under a York County breadcrumb. | carried | — |

## Divine — needs the droplet

Item 0 above comes first. These are the rest.

| # | Item | Open | Where |
| --- | --- | --- | --- |
| 7 | **Read two inboxes.** (a) Ask Eric whether his morning NEMO report arrived on each of 10-13 → today: `--owner-email` is on both 06:00 cron lines, so it runs all seven days and yields an exact stop date. (b) Your own inbox, Fridays ~06:10 UTC, from the `0 6 * * 5` line. Mail arriving → the run executes and only the snapshot write or the push is broken, nothing lost. Mail stopping on a date → cron or python died that day. | 24 d | — |
| 8 | **`python3 deploy/repair_titles.py`, read the report, then `--apply` — against the docroot, not the repo.** **25 of 45** live titles exceed the 65 characters Google renders, and 3 print the brand twice. Needs no API credit and no `growth/` deploy. Expected effect small and probably unmeasurable at 2.56 visitors/day; what it fixes for certain is 25 truncated titles and three stutters. | 24 d | — |
| 9 | **`deploy/deploy_growth.sh --apply`.** The droplet's engine code dates to 2026-07-27 → 2026-08-04, bracketed by the keys its own snapshot publishes. Until it ships, the morning report claims 7 working techniques where this repo's own `earned()` awards 3, three at a click rate ~30× the real one, and `keywords.ranked`, `gsc.pages` and `code_version` collect nothing. Read the 10-21 scaled-content caution before ranking it above items 1–3. **It no longer blocks the traffic backfill** — the 2026-11-03 run verified the backfill works on both archive naming schemes, so item 0a can be run before this ships. | **93 d** | — |
| 10 | **Anthropic credit + auto-reload under a monthly console cap — still the content blocker, with a softer deadline than this file gave it yesterday.** Both content jobs have written nothing since 10-12 on an empty balance. `BUDGET.md` rule 1 bounds a run to 3–5 calls at cents a day, so a cap enforces that rule rather than relaxing it. **What the credit actually buys, checked in code on 2026-11-03:** not a new page. All four uncovered ice-dam queries route via `_host_page()` to pages that already exist — **`/services/gutter-cleaning-repair.html` (three of the four) and `/services/seamless-gutter-installation.html` (one)** — and **neither mentions "ice dam" at all today**. So this is `strengthen_pages` adding a section to an indexed page, which is the technique that has been failing on the empty balance. Vendor estimates for that mechanism are recrawl 1–14 days and movement 2–8 weeks after, against 8–12 weeks for a new page — so **early December is probably not fatal**, where this file previously stated mid-November as a cliff. Still the only revenue-relevant window before autumn 2027 (T090/T095/T096 hold the lane; the two ice-dam guides ship but do *not* win this routing). **Paired with item 0 — neither half works without the other.** | 24 d | — |
| 11 | **Restore `--email divinejdavis@gmail.com` to the `0 11 * * *` watchdog line** (`deploy/cron-nemo-growth:69`). One flag; `cmd_watchdog` returns early when healthy, so it adds no daily mail. The GitHub alarm says only whether state *arrived*; the watchdog can say *why* it did not. Needs item 9. | 71 d | — |
| 12 | **Allow `nemoseamlessgutter.com` in the cloud environment's network policy.** Cloud-environment menu in the session title bar → Edit → Network access ([docs](https://code.claude.com/docs/en/cloud-environments#network-access)). Today it is a *policy denial*, not a dead host (`403 to CONNECT`, `connect_rejected` in the proxy status, re-confirmed 2026-11-06 11:10:21 UTC). With it, each review can verify the site is up, the phone number is right and the booking widget renders — which nothing in this project currently checks. | 9 d | — |
| 13 | **Merge the green Dependabot PRs, #14 first** (follow-redirects, security). #12 needs the Express 5 / better-sqlite3 majors ported. | carried | — |
| 14 | **`scripts/deploy_web.sh` to ship the 2026-11-05 structured-data fix — bundle it with item 8, one deploy covers both.** Four hand-built guides (`5-vs-6-inch-gutters…`, `gutter-cleaning-cost-york-pa`, `seamless-vs-sectional-gutters`, `signs-your-gutters-need-replacing…`) carried no business NAP node in their JSON-LD; `growth/techniques.py:378` `_provider_ld()` puts one on every *generated* page, so 40 of 44 always had it. Needs no API credit and no `growth/` deploy. **Expected effect small and probably unmeasurable at 2.56 visitors/day** — it is a correctness tidy-up, ranked below items 1–3 deliberately. The test half (`tests/test_site.py`) is already live via `ci.yml` and needs no deploy. | 1 d | T004 |

## Ledger edits the agent would make but will not make unasked

- **Retire T047** ("Coach each review to name the service and the town"). As of
  the 2026-10-28 research it is against Google's solicitation policy, not merely
  weakly evidenced. T007 and T033 cover the safe half of it.
- **Retire T082** (GBP messaging) — carried from earlier entries.
- **Strike T016's Q&A half** (Google retired Q&A) and **T025's FAQPage half**
  (already shipped on 42 of 44 generated pages).

## For whoever reviews this repo next

**The freshness alarm now carries the perishable deadline, so you do not have to
open this file to find it.** As of 2026-11-06 `growth/freshness.py` computes and
prints how many mornings of nginx traffic data are missing, how many are already
past recovery, how many remain, the date after which none of the hole is
recoverable, and the exact `measure --days N` to run — all from the snapshot's
own date, nothing hardcoded. It takes effect on push via `state-freshness.yml`,
needs no deploy, and `growth/test_freshness.py::PerishableTests` pins the
arithmetic (including that the first missing day is the snapshot's own date, not
the day after — an off-by-one three entries made). The ~14-day retention is an
estimate of the packaged logrotate policy and the message says so; one `ls`
replaces it with a fact.

**The review clone is shallow (depth 50), and the 2026-11-05 run walked into
the trap anyway** — `git log` reported `growth/publish_state.sh` as last changed
2026-10-01 by the commit that added the push-time secrets/test gate, eleven days
before the outage. After `git fetch --unshallow` (287 commits, not 50) its real
last change is 2026-07-27. Run the unshallow *first*. `git log -S` dates everything older
than `.git/shallow` *to* the boundary, which made three entries report the
engine deploy gap as 27 days when it is 87. Run `git fetch --unshallow` before
any "this entered in commit X" claim. Full writeup:
[`README.md`](README.md#dating-the-deploy-from-the-repo-side--and-the-shallow-clone-trap).

**`WebFetch` fails DNS on every host from the review session**, so citations in
recent entries are search-engine summaries of pages that could not be opened —
including Google's own review policy. Item 12 fixes this for
`nemoseamlessgutter.com` only.

**The prompt driving the review agent is wrong in six places** and has been for
weeks; the corrections are listed in the 2026-10-27 entry, and the 2026-11-03
entry adds that its Search-Console example figures (77 rows, 3 clicks, avg
position 12.4, "2 of 50 in the top 3") are the 2026-07-28 window, not current:
the file now reads 759 rows, 11 clicks, position 26.1 and **top3 0 of 239**. The two that cause
real misreading: it says the engine "pushes its state to this repo an hour
before you run" (false on twenty-four consecutive mornings — check for a publish
commit dated today before trusting `snapshot.json`), and its Known-blockers
section describes a self-imposed spend cap that cleared on 2026-08-01, when
every measured API failure since has been an empty credit balance.

## Standing rules this list obeys

No fake, incentivised or **content-coached** reviews, no review gating, no
on-premises pressure or review kiosks, no bought links, no doorway pages, no
scraped or AI-spun filler, no unsolicited bulk email or SMS, and nothing
outside the terms of Google, Bing, Yelp, Nextdoor or Meta. A Business Profile
suspension would cost more than any tactic here could earn.

Three GBP-specific limits from the 2026-10-06 policy rewrite, which the ledger
must obey: **in the listing** — no time-limited deals, no prices, no direct
calls-to-action; **in Posts** — no email addresses, no phone numbers, no social
links, no links to unrelated sites. T036, T052 and T024 violate it as written
(their *site-page* halves are unaffected); T008 survives with a constraint.

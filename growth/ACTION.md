# Open items — what is waiting on a human

**Rewritten in full by the review agent on every run. Generated 2026-10-26.**
If the date above is not roughly today's, this file is stale and
[`JOURNAL.md`](JOURNAL.md)'s last entry wins. Nothing here is a decision; every
line is a recommendation Eric or Divine can accept or reject.

Why this file exists: `JOURNAL.md` is append-only and 2.7 MB. That is correct
for a decision log — it shows what was believed at the time — but it means the
*current* ask is buried under ninety entries. Items 1–3 below are free, take
five minutes each, need nobody's permission, and the oldest has been open for
**91 days**.

**It is 26 October.** The back half of leaf-fall is the three weeks this
business's year turns on and about two and a half weeks of it are left. Items
1–4 are the only ones that can earn revenue inside that window; everything
below item 5 pays off in 2027.

## Eric — needs a login, no code, no cost

| # | Item | Open | Where |
| --- | --- | --- | --- |
| 1 | **Business Profile → Performance → write down the `Calls` number.** Note the date range used. **New:** that report is a rolling ~six-month window, so the summer baseline starts expiring around January 2027 — waiting now costs data permanently. | 79 d | T049 |
| 2 | **Business Profile audit, primary category FIRST.** Most specific *true* gutter category; then hours, services detail, photos, pending suggested edits, review replies. **Do not touch the business name** — keyword-stuffing it risks suspension and "NEMO Seamless Gutter" already carries the service term. | 91 d | T016 |
| 3 | **Ask every finished job for a Google review, out loud, 1–2 a month, not in a burst.** Ask them to say *what work was done and in which town*. No gating, no incentive — either would risk the profile. Review signals are ~20% of local-pack weight; "sustained influx over bursts" and "reviews with text" are the ranked factors. Leaf-fall means there are customers to ask *now*. | 91 d | T007, T047 |
| 4 | **Link GA4 to the Business Profile: GA4 → Admin → Product links → Google Business Profile links → Link.** One-time, ~5 min, needs one account holding both GBP and GA4 admin. Puts the profile's `calls` metric beside the site's `call_taps`, which `growth/metrics.py` provably cannot see — so item 1 stops needing a monthly login. Six-month window in GA4; not usable in explorations. | **NEW** | research 2026-10-26 |
| 5 | **Three real gutter-cleaning prices.** `guides/gutter-cleaning-cost-york-pa.html` promises "Typical price ranges" and prints no dollar figures. The agent will not invent them. | carried | — |
| 6 | **Will you drive York Springs (Adams County, ~25 min)?** Yes → add it to the profile's service area and drop it from `OUT_OF_AREA`. No → `deploy/retire_out_of_area.py --apply`. Either is fine; today's state is a page claiming Adams County under a York County breadcrumb. | carried | — |

## Divine — needs the droplet

| # | Item | Open | Where |
| --- | --- | --- | --- |
| 7 | **End the publish outage.** Three greps and one `cat`, ~10 min — the branch table is in [`README.md`](README.md#when-no-publish-commit-arrives). | **14 missed mornings** | — |
| 8 | **Read two inboxes.** (a) Ask Eric whether his morning NEMO report arrived on each of 10-13 → today: `--owner-email` is on both 06:00 cron lines, so it runs all seven days and yields an exact stop date. (b) Your own inbox, Fridays ~06:10 UTC, from the `0 6 * * 5` line. | 14 d | — |
| 9 | **`python3 deploy/repair_titles.py`, read the report, then `--apply` — against the docroot, not the repo.** 25 of 44 live titles exceed the 65 characters Google renders; three print the brand twice. Needs no API credit and no `growth/` deploy. Expected effect small and probably unmeasurable at 2.6 visitors/day. | 13 d | — |
| 10 | **`deploy/deploy_growth.sh --apply`. Re-dated 2026-10-26: this is 82 days outstanding, not 27.** The droplet's engine code dates to 2026-07-27 → 2026-08-04, bracketed by the keys its own snapshot publishes. The old "last verified deploy 09-27" figure was `deploy_web.sh` evidence (sitemap lastmods) that never covered `growth/*.py`. Until it ships, the morning report claims 7 working techniques where this repo's own `earned()` awards 3, three at a click rate ~30× the real one. Read the 10-21 scaled-content caution before ranking it above items 1–4. | **82 d** | — |
| 11 | **Anthropic credit + auto-reload under a monthly console cap.** Both content jobs have written nothing since 10-12. `BUDGET.md` rule 1 bounds a run to 3–5 calls at cents a day, so a cap enforces that rule rather than relaxing it. | 14 d | — |
| 12 | **Restore `--email divinejdavis@gmail.com` to the `0 11 * * *` watchdog line** (`deploy/cron-nemo-growth:69`). One flag; `cmd_watchdog` returns early when healthy, so it adds no daily mail. Needs item 10. | 60 d | — |
| 13 | **Merge the green Dependabot PRs, #14 first** (follow-redirects, security). #12 needs the Express 5 / better-sqlite3 majors ported. | carried | — |

## For whoever reviews this repo next

**The review clone is shallow (depth 50).** `git log -S` dates everything older
than `.git/shallow` *to* the boundary, which made three entries report the
engine deploy gap as 27 days when it is 82. Run `git fetch --unshallow` before
any "this entered in commit X" claim. Full writeup:
[`README.md`](README.md#dating-the-deploy-from-the-repo-side--and-the-shallow-clone-trap).

## Standing rules this list obeys

No fake or incentivised reviews, no review gating, no bought links, no doorway
pages, no scraped or AI-spun filler, no unsolicited bulk email or SMS, and
nothing outside the terms of Google, Bing, Yelp, Nextdoor or Meta. A Business
Profile suspension would cost more than any tactic here could earn.

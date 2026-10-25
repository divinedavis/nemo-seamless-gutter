# Open items — what is waiting on a human

**Rewritten in full by the review agent on every run. Generated 2026-10-25.**
If the date above is not roughly today's, this file is stale and
[`JOURNAL.md`](JOURNAL.md)'s last entry wins. Nothing here is a decision; every
line is a recommendation Eric or Divine can accept or reject.

Why this file exists: `JOURNAL.md` is append-only and 2.6 MB. That is correct
for a decision log — it shows what was believed at the time — but it means the
*current* ask is buried under ninety entries. Item 2 below is free, takes five
minutes, needs nobody's permission, and has been open for **90 days**.

## Eric — needs a login, no code, no cost

| # | Item | Open | Where |
| --- | --- | --- | --- |
| 1 | **Business Profile → Performance → write down the `Calls` number.** Note the date range used. | 78 d | T049 |
| 2 | **Business Profile audit, primary category FIRST.** Most specific *true* gutter category; then hours, services detail, photos, pending suggested edits, review replies. **Do not touch the business name** — keyword-stuffing it risks suspension and "NEMO Seamless Gutter" already carries the service term. | 90 d | T016 |
| 3 | **Ask every finished job for a Google review, out loud, 1–2 a month, not in a burst.** Ask them to say *what work was done and in which town*. No gating, no incentive — either would risk the profile. Review signals are ~20% of local-pack weight and "sustained influx over bursts" and "reviews with text" are the ranked factors. Leaf-fall means there are customers to ask *now*. | 90 d | T007, T047 |
| 4 | **Three real gutter-cleaning prices.** `guides/gutter-cleaning-cost-york-pa.html` promises "Typical price ranges" and prints no dollar figures. The agent will not invent them. | carried | — |
| 5 | **Will you drive York Springs (Adams County, ~25 min)?** Yes → add it to the profile's service area and drop it from `OUT_OF_AREA`. No → `deploy/retire_out_of_area.py --apply`. Either is fine; today's state is a page claiming Adams County under a York County breadcrumb. | carried | — |

## Divine — needs the droplet

| # | Item | Open | Where |
| --- | --- | --- | --- |
| 6 | **End the publish outage.** Three greps and one `cat`, ~10 min — the branch table is in [`README.md`](README.md#when-no-publish-commit-arrives). | 13 missed mornings | — |
| 7 | **Read two inboxes.** (a) Ask Eric whether his morning NEMO report arrived on each of 10-13 → today: `--owner-email` is on both 06:00 cron lines, so it runs all seven days and yields an exact stop date. (b) Your own inbox, Fridays ~06:10 UTC, from the `0 6 * * 5` line. | 13 d | — |
| 8 | **`python3 deploy/repair_titles.py`, read the report, then `--apply` — against the docroot, not the repo.** 25 of 44 live titles exceed the 65 characters Google renders; three print the brand twice. Needs no API credit and no `growth/` deploy. Expected effect small and probably unmeasurable at 2.6 visitors/day. | 12 d | — |
| 9 | **`deploy/deploy_growth.sh --apply`.** Last verified deploy 2026-09-27; first undeployed commit `098c2cc`, 2026-09-28. Until it ships the morning report claims 7 working techniques where this repo's own `earned()` awards 3, three of them at a click rate ~30× the real one. Read the 10-21 scaled-content caution before ranking it above items 1–3. | 27 d | — |
| 10 | **Anthropic credit + auto-reload under a monthly console cap.** Both content jobs have written nothing since 10-12. `BUDGET.md` rule 1 bounds a run to 3–5 calls at cents a day, so a cap enforces that rule rather than relaxing it. | 13 d | — |
| 11 | **Restore `--email divinejdavis@gmail.com` to the `0 11 * * *` watchdog line** (`deploy/cron-nemo-growth:69`). One flag; `cmd_watchdog` returns early when healthy, so it adds no daily mail. Needs item 9. | 59 d | — |
| 12 | **Merge the green Dependabot PRs, #14 first** (follow-redirects, security). #12 needs the Express 5 / better-sqlite3 majors ported. | carried | — |

## Standing rules this list obeys

No fake or incentivised reviews, no review gating, no bought links, no doorway
pages, no scraped or AI-spun filler, no unsolicited bulk email or SMS, and
nothing outside the terms of Google, Bing, Yelp, Nextdoor or Meta. A Business
Profile suspension would cost more than any tactic here could earn.

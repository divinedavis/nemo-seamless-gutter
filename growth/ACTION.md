# Open items — what is waiting on a human

**Rewritten in full by the review agent on every run. Generated 2026-10-27.**
If the date above is not roughly today's, this file is stale and
[`JOURNAL.md`](JOURNAL.md)'s last entry wins. Nothing here is a decision; every
line is a recommendation Eric or Divine can accept or reject.

Why this file exists: `JOURNAL.md` is append-only and 2.7 MB. That is correct
for a decision log — it shows what was believed at the time — but it means the
*current* ask is buried under ninety-odd entries. Items 1–3 below are free,
take five minutes each, need nobody's permission, and the oldest has been open
for **92 days**.

**It is 27 October.** Leaf-fall has roughly a week and a half left in it. Items
1–4 are the only ones that can earn revenue inside that window; everything
below item 5 pays off in 2027.

**The engine has published nothing for fifteen mornings** (last publish
`0b2c596`, 2026-10-12 06:05 UTC). Item 5 is the whole reason the rest of this
project is flying blind. The GitHub freshness alarm has now gone red on six
consecutive scheduled runs, 10-21 through 10-26, each notification addressed to
Divine.

## Eric — needs a login, no code, no cost

| # | Item | Open | Where |
| --- | --- | --- | --- |
| 1 | **Business Profile → Performance → write down the `Calls` number.** Note the date range used. That report is a rolling ~six-month window, so the summer baseline starts expiring around January 2027 — waiting costs data permanently. | 80 d | T049 |
| 2 | **Business Profile audit, primary category FIRST.** Most specific *true* gutter category; then hours, services detail, photos, pending suggested edits, review replies. **Do not touch the business name** — keyword-stuffing it risks suspension, and "NEMO Seamless Gutter" already carries the service term. (T016's Q&A half is dead — Google retired Q&A; the category half is not.) | 92 d | T016 |
| 3 | **Ask every finished job for an honest Google review — and reply to the 13 you already have.** **CHANGED 10-27:** do *not* ask customers to mention the service or the town. Google's solicitation rule allows asking for a genuine experience and disallows requesting specific content, and the relevance gain that wording was chasing rests on one practitioner's assertion — not worth the profile. Ask for a review, not for words: no incentive, no gating, no pressure in the driveway; a follow-up text or email with a plain link is the safe form, 1–2 a month, every month. **Then get the service and town onto the profile in your own voice:** reply under each of the 13 reviews naming what the work was and which town, non-defensive on the low ones. An owner's reply is his own content in a field Google provides for it, so no solicitation rule touches it. | 92 d / 85 d | T007, T033 |
| 4 | **Link GA4 to the Business Profile: GA4 → Admin → Product links → Google Business Profile links → Link.** One-time, ~5 min, needs one account holding both GBP and GA4 admin. Puts the profile's `calls` metric beside the site's `call_taps`, which `growth/metrics.py` provably cannot see — so item 1 stops needing a monthly login. | 1 d | research 2026-10-26 |
| 5 | **Three real gutter-cleaning prices.** `guides/gutter-cleaning-cost-york-pa.html` promises "Typical price ranges" and prints no dollar figures. The agent will not invent them. | carried | — |
| 6 | **Will you drive York Springs (Adams County, ~25 min)?** Yes → add it to the profile's service area and drop it from `OUT_OF_AREA`. No → `deploy/retire_out_of_area.py --apply`. Either is fine; today's state is a page claiming Adams County under a York County breadcrumb. | carried | — |

## Divine — needs the droplet

| # | Item | Open | Where |
| --- | --- | --- | --- |
| 7 | **End the publish outage.** Three greps and one `cat`, ~10 min — the branch table is in [`README.md`](README.md#when-no-publish-commit-arrives). | **15 missed mornings** | — |
| 8 | **Read two inboxes.** (a) Ask Eric whether his morning NEMO report arrived on each of 10-13 → today: `--owner-email` is on both 06:00 cron lines, so it runs all seven days and yields an exact stop date. (b) Your own inbox, Fridays ~06:10 UTC, from the `0 6 * * 5` line. | 15 d | — |
| 9 | **`python3 deploy/repair_titles.py`, read the report, then `--apply` — against the docroot, not the repo.** Re-counted 10-27: **25 of 45** live titles exceed the 65 characters Google renders, and 3 print the brand twice. Needs no API credit and no `growth/` deploy. Expected effect small and probably unmeasurable at 2.56 visitors/day. | 14 d | — |
| 10 | **`deploy/deploy_growth.sh --apply`.** The droplet's engine code dates to 2026-07-27 → 2026-08-04, bracketed by the keys its own snapshot publishes. Until it ships, the morning report claims 7 working techniques where this repo's own `earned()` awards 3, three at a click rate ~30× the real one, and `keywords.ranked`, `gsc.pages` and `code_version` collect nothing. Read the 10-21 scaled-content caution before ranking it above items 1–3. | **83 d** | — |
| 11 | **Anthropic credit + auto-reload under a monthly console cap.** Both content jobs have written nothing since 10-12. `BUDGET.md` rule 1 bounds a run to 3–5 calls at cents a day, so a cap enforces that rule rather than relaxing it. | 15 d | — |
| 12 | **Restore `--email divinejdavis@gmail.com` to the `0 11 * * *` watchdog line** (`deploy/cron-nemo-growth:69`). One flag; `cmd_watchdog` returns early when healthy, so it adds no daily mail. Needs item 10. | 61 d | — |
| 13 | **Allow `nemoseamlessgutter.com` in the cloud environment's network policy.** Cloud-environment menu in the session title bar → Edit → Network access ([docs](https://code.claude.com/docs/en/cloud-environments#network-access)). Today it is a *policy denial*, not a dead host (`403 to CONNECT`, `connect_rejected` in the proxy status). With it, each review can verify the site is up, the phone number is right and the booking widget renders — which nothing in this project currently checks. | **NEW** | — |
| 14 | **Merge the green Dependabot PRs, #14 first** (follow-redirects, security). #12 needs the Express 5 / better-sqlite3 majors ported. | carried | — |

## For whoever reviews this repo next

**The review clone is shallow (depth 50).** `git log -S` dates everything older
than `.git/shallow` *to* the boundary, which made three entries report the
engine deploy gap as 27 days when it is 83. Run `git fetch --unshallow` before
any "this entered in commit X" claim. Full writeup:
[`README.md`](README.md#dating-the-deploy-from-the-repo-side--and-the-shallow-clone-trap).

**`WebFetch` fails DNS on every host from the review session**, so citations in
recent entries are search-engine summaries of pages that could not be opened.
Item 13 fixes this for `nemoseamlessgutter.com` only.

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

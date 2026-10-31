# Open items — what is waiting on a human

**Rewritten by the review agent on every run. Generated 2026-10-31.**
If the date above is not roughly today's, this file is stale and
[`JOURNAL.md`](JOURNAL.md)'s last entry wins. Nothing here is a decision; every
line is a recommendation Eric or Divine can accept or reject. The 2026-10-31
run changed counters and ages, corrected the two lines that said nothing here
earns revenue before 2027, and coupled item 10 to item 0 with a deadline.

Why this file exists: `JOURNAL.md` is append-only and 2.8 MB. That is correct
for a decision log — it shows what was believed at the time — but it means the
*current* ask is buried under ninety-odd entries. Items 1–3 below are free,
take five minutes each, need nobody's permission, and the oldest has been open
for **96 days**.

**It is 31 October, leaf-fall is over, and there is about two weeks left on the
next window.** The autumn spike passed end to end with the engine dead. But
**ice-dam season (Jan–Feb) is the second spike**, and vendor estimates put a
long-tail local page at roughly 8–12 weeks from publish to useful rank — so
pages written by **mid-November** can rank for it, and pages written after
cannot. Earlier versions of this file said "nothing here earns revenue before
2027" and that the API credit "funds 2027". That was wrong in the one direction
that matters: it advised the delay that would have made it true. See the
2026-10-31 journal entry for the sourcing and the caveats, which are real —
these are vendor timings, not Google's, and the lane needs a snowy winter.

---

## Item 0 — the one that blocks everything else

**The engine has published nothing for nineteen mornings** (last publish
`0b2c596`, 2026-10-12 06:05 UTC). Every number this project reports is 461
hours old. The GitHub freshness alarm has gone red on **ten consecutive
scheduled runs**, 10-21 through 10-30, each notification addressed to Divine.

**This and item 10 are now one decision with a deadline.** Neither half works
alone: credit buys nothing while cron publishes nothing, and a repaired cron
writes nothing on an empty balance. Both inside ~2 weeks and the winter lane is
live; either one missed and the system idles until autumn 2027.

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

**Cadence recommendation, 2026-10-30, still unactioned on 10-31:** the review
agent has recommended that this daily review drop to **weekly** until a publish
commit lands — seven entries have now re-read the same 19-day-old file. The
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
| 1 | **Business Profile → Performance → write down the `Calls` number.** Note the date range used. That report is a rolling ~six-month window, so the summer baseline starts expiring around January 2027 — waiting costs data permanently. | 84 d | T049 |
| 2 | **Business Profile audit, primary category FIRST.** Most specific *true* gutter category; then hours, services detail, photos, pending suggested edits, review replies. **Do not touch the business name** — keyword-stuffing it risks suspension, and "NEMO Seamless Gutter" already carries the service term. (T016's Q&A half is dead — Google retired Q&A; the category half is not.) | 96 d | T016 |
| 3 | **Ask every finished job for an honest Google review — and reply to the 13 you already have.** Do *not* ask customers to mention the service or the town. Google's allowance lets a merchant "solicit or encourage the posting of content that does represent a genuine experience, **without offering incentives to do so or attempting to influence the rating or the contents of the review**" — that last clause is general, is about the merchant himself, and predates the April 2026 staff-quota clauses, so coaching the wording is out. Ask for a review, not for words: no incentive, no gating, no pressure in the driveway; a follow-up text or email with a plain link is the safe form, 1–2 a month, every month. **Then get the service and town onto the profile in your own voice:** reply under each of the 13 reviews naming what the work was and which town, non-defensive on the low ones. An owner's reply is his own content in a field Google provides for it, so no solicitation rule touches it. | 96 d / 89 d | T007, T033 |
| 4 | **Link GA4 to the Business Profile: GA4 → Admin → Product links → Google Business Profile links → Link.** One-time, ~5 min, needs one account holding both GBP and GA4 admin. Puts the profile's `calls` metric beside the site's `call_taps`, which `growth/metrics.py` provably cannot see — so item 1 stops needing a monthly login. | 5 d | research 2026-10-26 |
| 5 | **Three real gutter-cleaning prices.** `guides/gutter-cleaning-cost-york-pa.html` promises "Typical price ranges" and prints no dollar figures. The agent will not invent them. | carried | — |
| 6 | **Will you drive York Springs (Adams County, ~25 min)?** Yes → add it to the profile's service area and drop it from `OUT_OF_AREA`. No → `deploy/retire_out_of_area.py --apply`. Either is fine; today's state is a page claiming Adams County under a York County breadcrumb. | carried | — |

## Divine — needs the droplet

Item 0 above comes first. These are the rest.

| # | Item | Open | Where |
| --- | --- | --- | --- |
| 7 | **Read two inboxes.** (a) Ask Eric whether his morning NEMO report arrived on each of 10-13 → today: `--owner-email` is on both 06:00 cron lines, so it runs all seven days and yields an exact stop date. (b) Your own inbox, Fridays ~06:10 UTC, from the `0 6 * * 5` line. Mail arriving → the run executes and only the snapshot write or the push is broken, nothing lost. Mail stopping on a date → cron or python died that day. | 19 d | — |
| 8 | **`python3 deploy/repair_titles.py`, read the report, then `--apply` — against the docroot, not the repo.** **25 of 45** live titles exceed the 65 characters Google renders, and 3 print the brand twice. Needs no API credit and no `growth/` deploy. Expected effect small and probably unmeasurable at 2.56 visitors/day; what it fixes for certain is 25 truncated titles and three stutters. | 18 d | — |
| 9 | **`deploy/deploy_growth.sh --apply`.** The droplet's engine code dates to 2026-07-27 → 2026-08-04, bracketed by the keys its own snapshot publishes. Until it ships, the morning report claims 7 working techniques where this repo's own `earned()` awards 3, three at a click rate ~30× the real one, and `keywords.ranked`, `gsc.pages` and `code_version` collect nothing. Read the 10-21 scaled-content caution before ranking it above items 1–3. | **87 d** | — |
| 10 | **Anthropic credit + auto-reload under a monthly console cap — and it is now time-critical, not 2027 planning.** Both content jobs have written nothing since 10-12 on an empty balance. `BUDGET.md` rule 1 bounds a run to 3–5 calls at cents a day, so a cap enforces that rule rather than relaxing it. **Deadline ~mid-November:** at 8–12 weeks publish-to-rank, pages funded now can rank for Jan–Feb ice-dam demand (T090/T095/T096, already in the ledger; `guides/ice-dams-gutters-pennsylvania.html` and `guides/ice-dam-removal-york-pa.html` already ship). Funded later, they cannot, and the next window is autumn 2027. **Paired with item 0 — neither half works without the other.** | 19 d | — |
| 11 | **Restore `--email divinejdavis@gmail.com` to the `0 11 * * *` watchdog line** (`deploy/cron-nemo-growth:69`). One flag; `cmd_watchdog` returns early when healthy, so it adds no daily mail. The GitHub alarm says only whether state *arrived*; the watchdog can say *why* it did not. Needs item 9. | 65 d | — |
| 12 | **Allow `nemoseamlessgutter.com` in the cloud environment's network policy.** Cloud-environment menu in the session title bar → Edit → Network access ([docs](https://code.claude.com/docs/en/cloud-environments#network-access)). Today it is a *policy denial*, not a dead host (`403 to CONNECT`, `connect_rejected` in the proxy status, re-confirmed 2026-10-31 11:10:59 UTC). With it, each review can verify the site is up, the phone number is right and the booking widget renders — which nothing in this project currently checks. | 5 d | — |
| 13 | **Merge the green Dependabot PRs, #14 first** (follow-redirects, security). #12 needs the Express 5 / better-sqlite3 majors ported. | carried | — |

## Ledger edits the agent would make but will not make unasked

- **Retire T047** ("Coach each review to name the service and the town"). As of
  the 2026-10-28 research it is against Google's solicitation policy, not merely
  weakly evidenced. T007 and T033 cover the safe half of it.
- **Retire T082** (GBP messaging) — carried from earlier entries.
- **Strike T016's Q&A half** (Google retired Q&A) and **T025's FAQPage half**
  (already shipped on 42 of 44 generated pages).

## For whoever reviews this repo next

**The review clone is shallow (depth 50).** `git log -S` dates everything older
than `.git/shallow` *to* the boundary, which made three entries report the
engine deploy gap as 27 days when it is 87. Run `git fetch --unshallow` before
any "this entered in commit X" claim. Full writeup:
[`README.md`](README.md#dating-the-deploy-from-the-repo-side--and-the-shallow-clone-trap).

**`WebFetch` fails DNS on every host from the review session**, so citations in
recent entries are search-engine summaries of pages that could not be opened —
including Google's own review policy. Item 12 fixes this for
`nemoseamlessgutter.com` only.

**The prompt driving the review agent is wrong in six places** and has been for
weeks; the corrections are listed in the 2026-10-27 entry. The two that cause
real misreading: it says the engine "pushes its state to this repo an hour
before you run" (false on eighteen consecutive mornings — check for a publish
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

# Growth journal

Append-only. Never edit or delete a prior entry — the value of this file is
seeing what was believed at the time, including when that turned out wrong.

## 2026-07-27 — review agent

### Where the numbers stand

This is the engine's first day, so there is no trend to report yet, only a
starting line.

- **Goal (>50% of tracked York County queries at top-3):** `measured: false`.
  Search Console is not connected, so there is no rank data — `share_pct` is
  `null`. The only number available is *coverage* (does a page exist that
  targets the query), which sits at **63.8%** (30/47 tracked queries have a
  matching page). This is not progress toward the goal and should not be read
  as such — a page existing says nothing about whether it ranks. Worth
  repeating because it is the easiest number on this page to misread as good
  news.
- **Traffic:** `visitors`, `organic_visitors`, `local_visitors`, `bookings`,
  `phone_leads` are all **0** for both measured days (2026-07-25, 07-26).
  Lifetime totals (from before this engine existed) show 2 bookings and 10
  phone leads ever, so leads do happen on this site — the 2-day window is
  just too short and too small a business to show a signal either way. This
  is unmeasured-in-effect, not "zero performance."
- **Keyword coverage by intent:** hire-intent 26/31 covered, but price-intent
  only 2/6 and DIY/informational only 1/6 and 1/4. The uncovered list is
  mostly cost and "do I need this" questions — exactly the queries T002
  (money pages) exists to close, and exactly the queries that failed to
  generate today (see below).

### Did previous changes work?

There is no prior journal entry to check — this is the first one. So instead
of a false "too early to tell," here is what should have been checked before
today and now must wait for the next entry: **did T001 (area pages) and T002
(money pages) actually produce any owned_visitors once pages exist and have
had time to index?** Nothing to compare yet, but I am putting the trigger on
record: check `owned_visitors` on T001/T002 no sooner than ~3 weeks from
their `activated` date (2026-07-27), because indexing lag alone can eat that
long.

**One thing did already fail, on day one, and it needs to lead this entry
rather than hide in a table:** the engine's `build` and `scout` steps for
today both failed with the same error —

> `Your credit balance is too low to access the Anthropic API. Please go to
> Plans & Billing to upgrade or purchase credits.`

Concretely, today's run:
- Failed to write the area page for Shrewsbury (T001).
- Failed to write the money page for "how much do seamless gutters cost"
  (T002) — one of the highest-intent uncovered queries on the whole list.
- Failed to scout for any new technique ideas at all.
- Still succeeded at the free/local steps: link mesh, schema check, sitemap
  rebuild (15 URLs), IndexNow (nothing new to submit, consistent with 0 pages
  written).

So three of the ten techniques in the ledger — the two content techniques
that do the actual work of building the query moat, plus the discovery step
that finds new ideas — produced **nothing** on their first scheduled day.
This is not a one-off blip to shrug off: if the Anthropic account's balance
is at zero rather than just low, it will keep failing silently (well, loudly
in the log, but nobody reads that unless prompted) every single day until
someone adds funds. A month of "0 new, 0 changed" builds is a month closer to
autumn leaf-fall season with no additional coverage to show for it.

### What I researched today

Since the automated scout couldn't run (same credit failure), I ran the
research pass by hand.

- **Local Pack ranking weights, 2026.** GBP signals carry roughly the
  largest share of local ranking weight (~32%), ahead of on-page (~19%),
  reviews (~16%), links (~15%), behavioral (~8%), and citations (~7%).
  Review *recency* is called out specifically — Whitespark's Darren Shaw
  ranks it in his top 5, and a large share of users filter to reviews from
  the last 3 months. ([BrightLocal](https://www.brightlocal.com/learn/google-local-algorithm-and-ranking-factors/), [ClickRank](https://www.clickrank.ai/local-seo-ranking-factors/))
- **Gutter-specific data point.** Gutter companies with 50+ reviews are
  reported to rank 3-4x higher in the Map Pack than companies under 20. The
  Business Profile here has 13. That is a wide enough gap to matter, not
  noise. Also recommended: dedicated per-city and per-service pages (already
  T001's approach), and weekly GBP project-photo posts.
  ([Kelly WM — Gutter SEO](https://kellywm.com/blog/gutters-seo), [Home Service Direct](https://www.homeservicedirect.net/complete-seo-guide-gutter-companies/))
- **AI answer engines (AEO).** Getting cited by ChatGPT/Gemini/Perplexity for
  local trade queries currently leans on: FAQ content with FAQ-style
  structured data that's easy for a model to extract and quote, and genuine
  (not bulk/spun) presence in places these models pull from, like answering
  real questions on Reddit/Nextdoor threads. One survey cited only 1.2% of
  local businesses currently get recommended by AI at all — low bar, low
  competition. ([Evolve — Local Business AI Search 2026 Playbook](https://evolveamz.com/local-business-ai-search-guide/))

**What I rejected and why:**
- Anything from AEO-agency marketing pages that amounted to "buy AEO
  services" or third-party citation-farming tools — not something a one-owner
  business needs to pay a vendor for when the same effect (FAQ schema, honest
  answers) is achievable in the existing templates.
- Citation submission automation beyond what's already scoped as T009 — nothing
  new surfaced that beats the existing candidate.
- Nothing found today argues for retiring any active technique or contradicts
  a hypothesis already on record.

### Recommendations

1. **Fix the Anthropic billing balance.** *(Needs Eric/owner — this is a
   money and account-access action outside repo scope.)* Every day this stays
   unresolved, T001 and T002 write nothing and the scout finds nothing. This
   is not a growth idea, it's the thing blocking every growth idea that costs
   nothing else to fix. How you'd know it worked: tomorrow's `last_build.log`
   shows `ok: true` for `area_pages` and `money_pages` instead of the 400
   error, and `snapshot.json.last_build.new` is 1 instead of 0.

2. **Connect Search Console (activate T010).** *(Needs Eric — a Google Cloud
   service account and read grant on the GSC property, ~15 minutes,
   one-time, no ongoing cost.)* Right now the stated goal — >50% top-3 — is
   structurally unmeasurable. Coverage (63.8%) will keep climbing regardless
   of whether anything actually ranks, and every future journal entry has to
   keep repeating the same caveat until this exists. This is the single
   highest-leverage fix available this week because it turns every other
   recommendation from a guess into something checkable.

3. **Say yes to the review-request engine (activate T007).** *(Needs Eric's
   explicit go-ahead — it emails real past customers.)* Research today
   reinforces the ledger's own hypothesis with a number: 13 reviews vs. a
   reported 50+ for top-ranking competitors, and review recency specifically
   named as a top-5 local ranking factor for 2026. This only asks customers
   who already had a completed job — not incentivized, not gated, compliant
   with GBP terms. Expected effect: review count/recency climb over 1-2
   months; watch GBP review count directly (not in this snapshot yet) and
   `local_visitors` afterward. Effort: zero build cost, the code path already
   exists per the ledger note — it just needs the switch flipped.

4. **Don't wait on GBP API/OAuth for T008 — post manually, starting this
   week.** *(Needs Eric, ~5 minutes/week, no engine change required.)* T008 is
   stuck on OAuth access before the *engine* can post, but GBP signals are
   reportedly the single heaviest local-ranking bucket (~32%), and Eric can
   post a project photo and one line of text from the Business Profile app
   himself today without waiting on any API work. This decouples getting the
   SEO benefit from getting the automation built — do the manual version now,
   automate later if it's worth the OAuth setup.

5. **Lower priority for now: citations (T009).** Still a valid candidate —
   citation signals are real but the smallest of the five weighted buckets
   (~7%) — so it shouldn't jump ahead of #1-4 above. No action needed this
   week.

6. **New idea for the ledger, not yet a formal candidate:** add FAQPage
   structured data to the guide pages (T002's output) so that the same
   cost/buying-guide content that's meant to win the search click is also
   easy for an AI answer engine to lift and cite directly. This is a small,
   free, on-site template change with no ongoing cost — I'm flagging it here
   rather than touching `techniques.json` myself, since that file is
   droplet-owned runtime state. Whoever runs the next `seed`/scout pass with
   working credits should consider filing it as a formal candidate.

### Reasoning and uncertainties

I'm treating "0 traffic, 0 leads" for the two measured days as *unmeasured*,
not as evidence the site gets no traffic — two days is nothing for a
one-owner local business, and the lifetime totals (2 bookings, 10 phone
leads ever) prove leads do occasionally happen. I'd change my mind about that
read if a few more weeks pass and the daily series is still flat zero across
the board — at that point it stops being "too short a window" and starts
being either a real traffic problem or a measurement bug (e.g., the access
log filtering out real visits along with bots/Eric's IP), and it would be
worth someone checking the nginx log directly on the droplet.

I'm not able to tell from this repo alone whether the Anthropic credit
failure is a one-time dip or a recurring pattern — if it turns out the
account has hit this same wall before (this is outside what's visible from
the repo), the fix isn't "add more credits" but "set a top-up or higher
limit so this doesn't repeat every few weeks."

I did not activate anything, spend anything, or edit `techniques.json`,
`keywords.json`, `results.jsonl`, or `state.json` — all of that is
droplet-owned and outside this review's authority. The FAQ-schema idea above
is a suggestion for the next scout/build cycle, not something I implemented.

# Growth journal

Append-only record of what the growth engine and the daily review
agent did, why, and whether it worked. Newest entries at the bottom.
Nothing here is ever edited after the fact — a decision log is only
worth reading if it still shows what was believed at the time.

## 2026-07-27 — engine run

Goal: **unmeasured** (no Search Console). Coverage proxy 63.8% of 47 tracked queries.
Yesterday: 0 visitors (0 organic, 0 maps) · 0 bookings, 0 phone leads.

**Built:**
- `area_pages` — FAILED: content generation failed for Shrewsbury: anthropic 400: {"type":"error","error":{"type":"invalid_request_error","message":"Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits."},"request_id":"req_011CdS3x4PSB3Wtz7xUXJh6d"}
- `money_pages` — FAILED: content generation failed for 'how much do seamless gutters cost': anthropic 400: {"type":"error","error":{"type":"invalid_request_error","message":"Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits."},"request_id":"req_011CdS3x5LjpLoFvfSFg5E3V"}
- `internal_links` — ok: refreshed nearby-links on 0 page(s)
- `local_schema` — ok: LocalBusiness schema already current
- `rebuild_sitemap` — ok: [gen_sitemap] wrote 15 URLs to sitemap.xml
- `ping_indexnow` — ok: nothing new to submit

**Scout did not run:** anthropic 400: {"type":"error","error":{"type":"invalid_request_error","message":"Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits."},"request_id":"req_011CdS3x7VibNpoG43uaMqzT"}

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

## 2026-07-27 — review agent

### Lead with the blocker(s) — there are two, and the second is more important than the first

**Blocker 1 of 2 — journal entries were silently getting deleted, and I found it while doing Step 2.** Before writing anything below, I went looking for "your own previous entries" per this task's instructions and found exactly one: the engine's own same-day build log. That was wrong — `git log` shows a real review-agent entry was committed at `75cd2d9` (2026-07-27T00:33:38Z), with real research and five ranked recommendations. Six hours later the engine's own `93ff2a2` publish (06:00:06Z) overwrote `growth/JOURNAL.md` with the droplet's local copy and that entire entry vanished from the repo — not edited, not superseded, just gone, with no trace in `git log` (the deleting commit is a plain "Publish growth state" commit, nothing about a journal change). Root cause: `growth/snapshot.py`'s `append_journal` writes to the docroot's *local* copy of `JOURNAL.md`, which only ever accumulates this engine's own entries — it has no way to know about commits the cloud review agent pushes straight to GitHub. `publish_state.sh` then did a blind `cp` of that local copy over the GitHub clone on every run, which is a delete-by-omission every single day. This isn't a one-time glitch; it will keep happening on every future 06:00 publish until fixed, which means the append-only decision log this whole task depends on ("read your own previous entries carefully... check whether you previously recommended something and it was never acted on") was silently unable to do that from day one. I've restored the deleted entry verbatim in its correct chronological position above (with an editorial note marking it as recovered — see there), and I've fixed `growth/publish_state.sh` to merge the two files instead of overwriting (new `growth/merge_journal.py`, tested against the actual before/after content from this incident: it reconstructs the entry losslessly). This is a repo-code fix, not a droplet action — it does nothing until the next manual deploy syncs it to the droplet, which needs to happen before the next 06:00 run for the fix to take effect.

One direct benefit of recovering that entry: its recommendation #6 proposed adding FAQPage schema to guide pages. Checking `growth/techniques.py` today (as this task's Step 3b requires) shows `_faq_ld()` is already called by both `area_pages` and `money_pages` and has been since the ledger was seeded — that recommendation was already stale the moment it was written, on day one, before any human even had a chance to act on it. It cost nothing this time because the entry disappeared before it could mislead anyone, but it's a clean real-world example of exactly the trap this task warns about, and a reason to keep doing the code check even when (especially when) a past entry looks confident.

**Blocker 2 of 2 — the Anthropic API account has no credit balance, and it stopped the engine before it wrote a single word of content.** Today's build log shows `area_pages` and `money_pages` both failing with `Your credit balance is too low to access the Anthropic API` — the same failure on `scout`. This is not a partial slowdown: the two techniques that were supposed to close the 36% coverage gap (T001 town pages, T002 cost guides) produced zero pages, and the research step that was supposed to find new candidates didn't run either. Everything that happened today was the mechanical stuff that doesn't call the model: the link mesh, the schema refresh, the sitemap, IndexNow. Until Eric adds credits at console.anthropic.com, this engine is a cron job that touches nothing but its own plumbing. This is the single most important fact in today's report and the first thing that needs to change.

### Where the numbers stand

The goal (`>50% of tracked queries at top-3`) is **unmeasured** — Search Console isn't connected (T010, still a candidate), so there is no rank signal at all, only the coverage proxy: 63.8% of 47 tracked queries have a page that targets them (30/47). Coverage is not rank; a page can exist and still lose to a competitor's page, or lose to the map pack entirely. Take the 63.8% as "content exists," not "winning."

Traffic: 0 visitors, 0 organic, 0 local, 0 AI-referred on both 2026-07-25 and 2026-07-26 — the only two days in the series so far. All-time totals show 2 bookings and 10 phone leads, but neither happened on a day the traffic series covers, so I can't connect any visit to either.

### Did previous changes work?

There is technically one prior entry now that it's been recovered (see above), but it was written the same calendar day this engine first ran, reviewing the same zero-traffic, zero-content starting line I'm looking at now — there is no elapsed time between it and this entry, so there's still no before/after window for any technique. Every technique in the ledger (T001–T010) was added and, where active, activated *today*. The honest answer for day one is: too early to tell, on every single technique, and it will stay too early to tell for weeks even once the API is paid up again — new pages take time to get crawled and longer to rank, and two data points is noise, not a trend.

What I can check is whether the recovered entry's recommendations were acted on in the roughly six hours between it and this one — they were not, which is expected (no human was going to add API credits, connect Search Console, or approve emailing customers for reviews inside a single morning) but worth stating so the pattern is on record from day one: recommendation 1 (add credits) — not done, repeated below as #1. Recommendation 2 (connect GSC) — not done, repeated below. Recommendation 3 (activate T007 review requests) — not done, repeated below. Recommendation 4 (manual GBP posts) — can't tell from this repo whether Eric acted on it; restated below in expanded form (#3) since today's research broadens it beyond posts to full profile completeness. Recommendation 6 (add FAQPage schema) — moot; already shipped in code before it was ever written, per the code-check note above.

One thing worth flagging now so it doesn't get missed later: two of the ten techniques (T003 internal links, T005 sitemap, T006 IndexNow) ran successfully today but have no content to act on yet — `internal_links` reported "refreshed nearby-links on 0 page(s)" and IndexNow had nothing to submit. That's expected with zero new pages, not a sign anything is broken in those techniques themselves.

On the flat-zero traffic: two days is not enough to call the *measurement* suspect (the README's own threshold is about a week), so I'm not raising a metrics.py alarm today. But it is odd that a business with 10 all-time phone leads shows literally zero visitors of any channel on the two most recent days, and if next week's snapshot still shows zero across the board, that stops being a small-sample story and becomes a question about whether `metrics.py`'s bot/owner-IP filtering is eating real traffic (worth a `NEMO_OWNER_IPS` and `BOT_RE` sanity check against a manual log tail if so).

### What I researched today

Searched for what's currently moving the needle for local home-service contractors, prioritizing anything from the last six months over evergreen advice:

- **GBP ranking factors, 2026** — [Local SEO After March 2026 Core Update](https://www.digitalapplied.com/blog/local-seo-march-2026-core-update-gbp-optimization-guide), [Local SEO Ranking Factors 2026](https://www.clickrank.ai/local-seo-ranking-factors/). The March 2026 core update tightened the link between GBP *profile completeness* (categories, hours, services list, attributes, photos) and map-pack visibility, and it now weights **review recency and owner response rate above raw review count**. NEMO's profile sits at 13 reviews; the update makes *responding to the reviews already there* and keeping the profile itself fully filled out matter as much as chasing new review volume.
- **Getting cited by AI answer engines** — [How to Get Cited by ChatGPT and AI Search Engines](https://locafy.com/blog/how-to-get-cited-by-ai), [How to Get Your Local Business Cited by Perplexity AI in 2026](https://www.pleiadesconsultancy.com/blog/how-to-get-cited-by-perplexity-ai-2026). Four levers: consistent NAP, crawlable AI bots, complete schema (LocalBusiness + FAQPage), and reviews on the right platforms. Branded mentions across the web correlate with AI citation roughly 3x more strongly than backlinks do. Reddit and LinkedIn are the most-cited non-owned sources for local trade queries.
- **Converting visits to calls** — [Google Business Profile Optimization to Drive More Phone Calls](https://technijian.com/seo/local-seo-services/how-to-optimize-your-google-business-profile-to-drive-more-phone-calls-in-2026), general 2026 conversion-rate roundups. Mobile visitors are far more likely to call than fill a form; displaying 50+ visible reviews lifts call rate 31–35%; phone leads convert at 30–50% versus 2–5% for site-form leads, so the phone number being one tap away everywhere on the page matters more than any on-page copy tweak.

Rejected ideas from the research pass:
- **Self-declared AggregateRating/Review schema on the homepage or area pages.** The 13 reviews are real, but there's no actual Review content rendered on NEMO's own pages for that schema to describe, and Google's structured-data guidelines treat self-serving rating markup without on-page review content as a misuse risk, not a free ranking boost. Skipped for that reason, not because it wouldn't help if done properly.
- **Any content-volume push (more town pages faster, thinner pages).** Directly against `techniques.py`'s own one-page-per-run guardrail and the exact "scaled content abuse" pattern Google's 2026 policy still targets. Not recommending overriding that guardrail.

### Recommendations

1. **Add Anthropic API credits.** (Eric — costs money, five minutes) This is blocking everything else on this list; nothing else here matters until content generation and scout can run again. Checked: `growth/llm.py` calls the Anthropic API directly and every failure in today's build log traces to it — there's no code fix available here, only a billing one.
2. **Eric personally responds to all 13 existing Google reviews**, and to new ones within a day or two of posting. (Eric — free, ~20 minutes once, then ongoing) Expected effect: per the March 2026 update research above, owner response rate is now weighted above raw review count for map-pack rank — this is a lever Eric can pull today with zero engine involvement and zero review-gating risk. How you'd know it worked: review-adjacent local-pack visibility is not something this repo can measure without GSC (T010), so track it qualitatively for now — did the profile's "owner responds to reviews" indicator show up, and does the map-pack position for "gutter installation york pa" feel different once GSC is connected. Checked: nothing in `techniques.py` or the ledger touches GBP reviews at all — T007 is only about *requesting new* reviews after a job, a different action, still a candidate, still waiting on Eric's go-ahead per its notes.
3. **Fill out the Business Profile completely: every service listed, all attributes, real job photos.** (Eric — free, an hour, one-time plus periodic photo updates) Expected effect: profile completeness is now the single largest signal group in the 2026 breakdown above (~32% of the composite). How you'd know: same caveat as #2 — no GSC yet, so watch `local_visitors` in future snapshots for a lift once this is done and enough weeks pass. Checked: this is distinct from T008 (`gbp_posts`, which is about ongoing posts and needs OAuth the engine doesn't have) — nothing in the ledger currently covers static profile completeness, and it costs nothing to do by hand in the GBP dashboard.
4. **Seed the Business Profile's Q&A section with 5-6 of the FAQ questions already written for the site** (e.g. from `guides/seamless-vs-sectional-gutters.html`, `guides/gutter-cleaning-cost-york-pa.html`). (Eric — free, 15 minutes) GBP Q&A now feeds directly into AI Overviews per this year's research. Checked: no technique in the ledger touches GBP Q&A; this is copy-paste work from content that already exists, not new writing.
5. **Once credits are restored, activate T007 (review request engine)** if Eric agrees to the email-after-job flow described in its notes. Unchanged recommendation from the seed ledger, just reinforced by today's research on how much reviews now matter.
6. **Keep T010 (Search Console connection) near the top of the queue.** Every recommendation above that says "how you'd know it worked" hits the same wall: no rank data exists. This is the one candidate that turns the whole goal from a coverage proxy into an actual measurement, and it's a one-time service-account setup, not ongoing work.

### Reasoning and uncertainties

The API credit failure dominates today's read: a growth engine that can't write content or scout for six-plus weeks (however long the balance has been at zero — the snapshot only shows today) is not "early days," it's stalled, and I don't want a future entry to bury that under the coverage percentage. I'm confident about the credit-blocker finding since it's directly in the build log, not inferred.

I'm least confident about the flat-zero traffic — two data points can't distinguish "this is a genuinely quiet site" from "the log filter is too aggressive," and I chose not to sound the metrics-are-broken alarm on two days per the README's own week-long threshold, but I flagged it because all-time leads (2 bookings, 10 calls) prove someone finds this business somehow. If next week's snapshot still shows zero-across-the-board, that verdict changes to "the measurement is probably broken" and should be said that plainly.

I'm also uncertain whether Eric already responds to reviews and keeps the GBP profile complete — I have no visibility into the live Business Profile from this repo, only the ledger's note that it sits at 13 reviews. Recommendations 2–4 assume there's room to improve; if Eric already does all three, say so next time and I'll drop them rather than repeat a solved recommendation.

**What I actually changed in the repo today**, beyond this journal entry: `growth/publish_state.sh` (the journal-copy step is now a merge via new `growth/merge_journal.py` instead of a blind overwrite) and the entry restoration above. Both are small, and I verified the merge logic against the real before/after content of today's incident (feeding it the pre-wipe and post-wipe versions of this exact file reproduces the pre-wipe content plus the engine's new entry, losslessly) before committing it, rather than trusting the diff by inspection alone. I did not touch `techniques.json`, `keywords.json`, `results.jsonl`, or `state.json` — those stay droplet-owned. One real limit on my confidence here: I have no way to run this script against the actual droplet filesystem, so the fix is verified against the data I have, not against the live environment, and it only takes effect after a manual deploy syncs `growth/` to the droplet — someone should confirm the next 06:00 publish actually preserves this entry before trusting the mechanism is fully closed.

## 2026-07-28 — engine run

Goal: **2.6%** top-3 share of 76 tracked queries (target 50%).
Yesterday: 77 visitors (0 organic, 0 maps) · 0 bookings, 0 phone leads.

**Built:**
- `adopt_queries` — ok: adopted 1 real search(es) into the tracked universe: downspout installations york
- `improve_ctr` — ok: no page is due a snippet rewrite
- `strengthen_pages` — ok: added "Gutter Repair in Dover, PA" to /areas/seamless-gutters-dover-pa.html for 'gutter repair dover pa'
- `service_pages` — ok: published /services/commercial-gutters.html (19,398 bytes; 0 service(s) left in the queue)
- `area_pages` — ok: published Manchester (16,645 bytes; 4 town(s) left in the queue)
- `money_pages` — ok: published 'best gutter company york county pa' → /guides/best-gutter-company-york-county-pa.html
- `internal_links` — ok: refreshed nearby-links on 10 page(s)
- `local_schema` — ok: LocalBusiness schema already current
- `rebuild_sitemap` — ok: [gen_sitemap] wrote 27 URLs to sitemap.xml
- `ping_indexnow` — ok: submitted 13 URL(s), HTTP 200

**Scout did not run:** anthropic 400: {"type":"error","error":{"type":"invalid_request_error","message":"You have reached your specified API usage limits. You will regain access on 2026-08-01 at 00:00 UTC."},"request_id":"req_011CdTwv7KZ8hoopqJtHcmfq"}

## 2026-07-28 — review agent

### The blocker changed shape — it did not go away

The last two review entries led with the Anthropic account having no credit
balance, which stopped `area_pages` and `money_pages` from writing anything.
That specific problem looks fixed: today's build log shows both of them
succeeding (`area_pages` published Manchester, `money_pages` published "best
gutter company york county pa", `service_pages` published Commercial Gutters,
`strengthen_pages` added a Dover repair section) — the first day since this
engine started that the content techniques actually ran. Whoever added funds,
it worked; say so plainly rather than repeating a stale complaint.

But `scout` failed today with a different error than before —not "credit
balance too low," but **"You have reached your specified API usage limits.
You will regain access on 2026-08-01 at 00:00 UTC."** That reads as a
self-imposed spend/rate cap in the Anthropic console (a budget limit, not an
empty account), and on the evidence available it appears the account burned
through whatever cap is set almost immediately after being topped up — one
day of building 3 pages plus one strengthen-pass was enough to trip it. That
means no new candidate ideas will be filed until August 1, though the daily
build itself should keep working since it's the same API. Recommendation
below: whoever manages billing should check whether that limit is a deliberate
guardrail or an accidental default, because if it's the latter it will keep
interrupting scout every time the account is funded.

### Where the numbers stand

The goal is **measured now**, for the first time. T010 (connect Search
Console) is retired with a verdict of `works: true`, and today's snapshot
carries real Search Console data: 77 rows returned, 17 of the 76 tracked
queries matched to an actual position, 429 impressions and 3 clicks over the
trailing 28 days, average position 12.4. Top-3 share is **2.6%** (2 of 76)
against the 50% goal. Coverage (does a page exist targeting the query, the
old proxy) is 48.7% — a page existing is not the same as ranking, and today's
numbers make that gap concrete: 37 queries have a targeting page but only 2
hold a top-3 spot, and 59 of the 76 tracked queries have had **zero**
impressions in the last 28 days, meaning most of the "coverage" hasn't been
seen by a real searcher yet, let alone ranked. This is a real starting line,
not a trend — one day of GSC data is one data point.

Traffic: the only three days in the series are 2026-07-25 (0), 07-26 (0), and
07-27 (77 visitors, 128 pageviews, 193 bot hits filtered separately). The
07-27 spike is the first non-zero day this engine has ever recorded, and it
deserves scrutiny rather than a victory lap — see below.

### Did previous changes work?

Checking each prior recommendation against what's now in the repo:

- **"Add Anthropic credits" (repeated across all three prior entries)** —
  appears done. Build succeeded today for the first time. Verdict: **worked**,
  on the only evidence available (build log stopped failing).
- **"Connect Search Console" (T010)** — done, and it's the review loop's own
  code (`review.py`) that confirmed it, not me: the ledger already carries
  `verdict.works: true`. This is the one technique in the entire ledger with
  an actual verdict; everything else is `not_yet_judged`.
- **"Activate T007 (review-request engine) once credits are restored"** —
  still `candidate`, not activated. Credits are restored now, so this
  recommendation is fully ripe and I'm restating it below rather than letting
  it quietly age.
- **"Eric responds to all 13 Google reviews," "fill out the GBP profile
  completely," "seed GBP Q&A"** — I have no way to check any of these three
  from this repo; nothing in `snapshot.json` reflects live GBP state. Restating
  below, not dropping them, since silence isn't evidence they were done.
- **T001/T002/T017/T018 (area pages, money pages, strengthen, service pages)**
  — `review.py`'s own grace period is 30 days (`GRACE_DAYS = 30` in
  `growth/review.py`), and every one of these was activated 2026-07-27 — one
  day ago. There is exactly one day of `owned_visitors` measurement for any of
  them (T001: 8, T002: 4, T018: 5, all dated 07-27). That grace period runs
  until roughly **2026-08-26**; nothing here can be called worked or
  not-worked before then, and I'd flag it as a problem if a future entry
  claims otherwise. Noting the number now only so the eventual before/after
  comparison has a baseline to check against.
- **The FAQPage-schema idea from the very first entry** — already confirmed
  stale in the second entry's code check (`_faq_ld()` ships on every
  generated page). Nothing new to add; not re-litigating it.

### What I checked in the code before recommending anything

Per this task's standing instruction to verify against `techniques.py` /
`templates.py` rather than assumptions:

- **Sticky/floating call button.** Conversion research today (see below) says
  a persistent tap-to-call element lifts call volume 25-40%. `templates.py`
  already renders one (`<a href="tel:..." class="float-call">`, the phone SVG
  fixed to the corner) on every generated page. Not recommending it — already
  shipped.
- **T014's "GEO answer-first rewrite" candidate.** Its own notes ask for two
  things: FAQPage schema, and a 40-60 word direct-answer block at the top of
  each section. The first half is already done sitewide (`_faq_ld()` in
  `techniques.py`, confirmed again by reading the function this time, not
  trusting the earlier entry's note). The second half — an enforced
  direct-answer opening — is genuinely not in `AREA_SYSTEM`, `MONEY_SYSTEM`,
  or `STRENGTHEN_SYSTEM` in `techniques.py`; none of those prompts ask the
  model for a short lead-in answer before the sections. So T014 is still a
  live candidate, but its scope should shrink to just the direct-answer-block
  half when someone next touches it — the FAQ-schema half of its own "first
  step" note is moot.
- **The traffic-spike composition.** `growth/metrics.py`'s `collect()`
  classifies each visitor into one of: organic, local, ai, direct, referral,
  campaign, or **internal** (referred from another page on
  nemoseamlessgutter.com itself) — but the per-day dict it returns only
  extracts the first six. Visits classified `internal` count toward the
  total `visitors` figure but vanish from every channel bucket the snapshot
  shows. That fully or partly explains 07-27's 77 total vs. 57 `direct`: the
  other ~20 are plausibly a few real visitors browsing multiple pages, not a
  mystery, though I can't confirm that's the whole gap from this repo alone.
- **`BOT_RE` coverage.** While chasing the same spike, I checked which crawler
  user agents the bot filter actually catches. It matches on the substrings
  `bot|crawl|spider|slurp|...`, which covers most named crawlers (Googlebot,
  Bingbot, ClaudeBot, GPTBot, Amazonbot, Bytespider — all contain one of those
  words) — but it missed several real, currently-active crawlers whose names
  don't: `GoogleOther`, `Google-Extended`, `Google-InspectionTool`,
  `meta-externalagent`, and the older `anthropic-ai` token. Google's URL
  Inspection tool and `GoogleOther` in particular are exactly what would hit a
  page within hours of an IndexNow submission — which lines up with T001/T002
  showing `owned_visitors` the same morning their pages were published, faster
  than organic ranking could plausibly deliver a human click. **I fixed this**
  — added those five patterns to `BOT_RE` in `growth/metrics.py`. This doesn't
  retroactively fix 07-27's numbers, but tomorrow's snapshot is a cleaner test:
  if `direct_visitors` and same-day `owned_visitors` drop noticeably, that's
  the confirmation; if they don't, the spike wasn't this.

### What I researched today

Focused on what's new since the last scout ran (2026-07-27), and avoided
re-covering LSAs / Nextdoor / speed-to-lead / door-hangers / GBP category
audits — those are already filed as candidates T011-T016 and don't need a
second write-up.

- **Review recency and response rate now outweigh raw review count in the
  local pack.** The March 2026 core update tightened this: businesses
  responding to 90%+ of reviews see 23% more profile views and 18% more
  direction requests than those replying to under half, and responding at all
  correlates with 68% more clicks than staying silent.
  ([Digital Applied](https://www.digitalapplied.com/blog/local-seo-march-2026-core-update-gbp-optimization-guide),
  [ClickRank via biziq](https://biziq.com/blog/local-seo-statistics/))
  This sharpens, rather than replaces, the prior entry's recommendation that
  Eric respond to NEMO's 13 existing reviews.
- **Phone calls are reportedly the dominant conversion channel for this kind
  of business, and this site cannot see them.** Industry data: phone leads
  convert around 46% versus web-form leads, and phone calls account for
  60-70% of conversions in home-service verticals.
  ([CallRail](https://www.callrail.com/blog/home-services-marketing-statistics),
  [PipelineOn](https://pipelineon.com/blog/contractor-conversion-rate-optimization/))
  `growth/metrics.py`'s own docstring already says as much: tel: link taps
  fire as GA4 `contact_call` events and "GA4 has no server-side export without
  a service-account key" — this repo has never had that key. That is the same
  shape of problem Search Console was before T010: a real signal that exists
  but isn't wired in. See recommendation below.
- **GBP suspension risk in 2026 is concentrated in exactly the kind of
  profile-editing session T016 proposes.** Category mismatches and rapid,
  same-session edits (name/address/category/phone all changed at once) are
  named as common suspension triggers, especially for contractor-category
  listings.
  ([Splinternet Marketing](https://splinternetmarketing.com/digital-strategy/google-business-profile-verification-and-suspensions-in-2026-what-triggers-them-and-how-to-protect-local-rankings/),
  [RenewLocal](https://renewlocal.com/blog/why-google-keeps-suspending-business-profiles-2026))
  NEMO's declared address and category should be low-risk on their own, but
  this is a real caution to attach to T016's "first step" note: spread the
  category check, the Q&A seeding, and the attribute/photo fill-out across
  a few separate sessions rather than one sitting, since Google's abuse
  detection reportedly treats a burst of simultaneous profile edits as a
  hijack signal regardless of whether the edits themselves are legitimate.

**What I rejected:** nothing new to reject today — I didn't find anything
that contradicts an active technique or duplicates a candidate already on
file. I deliberately didn't re-research LSAs/Nextdoor/etc. since T011-T016
already cover that ground and re-running the same search would just relabel
existing candidates as new.

### Recommendations

1. **Check whether the Anthropic usage-limit cap is deliberate.** *(Eric/
   whoever manages billing — a console setting, not a purchase.)* Scout is
   blocked until 2026-08-01 by a self-imposed usage limit that the account
   hit the day after being funded. If that limit is an accidental default
   rather than an intentional guardrail, raising it prevents this from
   recurring every time the account is topped up. How you'd know: tomorrow's
   `last_scout` in the snapshot either stops erroring or keeps citing the same
   cap.
2. **Say yes to T007 (ask finished jobs for a Google review) now that credits
   are restored.** *(Eric — emails real past customers, needs explicit
   go-ahead per the ledger note.)* This was blocked on the credit issue before;
   it no longer is. Reinforced by today's research: review recency/response
   rate now outweighs raw count in the local pack, and NEMO's review count
   (13) is still the gap flagged in the original hypothesis.
3. **Eric respond to NEMO's existing Google reviews, and to new ones within a
   few days of posting.** *(Eric — free, ~20 minutes once then ongoing.)*
   Repeated from the 07-27 entry since I can't confirm it happened; today's
   number is sharper — 90%+ response rate correlates with 23% more profile
   views and 18% more direction requests than sub-50% responders.
4. **When acting on T016 (GBP category + Q&A audit), spread it across
   sessions.** *(Eric — free, no new time cost, just different pacing.)* Check
   the category first, wait a few days, then seed the Q&A, rather than doing
   both plus photos and attributes in one sitting. New reasoning from today's
   suspension-risk research, attached to an existing candidate rather than
   proposing a new one.
5. **New idea, not yet in the ledger: connect the GA4 Data API with a service
   account, the same pattern already proven for T010/Search Console.**
   *(Whoever seeds new techniques on the droplet — one-time setup, no ongoing
   cost, no code to write beyond what `gsc.py` already demonstrates as the
   pattern.)* This closes a gap `metrics.py` documents about itself: tel: taps
   fire as GA4 events this repo has never been able to read, and industry data
   says phone calls are probably the majority of this business's real
   conversions. Checked: grepped the repo for any existing GA4 server-side
   read — there is none; `analytics.js` only fires client-side events. I'm
   flagging this rather than filing it directly since `techniques.json` is
   droplet-owned runtime state, same reasoning as the FAQ-schema idea in the
   first entry.
6. **Watch tomorrow's snapshot for the effect of the BOT_RE fix I made today**
   (see code-check section above). If `direct_visitors` and same-day
   `owned_visitors` for freshly-published pages drop, the 07-27 spike was at
   least partly crawler traffic slipping past the old filter. If they don't
   move, say so plainly rather than declaring the fix a success by default.

### Reasoning and uncertainties

The single thing I'm least sure about is the 07-27 traffic spike. I found two
concrete, code-level reasons a chunk of it could be non-human (the
unattributed `internal` bucket, the `BOT_RE` gaps I fixed), and both are
real gaps, not speculation — but I have no droplet access to grep the actual
log lines and confirm either one actually fired that day. It's equally
possible some of that 77 is genuine early interest. I'm treating it as
**unresolved, not explained**, and said so rather than picking the
comfortable story (bots, so the "real" numbers are still flat) or the exciting
one (early traction). Tomorrow's snapshot, post-fix, is the actual test.

I'm fairly confident about the grace-period math (T001/T002/T017/T018 can't
be judged before ~2026-08-26) since it's directly from `review.py`'s own
constant, not an inference.

I'm least able to verify anything about the live Google Business Profile —
reviews responded to, profile completeness, Q&A seeding. I have zero
visibility into that from this repo and I'm carrying forward three
recommendations on the assumption they're still open, which could be wrong.
If a future entry can get a straight answer from Eric on this, drop whichever
of #2/#3/#4 are already handled instead of repeating them a fourth time.

**What I changed in the repo today:** one small fix to `growth/metrics.py`
(`BOT_RE` now catches five more real crawler user agents that lack a
bot/crawl/spider/slurp substring). I did not touch `techniques.json`,
`keywords.json`, `results.jsonl`, or `state.json` — all droplet-owned. I did
not activate T007, T014, or any other candidate; those are Eric's calls,
surfaced above as recommendations.

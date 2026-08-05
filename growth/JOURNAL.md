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

## 2026-07-29 — engine run

Goal: **2.3%** top-3 share of 87 tracked queries (target 50%).
Yesterday: 0 visitors (0 organic, 0 maps) · 0 bookings, 0 phone leads.

**Built:**
- `adopt_queries` — ok: adopted 2 real search(es) into the tracked universe: gutter installers york, gutter installation york
- `improve_ctr` — ok: no page is due a snippet rewrite
- `geo_answer_first_content_pass` — ok: answer-first opening on /services/gutter-guards.html for 'gutter guards in akron pa' (51 words, + FAQ schema, 6 impressions)
- `strengthen_pages` — ok: added "Hiring a Gutter Contractor in Spring Grove, PA: What to Expe" to /areas/seamless-gutters-spring-grove-pa.html for 'gutter contractor spring grove pa'
- `service_pages` — ok: every queued service already has a page
- `area_pages` — ok: published Mount Wolf (13,364 bytes; 3 town(s) left in the queue)
- `money_pages` — ok: published 'gutter services near me' → /guides/gutter-services-near-me.html
- `internal_links` — ok: refreshed nearby-links on 6 page(s)
- `local_schema` — ok: LocalBusiness schema already current
- `rebuild_sitemap` — ok: [gen_sitemap] wrote 29 URLs to sitemap.xml
- `ping_indexnow` — ok: submitted 10 URL(s), HTTP 200

**Scout proposed (as candidates, not running):**
- T021 Home inspector + realtor referral loop — Every home inspection report in York County flags gutter defects — pitch, seams, missing downspout extensions, rotted fascia — and the buyer or seller has a 10-to-30-day window to fix it before settle
- T022 Itemised GBP Services + weekly job photo — The profile gets ~300 views a month and produces zero calls, which means it is being seen and skipped. Two fixable causes: the Services section is probably thin or generic, so Google has nothing to ma
- T023 Call-first mechanics on every page — The site is built around a booking widget, but homeowners with a gutter overflowing down a wall do not book a slot — they call, and if the number is not thumb-reachable on a phone they call whoever's 

## 2026-07-29 — review agent

### Two corrections to the standing premises, before anything else

**The engine is not blocked.** This task's prompt says to expect the scout to
fail on an Anthropic usage cap until 2026-08-01. It did not. Today's `build`
ran all eleven techniques green and `scout` returned `ok: true` with three new
candidates (T021–T023). Whatever that cap was, it is not biting now. The
prompt is out of date on this point and should be corrected; there is no
billing blocker to lead with today.

**This business has never had a lead through the site — not two bookings and
ten calls, zero of each.** Every prior entry in this journal reasoned from
"all-time totals show 2 bookings and 10 phone leads," and the 07-27 entry
leaned on it explicitly ("all-time leads prove someone finds this business
somehow"). That premise is dead. Today's snapshot reads
`bookings_all_time: 0`, `phone_leads_all_time: 0`, `own_rows_excluded: 12`.
Twelve is exactly two plus ten. Divine's 2026-07-28 commit `ede51dc` ("Stop
counting our own testing as traffic and leads") reclassified every one of
those rows as Eric's own testing. The honest starting line is a site that has
produced no measured booking and no measured phone lead, ever. Nothing below
should be read as if there were a baseline to improve on.

### Where the numbers stand

The goal metric — tracked York County queries holding a top-3 position:

| | 2026-07-28 | 2026-07-29 |
| --- | --- | --- |
| top-3 count | **2** | **2** |
| tracked queries | 76 | 87 |
| share | 2.6% | **2.3%** |
| top-10 count | 7 | 6 |
| coverage proxy | 48.7% | 44.8% |

**The share went down because the denominator went up, not because anything
got worse.** The top-3 count is unchanged at 2. The tracked universe grew by
11 in one day (`adopt_queries` took 2, the scout added 9). County bucket is 2
of 56, up from 2 of 50 — same two wins, six more queries to win. Every town
bucket (york, hanover, dover, red-lion, dallastown, spring-grove) is still
**0 top-3**. Both of the site's top-3 positions are in the county bucket.

Search Console, 28-day rolling window: 87 rows / 19 matched / **3 clicks** /
497 impressions / avg position 13.9, against 77 / 17 / 3 / 429 / 12.4
yesterday. Clicks flat at three. Impressions up 68. Average position 1.5
worse — over a window with 497 impressions that is noise, not a decline, and
part of it is arithmetic: newly-surfacing low-ranked queries drag an average
down without anything falling.

Traffic, and this is the number that changed most:

| date | visitors, as reported 07-28 | visitors, as reported today |
| --- | --- | --- |
| 2026-07-27 | 77 | **9** |
| 2026-07-28 | — | 11 |

Pageviews for 07-27 went 128 → 26, direct 57 → 6, and bot hits 193 → **1,948**.
The series was recomputed retroactively by Divine's four filtering commits of
2026-07-28. Roughly 88% of what this journal recorded as the site's first
traffic was crawlers and scanners.

Leads: 0 bookings, 0 phone leads, both days, both all-time (see above).

Ignore the 2026-07-29 row in `traffic.*`. It shows 0 visitors and 16 bot hits
against ~1,950 on a complete day — it is a few hours of log, not a day. See
the reporting bug below.

### Did previous changes work?

**"Watch tomorrow's snapshot for the effect of the BOT_RE fix" (07-28, rec #6)
— worked, and decisively.** I predicted that if `direct_visitors` and same-day
`owned_visitors` dropped, the 07-27 spike was crawler traffic slipping the
filter. Direct went 57 → 6. `owned_visitors` for 07-27 went T001 8 → 2,
T002 4 → 2, T018 5 → 3. That is the confirmation, and it is unambiguous.
One caveat on credit: my `BOT_RE` addition was not the whole fix. Divine
landed three more filters the same day (own-device opt-out, datacenter/hosting
PTR lookup, and an asset-fetch heuristic that catches automation lying about
its user agent — `metrics.py` documents 232 of 272 addresses fetching pages and
never once fetching a stylesheet). I cannot separate the contributions and am
not going to claim the whole correction. The finding stands regardless: **the
site's real human traffic is roughly 9–11 visitors a day, not 77.**

**"Check whether the Anthropic usage cap is deliberate" (07-28, rec #1) —
resolved.** Scout ran. Three candidates filed. No further action needed.

**"Say yes to T007, the review-request engine" (asked 07-27, 07-28) — not
acted on.** Still `candidate`, `activated: null`. Third day of asking.

**"Eric responds to existing Google reviews / complete the GBP profile / seed
GBP Q&A" (asked 07-27, repeated 07-28) — still unverifiable, and I am going to
stop repeating them as three separate recommendations.** Nothing in this repo
can see the live Business Profile. Repeating an unverifiable ask a third time
adds no information. Collapsed into a single recommendation below: get a
straight answer. Worth noting the engine reached the same conclusion
independently — today's scout notes say "4.2 stars with 13 reviews is the quiet
drag on everything here," which is the scout arguing for promoting T007 above
its own three new proposals.

**"Connect the GA4 Data API" (07-28, rec #5) — not acted on, and it matters
more today than it did yesterday.** With all-time leads now correctly reading
zero, the only conversion this repo can see is a booking-widget submission.
`tel:` taps fire as GA4 `contact_call` events that nothing here can read. If
Eric's phone rang tomorrow because of this site, no number in this snapshot
would move.

**T014 (answer-first / GEO pass) — activated by Divine in `dd44c66`, ran for
the first time today, and it pointed at the wrong market.** See below. Too
early for any outcome; the implementation had a defect that I have fixed.

**T001 / T002 / T017 / T018 — still inside `review.py`'s 30-day grace period**
(`GRACE_DAYS = 30`, activated 2026-07-27, so ~2026-08-26). Post-filter
`owned_visitors` are T001 2/0/0, T002 2/0/0, T018 3/0/0 across 07-27/28/29.
Too early to tell, and now with a lower baseline than the pre-filter numbers
the 07-28 entry recorded. Nothing to conclude for another four weeks.

**`improve_ctr` reporting "no page is due a snippet rewrite" is not a failure.**
`CTR_COOLDOWN_DAYS = 21` in `techniques.py:851`, and the homepage was rewritten
on 07-27, so it is on cooldown until roughly 08-17. Working as designed.

### What I checked in the code before recommending anything

**The answer-first pass wrote the wrong county onto a live service page.**
Today's build log reads: *"answer-first opening on /services/gutter-guards.html
for 'gutter guards in akron pa'."* Akron, PA is in Lancaster County, about 35
miles outside the service area. The paragraph it wrote and published is now
the first thing on that page (`services/gutter-guards.html:163`):

> "NEMO Seamless Gutter installs gutter guards on homes in **Akron, PA and the
> surrounding Lancaster and York County area.**"

Cause, in `techniques.py`: `geo_answer_first_content_pass` took
`headline = queries[0]["query"]` straight from `gsc.queries_for_page()` with no
service-area test — while `adopt_queries`, twenty lines above it in the same
file, has had `SERVICE_AREA_WORDS` / `OUT_OF_AREA` filtering since it was
written, with a comment explaining exactly why. The filter existed; this
function did not use it. Three things make it worth fixing today rather than
noting: the block is written **once per page** and marked done in
`geo_answered` state, so it is permanent unless someone intervenes; it is
placed at the very top as the passage an AI answer engine is meant to lift, so
the wrong claim is the one that gets quoted; and it states a service area that
is not true, which is the NAP-consistency problem local-SEO guidance treats as
a confidence-reducing signal. The technique runs one page a day and there are
~27 pages left, so left alone it would have kept doing this.

**T023 (`call_first_page_mechanics`) is largely already shipped.** Its first
step is "add a persistent tap-to-call bar … so it appears on the homepage, all
four service pages, all five town pages and all three guides." `templates.py:160`
already renders `<a href="tel:+17175780073" class="float-call">`, and I checked
the generated output rather than trusting the template: **28 of 28** pages under
`areas/`, `guides/`, `services/` and `index.html` contain it. The scout proposed
something already live — the same trap the FAQPage recommendation fell into on
day one. Its remaining unshipped parts (the "Eric usually calls back same day"
line, the three-field mobile form) are real but much smaller than the
candidate's framing suggests, and its own expected-effect numbers should be
discounted accordingly.

**The "Yesterday" figure in the report is reading a partial day.** Today's
engine journal entry says "Yesterday: 0 visitors" — but the ledger recorded 11
for 07-28. `snapshot.py` and `report.py` both took `series(...)[-1]`, the newest
row, and there is a row dated today (16 bot hits, 0 visitors). So Eric's
morning email announced zero traffic on a day the site had eleven visitors.
`metrics.collect()` is careful to measure only complete days, so something
outside this repo is writing a same-day row; the cause needs a droplet check
(`results.jsonl` rows dated 2026-07-29 carry a `written` timestamp that will
identify the process). The mislabelling is fixable here regardless of cause,
and I fixed it.

### What I researched today

Deliberately avoided re-covering LSAs, Nextdoor, speed-to-lead, door-hangers
and GBP categories — those are T011–T016 and re-searching them would just
relabel existing candidates as new.

- **A service-area business cannot rank across a whole county from the map
  pack, and no setting changes that.** Proximity for an SAB is measured from
  the hidden verified address, not from the service areas listed on the
  profile; expanding the service-area setting does not expand the radius.
  Practical reach is roughly 10–15 miles, with service-area *pages* covering
  what falls outside it.
  ([SangFroid](https://www.sangfroidwebdesign.com/search-engine-optimization-seo/local-seo-explained/),
  [Local Dominator](https://localdominator.co/local-search-ranking-factors/),
  [RankAI](https://rankai.ai/articles/service-area-business-google-business-profile-guide))
  This is the most strategically useful thing I found today. York County runs
  ~35 miles north to south. From a York-area base, Hanover (~18mi), Dillsburg
  (~15mi) and Stewartstown/New Freedom (~15–20mi) sit at or past the edge.
  **The >50% county goal is not reachable through the Business Profile — the
  town pages are the only lever that scales geographically.** That is a direct
  argument for keeping T001 running, and against expecting GBP work to move the
  goal metric outside greater York.
- **Local landing pages: 15–30 towns, published in small batches, each
  genuinely distinct.** Duplicate copy with the town name swapped is named as
  the fastest route to a thin-content classification, and large sudden page
  sets are flagged as a doorway risk.
  ([Arc4](https://arc4.com/resources/local-seo-landing-pages/),
  [Bipper Media](https://bippermedia.com/seo/service-area-pages-seo/))
  `techniques.py` already caps at one new page per run and there are 12 area
  pages with 3 towns queued, so the engine is inside this guidance. Recording
  it as a boundary: **the town-page queue should stop in the 15–30 range**, not
  run to York County's 70+ municipalities as T001's hypothesis text implies.
- **Inconsistent NAP and vague service descriptions are named as the leading
  cause of AI answer engines declining to cite a local contractor.**
  ([Construction Marketing Association](https://blog.constructionmarketingassociation.org/answer-engine-optimization-for-construction-companies-in-2026-why-ai-visibility-now-matters-in-local-project-discovery/),
  [Finding Permits](https://findingpermits.com/blog/contractor-geo-ai-search-optimization-2026))
  This is what makes the Akron paragraph a live problem rather than a tidiness
  issue — it is a service-area inconsistency sitting in the highest-value
  passage on the page.
- **Apple Business Connect — rebranded to "Apple Business" in April 2026 — is
  free and is not in this ledger at all.** It controls how a business appears
  in Apple Maps, Siri, Spotlight, CarPlay and Apple Intelligence answers.
  ([PinMeTo](https://www.pinmeto.com/blog/apple-business-connect-listings-2026/),
  [NiceJob](https://get.nicejob.com/resources/apple-business-connect),
  [Local Falcon](https://www.localfalcon.com/blog/how-to-claim-and-optimize-your-apple-maps-listing))
  Checked against T001–T023: nothing covers Apple Maps or any non-Google map
  surface. A genuine gap, free, roughly half an hour.

**Rejected:** permit-record seeding as third-party AI evidence — interesting,
but it is a byproduct of doing jobs, not an action Eric can take. Anything
about buying citation-building packages — the T009 candidate already covers
manual NAP submission and paid bulk citation services are largely the same
directories at a markup.

### Recommendations

Ranked. Every on-site item needs a deploy to the droplet before it does
anything — `/var/www/nemo-seamless-gutter` is not a git checkout and nothing
committed here reaches the live site on its own.

1. **Fix the Akron paragraph on the live gutter-guards page.** *(Divine —
   minutes; needs droplet access.)* Rewrite `services/gutter-guards.html`'s
   `<p class="lead">` under the `<!-- geo:answer-first -->` marker so it names
   York County and no other, and drop `"services/gutter-guards.html"` from the
   `geo_answered` list in `state.json` so the corrected pass can rewrite it
   properly on the next run. **Do not fix it in this repo** — `publish_state.sh`
   rsyncs `areas/`, `guides/` and `services/` droplet → repo every morning, so
   any page edit committed here is overwritten tomorrow. How you would know it
   worked: the page's opening paragraph names York County; nothing else on the
   site claims Lancaster County. Checked: `growth/techniques.py`
   `geo_answer_first_content_pass`, and the live text at
   `services/gutter-guards.html:163`.
2. **Deploy the code fixes below to the droplet before the next 06:00 run.**
   *(Divine — a `growth/` sync.)* The filter fix stops this recurring on the
   ~27 pages the pass has not reached yet; the reporting fix stops Eric's email
   understating traffic. Neither is live until synced.
3. **Change how the goal number is calculated, or stop calling it progress.**
   *(Divine / Eric — a decision, then a small change to `snapshot.py`'s goal
   block.)* `share_pct = top3 / tracked_queries`, and the engine adds to
   `tracked_queries` every single day — 76 → 87 in one day, and both
   `adopt_queries` and the scout keep feeding it. The top-3 count did not move
   and the reported share still fell 2.6% → 2.3%. **As built, this number
   trends toward zero no matter how well the business does**, and Eric will
   watch his headline metric decline while things improve. Suggested fix:
   report the top-3 *count* as the headline with the denominator alongside
   ("2 of 87, was 2 of 76"), or freeze a fixed baseline set of queries for the
   percentage and track adopted ones separately. I am not making this change
   myself — it redefines the owner's stated goal, which is his call.
   Checked: `growth/snapshot.py` goal block, `growth/keywords.py`.
4. **Get a straight yes/no from Eric on four Business Profile questions, once.**
   *(Eric — one conversation.)* (a) Have you replied to the 13 existing Google
   reviews? (b) Is the Services section itemised or generic? (c) Is the Q&A
   section populated? (d) May the engine email finished jobs a review request
   — the T007 go-ahead, now asked three days running? These have been carried
   as unverifiable recommendations across three entries; four answers close all
   of them, including T007, T016 and T022. If the answers are "yes, already
   done," say so and they get dropped rather than repeated a fourth time.
   Checked: nothing in `snapshot.json` carries live GBP state; T007
   `activated: null`.
5. **Claim the Apple Business (formerly Apple Business Connect) listing.**
   *(Eric — free, ~30 minutes, one-time.)* Same NAP as the Google profile,
   real photos, correct service area. Expected effect: appearing in Apple Maps,
   Siri and Spotlight for iPhone users searching gutters in York County — a
   surface NEMO is currently absent from entirely. How you would know: search
   "gutter installer" in Apple Maps on an iPhone in York and see whether NEMO
   appears at all; there is no rank data for it, so this is a presence check,
   not a measurement. Checked: grepped all 23 ledger techniques — nothing
   mentions Apple, Bing Places, or any non-Google map surface. Modest
   expectations: this is closing a hole, not a growth lever.
6. **Connect the GA4 Data API with a service account.** *(Divine — one-time,
   free, and `gsc.py` is the working pattern to copy.)* Restated from 07-28
   and sharpened by today's zero-leads finding: the site's primary conversion
   is a phone call, and this repo cannot see one. Until it can, every
   conversion recommendation in this journal is unfalsifiable. Checked: no
   server-side GA4 read exists anywhere in the repo; `analytics.js` is
   client-side only.
7. **Cap the town-page queue at ~30 and let T001 stop there.** *(Divine — a
   note on the technique, or a queue length check.)* T001's hypothesis text
   aims at "York County has 70+ municipalities." Today's research says 15–30
   substantive pages, not one per municipality; past that the marginal town is
   thin-content risk with almost no search volume behind it. There are 12 area
   pages and 3 towns queued, so this is not urgent — record it before it is.
   Checked: `growth/techniques.py` `area_pages`, `growth/keywords.py` town list.

### What I changed in this repo today

Four files, all engine code, none of it live until deployed:

- **`growth/techniques.py`** — added `_names_other_market()` and applied it in
  `geo_answer_first_content_pass`, to both the headline choice and the query
  list shown to the model. It rejects a query naming a state or county that is
  not ours, and is deliberately weaker than the `adopt_queries` test: that one
  needs a positive in-area signal because it sets the goal's denominator, this
  one only needs to reject somewhere else, so geo-neutral searches like
  "gutter installer" (106 impressions, the site's largest single source) still
  qualify as headlines. Also removed the bare `"county"` from
  `SERVICE_AREA_WORDS` — it is what let "schuylkill county seamless gutter"
  into the tracked universe — and added the five out-of-area towns visible in
  today's `discovered_untracked`. Tested against all 23 real queries in today's
  snapshot: every out-of-area one rejected, every in-area and geo-neutral one
  kept.
- **`growth/ledger.py`** — new `complete_series()`, which is `series()` minus a
  row dated today, falling back to the raw series if that would empty it.
- **`growth/snapshot.py`, `growth/report.py`, `growth/email_report.py`** — the
  "yesterday" figures and 14-day medians now read `complete_series`, and the
  journal header prints the date it is actually reporting instead of the word
  "Yesterday".
- **`growth/review.py`** — `_owned()` and `_global()` also read
  `complete_series`. This one is a safety fix rather than a display fix:
  `review.py` retires techniques autonomously on median comparisons, and a
  partial day dragging a median down is how a working technique gets killed on
  the strength of one morning.

`growth/test_metrics.py` still passes (22 tests). I did not touch
`techniques.json`, `keywords.json`, `results.jsonl` or `state.json`, did not
activate any candidate, and did not edit any page under `areas/`, `guides/` or
`services/` — those are rsynced from the droplet daily and an edit here would
be silently reverted tomorrow.

### Reasoning and uncertainties

The Akron finding is the thing I am most confident about and the thing I would
most want Eric to see: it is visible in the build log, in the live page text,
and in the code path that produced it, with no inference in between.

The claim I am least sure of is the shape of the fix, not the need for it. My
filter rejects a query that names Pennsylvania without naming one of our towns
— so "ice dams gutters pennsylvania," a legitimately tracked statewide query,
would be skipped as a headline. That is conservative in the safe direction
(the pass falls through to the next query, then to the page's own `<h1>`), but
it is a real edge and someone reading this later should know it was a choice
rather than an oversight.

I cannot explain where the same-day ledger row comes from. `metrics.collect()`
measures only complete days and `growth_daily.py` is its only caller in this
repo, so something outside it is writing that row — a dashboard is referenced
in a `metrics.py` comment but does not live here. My fix makes the reporting
correct regardless of the cause, which is why I made it without waiting for the
answer, but the cause is still open and worth five minutes on the droplet.

The zero-leads correction changes my read of this whole project more than
anything else today. Two prior entries reasoned from ten all-time phone leads
as evidence that customers find this business somehow. They do not, through
this site. That does not mean Eric has no work — it means **the site has never
been the channel**, and the ledger's offline candidates (T021 inspector
referrals, T015 neighbour flyers, T012 Nextdoor) deserve more weight relative
to the SEO work than the volume of on-site technique activity implies. I am
not recommending they be activated over Eric's head; I am saying the ranking
above would look different if this journal had known the real lead count a
week ago.

What would change my mind: if the 3 clicks in Search Console become 15–20 over
the next fortnight while the top-3 count stays at 2, the town pages are earning
attention below the top three and the strategy is working slower than the goal
metric can show. If clicks stay at 3 through mid-August with 12 area pages
live, the pages are not competitive and the effort should shift to the offline
candidates. Either way that is a two-week question, and nothing in today's
numbers can answer it.

## 2026-07-30 — engine run

Goal: **2.3%** top-3 share of 87 tracked queries (target 50%).
Yesterday: 14 visitors (3 organic, 0 maps) · 0 bookings, 0 phone leads.

**Built:**
- `adopt_queries` — ok: no new in-area searches worth tracking
- `improve_ctr` — ok: no page is due a snippet rewrite
- `geo_answer_first_content_pass` — FAILED: generation failed for /services/gutter-cleaning-repair.html: anthropic 529: {"type":"error","error":{"type":"overloaded_error","message":"Overloaded"},"request_id":"req_011CdXjQqEyfMeLcPgVybGhk"}
- `strengthen_pages` — FAILED: generation failed for 'emergency gutter repair after storm york pa': Expecting ',' delimiter: line 1 column 772 (char 771)
- `service_pages` — ok: every queued service already has a page
- `area_pages` — FAILED: content generation failed for Wrightsville: anthropic 529: {"type":"error","error":{"type":"overloaded_error","message":"Overloaded"},"request_id":"req_011CdXjSjgfbzC9Vrmz6j1Ab"}
- `money_pages` — ok: published 'gutters york pa' → /guides/gutters-york-pa.html
- `internal_links` — ok: refreshed nearby-links on 0 page(s)
- `local_schema` — ok: LocalBusiness schema already current
- `rebuild_sitemap` — ok: [gen_sitemap] wrote 30 URLs to sitemap.xml
- `ping_indexnow` — ok: submitted 1 URL(s), HTTP 200

**Scout did not run:** anthropic 529: {"type":"error","error":{"type":"overloaded_error","message":"Overloaded"},"request_id":"req_011CdXjYApQ2PKaX1cZA7z7n"}

## 2026-07-30 — review agent

### Lead: a third of the run failed, and the prompt's stated blocker is not the reason

Three of today's eleven build steps failed, plus the scout. Two distinct
causes, and **neither is the API usage cap this task's prompt says to expect
until 2026-08-01**. That premise is now wrong for the second day running and
should be deleted from the prompt rather than re-checked a third time.

The actual errors:

| step | error |
| --- | --- |
| `geo_answer_first_content_pass` | `anthropic 529 … "Overloaded"` |
| `area_pages` (Wrightsville) | `anthropic 529 … "Overloaded"` |
| `scout` | `anthropic 529 … "Overloaded"` |
| `strengthen_pages` | `Expecting ',' delimiter: line 1 column 772 (char 771)` |

A 529 is Anthropic's servers being busy for a moment. It says nothing about
this account, it bills nothing, and it is the textbook retryable error.
**`growth/llm.py` had no retry of any kind** — I grepped the whole engine for
`retry|backoff|sleep|attempt` and the only hit was a comment in `metrics.py`.
Every one of those three techniques threw away its whole day's work on a
hiccup that a five-second pause would have cleared. Today's output was one
page instead of four.

The fourth failure is not an API problem and is the more serious of the two.
See below — left alone it stalls `strengthen_pages` permanently, not for a day.

### Where the numbers stand

The goal metric — tracked York County queries holding a top-3 position:

| | 07-28 | 07-29 | 07-30 |
| --- | --- | --- | --- |
| **top-3 count** | 2 | 2 | **2** |
| tracked queries | 76 | 87 | 87 |
| share | 2.6% | 2.3% | **2.3%** |
| top-10 count | 7 | 6 | 6 |
| coverage proxy | 48.7% | 44.8% | 46.0% |

**Fourth consecutive day at two.** The county bucket is 2 of 56, unchanged from
yesterday. Every town bucket — york, hanover, dover, red-lion, dallastown,
spring-grove — is still **0 top-3**, as it has been every day since the goal
became measurable. Both of the site's top-3 positions are county-level. The
share held flat at 2.3% today only because `adopt_queries` found nothing to
add; the denominator problem from yesterday's entry is unchanged, just dormant
for a day.

Search Console, 28-day rolling: 97 rows / 21 matched / **3 clicks** / 686
impressions / avg position 12.5, against 87 / 19 / 3 / 497 / 13.9 yesterday.
Impressions up 189 (+38%) in a day and up 60% since 07-28. **Clicks have been
exactly 3 for four days running.** Average position improved 13.9 → 12.5, which
at these volumes is noise and partly arithmetic.

Traffic, and this is the one genuinely encouraging line in today's data:

| | 07-27 | 07-28 | 07-29 |
| --- | --- | --- | --- |
| visitors | 9 | 11 | 14 |
| organic | 0 | 1 | **3** |
| direct | 6 | 10 | 8 |
| bot hits | 1,948 | 1,954 | 2,374 |

Organic visitors moved off zero for the first time and have risen three days
running. Three visitors is three visitors — I am recording the direction, not
claiming a trend. Local (maps), AI-referred, referral and campaign are all
still flat zero.

Leads: **0 bookings, 0 phone leads, 0 all-time.** `own_rows_excluded` went 12 →
13, so one more of Eric's own test rows was correctly filtered out.

**The measurement-is-broken watch is not triggered.** The prompt says to call
the measurement suspect if `visitors` sits at zero for about a week while the
site is live. It does not: 9 / 11 / 14 with organic rising. The filtering work
of 07-28 looks like it landed correctly rather than over-broadly.

### Did previous changes work?

**"Fix the Akron paragraph on the live gutter-guards page" (07-29, rec #1) —
not acted on. It is still live.** `services/gutter-guards.html:163` still opens
"NEMO Seamless Gutter installs gutter guards on homes in Akron, PA and the
surrounding Lancaster and York County area." `publish_state.sh` rsyncs
`services/` droplet → repo every morning, so the copy in this repo after
today's publish *is* the live page. The highest-value passage on that page has
now been advertising the wrong county for two days.

**"Deploy the code fixes to the droplet before the next 06:00 run" (07-29,
rec #2) — not acted on, and I can prove it.** Today's engine entry opens
`Yesterday: 14 visitors`. The string `Yesterday` does not appear anywhere in
this repo's `growth/*.py` — I replaced that literal on 07-29 with the actual
date of the row being reported. `publish_state.sh` copies only
`snapshot.json`, `sitemap.xml`, `index.html`, the merged journal, and
`areas/ guides/ services/`; it never syncs `growth/*.py` in either direction,
so **the repo's engine code is not evidence of what the droplet is running.**
The droplet is running code older than this repo. Consequences:

- `_names_other_market()` — the out-of-area filter I added on 07-29 — **is not
  live.** The answer-first pass can still write another wrong-county paragraph
  onto any of the ~26 pages it has not reached. It only failed to do so today
  because it 529'd.
- The `complete_series` fix in `review.py` is not live either. That one is a
  safety fix: `review.py` retires techniques autonomously on median
  comparisons, and a partial day dragging a median down is how a working
  technique gets killed on one morning's data.

This is not a criticism of Divine, whose last seven commits are all real work
on the phone assistant. It is a statement that a repo commit and a deployed fix
are different things, and this journal has now twice written up a fix as done
when nothing changed on the live machine.

**"Connect the GA4 Data API" (07-28 rec #5, 07-29 rec #6) — superseded by
something better, and half-finished.** Divine's `14449f9` added
`growth/calls.py`, which counts inbound calls to the AI phone assistant from
ElevenLabs' conversation history, excluding the owner's own numbers. That is a
better answer than GA4 — it counts calls that actually connected rather than
`tel:` taps, and it counts the caller who hung up before leaving a message.
`metrics.py` records it into the ledger. **But `snapshot.py` never surfaces it**
— I grepped, there is no reference to `calls` in `snapshot.py`, `report.py` or
today's `snapshot.json`. So the number Divine just built still does not reach
this review, and the honest current state remains "the phone is not measured
from here." Small fix, flagged below.

**"Change how the goal share is calculated" (07-29, rec #3) — not acted on.**
`share_pct` is still `top3 / tracked_queries`. Dormant today only because the
denominator happened not to grow.

**T007 (ask finished jobs for a Google review) — still `candidate`,
`activated: null`. Fourth day of asking.**

**The four GBP questions (07-29, rec #4), Apple Business (rec #5), the
town-queue cap (rec #7)** — no way to verify any of these from this repo. Not
dropping them; not repeating them at length either.

**My 07-29 two-week prediction on clicks** — "if 3 clicks becomes 15–20 while
top-3 stays at 2, the pages are earning attention below the top three." One day
in: clicks 3, top-3 still 2, impressions up 38%. Far too early. The check date
is mid-August and I am leaving it there.

**T001 / T002 / T017 / T018** — still inside `review.py`'s 30-day grace period
(`GRACE_DAYS = 30`, activated 2026-07-27, so ~2026-08-26). Today's
`owned_visitors`: T001 2/0/3, T002 2/0/2, T018 3/0/3 across 07-27/28/29. Too
early to tell, as it will be for another four weeks.

### What I checked in the code before recommending anything

**The `strengthen_pages` JSON failure is an unescaped inch mark, and the
failure mode is a permanent stall, not a lost day.** `Expecting ','
delimiter` partway through a single-line JSON blob is the signature of a
literal `"` inside a string value. This trade writes `6"` and `5"` constantly —
I counted **44 raw inch marks** in the pages already published under `areas/`,
`guides/` and `services/`. A model asked for JSON will emit
`{"h2": "5" vs 6" Gutters"}`, which is fine English and invalid JSON.
`llm._salvage()` cannot rescue it: salvage only closes structures that were
*truncated*, and this blob is corrupt in the middle.

Worse than the parse error is what the loop did with it. `strengthen_pages`
**`return`ed** on the first exception rather than trying the next query, and a
failure never adds the query to the `strengthened` state list. `todo` is sorted
deterministically. So tomorrow the engine would have picked the identical query
first, hit the identical inch mark, and returned nothing — every morning,
indefinitely. `strengthen_pages` is described in its own hypothesis as "the
technique that actually moves the goal," and it was one bad sentence away from
being dead for the rest of the summer with `ok: false` scrolling past in a log.

**Seasonality is now the binding constraint, and the build queue does not know
it.** Research below puts new-page ranking lead time at 8–12 weeks and the
gutter demand peak at leaf-fall. From 30 July that is late September to late
October, against a York County leaf-fall peak of mid-October to mid-November —
pages written today land just in time, pages written in September miss the
front of the season. Meanwhile `strengthen_pages` sorts its queue by
`order = {"hire": 0, "price": 1, "check": 2, "diy": 3}` with no seasonal
weighting at all, and the uncovered list is full of exactly the fall-demand
terms sitting at the back of that ordering: "gutter cleaning near me",
"gutter cleaning cost dover pa", "gutter cleaning cost red lion pa",
"how often should gutters be cleaned in pa", "are gutter guards worth it",
"gutter guard cost pa", "how much does a gutter guard cost per foot",
"gutters overflowing in heavy rain", "why do my gutters overflow when it rains".
Most are `price`, `check` or `diy` intent, so they queue behind every
installation query.

**Checked and NOT recommending, because it is already shipped:** FAQPage schema
(`_faq_ld()`, every generated page); the sticky tap-to-call bar
(`templates.py:160`, verified present in all generated pages, per 07-29);
IndexNow (T006, active, submitted 1 URL today).

### What I researched today

Deliberately skipped LSAs, Nextdoor, speed-to-lead, door-hangers, GBP
categories, GBP services/photos, call-first mechanics and inspector referrals —
those are T011–T023 and re-searching them just relabels existing candidates.

- **New-page ranking lead time is 8–12 weeks and fall is the demand spike.**
  "Build gutter cleaning and guard pages and earn their rankings before autumn,
  because demand spikes when leaves fall and a new page takes 8 to 12 weeks to
  rank"; map-pack movement typically 60–90 days.
  ([Kelly WM](https://kellywm.com/blog/gutters-seo),
  [Frizerly](https://blog.frizerly.com/18919/gutter_installation_seo_seasonal_content_that_wins_spring_and_fall_demand),
  [Elev8](https://www.elev8operations.com/guides/how-to-get-more-gutter-leads-2026))
  This is the most decision-relevant thing I found today and it converts a
  vague "keep publishing" into a dated deadline.
- **Rising impressions with flat clicks is the expected 2026 pattern, not
  necessarily a fault.** ~60% of Google searches now end without a click and AI
  Overviews appear in ~58% of queries; informational queries are hit hardest
  while commercial/transactional ones hold up better.
  ([Digital Applied](https://www.digitalapplied.com/blog/60-percent-searches-zero-click-crisis-2026-seo-strategy),
  [Semrush](https://www.semrush.com/blog/zero-click-searches/),
  [The Digital Bloom](https://thedigitalbloom.com/learn/organic-traffic-crisis-report-2026-update/))
  Relevant because impressions here rose 38% in a day against flat clicks. At
  686 impressions that is still too thin to diagnose, but it argues against
  reading flat clicks as proof the pages are bad.
- **Bing Places is free, ~15 minutes, imports from the Google profile, and
  feeds Copilot.** Modest traffic on its own (Copilot ≈3.5% of AI referral
  traffic) but the audience skews desktop, older and homeowning, and most
  competitors never claim it.
  ([Osprey](https://osprey.solutions/blog/bing-places-for-business-2026),
  [Thestacc](https://thestacc.com/blog/bing-places-guide/))
  Checked against all 23 ledger techniques: nothing covers Bing Places. Same
  category as the Apple Business gap flagged yesterday — closing a hole, not a
  growth lever.
- **Consistency across site, profile and listings is now an explicit ranking
  input.** Search engines compare the website, the Google listing and other
  local mentions and treat mismatches as weakened trust.
  ([Footbridge](https://www.footbridgemedia.com/marketing-tips/home-services-local-seo-2026),
  [EarlySEO](https://www.earlyseo.com/blogs/seo-for-home-service-businesses))
  This is a second, independent reason the Akron/Lancaster paragraph is a live
  problem rather than a tidiness one.

**Rejected:**
- **`llms.txt`.** Tempting, trivially cheap, and it does not work. No major
  consumer AI search engine has confirmed consuming it — not ChatGPT search,
  Perplexity, AI Overviews, Gemini or Copilot — and Google's John Mueller
  stated outright that Google does not use it.
  ([Layer3Labs](https://www.layer3labs.io/guides/llms-txt-explained),
  [Live Go Digital](https://livegodigital.com/the-great-llms-txt-confusion-of-2026/))
  Recording the rejection so a future scout does not file it as a free win.
- **Paid "AEO"/"AI Search Sync" packages aimed at contractors.** Vendor
  offerings around getting recommended by ChatGPT/Gemini; the underlying work
  is schema, NAP consistency and honest answers, all of which this engine
  already does or T014 covers.
- **Meta/paid social for volume.** Suggested by one gutter-leads source. Out of
  scope — it spends money and this review does not.

### Recommendations

Ranked. **Every on-site or engine item below needs a deploy to the droplet
before it does anything** — `/var/www/nemo-seamless-gutter` is not a git
checkout, and nothing committed here reaches the live site or the 06:00 cron on
its own.

1. **Deploy `growth/` to the droplet.** *(Divine — a sync, minutes.)* This is
   first because four separate fixes are now sitting in this repo doing nothing:
   today's retry and JSON-repair work, today's `strengthen_pages` stall fix,
   yesterday's out-of-area filter, and yesterday's `complete_series` safety fix
   for `review.py`. The retry fix alone would have turned today's one published
   page into four. How you would know: tomorrow's engine entry begins with a
   date rather than the word "Yesterday", and a 529 no longer appears as a
   technique failure. Checked: `publish_state.sh` copy list — it never syncs
   `growth/*.py`, so this cannot happen automatically.
2. **Fix the Akron paragraph on the live gutter-guards page.** *(Divine —
   minutes, needs droplet access.)* Second day of asking. Rewrite the
   `<p class="lead">` under the `<!-- geo:answer-first -->` marker in
   `services/gutter-guards.html` so it names York County and nothing else, and
   drop that path from the `geo_answered` list in `state.json` so the corrected
   pass can redo it. **Do not fix it in this repo** — `services/` is rsynced
   droplet → repo every morning and an edit here is silently reverted tomorrow.
   Checked: the text is still live at `services/gutter-guards.html:163` in
   today's post-publish tree.
3. **Reorder the content queue for leaf-fall season, now.** *(Divine — a small
   change to the sort in `strengthen_pages` and the money-page queue; the engine
   then does the rest itself.)* Pages need 8–12 weeks to rank and York County's
   leaf-fall peak is mid-October to mid-November, so the deadline for a page
   that earns its place in the season is roughly **now to mid-August**. Today
   the cleaning and gutter-guard queries sit at the back of the queue because
   they are `price`/`check`/`diy` intent. Suggested change: add a seasonal boost
   ahead of the intent sort for queries matching cleaning / guard / leaf /
   overflow / clog terms, until about 1 November. Expected effect: the pages
   that can actually catch the annual demand spike get written in the window
   where writing them still helps. How you would know: `impressions` on
   cleaning and guard queries in `keywords.discovered_untracked` and `by_intent`
   rising through September, versus flat. Checked: `growth/techniques.py`
   `strengthen_pages` — `order = {"hire": 0, "price": 1, "check": 2, "diy": 3}`,
   no date or season term anywhere in the function; nothing in the ledger's 23
   techniques mentions seasonality.
4. **Surface the call count in `snapshot.json`.** *(Divine — a few lines in
   `snapshot.py`, then deploy.)* `calls.py` already counts inbound calls to the
   AI assistant and `metrics.py` already records them into the ledger, but the
   snapshot does not carry them, so this review still cannot see whether the
   phone rang. It is the single number the owner's goal actually cares about.
   A count is an aggregate and passes `_assert_no_pii` — the caller numbers stay
   in the gitignored cache. Checked: no `calls` reference in `snapshot.py`,
   `report.py`, or today's `snapshot.json`.
5. **Answer T007 — yes or no.** *(Eric — one decision.)* Fourth day as a
   `candidate`. Review recency is the lever with the most evidence behind it in
   this whole journal, and the engine cannot email a single customer until Eric
   says the word. A "no" is a fine answer and closes it; silence just keeps it
   on the list.
6. **Claim Bing Places.** *(Eric — free, ~15 minutes, imports from the Google
   profile.)* Feeds Copilot and ChatGPT's local answers. Modest expectations —
   this is closing a hole, like yesterday's Apple Business item, and the two
   should be done in the same sitting. Checked: grepped all 23 ledger techniques;
   nothing mentions Bing Places, Copilot, or any non-Google listing surface.
7. **Carried forward, unverifiable from here:** the four Business Profile
   questions (07-29 rec #4), Apple Business (rec #5), the goal-share calculation
   (rec #3), the ~30-page town cap (rec #7). Not restating them at length; they
   are open until someone says otherwise.

### What I changed in this repo today

Two files, both engine code, neither live until deployed:

- **`growth/llm.py`** — a bounded retry on transient statuses
  (408/429/500/502/503/504/529) with 5s and 20s backoff, three attempts
  maximum. This respects BUDGET.md rule 4 ("never add an *unbounded* retry")
  and does not raise spend: a 529 bills nothing, so the only billed call is the
  one that succeeds — the same single unit of work the run was already paying
  for. Billing 400s are explicitly **not** retried, because an empty balance and
  a self-imposed cap are answers rather than hiccups, which is the distinction
  BUDGET.md draws. Also added `_escape_inner_quotes()`, tried in `call_json`
  before `_salvage`, which escapes a `"` inside a string value when the next
  non-space character is not one of `,:}]`.
- **`growth/techniques.py`** — `strengthen_pages` now continues to the next
  query instead of returning on a bad reply, capped at **three attempts**, still
  publishing at most one section per run so BUDGET.md rule 2 holds. If all
  attempts fail it now returns `ok: false` with the first error rather than the
  cheerful "no uncovered query has an existing page to strengthen", which would
  have been precisely the quiet-partial-success failure BUDGET.md rule 6 warns
  about.

Verified rather than eyeballed: the existing suite passes (33 tests), and I
drove `llm.call` against a stubbed urlopen to confirm all four behaviours — a
529 followed by success recovers on attempt 2; a persistent 529 raises after
exactly 3; a billing 400 makes exactly 1 attempt; and the real failing blob
shape `{"h2": "6" gutters", …}` parses correctly end-to-end through the 529
retry. `_escape_inner_quotes` is byte-identical on already-valid JSON,
including JSON containing correctly escaped inch marks and strings containing
`,:}]`.

I did not touch `techniques.json`, `keywords.json`, `results.jsonl` or
`state.json`; did not activate any candidate; did not edit any page under
`areas/`, `guides/` or `services/`.

### Reasoning and uncertainties

The inch-mark diagnosis is the one thing today where I am reasoning from a
signature rather than from the failing string itself. I never saw the model's
reply — only `Expecting ',' delimiter: line 1 column 772`. That error at that
position in a single-line blob is characteristic of an unescaped quote, and 44
raw inch marks in the published corpus make this trade an obvious candidate,
but I cannot rule out some other stray character. It matters less than it
sounds: the loop fix means the technique survives *any* unparseable reply, and
the quote repair is a no-op on JSON that was already valid, so both changes are
correct even if my specific cause is wrong.

The one real edge in `_escape_inner_quotes`: a string whose literal inch mark is
immediately followed by a comma — `"...6", inch stock"` — is genuinely
ambiguous, and the heuristic will read it as the end of the string. That is
inherent to repairing invalid JSON rather than a flaw I can engineer out, and
it fails toward the old behaviour, which is a parse error and now a retry on
the next query.

I am most confident about the deploy gap, because it rests on a literal string
that exists on the droplet and does not exist in this repo, with no inference in
between. It also changes how I read the last two entries of this journal: both
described code fixes in a tone that implied the problem was handled. It was
written down, which is not the same thing, and any future entry that "fixes"
something in `growth/` should say plainly that it is inert until synced.

What would change my mind about the current strategy: organic visitors are 0 →
1 → 3 and impressions are up 60% in two days while clicks sit at 3. If by
mid-August impressions keep climbing and clicks are still 3, the honest read is
that this site's visibility is landing on queries whose clicks are being taken
by the map pack and AI Overviews, and the answer is the offline channels
(T021 inspector referrals, T015 neighbour flyers, T012 Nextdoor) rather than
more pages. If clicks start tracking impressions, the content engine is working
and the correct move is to feed it — which is what recommendation 3 is really
about, because after mid-August the seasonal window closes and that question
gets answered a year late.

## 2026-07-31 — engine run

Goal: **2.0%** top-3 share of 98 tracked queries (target 50%).
2026-07-30: 7 visitors (3 organic, 0 maps) · 1 bookings, 0 phone leads.

**Built:**
- `adopt_queries` — ok: no new in-area searches worth tracking
- `improve_ctr` — ok: no page is due a snippet rewrite
- `geo_answer_first_content_pass` — ok: answer-first opening on /guides/gutter-cleaning-cost-york-pa.html for 'gutter cleaning' (55 words, + FAQ schema, 8 impressions)
- `strengthen_pages` — ok: added "Emergency Gutter Repair After a Storm in York, PA" to /services/gutter-cleaning-repair.html for 'emergency gutter repair after storm york pa'
- `service_pages` — ok: every queued service already has a page
- `area_pages` — ok: published Wrightsville (11,841 bytes; 2 town(s) left in the queue)
- `money_pages` — ok: published 'gutter guys near me' → /guides/gutter-guys-near-me.html
- `internal_links` — ok: refreshed nearby-links on 0 page(s)
- `local_schema` — ok: LocalBusiness schema already current
- `rebuild_sitemap` — ok: [gen_sitemap] wrote 32 URLs to sitemap.xml
- `ping_indexnow` — ok: submitted 4 URL(s), HTTP 200

**Scout proposed (as candidates, not running):**
- T024 "Text a photo, get a price range today" — 300 GBP views and 7 site visits a day are producing 0 calls because the only asks on the profile and site are 'book a slot' or 'call a contractor and hope he answers'. A homeowner staring at a gutter 
- T025 Brave submission + FAQPage schema for Claude/Perplexity citations — The site has zero AI-answer-engine visitors, and the ledger's GEO work is content-side only — it assumes the engines can see the pages. They partly can't: the same-morning IndexNow push covers Bing (s
- T026 Six real York County authority links (chamber, suppliers, historic groups) — The site's ranking problem is prominence, not pages: it already sits top-3 for almost nothing across 87 tracked queries while thin national aggregators outrank it. A handful of genuinely local, hand-v

## 2026-07-31 — review agent

### Lead: the engine ran clean for the first time, and it published a duplicate

Every one of the eleven build steps returned `ok` today and the scout ran. That
has not happened before. The deploy asked for yesterday clearly landed — proof
below — and the retry and stall fixes are live.

The engine used that health to publish `/guides/gutter-guys-near-me.html`, the
**fifth** county-level "which gutter company should I hire" guide in five days,
and there are three more of the same shape queued behind it. That is the one
thing in today's data that gets worse the better the engine works, so it is
first.

Also: **the first booking in the project's history was recorded on 2026-07-30.**
One booking, no attribution, `own_rows_excluded` unchanged at 13 so it was not
one of Eric's test rows. It is real and it is one.

### Where the numbers stand

The goal metric — tracked York County queries holding a top-3 position:

| | 07-28 | 07-29 | 07-30 | 07-31 |
| --- | --- | --- | --- | --- |
| **top-3 count** | 2 | 2 | 2 | **2** |
| tracked queries | 76 | 87 | 87 | **98** |
| share | 2.6% | 2.3% | 2.3% | **2.0%** |
| top-10 count | 7 | 6 | 6 | 6 |
| coverage proxy | 48.7% | 44.8% | 46.0% | 42.9% |

**Fifth consecutive day at two.** The county bucket is 2 of 61 (was 2 of 56);
york, hanover, dover, red-lion, dallastown and spring-grove are all still **0
top-3**, as they have been every single day since the goal became measurable.
Both top-3 positions remain county-level.

The share fell today and **nothing on the site got worse**. The scout added 11
keywords, so the denominator went 87 → 98 while the numerator sat still. This
is the third time this journal has flagged `share_pct = top3 / total` and the
first time it has visibly moved the headline number in the wrong direction on
its own. Of the 98 tracked queries, Search Console has a position for **21**
(`ranked_known`). The other 77 are in the denominator on the strength of
somebody having typed them into a list.

Search Console, 28-day rolling:

| | 07-28 | 07-29 | 07-30 | 07-31 |
| --- | --- | --- | --- | --- |
| rows | 77 | 87 | 97 | **189** |
| matched | 17 | 19 | 21 | 21 |
| clicks | 3 | 3 | 3 | **5** |
| impressions | 429 | 497 | 686 | **975** |
| avg position | 12.4 | 13.9 | 12.5 | **17.0** |

Clicks moved for the first time in five days: 3 → 5. Two clicks. I am recording
it, not celebrating it.

**The impression growth is mostly not York County, and that is the finding of
the day.** Rows nearly doubled (97 → 189) and average position fell from 12.5 to
17.0, which is what happens when a pile of new low-position queries enters the
set. Reading `discovered_untracked`: 24 of the 36 entries name a town NEMO does
not serve — Finleyville, Donora, Morgan, Burgettstown, Bulger, Belle Vernon and
Waynesburg (Washington/Greene counties, ~200 miles west), Crum Lynne, Essington
(Delaware County), Myerstown, Newmanstown (Lebanon County), Perkasie (Bucks),
Yorkville (not York), and "alamo heights seamless gutter installation", which is
Texas. Those 24 account for roughly **132 impressions**, about 14% of the
window, all at positions 22–99, none of them a customer Eric can drive to.

Set against that, the site's genuinely strong showings are geo-agnostic head
terms where Google decides the location itself: **"gutter installer" position 1,
212 impressions, 0 clicks** and **"gutter contractor" position 1, 46
impressions, 0 clicks**. 258 impressions at position 1 across a week and not one
click. `improve_ctr` looked at the site today and reported "no page is due a
snippet rewrite". At position 1 a title is rarely the problem; the local pack
and the AI Overview taking the tap is the likelier answer, which is the caveat
already written into T019's own hypothesis.

Traffic:

| | 07-27 | 07-28 | 07-29 | 07-30 |
| --- | --- | --- | --- | --- |
| visitors | 9 | 11 | 14 | **7** |
| organic | 0 | 1 | 3 | **3** |
| direct | 6 | 10 | 8 | **3** |
| bot hits | 1,948 | 1,954 | 2,374 | 1,200 |

Visitors halved. The whole drop is **direct** (8 → 3); organic held at 3 for a
second day. Direct on a site with no offline campaign running is mostly people
who already know the URL, so a fall there is closer to "Eric's phone was busy"
than to anything the engine did. Local (maps), AI-referred, referral and
campaign are all still flat zero — thirty days of zeros between them.

Leads: **1 booking (07-30), 0 phone leads, 1 all-time.** `phone_leads` has been
zero every day, and I now believe that number is close to meaningless: Divine's
`fc4985b` added first-party `tel:` tap counting on 07-30 and it writes
`call_taps` into the ledger (`metrics.py:453`), but `snapshot.py` was not
carrying it, so this review still cannot see whether anybody tried to ring.
Fixed below.

**The measurement-is-broken watch is not triggered** — 9/11/14/7 with organic at
3 is a small site, not a broken filter.

### Did previous changes work?

**"Deploy `growth/` to the droplet" (07-30 rec #1) — DONE, and it is the reason
today looks the way it does.** The test I set was that today's engine entry would
open with a date rather than the literal word "Yesterday". It opens
`2026-07-30: 7 visitors`, and the string `Yesterday` does not appear anywhere in
this repo's `growth/*.py`. That is the droplet running code it did not have
yesterday. Build steps that failed yesterday and succeeded today: 3 of 3
(`geo_answer_first_content_pass`, `area_pages`, `strengthen_pages`), plus the
scout. Yesterday's entry predicted the retry work "would have turned today's one
published page into four" — today four content steps published. **Honest
caveat:** a green day proves the code is not broken; it does not prove a retry
fired. Anthropic may simply not have been overloaded this morning. What is
genuinely proven is the absence of a permanent stall (below).

**The `strengthen_pages` stall fix (my 07-30 change) — worked, and on the
identical input.** Yesterday it died on `'emergency gutter repair after storm
york pa'` with `Expecting ',' delimiter: line 1 column 772`, and because the old
loop `return`ed rather than continuing, that same query would have been picked
first every morning forever. Today: `added "Emergency Gutter Repair After a
Storm in York, PA" to /services/gutter-cleaning-repair.html` for that exact
query. I cannot tell whether `_escape_inner_quotes` repaired the reply or the
model simply returned valid JSON this time, and it does not matter much — the
technique is un-stalled either way.

**"Fix the Akron paragraph on the live gutter-guards page" (07-29 rec #1, 07-30
rec #2) — NOT acted on. Third day.** `services/gutter-guards.html:163` still
reads "installs gutter guards on homes in **Akron, PA** and the surrounding
**Lancaster** and York County area." Today it stopped being a tidiness item:
Google is showing this site for gutter queries in Lebanon, Bucks, Delaware,
Washington and Greene counties, and the site's single most-read guard page tells
it the business works out of a town in Lancaster County. I cannot prove the
paragraph caused those impressions — one page cannot produce a Texas query — but
"we serve Akron and Lancaster" plus 24 out-of-area queries is not a coincidence I
want to leave sitting there for a fourth day.

**"Surface the call count in `snapshot.json`" (07-30 rec #4) — not acted on by
anyone else, so I did it today.** See the changes section.

**"Reorder the content queue for leaf-fall season" (07-30 rec #3) — not acted
on.** `growth/techniques.py` still has `order = {"hire": 0, "price": 1,
"check": 2, "diy": 3}` in both `money_pages` (line 404) and `strengthen_pages`
(line 705), with no date or season term anywhere near either.

**"Change how the goal share is calculated" (07-29 rec #3) — not acted on, and
today it cost 0.3 points of headline number for no real-world reason.**

**T007 (ask finished jobs for a Google review) — still `candidate`,
`activated: null`. Fifth day of asking.** Today's research makes this the most
expensive unanswered question in the ledger; see below.

**My 07-29 prediction — "3 clicks becomes 15–20 by mid-August while top-3 stays
at 2"** — two days in: clicks 5, top-3 still 2, impressions up 96% since 07-28.
Check date stays mid-August.

**T001 / T002 / T017 / T018** — inside `review.py`'s 30-day grace to ~2026-08-26.
`owned_visitors` 07-27→07-30: T001 2/0/3/0, T002 2/0/2/0, T018 3/0/3/0. Alternating
zeros on a site with 7–14 visitors a day is noise, not a pattern. Too early, and
it will be too early for another four weeks.

**The prompt's stated blocker is wrong for the third day running.** It says to
expect the scout to fail on a self-imposed API cap until 2026-08-01. The scout
ran today, `ok: true`, and filed T024–T026 plus 11 keywords. That premise should
be deleted from the task prompt rather than re-checked a fourth time.

### What I checked in the code before recommending anything

**`money_pages` is building a doorway cluster, and its own guard does not see
it.** Five guides now answer the same question — who should I hire for gutters in
York County:

| page | words |
| --- | --- |
| `gutter-guys-near-me.html` (published today) | 1,517 |
| `gutter-services-near-me.html` | 1,533 |
| `gutters-york-pa.html` | 1,598 |
| `gutter-installer-near-me.html` | 1,080 |
| `best-gutter-company-york-county-pa.html` | 1,078 |

The prose is not duplicated — I measured word-level `SequenceMatcher` ratios
between all ten pairs and they run 0.17–0.22, so each was written fresh. The
*topics* are the problem: four of the five carry a "what gutter work costs in
York County" section and three carry a "5-inch or 6-inch" section. These pages
compete with each other for one query cluster, which is precisely what
`strengthen_pages`' docstring says the engine exists to avoid — "writing a new
page for those would split the site against itself".

`money_pages` does have a guard: `_needs_its_own_page()` refuses to build when
`_host_page()` finds a page the query belongs on, and only builds when the
homepage is the sole fallback. But `_host_page()` (line 660) checks the declared
target, then town area pages, then `SERVICE_HINTS` — and **never looks at
`/guides/`**. So a query with no town and no service verb — "gutter company york
pa", "gutter contractors york pa", "best gutter company york pa", all three
sitting in today's uncovered list — falls through to `/index.html` and reads as
"nowhere to live". I ran `_host_page` against the live docroot for 16 queued
queries to confirm rather than assume: those three returned `/index.html`, i.e.
three more near-identical guides queued at one a day.

This matters more than housekeeping. Today's research: the March 2026 core
update hit home-services hardest, "especially sites built on templated location
pages that swap in city names but don't offer anything unique", with programmatic
city/location pages reported down 32% in visibility and scaled-content cases
losing 60–90%.

So I checked whether this site is on the wrong side of that line, and **it is
not, for the town pages.** I read Wrightsville (published today) and Manchester
in full: Wrightsville is about wind coming off the Susquehanna, hidden hangers at
16" centres instead of 24" on exposed elevations, and spike-and-ferrule systems
working loose in swelling fascia; Manchester is about borough rowhomes where
there are only one or two places a downspout can land without hitting a
neighbour's walk. That is a tradesman's knowledge of two specific places, not a
find-and-replace. The guides were the exposure, and that is what I changed.

**Checked and NOT recommending, because it is already shipped:** FAQPage schema
(`_faq_ld()`, emitted on every generated page); the sticky tap-to-call bar
(`templates.py`); IndexNow (T006 active, 4 URLs submitted today); `tel:` tap
measurement (`metrics.py:453`, landed 07-30).

**Checked against the ledger and NOT filing as new:** everything today's
research points at is already T007, T016 or T022. Ask Maps changes their
*ranking*, not their existence — see below.

### What I researched today

- **Google Business Profile signals are now ~32% of local pack weight, and the
  March 2026 core update re-weighted reviews toward recency.** "A business
  picking up two or three real reviews every month regularly outranks a
  competitor sitting on 300 stale reviews", and the update "tightened proximity
  signals in competitive categories".
  ([Scorpion](https://www.scorpion.co/articles/news/industry-trends-news/googles-march-2026-core-update-what-local-servic/),
  [Digital Applied](https://www.digitalapplied.com/blog/local-seo-march-2026-core-update-gbp-optimization-guide),
  [The Valley Marketing Group](https://thevalleymarketinggroup.com/blog/google-business-profile-2026-service-businesses/))
  NEMO has 13 reviews at 4.2 and is asking nobody. This is T007, unanswered for
  five days, and the evidence behind it got stronger today.
- **"Ask Maps" — Gemini-powered conversational search inside Google Maps,
  launched March 2026 — decides whether a business fits a question by reading
  its Business Profile: reviews, photos, listed services and hours.** Consumers
  increasingly finish the decision inside Maps without visiting the site.
  ([SEO.com](https://www.seo.com/blog/google-ask-maps/),
  [Pluspoint](https://www.pluspoint.io/blog/how-google-maps-ask-maps-is-changing-local-seo),
  [E2M](https://www.e2msolutions.com/blog/local-seo-playbook-agency/))
  I am deliberately **not** filing this as a new technique. Its entire
  actionable content is already T022 (itemise the Services list, post real job
  photos) and T007 (reviews). What it does is re-rank them: a thin Services
  section is no longer just a missed keyword match, it is the input an AI uses
  to decide whether to name NEMO at all. That moves T022 above T016.
- **Fall gutter campaigns should launch in early September, and pre-season
  bookers are less price-sensitive.** ([NeverMiss](https://nevermisshq.com/blog/gutter-seasonal-marketing-automation),
  [Elev8](https://www.elev8operations.com/guides/how-to-get-more-gutter-leads-2026))
  Combined with yesterday's 8–12 week ranking lead time, the deadline for a
  leaf-season page that actually ranks in leaf season is **now**, and the queue
  still does not know it.
- **March 2026 core update vs programmatic pages** — sources above under the
  code section. ([NEURONwriter](https://neuronwriter.com/march-2026-core-update-aftermath-seo/),
  [Digital Applied](https://www.digitalapplied.com/blog/programmatic-seo-after-march-2026-surviving-scaled-content-ban))
- **Zero-click: a page can hold position 1 and take no clicks**, and the advice
  is to filter for high-impression/low-CTR pages and to track Business Profile
  actions ahead of raw site traffic.
  ([WebNet](https://www.webnetinnovation.com/blog/getting-impressions-in-google-search-console-but-no-clicks-heres-why/),
  [Surmado](https://www.surmado.com/blog/local-ai-search-zero-click-survival))
  Directly explains "gutter installer", position 1, 212 impressions, 0 clicks.

**Rejected:**
- **Search Console's new Generative AI performance reports** (announced 3 June
  2026) — I went looking for these specifically, because they would answer this
  journal's biggest open question: whether AI Overviews are eating the clicks.
  They will not, yet. They report **impressions only — no clicks, no CTR, no
  query data** — and rollout began with a subset of **UK-based** site owners.
  I found no confirmed Search Console API dimension for them, so there is
  nothing for `gsc.py` to call. Worth re-checking in a month; not worth
  Divine's afternoon today.
  ([PinMeTo](https://www.pinmeto.com/news/google-search-console-generative-ai-reports-2026/),
  [PikaSEO](https://pikaseo.com/articles/google-search-console-ai-performance-reports-2026))
- **Re-searching LSAs, Nextdoor, speed-to-lead, door-hangers, GBP categories,
  call-first mechanics, inspector referrals, photo-texting, Brave, local links.**
  Those are T011–T026. Re-searching a candidate and filing it again is how a
  ledger turns into noise.

### Recommendations

**Everything below needs a deploy to the droplet before it does anything.**
`/var/www/nemo-seamless-gutter` is not a git checkout and `publish_state.sh`
copies droplet → repo only.

1. **Fix the Akron/Lancaster paragraph on the live gutter-guards page.**
   *(Divine — minutes, needs droplet access. Third day of asking.)* Rewrite the
   `<p class="lead">` under the `<!-- geo:answer-first -->` marker in
   `services/gutter-guards.html` so it names York County and nothing else, and
   drop that path from `geo_answered` in `state.json` so the corrected pass can
   redo it. **Do not fix it in this repo** — `services/` is rsynced droplet →
   repo every morning and an edit here is reverted tomorrow. Expected effect:
   one fewer signal telling Google this business works in Lancaster County. How
   you would know: the out-of-area share of `discovered_untracked` falling from
   today's 24-of-36 over the next month. Checked: still live at
   `services/gutter-guards.html:163` in today's post-publish tree.
2. **Deploy today's two engine changes.** *(Divine — a sync.)* The
   duplicate-guide guard stops three near-identical guides being published over
   the next three mornings, starting tomorrow; the snapshot change makes call
   taps visible to this review for the first time. Both are inert until synced.
   Checked: `publish_state.sh` never copies `growth/*.py` in either direction.
3. **Answer T007 — yes or no.** *(Eric — one decision. Fifth day.)* Today's
   research raised the stakes: review **recency** now outweighs volume in the
   pack, and Ask Maps reads reviews to decide whether to recommend a business at
   all. 13 reviews at 4.2, nobody being asked. A "no" closes it honestly;
   silence just keeps it on the list. Checked: `activated: null` in today's
   snapshot.
4. **T022 before T016 — itemise the GBP Services list and start a weekly job
   photo.** *(Eric — free, an hour, then five minutes a week.)* Ask Maps reads
   the Services list, the photos and the reviews to decide fit. Every distinct
   thing sold as its own entry with an honest one-line description: 5" and 6"
   K-style, half-round aluminium, half-round copper, guards, cleaning, repair,
   downspout extension, soffit and fascia. This is the cheapest thing on the
   list that touches the 300-views/0-calls problem. Checked: T022 already in the
   ledger as a candidate — I am re-ranking it, not re-proposing it.
5. **Reorder the content queue for leaf-fall, now.** *(Divine — a small change
   to the sort; the engine does the rest.)* Carried from 07-30, unactioned, and
   the window is narrower today than it was yesterday: pages take 8–12 weeks,
   York County leaf-fall peaks mid-October to mid-November, campaigns should be
   live in early September. Cleaning and guard queries still sort behind every
   `hire` query because they are `price`/`check`/`diy` intent. Checked:
   `growth/techniques.py:404` and `:705`, both unchanged.
6. **Fix the goal-share denominator.** *(Divine — a few lines in
   `keywords.summary()`.)* Report top-3 against `ranked_known` (21) as the
   honest measured number, keeping top-3-against-all as the ambition. Today the
   scout lowered the headline goal metric by adding keywords, which is a
   measurement artefact reporting as a regression. Checked:
   `growth/keywords.py:296`, still `top3 / total`.
7. **Carried, unverifiable from this repo:** Bing Places (07-30 rec #6), Apple
   Business Connect, the four GBP owner Q&As, the ~30-page town cap. Open until
   someone says otherwise.

### What I changed in this repo today

Three edits, all engine code, none live until deployed. 56 tests pass.

- **`growth/techniques.py` — `_provider_guide()` + `PROVIDER_WORDS`.**
  `_host_page()` now routes a query whose distinguishing words only name a
  *firm* ("company", "companies", "contractor", "contractors", "gutter guys",
  "crew") at the guide that already answers it, instead of falling through to
  `/index.html`. `money_pages` then declines to write a sixth duplicate and
  `strengthen_pages` adds the section to the existing guide, which is the
  behaviour both functions' docstrings already describe. The check runs *after*
  the town and service lookups, so nothing that routes correctly today changes.
  Verified against the live docroot: the three queued duplicates
  ("best gutter company york pa", "gutter company york pa", "gutter contractors
  york pa") now resolve to `/guides/best-gutter-company-york-county-pa.html`,
  while "best gutter company dallastown pa" still goes to the Dallastown area
  page and "gutter installers york pa" still goes to the installation service
  page.
- **`growth/techniques.py` — a `soffit`/`fascia` entry in `SERVICE_HINTS`,
  placed above the repair and install lines.** Found while testing the above:
  "soffit and fascia repair york pa" was routing to the cleaning/repair page and
  "gutter soffit and fascia replacement" to the installation page — away from
  `/services/gutter-soffit-fascia-replacement.html`, the dedicated page the site
  already ranks 1.8 for and which T018 exists to have built.
- **`growth/snapshot.py` — `call_taps` and `ai_calls` added to `SERIES`.**
  Both were already being written into the ledger and read by nobody, because
  the review agent sees only this file. Counts are aggregates; caller numbers
  stay in the gitignored cache, so `_assert_no_pii` is unaffected. This is
  07-30 rec #4, done rather than asked for a second time.

I did not touch `techniques.json`, `keywords.json`, `results.jsonl` or
`state.json`; did not activate any candidate; did not edit any page under
`areas/`, `guides/` or `services/`.

### Reasoning and uncertainties

The duplicate-guide finding is the one I would defend hardest, because it does
not rest on interpretation: five pages exist, I read their headings, and the
next three queue entries route to `/index.html` in a function I executed against
the real docroot. What I am *less* sure of is the size of the harm. Five
overlapping guides on a 33-page site is not the thousands-of-pages pattern
Google's scaled-content policy targets, and the prose is genuinely distinct. My
fix is justified by authority-splitting — our own pages competing for one query —
more than by any penalty risk, and I would rather stop the pattern at five than
argue about where the line is at fifteen.

The out-of-area impressions are the finding I am least certain how to act on.
132 impressions across two dozen towns Eric cannot serve could mean Google is
confused about the service area, or it could simply be what a young site looks
like while Google works out what it is — broad, unconfident matching that
settles as the entity firms up. The Akron paragraph is worth fixing either way,
and it is free, so I have not tried to resolve the ambiguity before recommending
it. What would resolve it: if the out-of-area share is still a quarter of
discovered queries in a month with the paragraph fixed, the problem is the
entity and not one page.

I am uneasy about how good today looks. Eleven green steps, the first booking,
clicks finally moving — and the underlying goal metric has not moved in five
days, every town in the county is still at zero, and the two positions the site
holds at number one produce no clicks at all. The engine is working. Whether the
work is *earning* anything is still, honestly, unknown, and will stay unknown
until the grace period ends on 26 August. The danger in a day like today is
mistaking a healthy machine for a growing business.

What would change my mind about the current strategy: if clicks track
impressions through mid-August, the content engine deserves more fuel and
recommendation 5 becomes the most important item on the list. If impressions
keep climbing while clicks stay in single digits, then this site's visibility is
landing where the map pack and AI Overviews take the tap, and the honest answer
is the offline and profile channels — T007, T022, T021, T012 — rather than a
thirty-fourth page.

## 2026-08-01 — engine run

Goal: **1.9%** top-3 share of 108 tracked queries (target 50%).
2026-07-31: 6 visitors (1 organic, 0 maps) · 0 bookings, 0 phone leads.

**Built:**
- `adopt_queries` — ok: adopted 1 real search(es) into the tracked universe: york gutters
- `improve_ctr` — ok: rewrote title/description on /guides/gutter-cleaning-cost-york-pa.html (11 impressions, 0 clicks, pos 9.3) — Front-loaded the exact search wording ("gutter cleaning" + York) instead of a question phrasing, and swapped t
- `geo_answer_first_content_pass` — ok: answer-first opening on /services/gutter-cleaning-repair.html for 'clogged gutter repair' (54 words, + FAQ schema, 10 impressions)
- `strengthen_pages` — ok: added "Copper Half-Round Gutters for Historic Homes in York, PA" to /services/half-round-gutters.html for 'half round copper gutters historic home york pa'
- `service_pages` — ok: every queued service already has a page
- `area_pages` — ok: published Hallam (12,154 bytes; 1 town(s) left in the queue)
- `money_pages` — ok: published 'york gutters' → /guides/york-gutters.html
- `internal_links` — ok: refreshed nearby-links on 13 page(s)
- `local_schema` — ok: LocalBusiness schema already current
- `rebuild_sitemap` — ok: [gen_sitemap] wrote 35 URLs to sitemap.xml
- `ping_indexnow` — ok: submitted 18 URL(s), HTTP 200

**Scout proposed (as candidates, not running):**
- T027 Missed-call text-back on the business line — The AI agent catches calls it answers, but it cannot catch the caller who hangs up at ring 3, calls at 8pm, or gets a busy signal while Eric is talking to someone else — and those are exactly the home
- T028 Heavy-rain 48-hour response play (overflow page + GBP post) — York County gets thunderstorm bands in August and nor'easter rain in September, and the moment a gutter overflows over the front door a homeowner searches 'gutters overflowing in heavy rain' or 'gutte
- T029 Apple Business + Bing Places verified place cards — The ledger's AI-answer work is all on-site — it assumes the engines can read nemoseamlessgutter.com. But when a York homeowner asks Siri or Copilot 'who installs gutters near me', those assistants do 

## 2026-08-01 — review agent

### Lead: the site's largest asset is 336 impressions at the top of Google producing zero clicks, and the engine took the place name off the page holding them

Nine geo-agnostic head terms — "gutter installer", "gutter contractor", "gutter
guard installer", "gutter soffit and fascia replacement", "gutters", "gutter
replacement", "gutter repair", "gutter cleaning", "seamless spouting" — account
for **336 impressions in the 28-day window and zero clicks between them.** Three
of them sit at position 1. "gutter installer" alone is 212 impressions at
position 1.0, and nobody has clicked it once.

The homepage is the page holding those positions. Its title today:

> `Gutter Installer & Contractor | NEMO Seamless Gutter`

Its title on 2026-07-26:

> `Seamless Gutters in York, PA | NEMO Seamless Gutter — Free Estimates`

`improve_ctr` (T019) rewrote it on 07-27 and the place name went with it. The
meta description lost York County in the same edit. That is not a model slip —
it is `CTR_SYSTEM` working exactly as written: *"Lead with what the searcher
typed."* The searches it was handed were "gutter installer" and "gutter
contractor", which name no place, so the snippet it produced names no place, on
the one page that carries the whole site's visibility.

Two things follow, and they are the same fact seen twice. A York homeowner
scanning results for a local trade sees a title that could be a directory
listing from anywhere and taps the map pack instead. And Google, deciding which
searchers this page is for, is being told by the flagship page that it belongs
to no particular town — while the site collects impressions in Donora,
Finleyville, Burgettstown, Myerstown, Perkasie, Essington, Wilkes-Barre, York
**South Carolina**, Yorkville, and Alamo Heights, Texas.

I cannot prove the title caused any of that; see the uncertainties. I can prove
the title says nothing about York, that it used to, that this engine is what
changed it, and that restoring it costs nothing. That is the top recommendation.

**Second: the 07-31 review commit was never deployed, and Divine's same-day
commit was.** `growth/snapshot.py` in this repo lists `call_taps` and `ai_calls`
in `SERIES`; today's `snapshot.json` `traffic` block contains neither. Divine's
`2dfa649` ("Mark the techniques that had nothing to do as no-ops") *is* live —
today's build log carries `"noop": true` on `service_pages` and `local_schema`.
So the droplet is running Divine's 07-31 work and not the review agent's, from
the same day. Five fixes are now sitting in this repo doing nothing.

**Third: the Akron/Lancaster paragraph is still live. Fourth day of asking.**
`services/gutter-guards.html:163` still opens "installs gutter guards on homes in
Akron, PA and the surrounding Lancaster and York County area."

### Where the numbers stand

The goal metric — tracked York County queries holding a top-3 position:

| | 07-28 | 07-29 | 07-30 | 07-31 | 08-01 |
| --- | --- | --- | --- | --- | --- |
| **top-3 count** | 2 | 2 | 2 | 2 | **2** |
| tracked queries | 76 | 87 | 87 | 98 | **108** |
| share | 2.6% | 2.3% | 2.3% | 2.0% | **1.9%** |
| top-10 count | 7 | 6 | 6 | 6 | 6 |
| coverage proxy | 48.7% | 44.8% | 46.0% | 42.9% | 40.7% |
| queries GSC can actually rank | — | — | — | 21 | 21 |

**Sixth consecutive day at two.** County bucket 2 of 65 (was 2 of 61, 2 of 56,
2 of 50). York, Hanover, Dover, Red Lion, Dallastown and Spring Grove are all
**0 top-3**, as they have been every day since the goal became measurable on
07-28. Both of the site's top-3 positions are county-level.

The share fell again and nothing got worse: `adopt_queries` took one query and
the scout added nine, so the denominator went 98 → 108 while the numerator sat
still. Fourth entry flagging `share_pct = top3 / total`. 87 of the 108 tracked
queries have no measured position at all; they are in the denominator because
somebody typed them into a list.

Search Console, 28-day rolling:

| | 07-28 | 07-29 | 07-30 | 07-31 | 08-01 |
| --- | --- | --- | --- | --- | --- |
| rows | 77 | 87 | 97 | 189 | **219** |
| matched | 17 | 19 | 21 | 21 | **21** |
| clicks | 3 | 3 | 3 | 5 | **6** |
| impressions | 429 | 497 | 686 | 975 | **1,167** |
| avg position | 12.4 | 13.9 | 12.5 | 17.0 | **18.3** |

Impressions have nearly tripled in four days; clicks have gone 3 → 6. `matched`
has been stuck at 21 for three days while `rows` more than doubled — the growth
is entirely in queries nobody is tracking. Average position 12.4 → 18.3 is
mostly arithmetic: new low-ranked rows drag an average down without anything
falling.

Out-of-area queries in `discovered_untracked`: **29 of 40 rows, 174 impressions**
(07-31: 24 of 36, ~132). Roughly flat as a share of rows, up in absolute terms.
The eleven in-area or geo-agnostic rows carry 351 impressions between them.

Traffic:

| | 07-27 | 07-28 | 07-29 | 07-30 | 07-31 |
| --- | --- | --- | --- | --- | --- |
| visitors | 9 | 11 | 14 | 7 | **6** |
| organic | 0 | 1 | 3 | 3 | **1** |
| direct | 6 | 10 | 8 | 3 | **4** |
| campaign | 0 | 0 | 0 | 0 | **1** |
| bot hits | 1,948 | 1,954 | 2,374 | 1,200 | **3,162** |

Six visitors. Organic fell 3 → 1. The first campaign-tagged visitor ever
appeared, which is one visitor and means nothing on its own. Local (maps),
AI-referred and referral are still flat zero — thirty-plus days of zeros.

Leads: **0 bookings and 0 phone leads on 07-31; 1 booking all-time**, the
2026-07-30 one. `own_rows_excluded` unchanged at 13.

`call_taps` and `ai_calls` are still **not in the snapshot** — see the deploy
finding. The phone remains unmeasured from here, on a business whose goal is a
ringing phone.

**The measurement-is-broken watch is not triggered.** 9/11/14/7/6 with organic
non-zero on four of five days is a small site, not a broken filter.

### Did previous changes work?

**"Deploy today's two engine changes" (07-31 rec #2) — NOT done, and the proof
is in the snapshot.** `SERIES` in this repo's `growth/snapshot.py` includes
`call_taps` and `ai_calls`; today's `snapshot.json` `traffic` keys are
`ai_visitors, bookings, bot_hits, campaign_visitors, direct_visitors,
local_visitors, organic_visitors, pageviews, phone_leads, referral_visitors,
total_leads, visitors`. Neither is there. Meanwhile Divine's 07-31 commit
`2dfa649` is live, visible as the `"noop"` keys in today's build log. Same day,
one deployed and one not. Undeployed and waiting: the out-of-area filter
(07-29), `complete_series` in `review.py` (07-29), the provider-guide routing
and the soffit hint (07-31), the call-tap surfacing (07-31).

**My provider-guide fix (07-31) — right diagnosis, fix too narrow, and the
engine proved it this morning.** I predicted it would "stop three near-identical
guides being published over the next three mornings." What actually happened:
`money_pages` published **`/guides/york-gutters.html`** for the query "york
gutters", one day after publishing **`/guides/gutters-york-pa.html`** for
"gutters york pa". Same question, words reversed. Six of the seven headings on
each page are the same beats — price ranges in York County, what moves the
number, 5-inch or 6-inch, guards, how to get a real number. `_provider_guide`
would not have caught it even if deployed: "york gutters" contains none of
`PROVIDER_WORDS`. I patched a word list where the problem was topic overlap.
Recorded plainly because the previous entry reads as if that was solved.
(Word-level `SequenceMatcher` between the two pages is 0.186, so the prose is
freshly written — the duplication is of *purpose*, not text.)

**"Fix the Akron paragraph" (07-29 #1, 07-30 #2, 07-31 #1) — not acted on.
Fourth day.** Still live at `services/gutter-guards.html:163`.

**"Reorder the content queue for leaf-fall" (07-30 #3, 07-31 #5) — not acted
on.** `order = {"hire": 0, "price": 1, "check": 2, "diy": 3}` still sits at
`growth/techniques.py:405` and `:748`, no season term anywhere near either.
The window is 60–75 days narrower than when it was first raised.

**"Fix the goal-share denominator" (07-29 #3, 07-31 #6) — not acted on.**
`growth/keywords.py:296` is still `top3 / total`. It cost another 0.1 points
today for no real-world reason.

**T007 (ask finished jobs for a Google review) — still `candidate`,
`activated: null`. Sixth day of asking.**

**My 07-29 prediction — "3 clicks becomes 15–20 by mid-August while top-3 stays
at 2."** Three days in: clicks 6, top-3 still 2, impressions up 172% since
07-28. Check date stays mid-August.

**T001 / T002 / T018** — inside `review.py`'s 30-day grace to ~2026-08-26.
`owned_visitors` 07-27→07-31: T001 2/0/3/0/0, T002 2/0/2/0/0, T018 3/0/3/0/0.
Zeros on a six-visitor day are noise. Four more weeks before any verdict is
honest.

**`improve_ctr` fired for the first time since 07-27**, on
`/guides/gutter-cleaning-cost-york-pa.html`, and that rewrite kept York in both
title and description. So the technique is not always destructive — it was
destructive on the one page whose top queries name no place. That is the
distinction the fix below encodes.

**Divine's `888325a` (audience roster) and `portfolio_stats.py` landed 07-31.**
Not growth-facing: it answers "how many different people, ever" for a portfolio
card. Noted so it is not mistaken for a metrics change.

**The prompt's blocker premise, one last time.** It says to expect the scout to
fail on a self-imposed API cap "until 2026-08-01 at 00:00 UTC". The scout ran
clean on 07-29, 07-31 and again today, filing T027–T029. The date has now passed
so the premise is moot rather than merely wrong, but it was wrong on three of
the four days it was checked and should come out of the prompt.

### What I checked in the code before recommending anything

**The homepage title, traced rather than assumed.** `git log -- index.html`
shows the string changing between `923b471` (07-26) and `d569d0e` (07-27), the
same morning the 07-27 build log records `improve_ctr` rewriting the homepage.
`CTR_SYSTEM` (`techniques.py:906`) has no rule about geography and
`improve_ctr` validates only snippet *length*, so nothing in the code path could
have stopped it. I audited every generated page: exactly two titles on the site
name no place — the homepage, and `guides/seamless-vs-sectional-gutters.html`,
which is a genuinely non-local comparison and is fine.

**`publish_state.sh` copies `index.html` droplet → repo.** So the homepage fix,
like the Akron fix, has to happen on the droplet; an edit committed here is
reverted by tomorrow's 06:00 publish. I did not edit it.

**Where the money-page queue points.** I ran `_host_page` against the real
docroot for all 65 uncovered queries. Before today's change, **7** fell through
to `/index.html`, which `money_pages` reads as "nowhere to live, write a guide":
three phrasings of "5 inch vs 6 inch gutters" and "what size gutters do i need",
against a size guide the site already has. After the change, **3** fall through
— "gutter pulling away from house", "ice dams gutters pennsylvania", "do i need
gutters on my house" — all genuinely uncovered topics, and the first two happen
to be exactly the storm and ice-dam wording T028 argues for.

**Checked and NOT recommending, because it is already shipped:** FAQPage schema
(`_faq_ld()`, every generated page); the sticky tap-to-call bar
(`templates.py:160`); IndexNow (T006 active, 18 URLs submitted today); `tel:`
tap counting (`metrics.py:453`). **Checked against the ledger and not filing as
new:** everything today's research points at is already T007, T022, T025, T026
or T029.

**One known limitation of my own change, recorded rather than hidden:**
`SERVICE_HINTS` still runs ahead of the new topic check, so "seamless gutters vs
sectional gutters" routes to the installation service page rather than to
`/guides/seamless-vs-sectional-gutters.html`, which exists. That query is
already covered so nothing acts on it today, but reordering those two lookups is
riskier than the benefit and I left it alone.

### What I researched today

Deliberately skipped LSAs, Nextdoor, speed-to-lead, door-hangers, GBP
categories, GBP services/photos, call-first mechanics, inspector referrals,
photo-texting, Brave, local authority links, missed-call text-back, the rain
play and Apple/Bing — those are T011–T029 and re-searching them turns the ledger
into noise.

- **The AI Overview local pack, and why position 1 can be worth nothing.**
  Reported to appear on roughly 68% of local queries with informational or
  comparison intent, showing a generative answer and two to four cited
  businesses; position-one CTR measured falling ~78% when an AI Overview is
  present; and — the number that matters most here — only about 23% of citations
  on branded queries come from the business's own content, with **77% from
  off-page sources**.
  ([Marketing Code, Jul 2026](https://www.marketingcode.com/ai-search-overview-local-pack-map-pack-contractor-citation-playbook-jul-2026/),
  [Search Engine Journal](https://www.searchenginejournal.com/ai-overviews-now-answer-most-local-searches-how-to-get-your-business-cited/580757/),
  [Indexsy CTR statistics](https://indexsy.com/ctr-statistics/),
  [GoodFirms](https://www.goodfirms.co/resources/seo-statistics-ai-search-rankings-zero-click-trends))
  **Honesty note: the Marketing Code article returned HTTP 403 to a direct
  fetch, so I have its claims only through search-result summaries and have not
  read the primary source.** Treat those specific percentages as indicative.
  The direction is consistent across the other three and matches what this
  site's own data shows, which is why I am using it at all.
  What it changes: if three-quarters of local AI citations come from off-page
  sources, then a 36th page is not the lever. Reviews, listings and local links
  are — T007, T029, T026 — and the site's job is to be consistent enough to be
  quotable, which is what makes the homepage and Akron fixes worth more than
  their size suggests.
- **Google is reported to favour clearly defined geographic coverage over broad
  or vague service areas, and to cross-check the website against the profile.**
  The specific failure named: a site claiming different places than the profile
  is a discrepancy that "can confuse the algorithm", and the recommended check
  is to look at the queries driving impressions and ask whether the site's
  content actually addresses those places.
  ([Hook Agency](https://hookagency.com/blog/local-seo-for-home-service-businesses/),
  [RankAI](https://rankai.ai/articles/service-area-business-google-business-profile-guide),
  [DM Net Solutions](https://www.dmnetsolutions.com/google-business-service-areas/))
  This is the second independent line of evidence for both the homepage title
  and the Akron paragraph, and it is the reason I stopped treating them as
  tidiness items.
- **AI search recommends roughly 1.2% of local businesses analysed** across a
  350,000-location sample — the same figure the 07-27 entry found from a
  different source, so it has now survived a second look.
  ([Marketing Code, May 2026](https://www.marketingcode.com/1-2-percent-local-businesses-ai-search-trust-stack-may-2026/))
  Low bar, low competition, and consistent with T025/T029 being cheap bets
  rather than long shots.

**Rejected:**
- **Anything about paid AEO/"AI visibility" packages** — third time this journal
  has met them and the underlying work is still schema, NAP consistency and
  honest answers, all of which the engine does or the ledger covers.
- **`llms.txt`** — rejected 07-30 on the evidence that no major engine consumes
  it. Nothing found today changes that; recording the re-rejection so a future
  scout does not file it as a free win.
- **Re-checking Search Console's generative-AI reports** — I said on 07-31 to
  look again in a month. One day has passed. Not re-checked.

### Recommendations

**Everything below needs a deploy to the droplet before it does anything.**
`/var/www/nemo-seamless-gutter` is not a git checkout and `publish_state.sh`
copies droplet → repo only.

1. **Put York back in the homepage title and description — on the droplet.**
   *(Divine — minutes. Free.)* This is first because it is the site's strongest
   page, it holds position 1 on the terms carrying most of its visibility, those
   terms have produced zero clicks in four weeks, and the snippet a searcher
   sees names nowhere. Suggested restoration, which is the text this engine
   replaced:
   > title: `Seamless Gutters in York, PA | NEMO Seamless Gutter`
   > description: `NEMO Seamless Gutter installs custom seamless gutters, gutter
   > guards and downspouts across York County, PA — plus gutter cleaning &
   > repair. Formed on-site to fit your home exactly. Free estimates. Call or
   > text (717) 578-0073.`
   Also drop `index.html` from `ctr_rewrites` in `state.json` only if you want
   the technique to try again; with the fix below deployed it can no longer strip
   the place name, but the 21-day cooldown expires ~08-17 anyway.
   Expected effect: some share of 336 wasted impressions becoming clicks, and one
   fewer signal telling Google this business belongs to no town. How you would
   know: clicks on "gutter installer"/"gutter contractor" in
   `discovered_untracked` moving off zero within two to three weeks, and the
   out-of-area share of discovered rows falling from today's 29-of-40.
   **Do not fix it in this repo** — `publish_state.sh` copies `index.html`
   droplet → repo. Checked: `git log -- index.html` for the 07-26 → 07-27 change;
   `CTR_SYSTEM` and `improve_ctr` in `growth/techniques.py` for the absence of any
   geographic rule; every generated page's `<title>` for how many others lost it
   (one, and legitimately).
2. **Deploy `growth/` to the droplet.** *(Divine — a sync, minutes. Free.)*
   Seven fixes are now waiting across three days: the out-of-area filter, the
   `complete_series` safety fix in `review.py`, the provider-guide routing, the
   soffit hint, the call-tap surfacing, and today's two. How you would know:
   `call_taps` and `ai_calls` appear in tomorrow's `snapshot.json` `traffic`
   block. Checked: they are absent today while `SERIES` in this repo's
   `snapshot.py` lists them.
3. **Fix the Akron/Lancaster paragraph on the live gutter-guards page.**
   *(Divine — minutes, droplet access. Free. Fourth day.)* Rewrite the
   `<p class="lead">` under the `<!-- geo:answer-first -->` marker so it names
   York County and nothing else, and drop that path from `geo_answered` in
   `state.json` so the corrected pass can redo it. Checked: still live at
   `services/gutter-guards.html:163` in today's post-publish tree.
4. **Answer T007 — yes or no.** *(Eric — one decision. Free. Sixth day.)* If
   three-quarters of local AI citations come from off-page sources, and review
   recency is weighted above volume, then 13 reviews at 4.2 with nobody being
   asked is the largest untouched lever in the ledger. A "no" closes it
   honestly; silence keeps it on the list a seventh day. Checked:
   `activated: null` in today's snapshot.
5. **Reorder the content queue for leaf-fall.** *(Divine — a small change to the
   sort in `money_pages` and `strengthen_pages`; the engine does the rest.
   Free.)* Carried unactioned from 07-30 and 07-31, and the window has closed by
   two more days. Pages take 8–12 weeks to rank; York County leaf-fall peaks
   mid-October to mid-November. Cleaning, guard, overflow and clog queries still
   sort behind every `hire` query because they are `price`/`check`/`diy` intent.
   Checked: `growth/techniques.py:405` and `:748`, both unchanged.
6. **Fix the goal-share denominator.** *(Divine — a few lines in
   `keywords.summary()`. Free.)* Report top-3 against the 21 queries Search
   Console can actually rank, keeping top-3-against-all as the ambition. Eric
   has now watched his headline metric fall 2.6% → 1.9% across a week in which
   nothing on the site got worse. Checked: `growth/keywords.py:296`, still
   `top3 / total`.
7. **Carried, unverifiable from this repo, not restated at length:** T022
   (itemised GBP Services + weekly job photo), T029 (Apple Business + Bing
   Places — now formally in the ledger, which supersedes the loose 07-29/07-30
   recommendations), the four GBP owner questions, the ~30-page town cap. Open
   until someone says otherwise.

### What I changed in this repo today

Three files, all engine code, none of it live until deployed. 81 tests pass
(71 before, 10 new).

- **`growth/techniques.py` — `GEO_ANCHOR` + a placeless-snippet rejection in
  `improve_ctr`, and a matching rule in `CTR_SYSTEM`.** A rewrite whose title
  *and* description both fail to name York, York County or PA is now refused the
  same way an over-long one is. The title alone is not required to carry it, so
  a legitimate comparison headline like "Seamless vs. Sectional Gutters" can
  still be used as long as the description says where the business is. `\bpa\b`
  is bounded so it does not match inside "repair" or "page".
- **`growth/techniques.py` — `_topic_guide()`, wired into `_host_page`.** A
  query whose content words are all already present in an existing guide's slug
  routes to that guide instead of falling through to `/index.html`; the tightest
  matching guide wins, and a query with fewer than two content words never
  matches. This is the fix `_provider_guide` should have been: it catches "york
  gutters" against `gutters-york-pa.html` and all three "5 inch vs 6 inch"
  phrasings plus "what size gutters do i need" against the size guide that
  already exists, while leaving genuinely new topics alone.
- **`growth/test_techniques.py` — new.** Ten tests over both guards, written
  against the two failures that actually happened rather than against the happy
  path: the exact title that shipped on 07-27, the exact duplicate that shipped
  this morning, and the three queries that must still earn their own page.

Verified rather than eyeballed: `_host_page` run against the real docroot for
all 65 uncovered queries before and after, fall-through 7 → 3 with no in-area
town or service query re-routed; `GEO_ANCHOR` checked against the two real
homepage titles and against "repair"/"page" for false positives.

I did not touch `techniques.json`, `keywords.json`, `results.jsonl` or
`state.json`; did not activate any candidate; did not edit `index.html` or any
page under `areas/`, `guides/` or `services/` — all of those are copied
droplet → repo every morning and an edit here is reverted by tomorrow.

### Reasoning and uncertainties

**I cannot prove the homepage title cost anything, and I am not going to imply
otherwise.** There is no counterfactual: I do not have a week of the old title
against a week of the new one under comparable conditions, and the 28-day
rolling window means every number moves for reasons unrelated to any change.
Three confounders are live at once — the window accumulates queries mechanically,
a four-week-old site broadening into odd geographies is ordinary while Google
works out what it is, and 336 impressions is a sample thin enough that zero
clicks is not statistically astonishing on its own. What I am confident about is
narrower and sufficient: the title names no place, it used to, this engine
changed it, no code path could have prevented it, and restoring it is free and
reversible. I would rather act on a solid mechanism with an uncertain magnitude
than wait for significance that 336 impressions will never deliver.

**My 07-31 fix was too narrow and I said it was solved.** That is the most
useful thing in today's entry for whoever reads this journal later. The
diagnosis was right — the engine was building near-duplicate guides — but I
encoded it as a list of words about firms, and the very next morning it shipped
a duplicate through a route the word list could not see. Today's replacement
tests topic overlap instead, which generalises. It may well have its own blind
spot; if a seventh overlapping guide appears, the answer is probably that
`money_pages` should require a positive reason to write rather than merely the
absence of a host page.

**The deploy gap is the finding I am most sure of and least able to fix.** It
rests on a key present in this repo's `SERIES` and absent from the snapshot the
droplet produced this morning, with no inference in between. This journal has
now described five separate fixes in language implying they were handled. They
were written down. On the strength of today, I would rather the next entry
opened by checking what is actually running than by adding a sixth.

**What would change my mind.** If clicks on the geo-agnostic head terms stay at
zero for three weeks *after* the homepage title is restored, then the local pack
and the AI Overview are taking those taps and no snippet will recover them — at
which point the honest conclusion is that organic clicks are not this site's
channel, and the effort belongs on the profile and offline candidates (T007,
T022, T021, T012, T027) rather than a thirty-sixth page. If clicks start
tracking impressions instead, recommendation 5 becomes the most important item
on the list, because after mid-August the leaf-fall window closes and that
question gets answered a year late. Either way, the goal metric has not moved in
six days, every town in the county is still at zero, and the business has one
booking to its name. The engine is healthy. Whether it is earning anything is
still unknown, and will stay unknown until the grace period ends on 26 August.

## 2026-08-02 — engine run

Goal: **1.7%** top-3 share of 117 tracked queries (target 50%).
2026-08-01: 6 visitors (0 organic, 0 maps) · 0 bookings, 0 phone leads.

**Built:**
- `adopt_queries` — ok: no new in-area searches worth tracking
- `improve_ctr` — ok: no page is due a snippet rewrite
- `geo_answer_first_content_pass` — ok: answer-first opening on /guides/seamless-vs-sectional-gutters.html for 'seamless vs sectional gutters' (53 words, + FAQ schema, 6 impressions)
- `strengthen_pages` — ok: added "How to Choose the Best Gutter Company in Dallastown, PA" to /areas/seamless-gutters-dallastown-pa.html for 'best gutter company dallastown pa'
- `service_pages` — ok: every queued service already has a page
- `area_pages` — ok: published Jacobus (12,867 bytes; 0 town(s) left in the queue)
- `money_pages` — ok: published 'gutter pulling away from house' → /guides/gutter-pulling-away-from-house.html
- `internal_links` — ok: refreshed nearby-links on 6 page(s)
- `local_schema` — ok: LocalBusiness schema already current
- `rebuild_sitemap` — ok: [gen_sitemap] wrote 37 URLs to sitemap.xml
- `ping_indexnow` — ok: submitted 9 URL(s), HTTP 200

**Scout proposed (as candidates, not running):**
- T030 Trade-partner referral loop (roofers, siders, painters) — Every roof replacement and siding job in York County ends with gutters off the house and someone has to hang them back. Roofing crews in York, Dover and Red Lion mostly sub that work out or fumble it.
- T031 Leaf-season callback to past customers and unsold estimates — Eric already has a small list of people who bought from him and a larger one who got a quote and never called back. In York County the fall leaf-fall window is when a homeowner will finally say yes to
- T032 Answer recommendation threads in York County Facebook groups — 'Anyone know a good gutter guy?' gets posted in York, Dover, Dallastown and Red Lion township Facebook groups every single week, and each of those posts is a homeowner buying within 30 days — the exac

## 2026-08-02 — review agent

### Lead: the deploy finally happened, the content engine ran out of work on the same morning, and the goal metric has not moved once in six days of measurement

Three things, in the order they matter.

**One: `growth/` is on the droplet.** Yesterday's recommendation #2 named a
specific falsifiable test — "`call_taps` and `ai_calls` appear in tomorrow's
`snapshot.json` `traffic` block". They are both there. This is the first
recommendation in this journal that has been acted on, and it cleared a backlog
of seven fixes across three days. Details and the two corroborating signs are in
the section below.

**Two: `area_pages` has run out of towns.** `TOWN_QUEUE` at
`growth/techniques.py:49` holds exactly ten towns. Today's build published
Jacobus, the tenth, and logged `0 town(s) left in the queue`. From tomorrow
morning `area_pages` returns `{"noop": True, "detail": "every queued town
already has a page"}` and does so every morning after that. **T001 — the
technique the ledger calls "the highest-leverage thing a contractor site can
own" — is now inert**, and the verdict `review.py` is scheduled to pass on it on
26 August will be computed over a series that stopped growing today. That needs
a decision, not a default.

**Three: six daily snapshots since the goal became measurable, and the number is
2 in every one of them.** Not 2 then 3 then 2. Two, six times. Every named town
in York County — York, Dover, Red Lion, Dallastown, Spring Grove, Hanover — is
at zero top-3, and five of those six have had a dedicated page for the whole
period. Having a page is not the thing that was missing.

Also still true, and still nobody's done it: the homepage title names no place
(day 2 of asking), and the Akron/Lancaster paragraph is live on the gutter-guards
page (**day 5**).

### Where the numbers stand

The goal metric — tracked York County queries holding a top-3 position:

| | 07-28 | 07-29 | 07-30 | 07-31 | 08-01 | 08-02 |
| --- | --- | --- | --- | --- | --- | --- |
| **top-3 count** | 2 | 2 | 2 | 2 | 2 | **2** |
| tracked queries | 76 | 87 | 87 | 98 | 108 | **117** |
| share (`top3/total`) | 2.6% | 2.3% | 2.3% | 2.0% | 1.9% | **1.7%** |
| top-10 count | 7 | 6 | 6 | 6 | 6 | **6** |
| coverage proxy | 48.7% | 44.8% | 46.0% | 42.9% | 40.7% | **39.3%** |
| `ranked_known` | — | — | — | 21 | 21 | **22** |

Against the denominator that means something — the 22 queries Search Console has
actually returned a position for — the share is **2 of 22, 9.1%**, down from
2 of 21 (9.5%) because a query joined the ranked set and it wasn't a top-3 one.
Against all 117 it is 1.7%, and it fell for the fifth consecutive day for the
fifth consecutive time because somebody added queries, not because anything got
worse. Fifth entry flagging this.

Per town (`covered` / `total`, all at **0 top-3** except the county bucket):

| bucket | total | covered | top-3 |
| --- | --- | --- | --- |
| county | 68 | 27 | **2** |
| york | 12 | 4 | 0 |
| dover | 11 | 3 | 0 |
| red-lion | 7 | 2 | 0 |
| dallastown | 7 | 3 | 0 |
| hanover | 6 | 4 | 0 |
| spring-grove | 6 | 3 | 0 |

By intent, `covered/total`: hire **40/77 (52%)**, price **3/22 (14%)**, check
**2/11 (18%)**, diy **1/7 (14%)**. Keep those four numbers in mind for
recommendation 6 — the build queue sorts hire first, and hire is the one bucket
already half done.

Search Console, 28-day rolling:

| | 07-28 | 07-29 | 07-30 | 07-31 | 08-01 | 08-02 |
| --- | --- | --- | --- | --- | --- | --- |
| rows | 77 | 87 | 97 | 189 | 219 | **277** |
| matched | 17 | 19 | 21 | 21 | 21 | **22** |
| clicks | 3 | 3 | 3 | 5 | 6 | **7** |
| impressions | 429 | 497 | 686 | 975 | 1,167 | **1,588** |
| avg position | 12.4 | 13.9 | 12.5 | 17.0 | 18.3 | **20.9** |

Site-wide CTR is **7 clicks on 1,588 impressions, 0.44%**. Impressions have
grown 270% in five days and clicks have grown by four. `matched` moved for the
first time in four days, 21 → 22, while `rows` grew by 58 — the visibility this
site is accumulating is almost entirely in queries nobody chose to track.

The nine geo-agnostic head terms yesterday's entry called out (`gutter installer`,
`gutter contractor`, `gutter guard installer`, `gutter soffit and fascia
replacement`, `gutters`, `gutter replacement`, `gutter repair`, `gutter cleaning`,
plus `gutter replacement services` replacing `seamless spouting` in today's
top-40) now carry **353 impressions and zero clicks between them**. Three sit at
position 1. `gutter installer` is 212 impressions at position 1.0 — byte-identical
to yesterday, so it took no new impressions in 24 hours either.

Out-of-area rows in `discovered_untracked`: **31 of 40, 219 impressions**
(yesterday 29 of 40). Bryn Mawr, Ardmore, Villanova, Wynnewood, Gladwyne, Chadds
Ford, Garnet Valley, Crum Lynne, Essington — the Philadelphia Main Line and
Delaware County. Donora, Morgan, Bulger, Belle Vernon, Finleyville, New Brighton
— greater Pittsburgh. Myerstown, Newmanstown, Perkasie, Wilkes-Barre. York
*South Carolina*, four separate queries. Alamo Heights, Texas. And **zero rows
naming a York County town.** Not one. The county this business serves is absent
from the list of places Google thinks it might be for.

Traffic:

| | 07-27 | 07-28 | 07-29 | 07-30 | 07-31 | 08-01 |
| --- | --- | --- | --- | --- | --- | --- |
| visitors | 9 | 11 | 14 | 7 | 6 | **6** |
| pageviews | 26 | 24 | 37 | 12 | 14 | **7** |
| organic | 0 | 1 | 3 | 3 | 1 | **0** |
| direct | 6 | 10 | 8 | 3 | 4 | **6** |
| local (maps) | 0 | 0 | 0 | 0 | 0 | **0** |
| AI-referred | 0 | 0 | 0 | 0 | 0 | **0** |
| bot hits | 1,948 | 1,954 | 2,374 | 1,200 | 3,162 | **1,412** |

Six visitors, **seven pageviews** — 1.17 pages per visitor, against 2.6 on 07-29.
Zero organic. Maps, AI and referral are still flat zero across every day on
record.

Now that `call_taps` is finally in the snapshot, here is what it says:

| | 07-30 | 07-31 | 08-01 |
| --- | --- | --- | --- |
| `call_taps` | 0 | 0 | **0** |
| `ai_calls` | 2 | 0 | **0** |

**Three days of first-party tap-to-call measurement and nobody has tapped the
number.** On ~6 visitors a day that is entirely unsurprising and proves nothing
about the button; what it does mean is that the channel is now instrumented and
the reading is honest. `ai_calls` has one non-zero day, 07-30 — the same day as
the site's only booking. One booking all-time, zero phone leads all-time,
`own_rows_excluded` unchanged at 13.

**The measurement-is-broken watch is not triggered.** 9/11/14/7/6/6 with organic
non-zero on four of the six days is a small site, not an over-broad filter in
`metrics.py`. If organic sits at zero for the rest of this week I will revisit.

### Did previous changes work?

**08-01 rec #2 — "Deploy `growth/` to the droplet" — DONE, and it is the first
recommendation from this journal that has been.** The named test passed:
`call_taps` and `ai_calls` are in today's `traffic` block and were absent
yesterday. Two independent corroborations that the sync included more than
`snapshot.py`: `adopt_queries` logged *"no new **in-area** searches worth
tracking"*, which is the out-of-area filter written on 07-29; and `money_pages`
published `gutter-pulling-away-from-house`, one of exactly three queries the
08-01 entry predicted would survive `_topic_guide` as a legitimate fall-through,
rather than a fourth near-duplicate of the size guide. **Honest limit:** I cannot
directly observe the droplet, so I am inferring from three behaviours that a sync
happened, not reading a file. I have not verified `GEO_ANCHOR` specifically —
nothing in today's run exercised it (`improve_ctr` no-op'd: "no page is due a
snippet rewrite").

**08-01 rec #1 — homepage title — NOT done, and the guard does not fix it.**
`index.html` in this repo, which `publish_state.sh` copies droplet → repo, still
reads:

> title: `Gutter Installer & Contractor | NEMO Seamless Gutter`
> description: `Seamless gutters and gutter guards formed on-site to fit your
> home. Free on-site estimate, same-week scheduling. Call (717) 578-0073.`

Neither names York, York County or PA. Worth being explicit about something the
08-01 entry left implicit: **`GEO_ANCHOR` prevents a recurrence, it does not
repair the page.** It rejects a *new* rewrite that names no place; it has no
opinion about a placeless snippet already sitting on disk. The homepage is also
inside its 21-day `ctr_rewrites` cooldown until ~08-17, so the engine will not
revisit it on its own. This one only gets fixed by a human typing it.

**"Fix the Akron/Lancaster paragraph" (07-29 #1, 07-30 #2, 07-31 #1, 08-01 #3) —
not acted on. Fifth day.** Still live verbatim at `services/gutter-guards.html:163`:
"installs gutter guards on homes in Akron, PA and the surrounding Lancaster and
York County area."

**"Reorder the content queue for leaf-fall" (07-30 #3, 07-31 #5, 08-01 #5) — not
acted on. Fourth day.** `order = {"hire": 0, "price": 1, "check": 2, "diy": 3}`
is now at `growth/techniques.py:435` and `:834` (the line numbers moved because
of yesterday's additions; the dict did not).

**"Fix the goal-share denominator" (07-29 #3, 07-31 #6, 08-01 #6) — not acted
on.** `growth/keywords.py` still computes `share_pct` as `top3 / total`. I chose
**not** to change it myself — redefining the headline metric on day six of a
six-day series destroys the only comparison anyone has. What I did instead is
document `ranked_known` in `growth/README.md` so the honest denominator is at
least discoverable by whoever reads that file next. See "what I changed" below.

**T007 (ask finished jobs for a Google review) — still `candidate`,
`activated: null`. Seventh day of asking.**

**My 07-29 prediction — "3 clicks becomes 15–20 by mid-August while top-3 stays
at 2" — is on track and I now think it was a badly formed prediction.** Clicks
have gone 3 → 3 → 3 → 5 → 6 → 7, roughly +1/day, and mid-August at that rate
lands inside the band. Top-3 is still 2. But `clicks` here is a **28-day rolling
total** on a site Google only began crawling in earnest in late July, so the
window is still filling: the count rises mechanically whether or not any given
day is better than the one before. Set against it, *daily* organic visitors have
gone 3 → 3 → 1 → 0. A rolling total climbing while the daily series decays is
exactly what window-fill looks like. **I am replacing the prediction rather than
letting it come true for free:** by 2026-08-16, either daily `organic_visitors`
holds a 7-day median of ≥2, or I will call the click growth an artifact of the
window and stop citing it.

**T001 / T002 / T018 remain inside the 30-day grace to ~2026-08-26.**
`owned_visitors` 07-27 → 08-01: T001 `2/0/3/0/0/0`, T002 `2/0/2/0/0/0`, T018
`3/0/3/0/0/0`. Four consecutive zero days each. On six-visitor days that is
noise and I am not calling it anything else — but it is four in a row, and T001
can no longer add to its own series (see the lead).

**T014 has been running since 27 July and could never have been judged.** New
finding, mine, and a defect rather than a recommendation. `geo_answer_first_content_pass`
sits in the ledger as `status: "active"` with `activated: null`. `_days_active`
in `growth/review.py` read a missing `activated` as **0**, so `evaluate` returned
*"only 0d active — under the 30d grace period"* — and would have returned that
every day forever. A technique that can never leave the grace period can never be
retired or found redundant, in the one module whose entire job is deciding that.
`ledger.set_status` does stamp `activated`, so the normal path was fine; T014
reached the ledger active by some other route. Fixed today with tests.

### What I checked in the code before recommending anything

- **`TOWN_QUEUE`, counted rather than assumed.** `growth/techniques.py:49` — ten
  tuples, all ten now present in `snapshot.pages.areas` (which lists 15, the ten
  plus the five hand-built ones). `area_pages` at `:276` returns the `noop` on an
  empty `todo`. There is no code path that adds a town.
- **Whether the site is telling Google it works outside York County. It is not.**
  `_provider_ld()` (`growth/techniques.py`) emits
  `areaServed: {"@type": "AdministrativeArea", "name": "York County,
  Pennsylvania"}`, and the homepage's parsed JSON-LD `RoofingContractor` node
  says the same, with a York PA street address. **So the Main Line / Pittsburgh /
  York-SC impressions are not caused by anything in the site's structured data,
  and I am not going to blame the site for them.** That leaves the Business
  Profile service-area list (which I cannot see) or Google simply exploring a
  young site — see the recommendation and the uncertainties.
- **The overlapping-guides question, measured instead of eyeballed.** Six of the
  thirteen guides answer some version of "what does gutter work cost in York
  County / who should I hire": `gutter-guys-near-me`, `gutter-installer-near-me`,
  `gutter-services-near-me`, `gutters-york-pa`, `york-gutters`,
  `best-gutter-company-york-county-pa`. Three of them —
  `gutter-guys-near-me`, `gutters-york-pa`, `york-gutters` — share a near-identical
  H2 skeleton: price ranges in York County 2026 → what moves your number → 5-inch
  or 6-inch → guards → how to get a real number. **But I ran word-level
  `SequenceMatcher` across all 78 pairs of guide pages and not one pair exceeds
  0.30.** The prose is genuinely different. This is duplication of *purpose*, not
  of text, exactly as the 08-01 entry found for the one pair it checked. I am
  ranking the recommendation accordingly — low, and hedged.
- **Checked and NOT recommending, because it is already shipped:** FAQPage schema
  (`_faq_ld()`, on every generated page); the sticky tap-to-call bar
  (`templates.py:160`); `rel="canonical"` on every generated page
  (`templates.py:33`); IndexNow (T006 active, 9 URLs today); `tel:` tap counting
  (`metrics.py`, and now visible in the snapshot). **Checked against the ledger
  and not filing as new:** every off-site idea today's research touches is already
  T007, T011, T016, T022, T025, T026 or T029.

### What I researched today

Skipped everything already sitting in the ledger as T011–T032; re-searching those
turns the ledger into noise.

- **Near-duplicate *sets* of location pages, not individual thin pages, are what
  the 2026 helpful-content classifier is reported to target** — with the working
  standard given as roughly 60–70% of each page being unique and
  location-specific, and the recommended remedy being consolidation onto a
  service-area hub with 301s from the weaker duplicates rather than more pages.
  ([Netco Design](https://netcodesign.com/role-of-service-area-pages-seo/),
  [Construction Marketing Services](https://constructionmarketingservices.com/keyword-cannibalization-contractor-seo/),
  [Hook Agency](https://hookagency.com/blog/local-seo-for-home-service-businesses/))
  What it changes: it is the argument *against* extending `TOWN_QUEUE` by
  another ten towns as the reflex answer to the queue running dry, and it is
  the frame for the six-guide finding above.
- **A wide service-area setting is reported not to affect rank directly, but to
  act as a geographic filter and to dilute relevance where you actually work.**
  Sterling Sky's position is the specific one worth citing: the service area
  decides *where you can appear*, not *how well you rank*, while the broader 2026
  advice is that a list covering more ground than you truly serve reads as "not
  particularly relevant anywhere".
  ([Sterling Sky](https://www.sterlingsky.ca/does-the-service-area-in-google-my-business-impact-ranking/),
  [Hibu](https://hibu.com/blog/industries/why-setting-your-electrician-business-radius-too-wide-hurts-your-google-maps-ranking-and-how-to-fix-it),
  [RankAI](https://rankai.ai/articles/service-area-business-google-business-profile-guide))
  Relevant because 31 of 40 discovered rows are out-of-area and the site's own
  schema is clean — which makes the profile the next place to look, and makes
  this a five-minute check rather than a project.
- **Position 1 with zero clicks now has named mechanisms.** Four are given: AI
  features registering impressions that can never become clicks (position-one CTR
  measured falling ~78% when an AI Overview is present, an Ahrefs figure this
  journal has now met twice); an average position between 8 and 30 where CTR is
  near zero; ranking for queries whose searcher wanted something else; and
  snippets that don't earn the click. The recommended diagnosis is to segment
  Search Console by query class rather than chase rank.
  ([Stridec](https://www.stridec.com/blog/zero-click-search-problem/),
  [Sort the Clicks](https://sorttheclicks.com/insights/impressions-but-no-clicks/),
  [Click Laboratory](https://www.clicklaboratory.com/content-analytics/declining-click-through-rates-page-one/))
  Note the third mechanism against this site's own data: `gutter installer` at
  position 1 with 212 impressions and no place name anywhere in the snippet is a
  textbook case of ranking for a query whose searcher wanted a local business and
  was shown something that looks national. That is two independent reasons for
  recommendation 1, and it is also a caution — some of those 353 impressions may
  be unrecoverable no matter what the title says.
- **Review recency over review volume, again.** The 2026 framing is that a
  business picking up two or three real reviews a month with owner responses
  outranks a competitor sitting on hundreds of stale ones, and that AI Overviews
  above the map pack cite the businesses that already have strong profiles — so
  the profile work and the AI-citation work are the same work.
  ([Wolfpack Advising](https://wolfpackadvising.com/blog/how-to-rank-higher-on-google-maps/),
  [SEOLocale](https://seolocale.com/google-map-pack-ranking-in-2026-how-the-local-3-pack-really-works/))
  Third independent source pointing at T007. Filed as more weight on an existing
  candidate, not as a new one.

**Rejected:** paid "AI visibility" packages (fourth time; the underlying work is
still schema, NAP and honest answers); `llms.txt` (re-rejected 07-30, nothing
new); geo-grid rank trackers (measurement, not calls); and — specific to today —
**extending `TOWN_QUEUE` with the next ten boroughs**, which is the obvious
answer to the empty queue and which I think is wrong, for the reasons in
recommendation 3.

### Recommendations

**Everything below needs a deploy or a droplet action before it does anything.**
`/var/www/nemo-seamless-gutter` is not a git checkout and `publish_state.sh`
copies droplet → repo only. The two repo files I changed today are inert until
synced.

1. **Put York back in the homepage title and description — on the droplet.**
   *(Divine — minutes. Free. Day 2.)* Unchanged from yesterday and now with a
   second, independent reason behind it: "ranking for a query whose searcher
   wanted something else" is one of the four named causes of position-1-zero-clicks,
   and a placeless snippet on `gutter installer` is exactly that. Suggested text
   is in the 08-01 entry. **`GEO_ANCHOR` does not do this for you** — it blocks a
   future placeless rewrite, it does not repair the one on disk, and the page is
   in cooldown until ~08-17 anyway. Checked: `index.html` `<title>` and
   `<meta name="description">` in today's post-publish tree; `GEO_ANCHOR` at
   `growth/techniques.py:1020` and its use at `:1124` — a rejection test on new
   output only.
2. **Fix the Akron/Lancaster paragraph.** *(Divine — minutes, droplet access.
   Free. Day 5.)* Rewrite the `<p class="lead">` under the
   `<!-- geo:answer-first -->` marker to name York County and nothing else, and
   drop that path from `geo_answered` in `state.json` so the corrected pass can
   redo it. Five days is long enough that it is worth saying plainly: this is a
   page telling York County searchers the business is in Lancaster County.
   Checked: `services/gutter-guards.html:163`, still there.
3. **Decide what `area_pages` does now the queue is empty — and my
   recommendation is: not more towns.** *(Divine, one ledger decision; Eric if he
   disagrees. Free.)* The reflex is to add boroughs 16–25. The evidence against:
   the six towns with tracked queries all have pages, all six sit at **0 top-3**,
   and their coverage is 2–4 of 6–12 queries each — the existing pages are not
   winning and are not even complete. The 2026 research says near-duplicate
   location page *sets* are precisely what gets treated as doorway pages. And
   `strengthen_pages` — which deepens a page that already exists, and which added
   a real Dallastown section this morning — is the technique with a live
   mechanism for those zeros. Concretely: leave T001 no-op'd or retire it with an
   honest verdict, and let the morning slot go to `strengthen_pages` and
   `money_pages`. **If it is extended anyway, extend it toward demand, not
   alphabetically** — but note that `discovered_untracked` contains zero York
   County town queries, so there is currently no demand signal to aim at.
   Checked: `TOWN_QUEUE` (`growth/techniques.py:49`, ten entries, all published),
   `area_pages` (`:276`), `keywords.by_town` in today's snapshot, today's build
   log line `published Jacobus (…; 0 town(s) left in the queue)`.
4. **Answer T007 — yes or no.** *(Eric — one decision. Free. Day 7.)* Third
   independent source in a week says review *recency* beats volume and that the
   businesses cited above the map pack by AI are the ones with strong profiles.
   13 reviews at 4.2 with nobody being asked is still the largest untouched lever
   in the ledger, and it is the only one that feeds the map pack, the AI answers
   and the phone at once. A "no" closes it honestly. Checked: `activated: null`
   in today's snapshot.
5. **Check the Business Profile's service-area list.** *(Eric — five minutes.
   Free.)* 31 of 40 discovered query rows are out-of-area — the Philadelphia Main
   Line, greater Pittsburgh, York South Carolina — and **zero** name a York County
   town. I checked and the site is not the cause: `_provider_ld()` and the
   homepage JSON-LD both declare `areaServed: York County, Pennsylvania` against
   a York PA address. So if the profile lists a wide radius or a long town list
   beyond where Eric actually drives, that is the remaining on-our-side
   explanation and it is a two-minute fix; if it is already tight, this costs five
   minutes and rules the last controllable cause out. How you would know: the
   out-of-area share of `discovered_untracked` falling from 31/40 over three to
   four weeks. **Honest caveat: a young site collecting odd geographies while
   Google works out what it is, is ordinary, and this may simply be that.**
6. **Reorder the content queue for leaf-fall.** *(Divine — the sort in
   `money_pages` and `strengthen_pages`. Free. Day 4.)* New numbers in support:
   hire intent is **40/77 covered (52%)**, price is **3/22 (14%)**, check is
   **2/11 (18%)**. The sort puts hire first, so the engine keeps working the one
   bucket that is already half done while cleaning, guard, overflow and cost
   queries — the ones York County homeowners search from mid-October — wait
   behind it. Pages take 8–12 weeks to rank. The window has closed by two more
   days. And with the town queue empty, `money_pages` and `strengthen_pages` are
   now most of what the engine does each morning, which makes their sort order
   matter more today than it did yesterday. Checked: `growth/techniques.py:435`
   and `:834`.
7. **Pick one canonical "gutter cost in York County" guide and 301 the
   duplicates — low priority, and hedged.** *(Divine — a nginx redirect block.
   Free.)* Six guides answer that question; three share a near-identical heading
   skeleton. **But every pairwise word-level similarity across the 13 guides is
   below 0.30, so this is redundancy of purpose, not duplicated text, and I
   cannot show from the data I have that it is costing anything** — I have no
   per-page Search Console data in the snapshot to prove the three are competing
   for the same query. Ranked seventh for that reason. If it is done, keep
   `gutters-york-pa.html` (the title that names the place) and redirect
   `york-gutters.html` and `gutter-guys-near-me.html` into it. Checked: titles
   and H2s of all six; `difflib.SequenceMatcher` over all 78 guide pairs;
   `rel="canonical"` already present on every generated page (`templates.py:33`).
8. **Carried, unverifiable from this repo, not restated at length:** T022
   (itemised GBP Services + weekly job photo), T029 (Apple Business + Bing
   Places), T016 (GBP category audit), the four GBP owner questions, the ~30-page
   town cap. Open until someone says otherwise.

### What I changed in this repo today

Two files. Neither is live until `growth/` is synced to the droplet again. All
**98** tests pass across the six test modules (86 before, 12 new). Note for the
record: the 08-01 entry reported 81, but `f55fd99` ("Treat what the model writes
as untrusted input") added five more after it was written — the count was right
when it was made and is stale now, which is the ordinary hazard of quoting a
total in an append-only log.

- **`growth/review.py` — `_since()`, and `_days_active` falling back to `added`.**
  This is the T014 fix. A technique that is `status: "active"` with
  `activated: null` was being read as zero days old, permanently, which parked it
  inside the grace period forever and made it unjudgeable and un-retirable.
  `_since()` returns `activated or added` — the honest floor, since whatever day
  a technique started running it was not before the day it existed — and both
  `_owned()` and the site-wide before/after split now use it, so an undated
  technique gets a real baseline comparison instead of an empty `before` window.
  `set_status` was never the broken path and is untouched.
- **`growth/test_review.py` — new, 12 tests.** Written against the state that
  actually exists rather than the happy path: T014 as it stood this morning,
  `activated` correctly winning over `added` for a candidate switched on later, a
  genuinely three-day-old technique still protected by the grace period, and
  unparseable dates still returning 0 rather than raising inside the module that
  retires things autonomously.
- **`growth/README.md` — the "goal metric, honestly" section.** It still said
  Search Console was "**not connected yet**" and that `share_pct` is `null` and
  the report says `UNMEASURED`. That has been false for six days and it is the
  file a new reader orients from. Replaced with what is actually true, including
  the `ranked_known` denominator and why the headline share falls on mornings
  when nothing got worse — which is the honest version of the fix recommended
  three times and not yet made in `keywords.py`.

I did not touch `techniques.json`, `keywords.json`, `results.jsonl` or
`state.json`; did not activate, retire or re-status any technique; did not edit
`index.html` or any page under `areas/`, `guides/` or `services/`, all of which
are copied droplet → repo every morning and would be reverted tomorrow.

### Reasoning and uncertainties

**The most important thing in today's numbers is a non-event.** Six measured
days, full-speed publishing every morning — 15 town pages, 13 guides, 7 service
pages, sitemap, IndexNow, link mesh — and the goal metric is 2 on every single
one of them. Six days is far too short to conclude the content engine does not
work; local SEO takes 8–12 weeks and `review.py` is right to hold its verdict to
26 August. But it is long enough to say that **nothing so far is evidence that it
does**, and long enough that the queue running dry today is a good moment to ask
whether the next intervention should be the same intervention. Every town with a
page is at zero. That is the fact I keep returning to.

**Where I am least sure: the out-of-area impressions.** I have ruled out the
site's structured data, which is the part I can actually inspect, and that is
worth something. What is left is a profile setting I cannot see and a null
hypothesis I cannot dismiss — Google exploring a five-week-old site and
provisionally showing it for things it half-matches. Under that hypothesis the
Main Line rows are meaningless noise that will decay on their own, and
recommendation 5 costs Eric five minutes to rule out the alternative. I would not
spend more than five minutes on it.

**Where I may be wrong about the town pages.** Recommendation 3 argues against
more towns on the grounds that the existing ones are not ranking. The honest
counter is that they have had five to thirty days and need eight to twelve weeks
— judging a town-page strategy on a fortnight is exactly the error this journal
keeps warning about. What makes me hold the line anyway is that the argument for
*stopping* does not depend on the existing pages having failed; it depends on
there being a better use of the daily slot, and `strengthen_pages` filling in the
2-to-4-of-11 coverage gaps on pages that already exist is that better use. If by
early September the town pages start pulling top-10 positions, the queue should
be extended and I will have been wrong to slow it.

**What I got wrong before and am correcting today.** My 07-29 click prediction
was framed against a 28-day rolling total on a site whose window was still
filling, which made it nearly unfalsifiable — it was going to come true whether
or not anything improved. Yesterday's entry cited it as "on track" without
noticing. It is replaced above with a daily-median test that can actually fail.

**What would change my mind.** If daily organic visitors hold a 7-day median of
≥2 by 16 August, the content engine is working and recommendation 6 (leaf-fall
ordering) becomes the most valuable item on the list, because after mid-August
that window shuts for the year. If they stay at 0–1 while impressions keep
climbing, then this site's problem is not visibility and no thirty-eighth page
fixes it — the honest conclusion becomes that organic clicks are not this
business's channel, and everything should move to the profile and the offline
candidates (T007, T016, T022, T030, T031). Either way: six days measured, top-3
stuck at 2, every town in the county at zero, zero call taps, and one booking to
the business's name. The engine is healthy and it deployed cleanly for the first
time. Whether it is earning anything is still unknown.

## 2026-08-03 — engine run

Goal: **1.6%** top-3 share of 122 tracked queries (target 50%).
2026-08-02: 9 visitors (0 organic, 0 maps) · 0 bookings, 0 phone leads.

**Built:**
- `adopt_queries` — ok: no new in-area searches worth tracking
- `improve_ctr` — ok: no page is due a snippet rewrite
- `geo_answer_first_content_pass` — ok: answer-first opening on /services/half-round-gutters.html for 'Half-Round Gutters in York, PA' (51 words, + FAQ schema, 5 impressions)
- `strengthen_pages` — ok: added "Gutter Replacement Near You in York County, PA" to /services/seamless-gutter-installation.html for 'gutter replacement near me'
- `service_pages` — ok: every queued service already has a page
- `area_pages` — ok: every queued town already has a page
- `money_pages` — ok: published 'ice dams gutters pennsylvania' → /guides/ice-dams-gutters-pennsylvania.html
- `internal_links` — ok: refreshed nearby-links on 0 page(s)
- `local_schema` — ok: LocalBusiness schema already current
- `rebuild_sitemap` — ok: [gen_sitemap] wrote 38 URLs to sitemap.xml
- `ping_indexnow` — ok: submitted 3 URL(s), HTTP 200

**Scout proposed (as candidates, not running):**
- T033 Reply to all 13 reviews, publicly fix the low ones — 300 GBP views a month produce zero calls, and the profile shows 4.2 stars with 13 reviews and (almost certainly) no owner replies. A York homeowner comparing three gutter installers on Maps sees a 4.2
- T034 One real job page per completed install, photographed and dated — The site has town pages and guides but zero proof — and for a one-truck contractor with 13 reviews, proof is the thing that makes a stranger dial instead of bounce. Publishing a short page per finishe
- T035 Claim Yelp page, switch on Request a Quote, answer inside the hour — This is the one channel that hands Eric a named York County homeowner with a stated gutter problem for zero dollars, rather than hoping a ranking becomes a call. Yelp quote requests cost nothing to re

## 2026-08-03 — review agent

### Lead: the two "position 1" queries this journal has cited for four days are dead, and `local_visitors` cannot see the map pack at all

Two findings, both corrections of things believed here on the basis of numbers
that do not mean what they were read to mean.

**One: `gutter installer` at position 1 with 212 impressions is not live
visibility. It stopped on 27 July.** The row has been byte-identical in five
consecutive daily snapshots while other rows moved every day. Search Console's
window here ends three days back, so five frozen days means literally zero
impressions on 07-28, 07-29, 07-30 and 07-31. Working numbers below. This
journal has cited those impressions three days running as an audience being
wasted by a placeless homepage title. The title should still be fixed; the
argument that it recovers a live audience should not be made again.

**Two: `local_visitors` is structurally incapable of counting Google Business
Profile traffic, and four ledger techniques are scored on it.** `LOCAL_HOSTS`
(`growth/metrics.py:63`) matches `"google.com/maps"` against the referrer
string, but Google strips the path from cross-origin referrers by default, so a
GBP website click arrives as `https://www.google.com/` and falls through to
`SEARCH_HOSTS` as **organic**; from the Maps mobile app it arrives with no
referrer at all and lands in **direct**. T004 (active), T007, T008 and T016 all
carry `"metric": "local_visitors"`. **"Maps flat zero on every day on record" —
written in this journal on 07-31, 08-01 and 08-02 — is not evidence that the map
pack sends nothing.** It is a blind spot, and it also plausibly explains why 9
of 9 visitors on 08-02 were classified `direct`. `classify()` already routes
`utm_source=gbp` to `local` (`metrics.py:277-288`); the code has been waiting
for a tag nobody has set. Recommendation 2, two minutes, free.

Still nobody's done it: homepage title names no place (**day 3**), the
Akron/Lancaster paragraph is live on the gutter-guards page (**day 6**), the
leaf-fall queue reorder (**day 5**), T007 unanswered (**day 8**).

### Where the numbers stand

The goal metric — tracked York County queries holding a top-3 position:

| | 07-28 | 07-29 | 07-30 | 07-31 | 08-01 | 08-02 | 08-03 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **top-3 count** | 2 | 2 | 2 | 2 | 2 | 2 | **2** |
| top-10 count | 7 | 6 | 6 | 6 | 6 | 6 | **7** |
| `ranked_known` | 17 | 19 | 21 | 21 | 21 | 22 | **22** |
| tracked queries | 76 | 87 | 87 | 98 | 108 | 117 | **122** |
| share (`top3/total`) | 2.6% | 2.3% | 2.3% | 2.0% | 1.9% | 1.7% | **1.6%** |
| coverage proxy | 48.7% | 44.8% | 46.0% | 42.9% | 40.7% | 39.3% | **39.3%** |

**Top-3 is 2 for the seventh consecutive measured day.** Against the honest
denominator — the 22 queries Search Console has returned a position for — that
is 2 of 22, **9.1%**, unchanged from yesterday. The headline 1.6% fell for the
sixth day running because the tracked universe grew by five queries, not because
anything got worse; sixth entry flagging it, and I am still not changing
`keywords.py:296` mid-series for the reason the 08-02 entry gave.

**One thing moved: top-10 went 6 → 7, the first upward move in six days.** One
query crossed into the top ten. On this volume that is directional at best and I
am not calling it more than that.

Per town (`covered`/`total`), every named town still at **0 top-3**:

| bucket | total | covered | top-3 |
| --- | --- | --- | --- |
| county | 70 | 29 | **2** |
| york | 13 | 4 | 0 |
| dover | 11 | 3 | 0 |
| hanover | 6 | 4 | 0 |
| dallastown | 8 | 3 | 0 |
| red-lion | 7 | 2 | 0 |
| spring-grove | 7 | 3 | 0 |

Search Console, 28-day rolling: rows **287** (+10), matched **22** (flat, third
day), clicks **7**, impressions **1,677** (+89), avg position **21.0**.

Because the window ends three days back and nothing has yet fallen off the far
end, each day's delta is that one day's traffic. Read that way:

| day earned | 07-27 | 07-28 | 07-29 | 07-30 | 07-31 |
| --- | --- | --- | --- | --- | --- |
| impressions | +189 | +289 | +192 | +421 | **+89** |
| clicks | 0 | +2 | +1 | +1 | **0** |

**Clicks did not move today — the first flat day since 07-30 — and impressions
added on 07-31 were a fifth of the day before.** Site-wide CTR is 7 on 1,677,
**0.42%**.

Traffic (nginx, bots and owner IPs excluded):

| | 07-28 | 07-29 | 07-30 | 07-31 | 08-01 | 08-02 |
| --- | --- | --- | --- | --- | --- | --- |
| visitors | 11 | 14 | 7 | 6 | 6 | **9** |
| pageviews | 24 | 37 | 12 | 14 | 7 | **14** |
| organic | 1 | 3 | 3 | 1 | 0 | **0** |
| direct | 10 | 8 | 3 | 4 | 6 | **9** |
| local (maps) | 0 | 0 | 0 | 0 | 0 | **0** |
| AI-referred | 0 | 0 | 0 | 0 | 0 | **0** |
| bot hits | 1,954 | 2,374 | 1,200 | 3,162 | 1,412 | **1,554** |

Second consecutive zero-organic day, and **100% of 08-02's visitors classified
`direct`** — see the lead for why that number should not be trusted as written.
`call_taps` 0 for four days, `ai_calls` 0 for three, `bookings` 0 since 07-30.
All-time: **1 booking, 0 phone leads.**

**The measurement-is-broken watch is still not triggered for the visitor
count** — 11/14/7/6/6/9 with four non-zero organic days in the series is a small
site, not an over-broad filter. The channel *split* is a different matter and is
the lead.

**The engine is running short of work.** Six of eleven techniques no-op'd this
morning: `adopt_queries`, `improve_ctr`, `service_pages`, `area_pages`
(second day since `TOWN_QUEUE` emptied), `local_schema`, and `internal_links`
refreshed 0 pages. Three did real work: one new guide
(`ice-dams-gutters-pennsylvania`), one strengthen section, one answer-first
opening. A week ago it was publishing a town page every morning.

### Did previous changes work?

**The frozen head terms — a correction, not a result.** Pulled every published
snapshot and read one row across all of them:

| snapshot | 07-28 | 07-29 | 07-30 | 07-31 | 08-01 | 08-02 | 08-03 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `gutter installer` | 104@1 | 106@1 | 212@1 | 212@1 | 212@1 | 212@1 | **212@1** |
| `gutter contractor` | 20@1 | 20@1 | 46@1 | 46@1 | 46@1 | 46@1 | **46@1** |
| `gutter guard installer` | 12@1 | 12@1 | 14@1 | 14@1 | 14@1 | 14@1 | **14@1** |
| `gutters` | — | — | 20@5.8 | 21@5.6 | 24@5.6 | 25@5.4 | **46@3.7** |

`gutters` moves every single day and improved four positions overnight, so this
is not a stale pipeline — `growth/gsc.py` fetches live on every run with no
cache. Those three specific rows stopped. Decoded against `LAG_DAYS = 3`:
`gutter installer` earned **+106 impressions on 27 July alone** — more than half
its total — and **zero on each of 07-28, 07-29, 07-30 and 07-31.** Same shape for
the other two. So **272 of the 388 impressions on the geo-agnostic head terms
are a one-day burst that ended six days ago**, not an audience sitting there
waiting for a better title. Verdict on the 08-01/08-02 framing of those numbers:
**wrong, and mine to correct.** The homepage title should still be fixed — a
placeless title on a local business is wrong on its own terms — but its expected
payoff is smaller than this journal has been claiming.

**08-02's replaced prediction — "daily `organic_visitors` holds a 7-day median
of ≥2 by 2026-08-16, or the click growth is a window artifact" — is tracking
against itself but is not yet due.** Median over 07-27…08-02 of `[0,1,3,3,1,0,0]`
is **1**. Two consecutive zeros. Thirteen days left; **too early to tell**, and I
note today's flat click count is the first evidence on the artifact side.

**08-02 rec #1, homepage title — NOT done. Day 3.** `index.html:16-17` still
reads `Gutter Installer & Contractor | NEMO Seamless Gutter` with a description
naming no place. This is authoritative rather than stale: `publish_state.sh`
copies `index.html` droplet → repo every morning, and today's publish commit
(`4e04a51`) did not touch it.

**Akron/Lancaster paragraph (07-29 #1 through 08-02 #2) — NOT done. Day 6.**
`services/gutter-guards.html:163`, and I confirmed something the earlier entries
asserted without showing: it sits **directly under the `<!-- geo:answer-first -->`
marker**, so it is T014's own output, not hand-written legacy copy. I shipped a
guard against recurrence today (below); the guard does not repair the live page.

**Leaf-fall queue reorder (07-30 #3 onward) — NOT done. Day 5.**
`order = {"hire": 0, "price": 1, "check": 2, "diy": 3}` at
`growth/techniques.py:435` and `:834`. Intent coverage today: hire **41/80
(51%)**, price **3/24 (13%)**, check **3/11 (27%)**, diy **1/7 (14%)**. The gap
between the bucket the engine works first and the buckets York County searches in
October has widened by two more queries.

**T007 (ask finished jobs for a Google review) — still `candidate`,
`activated: null`. Day 8.**

**08-02's own repo changes have not taken effect and cannot until someone
deploys.** I read `growth/publish_state.sh`: it copies `growth/snapshot.json`,
`sitemap.xml`, `index.html`, merges `JOURNAL.md`, and rsyncs `areas/`, `guides/`,
`services/`. **It copies no `growth/*.py` in either direction.** So the
`review.py` T014 fix and the README correction are inert, and the droplet→repo
sync cannot overwrite them either. T014 still shows `activated: null` in today's
snapshot, which is consistent with no deploy but does not prove it — the fix
changes a computation, not a stored field.

**08-02 rec #3 — "do not extend `TOWN_QUEUE`" — no action needed, and today's
research supports it.** The March 2026 core update is reported to have hit
templated location pages in home services hardest. I also measured what the
08-02 entry measured for guides but not for areas; see below.

**T001/T002/T018 remain inside grace to ~2026-08-26.** `owned_visitors` is now
**five consecutive zero days** for each. On 6–9 visitor days that is noise, and
T001 can no longer add to its own series.

### What I checked in the code before recommending anything

- **`local_visitors` cannot see GBP.** `LOCAL_HOSTS` at `growth/metrics.py:63`,
  the referrer/UTM branch at `:273-301`, and the four techniques carrying
  `"metric": "local_visitors"` in today's snapshot (T004, T007, T008, T016).
  `classify()` already maps `utm_source=gbp|google-business|gmb` → `local`, so
  no code change is needed — only the tag.
- **Area-page similarity, measured rather than assumed.** The 08-02 entry ran
  `SequenceMatcher` across the guides and found nothing above 0.30; nobody had
  run it across the 15 area pages, which are the pages the doorway-page research
  is actually about. Word-level, tags and scripts stripped, 105 pairs: **max
  0.457** (Hanover | Red Lion), **median 0.227**, min 0.153. Guides for
  comparison: max 0.225, median 0.152. So the town pages are roughly twice as
  alike as the guides and Red Lion appears in three of the four tightest pairs —
  but 0.457 is still inside the 60–70%-unique working standard cited on 08-02.
  **Not an emergency; a reason not to mass-produce more from this template.**
- **Call mechanics are already shipped, so T023 is largely redundant on-site.**
  Floating tap-to-call on every generated page (`growth/templates.py:160`) and
  eight `tel:` links in `index.html` including the hero. The remaining unshipped
  part of T023 is the *answering*, not the button.
- **Checked and NOT recommending, because it is already shipped:** FAQPage
  JSON-LD on every generated page (`_faq_ld`), `rel="canonical"`
  (`templates.py:33`), IndexNow (T006, 3 URLs today), `areaServed: York County`
  in `_provider_ld()`, out-of-area query filtering into the answer-first pass
  (`_names_other_market`, `techniques.py:1170`).
- **Checked against the ledger and not filing as new:** every off-site idea
  today's research touches is already T007, T011, T016, T022, T029 or T035.

### What I researched today

- **GBP signals are the largest single block of local-pack weight — 32% — and
  the primary category is the most influential signal inside it**, with a
  reported case of an HVAC business falling from position 1 to 31 after
  broadening its primary category. Steady new reviews are reported to matter
  more than total count.
  ([SEOLocale](https://seolocale.com/google-map-pack-ranking-in-2026-how-the-local-3-pack-really-works/),
  [Wolfpack Advising](https://wolfpackadvising.com/blog/how-to-rank-higher-on-google-maps/),
  [Green Thumb Local](https://www.greenthumblocal.com/google-maps-rankings-for-home-service-businesses))
  What it changes: T016 moves up the ranking. It is a free dashboard check with
  the largest documented single-signal effect available to this business.
- **AI Overviews appear on ~68% of local searches, and the businesses they cite
  are the ones already ranking in the map pack.**
  ([Search Engine Journal](https://www.searchenginejournal.com/ai-overviews-now-answer-most-local-searches-how-to-get-your-business-cited/580757/),
  [Valley Marketing Group](https://thevalleymarketinggroup.com/blog/google-ai-mode-local-seo-service-businesses-2026/))
  What it changes: it tempers T014. The answer-first pass is worth running, but
  it is downstream of the map pack, not a way around it — which is consistent
  with `ai_visitors` sitting at 0 on every day on record.
- **The March 2026 core update hit templated location pages in home services
  hardest** — pages that swap a city name in and offer nothing else.
  ([Scorpion](https://www.scorpion.co/articles/news/industry-trends-news/googles-march-2026-core-update-what-local-servic/),
  [Optra](https://optramarketing.com/blog/how-googles-algorithm-updates-affected-local-search/))
  What it changes: nothing to do, but it is why I measured the area pages rather
  than trusting the guide result.
- **Google Analytics gained a native Business Profile integration on 8 June
  2026, replacing UTM tagging as the way to see GBP website clicks — for sites
  on GA4.**
  ([PPC Land](https://ppc.land/google-analytics-links-business-profiles-to-report-local-metrics/),
  [Search Engine Journal](https://www.searchenginejournal.com/google-analytics-is-adding-google-business-profile-data/578107/))
  What it changes: this site measures from nginx logs, not GA4, so the
  integration does nothing for it and the UTM tag remains the only way to see
  that traffic. That is what turned a vague suspicion into recommendation 2.
- **Conversion base rates, for calibration.** The median contractor site is
  reported to convert 2–4% of visitors to a call or form; CallRail's 2026 home
  services figure is that replying within 60 seconds lifts conversion 391%.
  ([Social Climb](https://socialclimb.org/local-seo/contractor-website-conversion-essentials/),
  [Hook Agency](https://hookagency.com/blog/contractor-website-design-trends-2026/))
  What it changes: at 9 visitors a day, 2–4% predicts **0.2–0.4 calls per day**.
  Four days of zero `call_taps` on ~28 visitors is exactly the base rate. It is
  not evidence the button is broken, and no amount of conversion work fixes a
  number that small — which is an argument for the map pack, not the page.

**Rejected:** paid "AI visibility" packages (fifth time); geo-grid rank trackers
(measurement, not calls); anything requiring GA4; and **extending `TOWN_QUEUE`**,
re-rejected on today's core-update finding and my own similarity measurement.

### Recommendations

**Everything below needs a droplet action before it does anything.**
`/var/www/nemo-seamless-gutter` is not a git checkout and `publish_state.sh`
copies droplet → repo only, and copies no Python at all. The code I changed today
is inert until `growth/` is synced by hand.

1. **Audit the Business Profile's primary category — and do it in the same
   sitting as #2.** *(Eric — 15 minutes. Free. T016, already in the ledger.)*
   The 2026 sources put GBP signals at 32% of local-pack weight, the largest
   single block, with primary category the most influential item inside it and a
   documented position-1-to-31 fall from broadening one. The category must be the
   most specific true match ("Gutter Cleaning Service" / "Gutter Contractor"),
   not a general "Contractor". How you would know: `top3` moving off 2, or town
   buckets leaving 0 — over four to eight weeks, not days. I cannot see the
   profile from here, so I cannot tell you whether it is already right; that is
   exactly why it is a 15-minute check. Checked: T016 `status: candidate`,
   `activated: null` in today's snapshot — proposed 2026-07-29 and never actioned.
2. **Add `?utm_source=gbp` to the website URL in the Business Profile.**
   *(Eric — two minutes. Free. NEW.)* Without it this site cannot distinguish a
   map-pack click from a plain organic one or from a bookmark, because Google
   strips the referrer path and the Maps app sends no referrer at all. Four
   techniques are scored on `local_visitors` and all four are currently being
   judged blind — including T004, which is **active** and will be handed a
   verdict by `review.py`. How you would know it worked: `local_visitors` becomes
   non-zero within days, and some of what is now `direct` moves into it. Checked:
   `growth/metrics.py:63` (`LOCAL_HOSTS`), `:273-301` (`classify`, which already
   handles the tag). No code change required.
3. **Put York back in the homepage title and description — on the droplet.**
   *(Divine — minutes. Free. Day 3.)* Still right, with a **weaker** stated
   reason than yesterday: the 272 impressions on `gutter installer` and
   `gutter contractor` are dead, so this is no longer about recovering a live
   audience. It is about a local business whose strongest page tells Google and
   every reader nothing about where it works. `GEO_ANCHOR` blocks a future
   placeless rewrite; it does not repair the one on disk, and the homepage is in
   its 21-day `ctr_rewrites` cooldown until ~08-17. Checked: `index.html:16-17`
   in today's post-publish tree; `GEO_ANCHOR` at `growth/techniques.py:1020`,
   used at `:1124` on new output only.
4. **Fix the Akron/Lancaster paragraph.** *(Divine — minutes, droplet access.
   Free. Day 6.)* Rewrite the `<p class="lead">` under `<!-- geo:answer-first -->`
   at `services/gutter-guards.html:163` to name York County and nothing else,
   then drop that path from `geo_answered` in `state.json` so the corrected pass
   can redo it. Sixth day that a page has been telling York County searchers this
   business is in Lancaster County — and it is the exact passage an AI answer
   engine lifts. I shipped the guard against a recurrence today; only a human
   fixes the live page.
5. **Answer T007 — yes or no.** *(Eric — one decision. Free. Day 8.)* Today's
   sources say again that steady new reviews beat total count and that AI
   Overviews cite the businesses already strong in the pack. 13 reviews at 4.2
   with nobody being asked is still the largest untouched lever in the ledger. A
   "no" closes it honestly and stops it being re-proposed every morning.
6. **Reorder the content queue for leaf-fall.** *(Divine — the sort in
   `money_pages` and `strengthen_pages`. Free. Day 5.)* hire is **51% covered**,
   price **13%**, check **27%**, diy **14%**, and the sort works hire first.
   Pages need 8–12 weeks; leaf-fall calls start mid-September. With `area_pages`
   and `service_pages` both no-op'd, these two techniques *are* the engine now,
   so their sort order matters more than it did a week ago. The window has closed
   by another day. Checked: `growth/techniques.py:435` and `:834`.
7. **Sync `growth/` to the droplet again.** *(Divine — minutes.)* The T014
   grace-period fix from 08-02 and today's answer-first output guard are both
   sitting in the repo doing nothing. `publish_state.sh` will never carry them.
   How you would know: nothing observable in the snapshot, which is itself worth
   noting — this deploy is unverifiable from the repo and should be reported by
   whoever does it.
8. **Carried, unverifiable from this repo, not restated at length:** T022
   (itemised GBP Services + job photo cadence), T029 (Apple Business Connect +
   Bing Places), T033/T034/T035 (this morning's scout proposals — review replies,
   job-proof pages, Yelp RAQ), the ~30-page town cap. Open until someone says
   otherwise.

### What I changed in this repo today

Two files. Neither is live until `growth/` is synced. **106 tests pass** across
the six test modules (98 before, 8 new).

- **`growth/techniques.py` — `_off_area_prose()` and `OFF_AREA_COUNTY`, wired
  into `geo_answer_first_content_pass`.** The answer-first pass validated its
  generated paragraph on **word count only**. `_names_other_market` filters the
  query going *in* — that guard was added on 07-29, after the Akron paragraph
  shipped — but nothing looked at what came back *out*, and what came back out is
  still live on the site six days later. The new check rejects a generated answer
  naming a town in `OUT_OF_AREA` or any `"<Name> County"` other than York, and
  drops individual off-area FAQs rather than failing the whole page for one. It
  uses word boundaries where the query filter uses substrings, because
  `OUT_OF_AREA` contains `"york ne"` (York, Nebraska) and a substring test would
  reject the sentence "a York neighborhood".
- **`growth/test_techniques.py` — 8 new tests.** Written against the paragraph
  that actually shipped, plus the shape it does not cover: a bare "Lancaster
  County" with no banned town in it, which a word-count check waves straight
  through. One test asserts the guard is reachable from the technique, because
  the path around it needs a live model call and no unit test can walk it.

I did not touch `techniques.json`, `keywords.json`, `results.jsonl` or
`state.json`; did not activate, retire or re-status any technique; did not edit
`index.html` or any page under `areas/`, `guides/` or `services/`, all of which
are copied droplet → repo every morning and would be reverted tomorrow.

### Reasoning and uncertainties

**Both of today's findings are corrections, and that is the honest summary of
the week.** Seven measured days, top-3 pinned at 2, every named town at zero.
Nothing in that changed today. What changed is that two of the numbers this
journal has been reasoning from turned out to mean less than was claimed: the
head-term impressions are a dead burst, and the map-pack zero is a blind spot
rather than a measurement. Both make the picture slightly *better* than the last
few entries implied — the map pack may be sending traffic that lands in
`direct` — and both make the evidence thinner.

**Where I am least sure: the frozen rows.** I am confident about the arithmetic —
five identical snapshots against a three-day-lagged window is zero impressions on
four specific days, and `gutters` moving in the same fetch rules out a stale
pipeline. I am much less confident about *why*. A ~106-impression single-day
burst on 27 July, the day the engine started and the sitemap and IndexNow first
fired, then silence, is consistent with Google briefly testing a newly-crawled
site and deciding against it. It is also consistent with something in those
queries' SERP that I cannot see. I would not spend effort chasing it; I would
stop citing it.

**Where I may be wrong about `local_visitors`.** I have read the classifier and
Google's referrer behaviour is well documented, but I cannot see a raw referrer
line from this repo — `metrics.py` parses a log on the droplet I have no access
to. If GBP clicks *are* arriving with a full `google.com/maps/place/...`
referrer, the metric works and my lead is wrong. The UTM tag settles it either
way for two minutes of Eric's time, which is why I ranked it where I did rather
than arguing about it.

**What would change my mind about the whole strategy.** The 08-16 test stands:
if daily organic visitors hold a 7-day median of ≥2, the content engine is
working and recommendation 6 becomes the most valuable item here. If they stay at
0–1 while impressions climb, the conclusion is that organic clicks are not this
business's channel, and everything should move to the profile and the offline
candidates. Today's numbers — clicks flat, impressions decelerating to +89,
organic at zero two days running, and 51% of the tracked hire intent already
covered by pages that rank for none of it — lean toward the second. **Nine days
after the goal became measurable, the engine has published 38 URLs and the phone
has rung once.**

## 2026-08-04 — engine run

Goal: **1.6%** top-3 share of 127 tracked queries (target 50%).
2026-08-03: 32 visitors (2 organic, 0 maps) · 0 bookings, 0 phone leads.

**Built:**
- `adopt_queries` — ok: no new in-area searches worth tracking
- `improve_ctr` — ok: no page is due a snippet rewrite
- `geo_answer_first_content_pass` — ok: every ranking page already opens with a direct answer
- `strengthen_pages` — ok: added "Gutter Repair in Red Lion, PA" to /areas/seamless-gutters-red-lion-pa.html for 'gutter repair red lion pa'
- `service_pages` — ok: every queued service already has a page
- `area_pages` — ok: every queued town already has a page
- `money_pages` — ok: no query needs its own page — the remaining gaps all belong on pages that exist, which strengthen_pages handles
- `internal_links` — ok: refreshed nearby-links on 0 page(s)
- `local_schema` — ok: LocalBusiness schema already current
- `rebuild_sitemap` — ok: [gen_sitemap] wrote 38 URLs to sitemap.xml
- `ping_indexnow` — ok: submitted 1 URL(s), HTTP 200

**Scout proposed (as candidates, not running):**
- T036 Published flat-price fall gutter cleaning as the front door — Nobody calls a stranger to spend $2,400 on seamless gutter, but plenty of York County homeowners will call in August-October to get gutters cleaned before leaf-fall. Eric already does cleaning. A clea
- T037 Mystery-call the AI phone agent and add a live human escape hatch — 300 profile views a month and zero phone-agent leads is not a demand problem, it is a suspicion that the answered-call experience is leaking. The ledger already plans a 5-minute callback on captured l
- T038 Coordinate-grid map-pack check across York County — Search Console now measures organic position, but it cannot see the map pack — and the map pack is where 'gutter installer near me' money lands. For a service-area business, rank collapses with distan

## 2026-08-04 — review agent

### Lead: Google spent 2026-08-01 showing this site to Philadelphia, and the homepage has been serving two contradicting business records for eight days

**One: site-wide Search Console numbers stopped describing this business
overnight.** Impressions for the 28-day window went **1,677 → 20,196** in a
single window-day. Clicks went **7 → 7**. Average position went **21.0 → 25.0**.
None of it is York County. 39 of the 40 rows in `discovered_untracked` are now
searches like `seamless gutter contractors glenside pa`, `seamless gutter
company wayne pa`, `seamless gutter contractor norristown pa` — Glenside,
Wayne, Norristown, Plymouth Meeting, Royersford, Phoenixville, Blue Bell,
Collegeville, Willow Grove — the Montgomery/Chester County suburbs of
Philadelphia, ninety-odd miles east, positions **10.0 to 35.5**, **zero clicks
on all forty rows**.

Nothing on this site names any of those towns. I grepped every `.html`, `.py`,
`.json`, `.xml` and `.txt` in the repo: the only occurrences are in today's
snapshot, reporting them back. This is Google matching generic "seamless gutter
contractor" content into somebody else's geography, not a page anyone wrote.

The engine's guards held — `adopt_queries` correctly logged "no new in-area
searches worth tracking" and `_names_other_market` (`techniques.py:1170`) keeps
them out of the goal's denominator. But the *reporting* did not hold:
`gsc.avg_position` is a site-wide aggregate, so 25.0 is now a fact about
Norristown. I fixed that in the repo today (below).

**Two: `index.html` carries two `RoofingContractor` JSON-LD nodes with the same
`@id`, stating different opening hours.** Line 45 is hand-written: Mon–Fri
**07:30–18:00**, Saturday **08:00–14:00**. Line 176 is tagged
`data-growth="localbusiness"` — T004's own output — and says Mon–Fri
**07:00–18:00** and **no Saturday at all**. `local_schema` only ever looked for
its own marker (`techniques.py:582`), so on 2026-07-27 it appended a second node
beside the existing one and has reported *"LocalBusiness schema already
current"* every morning since. `_provider_ld()` (`techniques.py:564-567`) writes
the no-Saturday version onto all 36 generated pages, so **35 of 38 URLs on this
site tell Google the business is closed on Saturday**, while the homepage
simultaneously says it is open until 2pm.

Two nodes sharing an `@id` are one node to a consumer that follows the spec, and
which value wins for a repeated property is not the page's decision. That would
be a pedantic complaint except for what I found in today's research: **Whitespark's
2026 survey ranks "open at the time of search" the 5th strongest Local Pack
factor**, and Google's Danny Sullivan has confirmed openness "recently became a
stronger signal." A homeowner who finds an overflowing gutter finds it on a
Saturday morning. T004 is an **active** technique whose entire hypothesis is
"consistent NAP in structured data"; it has been publishing an inconsistency.

Still nobody's done it: homepage title names no place (**day 4**), the
Akron/Lancaster paragraph is live on the gutter-guards page (**day 7**), the
leaf-fall queue reorder (**day 6**), T007 unanswered (**day 9**), `growth/` not
synced to the droplet since 08-02 (**day 2**).

### Where the numbers stand

The goal metric — tracked York County queries holding a top-3 position:

| | 07-28 | 07-29 | 07-30 | 07-31 | 08-01 | 08-02 | 08-03 | 08-04 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **top-3 count** | 2 | 2 | 2 | 2 | 2 | 2 | 2 | **2** |
| top-10 count | 7 | 6 | 6 | 6 | 6 | 6 | 7 | **8** |
| `ranked_known` | 17 | 19 | 21 | 21 | 21 | 22 | 22 | **22** |
| tracked queries | 76 | 87 | 87 | 98 | 108 | 117 | 122 | **127** |
| share (`top3/total`) | 2.6% | 2.3% | 2.3% | 2.0% | 1.9% | 1.7% | 1.6% | **1.6%** |
| coverage proxy | 48.7% | 44.8% | 46.0% | 42.9% | 40.7% | 39.3% | 39.3% | **38.6%** |

**Top-3 is 2 for the eighth consecutive measured day.** The headline share reads
flat at 1.6% only because of rounding — 2/122 is 1.64%, 2/127 is 1.57%, so it
fell again, for the seventh day running, and again because the denominator grew
by five queries rather than because anything got worse. Against the honest
denominator, the 22 queries Search Console returns a position for, it is 2 of 22
= **9.1%**, unchanged for three days.

**Top-10 went 7 → 8 — the second consecutive up move (6 → 7 → 8).** Two queries
have crossed into the top ten in two days. That is the only tracked number
moving in the right direction, and on this volume it is directional, not a
result.

Per town (`covered`/`total`), every named town still at **0 top-3**, day 8:

| bucket | total | covered | top-3 |
| --- | --- | --- | --- |
| county | 73 (+3) | 29 | **2** |
| york | 13 | 4 | 0 |
| dover | 11 | 3 | 0 |
| hanover | 6 | 4 | 0 |
| dallastown | 8 | 3 | 0 |
| red-lion | 8 (+1) | 3 (+1) | 0 |
| spring-grove | 8 (+1) | 3 | 0 |

Search Console, 28-day rolling: rows **493** (+206), matched **22** (flat, fourth
day), clicks **7** (flat, second day), impressions **20,196** (+18,519), avg
position **25.0** (+4.0). Site-wide CTR is 7 on 20,196 — **0.035%** — a number
that means nothing and should not be quoted at Eric as if it did.

Decoded against `LAG_DAYS = 3`, assuming nothing yet falls off the far end of the
window, each day's delta is that one day's impressions:

| day earned | 07-28 | 07-29 | 07-30 | 07-31 | 08-01 |
| --- | --- | --- | --- | --- | --- |
| impressions | +289 | +192 | +421 | +89 | **+18,519** |
| clicks | +2 | +1 | +1 | 0 | **0** |

Traffic (nginx, bots and owner IPs excluded):

| | 07-29 | 07-30 | 07-31 | 08-01 | 08-02 | 08-03 |
| --- | --- | --- | --- | --- | --- | --- |
| visitors | 14 | 7 | 6 | 6 | 9 | **32** |
| pageviews | 37 | 12 | 14 | 7 | 14 | **70** |
| organic | 3 | 3 | 1 | 0 | 0 | **2** |
| direct | 8 | 3 | 4 | 6 | 9 | **28** |
| local (maps) | 0 | 0 | 0 | 0 | 0 | **0** |
| AI-referred | 0 | 0 | 0 | 0 | 0 | **0** |
| bot hits | 2,374 | 1,200 | 3,162 | 1,412 | 1,554 | **2,189** |

**08-03 is 3.5× the previous best day and I cannot explain it.** 28 of 32
visitors classified `direct`, organic only 2, and the GSC window does not reach
08-03 so there is no rank data to check it against. It cleared a strict filter —
`metrics.py` requires an asset load, caps pages per IP per day, rejects hosting
ranges and ancient user agents — so it is not obviously a crawler. One day is one
day: **this is not evidence of growth and should not be reported as any.** If it
repeats twice more it is real; if it does not, it was a scrape or a share.

`call_taps` **0 for five days**. `ai_calls` 0 for four. `bookings` 0 since 07-30.
All-time: **1 booking, 0 phone leads.** Intent coverage: hire **42/83 (51%)**,
price **3/25 (12%)**, check **3/12 (25%)**, diy **1/7 (14%)**.

**The engine is running short of work, second day.** Seven of eleven techniques
no-op'd: `adopt_queries`, `improve_ctr`, `geo_answer_first_content_pass`,
`service_pages`, `area_pages`, `money_pages` (first no-op — "the remaining gaps
all belong on pages that exist"), and `internal_links` refreshed 0 pages. One did
real work: a Red Lion repair section. `new: 0, changed: 1`. A week ago it
published a town page every morning; it now has essentially nothing left to build
from its current queue.

### Did previous changes work?

**The 20,196 impressions are not a result, and nobody should treat them as one.**
Zero clicks on all forty visible rows, all out of market, and the tracked county
numbers (matched 22, top-3 2, clicks 7) did not move at all. Verdict: **not a
change that worked, and not a change anyone made** — an event that happened to
the site.

**The frozen head terms — the 08-03 finding holds, and the flood has now hidden
them.** `gutter installer` is **212 impressions @ position 1 for the eighth
identical snapshot**, so still zero impressions on 07-28 through 08-01. But
`gutter contractor` (46@1), `gutter guard installer` (14@1) and `gutters`
(46@3.7) have **dropped out of `discovered_untracked` entirely** — not because
they lost anything, but because `gsc.discover()` returns `out[:40]` sorted by
impressions and thirty-nine Philadelphia queries now outrank them. `gutters` was
the one row genuinely improving (20@5.8 → 46@3.7 over six days) and I can no
longer see it. Noted as recommendation 7.

**08-02's prediction — "daily `organic_visitors` holds a 7-day median of ≥2 by
2026-08-16" — still tracking, still not due.** Median over 07-28…08-03 of
`[1,3,3,1,0,0,2]` is **1**. Twelve days left. **Too early to tell.** The 08-03
entry read the flat click count as leaning toward the artifact side; today clicks
were flat a second day while impressions multiplied twelvefold, which leans
further that way. Not calling it.

**08-03 rec #1 (GBP primary category, T016) — no way to tell from here, and
still `candidate`/`activated: null`.** Ninth day in the ledger untouched.

**08-03 rec #2 (`?utm_source=gbp` on the Business Profile URL) — NOT done.**
`local_visitors` is 0 on 08-03, as on every prior day. `classify()` routes the
tag to `local` already, so a single non-zero day would prove it landed. Two
minutes, still unspent, and four techniques are still being scored blind on that
metric.

**08-03 rec #3 (homepage title) — NOT done. Day 4.** `index.html:16` still reads
`Gutter Installer &amp; Contractor | NEMO Seamless Gutter`; the description names
no place. Today's publish commit (`03b3a3b`) touched `areas/`, the journal, the
snapshot and the sitemap — not `index.html` — and `publish_state.sh` copies that
file droplet → repo daily, so the repo copy is authoritative. **Today's flood is
a much stronger argument for this than yesterday's was.** Yesterday I had to
downgrade the case because the impressions it was meant to recover were dead. The
case now is different and better: a site whose strongest page names no place got
sprayed across a metropolitan area it does not serve. That is what a weak geo
anchor looks like from Google's side.

**08-03 rec #4 (Akron/Lancaster paragraph) — NOT done. Day 7.**
`services/gutter-guards.html:163`, still under the `<!-- geo:answer-first -->`
marker, still telling York County searchers this business is in Lancaster County.

**08-03 rec #6 (leaf-fall queue reorder) — NOT done. Day 6.**
`order = {"hire": 0, "price": 1, "check": 2, "diy": 3}` at `techniques.py:435`
and `:834`. It matters more today, not less: `money_pages` no-op'd for the first
time this morning saying the remaining gaps belong on existing pages — while
**22 of 25 price-intent queries are uncovered**. The sort is why the engine
believes it has run out of work.

**08-03 rec #7 (sync `growth/` to the droplet) — NOT done. Day 2.** The T014
grace-period fix (08-02) and the off-area output guard (08-03) are both still
inert, and today's two changes join them.

**T001/T002/T018 remain inside grace to ~2026-08-26.** `owned_visitors` is now
**six consecutive zero days** for each. Still noise at this volume; still cannot
be judged.

**One denominator note, third time:** `schuylkill county seamless gutter` is
still in the tracked universe (it is in today's `uncovered` list). It entered
before the `_names_other_market` fix and nothing removes an already-tracked
query. It inflates the goal's denominator by one. `keywords.json` is
droplet-owned and gitignored, so I cannot fix it from here.

### What I checked in the code before recommending anything

- **The Philadelphia queries are not from this site's own copy.** `grep -rniE`
  across `*.html`, `*.py`, `*.json`, `*.xml`, `*.txt` for twenty of the town
  names: hits only inside `growth/snapshot.json`.
- **The duplicate business node**, `index.html:45` vs `index.html:176`, both
  `@type: RoofingContractor`, both `@id: https://nemoseamlessgutter.com/#business`,
  contradicting `openingHoursSpecification`. `local_schema` at
  `techniques.py:542-599` and the marker test at `:582`.
- **Site hours appear nowhere in visible copy** — only in the two schema blocks.
  A reader cannot tell when to call.
- **The Search Console API cannot separate AI Mode / AI Overview impressions.**
  `type` still accepts only web/image/video/news/discover/googleNews, there is no
  `searchAppearance` value for it, and no BigQuery export. So I **rejected**
  extending `gsc.py` to diagnose the flood automatically — it is a UI-only report.
  `gsc.py:130-143` is the query body; it is already correct.
- **Checked and NOT recommending, because it is already shipped:** FAQPage
  JSON-LD on every generated page (`_faq_ld`), `rel="canonical"`
  (`templates.py:33`), floating tap-to-call on every generated page
  (`templates.py:160`) plus eight `tel:` links in `index.html`, `areaServed:
  York County` in `_provider_ld()`, IndexNow (T006), out-of-area filtering on
  queries entering the universe (`techniques.py:1170`) and on answer-first output
  (`_off_area_prose`, shipped 08-03).
- **Checked against the ledger and not filing as new:** business-hours accuracy
  is in **no** technique — T016 is categories + owner Q&A, T022 is Services list
  + photos, neither mentions hours. That is why recommendation 1 is new. Every
  other off-site idea in today's research is already T007, T011, T016, T022,
  T029, T033 or T035.

### What I researched today

- **"Open at the time of search" is the 5th strongest Local Pack ranking factor
  in Whitespark's 2026 survey** (47 local SEO practitioners, 187 factors), with
  reports of rankings degrading in the final hour a business shows as open and
  of a business holding #1 while open and dropping to #4 when it closes. Danny
  Sullivan: openness "recently became a stronger signal for non-navigational
  queries."
  ([Whitespark](https://whitespark.ca/local-search-ranking-factors/),
  [The Kaleidoscope](https://thekaleidoscope.com/openness-ranking-factor-google-business-profile-hours-operation/),
  [Sam Bretzmann](https://sambretzmann.com/2026-local-seo-ranking-factors-overview/))
  What it changes: it turns a schema-tidiness bug into recommendation 1, and it
  is the cheapest lever in this entire journal.
- **Impression spikes with flat clicks are normal, are not a penalty, and the
  most common 2026 cause is AI Mode query fan-out** — Google splitting one prompt
  into 8–16 sub-queries, each registering impressions. The tell is stilted,
  machine-shaped queries. Chasing a spike as if it were a problem "leads to
  unnecessary fixes that solve nothing."
  ([Brodie Clark](https://brodieclark.com/impression-spike-google-search-console/),
  [Stan Ventures](https://www.stanventures.com/news/google-clarifies-why-sudden-search-impression-spikes-are-not-a-problem-6979/),
  [Ritner Digital](https://www.ritnerdigital.com/blog/what-causes-those-sudden-impression-spikes-in-google-search-console))
  What it changes: it stops me treating the flood as an emergency. But these
  queries read as ordinary human searches, not fan-out shapes, so I do **not**
  think AI Mode is the explanation here — see uncertainties.
- **Search Console gained dedicated generative-AI performance reports on 3 June
  2026**, isolating AI Overviews / AI Mode impressions — **UI only**, with no API
  or BigQuery path, history starting ~18 May 2026.
  ([PPC Land](https://ppc.land/google-finally-gives-search-console-its-own-generative-ai-visibility-reports/),
  [Search Engine Land](https://searchengineland.com/google-ai-mode-traffic-data-search-console-457076))
  What it changes: recommendation 4 — a five-minute human check that settles a
  question the engine structurally cannot.
- **Map-pack weight, 2026, consistent with the 08-03 sources:** primary category
  is the single strongest signal; ~42% of local search clicks go to the three-pack;
  AI Overviews now sit above the pack for many local searches and cite the
  businesses already strong in it.
  ([SEOLocale](https://seolocale.com/google-map-pack-ranking-in-2026-how-the-local-3-pack-really-works/),
  [Wolfpack Advising](https://wolfpackadvising.com/blog/how-to-rank-higher-on-google-maps/),
  [Local SEO Citation Builder](https://localseocitationbuilder.com/blog/map-pack-ranking-factors))
- **LSA economics for this specific trade are better than the ledger's note
  says.** The scout quoted the $53 all-trades average; gutter-category cost per
  lead is reported at **$20–$55**, at the cheap end of the $25–$120 contractor
  range, pay-per-lead not per-click, gated on background check, licence,
  insurance and a Business Profile — with reviews the top ranking factor inside
  the auction.
  ([Searchlight Digital](https://searchlightdigital.io/google-local-service-ads-cost-per-lead/),
  [Home Service Direct](https://www.homeservicedirect.net/google-local-services-ads-cost/))
  What it changes: a refinement to T011's economics, and another reason T007
  (reviews) blocks more than it looks like it blocks.
- **Weak geo relevance is treated as fixable by aligning location signals** across
  profile, site copy, schema and citations, with service area defined explicitly
  rather than implied by the address.
  ([Incremys](https://www.incremys.com/en/resources/blog/geo-search),
  [Search Engine Land](https://searchengineland.com/local-seo-sprints-a-90-day-plan-for-service-businesses-in-2026-469059))

**Rejected:** paid "AI visibility" packages (sixth time); any attempt to suppress
the Philadelphia impressions — there is no lever for it and the sources agree
it is not a problem to solve; extending `gsc.py` to pull AI-surface impressions
(no API exists); geo-grid trackers as anything but diagnosis (T038 already);
extending `TOWN_QUEUE` (re-rejected, fourth time).

### Recommendations

**Everything below needs a droplet action before it does anything.**
`/var/www/nemo-seamless-gutter` is not a git checkout, and `publish_state.sh`
copies droplet → repo only and carries no Python at all.

1. **Confirm the real business hours, fix them in the Business Profile first,
   then merge the two schema blocks.** *(Eric decides the hours — 5 minutes, free.
   Divine merges the blocks — 10 minutes, droplet. NEW.)* Whitespark 2026 puts
   "open at time of search" 5th among Local Pack factors and Google has confirmed
   it strengthened. The **profile** hours are what Google ranks on; the schema is
   corroboration, not the lever — but this site currently corroborates two
   different answers and 35 of 38 pages say closed Saturday. If Eric works
   Saturday mornings and the profile says otherwise, he is invisible for every
   Saturday-morning "gutter overflowing" search in the county. How you would know:
   nothing in this snapshot will show it; it shows up as map-pack impressions and
   calls in GBP Performance, over weeks. Checked: `index.html:45` vs `:176`,
   `techniques.py:564-567`, and the whole ledger — no technique covers hours.
2. **Put York back in the homepage title and description.** *(Divine — minutes,
   droplet. Free. Day 4.)* Promoted from #3 on a stronger argument than
   yesterday's: the site was just shown across the Philadelphia suburbs for
   generic seamless-gutter queries, which is what a placeless strongest-page looks
   like from the index. `GEO_ANCHOR` (`techniques.py:1020`) blocks a future
   placeless rewrite but does not repair the one on disk; the homepage is in its
   21-day `ctr_rewrites` cooldown until ~08-17. Checked: `index.html:16-17`.
3. **Add `?utm_source=gbp` to the website URL in the Business Profile.** *(Eric —
   two minutes. Free. Day 2.)* Unchanged and still unspent. Four techniques
   including active T004 are judged on `local_visitors`, which cannot see a
   map-pack click without the tag. Checked: `metrics.py:63`, `:273-301` — the
   classifier already handles it, no code change needed.
4. **Open Search Console → the generative-AI performance report and look at
   2026-08-01.** *(Divine — five minutes. Free. NEW.)* This settles whether the
   18,519 impressions are AI Mode fan-out or Google genuinely testing this site in
   Montgomery County, and it decides how much weight #2 deserves. The API cannot
   answer it — the report is UI-only. How you would know it worked: you will have
   a one-word answer to write in tomorrow's journal instead of my two hypotheses.
5. **Answer T007 — yes or no.** *(Eric — one decision. Free. Day 9.)* Today's LSA
   research adds a reason: reviews are the top ranking factor inside the LSA
   auction too, so T007 gates T011 as well as the map pack. 13 reviews at 4.2 with
   nobody being asked. A "no" closes it honestly.
6. **Reorder the content queue for leaf-fall.** *(Divine — the sort at
   `techniques.py:435` and `:834`. Free. Day 6.)* Now urgent rather than
   advisable: `money_pages` no-op'd this morning claiming no query needs its own
   page, while **22 of 25 price-intent queries are uncovered** and price is what
   York County types in October. The sort is why the engine thinks it is finished.
   Pages need 8–12 weeks; leaf-fall calls start mid-September.
7. **Widen or split `gsc.discover()`.** *(Divine — small, `growth/gsc.py:299-325`.
   Free. NEW.)* `out[:40]` sorted by impressions means one out-of-market flood
   evicts every row this review actually needs — `gutters`, the only genuinely
   improving row, vanished from view today. Simplest honest fix: return the top
   40 by impressions **plus** the top 20 by position among rows under 100
   impressions, or split the list into in-area and out-of-area buckets. I did not
   ship it because the in-area test lives in `techniques.py` and importing it into
   `gsc.py` is a bigger change than I want to make unreviewed on a day I already
   changed two files.
8. **Sync `growth/` to the droplet.** *(Divine — minutes. Day 2.)* Four changes
   are now stranded: the T014 grace fix (08-02), the off-area output guard
   (08-03), and today's two. `publish_state.sh` will never carry them. Whoever
   does it should report it, because nothing in the snapshot can confirm it.
9. **Carried, unchanged, not restated:** T016 (GBP category audit), T022, T029,
   T033, T034, T035, T036–T038 (this morning's scout), the Akron/Lancaster repair
   (day 7), the ~30-page town cap.

### What I changed in this repo today

Three files, two changes. **120 tests pass** (106 before, 14 new). Neither change
is live until `growth/` is synced.

- **`growth/gsc.py` — `tracked_totals()`, wired into `sync()` as `gsc.tracked`.**
  Site-wide `totals()` answers "how is the property doing", which stopped being
  the same question as "how is this business doing in York County" the moment
  Google started showing the site in Montgomery County. The new function reports
  clicks, impressions and an **impression-weighted** average position over the
  curated keyword universe only, so tomorrow's snapshot carries a county number
  beside the site-wide one instead of only 25.0. I documented its blind spot in
  the docstring rather than hiding it: a geo-neutral search like
  `gutter installer` is not in the tracked universe, so this is the floor of the
  county's real numbers, not all of them.
- **`growth/techniques.py` — `_foreign_ld_nodes()`, `LB_MARKER`, and a refusal in
  `local_schema`.** It now detects a JSON-LD block other than its own claiming the
  same `@id` and returns `ok: False` naming the line number and the field that
  disagrees, instead of appending a second node. `ok: False` surfaces in the daily
  email (`email_report.py:363`) and in `last_build`, so the conflict stays visible
  every morning until a human merges the blocks — which is the right outcome: a
  review agent that cannot deploy should not be silently rewriting a hand-authored
  homepage. Verified against the real file: it reports line 45.
- **`growth/test_gsc.py` (new, 7 tests) and `growth/test_techniques.py` (+7).**
  The gsc tests are pure — no network — and include the exact 08-04 shape:
  630 tracked impressions alongside 2,000 out-of-market ones must report the
  county's position, not the average of both. One test asserts no-tracked-rows
  returns `None` rather than 0.0, because a position of zero reads as "ranking
  first everywhere". One asserts the conflict check runs before anything is
  written.

I did not touch `techniques.json`, `keywords.json`, `results.jsonl` or
`state.json`; did not activate, retire or re-status any technique; did not edit
`index.html` or any page under `areas/`, `guides/` or `services/`, all of which
are copied droplet → repo every morning and would be reverted tomorrow.

### Reasoning and uncertainties

**The honest summary of day nine: top-3 is still 2, every named town is still 0,
the phone has still rung once, and today's twelvefold traffic-looking number is
somebody else's county.** The only tracked movement in a week is top-10 going
6 → 7 → 8, which is two queries on very thin data.

**Where I am least sure: what caused the flood.** Two hypotheses. (a) AI Mode
query fan-out — the most common 2026 cause per the research, but the queries read
as ordinary human searches ("seamless gutter contractors glenside pa"), not the
stilted machine shapes the sources say identify fan-out, so I lean against it.
(b) Google testing a newly-crawled, geo-unanchored site broadly across a
metropolitan area, which fits the pattern of the 27 July head-term burst that
then died. If (b), recommendation 2 matters more than it looks; if (a), it is
noise and the geo argument reverts to yesterday's weaker one. **The GSC UI report
distinguishes them in five minutes and I cannot** — that is recommendation 4 and
it is why I did not rank the title fix first.

**Where I may be wrong about the hours.** I have verified the contradiction in
the files and I have the Whitespark ranking, but I cannot see the Business
Profile, and **the profile's hours are what Google actually ranks on** — schema
is corroboration. If the profile is already correct and open Saturdays, the
schema merge is hygiene and not a ranking lever, and recommendation 1 drops to
about #5. I still ranked it first because the check is five minutes, the
downside if wrong is a tidier homepage, and the downside if right is every
Saturday-morning search in the county.

**Where I may be wrong about 08-03's 32 visitors.** It cleared a strict bot
filter, so either it is real or the filter has a hole I cannot see from a repo
with no access to the log. I have deliberately not built anything on it. If
08-04 and 08-05 come in at 6–9 again, it was a one-off; if they hold near 30,
it is the first real signal in this journal and everything reorders around
finding out where it came from.

**What would change my mind about the whole strategy.** The 08-16 test stands
unchanged: 7-day median of daily `organic_visitors` ≥ 2 means the content engine
works. Today it is 1, clicks are flat for a second day, and the engine no-op'd
seven of eleven techniques because it believes it has run out of things to
build — while 22 of 25 price queries and 9 of 12 check queries sit uncovered.
**That is not an engine out of work; it is an engine sorting its work in the
wrong order.** Recommendation 6 is now the one I would fight for.

## 2026-08-05 — engine run

Goal: **0.8%** top-3 share of 127 tracked queries (target 50%).
2026-08-04: 10 visitors (2 organic, 0 maps) · 0 bookings, 0 phone leads.

**Built:**
- `adopt_queries` — ok: no new in-area searches worth tracking
- `improve_ctr` — ok: no page is due a snippet rewrite
- `geo_answer_first_content_pass` — ok: every ranking page already opens with a direct answer
- `strengthen_pages` — FAILED: 3 candidate(s) failed, last: generation failed for 'gutter repair near me': anthropic 400: {"type":"error","error":{"type":"invalid_request_error","message":"Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits."},"request_id":"req_011Cdj6FNcaSdvThexG51exc"}
- `service_pages` — ok: every queued service already has a page
- `area_pages` — ok: every queued town already has a page
- `money_pages` — ok: no query needs its own page — the remaining gaps all belong on pages that exist, which strengthen_pages handles
- `internal_links` — ok: refreshed nearby-links on 0 page(s)
- `local_schema` — ok: LocalBusiness schema already current
- `rebuild_sitemap` — ok: [gen_sitemap] wrote 38 URLs to sitemap.xml
- `ping_indexnow` — ok: nothing new to submit

**Scout did not run:** anthropic 400: {"type":"error","error":{"type":"invalid_request_error","message":"Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits."},"request_id":"req_011Cdj6FPwh6RVocMWxMe1Da"}

## 2026-08-05 — review agent

### Lead: the API account is empty again, so the engine published nothing this morning — and the goal metric went down for the first time

**One: `"Your credit balance is too low to access the Anthropic API."`** That is
the error text in both `last_build` (`strengthen_pages`, after 3 candidates
failed) and `last_scout` this morning. Per `growth/BUDGET.md`'s own rule — *read
the error text, the two failures are different* — this is the **empty-account**
failure, not the self-imposed cap. The cap that locked the account on 07-28
expired on schedule at 08-01 and the engine ran normally on 08-01 through 08-04.
The balance ran out somewhere between yesterday's 06:00 run, which successfully
wrote a Red Lion repair section, and today's.

**This prompt's standing description of the blocker is now out of date and should
be corrected:** it says to expect the *usage-limit* error until 2026-08-01. That
cap is gone. Today's failure is the third billing incident in ten days and the
second empty balance; I have added the row to the table in `growth/BUDGET.md`.

The consequence is not partial. `strengthen_pages` was the **only** technique
still doing real work — it wrote the Manchester content, the Dover section, the
Red Lion section. Every other content technique has been reporting "nothing left
to build" for three days. So today's build log is nine no-ops, one billing
failure, and a sitemap rebuild that wrote the same 38 URLs as yesterday:
**`new: 0, changed: 0`**. The site did not change this morning. It will not
change tomorrow morning either, unless someone tops up the account.

**Two: top-3 fell from 2 to 1.** After eight consecutive measured days at 2, the
goal count dropped. Top-10 held at 8 and `ranked_known` held at 22, so this is
one query sliding from the top three into positions 4–10 — not a query
disappearing. On 22 ranked queries and 7 clicks in the window, one place of
movement is thin, and I am not calling it a trend. But it is the first movement
in the goal metric in nine days and it is the wrong way, so it goes at the top
rather than in a footnote.

**I cannot tell you which query fell, and that is a hole in the snapshot rather
than a fact about the world.** `keywords.json` on the droplet stores a
`position` per query; `snapshot.py` published only the totals. So the review
agent sees "2 → 1" and has no way to name it. I fixed that in the repo today
(below) — from the next synced run the snapshot carries one row per ranked
query. Today I am guessing, and I have declined to guess.

Still nobody's done it: homepage title names no place (**day 5**), the
Akron/Lancaster paragraph on the gutter-guards page (**day 8**), the leaf-fall
queue reorder (**day 7**), `?utm_source=gbp` (**day 3**), `growth/` not synced to
the droplet (**day 3**, now four stranded changes), T007 unanswered (**day 10**).

### Where the numbers stand

The goal metric — tracked York County queries holding a top-3 position:

| | 07-29 | 07-30 | 07-31 | 08-01 | 08-02 | 08-03 | 08-04 | 08-05 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **top-3 count** | 2 | 2 | 2 | 2 | 2 | 2 | 2 | **1** |
| top-10 count | 6 | 6 | 6 | 6 | 7 | 8 | 8 | **8** |
| `ranked_known` | 19 | 21 | 21 | 21 | 22 | 22 | 22 | **22** |
| tracked queries | 87 | 87 | 98 | 108 | 117 | 122 | 127 | **127** |
| share (`top3/total`) | 2.3% | 2.3% | 2.0% | 1.9% | 1.7% | 1.6% | 1.6% | **0.8%** |
| coverage proxy | 44.8% | 46.0% | 42.9% | 40.7% | 39.3% | 39.3% | 38.6% | **38.6%** |

Two things changed and they point opposite ways. The headline share halved —
but for the first time in eight days **the denominator did not grow**: 127 on
both days. Every previous fall in this row was the universe expanding. This one
is the numerator. Against the honest denominator, the 22 queries Search Console
returns a position for, it is **1 of 22 = 4.5%**, down from 9.1%.

Per town, unchanged in every cell except the county's top-3, and the totals are
flat for the first time since this table started:

| bucket | total | covered | top-3 |
| --- | --- | --- | --- |
| county | 73 | 29 | **1** (was 2) |
| york | 13 | 4 | 0 |
| dover | 11 | 3 | 0 |
| hanover | 6 | 4 | 0 |
| dallastown | 8 | 3 | 0 |
| red-lion | 8 | 3 | 0 |
| spring-grove | 8 | 3 | 0 |

**Nine measured days, every named town still at zero.** Whatever the site is
winning, it is winning county-wide phrasing, not the towns the engine has been
writing pages for.

Search Console, 28-day rolling: rows **590** (+97), matched **22** (flat, fifth
day), clicks **7** (flat, third day), impressions **21,390** (+1,194), avg
position **25.1** (+0.1). The Philadelphia flood has not receded — it has
levelled off and become the site's normal. All 39 out-of-market rows in
`discovered_untracked` are still there, 186–530 impressions each, **still zero
clicks on every one of them**, nine days in. That number is now a permanent
distortion in the site-wide row and should be read as noise every morning until
`gsc.tracked` is live.

Traffic (nginx, bots and owner IPs excluded):

| | 07-30 | 07-31 | 08-01 | 08-02 | 08-03 | 08-04 |
| --- | --- | --- | --- | --- | --- | --- |
| visitors | 7 | 6 | 6 | 9 | 32 | **10** |
| pageviews | 12 | 14 | 7 | 14 | 70 | **35** |
| organic | 3 | 1 | 0 | 0 | 2 | **2** |
| direct | 3 | 4 | 6 | 9 | 28 | **7** |
| local (maps) | 0 | 0 | 0 | 0 | 0 | **0** |
| AI-referred | 0 | 0 | 0 | 0 | 0 | **0** |
| bot hits | 1,200 | 3,162 | 1,412 | 1,554 | 2,189 | **1,612** |

`call_taps` **0 for six days**. `ai_calls` 0 for four. `bookings` 0 since 07-30.
All-time: **1 booking, 0 phone leads.** Intent coverage identical to yesterday in
all four buckets: hire 42/83, price **3/25**, check 3/12, diy 1/7.

The measurement itself is not suspect. Visitors are non-zero on nine of the last
nine days and the classifier is separating direct from organic from bot, so the
"flat zero for a week means `metrics.py` is over-filtering" check does not fire.
The numbers are small because the site is small.

### Did previous changes work?

**08-04's uncertainty about the 32-visitor day is settled: it was a one-off.**
I wrote that if 08-04 and 08-05 came in at 6–9 it was a scrape or a share, and if
they held near 30 it was the first real signal in this journal. 08-04 came in at
**10 visitors, 35 pageviews, 7 direct**. Back to baseline. **Verdict: not
growth.** Nothing was built on it and nothing needs unwinding.

**08-04's two repo changes are inert, and today's snapshot proves it rather than
implying it.** `gsc.sync()` in this repo now emits a `tracked` key; today's
`gsc` block has `date, ok, connected, rows, matched, clicks, impressions,
avg_position` and **no `tracked`**. Separately `local_schema` reported
*"LocalBusiness schema already current"* this morning, which is exactly the
message the new conflict check replaces with a refusal. Both confirm the droplet
is running the old code. **Verdict: not tested, because not deployed.** Day 3.

**The duplicate `RoofingContractor` node is still live.** `index.html:45` and
`index.html:176`, same `@id`, contradicting `openingHoursSpecification` —
verified again today, unchanged. 35 of 38 pages still say closed Saturday.

**08-04 rec #2 (homepage title) — NOT done. Day 5.** `index.html:16` still reads
`Gutter Installer &amp; Contractor | NEMO Seamless Gutter`; the description at
`:17` still names no place. Note the site is ranking **position 1 for the
geo-neutral query `gutter installer`** (214 impressions, 0 clicks) — which is
the title tag doing its job for a search with no money in it, in no particular
county.

**08-04 rec #3 (`?utm_source=gbp`) — NOT done. Day 3.** `local_visitors` 0 on
08-04 as on every prior day. Four techniques still scored blind.

**08-04 rec #4 (open the GSC generative-AI report) — cannot tell, and it now
matters less.** I asked for it to distinguish AI-Mode fan-out from Google testing
the site across Montgomery County. Nine days of the same 39 rows at stable
impressions with zero clicks reads much more like the second than like fan-out,
which is bursty. I am no longer blocked on the answer; the recommendation drops
down the list rather than off it.

**08-04 rec #6 (leaf-fall queue reorder) — NOT done. Day 7.** `order = {"hire":
0, "price": 1, "check": 2, "diy": 3}` at `techniques.py:435` and `:879`,
unchanged. 22 of 25 price queries uncovered, seventh day.

**08-04 rec #7 (widen `gsc.discover()`) — I shipped it today.** Yesterday I
identified it and declined to write it. See below; it needed no import from
`techniques.py` after all.

**08-04 rec #8 (sync `growth/`) — NOT done. Day 3.** Now six stranded changes:
the T014 grace fix (08-02), the off-area output guard (08-03), `tracked_totals`
and the `local_schema` refusal (08-04), and today's two.

**08-02's prediction — "daily `organic_visitors` holds a 7-day median of ≥2 by
2026-08-16" — still tracking, still not due.** Median over 07-30…08-05 of
`[3,1,0,0,2,2]` (six days, 08-05 not yet measured) is **1.5**. Eleven days left.
**Too early to tell.** It has now been "1 or 1.5" for four consecutive checks
against a target of 2, on a site whose content engine has been idle for three
days — I would not bet on it, but the test stands as written.

**T001/T002/T018 remain inside grace to ~2026-08-26.** `owned_visitors` is
**seven consecutive zero days** for each. Still unjudgeable at this volume. Worth
saying plainly: T001 (`area_pages`) has been unable to add to its own series for
a week because it has no towns left in its queue, so the grace period is running
down on a technique that is no longer doing anything. That is a scoring problem
for 08-26, not today.

**`schuylkill county seamless gutter` is still in the tracked universe, fourth
mention.** Inflates the denominator by one. Droplet-owned, cannot fix from here.

### What I checked in the code before recommending anything

- **`keywords.json` has the per-query positions and the snapshot was throwing
  them away.** `keywords.apply_gsc()` writes `position`/`impressions`/`clicks`
  onto each tracked query (`keywords.py:248-266`); `summary()` collapsed them to
  `top3`/`top10`/`ranked_known` (`:274-291`) and `snapshot.build()` published
  only those (`snapshot.py:125-127`). That is why "which query fell" has no
  answer today. Fixed below.
- **`gsc.discover()` really was cutting the rows I need.** `out[:40]` sorted by
  impressions, `gsc.py:325`. Checked against today's data: `gutters`,
  `gutter contractor` and `gutter guard installer` are **all absent** from the
  40 rows, and the smallest row that made it has **186 impressions**. Fixed
  below.
- **The area pages are not the thin templated location pages the 2026 core
  updates went after.** This mattered enough to measure rather than assume, so I
  stripped tags and scripts and counted: Manchester **1,027 words**, Mount Wolf
  **820**, both with specific, checkable local content — Manchester Borough's
  narrow lots and downspout placement against the township's 1960s–90s ranchers,
  Mount Wolf's rail-corridor frame houses and the steep-gable-onto-short-eave
  overflow problem, hanger spacing tightened to 16–18" on north-facing eaves.
  Combined with the 08-03 similarity measurement (max pairwise 0.457, median
  0.227 across 105 pairs), these are on the right side of that line.
  **No action, and that is the finding** — the risk is scaling the template, not
  the pages that exist.
- **Already shipped, so not recommending:** `Service` JSON-LD on every area page
  (`techniques.py:323-331`, verified present in 10+ files under `areas/`),
  `FAQPage` on every generated page (`_faq_ld`, `techniques.py:194`),
  `OfferCatalog` of the seven services in the provider node (`:614-617`),
  `rel="canonical"` (`templates.py:33`), floating tap-to-call (`templates.py:160`)
  plus eight `tel:` links in `index.html`, IndexNow (T006), out-of-area filtering
  on adopted queries (`techniques.py:1170`) and on answer-first output.
- **Checked against the ledger and not filing as new:** everything off-site in
  today's research is already T007, T008, T011, T013, T016, T022, T027, T035,
  T036 or T037. The one thing I am filing is a **correction** to T008's stated
  hypothesis, not a new technique.

### What I researched today

- **Google Business Profile posts do not move map-pack rank — and there is a
  controlled test, not an opinion.** Sterling Sky ran 1 post a week for 9 weeks
  against **441 tracked keywords per location**, posts written about the tracked
  keywords: no ranking change on the first listing, a decline on the second that
  they traced to an unrelated competitor. Their own conclusion is to use posts
  for conversions and messaging, **not** for rankings.
  ([Sterling Sky](https://www.sterlingsky.ca/do-google-posts-impact-ranking/))
  What it changes: **T008's hypothesis is wrong as written.** It says posts
  "surface seasonal offers directly in the pack, where the hire-intent searches
  land" — a visibility claim. It should be rewritten as a conversion claim
  before anyone activates it, and the T028 heavy-rain play should not count its
  Business-Profile post as a ranking lever either. This also cuts against the
  agency-blog consensus I found the same morning — "post twice a week, frequent
  activity is a top-tier ranking signal"
  ([Blue Interactive](https://blueinteractiveagency.com/seo-blog/2026/06/google-business-profile-optimization-in-2026/),
  [DigitalApplied](https://www.digitalapplied.com/blog/google-business-profile-guide-every-feature-2026))
  — and where a controlled test and a listicle disagree, the test wins.
- **Two core updates have landed since March and both went after templated
  location pages.** March 2026: started 27 March, complete 8 April. May 2026:
  started 21 May, complete 2 June, ~12 days.
  ([Search Engine Land, March](https://searchengineland.com/google-march-2026-core-update-rollout-is-now-complete-473883),
  [Search Engine Land, May](https://searchengineland.com/google-may-2026-core-update-rollout-is-now-complete-479119),
  [Search Engine Roundtable](https://www.seroundtable.com/google-may-2026-core-update-done-41435.html))
  Secondary sources characterise the target as "templated location pages that
  swap in city names but have nothing real underneath", with home services named
  as a hardest-hit vertical
  ([Scorpion](https://www.scorpion.co/articles/news/industry-trends-news/googles-march-2026-core-update-what-local-servic/),
  [1ClickReport](https://www.1clickreport.com/blog/google-may-2026-core-update-programmatic-seo-dead)).
  **Both of those returned HTTP 403 to a direct fetch, so I have search-result
  summaries only and am flagging them as second-hand.** The dates are
  first-party.
  What it changes: it is why I measured the area pages above rather than
  repeating 08-03's conclusion. It also reinforces the standing "do not extend
  `TOWN_QUEUE`" decision, now for the fourth time.
- **Phone leads convert at 46% in home services, and 37% close on the first
  call.** ([Invoca 2026 benchmarks](https://www.invoca.com/reports/the-invoca-home-services-lead-conversion-benchmarks-report-2026),
  [Supply House Times summary](https://www.supplyht.com/articles/106612-home-services-call-performance-report-46-lead-conversion-rate-segment-benchmarks))
  Calls are 60–70% of home-service conversions, forms 20–30%, online booking
  **5–10%** ([Web Tonic](https://www.webtonic.io/blog/heating-ventilation-landing-page-statistics),
  [Pipeline On](https://pipelineon.com/blog/contractor-conversion-rate-optimization/)).
  What it changes: nothing new to build — tap-to-call is already on every page —
  but it is the numeric case for T013/T027/T037 over any further site work, and
  it says the booking widget this site is built around is the *smallest* of the
  three channels for this trade.
- **A contradiction worth recording rather than smoothing over.** The 08-03 entry
  cites Search Engine Journal for "AI Overviews appear on ~68% of local
  searches". Today's source says **~7%**
  ([Host Merchant Services](https://hostmerchantservices.com/2026/07/local-seo-ai-overviews/)),
  alongside the more interesting claim that **65% of AI citations do not overlap
  the classic top 10**. I cannot reconcile a 7% and a 68% and I am not going to
  pick the one that suits me. Both entries' conclusion survives either way — AI
  visibility is downstream of the map pack, and `ai_visitors` has been 0 on every
  day on record — but T014's ceiling is genuinely unknown and this journal should
  stop quoting either figure as settled.

**Rejected:** paid "AI visibility" packages (seventh time); extending
`TOWN_QUEUE` (fourth time); geo-grid trackers as anything beyond diagnosis
(T038 covers it); GBP posting cadence as a ranking tactic (rejected *today*, on
the Sterling Sky test, having nearly recommended it from the listicles);
any attempt to suppress the Philadelphia impressions — nine days of stability
confirm there is no lever and nothing to fix.

### Recommendations

**Everything below needs a droplet action before it does anything.**
`/var/www/nemo-seamless-gutter` is not a git checkout and `publish_state.sh`
copies droplet → repo only.

1. **Top up the Anthropic API balance.** *(Eric or Divine — minutes, costs
   money. NEW and blocking.)* This is the empty-account error, not a cap; per
   `BUDGET.md` the response is "top up", and waiting does nothing. Until it is
   done the engine writes **zero** pages and the scout files **zero** candidates,
   because `strengthen_pages` was the last technique with work left. Per-run cost
   is 3–5 calls, cents per day, and the bounded call count is why. How you would
   know it worked: tomorrow's `last_build` shows `strengthen_pages` `ok` with a
   named section, and `last_scout.ok` is true. Checked: the error strings in
   `snapshot.json` `last_build`/`last_scout`, and `growth/BUDGET.md`'s own
   decision rule.
2. **Reorder the content queue for leaf-fall — do it *before* the credit lands,
   not after.** *(Divine — the sort at `techniques.py:435` and `:879`. Free.
   Day 7.)* This decides what the engine writes the moment it can write again,
   so the idle window is the cheapest possible time to change it. 22 of 25
   price-intent queries are uncovered, price is what York County types in
   October, and pages need 8–12 weeks to rank against a leaf-fall season that
   starts mid-September. The engine is not out of work; it is sorting `hire`
   first through a queue whose `hire` rows are done. Checked: both sort
   dictionaries, and `money_pages`' own no-op text.
3. **Sync `growth/` to the droplet.** *(Divine — minutes. Day 3.)* Six changes
   are now stranded, including both of today's, and two of them exist
   specifically to make tomorrow's review able to answer questions today's
   could not. Nothing in the snapshot confirms a sync, so whoever does it should
   say so. Checked: today's `gsc` block has no `tracked` key and `local_schema`
   still reports "already current" — both prove the droplet is on old code.
4. **Put York back in the homepage title and description.** *(Divine — minutes,
   droplet. Free. Day 5.)* Unchanged argument, plus one new data point: the site
   holds **position 1 for `gutter installer`** — placeless, 214 impressions, zero
   clicks — which is what a strong page with no geography anchored to it earns.
   Checked: `index.html:16-17`.
5. **Add `?utm_source=gbp` to the website URL in the Business Profile.**
   *(Eric — two minutes. Free. Day 3.)* `classify()` already routes the tag;
   `local_visitors` has been 0 for nine days and four techniques are judged on
   it. Checked: `metrics.py:63`, `:273-301` — no code change needed.
6. **Confirm the real hours in the Business Profile, then merge the two schema
   blocks.** *(Eric decides — 5 minutes. Divine merges — 10 minutes, droplet.
   Day 2.)* Unchanged from yesterday; the profile hours are the ranking lever and
   the schema is corroboration, but the site currently corroborates two
   contradicting answers. Checked again today: `index.html:45` vs `:176`, still
   both present.
7. **Answer T007 — yes or no.** *(Eric — one decision. Free. Day 10.)* 13
   reviews, nobody being asked, and it gates both the map pack and the LSA
   auction. A "no" closes it honestly and stops it being restated every morning.
8. **Rewrite T008's hypothesis before anyone activates it.** *(Divine — one line
   in droplet-owned `techniques.json`. Free. NEW.)* It currently claims posts
   "surface seasonal offers directly in the pack". Sterling Sky's 9-week,
   441-keyword controlled test says posts do not move pack position. Posts may
   still be worth doing for panel click-through — but a technique whose stated
   hypothesis is false will be judged against the wrong metric (`local_visitors`)
   and retired for the wrong reason. Same note applies to T028's post component.
   Checked: T008's `hypothesis` and `metric` fields in today's snapshot.
9. **Carried, unchanged, not restated:** the Akron/Lancaster paragraph on
   `services/gutter-guards.html:163` (day 8), the GSC generative-AI report check
   (demoted — nine days of stable rows have mostly answered it), T016, T022,
   T029, T033, T034, T035, T036–T038, the ~30-page town cap.

### What I changed in this repo today

Four files, two changes plus a doc row. **135 tests pass** (120 before, 15 new).
Nothing here is live until `growth/` is synced to the droplet.

- **`growth/keywords.py` + `growth/snapshot.py` — publish the ranked queries, not
  just their count.** `summary()` gains a `ranked` list: every tracked query
  Search Console returns a position for, best first, carrying town, intent,
  target page, coverage, position, impressions and clicks. `snapshot.build()`
  publishes it under `keywords.ranked`. This is the change that would have let me
  answer today's headline question. `ranked_known` has been 17–22 since Search
  Console was connected, so it costs roughly twenty rows a day. New
  `growth/test_keywords.py`, 7 tests, `load()` patched with a fixture — one of
  them reconstructs today's exact situation (top-3 2 → 1 with top-10 flat) and
  asserts the dropped query is nameable from two consecutive lists.
- **`growth/gsc.py` — `_select_discoveries()`, a second slate in `discover()`.**
  Was: top 40 untracked rows by impressions. Now: those 40, plus up to 20 more
  by best position among rows the first slate did not take. The first list still
  answers "what is Google showing this site for"; the second answers "what is
  this site close to winning", and a flood in someone else's market cannot evict
  it. **A test caught a real bug in my first attempt**: I had restricted the
  second slate to rows under 100 impressions, which meant `gutter installer` —
  214 impressions at position 1, a real row in today's data — was too loud for
  the second slate and too quiet for the first, and vanished entirely. The only
  threshold that belongs there is "was it already picked". 8 tests, no network.
- **`growth/BUDGET.md` — the 2026-08-05 row in the incident table.** Third
  billing failure in ten days, second empty balance. The table's whole point is
  that a cost failure looks like a quiet partial success, and today is the
  cleanest example yet: nine `ok`s, `new: 0, changed: 0`.

I did not touch `techniques.json`, `keywords.json`, `results.jsonl` or
`state.json`; did not activate, retire or re-status any technique; did not edit
`index.html` or anything under `areas/`, `guides/` or `services/`, all of which
are copied droplet → repo every morning and would be reverted tomorrow.

### Reasoning and uncertainties

**Day ten, honestly: the engine produced nothing this morning, the goal metric
went down, the phone has rung once ever, and every named town is still at zero.**
The only number that has moved in the right direction in two weeks is top-10
going 6 → 7 → 8, and it has been flat at 8 for three days.

**Where I am least sure: whether the top-3 drop means anything.** One query, on
22 ranked queries, with 7 clicks in a 28-day window. It could be a competitor's
page, a SERP layout change, or Search Console's own averaging over a handful of
impressions. I have deliberately not built a recommendation on it. What would
settle it is exactly what I shipped today — two consecutive `ranked` lists name
the query, and then the question becomes "what happened to that page", which is
answerable. Ask me again in three days.

**Where I may be wrong about the credit blocker.** I am reading an error string
from a snapshot, not the console. If the balance is actually fine and something
else returns that message, recommendation 1 is wrong and the real fault is
elsewhere. But the string is verbatim, `BUDGET.md` documents the exact same
message from 2026-07-27, and the run before it succeeded — I do not think there
is much room here.

**Where I have changed my mind.** I came into today's research half-expecting to
recommend a Business Profile posting cadence; three separate 2026 guides say to
post twice a week and call it a top-tier ranking signal. A controlled test with
441 keywords says it does nothing for rank. I dropped it, and filed the ledger
correction instead. I would rather lose the recommendation than spend Eric's
week on it.

**What would change my mind about the whole strategy.** The 08-16 test stands:
7-day median daily `organic_visitors` ≥ 2. It is 1.5 and the content engine has
been idle for three days, so the test is now partly measuring a billing problem
rather than the hypothesis. If it fails on 08-16 with the engine having been
blocked for a third of the window, the honest reading is "inconclusive, rerun",
not "content does not work" — and I am writing that down now, before the result,
so it cannot be chosen after the fact.

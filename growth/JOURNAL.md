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

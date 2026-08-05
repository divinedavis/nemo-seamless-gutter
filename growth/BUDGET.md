# Budget — do not blow it

**Standing rule: this engine must never be the reason an API bill or a spend cap
is hit.** It runs unattended every morning, so a bad cost decision here does not
get caught by anyone until the money is gone or the account is locked.

This is not hypothetical. It has already happened twice:

| Date | What happened | How it surfaced |
|---|---|---|
| 2026-07-27 | Account credit balance hit $0 | `area_pages`, `money_pages` and `scout` all no-op'd; only the non-LLM techniques ran |
| 2026-07-28 | Self-imposed usage cap reached, locked until 08-01 | `scout` failed at 6am with a 400 — the build still ran, so the report looked healthy at a glance |
| 2026-08-05 | Credit balance hit $0 again, five days after the 08-01 cap lifted | `strengthen_pages` failed after 3 candidates and `scout` failed; the other nine steps reported `ok` because they had nothing to do, so `last_build` read `new: 0, changed: 0` — a run that produced nothing and looked calm |

All three times the engine kept reporting `[ok]` on most steps. **A cost failure
here looks like a quiet, partial success**, which is exactly why it needs a rule
rather than vigilance.

## The rules

1. **Know the per-run cost before changing a model or a token budget.** The daily
   run makes at most 7 LLM calls — 6 in `techniques.py`, 1 in `scout.py` — and
   each technique returns after its first success, so a run is normally 3-5 calls.
   At Opus 5 rates ($5/MTok in, $25/MTok out) that is cents per day. It stays that
   way only because the call count is bounded.

2. **One unit of work per technique per run.** Every technique returns after it
   publishes or edits one thing. Do not add a loop that processes the whole queue
   in one morning — that is the change that turns cents into a capped account, and
   it is also what triggers scaled-content-abuse enforcement. The two failure modes
   share a cause.

3. **`max_tokens` is a budget, not a ceiling to round up.** On Opus 5 thinking is
   billed against the same allowance, so raising it raises real spend even when the
   visible output is unchanged. `llm.MIN_MAX_TOKENS = 3000` exists because a
   900-token request spent 721 on thinking and returned an empty string. Raise it
   only with a reason, and record the reason.

4. **Never add an unbounded retry.** A failed call that retries forever against a
   rate limit is how a cap gets hit in one morning.

5. **Prefer the technique that spends nothing.** `internal_links`, `local_schema`,
   `rebuild_sitemap` and `ping_indexnow` make no model calls at all. When a
   non-LLM technique and an LLM technique would achieve the same thing, the
   non-LLM one wins.

6. **Surface the cost failure loudly.** A 400 from billing must appear at the top
   of the report, not buried in a run log. The report already prints a BLOCKED
   banner for this; keep it.

## Read the error text — the two failures are different

They need opposite responses, and the message is the only way to tell them apart:

- `"Your credit balance is too low"` → the account is empty. Top up.
- `"You have reached your specified API usage limits"` → the balance is fine; a
  **self-imposed cap** was hit. Raise or wait out the cap. Topping up does nothing.

## Before raising any model or token setting

Ask, in order: what does this cost per run, what does it cost per month, and what
happens to the daily loop if the cap is hit mid-month? If the answer to the third
is "the report still says ok on most steps", fix that first.

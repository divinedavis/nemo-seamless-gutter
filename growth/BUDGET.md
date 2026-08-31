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
| 2026-08-12 → 08-13 | Balance $0 again | Same shape: `strengthen_pages` + `scout` failed, everything else `ok`, `new: 0, changed: 0` for two days |
| 2026-08-19 → 08-20 | Balance $0 again | Same shape, two more days. On 08-20 `geo_answer_first_content_pass` failed too |
| 2026-08-31 | Balance $0 again, three days after the 08-24 top-up was first drawn on | Same shape. `new: 0, changed: 0` |

Every time, the engine kept reporting `[ok]` on most steps. **A cost failure
here looks like a quiet, partial success**, which is exactly why it needs a rule
rather than vigilance.

## How long a top-up actually lasts — measured, not estimated

Every published `snapshot.json` in this repo records whether that morning's build
and scout hit `credit balance is too low`. Reading them end to end gives the real
duty cycle rather than a guess:

| Window | Days | State |
|---|---|---|
| 08-12 → 08-13 | 2 | dead — no credit |
| 08-14 → 08-18 | 5 | **alive** — 1 new page, 7 page edits |
| 08-19 → 08-20 | 2 | dead — no credit |
| 08-21 → 08-27 | 7 | dead — unrelated crash in `growth_daily.py` |
| 08-28 → 08-30 | 3 | **alive** — 3 page edits |
| 08-31 | 1 | dead — no credit |

**A top-up has bought 3–5 productive mornings, twice in a row.** Over the twenty
days 08-12 → 08-31 the engine did billable work on **8 of 20**; an empty balance
accounts for 5 of the 12 lost days and the crash for the other 7.

This is a funding-shape problem, not a spending problem. Rule 1 above still holds
— a run is cents — so the fix is **an auto-reload threshold on the Anthropic
account**, not a bigger manual top-up, which only lengthens the gap between
stalls. Whoever sets it should also set a monthly cap, so rule 1 stays enforced
by the console rather than by whoever remembers to check.

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

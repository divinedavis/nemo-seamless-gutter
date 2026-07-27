#!/usr/bin/env python3
"""Publish a machine-readable state snapshot for the daily review agent.

The growth engine runs on the droplet; the agent that reviews it runs in the
cloud with no access to this machine. The git repository is the bridge: this
writes `growth/snapshot.json` and appends to `growth/JOURNAL.md`, and
publish_state.sh pushes both to GitHub straight after the 6am run.

PRIVACY — the single most important rule in this file. The bookings and leads
tables contain real customers: names, phone numbers, street addresses, and free
-text notes about their houses. NONE of that may leave this machine. The
snapshot carries counts and dates only, and `_assert_no_pii` fails the write if
anything that looks like a phone number, email or street address slips in.
"""
import datetime
import json
import os
import re

from . import keywords, ledger, metrics, review

HERE = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT_PATH = os.path.join(HERE, "snapshot.json")
JOURNAL_PATH = os.path.join(HERE, "JOURNAL.md")

# Series worth carrying to the agent. Aggregates only.
SERIES = ("visitors", "pageviews", "organic_visitors", "local_visitors",
          "ai_visitors", "direct_visitors", "referral_visitors",
          "campaign_visitors", "bot_hits", "bookings", "phone_leads",
          "total_leads")

PII_PATTERNS = (
    (re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b"), "phone number"),
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "email address"),
    (re.compile(r"\b\d{1,5}\s+[A-Z][a-z]+\s+(St|Street|Rd|Road|Ave|Avenue|Ln|Lane|Dr|Drive|Ct|Court|Blvd|Way|Cir|Circle)\b"),
     "street address"),
)

# The business's own published contact details are not PII leakage — they are
# on every page of the site already.
ALLOWED = ("717-578-0073", "7175780073", "717.578.0073", "(717) 578-0073",
           "enemo@nemoseamlessgutter.com", "eric@nemoseamlessgutter.com",
           "divinejdavis@gmail.com", "808 W Mason Ave")


def _assert_no_pii(blob):
    text = json.dumps(blob)
    for token in ALLOWED:
        text = text.replace(token, "")
    for pattern, label in PII_PATTERNS:
        m = pattern.search(text)
        if m:
            raise RuntimeError(
                f"refusing to publish snapshot: found what looks like a {label} "
                f"({m.group(0)!r}). Customer data must never leave the droplet.")


def _series(metric, days=45):
    return [{"date": d, "value": v}
            for d, v in ledger.series("__site__", metric)[-days:]]


def build(docroot):
    kw = keywords.summary()
    sb = review.scoreboard()
    techs = ledger.load_techniques()

    snap = {
        "generated": datetime.datetime.now(datetime.timezone.utc)
                     .isoformat(timespec="seconds"),
        "date": ledger.today(),
        "site": "nemoseamlessgutter.com",
        "goal": {
            "statement": "more than 50% of tracked York County gutter queries "
                         "holding a top-3 position",
            "target_pct": 50,
            "share_pct": kw["share_pct"],
            "measured": kw["share_pct"] is not None,
            "why_unmeasured": (None if kw["share_pct"] is not None else
                               "Google Search Console is not connected, so no "
                               "true rank data exists. coverage_pct below is a "
                               "proxy for whether a page exists, NOT for rank."),
            "coverage_pct": kw["coverage_pct"],
            "tracked_queries": kw["total"],
            "top3": kw["top3"], "top10": kw["top10"],
            "ranked_known": kw["ranked_known"],
        },
        "traffic": {m: _series(m) for m in SERIES},
        "lead_totals": metrics.lead_totals(),
        "keywords": {
            "by_town": kw["by_town"],
            "by_intent": kw["by_intent"],
            "uncovered": kw["gaps"],
        },
        "techniques": [
            {"id": t["id"], "slug": t["slug"], "name": t["name"],
             "kind": t.get("kind"), "status": t.get("status"),
             "hypothesis": t.get("hypothesis"), "evidence": t.get("evidence"),
             "prefixes": t.get("prefixes"), "metric": t.get("metric"),
             "source": t.get("source"), "added": t.get("added"),
             "activated": t.get("activated"), "retired": t.get("retired"),
             "notes": t.get("notes"), "verdict": t.get("verdict"),
             "owned_visitors": ([{"date": d, "value": v} for d, v in
                                 ledger.series(t["slug"], "owned_visitors",
                                               since=t.get("activated"))[-45:]]
                                if t.get("prefixes") else None)}
            for t in techs],
        "scoreboard": {"works": [r["id"] for r in sb["works"]],
                       "does_not_work": [r["id"] for r in sb["does_not_work"]],
                       "not_yet_judged": [r["id"] for r in sb["not_yet_judged"]]},
        "last_build": ledger.get_state("last_build"),
        "last_scout": ledger.get_state("scout_last"),
        "pages": _page_inventory(docroot),
    }
    _assert_no_pii(snap)
    return snap


def _page_inventory(docroot):
    """What actually exists on the site, so the agent is not guessing."""
    out = {}
    for sub in ("areas", "guides", "services"):
        d = os.path.join(docroot, sub)
        if os.path.isdir(d):
            out[sub] = sorted(f for f in os.listdir(d) if f.endswith(".html"))
    root = [f for f in os.listdir(docroot)
            if f.endswith(".html") and os.path.isfile(os.path.join(docroot, f))]
    out["root"] = sorted(root)
    return out


def write(docroot):
    snap = build(docroot)
    tmp = SNAPSHOT_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(snap, f, indent=2, sort_keys=False)
        f.write("\n")
    os.replace(tmp, SNAPSHOT_PATH)
    return snap


# ------------------------------------------------------------------- journal

def append_journal(entry):
    """Append one dated entry. Append-only: the value of the journal is that
    it records what was believed at the time, so nothing rewrites history."""
    existing = ""
    if os.path.exists(JOURNAL_PATH):
        with open(JOURNAL_PATH) as f:
            existing = f.read()
    else:
        existing = (
            "# Growth journal\n\n"
            "Append-only record of what the growth engine and the daily review\n"
            "agent did, why, and whether it worked. Newest entries at the bottom.\n"
            "Nothing here is ever edited after the fact — a decision log is only\n"
            "worth reading if it still shows what was believed at the time.\n")
    with open(JOURNAL_PATH, "w") as f:
        f.write(existing.rstrip("\n") + "\n\n" + entry.rstrip("\n") + "\n")
    return JOURNAL_PATH


def engine_entry(run_log=None, review_out=None, scout_out=None):
    """The engine's own daily entry — what it did, in its own words."""
    L = [f"## {ledger.today()} — engine run", ""]
    kw = keywords.summary()
    if kw["share_pct"] is not None:
        L.append(f"Goal: **{kw['share_pct']}%** top-3 share of {kw['total']} "
                 f"tracked queries (target 50%).")
    else:
        L.append(f"Goal: **unmeasured** (no Search Console). Coverage proxy "
                 f"{kw['coverage_pct']}% of {kw['total']} tracked queries.")

    def last(m):
        s = ledger.series("__site__", m)
        return s[-1][1] if s else "—"
    L.append(f"Yesterday: {last('visitors')} visitors "
             f"({last('organic_visitors')} organic, {last('local_visitors')} maps) · "
             f"{last('bookings')} bookings, {last('phone_leads')} phone leads.")
    L.append("")

    if run_log:
        L.append("**Built:**")
        for r in run_log:
            L.append(f"- `{r['slug']}` — {'ok' if r.get('ok') else 'FAILED'}: "
                     f"{r.get('detail', '')}")
        L.append("")
    if review_out and review_out.get("actions"):
        L.append("**Review decisions:**")
        for a in review_out["actions"]:
            L.append(f"- {a}")
        L.append("")
    if scout_out and scout_out.get("techniques_added"):
        L.append("**Scout proposed (as candidates, not running):**")
        for s in scout_out["techniques_added"]:
            t = ledger.get(s)
            if t:
                L.append(f"- {t['id']} {t['name']} — {(t.get('hypothesis') or '')[:200]}")
        L.append("")
    elif scout_out and not scout_out.get("ok"):
        L.append(f"**Scout did not run:** {scout_out.get('detail', '')[:300]}")
        L.append("")
    return "\n".join(L)

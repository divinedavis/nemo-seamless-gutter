#!/usr/bin/env python3
"""Publish a machine-readable state snapshot for the daily review agent.

The growth engine runs on the droplet; the agent that reviews it runs in the
cloud with no access to this machine. The git repository is the bridge: this
writes `growth/snapshot.json` and appends to `growth/JOURNAL.md`, and
publish_state.sh pushes both to GitHub straight after the 6am run.

PRIVACY — the single most important rule in this file. The bookings and leads
tables contain real customers: names, phone numbers, street addresses, and
free-text notes about their houses. NONE of that may leave this machine. The
snapshot carries counts and dates only, and `scrub()` redacts anything shaped
like a phone number, email or street address before the file is written,
recording each hit under `redactions` so it is visible rather than silent.
"""
import datetime
import hashlib
import json
import os
import re

from . import gsc, keywords, ledger, metrics, review

HERE = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT_PATH = os.path.join(HERE, "snapshot.json")
JOURNAL_PATH = os.path.join(HERE, "JOURNAL.md")

# Series worth carrying to the agent. Aggregates only.
#
# `call_taps` (metrics.py, unique tappers of a tel: link per day) and `ai_calls`
# (calls.py, inbound calls that reached the phone assistant) were both being
# written into the ledger and read by nobody: the review agent sees only this
# file, so a number missing here does not exist as far as the judgment layer is
# concerned, and three consecutive reviews had to write "the phone is not
# measured from here" about metrics that were already being collected. Counts
# are aggregates — the caller numbers stay in the gitignored cache — so they
# pass _assert_no_pii unchanged.
# `log_visitors`/`log_pageviews` exist for the same reason. From
# metrics.PV_START the headline `visitors` count comes from the JS beacon, and
# metrics.collect() records the raw-log tallies alongside it precisely so that a
# beacon which stops firing reads as "log says 12, beacon says 0" rather than as
# a quiet day (metrics.py:579-602). That guarantee only holds for someone who
# can see both numbers, and the review agent cannot: it reads this file. Without
# them, the 2026-08-14 cutover looks from here like traffic falling 17 -> 2
# overnight. They are absent for every date before PV_START, which is correct —
# pre-cutover history was never counted that way and cannot be reconstructed.
SERIES = ("visitors", "pageviews", "log_visitors", "log_pageviews",
          "organic_visitors", "local_visitors",
          "ai_visitors", "direct_visitors", "referral_visitors",
          "campaign_visitors", "bot_hits", "call_taps", "ai_calls",
          "bookings", "phone_leads", "total_leads") + metrics.CRAWLER_SERIES

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


def _scrub(value, found):
    """Walk the structure and redact anything shaped like personal data.

    Redact rather than refuse. The first version raised, and on day one a scout
    technique quoting a marketing article — "We just finished a roof for your
    neighbor at 123 Maple St" — matched the street-address pattern and blocked
    the entire publish, which cut the review agent off from every metric over
    one line of example prose in someone else's blog post.

    Refusing is the wrong failure for a filter that runs unattended: a false
    positive takes the whole bridge down, and a real leak is equally well
    prevented by removing the value. Every redaction is counted and surfaced in
    the snapshot, so a hit still gets noticed rather than silently swallowed —
    and a hit in a field fed by the bookings database would be a genuine bug
    worth chasing, since nothing on that path should reach here at all.
    """
    if isinstance(value, dict):
        return {k: _scrub(v, found) for k, v in value.items()}
    if isinstance(value, list):
        return [_scrub(v, found) for v in value]
    if not isinstance(value, str):
        return value

    out = value
    for pattern, label in PII_PATTERNS:
        def _sub(m):
            hit = m.group(0)
            if any(a in hit or hit in a for a in ALLOWED):
                return hit          # the business's own published details
            found.append({"kind": label, "sample": hit[:40]})
            return f"[redacted {label}]"
        out = pattern.sub(_sub, out)
    return out


def scrub(blob):
    """Returns (clean_blob, [redaction, ...])."""
    found = []
    clean = _scrub(blob, found)
    return clean, found


def _series(metric, days=45):
    return [{"date": d, "value": v}
            for d, v in ledger.series("__site__", metric)[-days:]]


def _code_fingerprint():
    """Which version of the engine actually produced this snapshot.

    The droplet's docroot is not a git checkout, so a change committed to the
    repository is not running until somebody copies the file across. Three
    consecutive reviews have had to work that out by forensics — inferring the
    deployed version from which optional keys were missing from this file —
    and on 2026-08-09 that inference had to resolve a *partial* deploy, where
    techniques.py and templates.py were live but snapshot.py, gsc.py,
    metrics.py and scout.py were four days stale. Absence-of-a-key is a poor
    signal for that: it only exists where a change happened to add a key, it
    says nothing about changes that altered behaviour in place, and it goes
    quiet the moment the two versions agree on their output shape.

    A digest per module is the direct measurement. The reviewer can hash the
    same files in its checkout and compare, so "is the droplet running what is
    on main" stops being an inference and becomes a diff. Content hashes
    rather than a git revision because the docroot has no git metadata to read.

    Tests are excluded: they never run on the droplet, so a difference there
    would be noise in exactly the comparison this exists to make.
    """
    modules = {}
    for name in sorted(os.listdir(HERE)):
        if not name.endswith(".py") or name.startswith("test_"):
            continue
        try:
            with open(os.path.join(HERE, name), "rb") as fh:
                modules[name] = hashlib.sha256(fh.read()).hexdigest()[:12]
        except OSError:
            continue

    # The CLI entry point lives beside the package, not inside it, and it is a
    # file the deploy can miss on its own — 2026-08-08's scout change needed
    # both growth_daily.py and growth/scout.py to move together.
    cli = os.path.join(os.path.dirname(HERE), "growth_daily.py")
    try:
        with open(cli, "rb") as fh:
            modules["../growth_daily.py"] = hashlib.sha256(fh.read()).hexdigest()[:12]
    except OSError:
        pass

    joined = "".join(f"{k}:{v}" for k, v in sorted(modules.items()))
    return {"modules": modules,
            "combined": hashlib.sha256(joined.encode()).hexdigest()[:12],
            "note": ("sha256[:12] of each engine source file as it exists on the "
                     "machine that ran it. Hash the same files in the repository "
                     "to see what is deployed and what is still only committed.")}


def build(docroot):
    kw = keywords.summary()
    sb = review.scoreboard()
    techs = ledger.load_techniques()
    # Carried through as-is when Search Console has never run, so that
    # "gsc": null still means "no rank data" rather than "an empty report".
    gsc_last = ledger.get_state("gsc_last")

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
            # The goal metric, one row per query, instead of only its total.
            # See keywords.summary().
            "ranked": kw["ranked"],
            # What Google shows this site for that nobody chose to track.
            # Not added automatically — see gsc.discover() for why.
            "discovered_untracked": gsc.discover(),
        },
        # `pages` is why improve_ctr did or did not pick each page up. See
        # gsc._classify_pages() — a no-op from that technique is otherwise
        # unauditable from the snapshot alone.
        "gsc": ({**gsc_last, "pages": gsc.page_report()} if gsc_last
                else gsc_last),
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
        # See _code_fingerprint(): what the droplet is actually running, so the
        # reviewer can diff it against the repository instead of deducing it.
        "code_version": _code_fingerprint(),
    }
    snap, redactions = scrub(snap)
    snap["redactions"] = {
        "count": len(redactions),
        "items": redactions[:20],
        "note": ("Anything shaped like a phone number, email or street address is "
                 "removed before publishing. A non-zero count is usually an example "
                 "quoted in scout research, not customer data — but a hit in a field "
                 "fed by the bookings database would be a real bug worth chasing."),
    }
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
        s = ledger.complete_series("__site__", m)
        return s[-1][1] if s else "—"
    day = ledger.complete_series("__site__", "visitors")
    when = day[-1][0] if day else "yesterday"
    L.append(f"{when}: {last('visitors')} visitors "
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

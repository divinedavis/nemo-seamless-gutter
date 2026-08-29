#!/usr/bin/env python3
"""The daily review: keep what works, retire what doesn't, drop what's redundant.

This is the half of the loop that makes it self-improving rather than merely
automated. Every day it re-reads the measured series behind each active
technique and asks three questions:

  1. Has it had a fair run?      (below GRACE_DAYS, nothing is judged — SEO
                                  changes take weeks to show up in a series)
  2. Did it earn its traffic?    (owned visitors since activation vs threshold)
  3. Is it redundant?            (another technique owns overlapping URLs and
                                  massively outperforms it)

Retiring is cheap and reversible: status flips to "retired", the driver stops
running it tomorrow, and the verdict stays in the ledger forever so the same
idea does not get re-proposed as if it were new.
"""
import datetime
import statistics

from . import ledger

GRACE_DAYS = 30          # nothing is judged before this — local SEO is slow, and
                         # a new town page can take a month just to get indexed
WINDOW = 14              # trailing window for "is it working now"
MIN_TOTAL_VISITORS = 8   # cumulative owned visitors needed to call it alive.
                         # Low on purpose: this is a county contractor, not a
                         # content site. Eight of the right people is a job.
MIN_RECENT_MEDIAN = 0    # a technique can go days between visitors here and
                         # still be earning its keep
REDUNDANCY_RATIO = 0.10  # <10% of an overlapping technique's traffic = redundant

# Plumbing, not experiments. Retiring the sitemap rebuild because traffic was
# flat would break every other technique, so these are never auto-retired.
PROTECTED = {"rebuild_sitemap", "ping_indexnow", "internal_links"}


# The date a running technique should be judged from.
#
# `set_status` stamps `activated` whenever it flips something to active, so in
# the normal path this is just that field. But a technique can reach the ledger
# already active without going through it — seeded that way, or hand-edited in
# techniques.json on the droplet — and T014 (geo_answer_first_content_pass) is
# sitting in exactly that state today: status "active", `activated` null,
# building pages every morning. Reading the missing field as "zero days old"
# meant it could never leave the grace period and therefore could never be
# judged, in the one module whose whole job is judging. `added` is the honest
# floor: whatever day it started running, it was not before the day it existed.
def _since(t):
    return t.get("activated") or t.get("added")


def _days_active(t):
    a = _since(t)
    if not a:
        return 0
    try:
        return (datetime.date.today() - datetime.date.fromisoformat(a)).days
    except Exception:
        return 0


# complete_series, not series: a technique is judged on finished days only. A
# row dated today is a few hours of log, and this is the code that retires
# things autonomously — a partial day dragging a median down is how a working
# technique gets killed on the strength of one morning.
def _owned(t):
    return ledger.complete_series(t["slug"], "owned_visitors",
                                  since=_since(t))


def _global(metric, since=None):
    return ledger.complete_series("__site__", metric, since=since)


def _trend(pairs, window=WINDOW):
    """(recent_median, prior_median) over two adjacent windows."""
    vals = [v for _, v in pairs]
    if len(vals) < 2:
        return (None, None)
    recent = vals[-window:]
    prior = vals[-2 * window:-window] or []
    return (statistics.median(recent) if recent else None,
            statistics.median(prior) if prior else None)


def evaluate(t):
    """Judge one technique. Returns a dict; does not mutate the ledger."""
    days = _days_active(t)
    slug = t["slug"]
    res = {"id": t["id"], "slug": slug, "name": t.get("name", slug),
           "days_active": days, "action": "keep", "why": "", "measured": {}}

    if t.get("status") != "active":
        res["action"] = "skip"
        res["why"] = f"status is {t.get('status')}"
        return res

    if slug in PROTECTED:
        res["why"] = "infrastructure — kept regardless of measured traffic"
        return res

    if days < GRACE_DAYS:
        res["action"] = "keep"
        res["why"] = f"only {days}d active — under the {GRACE_DAYS}d grace period"
        return res

    if t.get("prefixes"):
        pairs = _owned(t)
        total = sum(v for _, v in pairs)
        recent, prior = _trend(pairs)
        res["measured"] = {"total_owned_visitors": total,
                           "recent_median": recent, "prior_median": prior,
                           "days_measured": len(pairs)}
        if len(pairs) < GRACE_DAYS // 2:
            res["why"] = f"only {len(pairs)} days of measurement — not enough to judge"
            return res
        if total < MIN_TOTAL_VISITORS and (recent or 0) < MIN_RECENT_MEDIAN:
            res["action"] = "retire"
            res["why"] = (f"{total} owned visitors in {days}d and a trailing median of "
                          f"{recent} — below the bar to keep running daily")
            return res
        direction = ""
        if recent is not None and prior is not None:
            direction = " and rising" if recent > prior else (
                " but falling" if recent < prior else " and flat")
        res["why"] = f"{total} owned visitors in {days}d (median {recent}/day{direction})"
        return res

    # Site-wide technique: judged on its declared global metric, comparing the
    # trailing window against the window immediately before it was activated.
    metric = t.get("metric") or "organic_visitors"
    pairs = _global(metric)
    since = _since(t) or ""
    after = [(d, v) for d, v in pairs if d >= since]
    before = [(d, v) for d, v in pairs if d < since][-WINDOW:]
    a_med = statistics.median([v for _, v in after[-WINDOW:]]) if after else None
    b_med = statistics.median([v for _, v in before]) if before else None
    res["measured"] = {"metric": metric, "median_after": a_med, "median_before": b_med,
                       "days_measured": len(after)}
    if len(after) < GRACE_DAYS // 2:
        res["why"] = f"only {len(after)} days of {metric} since activation"
        return res
    if b_med is None:
        res["why"] = f"{metric} median {a_med}/day since activation (no pre-activation baseline)"
        return res
    if a_med is not None and a_med <= b_med:
        res["action"] = "flag"
        res["why"] = (f"{metric} median {a_med}/day vs {b_med}/day before activation — "
                      f"no measurable lift after {days}d")
        return res
    res["why"] = f"{metric} median {a_med}/day vs {b_med}/day before activation"
    return res


def earned(res):
    """Does this technique's own measurement support the claim that it WORKS?

    `evaluate` returns action "keep" for two quite different situations: the
    evidence is good, and there is no evidence. Before this existed, `run`
    stamped `works: True` on both, so T001 carried the verdict
    "7 owned visitors in 33d (median 0.0/day and flat)" with `works: True` —
    a sentence that states the failure and a field that reports success.

    The bar here is not a new one. It is the module's own already-declared
    threshold, applied to the positive verdict as well as the negative one:

      * a technique with URLs of its own must clear MIN_TOTAL_VISITORS, the
        same count `evaluate` uses to decide it is alive at all;
      * a site-wide technique must beat the window before it was switched on.
        No baseline is not a pass — it is an unanswerable question, and the
        honest record is no verdict rather than a favourable one.

    Returning False is NOT a finding of failure. It means "no claim yet", and
    the caller withdraws any running verdict rather than writing `works: False`.
    """
    m = res.get("measured") or {}
    if not m:
        return False
    if "total_owned_visitors" in m:
        return m["total_owned_visitors"] >= MIN_TOTAL_VISITORS
    before, after = m.get("median_before"), m.get("median_after")
    if before is None or after is None:
        return False
    return after > before


def find_redundant(techs):
    """Techniques whose URLs overlap and whose traffic is a rounding error next
    to the overlapping one. Running both costs build time and splits link equity."""
    out = []
    act = [t for t in techs if t.get("status") == "active" and t.get("prefixes")]
    totals = {t["slug"]: sum(v for _, v in _owned(t)) for t in act}
    for a in act:
        for b in act:
            if a["slug"] >= b["slug"]:
                continue
            overlap = any(p.startswith(q) or q.startswith(p)
                          for p in a["prefixes"] for q in b["prefixes"])
            if not overlap:
                continue
            ta, tb = totals[a["slug"]], totals[b["slug"]]
            if _days_active(a) < GRACE_DAYS or _days_active(b) < GRACE_DAYS:
                continue
            weak, strong, wv, sv = ((a, b, ta, tb) if ta < tb else (b, a, tb, ta))
            if sv > 0 and wv <= sv * REDUNDANCY_RATIO:
                out.append({"weak": weak["id"], "weak_slug": weak["slug"],
                            "strong_slug": strong["slug"], "weak_visitors": wv,
                            "strong_visitors": sv})
    return out


def auto_activate(apply=True):
    """Switch on any candidate that has a working implementation.

    The scout files ideas as candidates and cannot activate them, which is the
    right default for ideas that need money, an OAuth grant, or someone to
    knock on a door. But a candidate whose slug matches a function in
    techniques.REGISTRY is different: the code exists, it was reviewed by a
    human before it shipped, and leaving it switched off means the engine sits
    on a capability it already has waiting to be told twice.

    So the rule is narrow and mechanical — implementation exists, therefore it
    runs. Anything without code stays a candidate no matter how good it sounds.
    """
    from . import techniques
    out = []
    for t in ledger.load_techniques():
        if t.get("status") != "candidate":
            continue
        if t.get("slug") not in techniques.REGISTRY:
            continue
        # A previous verdict of "does not work" is a decision, not a gap.
        v = t.get("verdict") or {}
        if v and not v.get("works"):
            continue
        if apply:
            ledger.set_status(t["id"], "active",
                              "auto-activated: an implementation exists for this slug")
        out.append(f"ACTIVATED {t['id']} {t['slug']} — implementation exists")
    return out


def run(apply=True):
    """Evaluate everything; optionally write the decisions back to the ledger."""
    activated = auto_activate(apply=apply)
    techs = ledger.load_techniques()
    results = [evaluate(t) for t in techs]
    redundant = find_redundant(techs)
    red_ids = {r["weak"] for r in redundant}

    actions = []
    for r in results:
        if r["action"] == "retire" and apply:
            ledger.set_status(r["id"], "retired", r["why"])
            ledger.set_verdict(r["id"], False, r["why"], r["measured"])
            actions.append(f"RETIRED {r['id']} {r['slug']} — {r['why']}")
        elif r["action"] == "keep" and r["days_active"] >= GRACE_DAYS and r["measured"] and apply:
            # Record a running verdict so the year-end list is always current —
            # but only where the measurement actually supports one. Where it
            # does not, withdraw any verdict a previous run stamped, so the
            # scoreboard heals itself instead of carrying the claim all year.
            if earned(r):
                ledger.set_verdict(r["id"], True, r["why"], r["measured"])
            else:
                v = ledger.get(r["id"]) or {}
                v = v.get("verdict") or {}
                if v.get("works"):
                    ledger.clear_verdict(r["id"])
                    actions.append(
                        f"WITHDREW verdict on {r['id']} {r['slug']} — "
                        f"not supported by its own measurement: {r['why']}")

    for rr in redundant:
        if rr["weak"] in red_ids and apply:
            why = (f"redundant with {rr['strong_slug']} "
                   f"({rr['weak_visitors']} vs {rr['strong_visitors']} owned visitors)")
            ledger.set_status(rr["weak"], "retired", why)
            ledger.set_verdict(rr["weak"], False, why)
            actions.append(f"RETIRED {rr['weak']} — {why}")

    return {"evaluated": results, "redundant": redundant,
            "actions": activated + actions}


def scoreboard():
    """The list the owner wants at the end of the year: what worked, what didn't."""
    techs = ledger.load_techniques()
    works, fails, pending = [], [], []
    for t in techs:
        v = t.get("verdict")
        row = {"id": t["id"], "name": t.get("name"), "kind": t.get("kind"),
               "status": t.get("status"), "source": t.get("source"),
               "hypothesis": t.get("hypothesis"),
               "activated": t.get("activated"), "retired": t.get("retired"),
               "why": (v or {}).get("why"), "measured": (v or {}).get("measured")}
        if not v:
            pending.append(row)
        elif v.get("works"):
            works.append(row)
        else:
            fails.append(row)
    works.sort(key=lambda r: -( (r.get("measured") or {}).get("total_owned_visitors") or 0))
    return {"works": works, "does_not_work": fails, "not_yet_judged": pending}

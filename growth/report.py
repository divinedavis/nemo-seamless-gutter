#!/usr/bin/env python3
"""The daily growth email: what ran, what it moved, and how far from the goal.

Deliberately blunt. If a technique did nothing, the report says it did nothing —
a growth loop that only reports good news is a slower way of wasting the summer.

Two honesty rules this file enforces:
  * When Search Console is not connected, the goal line says UNMEASURED and
    shows coverage as a labelled proxy. It never prints coverage where a reader
    would read rank.
  * Call volume is reported as "leads captured", not "calls", because tel: taps
    are only visible in GA4 and the engine cannot read them. The gap is stated
    rather than papered over.
"""
import os
import smtplib
import statistics
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from . import keywords, ledger, review

BAR = "=" * 58


def _fmt(v):
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:,.2f}"
    return f"{v:,}" if isinstance(v, int) else str(v)


def _last(metric):
    s = ledger.series("__site__", metric)
    return s[-1][1] if s else None


def _series_summary(metric, days=14):
    pairs = ledger.series("__site__", metric)[-days:]
    if not pairs:
        return "no data yet"
    vals = [v for _, v in pairs]
    recent = statistics.median(vals[-7:]) if len(vals) >= 3 else vals[-1]
    prior = statistics.median(vals[-14:-7]) if len(vals) >= 10 else None
    arrow = ""
    if prior is not None:
        arrow = " (up)" if recent > prior else (" (down)" if recent < prior else " (flat)")
    return f"{_fmt(vals[-1])} yesterday · {_fmt(recent)}/day median{arrow}"


def _sum_last(metric, days=30):
    return sum(v for _, v in ledger.series("__site__", metric)[-days:])


def build_text(run_log=None, review_out=None, scout_out=None):
    techs = ledger.load_techniques()
    active = [t for t in techs if t.get("status") == "active"]
    cands = [t for t in techs if t.get("status") == "candidate"]
    retired = [t for t in techs if t.get("status") == "retired"]
    kw = keywords.summary()

    L = []
    L.append("NEMO SEAMLESS GUTTER — DAILY GROWTH REPORT")
    L.append(BAR)
    L.append(ledger.today())
    L.append("")

    # ---- anything that stopped the engine working at all -------------------
    # Surfaced at the very top, not buried in the run log. An engine that
    # silently produced nothing for three weeks because a key expired is worse
    # than one that never ran.
    blockers = []
    details = [r.get("detail", "") for r in (run_log or [])]
    if scout_out and not scout_out.get("ok"):
        details.append(scout_out.get("detail", ""))
    if any("credit balance is too low" in d for d in details):
        blockers.append(
            "Anthropic API credits are exhausted. No new pages can be written and the "
            "scout cannot run until the account is topped up. This also stops the "
            "monthly guide cron (seo/gen_article.py), which shares the same key.")
    if any("no Anthropic key" in d for d in details):
        blockers.append("No Anthropic API key found — expected ANTHROPIC_API_KEY in seo/.env.")
    if blockers:
        L.append("BLOCKED")
        for b in blockers:
            L.append(f"  * {b}")
        L.append("")

    # ---- the goal ----------------------------------------------------------
    L.append("THE GOAL — over half of York County gutter searches")
    if kw["share_pct"] is not None:
        L.append(f"  Search share   {kw['share_pct']}% of {kw['total']} tracked queries "
                 f"hold a top-3 position  (target: 50%)")
        L.append(f"                 {kw['top3']} in top 3 · {kw['top10']} in top 10 · "
                 f"{kw['ranked_known']} queries with known rank")
    else:
        L.append("  Search share   UNMEASURED — Search Console is not connected, so no")
        L.append("                 tool here knows where the site actually ranks.")
        L.append(f"  Coverage proxy {kw['coverage_pct']}% of {kw['total']} tracked queries "
                 f"have a page targeting them")
        L.append("                 (coverage is not rank — see WAITING ON YOU below)")
    L.append("")

    # ---- what the business actually cares about ----------------------------
    L.append("LEADS (what pays the bills)")
    L.append(f"  Online bookings      {_series_summary('bookings')}")
    L.append(f"  Phone-agent leads    {_series_summary('phone_leads')}")
    L.append(f"  Last 30 days         {_fmt(_sum_last('bookings'))} bookings + "
             f"{_fmt(_sum_last('phone_leads'))} phone leads")
    L.append(f"  All time             {_fmt(_last('bookings_all_time'))} bookings, "
             f"{_fmt(_last('phone_leads_all_time'))} phone leads")
    L.append("  Note: direct dials from the page or the Business Profile are NOT counted")
    L.append("        here — those fire as GA4 events and need a GA4 service account.")
    L.append("")

    # ---- traffic -----------------------------------------------------------
    L.append("TRAFFIC (bots and Eric's own visits excluded)")
    for m, label in (("visitors", "All visitors"),
                     ("organic_visitors", "Organic search"),
                     ("local_visitors", "Maps / directories"),
                     ("ai_visitors", "AI answer engines"),
                     ("direct_visitors", "Direct"),
                     ("referral_visitors", "Referral")):
        L.append(f"  {label:<21} {_series_summary(m)}")
    L.append("")

    # ---- what ran ----------------------------------------------------------
    if run_log:
        L.append("WHAT RAN THIS MORNING")
        for r in run_log:
            mark = "ok  " if r.get("ok") else "FAIL"
            L.append(f"  [{mark}] {r['slug']:<16} {r.get('detail', '')}")
        L.append("")

    # ---- per-technique performance ----------------------------------------
    L.append(f"ACTIVE TECHNIQUES ({len(active)})")
    for t in active:
        L.append(f"  {t['id']} {t['name']}")
        if t.get("prefixes"):
            pairs = ledger.series(t["slug"], "owned_visitors", since=t.get("activated"))
            total = sum(v for _, v in pairs)
            recent = statistics.median([v for _, v in pairs[-7:]]) if pairs else None
            L.append(f"       {_fmt(total)} visitors since {t.get('activated')} · "
                     f"{_fmt(recent)}/day recent · owns {', '.join(t['prefixes'])}")
        else:
            L.append(f"       site-wide · judged on {t.get('metric')} · "
                     f"{_series_summary(t.get('metric'))}")
    L.append("")

    # ---- review decisions --------------------------------------------------
    if review_out and review_out.get("actions"):
        L.append("REVIEW DECISIONS TODAY")
        for a in review_out["actions"]:
            L.append(f"  {a}")
        L.append("")

    # ---- scout -------------------------------------------------------------
    if scout_out and scout_out.get("ok"):
        added = scout_out.get("techniques_added") or []
        L.append("SCOUT")
        if added:
            L.append(f"  Proposed {len(added)} new technique(s) — they are CANDIDATES and")
            L.append("  will not run until switched on:")
            for s in added:
                t = ledger.get(s)
                if not t:
                    continue
                L.append(f"    {t['id']} {t['name']}")
                L.append(f"        {(t.get('hypothesis') or '')[:150]}")
                first = (t.get("notes") or "").strip().split("\n")[0]
                if first:
                    L.append(f"        {first}")
        else:
            L.append("  No new techniques worth proposing today.")
        if scout_out.get("keywords_added"):
            L.append(f"  Added {len(scout_out['keywords_added'])} quer(y/ies) to the "
                     f"tracked universe.")
        if scout_out.get("notes"):
            L.append(f"  Note: {scout_out['notes'][:400]}")
        L.append("")
    elif scout_out:
        L.append(f"SCOUT — did not run: {scout_out.get('detail', 'unknown')}")
        L.append("")

    # ---- scoreboard --------------------------------------------------------
    sb = review.scoreboard()
    if sb["works"] or sb["does_not_work"]:
        L.append("SCOREBOARD SO FAR")
        for r in sb["works"]:
            L.append(f"  WORKS        {r['id']} {r['name']} — {r['why']}")
        for r in sb["does_not_work"]:
            L.append(f"  DIDN'T WORK  {r['id']} {r['name']} — {r['why']}")
        L.append("")

    # ---- blocked on a human ------------------------------------------------
    blocked = [t for t in cands if t.get("notes")]
    if blocked:
        L.append("WAITING ON YOU — these cannot run until someone acts")
        for t in blocked:
            first = (t.get("notes") or "").strip().split("\n")[0]
            L.append(f"  {t['id']} {t['name']}")
            L.append(f"       {first}")
        L.append("")

    # ---- content roadmap ---------------------------------------------------
    if kw["gaps"]:
        L.append(f"UNCOVERED QUERIES ({len(kw['gaps'])} total — this is the build queue)")
        for g in kw["gaps"][:12]:
            L.append(f"  · {g}")
        L.append("")

    L.append(f"Ledger: {len(techs)} techniques — {len(active)} active, "
             f"{len(cands)} candidate, {len(retired)} retired")
    L.append("Full detail: growth_daily.py status   ·   logs: /var/log/nemo-growth.log")
    return "\n".join(L)


def _smtp_from_env():
    """The booking server's SMTP settings are the ones already proven to work."""
    host = os.environ.get("SMTP_HOST")
    port = int(os.environ.get("SMTP_PORT", "587") or 587)
    user = os.environ.get("SMTP_USER")
    pw = os.environ.get("SMTP_PASS") or os.environ.get("SMTP_PASSWORD")
    return host, port, user, pw


def subject_line():
    """Lead with the number being chased, so the inbox list is already useful."""
    kw = keywords.summary()
    if kw["share_pct"] is not None:
        head = f"{kw['share_pct']}% top-3"
    else:
        head = "rank unmeasured"
    leads = ledger.series("__site__", "total_leads")
    y = leads[-1][1] if leads else 0
    tail = f"{y} lead{'s' if y != 1 else ''} yesterday" if y else "no leads yesterday"
    return f"NEMO growth · {head} · {tail} · {ledger.today()}"


def email(text, to, subject=None, html=None):
    """Send the report as multipart/alternative.

    The HTML part is what Eric sees on his phone; the plain-text part is the
    same content and is what shows up in clients that block HTML, in search
    results, and in notification previews. Sending only HTML would make the
    report unreadable in exactly the places it gets skimmed.
    """
    host, port, user, pw = _smtp_from_env()
    if not (host and user and pw):
        raise RuntimeError("SMTP_HOST/SMTP_USER/SMTP_PASS not set — source server/.env")

    sender = os.environ.get("FROM_EMAIL", user)
    recipients = [a.strip() for a in to.split(",") if a.strip()]

    if html:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(text, "plain", "utf-8"))
        # Last part wins in multipart/alternative, so HTML must come second.
        msg.attach(MIMEText(html, "html", "utf-8"))
    else:
        msg = MIMEText(text, "plain", "utf-8")

    msg["Subject"] = subject or subject_line()
    msg["From"] = f"NEMO Growth <{sender}>"
    msg["To"] = to
    with smtplib.SMTP(host, port, timeout=30) as s:
        s.starttls()
        s.login(user, pw)
        s.sendmail(sender, recipients, msg.as_string())
    return True

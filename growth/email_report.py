#!/usr/bin/env python3
"""The HTML version of the daily growth email.

Eric reads this on a phone between jobs, so it is built for scanning: the
number that matters is large and near the top, and everything below it is a
short labelled row. `report.build_text()` is still the source of truth for
content — this presents the same facts, and the plain-text version rides along
as the multipart fallback.

Email HTML is not web HTML. Rules followed here, all of them the boring kind:
tables for layout (Outlook ignores flexbox and grid), styles inlined on the
elements (Gmail strips <style> from the head in some clients), no external
images or fonts (they are blocked by default and would leave holes), and a
600px max width. Nothing here depends on JavaScript or a network fetch.

Colours are the brand's: navy #243C94, orange #F16C27 for calls to action.
Red is reserved for things that are actually broken, so it keeps its meaning.
"""
import html
import statistics

from . import keywords, ledger, review

NAVY = "#243C94"
ORANGE = "#F16C27"
INK = "#1a1a1a"
MUTED = "#6b7280"
LINE = "#e5e7eb"
BG = "#f4f5f7"
CARD = "#ffffff"
GOOD = "#15803d"
BAD = "#b91c1c"
WARN = "#b45309"

FONT = ("-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,"
        "Arial,sans-serif")


def _e(s):
    return html.escape(str(s if s is not None else ""), quote=False)


def _last(metric):
    s = ledger.series("__site__", metric)
    return s[-1][1] if s else None


def _trend(metric, days=14):
    """(latest, median_recent, direction) for a metric."""
    pairs = ledger.series("__site__", metric)[-days:]
    if not pairs:
        return None, None, ""
    vals = [v for _, v in pairs]
    recent = statistics.median(vals[-7:]) if len(vals) >= 3 else vals[-1]
    prior = statistics.median(vals[-14:-7]) if len(vals) >= 10 else None
    direction = ""
    if prior is not None:
        direction = "up" if recent > prior else ("down" if recent < prior else "flat")
    return vals[-1], recent, direction


def _arrow(direction):
    if direction == "up":
        return f'<span style="color:{GOOD};font-weight:600">&#9650;</span>'
    if direction == "down":
        return f'<span style="color:{BAD};font-weight:600">&#9660;</span>'
    if direction == "flat":
        return f'<span style="color:{MUTED}">&#8212;</span>'
    return ""


def _card(inner, pad="18px 20px"):
    return (f'<tr><td style="padding:0 0 14px 0">'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            f'style="background:{CARD};border:1px solid {LINE};border-radius:10px">'
            f'<tr><td style="padding:{pad}">{inner}</td></tr></table></td></tr>')


def _h(text, colour=None):
    return (f'<div style="font:600 11px {FONT};letter-spacing:.08em;'
            f'text-transform:uppercase;color:{colour or MUTED};'
            f'margin:0 0 12px 0">{_e(text)}</div>')


def _rows(pairs):
    """Label/value rows — the workhorse layout for most sections."""
    out = ['<table role="presentation" width="100%" cellpadding="0" cellspacing="0">']
    for i, (label, value) in enumerate(pairs):
        border = f"border-top:1px solid {LINE};" if i else ""
        out.append(
            f'<tr><td style="{border}padding:8px 0;font:400 14px {FONT};'
            f'color:{MUTED};width:52%">{label}</td>'
            f'<td style="{border}padding:8px 0;font:600 14px {FONT};'
            f'color:{INK};text-align:right">{value}</td></tr>')
    out.append("</table>")
    return "".join(out)


# ------------------------------------------------------------------ sections

def _goal_card():
    kw = keywords.summary()
    if kw["share_pct"] is None:
        body = (
            f'{_h("The goal", NAVY)}'
            f'<div style="font:700 30px {FONT};color:{WARN};line-height:1.1">'
            f'Unmeasured</div>'
            f'<div style="font:400 13px {FONT};color:{MUTED};margin-top:8px;'
            f'line-height:1.5">Search Console is not connected, so nothing here '
            f'knows where the site actually ranks.<br>'
            f'<strong style="color:{INK}">{kw["coverage_pct"]}%</strong> of '
            f'{kw["total"]} tracked queries have a page targeting them — that is '
            f'page coverage, <em>not</em> rank.</div>')
        return _card(body)

    pct = kw["share_pct"]
    target = 50
    fill = max(1.5, min(100.0, pct / target * 100))
    colour = GOOD if pct >= target else (ORANGE if pct > 0 else BAD)

    body = (
        f'{_h("The goal — top-3 share of York County gutter searches", NAVY)}'
        f'<table role="presentation" cellpadding="0" cellspacing="0"><tr>'
        f'<td style="font:700 38px {FONT};color:{colour};line-height:1">{pct}%</td>'
        f'<td style="padding-left:12px;font:400 13px {FONT};color:{MUTED};'
        f'vertical-align:bottom;padding-bottom:6px">of a {target}% target</td>'
        f'</tr></table>'
        # progress bar: two nested tables, the only thing every client renders
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="margin:14px 0 10px 0;background:{LINE};border-radius:5px">'
        f'<tr><td style="width:{fill}%;background:{colour};height:8px;'
        f'border-radius:5px;font-size:0;line-height:0">&nbsp;</td>'
        f'<td style="font-size:0;line-height:0">&nbsp;</td></tr></table>'
        f'<div style="font:400 13px {FONT};color:{MUTED};line-height:1.5">'
        f'<strong style="color:{INK}">{kw["top3"]}</strong> queries in the top 3 · '
        f'<strong style="color:{INK}">{kw["top10"]}</strong> in the top 10 · '
        f'rank known for {kw["ranked_known"]} of {kw["total"]} tracked</div>')
    return _card(body)


def _leads_card():
    b_last, b_med, b_dir = _trend("bookings")
    p_last, p_med, p_dir = _trend("phone_leads")
    b30 = sum(v for _, v in ledger.series("__site__", "bookings")[-30:])
    p30 = sum(v for _, v in ledger.series("__site__", "phone_leads")[-30:])

    body = (
        f'{_h("Leads — what pays the bills", NAVY)}'
        + _rows([
            ("Online bookings yesterday",
             f'{b_last if b_last is not None else "&#8212;"} {_arrow(b_dir)}'),
            ("Phone-agent leads yesterday",
             f'{p_last if p_last is not None else "&#8212;"} {_arrow(p_dir)}'),
            ("Last 30 days", f"{b30} booked · {p30} phoned"),
            ("All time", f'{_last("bookings_all_time") or 0} booked · '
                         f'{_last("phone_leads_all_time") or 0} phoned'),
        ])
        + f'<div style="font:400 12px {FONT};color:{MUTED};margin-top:12px;'
          f'line-height:1.5;padding-top:10px;border-top:1px solid {LINE}">'
          f'Direct dials from the page or the Business Profile are not counted '
          f'here — those fire as GA4 events and need a separate service account.</div>')
    return _card(body)


def _traffic_card():
    rows = []
    for metric, label in (("visitors", "All visitors"),
                          ("organic_visitors", "Organic search"),
                          ("local_visitors", "Maps &amp; directories"),
                          ("ai_visitors", "AI answer engines"),
                          ("direct_visitors", "Direct"),
                          ("referral_visitors", "Referral")):
        last, med, direction = _trend(metric)
        if last is None:
            rows.append((label, '<span style="color:%s">no data</span>' % MUTED))
        else:
            rows.append((label,
                         f'{last} <span style="color:{MUTED};font-weight:400">'
                         f'· {med}/day median</span> {_arrow(direction)}'))
    body = (_h("Traffic yesterday — bots and Eric's own visits excluded", NAVY)
            + _rows(rows))
    return _card(body)


def _rank_card():
    """Where the tracked money queries actually sit. Only once rank is known."""
    kws = [k for k in keywords.load() if k.get("position")]
    if not kws:
        return ""
    kws.sort(key=lambda k: k["position"])
    out = ['<table role="presentation" width="100%" cellpadding="0" cellspacing="0">',
           f'<tr><td style="font:600 11px {FONT};color:{MUTED};padding:0 0 6px 0">'
           f'QUERY</td>'
           f'<td style="font:600 11px {FONT};color:{MUTED};text-align:right;'
           f'padding:0 0 6px 0">POS</td>'
           f'<td style="font:600 11px {FONT};color:{MUTED};text-align:right;'
           f'padding:0 0 6px 0">IMPR</td></tr>']
    for k in kws[:12]:
        pos = k["position"]
        colour = GOOD if pos <= 3 else (ORANGE if pos <= 10 else MUTED)
        out.append(
            f'<tr><td style="border-top:1px solid {LINE};padding:7px 0;'
            f'font:400 13px {FONT};color:{INK}">{_e(k["query"])}</td>'
            f'<td style="border-top:1px solid {LINE};padding:7px 0;'
            f'font:600 13px {FONT};color:{colour};text-align:right">{pos}</td>'
            f'<td style="border-top:1px solid {LINE};padding:7px 0;'
            f'font:400 13px {FONT};color:{MUTED};text-align:right">'
            f'{int(k.get("impressions") or 0)}</td></tr>')
    out.append("</table>")
    extra = ""
    if len(kws) > 12:
        extra = (f'<div style="font:400 12px {FONT};color:{MUTED};margin-top:10px">'
                 f'+{len(kws) - 12} more with known rank</div>')
    return _card(_h("Where the tracked queries rank", NAVY) + "".join(out) + extra)


def _discovered_card(snapshot_data=None):
    """Queries Google shows the site for that nobody chose to track."""
    from . import gsc
    try:
        found = gsc.discover()
    except Exception:
        return ""
    if not found:
        return ""
    rows = []
    for d in found[:8]:
        pos = d.get("position")
        colour = GOOD if pos and pos <= 3 else MUTED
        rows.append(
            f'<tr><td style="border-top:1px solid {LINE};padding:7px 0;'
            f'font:400 13px {FONT};color:{INK}">{_e(d["query"])}</td>'
            f'<td style="border-top:1px solid {LINE};padding:7px 0;'
            f'font:600 13px {FONT};color:{colour};text-align:right">{pos}</td>'
            f'<td style="border-top:1px solid {LINE};padding:7px 0;'
            f'font:400 13px {FONT};color:{MUTED};text-align:right">'
            f'{d["impressions"]}</td></tr>')
    body = (_h("Showing up for these — but not tracking them", NAVY)
            + '<table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
            + "".join(rows) + "</table>"
            + f'<div style="font:400 12px {FONT};color:{MUTED};margin-top:12px;'
              f'line-height:1.5">Not added automatically: the goal is a percentage, '
              f'so padding its denominator with out-of-area searches would make 50% '
              f'both harder and meaningless.</div>')
    return _card(body)


def _ran_card(run_log):
    if not run_log:
        return ""
    rows = []
    for r in run_log:
        ok = r.get("ok")
        chip = (f'<span style="background:{"#dcfce7" if ok else "#fee2e2"};'
                f'color:{GOOD if ok else BAD};font:600 10px {FONT};'
                f'padding:2px 7px;border-radius:9px;letter-spacing:.04em">'
                f'{"OK" if ok else "FAIL"}</span>')
        rows.append(
            f'<tr><td style="padding:8px 10px 8px 0;vertical-align:top;'
            f'white-space:nowrap">{chip}</td>'
            f'<td style="padding:8px 0;font:400 13px {FONT};color:{INK};'
            f'line-height:1.5"><strong>{_e(r["slug"])}</strong><br>'
            f'<span style="color:{MUTED}">{_e(r.get("detail", ""))[:300]}</span>'
            f'</td></tr>')
    return _card(_h("What ran this morning", NAVY)
                 + '<table role="presentation" width="100%" cellpadding="0" '
                   'cellspacing="0">' + "".join(rows) + "</table>")


def _waiting_card():
    cands = [t for t in ledger.load_techniques()
             if t.get("status") == "candidate" and t.get("notes")]
    if not cands:
        return ""
    rows = []
    for t in cands:
        first = (t.get("notes") or "").strip().split("\n")[0]
        first = first.replace("first step:", "").strip()
        rows.append(
            f'<div style="padding:10px 0;border-top:1px solid {LINE}">'
            f'<div style="font:600 14px {FONT};color:{INK}">{_e(t["name"])}</div>'
            f'<div style="font:400 13px {FONT};color:{MUTED};margin-top:3px;'
            f'line-height:1.5">{_e(first)[:260]}</div></div>')
    return _card(
        _h("Waiting on you — these cannot run until someone acts", ORANGE)
        + "".join(rows))


def _blocked_banner(run_log, scout_out):
    details = [r.get("detail", "") for r in (run_log or [])]
    if scout_out and not scout_out.get("ok"):
        details.append(scout_out.get("detail", ""))
    msgs = []
    if any("credit balance is too low" in d for d in details):
        msgs.append("Anthropic API credits are exhausted — no new pages can be "
                    "written and the scout cannot run until the account is topped up.")
    if any("no Anthropic key" in d for d in details):
        msgs.append("No Anthropic API key found (expected in seo/.env).")
    g = ledger.get_state("gsc_last") or {}
    if g and not g.get("ok") and g.get("detail"):
        msgs.append("Search Console: " + str(g["detail"])[:220])
    if not msgs:
        return ""
    items = "".join(
        f'<div style="font:400 13px {FONT};color:#7f1d1d;line-height:1.55;'
        f'padding:3px 0">&bull; {_e(m)}</div>' for m in msgs)
    return (f'<tr><td style="padding:0 0 14px 0">'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            f'style="background:#fef2f2;border:1px solid #fecaca;border-radius:10px">'
            f'<tr><td style="padding:16px 20px">'
            f'<div style="font:700 12px {FONT};letter-spacing:.08em;color:{BAD};'
            f'margin-bottom:8px">BLOCKED</div>{items}</td></tr></table></td></tr>')


def _scout_card(scout_out):
    if not scout_out or not scout_out.get("ok"):
        return ""
    added = scout_out.get("techniques_added") or []
    if not added:
        return ""
    rows = []
    for slug in added:
        t = ledger.get(slug)
        if not t:
            continue
        rows.append(
            f'<div style="padding:10px 0;border-top:1px solid {LINE}">'
            f'<div style="font:600 14px {FONT};color:{INK}">{_e(t["name"])}</div>'
            f'<div style="font:400 13px {FONT};color:{MUTED};margin-top:3px;'
            f'line-height:1.5">{_e((t.get("hypothesis") or "")[:220])}</div></div>')
    if not rows:
        return ""
    return _card(
        _h("Scout proposed — candidates only, not running", NAVY)
        + "".join(rows)
        + f'<div style="font:400 12px {FONT};color:{MUTED};margin-top:10px">'
          f'Nothing here changes the site until it is switched on deliberately.</div>')


def _footer():
    return (f'<tr><td style="padding:6px 4px 0 4px;font:400 12px {FONT};'
            f'color:{MUTED};line-height:1.6">'
            f'NEMO Seamless Gutter growth engine · runs 06:00 ET daily<br>'
            f'Detail: <code style="font-size:11px">growth_daily.py status</code> · '
            f'logs: <code style="font-size:11px">/var/log/nemo-growth.log</code>'
            f'</td></tr>')


def build_html(run_log=None, review_out=None, scout_out=None):
    techs = ledger.load_techniques()
    active = sum(1 for t in techs if t.get("status") == "active")

    sections = [
        _blocked_banner(run_log, scout_out),
        _goal_card(),
        _leads_card(),
        _traffic_card(),
        _rank_card(),
        _discovered_card(),
        _ran_card(run_log),
        _scout_card(scout_out),
        _waiting_card(),
    ]

    decisions = ""
    if review_out and review_out.get("actions"):
        items = "".join(
            f'<div style="font:400 13px {FONT};color:{INK};padding:4px 0;'
            f'line-height:1.5">&bull; {_e(a)}</div>'
            for a in review_out["actions"])
        decisions = _card(_h("Review decisions today", NAVY) + items)

    body = "".join(s for s in sections if s) + decisions + _footer()

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NEMO growth report</title></head>
<body style="margin:0;padding:0;background:{BG}">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
       style="background:{BG};padding:20px 12px">
<tr><td align="center">
<table role="presentation" width="600" cellpadding="0" cellspacing="0"
       style="max-width:600px;width:100%">

  <tr><td style="background:{NAVY};border-radius:10px;padding:20px 22px">
    <div style="font:700 17px {FONT};color:#ffffff;letter-spacing:-.01em">
      NEMO Seamless Gutter</div>
    <div style="font:400 13px {FONT};color:#c7d0f0;margin-top:3px">
      Daily growth report &middot; {ledger.today()}</div>
  </td></tr>
  <tr><td style="height:14px;font-size:0;line-height:0">&nbsp;</td></tr>

  {body}

  <tr><td style="padding:14px 4px 0 4px;font:400 12px {FONT};color:{MUTED}">
    Ledger: {len(techs)} techniques &middot; {active} active
  </td></tr>

</table>
</td></tr></table>
</body></html>"""

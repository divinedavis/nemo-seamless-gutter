#!/usr/bin/env python3
"""Print the NEMO numbers shown on the divinedavis.com portfolio card, as JSON.

The portfolio host cannot reach this droplet's data — bookings live in SQLite
here, calls come from the ElevenLabs API with a key that stays here, and the
access log never leaves the box. So the portfolio's nightly stats job SSHes in
and runs this, and gets back only the handful of already-aggregated, already
public-safe figures the card displays. No visitor, caller or customer detail
crosses the wire.

Keys are prefixed `nemo_` and match the data-stat attributes in
portfolio.html. Values are preformatted strings, because the page just drops
them into the cell.

Every source is wrapped: a revoked ElevenLabs key or an unreachable Search
Console must not cost the whole card. A missing key is simply absent from the
output, and the portfolio keeps the last-known value already in its HTML.
"""
import json
import sys

from . import audience


def commas(n):
    return f"{int(n):,}"


def traffic():
    t = audience.totals()
    if not t["visitors"]:
        return {}
    pct = t["returning_pct"]
    return {
        "nemo_visitors": commas(t["visitors"]),
        "nemo_returning": f"{commas(t['returning'])} ({pct}%)",
        "nemo_pageviews": commas(t["pageviews"]),
        "nemo_since": t["since"] or "",
    }


def demand():
    """Calls into the AI assistant and jobs booked on the site.

    Calls lead: the assistant is not allowed to book anything, so bookings
    measure the one path a caller is never taken down.
    """
    out = {}
    try:
        from . import calls
        status = {}
        rows = calls.fetch(status=status)
        if status.get("ok"):
            out["nemo_ai_calls"] = commas(calls.call_totals(rows, refresh=False)
                                          ["ai_calls_all_time"])
    except Exception as exc:
        print(f"calls unavailable: {exc}", file=sys.stderr)
    try:
        from . import metrics
        out["nemo_bookings"] = commas(metrics.lead_totals()["bookings_all_time"])
    except Exception as exc:
        print(f"bookings unavailable: {exc}", file=sys.stderr)
    return out


def search():
    try:
        from . import gsc
        if not gsc.available():
            return {}
        t = gsc.totals()
    except Exception as exc:
        print(f"search console unavailable: {exc}", file=sys.stderr)
        return {}
    return {
        "nemo_gsc_impressions": commas(t["impressions"]),
        "nemo_gsc_clicks": commas(t["clicks"]),
        "nemo_gsc_position": f"{t['position']:.0f}",
    }


def collect():
    stats = {}
    stats.update(traffic())
    stats.update(demand())
    stats.update(search())
    return stats


if __name__ == "__main__":
    print(json.dumps(collect(), indent=2))

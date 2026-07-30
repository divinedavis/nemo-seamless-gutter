#!/usr/bin/env python3
"""Calls into the AI phone assistant — the top-of-funnel number.

Bookings are the wrong thing to watch on this site. The assistant is forbidden
from booking anything (it takes a number and a callback window; Eric sets the
time himself), and most people who ring a contractor never touch the booking
form at all. So "did the phone ring?" is the honest demand signal, and a call
that ended before the caller left a message still counts as a call — it just
didn't become a lead. Counting only the `leads` rows hides exactly the calls
worth knowing about: the ones that hung up.

Source of truth is ElevenLabs' conversation history for the agent, not the
`leads` table, for that reason.

Two things this module is careful about:

  Owner calls are excluded. Every call so far has come from the developer's own
  number while wiring the thing up; counting those would report demand that
  does not exist. The exclusion list is the same `owner_phones` the booking and
  lead counters already use, so one number added to the ledger's state file
  drops out of every metric at once.

  The API is not re-read for calls it has already described. The list endpoint
  does not carry the caller's number, so identifying a call costs a second
  request — fine once per call, wasteful on every dashboard load. Numbers are
  cached on disk by conversation id and only unseen calls are fetched, which
  keeps a page refresh at one request no matter how long the history gets.
"""
import datetime
import json
import os
import subprocess
import urllib.error
import urllib.parse
import urllib.request

from . import ledger, metrics

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://api.elevenlabs.io/v1/convai"
AGENT_ID_FILE = os.path.join(HERE, "..", "agent", "agent.id")
# agent/ is a development directory and is not deployed to the droplet, so the
# id cannot come only from that file — reading it there yields None and the
# request 404s with a URL that looks perfectly valid. The id is not a secret
# (it is committed at agent/agent.id); NEMO_AGENT_ID overrides it.
DEFAULT_AGENT_ID = "agent_0401ky4xrfybew98htzahkv1rs8e"
CACHE = os.environ.get("NEMO_CALLS_CACHE", os.path.join(HERE, "calls_cache.json"))

# The business day is Eastern — a 9pm call is that evening's call, not
# tomorrow's, which is what UTC would make of it. Same convention as the
# booking counters in metrics.py. A fixed offset would drift by an hour every
# November, so the zone is named and only falls back to EDT if tzdata is absent.
try:
    from zoneinfo import ZoneInfo
    BUSINESS_TZ = ZoneInfo("America/New_York")
except Exception:
    BUSINESS_TZ = datetime.timezone(datetime.timedelta(hours=-4))

# A refresh should cost one list request plus a lookup for genuinely new calls.
# The cap is a backstop against a cold cache on a busy day turning one page
# load into hundreds of requests; anything beyond it is picked up next refresh.
MAX_LOOKUPS_PER_REFRESH = 40
TIMEOUT = 20


def load_key():
    v = os.environ.get("ELEVENLABS_API_KEY") or os.environ.get("XI_API_KEY")
    if v:
        return v.strip()
    for p in (os.path.join(HERE, ".elevenlabs_key"),
              os.path.join(HERE, "..", "agent", ".elevenlabs_key")):
        p = os.path.abspath(p)
        try:
            with open(p) as f:
                k = f.read().strip()
            if k:
                return k
        except Exception:
            pass
    try:
        return subprocess.check_output(
            ["security", "find-generic-password", "-s", "nemo-elevenlabs", "-w"],
            stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return None


def agent_id():
    v = os.environ.get("NEMO_AGENT_ID")
    if v:
        return v.strip()
    try:
        with open(os.path.abspath(AGENT_ID_FILE)) as f:
            v = f.read().strip()
        if v:
            return v
    except Exception:
        pass
    return DEFAULT_AGENT_ID


def _get(path, key, params=None):
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"xi-api-key": key})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.load(r)


def _read_cache():
    try:
        with open(CACHE) as f:
            c = json.load(f)
        if isinstance(c, dict) and isinstance(c.get("calls"), dict):
            return c
    except Exception:
        pass
    return {"calls": {}}


def _write_cache(cache):
    tmp = CACHE + ".tmp"
    try:
        with open(tmp, "w") as f:
            json.dump(cache, f)
        os.replace(tmp, CACHE)
    except Exception:
        try:
            os.unlink(tmp)
        except Exception:
            pass


def _day(ts):
    return datetime.datetime.fromtimestamp(ts, BUSINESS_TZ).date().isoformat()


def fetch(key=None, aid=None, refresh=True, status=None):
    """Every call the agent has taken. [{id, ts, day, phone, secs, ...}], oldest first.

    Returns whatever the cache holds if the API can't be reached, so a dead key
    or a network blip degrades the dashboard to "no new calls" rather than to
    an error page. `refresh=False` reads the cache only.

    Pass a dict as `status` to find out which of those happened. Silence here
    is dangerous in one specific way: a revoked key and a genuinely quiet phone
    both produce zero, and only one of them is good news. Callers that display
    the number are expected to check.
    """
    st = status if isinstance(status, dict) else {}
    st.setdefault("ok", False)
    st.setdefault("error", None)

    cache = _read_cache()
    known = cache["calls"]
    if not refresh:
        st["ok"] = True
        st["stale"] = True
        return _rows(known)

    key = key or load_key()
    aid = aid or agent_id()
    if not key or not aid:
        st["error"] = "no ElevenLabs API key" if not key else "no agent id"
        return _rows(known)

    listing, cursor, pages = [], None, 0
    try:
        while pages < 20:
            params = {"agent_id": aid, "page_size": 100}
            if cursor:
                params["cursor"] = cursor
            d = _get("/conversations", key, params)
            listing.extend(d.get("conversations") or [])
            cursor = d.get("next_cursor")
            pages += 1
            if not d.get("has_more") or not cursor:
                break
    except Exception as e:
        st["error"] = f"{type(e).__name__}: {e}"
        return _rows(known)

    looked_up = 0
    for c in listing:
        cid = c.get("conversation_id")
        if not cid:
            continue
        row = known.get(cid)
        ts = c.get("start_time_unix_secs")
        if row is None:
            # The caller's number lives on the conversation detail, not the
            # list. Without it there is no way to tell the owner's testing from
            # a customer, so an unidentified call is fetched — or, past the cap,
            # left out entirely rather than counted as a stranger.
            if looked_up >= MAX_LOOKUPS_PER_REFRESH:
                continue
            looked_up += 1
            try:
                det = _get("/conversations/" + cid, key)
            except Exception:
                continue
            pc = (det.get("metadata") or {}).get("phone_call") or {}
            row = {"ts": ts,
                   "phone": metrics._digits(pc.get("external_number"))[-10:],
                   "direction": pc.get("direction") or det.get("direction") or "inbound"}
        row["secs"] = c.get("call_duration_secs") or 0
        row["messages"] = c.get("message_count") or 0
        row["status"] = c.get("status")
        if ts:
            row["ts"] = ts
        known[cid] = row

    _write_cache(cache)
    st["ok"] = True
    st["stale"] = False
    st["pending_lookups"] = max(0, len(listing) - len(known))
    return _rows(known)


def _rows(known):
    out = []
    for cid, r in known.items():
        ts = r.get("ts")
        if not ts:
            continue
        out.append({"id": cid, "ts": ts, "day": _day(ts),
                    "phone": r.get("phone") or "",
                    "direction": r.get("direction") or "inbound",
                    "secs": r.get("secs") or 0,
                    "messages": r.get("messages") or 0,
                    "status": r.get("status")})
    out.sort(key=lambda r: r["ts"])
    return out


def is_own_call(row, phones=None):
    """True if this is our own testing rather than somebody ringing the business."""
    phones = metrics.owner_phones() if phones is None else phones
    d = (row.get("phone") or "")[-10:]
    if not d:
        return False
    if d in phones:
        return True
    return len(d) == 10 and d[3:6] == "555"


def _split(rows=None, refresh=True):
    rows = fetch(refresh=refresh) if rows is None else rows
    phones = metrics.owner_phones()
    real, own = [], []
    for r in rows:
        # Outbound calls are the business ringing out, not demand coming in.
        if r.get("direction") == "outbound":
            continue
        (own if is_own_call(r, phones) else real).append(r)
    return real, own


def call_totals(rows=None, refresh=True):
    """All-time call counts, shaped like metrics.lead_totals()."""
    real, own = _split(rows, refresh)
    return {"ai_calls_all_time": len(real),
            "own_calls_excluded": len(own)}


def calls_by_day(dates, rows=None, refresh=True):
    """{date: {'ai_calls': n}} for the given Eastern dates."""
    real, _own = _split(rows, refresh)
    out = {d: {"ai_calls": 0} for d in dates}
    for r in real:
        if r["day"] in out:
            out[r["day"]]["ai_calls"] += 1
    return out


def record(dates=None):
    """Write call counts into the ledger, so history survives cache loss."""
    rows = fetch()
    totals = call_totals(rows, refresh=False)
    today = ledger.today()
    if dates:
        for d, m in calls_by_day(dates, rows, refresh=False).items():
            ledger.record_result(d, "__site__", "ai_calls", m["ai_calls"])
    for k, v in totals.items():
        ledger.record_result(today, "__site__", k, v)
    return totals


if __name__ == "__main__":
    st = {}
    rows = fetch(status=st)
    real, own = _split(rows, refresh=False)
    print(json.dumps({"status": st,
                      "all": len(rows), "counted": len(real), "own_excluded": len(own),
                      "by_day": {d: n["ai_calls"] for d, n in
                                 sorted(calls_by_day(sorted({r["day"] for r in rows}),
                                                     rows, refresh=False).items())}},
                     indent=2))

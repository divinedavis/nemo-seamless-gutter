#!/usr/bin/env python3
"""Who has been here, ever — and who came back.

metrics.collect() answers "how many people yesterday". It cannot answer "how
many different people since launch", because nginx rotates the access log away
after a few days and a sum of daily uniques counts the same person once per
visit. So each day's surviving visitors are folded into a roster here, and the
roster is what all-time figures are read from.

The visitor id metrics.py works with is `ip|user-agent` — personal data. It is
never stored: what lands in audience.json is a SHA-256 of that string with a
random per-install salt, truncated to 16 hex chars. That is enough to recognise
the same browser tomorrow and useless for identifying anybody, and it means the
file can be lost without leaking anything. Losing it does cost the history,
which is why the droplet copy is the source of truth and the repo ignores it.

The usual IP+UA caveats apply and are worth stating wherever these numbers are
published: a household behind one NAT reads as one person, and the same person
on wifi and then cellular reads as two. Both biases are steady, so the shape of
the trend is trustworthy even where the absolute count is soft.
"""
import datetime
import hashlib
import json
import os
import secrets
import threading

from . import metrics

HERE = os.path.dirname(os.path.abspath(__file__))
ROSTER_PATH = os.environ.get("NEMO_AUDIENCE_PATH",
                             os.path.join(HERE, "audience.json"))

_lock = threading.Lock()


def _blank():
    return {"salt": secrets.token_hex(16), "since": None, "people": {}}


def load(path=None):
    path = path or ROSTER_PATH
    try:
        with open(path) as f:
            data = json.load(f)
    except (OSError, ValueError):
        return _blank()
    if not isinstance(data, dict) or not data.get("salt"):
        return _blank()
    data.setdefault("people", {})
    data.setdefault("since", None)
    for p in data["people"].values():
        _normalise(p)
    return data


def _normalise(p):
    """Upgrade a person written by an earlier shape of this file.

    `days` was once a plain count. The individual days are gone, but first and
    last are not, so seeding those keeps the one thing derived from the count —
    whether this person ever came back — true.
    """
    if isinstance(p.get("days"), dict):
        return p
    n = p.get("days")
    p["days"] = {p.get("first", ""): 1}
    if isinstance(n, int) and n > 1:
        p["days"][p.get("last", "")] = 1
    return p


def save(data, path=None):
    path = path or ROSTER_PATH
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f)
    os.replace(tmp, path)
    os.chmod(path, 0o600)


def fingerprint(vid, salt):
    return hashlib.sha256((salt + "|" + vid).encode("utf-8")).hexdigest()[:16]


def merge(roster, data=None):
    """Fold {date: {visitor_id: pageviews}} into the roster. Returns it.

    Re-running a day is safe: a day already recorded for a person updates that
    day's view count instead of counting the person twice.
    """
    data = load() if data is None else data
    salt, people = data["salt"], data["people"]
    for day in sorted(roster):
        for vid, views in roster[day].items():
            fp = fingerprint(vid, salt)
            p = _normalise(people.setdefault(
                fp, {"first": day, "last": day, "days": {}}))
            p["days"][day] = views
            if day < p["first"]:
                p["first"] = day
            if day > p["last"]:
                p["last"] = day
        # Only a day that actually had somebody moves the start date. A day
        # with no visitors is indistinguishable from a day whose log had
        # already rotated away, and dating the record from a day we may never
        # have measured would overstate how long these numbers have run.
        if roster[day] and (data["since"] is None or day < data["since"]):
            data["since"] = day
    return data


def totals(data=None):
    """All-time audience figures.

    `returning` counts people seen on more than one day — a second page view in
    the same session is not somebody coming back.
    """
    data = load() if data is None else data
    people = data["people"]
    visitors = len(people)
    returning = sum(1 for p in people.values() if len(p.get("days") or {}) > 1)
    views = sum(sum((p.get("days") or {}).values()) for p in people.values())
    return {
        "since": data.get("since"),
        "visitors": visitors,
        "returning": returning,
        "returning_pct": round(returning / visitors * 100) if visitors else 0,
        "pageviews": views,
    }


def merge_and_save(roster, path=None):
    """Fold a roster the caller already collected into the stored one.

    This is the hook metrics.collect_and_record() uses, so the daily run pays
    for exactly one pass over the log.
    """
    with _lock:
        data = merge(roster, load(path))
        save(data, path)
    return totals(data)


def update(days=1, end=None, log_path=None, path=None):
    """Read the log for the given days and fold them into the roster.

    Standalone entry point, for backfilling whatever days the log still holds.
    The daily run goes through merge_and_save() instead.
    """
    roster = {}
    metrics.collect(days=days, end=end, log_path=log_path, roster=roster)
    return merge_and_save(roster, path)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=1,
                    help="how many complete days back to read from the log")
    ap.add_argument("--end", help="last day to read (YYYY-MM-DD), default yesterday")
    args = ap.parse_args()
    end = (datetime.date.fromisoformat(args.end) if args.end else None)
    print(json.dumps(update(days=args.days, end=end), indent=2))

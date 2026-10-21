#!/usr/bin/env python3
"""Is the repository's copy of the engine's state current?

Every alarm this system has runs on the droplet: Eric's 06:00 report, the
developer's Friday copy, the 11:00 `growth_daily.py watchdog`, the log. When
the droplet stops, all of them stop with it. `deploy/cron-nemo-growth` predicts
that in its own comment — "a failure of cron itself surfaces never, because the
Friday mail is also a cron job" — and from 2026-10-13 it happened: nine
consecutive mornings with no publish commit, every droplet-side alarm silent,
and the only notice anybody got was the cloud review agent writing it down each
morning in a journal that nobody reads at 07:00.

This check runs in GitHub Actions instead, which is the one place outside the
droplet that can see whether the morning's state arrived — and the one place a
change in this repository takes effect without a deploy. It cannot say why a
publish failed. It reads `growth/snapshot.json`'s own date, says how old it is,
and exits non-zero so that the failure lands somewhere a human looks.

It deliberately duplicates no reasoning: the diagnostic that tells the three
causes of a missing publish apart is the watchdog's, imported rather than
copied, so the pair cannot drift the way the alert and the runbook already did
once on 2026-10-18.
"""
import datetime
import json
import os
import sys

# Defined here rather than imported from `snapshot` so that this module stays
# importable by itself: `growth.snapshot` pulls in the whole engine, and the
# one job of this file is to be the check that still works when the engine does
# not. Both resolve to the copy of the file sitting next to this one, which is
# the droplet's working copy on the droplet and the checkout's in CI.
HERE = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT_PATH = os.path.join(HERE, "snapshot.json")


def stale_days(snapshot_date, today):
    """Whole days between the snapshot's own date and `today`, or None.

    None means "cannot tell", which this module treats as an alarm rather than
    as an all-clear: an unreadable date is the state a frozen file is in.
    """
    try:
        return (today - datetime.date.fromisoformat(snapshot_date)).days
    except (TypeError, ValueError):
        return None


def check(path=None, today=None):
    """(ok, message) for the state file at `path`.

    Healthy is stale_days == 0: the 06:00 America/New_York run publishes hours
    before this check's 13:17 UTC schedule, year round, in either direction of
    daylight saving. A 1 means this morning's state never arrived, which is the
    same bar `cmd_watchdog` uses — one missed morning is already the alarm,
    because the review agent spends a missed morning reading stale numbers as
    though they were today's.

    A negative value is not an error worth its own branch: a snapshot dated
    ahead of this runner's clock is still a snapshot that arrived.
    """
    path = SNAPSHOT_PATH if path is None else path
    today = datetime.date.today() if today is None else today

    try:
        with open(path) as f:
            snap_date = json.load(f).get("date")
    except FileNotFoundError:
        return False, (f"{path} does not exist. The droplet has never "
                       f"published its state to this repository.")
    except Exception as e:
        return False, (f"{path} cannot be read ({e}). The daily review agent "
                       f"reads this file and nothing else from the droplet.")

    days = stale_days(snap_date, today)
    if days is None:
        return False, (f"{path} has no readable date (found {snap_date!r}), so "
                       f"nothing here can tell whether it is this morning's.")
    if days <= 0:
        return True, f"ok — growth/snapshot.json is dated {snap_date}"

    morning = "morning" if days == 1 else "consecutive mornings"
    return False, (
        f"growth/snapshot.json is {days} day(s) stale — it is dated "
        f"{snap_date} and today is {today.isoformat()}. {days} {morning} have "
        f"produced no publish commit, so the daily review agent has been "
        f"reading {snap_date}'s numbers as its view of the business. "
        + _diagnostic())


def _diagnostic():
    """The watchdog's three-cause diagnostic, or a pointer if it won't load.

    Imported late and defensively on purpose. The text belongs to
    `growth_daily`, which imports the whole engine; if that import is what is
    broken, this check still has to deliver the one fact it exists to deliver.
    """
    try:
        sys.path.insert(0, os.path.dirname(HERE))
        import growth_daily
        return growth_daily._UNPUBLISHED_MORNING_DIAGNOSTIC
    except Exception as e:
        return (f"(The three-cause diagnostic could not be loaded from "
                f"growth_daily: {e}. It is in that file as "
                f"_UNPUBLISHED_MORNING_DIAGNOSTIC, and in growth/README.md "
                f"under \"When no publish commit arrives\".)")


def main(argv=None):
    ok, message = check()
    # GitHub renders ::error:: in the job's annotation list and on the run
    # summary, which is what makes a scheduled failure readable without
    # opening the log.
    prefix = "::error::" if os.environ.get("GITHUB_ACTIONS") else ""
    print(f"{prefix}state-freshness: {message}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

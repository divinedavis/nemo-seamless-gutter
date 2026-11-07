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

# How many days of nginx archives to assume still exist, for the one sentence
# below that says how much traffic history is already past saving.
#
# It is an estimate, not a reading: `growth.metrics.rotations()` deliberately
# enumerates whatever logrotate actually kept rather than trusting a number,
# and nothing in this repository can see the droplet's disk. 14 is the
# packaged Debian/Ubuntu policy (daily, rotate 14). It is stated as an estimate
# wherever it is printed, and `ls -la /var/log/nginx/nemo-access.log*` settles
# it in ten seconds. Wrong in the safe direction: if the droplet keeps more,
# the alarm has overstated the loss and understated the window, which costs
# nobody anything. If it keeps fewer, the deadline has already passed and the
# listing is the only thing that would have said so.
ASSUMED_LOG_RETENTION_DAYS = 14


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
        + perishable(snap_date, today) + " " + _diagnostic())


def perishable(snap_date, today, retention_days=ASSUMED_LOG_RETENTION_DAYS):
    """What the outage has already destroyed, and what the next day costs.

    The rest of this alarm says the state file is stale, which is recoverable
    at any time: Search Console backfills about sixteen months, so rank history
    survives any outage this project is likely to have. Traffic history does
    not. `metrics.collect_and_record` records yesterday only and the series is
    accumulated rather than recomputed, so every missed morning is a hole that
    stays a hole, and the only thing that fills one is an nginx archive that
    logrotate has not yet deleted.

    That makes this the one fact in the alarm with a deadline attached, and it
    was not in it: for twenty-five mornings the delivered message said "N days
    stale" and the perishable half lived only in a 2.9 MB journal and a
    hand-written ACTION.md. A number that expires belongs in the channel that
    is actually delivered.

    A snapshot dated D holds data through D-1, because the D run records
    yesterday — so the first missing day is D itself, not D+1. Getting that
    wrong undercounts the loss by a day, which three entries did.
    """
    first_missing = datetime.date.fromisoformat(snap_date)
    last_missing = today - datetime.timedelta(days=1)
    if last_missing < first_missing:
        return ""
    oldest_recoverable = today - datetime.timedelta(days=retention_days)
    lost = max(0, (min(oldest_recoverable, today) - first_missing).days)
    recoverable = (last_missing - max(first_missing, oldest_recoverable)).days + 1
    recoverable = max(0, recoverable)
    # The last missing morning stays readable until it ages out, so this is the
    # date after which no part of *today's* hole can be recovered at all. Days
    # that go missing later carry their own clocks; this is not the date the
    # engine stops mattering.
    expires = last_missing + datetime.timedelta(days=retention_days)
    span = (f"{first_missing.isoformat()} to {last_missing.isoformat()}")

    out = [f"Traffic history is not merely frozen, it is being deleted. "
           f"{(last_missing - first_missing).days + 1} mornings of nginx "
           f"traffic data are missing ({span})."]
    if lost:
        out.append(f"On a ~{retention_days}-day log-retention estimate about "
                   f"{lost} of them are already past recovery, {recoverable} "
                   f"are still recoverable today, and one more expires every "
                   f"day.")
    else:
        out.append(f"On a ~{retention_days}-day log-retention estimate all "
                   f"{recoverable} are still recoverable today, and they "
                   f"start expiring one per day from "
                   f"{(first_missing + datetime.timedelta(days=retention_days)).isoformat()}.")
    if lost:
        # The sentence this replaces — "after <expires> none of this hole can
        # be recovered" — was true as written and misleading as read. `expires`
        # is the newest missing morning plus the window, so it advances one day
        # for every day the outage continues: on 2026-11-06 it printed
        # 2026-11-19, on 2026-11-07 2026-11-20, and on 2027-01-01 it would
        # print 2027-01-14. A date that recedes as fast as you approach it
        # reads as a fortnight of slack and is the opposite of one. Past the
        # retention window `recoverable` is pinned at `retention_days` too, so
        # "14 are still recoverable" has been constant since the window closed
        # and reads reassuringly static. What is actually true, and what does
        # not recede, is per morning: one named day dies every day, and waiting
        # changes which mornings come back, never how many.
        out.append(f"There is no single cutoff to plan around. "
                   f"{expires.isoformat()} is when the newest missing morning "
                   f"ages out, and that date moves a day later for every day "
                   f"the outage continues, so it is not slack. The deadline is "
                   f"per morning: {oldest_recoverable.isoformat()} is the "
                   f"oldest still readable and is the next to be destroyed, "
                   f"and past the retention window waiting no longer changes "
                   f"how many mornings a backfill returns "
                   f"({recoverable}, capped by the window) — only which ones.")
    else:
        out.append(f"After {expires.isoformat()} none of this hole can be "
                   f"recovered by anything.")
    out.append(f"Recover what is left with "
                f"`growth_daily.py measure --days {(today - first_missing).days}` "
                f"on the droplet, and read the real retention off "
                f"`ls -la /var/log/nginx/nemo-access.log*` first — the "
                f"{retention_days} days above is the packaged default, not a "
                f"measurement. Rank history is not at risk; Search Console "
                f"backfills it.")
    return " ".join(out)


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

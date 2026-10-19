#!/usr/bin/env python3
"""NEMO Seamless Gutter growth engine — daily driver.

One cron runs this on the droplet at 06:00 America/New_York:

    growth_daily.py daily --email eric@nemoseamlessgutter.com

which is: measure yesterday → judge what's running → build today's page →
tell search engines → scout for new techniques → report.

Commands:
  measure   pull yesterday's traffic and leads into the ledger
  review    judge active techniques; retire the ones that aren't earning it
  build     run every ACTIVE technique (this is what writes pages)
  scout     research and propose new techniques (proposals only, never activates)
  report    print / email the growth report
  daily     measure → review → build → scout → report
  status    print the ledger and the scoreboard
  goal      print just the goal line and exit non-zero until it's met

Every command takes --dry-run, which makes the whole thing read-only, so it is
safe to run by hand on the server while Eric's site is serving traffic.
"""
import argparse
import json
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from growth import (email_report, gsc, indexstatus, keywords, ledger,  # noqa: E402
                    metrics, report, review, scout, seed, snapshot,
                    techniques)

DEFAULT_DOCROOT = os.environ.get("WEB_ROOT", "/var/www/nemo-seamless-gutter")

# The credentials this needs already live in two .env files on the droplet:
# the Anthropic key in seo/.env, and the proven-working SMTP settings in
# server/.env. They are read here rather than shell-sourced from cron, because
# server/.env contains unquoted values with spaces (OWNER_NAME) that a shell
# `.` would try to execute.
ENV_FILES = ("seo/.env", "server/.env")


def load_env(docroot):
    for rel in ENV_FILES:
        path = os.path.join(docroot, rel)
        if not os.path.exists(path):
            continue
        try:
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip('"').strip("'")
                    # Never let a file override something set explicitly in the
                    # environment — that is how a manual run overrides config.
                    os.environ.setdefault(k, v)
        except Exception as e:
            print(f"  warning: could not read {rel}: {e}", flush=True)


def log(msg):
    print(msg, flush=True)


# ----------------------------------------------------------------- measure

def cmd_measure(args):
    log("measure:")
    seed.run()          # so a standalone `measure` has a universe to score against
    try:
        data, totals = metrics.collect_and_record(days=args.days)
    except Exception as e:
        traceback.print_exc()
        log(f"  measurement failed: {e}")
        return {}
    for d, m in sorted(data.items()):
        log(f"  {d}  {m['visitors']} visitors "
            f"({m['organic_visitors']} organic, {m['local_visitors']} maps) · "
            f"{m['bookings']} bookings, {m['phone_leads']} phone leads "
            f"· {m['bot_hits']} bot hits ignored")
    log(f"  all time: {totals.get('bookings_all_time', 0)} bookings, "
        f"{totals.get('phone_leads_all_time', 0)} phone leads")
    kws, changed = keywords.check_coverage(args.docroot)

    # Rank data. This is what turns the goal from a proxy into a measurement,
    # so its absence is reported rather than passed over in silence.
    g = gsc.sync()
    if not g.get("connected"):
        log("  gsc: NOT CONNECTED — the >50% goal stays unmeasured "
            "(coverage below is only a proxy)")
    elif not g.get("ok"):
        log(f"  gsc: FAILED — {g.get('detail', '')[:160]}")

    # Rank says where a page sits when it is shown. This says whether Google
    # kept it at all — which is the question rank cannot answer for a page
    # earning nothing, because "never indexed" and "indexed, nobody searched"
    # look identical from here and need opposite responses.
    ix = indexstatus.summary(indexstatus.run(dry_run=args.dry_run))
    if not ix.get("measured"):
        log(f"  indexing: not measured ({(ix.get('detail') or '')[:120]})")
    else:
        log(f"  indexing: {ix['indexed']}/{ix['inspected']} indexed "
            f"({ix['accept_pct']}%), {ix['unknown_to_google']} never seen by Google")

    s = keywords.summary()
    # Record the size of the tracked universe as a series. share_pct is a
    # fraction of it, so a day that adopts new queries moves the percentage
    # without any ranking having changed — and a jump that came from moving
    # the measuring stick must never be reported as progress.
    ledger.record_result(ledger.today(), "__site__", "tracked_queries", s["total"])
    if s["share_pct"] is not None:
        log(f"  goal: {s['share_pct']}% of {s['total']} tracked queries in the "
            f"top {keywords.TOP_N} (target 50%)")
    log(f"  keywords: {s['covered']}/{s['total']} covered ({s['coverage_pct']}%), "
        f"{changed} changed today")
    return data


# ------------------------------------------------------------------ review

def cmd_review(args):
    log("review:")
    out = review.run(apply=not args.dry_run)
    for r in out["evaluated"]:
        if r["action"] == "skip":
            continue
        log(f"  [{r['action']:<6}] {r['slug']:<16} {r['why']}")
    for a in out["actions"]:
        log(f"  {a}")
    if not out["actions"]:
        log("  no changes")
    return out


# ------------------------------------------------------------------- build

def cmd_build(args):
    log("build:")
    seed.run()
    # Score coverage before deciding what to build, so the build queue reflects
    # the site as it stands rather than an empty or stale picture.
    keywords.check_coverage(args.docroot)
    ctx = techniques.Context(args.docroot, dry_run=args.dry_run, log=log)
    active = {t["slug"] for t in ledger.active()}
    run_log = []
    for slug in techniques.ORDER:
        if slug not in active:
            log(f"  skip {slug} (not active in the ledger)")
            continue
        fn = techniques.REGISTRY.get(slug)
        if not fn:
            log(f"  skip {slug} (no implementation)")
            continue
        try:
            res = fn(ctx)
        except Exception as e:
            traceback.print_exc()
            res = {"ok": False, "detail": f"crashed: {e}"}
        res["slug"] = slug
        run_log.append(res)
        log(f"  [{'ok  ' if res.get('ok') else 'FAIL'}] {slug}: {res.get('detail', '')}")
    ledger.set_state("last_build", {"date": ledger.today(), "log": run_log,
                                    "new": len(ctx.new_urls),
                                    "changed": len(ctx.changed_urls)})
    log(f"  {len(ctx.new_urls)} new URL(s), {len(ctx.changed_urls)} changed")
    return run_log


# ------------------------------------------------------------------- scout

def cmd_scout(args):
    log("scout:")
    return scout.run(dry_run=args.dry_run, docroot=args.docroot)


# ------------------------------------------------------------------ report

def _send(args, to, audience, text, run_log, review_out, scout_out):
    """One recipient, one audience. Kept separate so a failure sending the
    owner's copy cannot stop the developer's copy going out, or vice versa."""
    try:
        html = email_report.build_html(run_log=run_log, review_out=review_out,
                                       scout_out=scout_out, audience=audience)
    except Exception as e:
        log(f"  html report failed for {audience} ({e}); sending plain text")
        html = None
    try:
        report.email(text, to, html=html)
        log(f"  emailed {audience} copy to {to}")
    except Exception as e:
        log(f"  email to {to} failed: {e}")


def cmd_report(args, run_log=None, review_out=None, scout_out=None):
    text = report.build_text(run_log=run_log, review_out=review_out, scout_out=scout_out)
    print(text)
    if args.owner_email and not args.dry_run:
        _send(args, args.owner_email, "owner", text, run_log, review_out, scout_out)
    if args.email and not args.dry_run:
        _send(args, args.email, "internal", text, run_log, review_out, scout_out)
    return text


# ------------------------------------------------------------------- daily

def cmd_daily(args):
    # Each of the four build-side steps is wrapped for the same reason the
    # scout below it is: a raise here used to take the morning's only two
    # outputs — the state snapshot and the report — down with it.
    #
    # Leaving them unwrapped cost 2026-10-13 and 2026-10-14. Something raised
    # ahead of `snapshot.write()`, so no snapshot was written; and because
    # `publish_state.sh` exits 0 printing "nothing changed" when the clone has
    # no diff (growth/publish_state.sh:81-84), no commit appeared either. The
    # cloud review agent, whose only view of this machine is those two files,
    # read 2026-10-12's numbers on two consecutive mornings and had no way to
    # see why. Two blind days is a worse outcome than any of these four steps
    # failing, because a recorded failure is something the next run can act on.
    #
    # So a crash costs its own step and nothing downstream. `engine_entry()`
    # and `report.build_text()` both accept None for all three arguments, and
    # the individual techniques inside `cmd_build` are already wrapped — what
    # is caught here is the pre-loop work (`seed.run`, `keywords.check_coverage`,
    # `techniques.Context`) and `ledger.set_state` after it.
    #
    # Deliberately NOT done here: writing a fresh `last_build` date on a crash.
    # The 11:00 watchdog reads that date to decide whether a morning went
    # missing, so stamping it today would hand the run a clean bill of health
    # and silence the one check that still fires. A failed build leaves
    # `last_build` dated to the last run that finished, which is true, and the
    # crash reaches the reader through `aborted` in the run log instead.
    aborted = []

    def _step(name, fn, default=None):
        try:
            return fn()
        except Exception as e:
            traceback.print_exc()
            log(f"  {name} FAILED — {e}")
            aborted.append({"ok": False, "slug": name,
                            "detail": f"aborted the morning: {e}"})
            return default

    _step("seed", seed.run)
    _step("measure", lambda: cmd_measure(args))
    review_out = _step("review", lambda: cmd_review(args))
    run_log = _step("build", lambda: cmd_build(args))
    # Coverage is re-checked after the build so the report reflects the page
    # written this morning rather than yesterday's picture.
    #
    # Both of these are wrapped because of where they sit: between the build
    # and the only two things anything outside this machine ever reads — the
    # state snapshot and the report. Neither step is load-bearing for either.
    # Coverage has already been scored twice by now (cmd_measure, cmd_build),
    # and the scout only ever proposes candidates; it never activates one.
    #
    # Leaving them unwrapped cost seven days. On 2026-08-21 a deploy moved
    # growth_daily.py without growth/scout.py, so `scout.run()` was called
    # with a `docroot` keyword the deployed version did not accept and raised
    # TypeError here. The run kept writing pages every morning and never wrote
    # snapshot.json or sent the report, which is the one failure shape the
    # watchdog is worst at seeing: last_build is fresh, no technique reports a
    # failure, and the inbox is quiet. A crash here must cost the scout, not
    # the morning's only two outputs.
    try:
        keywords.check_coverage(args.docroot)
    except Exception as e:
        traceback.print_exc()
        log(f"  post-build coverage check failed: {e}")
    try:
        scout_out = cmd_scout(args)
    except Exception as e:
        traceback.print_exc()
        # Same shape scout.run() returns on a handled failure, so the report's
        # BLOCKED section surfaces it instead of the run dying silently.
        scout_out = {"ok": False, "detail": f"crashed: {e}"}
        log(f"  scout crashed: {e}")

    # The aborted steps ride in the run log so the journal entry and the
    # report name them: `engine_entry()` prints every row as ok/FAILED, which
    # is how a crash ahead of this point becomes something the review agent
    # can read rather than a morning of missing numbers.
    if aborted:
        run_log = aborted + list(run_log or [])

    # Publish state for the cloud review agent, which cannot reach this machine.
    if not args.dry_run:
        try:
            snapshot.write(args.docroot)
            snapshot.append_journal(
                snapshot.engine_entry(run_log, review_out, scout_out))
            log("\nsnapshot: wrote growth/snapshot.json and appended growth/JOURNAL.md")
        except Exception as e:
            log(f"\nsnapshot: FAILED — {e}")

    print()
    cmd_report(args, run_log=run_log, review_out=review_out, scout_out=scout_out)
    return 0


# ------------------------------------------------------------------ status

def _snapshot_problems(build_date, stale_days):
    """Alert when the run completed but the state snapshot did not get written.

    `snapshot.write()` is wrapped in a try/except in `cmd_daily` so a failure
    there cannot take down the rest of the morning. That is right for the site
    and wrong for visibility: on 2026-08-21 the write raised, the run carried
    on and published a sitemap, and the only trace was a single
    "snapshot: FAILED" line in /var/log/nemo-growth.log. The review agent spent
    that morning reviewing the previous day's numbers without being told.

    Nothing else here can see it. Every other check reads state the engine
    wrote, so a missing write is invisible to all of them — the engine looks
    healthy precisely because it is healthy everywhere except the one file the
    cloud agent depends on.

    The comparison is against the build rather than against the calendar: a
    build that completed today next to a snapshot that still reads an older
    date is unambiguous and needs no staleness grace. When the engine has not
    run at all, `stale_days` is not 0 and the build check above owns the alarm,
    so this stays quiet rather than reporting the same outage twice.
    """
    try:
        with open(snapshot.SNAPSHOT_PATH) as f:
            snap_date = json.load(f).get("date")
    except FileNotFoundError:
        snap_date = None
    except Exception as e:
        return [f"growth/snapshot.json cannot be read ({e}). The daily review "
                f"agent reads this file and nothing else from this machine."]

    if stale_days != 0 or snap_date == build_date:
        return []
    return [f"Today's run completed the build but growth/snapshot.json still "
            f"reads {snap_date or 'no date'} against a build dated "
            f"{build_date}, so the daily review agent is reviewing stale "
            f"state. Two different causes look identical from here: "
            f"snapshot.write() raised (look for 'snapshot: FAILED' in "
            f"/var/log/nemo-growth.log), or the run died between the build "
            f"and the snapshot and never reached it at all (no such line — "
            f"look for the last Traceback instead). Check which: if "
            f"reports/waiting-on-you.html is also stale the report never ran, "
            f"which means the second."]


# The three causes of a morning with no publish commit, and the greps that
# separate them. Shared by both staleness branches of `cmd_watchdog` below.
#
# Kept deliberately in step with the "When no publish commit arrives" runbook
# in growth/README.md. The two drifted once already: on 2026-10-18 the runbook
# was corrected to say that git's error cannot follow a `publish:` line, and
# the alert — the copy the person reading at 11:00 actually gets — kept the
# repudiated version for another day. If one of the two changes, change both.
_UNPUBLISHED_MORNING_DIAGNOSTIC = (
    "Three causes look identical from out here and need different responses. "
    "`grep publish /var/log/nemo-growth.log | tail -40` splits them, and then "
    "`grep 'snapshot: FAILED' /var/log/nemo-growth.log | tail -5` splits the "
    "first two. "
    "(1) 'publish: nothing changed' that morning AND a 'snapshot: FAILED' "
    "line: the engine ran to its last line and only the snapshot write raised. "
    "Nothing is lost and no backfill is needed; fix what the error says, "
    "usually a full disk or a permissions change. "
    "(2) 'publish: nothing changed' and NO 'snapshot: FAILED': the run raised "
    "before the snapshot block. Find the last Traceback in the log. This is "
    "the case that loses the morning's data. "
    "(3) No 'publish:' line at all: run "
    "`grep -iE 'permission denied|could not read from remote|publickey|host "
    "key|fatal:' /var/log/nemo-growth.log | tail -10`. Error text there means "
    "only the git step broke, the droplet's state is current and nothing is "
    "lost — fix the credential. No error text there means cron, python or the "
    "droplet never got that far, so check `systemctl status cron`, "
    "`df -h /var /root` and whether /etc/cron.d/nemo-growth still exists. "
    "Do not expect git's error to follow a 'publish:' line: publish_state.sh "
    "is `set -euo pipefail` and prints nothing before the push, so a failed "
    "push and a dead deploy key both leave no 'publish:' line at all. "
    "Two shortcuts that do not work: a frozen growth/snapshot.json next to "
    "engine-run journal entries that stop on the same day fits (1) and (2) "
    "equally, because (2) never calls either write; and an arrived report "
    "email only rules out (2), since cmd_report is the last call in cmd_daily "
    "and both (1) and (3) leave it intact."
)


def cmd_watchdog(args):
    """Alert if the engine has stopped running.

    Every other check here reports from inside a run. If cron breaks, python
    fails to start, or the droplet reboots, there is no run and therefore no
    report — and an inbox with nothing in it looks exactly like a quiet week.
    This runs from a separate cron entry so it survives the engine failing.
    """
    import datetime
    last = ledger.get_state("last_build") or {}
    when = last.get("date")
    stale_days = None
    if when:
        try:
            stale_days = (datetime.date.today()
                          - datetime.date.fromisoformat(when)).days
        except Exception:
            pass

    problems = []
    if not when:
        problems.append("The growth engine has never recorded a completed build.")
    elif stale_days == 1:
        # One missed morning is already the alarm, and this entry runs late
        # enough to be sure of it. On a healthy day the 06:00 run writes
        # last_build hours before this 11:00 check, so stale_days is 0; a 1
        # here means the run that was due five hours ago never reached the end
        # of cmd_build. The threshold was >= 2 until 2026-10-13, which gave the
        # failure a free day: on that date the engine produced nothing, the
        # morning's publish commit never appeared, and this check said "ok —
        # last build 2026-10-12" because one day of silence was under the bar.
        # The cost of that free day is specific rather than theoretical — the
        # cloud review agent's only view of this machine is growth/snapshot.json,
        # so a day of it reads yesterday's numbers as though they were today's.
        #
        # The diagnostic goes in the alert rather than in a runbook because the
        # person reading this at 11:00 is the person who has to tell the
        # causes apart, and they need opposite responses.
        #
        # This assumes the check runs after the morning's engine run, which its
        # own cron entry guarantees. Run `growth_daily.py watchdog` by hand
        # before 06:00 and it will report the run it is standing in front of.
        problems.append(
            f"No completed build today — the last one was {when}. This "
            f"morning's 06:00 run did not reach the end of the build. "
            + _UNPUBLISHED_MORNING_DIAGNOSTIC)
    elif stale_days is not None and stale_days >= 2:
        # The same diagnostic, because the reader's problem on day 7 is the
        # problem they had on day 1 — and day 7 is when somebody is actually
        # reading. Until 2026-10-19 this branch said only "The 06:00 cron is
        # not producing runs", which (a) dropped the diagnostic exactly when
        # the outage was long enough for someone to act on it and (b) asserted
        # one of three indistinguishable causes as fact. That is the branch
        # that fires on every morning of a real outage, and the only one that
        # will be mailed once `--email` is restored to the cron entry, so a
        # confidently wrong cause here sends the reader to `systemctl status
        # cron` for a failure that may be a dead deploy key or a full disk.
        problems.append(
            f"No completed build for {stale_days} days — the last one was "
            f"{when}. {stale_days} consecutive mornings have produced no run "
            f"and no publish commit, so the cloud review agent has been "
            f"reading {when}'s numbers that whole time. "
            + _UNPUBLISHED_MORNING_DIAGNOSTIC)

    failed = [r for r in (last.get("log") or []) if not r.get("ok")]
    if failed and stale_days == 0:
        problems.append("Today's run completed but these steps failed: "
                        + "; ".join(f"{r['slug']} — {r.get('detail', '')[:120]}"
                                    for r in failed))
    problems.extend(_snapshot_problems(when, stale_days))

    g = ledger.get_state("gsc_last") or {}
    if g and not g.get("ok"):
        problems.append(f"Search Console sync is failing: "
                        f"{str(g.get('detail', ''))[:160]}")

    if not problems:
        log(f"watchdog: ok — last build {when}")
        return 0

    for p_ in problems:
        log(f"watchdog: {p_}")
    if args.email and not args.dry_run:
        body = ("The NEMO growth engine needs attention.\n\n"
                + "\n\n".join(f"* {p_}" for p_ in problems)
                + "\n\nCheck /var/log/nemo-growth.log on 104.236.120.144.\n")
        try:
            report.email(body, args.email,
                         subject=f"NEMO growth engine needs attention — {ledger.today()}")
            log(f"watchdog: alerted {args.email}")
        except Exception as e:
            log(f"watchdog: alert email failed: {e}")
    return 1


def cmd_status(args):
    techs = ledger.load_techniques()
    s = keywords.summary()
    print(f"LEDGER — {len(techs)} techniques")
    for t in techs:
        v = t.get("verdict") or {}
        mark = "WORKS" if v.get("works") else ("FAILED" if v else "")
        print(f"  {t['id']} [{t['status']:<9}] {t['name']:<38} {mark}")
        if v.get("why"):
            print(f"        {v['why']}")
    print()
    print(f"KEYWORDS — {s['covered']}/{s['total']} covered ({s['coverage_pct']}%)")
    if s["share_pct"] is not None:
        print(f"  top-3 share: {s['share_pct']}%  (goal 50%)")
    else:
        print("  top-3 share: unmeasured (no Search Console)")
    for town, d in sorted(s["by_town"].items()):
        print(f"    {town:<14} {d['covered']}/{d['total']} covered")
    return 0


def cmd_goal(args):
    """Exit 0 once the goal is met, 1 otherwise — so the loop has a real
    terminating condition rather than running forever by default."""
    s = keywords.summary()
    if s["share_pct"] is None:
        print(f"goal UNMEASURED — Search Console not connected. "
              f"coverage proxy {s['coverage_pct']}% of {s['total']} queries")
        return 1
    met = s["share_pct"] >= 50
    print(f"top-3 share {s['share_pct']}% of {s['total']} tracked queries "
          f"(goal 50%) — {'MET' if met else 'not met'}")
    return 0 if met else 1


def cmd_snapshot(args):
    """Write the state snapshot without running anything else — useful for
    checking what the review agent will see."""
    seed.run()
    keywords.check_coverage(args.docroot)
    snap = snapshot.write(args.docroot)
    g = snap["goal"]
    log(f"wrote growth/snapshot.json — goal "
        f"{g['share_pct'] if g['measured'] else 'UNMEASURED'} "
        f"(coverage {g['coverage_pct']}% of {g['tracked_queries']} queries), "
        f"{len(snap['techniques'])} techniques")
    return 0


def main():
    p = argparse.ArgumentParser(description="NEMO growth engine")
    p.add_argument("command", choices=["measure", "review", "build", "scout",
                                       "report", "daily", "status", "goal",
                                       "snapshot", "watchdog"])
    p.add_argument("--docroot", default=DEFAULT_DOCROOT)
    p.add_argument("--days", type=int, default=1,
                   help="how many complete days to measure (default: yesterday)")
    p.add_argument("--email", default=None,
                   help="send the full developer report here")
    p.add_argument("--owner-email", default=None,
                   help="send the business-owner report here — leads, rank and "
                        "what needs him, with none of the engine's internals")
    p.add_argument("--dry-run", action="store_true",
                   help="read-only: measure and judge, but write nothing")
    args = p.parse_args()
    load_env(args.docroot)

    if args.dry_run:
        log("DRY RUN — nothing will be written\n")

    return {
        "measure": lambda: (cmd_measure(args), 0)[1],
        "review": lambda: (cmd_review(args), 0)[1],
        "build": lambda: (cmd_build(args), 0)[1],
        "scout": lambda: (cmd_scout(args), 0)[1],
        "report": lambda: (cmd_report(args), 0)[1],
        "daily": lambda: cmd_daily(args),
        "status": lambda: cmd_status(args),
        "goal": lambda: cmd_goal(args),
        "snapshot": lambda: cmd_snapshot(args),
        "watchdog": lambda: cmd_watchdog(args),
    }[args.command]()


if __name__ == "__main__":
    sys.exit(main())

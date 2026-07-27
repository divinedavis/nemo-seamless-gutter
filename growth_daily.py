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
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from growth import (keywords, ledger, metrics, report,  # noqa: E402
                    review, scout, seed, techniques)

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
    s = keywords.summary()
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
    return scout.run(dry_run=args.dry_run)


# ------------------------------------------------------------------ report

def cmd_report(args, run_log=None, review_out=None, scout_out=None):
    text = report.build_text(run_log=run_log, review_out=review_out, scout_out=scout_out)
    print(text)
    if args.email and not args.dry_run:
        try:
            report.email(text, args.email)
            log(f"\n  emailed to {args.email}")
        except Exception as e:
            log(f"\n  email failed: {e}")
    return text


# ------------------------------------------------------------------- daily

def cmd_daily(args):
    seed.run()
    cmd_measure(args)
    review_out = cmd_review(args)
    run_log = cmd_build(args)
    # Coverage is re-checked after the build so the report reflects the page
    # written this morning rather than yesterday's picture.
    keywords.check_coverage(args.docroot)
    scout_out = cmd_scout(args)
    print()
    cmd_report(args, run_log=run_log, review_out=review_out, scout_out=scout_out)
    return 0


# ------------------------------------------------------------------ status

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


def main():
    p = argparse.ArgumentParser(description="NEMO growth engine")
    p.add_argument("command", choices=["measure", "review", "build", "scout",
                                       "report", "daily", "status", "goal"])
    p.add_argument("--docroot", default=DEFAULT_DOCROOT)
    p.add_argument("--days", type=int, default=1,
                   help="how many complete days to measure (default: yesterday)")
    p.add_argument("--email", default=None, help="send the report here")
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
    }[args.command]()


if __name__ == "__main__":
    sys.exit(main())

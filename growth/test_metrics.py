#!/usr/bin/env python3
"""Tests for the measurement rules that decide what counts as a visit.

Run:  python3 -m growth.test_metrics      (from the site root)

These exist because every rule here was added to stop something being counted
that shouldn't be, and a silent regression would look exactly like growth.
"""
import contextlib
import datetime
import gzip
import os
import shutil
import tempfile
import unittest

from . import ledger
from . import metrics

# ---------------------------------------------------------------- isolation
#
# metrics.hosting_skipper() memoises PTR lookups in ledger state — which lives
# in growth/state.json, is gitignored, and survives between runs. is_hosting()
# consults the resolver a test injects ONLY on a cache miss, so a cached entry
# for a fixture address silently overrides the injected resolver and the test
# asserts against whatever the file happens to hold.
#
# That is reachable, not theoretical. On 2026-11-03 a review-session script that
# called collect() with a null resolver over a log containing 203.0.113.20/.21
# cached "" for both, and two HostingExclusion tests then failed against an
# unmodified repo until the file was deleted. The trigger there was a throwaway
# probe rather than anything the droplet runs, so this is a demonstrated
# fragility and NOT evidence that the droplet's own state.json is poisoned.
# It is worth closing anyway, because scripts/test.sh is the gate in
# .githooks/pre-push, ci.yml, deploy_web.sh, deploy_api.sh and deploy_growth.sh:
# were it ever to happen there, every deploy would refuse to run and the failure
# reads like a measurement bug rather than stale state. CI cannot catch it — a
# fresh clone has no state.json — so it would only ever fire on a long-lived
# checkout, which is to say on the droplet.
#
# Pointing STATE_PATH at a throwaway file for the module's lifetime makes every
# test here read and write its own state and touch the real file never.

_REAL_STATE_PATH = ledger.STATE_PATH
_STATE_DIR = None


def setUpModule():
    global _STATE_DIR
    _STATE_DIR = tempfile.mkdtemp()
    ledger.STATE_PATH = os.path.join(_STATE_DIR, "state.json")


def tearDownModule():
    ledger.STATE_PATH = _REAL_STATE_PATH
    if _STATE_DIR:
        shutil.rmtree(_STATE_DIR, ignore_errors=True)

DAY = "27/Jul/2026:12:00:00 +0000"
DATE = "2026-07-27"
# A day on the beacon side of metrics.PV_START, when a visitor means "ran our
# JavaScript" rather than "fetched HTML convincingly".
PV_DAY = "20/Aug/2026:12:00:00 +0000"
PV_DATE = "2026-08-20"
BROWSER = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 "
           "(KHTML, like Gecko) Version/17.0 Safari/605.1.15")


def line(ip, path, ua=BROWSER, ref="-", status=200, owner=None, day=DAY):
    """One access-log line. owner=None writes the pre-2026-07-28 format."""
    base = (f'{ip} - - [{day}] "GET {path} HTTP/1.1" {status} 500 '
            f'"{ref}" "{ua}"')
    return base + (f' "{owner}"' if owner is not None else "") + "\n"


def visit(ip, owner=None, ua=BROWSER, day=DAY):
    """A page plus its stylesheet — what a real browser does."""
    return (line(ip, "/", ua=ua, owner=owner, day=day)
            + line(ip, "/styles.css", ua=ua, owner=owner, day=day))


def pv(ip, vid="a", p="/", r="", ua=BROWSER, status=204, owner=None, day=PV_DAY):
    """The pageview beacon analytics.js fires once per page load.

    vid=None writes a beacon with no v param — a browser whose cookie AND
    localStorage were blocked.
    """
    q = f"p={p}" if vid is None else f"v={vid}&p={p}"
    if r:
        q += f"&r={r}"
    base = (f'{ip} - - [{day}] "POST /e/pv?{q} HTTP/1.1" {status} 0 '
            f'"-" "{ua}"')
    return base + (f' "{owner}"' if owner is not None else "") + "\n"



def tap(ip, ua=BROWSER, method="POST", status=204, owner=None):
    """The call beacon analytics.js fires when a tel: link is tapped."""
    base = (f'{ip} - - [{DAY}] "{method} /e/call-tap?p=/ HTTP/1.1" {status} 0 '
            f'"-" "{ua}"')
    return base + (f' "{owner}"' if owner is not None else "") + "\n"

class LogParsing(unittest.TestCase):
    def test_old_format_still_parses(self):
        m = metrics.LOG_RE.match(line("198.51.100.1", "/"))
        self.assertIsNotNone(m, "log lines written before the cookie field must still parse")
        self.assertIsNone(m.group("owner"))

    def test_new_format_exposes_cookie(self):
        m = metrics.LOG_RE.match(line("198.51.100.1", "/", owner="1"))
        self.assertEqual(m.group("owner"), "1")

    def test_empty_cookie_is_not_an_owner(self):
        m = metrics.LOG_RE.match(line("198.51.100.1", "/", owner="-"))
        self.assertEqual(m.group("owner"), "-")


@contextlib.contextmanager
def fresh_state():
    """Give one metrics.collect() call a ledger state file of its own.

    The module-level isolation above keeps the suite off the real state.json.
    This keeps each call off the *previous call's* state, which is a separate
    problem with the same cause: the PTR cache is shared, so one test resolving
    an address to "" decides what a later test injecting a different resolver
    for that same address will see. Addresses are deliberately disjoint between
    classes, but a shared mutable cache should not be the thing enforcing that.
    """
    d = tempfile.mkdtemp()
    prev = ledger.STATE_PATH
    ledger.STATE_PATH = os.path.join(d, "state.json")
    try:
        yield
    finally:
        ledger.STATE_PATH = prev
        shutil.rmtree(d, ignore_errors=True)


class BaseCollect(unittest.TestCase):
    """Runs metrics.collect() against a throwaway log file.

    resolver is injected everywhere so the suite never makes a DNS call: the
    fixtures use TEST-NET addresses, whose lookups would hang on the resolver
    timeout and make a fast unit suite take seconds.
    """
    def collect(self, log_text, state=None, resolver=lambda ip: "", date=DATE):
        fd, path = tempfile.mkstemp()
        with os.fdopen(fd, "w") as f:
            f.write(log_text)
        try:
            with fresh_state():
                return metrics.collect(days=1,
                                       end=datetime.date.fromisoformat(date),
                                       log_path=path, resolver=resolver)[date]
        finally:
            os.unlink(path)

class OwnerExclusion(BaseCollect):
    def test_cookie_visit_is_not_counted(self):
        log = visit("198.51.100.10") + visit("203.0.113.55", owner="1")
        m = self.collect(log)
        self.assertEqual(m["visitors"], 1, "the opted-out device must not be a visitor")
        self.assertEqual(m["pageviews"], 1)

    def test_cookie_clears_the_whole_day_for_that_address(self):
        # First request of a session arrives before the cookie is set.
        log = line("203.0.113.55", "/") + visit("203.0.113.55", owner="1")
        self.assertEqual(self.collect(log)["visitors"], 0)

    def test_empty_cookie_field_is_counted(self):
        # Every ordinary visitor's line carries "-" here.
        self.assertEqual(self.collect(visit("198.51.100.10", owner="-"))["visitors"], 1)

    def test_old_format_lines_are_counted(self):
        self.assertEqual(self.collect(visit("198.51.100.10"))["visitors"], 1)


class UaRotation(unittest.TestCase):
    """One address, many browsers in a day — a scraping farm, not a household.

    The 2026-07-29 audit found this was most of NEMO's reported traffic: single
    addresses claiming Windows Chrome, Linux Chrome and macOS Safari at once,
    each UA ordinary enough that no blocklist would ever catch it.
    """
    collect = OwnerExclusion.collect

    def ua(self, n):
        return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/14{n}.0.0.0 Safari/537.36"

    def test_rotating_uas_from_one_address_are_bots(self):
        log = "".join(visit("203.0.113.9").replace(BROWSER, self.ua(i))
                      for i in range(metrics.MAX_UAS_PER_IP_PER_DAY + 1))
        m = self.collect(log)
        self.assertEqual(m["visitors"], 0,
                         "an address presenting more browsers than a household has is automation")
        self.assertEqual(m["pageviews"], 0)

    def test_a_household_of_devices_still_counts(self):
        # A phone, a laptop and a tablet behind one router must survive.
        log = "".join(visit("203.0.113.9").replace(BROWSER, self.ua(i))
                      for i in range(metrics.MAX_UAS_PER_IP_PER_DAY))
        self.assertEqual(self.collect(log)["visitors"], metrics.MAX_UAS_PER_IP_PER_DAY)

    def test_one_person_reloading_is_untouched(self):
        log = visit("203.0.113.9") * 4
        self.assertEqual(self.collect(log)["visitors"], 1)

    def test_declared_bots_do_not_taint_a_shared_address(self):
        # A crawler and a person can share an office/NAT address. The crawler is
        # excluded on its own merits; it must not push the human over the limit.
        crawler = "Mozilla/5.0 (compatible; SemrushBot/7~bl; +http://www.semrush.com/bot.html)"
        log = visit("203.0.113.9")
        for i in range(5):
            log += visit("203.0.113.9").replace(BROWSER, crawler + str(i))
        self.assertEqual(self.collect(log)["visitors"], 1,
                         "self-declared bots must not count toward UA rotation")


class HostingExclusion(unittest.TestCase):
    """Datacenter traffic wearing an ordinary browser's user agent.

    This was the bulk of NEMO's reported traffic in the 2026-07-29 audit: one
    "/" fetch plus one asset, a current Chrome UA, one address — the exact
    shape of a real visit. Only the PTR record gives it away.
    """
    collect = OwnerExclusion.collect

    def test_ec2_visitor_is_not_a_customer(self):
        log = visit("203.0.113.20")
        m = self.collect(log, resolver=lambda ip: "ec2-3-81-75-163.compute-1.amazonaws.com")
        self.assertEqual(m["visitors"], 0)

    def test_scanner_ptr_is_excluded(self):
        log = visit("203.0.113.21")
        m = self.collect(log, resolver=lambda ip: "prod-boron-us-central-25.li.binaryedge.ninja")
        self.assertEqual(m["visitors"], 0)

    def test_small_vps_hosts_are_excluded(self):
        # 2026-08-11: these exact PTRs were counted as visitors because only
        # their rDNS suffix was missing from HOSTING_RE — ovh.us (only ovh.net
        # was listed), lnvps.cloud, colocrossing, cybeservers — plus the
        # generic vm-NNNN / vps-XXXX naming convention hosts use.
        for ptr in ("vps-98c597da.vps.ovh.us",
                    "vm-1527.lnvps.cloud",
                    "107-173-171-201-host.colocrossing.com",
                    "194-231-192-68.cybeservers.com"):
            m = self.collect(visit("203.0.113.30"), resolver=lambda ip: ptr)
            self.assertEqual(m["visitors"], 0, ptr)

    def test_self_declared_scanner_ua_is_a_bot(self):
        # UAs that literally say "scanner" but contain none of the classic
        # bot substrings; both were counted as visitors on 2026-08-11.
        for ua in ("Mozilla/5.0 (compatible; ModatScanner/1.2; +https://modat.io)",
                   "fhms-its-research-scanner/1.0 (+https://fb02itsscan02.fh-muenster.de)"):
            log = visit("203.0.113.31", ua=ua)
            m = self.collect(log, resolver=lambda ip: "")
            self.assertEqual(m["visitors"], 0, ua)

    def test_residential_isp_is_kept(self):
        # The customer this site exists for. Comcast/Verizon PTRs must survive.
        log = visit("203.0.113.22")
        m = self.collect(log, resolver=lambda ip: "c-73-45-12-9.hsd1.pa.comcast.net")
        self.assertEqual(m["visitors"], 1)

    def test_unresolvable_address_is_kept(self):
        # Plenty of real mobile carriers have no PTR. Absence of evidence must
        # not exclude a visitor, or a resolver outage would zero the numbers.
        self.assertEqual(self.collect(visit("203.0.113.23"),
                                      resolver=lambda ip: "")["visitors"], 1)

    def test_resolver_failure_does_not_drop_traffic(self):
        # A broken resolver must fail toward counting people, not toward a
        # day that silently reads as zero traffic.
        def boom(ip):
            raise RuntimeError("DNS down")
        self.assertEqual(self.collect(visit("203.0.113.24"), resolver=boom)["visitors"], 1)


class IpSkipper(unittest.TestCase):
    def test_exact_and_cidr(self):
        skip = metrics.ip_skipper(["1.2.3.4", "165.225.0.0/16"])
        self.assertTrue(skip("1.2.3.4"))
        self.assertTrue(skip("165.225.220.149"))
        self.assertFalse(skip("8.8.8.8"))

    def test_unparseable_entry_excludes_nothing_extra(self):
        skip = metrics.ip_skipper(["not-an-ip/99"])
        self.assertFalse(skip("8.8.8.8"))


class OwnRows(unittest.TestCase):
    def test_test_marker_in_name(self):
        self.assertTrue(metrics.is_own_row({"name": "TEST LEAD - please ignore"}, set()))

    def test_reserved_555_exchange(self):
        self.assertTrue(metrics.is_own_row({"phone": "717-555-0142"}, set()))

    def test_owner_phone(self):
        self.assertTrue(metrics.is_own_row({"phone": "(717) 555-1234"}, {"7175551234"}))

    def test_real_customer_is_kept(self):
        row = {"name": "Sandra Whitcomb", "phone": "717-848-2211",
               "service": "gutter cleaning", "notes": "two-story, back of house"}
        self.assertFalse(metrics.is_own_row(row, {"7176599999"}))


class CallTaps(BaseCollect):
    """The tel: beacon — the site's only first-party call signal."""

    def test_a_tap_is_counted(self):
        m = self.collect(visit("192.0.2.10") + tap("192.0.2.10"))
        self.assertEqual(m["call_taps"], 1)

    def test_a_tap_is_not_a_pageview_or_a_visit(self):
        base = self.collect(visit("192.0.2.11"))
        with_tap = self.collect(visit("192.0.2.11") + tap("192.0.2.11"))
        self.assertEqual(with_tap["pageviews"], base["pageviews"])
        self.assertEqual(with_tap["visitors"], base["visitors"])
        self.assertEqual(with_tap["bot_hits"], base["bot_hits"])

    def test_tapping_twice_is_still_one_caller(self):
        m = self.collect(visit("192.0.2.12") + tap("192.0.2.12") + tap("192.0.2.12"))
        self.assertEqual(m["call_taps"], 1)

    def test_two_people_are_two_taps(self):
        m = self.collect(visit("192.0.2.13") + tap("192.0.2.13")
                         + visit("192.0.2.14") + tap("192.0.2.14"))
        self.assertEqual(m["call_taps"], 2)

    def test_the_get_fallback_counts_too(self):
        m = self.collect(visit("192.0.2.15") + tap("192.0.2.15", method="GET"))
        self.assertEqual(m["call_taps"], 1)

    def test_a_bot_tap_is_not_a_caller(self):
        m = self.collect(visit("192.0.2.16")
                         + tap("192.0.2.16", ua="SemrushBot/7.0"))
        self.assertEqual(m["call_taps"], 0)

    def test_the_owner_tapping_his_own_number_is_not_a_lead(self):
        m = self.collect(visit("192.0.2.17", owner="1") + tap("192.0.2.17", owner="1"))
        self.assertEqual(m["call_taps"], 0)

    def test_a_failed_beacon_is_not_a_tap(self):
        m = self.collect(visit("192.0.2.18") + tap("192.0.2.18", status=500))
        self.assertEqual(m["call_taps"], 0)

    def test_no_taps_reads_zero_not_missing(self):
        m = self.collect(visit("192.0.2.19"))
        self.assertEqual(m["call_taps"], 0)


class AnswerEngineCrawlers(BaseCollect):
    """Whether the AI crawlers reach the site at all — T046's whole question.

    Every one of these agents is already excluded as a bot. The point of the
    counters is that "excluded" and "never came" look identical in bot_hits,
    and only one of those two is a problem worth an afternoon.
    """

    GPTBOT = "Mozilla/5.0 AppleWebKit/537.36 (compatible; GPTBot/1.2; +https://openai.com/gptbot)"
    PERPLEXITY = "Mozilla/5.0 (compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot)"

    def test_a_gptbot_fetch_is_counted(self):
        m = self.collect(line("203.0.113.5", "/", ua=self.GPTBOT))
        self.assertEqual(m["crawl_gptbot"], 1)

    def test_a_crawler_that_never_came_reads_zero_not_missing(self):
        m = self.collect(visit("192.0.2.30"))
        for key in metrics.CRAWLER_SERIES:
            self.assertEqual(m[key], 0, f"{key} must be a real zero")

    def test_a_blocked_crawler_still_counts(self):
        # A 403 from a CDN rule is the finding, not something to filter out.
        m = self.collect(line("203.0.113.6", "/", ua=self.PERPLEXITY, status=403))
        self.assertEqual(m["crawl_perplexitybot"], 1)

    def test_crawlers_are_still_bots_not_visitors(self):
        m = self.collect(line("203.0.113.7", "/", ua=self.GPTBOT))
        self.assertEqual(m["visitors"], 0)
        self.assertEqual(m["bot_hits"], 1)

    def test_one_hit_is_charged_to_one_crawler(self):
        # ChatGPT-User contains neither "GPTBot" nor "bingbot"; the break in
        # the match loop is what keeps a UA from being double-counted if the
        # patterns ever overlap.
        m = self.collect(line("203.0.113.8", "/", ua=self.GPTBOT))
        self.assertEqual(sum(m[k] for k in metrics.CRAWLER_SERIES), 1)

    def test_bingbot_is_the_control(self):
        m = self.collect(line("203.0.113.9", "/", ua="Mozilla/5.0 (compatible; bingbot/2.0)"))
        self.assertEqual(m["crawl_bingbot"], 1)
        self.assertEqual(m["crawl_gptbot"], 0)

    def test_the_owner_is_not_a_crawler(self):
        m = self.collect(line("192.0.2.31", "/", ua=self.GPTBOT, owner="1"))
        self.assertEqual(m["crawl_gptbot"], 0)


class Rotations(unittest.TestCase):
    """A backfill is only as deep as the archives it bothers to open."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.log = os.path.join(self.dir, "nemo-access.log")

    def touch(self, name):
        open(os.path.join(self.dir, name), "w").close()

    def test_every_kept_rotation_is_read_in_order(self):
        for n in ("nemo-access.log", "nemo-access.log.1",
                  "nemo-access.log.2.gz", "nemo-access.log.3.gz"):
            self.touch(n)
        got = [os.path.basename(p) for p in metrics.rotations(self.log)]
        self.assertEqual(got, ["nemo-access.log", "nemo-access.log.1",
                               "nemo-access.log.2.gz", "nemo-access.log.3.gz"])

    def test_another_sites_log_is_not_picked_up(self):
        self.touch("nemo-access.log")
        self.touch("other-access.log.1")
        self.touch("nemo-access.log.old")
        got = [os.path.basename(p) for p in metrics.rotations(self.log)]
        self.assertEqual(got, ["nemo-access.log"])

    def test_dateext_rotations_are_read_newest_first(self):
        """logrotate's `dateext` names archives by date, not by number.

        Matching only `.1`/`.2.gz` left this returning the live log alone, so a
        backfill over a dead fortnight read one day and reported success.
        """
        for n in ("nemo-access.log", "nemo-access.log-20261030.gz",
                  "nemo-access.log-20261101", "nemo-access.log-20261031.gz"):
            self.touch(n)
        got = [os.path.basename(p) for p in metrics.rotations(self.log)]
        self.assertEqual(got, ["nemo-access.log",
                               "nemo-access.log-20261101",
                               "nemo-access.log-20261031.gz",
                               "nemo-access.log-20261030.gz"])

    def test_a_dashed_dateformat_is_also_a_rotation(self):
        """logrotate's `dateformat` is configurable; -%Y-%m-%d is common."""
        for n in ("nemo-access.log", "nemo-access.log-2026-10-30.gz",
                  "nemo-access.log-2026-11-01"):
            self.touch(n)
        got = [os.path.basename(p) for p in metrics.rotations(self.log)]
        self.assertEqual(got, ["nemo-access.log",
                               "nemo-access.log-2026-11-01",
                               "nemo-access.log-2026-10-30.gz"])

    def test_a_date_suffix_that_is_not_a_date_is_ignored(self):
        self.touch("nemo-access.log")
        self.touch("nemo-access.log-backup")
        self.touch("nemo-access.log-2026110.gz")
        self.touch("nemo-access.log-old")
        got = [os.path.basename(p) for p in metrics.rotations(self.log)]
        self.assertEqual(got, ["nemo-access.log"])


class BackfillAcrossRotations(unittest.TestCase):
    """The recovery command, end to end: `measure --days N` over a dead stretch.

    Rotations() enumerating the archives and collect() recovering a day are
    tested separately above and in BaseCollect. Nothing tested them together,
    which is the only form anyone actually runs: three journal entries have told
    a human to repair a multi-week hole with `growth_daily.py measure --days N`,
    and on 2026-11-03 that path had never once been exercised over more than a
    single day or a single file. A regression here is invisible — the command
    exits 0 either way — and by the time it shows up the logs it was meant to
    read have rotated away.
    """
    DAYS = 22                       # the 2026-10-12 → 11-02 publish outage
    END = datetime.date(2026, 11, 2)
    MON = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

    def day_str(self, d):
        return f"{d.day:02d}/{self.MON[d.month - 1]}/{d.year}:12:00:00 +0000"

    def one_human(self, d, n):
        """A page, its stylesheet and the beacon — post-PV_START, all three.

        The asset is what clears the shape gate and the beacon is the only
        thing a visitor is counted from after PV_START, so a fixture missing
        either records zero visitors on a day that plainly had one.
        """
        day = self.day_str(d)
        # 198.51.100.100+ is free across this module; .20/.21 in the
        # 203.0.113 block belong to HostingExclusion and sharing them
        # made this class decide that class's result.
        ip = f"198.51.100.{100 + n}"
        return visit(ip, day=day) + pv(ip, vid=f"vid{n}", day=day)

    def build(self, dirpath, scheme):
        """One visitor per day, spread over the live log plus one archive each."""
        live = os.path.join(dirpath, "nemo-access.log")
        chunks = {i: self.one_human(self.END - datetime.timedelta(days=i), i + 1)
                  for i in range(self.DAYS)}
        with open(live, "w") as f:
            f.write(chunks[1] + chunks[0])
        for i in range(2, self.DAYS):
            if scheme == "numeric":
                name = f"nemo-access.log.{i - 1}" + ("" if i == 2 else ".gz")
            else:
                d = self.END - datetime.timedelta(days=i)
                name = f"nemo-access.log-{d.strftime('%Y%m%d')}.gz"
            path = os.path.join(dirpath, name)
            opener = (gzip.open(path, "wt") if path.endswith(".gz")
                      else open(path, "w"))
            with opener as f:
                f.write(chunks[i])
        return live

    def recovered(self, scheme):
        with tempfile.TemporaryDirectory() as td:
            live = self.build(td, scheme)
            with fresh_state():
                data = metrics.collect(days=self.DAYS, end=self.END,
                                       log_path=live, resolver=lambda ip: "")
            return {d: m["visitors"] for d, m in data.items()}

    def test_numeric_archives_recover_every_day(self):
        got = self.recovered("numeric")
        self.assertEqual(len(got), self.DAYS)
        self.assertEqual([d for d, v in got.items() if not v], [])

    def test_dateext_archives_recover_every_day(self):
        """The case the 2026-11-02 fix was written for, exercised end to end."""
        got = self.recovered("dateext")
        self.assertEqual(len(got), self.DAYS)
        self.assertEqual([d for d, v in got.items() if not v], [])

    def test_the_window_is_the_days_before_end_inclusive(self):
        """A backfill that silently measured the wrong fortnight is no backfill."""
        got = self.recovered("numeric")
        self.assertEqual(min(got), "2026-10-12")
        self.assertEqual(max(got), self.END.isoformat())


class StateIsolation(BaseCollect):
    """One test's PTR cache must not decide the next test's result.

    hosting_skipper() memoises lookups in ledger state and consults an injected
    resolver only on a cache miss, so without per-call isolation the FIRST
    verdict reached for an address is the one every later test sees. This pins
    the isolation rather than the production behaviour: the caching is correct
    for a daily engine run and is not what these assertions are about.
    """

    ADDR = "198.51.100.200"

    def test_a_cached_verdict_does_not_leak_into_the_next_call(self):
        host = self.collect(visit(self.ADDR),
                            resolver=lambda ip: "ec2-1-2-3-4.compute-1.amazonaws.com")
        self.assertEqual(host["visitors"], 0, "datacenter PTR should exclude")
        # Same address, a resolver that now calls it a household. A leaked cache
        # entry would hold the first verdict and report 0 here.
        home = self.collect(visit(self.ADDR),
                            resolver=lambda ip: "c-73-45-1-2.hsd1.pa.comcast.net")
        self.assertEqual(home["visitors"], 1,
                         "a previous call's PTR cache leaked into this one")

    def test_the_real_state_file_is_never_consulted(self):
        """The suite must not read or write growth/state.json.

        It is gitignored runtime state owned by the droplet, and on a
        long-lived checkout it is what made two of these tests fail on
        2026-11-03 while the repo was unchanged.
        """
        self.assertNotEqual(ledger.STATE_PATH, _REAL_STATE_PATH)
        with fresh_state():
            self.assertNotEqual(ledger.STATE_PATH, _REAL_STATE_PATH)


class PageviewBeacon(BaseCollect):
    """From PV_START, a visitor is a browser that fired /e/pv.

    The raw-log heuristics kept counting scanners with perfect Chrome UAs
    (2026-08-11 audit: ~5–8 humans in ~20 counted). Requiring JS execution
    plus a cookie id is the bar Find A Crib's numbers are already held to,
    and these tests pin the two dashboards to counting the same thing.
    """

    def test_beacon_counts_unique_vids(self):
        log = (visit("198.51.100.10", day=PV_DAY)
               + pv("198.51.100.10", vid="alice")
               + pv("198.51.100.10", vid="alice", p="/services.html")
               + visit("203.0.113.55", day=PV_DAY)
               + pv("203.0.113.55", vid="bob"))
        m = self.collect(log, date=PV_DATE)
        self.assertEqual(m["visitors"], 2, "two cookies = two people")
        self.assertEqual(m["pageviews"], 3, "three beacon fires = three views")

    def test_html_fetch_without_js_is_not_a_visitor(self):
        # The exact traffic that inflated the old numbers: page + asset with a
        # real UA, but nothing ever executed our script.
        log = visit("198.51.100.10", day=PV_DAY)
        m = self.collect(log, date=PV_DATE)
        self.assertEqual(m["visitors"], 0)
        self.assertEqual(m["log_visitors"], 1,
                         "the raw-log tally must stay visible as a cross-check")

    def test_legacy_days_still_count_from_the_log(self):
        m = self.collect(visit("198.51.100.10"))
        self.assertEqual(m["visitors"], 1)
        self.assertNotIn("log_visitors", m,
                         "pre-beacon history keeps its original single series")

    def test_headless_browser_beacon_is_a_bot(self):
        ua = BROWSER.replace("Safari", "HeadlessChrome")
        log = visit("198.51.100.10", day=PV_DAY, ua=ua) \
            + pv("198.51.100.10", vid="h", ua=ua)
        m = self.collect(log, date=PV_DATE)
        self.assertEqual(m["visitors"], 0,
                         "headless Chrome executes JS; the UA gate must still hold")

    def test_owner_device_beacon_not_counted(self):
        log = visit("198.51.100.10", day=PV_DAY, owner="1") \
            + pv("198.51.100.10", vid="own", owner="1")
        m = self.collect(log, date=PV_DATE)
        self.assertEqual(m["visitors"], 0)

    def test_datacenter_beacon_not_counted(self):
        # A dedicated IP, like every hosting test: the ptr_cache in the ledger
        # is warm from earlier runs, and a cached "" would mask the resolver.
        log = visit("203.0.113.40", day=PV_DAY) + pv("203.0.113.40", vid="ec2")
        m = self.collect(log, date=PV_DATE,
                         resolver=lambda ip: "ec2-3-81-75-163.compute-1.amazonaws.com")
        self.assertEqual(m["visitors"], 0,
                         "browser automation on a cloud box runs JS too")

    def test_referrer_rides_in_the_query(self):
        # The beacon request's own Referer header is always our page, so the
        # channel must come from the r param or every visit reads internal.
        log = (visit("198.51.100.10", day=PV_DAY)
               + pv("198.51.100.10", vid="s",
                    r="https%3A%2F%2Fwww.google.com%2F"))
        m = self.collect(log, date=PV_DATE)
        self.assertEqual(m["organic_visitors"], 1)
        self.assertEqual(m["direct_visitors"], 0)

    def test_blocked_storage_falls_back_to_ip_ua(self):
        log = visit("198.51.100.10", day=PV_DAY) + pv("198.51.100.10", vid=None)
        m = self.collect(log, date=PV_DATE)
        self.assertEqual(m["visitors"], 1,
                         "no cookie must degrade to the old proxy, not drop the person")

    def test_beacon_lines_do_not_inflate_log_pageviews(self):
        log = visit("198.51.100.10", day=PV_DAY) + pv("198.51.100.10", vid="a")
        m = self.collect(log, date=PV_DATE)
        self.assertEqual(m["log_pageviews"], 1,
                         "a beacon fire is not a page fetch")


if __name__ == "__main__":
    unittest.main(verbosity=2)

#!/usr/bin/env python3
"""Tests for the measurement rules that decide what counts as a visit.

Run:  python3 -m growth.test_metrics      (from the site root)

These exist because every rule here was added to stop something being counted
that shouldn't be, and a silent regression would look exactly like growth.
"""
import datetime
import os
import tempfile
import unittest

from . import metrics

DAY = "27/Jul/2026:12:00:00 +0000"
DATE = "2026-07-27"
BROWSER = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 "
           "(KHTML, like Gecko) Version/17.0 Safari/605.1.15")


def line(ip, path, ua=BROWSER, ref="-", status=200, owner=None):
    """One access-log line. owner=None writes the pre-2026-07-28 format."""
    base = (f'{ip} - - [{DAY}] "GET {path} HTTP/1.1" {status} 500 '
            f'"{ref}" "{ua}"')
    return base + (f' "{owner}"' if owner is not None else "") + "\n"


def visit(ip, owner=None, ua=BROWSER):
    """A page plus its stylesheet — what a real browser does."""
    return line(ip, "/", ua=ua, owner=owner) + line(ip, "/styles.css", ua=ua, owner=owner)



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


class BaseCollect(unittest.TestCase):
    """Runs metrics.collect() against a throwaway log file.

    resolver is injected everywhere so the suite never makes a DNS call: the
    fixtures use TEST-NET addresses, whose lookups would hang on the resolver
    timeout and make a fast unit suite take seconds.
    """
    def collect(self, log_text, state=None, resolver=lambda ip: ""):
        fd, path = tempfile.mkstemp()
        with os.fdopen(fd, "w") as f:
            f.write(log_text)
        try:
            return metrics.collect(days=1,
                                   end=datetime.date.fromisoformat(DATE),
                                   log_path=path, resolver=resolver)[DATE]
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


if __name__ == "__main__":
    unittest.main(verbosity=2)

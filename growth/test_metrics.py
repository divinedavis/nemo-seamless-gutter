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


def visit(ip, owner=None):
    """A page plus its stylesheet — what a real browser does."""
    return line(ip, "/", owner=owner) + line(ip, "/styles.css", owner=owner)


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


class OwnerExclusion(unittest.TestCase):
    def collect(self, log_text, state=None):
        fd, path = tempfile.mkstemp()
        with os.fdopen(fd, "w") as f:
            f.write(log_text)
        try:
            return metrics.collect(days=1,
                                   end=datetime.date.fromisoformat(DATE),
                                   log_path=path)[DATE]
        finally:
            os.unlink(path)

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


if __name__ == "__main__":
    unittest.main(verbosity=2)

#!/usr/bin/env python3
"""Tests for the AI-call counter.

Run:  python3 -m growth.test_calls      (from the site root)

The dashboard now leads with this number, so the ways it can lie matter:
counting the developer's own testing as demand, dropping a 9pm call onto
tomorrow, or reporting a comfortable zero when the API is actually broken.
"""
import datetime
import os
import tempfile
import unittest

from . import calls


def row(ts, phone, direction="inbound"):
    return {"ts": ts, "phone": phone, "direction": direction, "secs": 30,
            "messages": 4, "status": "done"}


# 2026-07-29 21:30 ET, an evening call — 01:30 UTC the following day.
EVENING_ET = int(datetime.datetime(2026, 7, 30, 1, 30,
                                   tzinfo=datetime.timezone.utc).timestamp())


class Exclusions(unittest.TestCase):
    def setUp(self):
        # owner_phones() reads the ledger state file, which lives only on the
        # droplet; the env override is the same list by another door.
        os.environ["NEMO_OWNER_PHONES"] = "7176599140"
        self.addCleanup(os.environ.pop, "NEMO_OWNER_PHONES", None)
        self.phones = {"7176599140"}

    def test_owner_number_is_not_demand(self):
        self.assertTrue(calls.is_own_call(row(EVENING_ET, "7176599140"), self.phones))

    def test_stranger_is_counted(self):
        self.assertFalse(calls.is_own_call(row(EVENING_ET, "4107339888"), self.phones))

    def test_reserved_555_exchange_is_a_test(self):
        self.assertTrue(calls.is_own_call(row(EVENING_ET, "7175550199"), self.phones))

    def test_unknown_number_is_counted_rather_than_dropped(self):
        # A call with no caller id is more likely a real one with a blocked
        # number than our own testing, and silently dropping it would under-
        # report demand — the failure that matters here.
        self.assertFalse(calls.is_own_call(row(EVENING_ET, ""), self.phones))

    def test_split_excludes_owner_and_outbound(self):
        rows = [row(EVENING_ET, "4107339888"),
                row(EVENING_ET, "7176599140"),
                row(EVENING_ET, "2125551234", direction="outbound")]
        real, own = calls._split(rows, refresh=False)
        self.assertEqual([r["phone"] for r in real], ["4107339888"])
        self.assertEqual(len(own), 1)


class BusinessDay(unittest.TestCase):
    def test_evening_call_counts_today_not_tomorrow(self):
        # 9:30pm Eastern is 01:30 UTC the next day. Counted in UTC, every
        # evening call would land on the following morning's report.
        self.assertEqual(calls._day(EVENING_ET), "2026-07-29")


class Cache(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, "calls_cache.json")
        self._orig = calls.CACHE
        calls.CACHE = self.path

    def tearDown(self):
        calls.CACHE = self._orig

    def test_round_trip(self):
        calls._write_cache({"calls": {"conv_1": row(EVENING_ET, "4107339888")}})
        rows = calls.fetch(refresh=False)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["day"], "2026-07-29")

    def test_corrupt_cache_is_not_fatal(self):
        with open(self.path, "w") as f:
            f.write("{not json")
        self.assertEqual(calls.fetch(refresh=False), [])


class Status(unittest.TestCase):
    """A broken key must not read as a quiet phone."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self._orig_cache, self._orig_get = calls.CACHE, calls._get
        calls.CACHE = os.path.join(self.tmp, "calls_cache.json")

    def tearDown(self):
        calls.CACHE, calls._get = self._orig_cache, self._orig_get

    def test_api_failure_reports_not_ok(self):
        def boom(*a, **k):
            raise RuntimeError("401 unauthorized")
        calls._get = boom
        st = {}
        rows = calls.fetch(key="x", aid="agent_x", status=st)
        self.assertEqual(rows, [])
        self.assertFalse(st["ok"])
        self.assertIn("401", st["error"])

    def test_missing_key_reports_not_ok(self):
        # No key passed and none to find: this must report a failure rather
        # than fall through to a real request (which on a dev machine with the
        # key in the keychain would quietly succeed and prove nothing).
        orig = calls.load_key
        calls.load_key = lambda: None
        self.addCleanup(setattr, calls, "load_key", orig)
        st = {}
        calls.fetch(status=st)
        self.assertFalse(st["ok"])
        self.assertEqual(st["error"], "no ElevenLabs API key")

    def test_success_reports_ok(self):
        def fake(path, key, params=None):
            if path == "/conversations":
                return {"conversations": [{"conversation_id": "c1",
                                           "start_time_unix_secs": EVENING_ET,
                                           "call_duration_secs": 19,
                                           "message_count": 5,
                                           "status": "done"}],
                        "has_more": False}
            return {"metadata": {"phone_call": {"external_number": "+14107339888",
                                                "direction": "inbound"}}}
        calls._get = fake
        st = {}
        rows = calls.fetch(key="x", aid="agent_x", status=st)
        self.assertTrue(st["ok"])
        self.assertEqual(rows[0]["phone"], "4107339888")
        # Second refresh must not re-fetch a call it has already identified.
        seen = []
        def counting(path, key, params=None):
            seen.append(path)
            return fake(path, key, params)
        calls._get = counting
        calls.fetch(key="x", aid="agent_x")
        self.assertEqual(seen, ["/conversations"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

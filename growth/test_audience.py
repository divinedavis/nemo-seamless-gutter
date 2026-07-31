#!/usr/bin/env python3
"""Tests for the all-time visitor roster.

Run:  python3 -m growth.test_audience      (from the site root)

The roster is the only place the "how many people, ever" and "how many came
back" figures on the portfolio come from, and it is accumulated — a bug here
does not show up as a wrong number today, it quietly corrupts a history that
cannot be rebuilt once nginx has rotated the log away.
"""
import json
import os
import tempfile
import unittest

from . import audience


class Roster(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp()
        os.close(fd)
        os.unlink(self.path)          # start with no file, as a fresh install does

    def tearDown(self):
        for p in (self.path, self.path + ".tmp"):
            if os.path.exists(p):
                os.unlink(p)

    def fold(self, roster):
        return audience.merge_and_save(roster, self.path)

    def test_a_missing_file_is_an_empty_roster_not_a_crash(self):
        self.assertEqual(audience.load(self.path)["people"], {})

    def test_a_corrupt_file_is_survivable(self):
        with open(self.path, "w") as f:
            f.write("{not json")
        self.assertEqual(audience.load(self.path)["people"], {})

    def test_visitors_accumulate_across_days(self):
        self.fold({"2026-07-28": {"a": 2, "b": 1}})
        t = self.fold({"2026-07-29": {"c": 1}})
        self.assertEqual(t["visitors"], 3)

    def test_the_same_person_on_two_days_is_one_person_who_returned(self):
        self.fold({"2026-07-28": {"a": 1, "b": 1}})
        t = self.fold({"2026-07-29": {"a": 1}})
        self.assertEqual(t["visitors"], 2)
        self.assertEqual(t["returning"], 1)
        self.assertEqual(t["returning_pct"], 50)

    def test_two_pages_in_one_day_is_not_a_return_visit(self):
        t = self.fold({"2026-07-28": {"a": 5}})
        self.assertEqual(t["returning"], 0)
        self.assertEqual(t["pageviews"], 5)

    def test_rerunning_a_day_does_not_double_count(self):
        self.fold({"2026-07-28": {"a": 3}})
        t = self.fold({"2026-07-28": {"a": 3}})
        self.assertEqual(t["visitors"], 1)
        self.assertEqual(t["pageviews"], 3)

    def test_a_backfill_moves_the_since_date_earlier(self):
        self.fold({"2026-07-30": {"a": 1}})
        t = self.fold({"2026-07-28": {"b": 1}})
        self.assertEqual(t["since"], "2026-07-28")

    def test_an_empty_day_does_not_backdate_the_record(self):
        # A day with no rows may simply be a day whose log had already rotated
        # away. Claiming to have counted from it would overstate the history.
        t = self.fold({"2026-07-26": {}, "2026-07-27": {"a": 1}})
        self.assertEqual(t["since"], "2026-07-27")

    def test_the_raw_visitor_id_is_never_written_to_disk(self):
        self.fold({"2026-07-28": {"203.0.113.9|Mozilla/5.0": 1}})
        with open(self.path) as f:
            raw = f.read()
        self.assertNotIn("203.0.113.9", raw)
        self.assertNotIn("Mozilla", raw)

    def test_the_salt_survives_so_a_person_stays_the_same_person(self):
        self.fold({"2026-07-28": {"203.0.113.9|Mozilla/5.0": 1}})
        salt = audience.load(self.path)["salt"]
        self.fold({"2026-07-29": {"203.0.113.9|Mozilla/5.0": 1}})
        data = audience.load(self.path)
        self.assertEqual(data["salt"], salt)
        self.assertEqual(len(data["people"]), 1)

    def test_the_roster_is_not_world_readable(self):
        self.fold({"2026-07-28": {"a": 1}})
        self.assertEqual(os.stat(self.path).st_mode & 0o077, 0)

    def test_empty_roster_reports_zeroes_not_a_division_error(self):
        t = audience.totals(audience.load(self.path))
        self.assertEqual((t["visitors"], t["returning"], t["returning_pct"]), (0, 0, 0))

    def test_a_day_recorded_before_view_counts_existed_still_upgrades(self):
        # An early roster stored days as a plain count. Reading one must not
        # throw, and the person must not be lost.
        with open(self.path, "w") as f:
            json.dump({"salt": "s", "since": "2026-07-28",
                       "people": {"abc": {"first": "2026-07-28",
                                          "last": "2026-07-28", "days": 1}}}, f)
        t = self.fold({"2026-07-29": {"x": 1}})
        self.assertEqual(t["visitors"], 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)

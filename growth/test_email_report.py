#!/usr/bin/env python3
"""Tests for the owner email's "Worth your time" card.

These exist because of what the 2026-09-26 review found. `OWNER_ACTIONABLE` is
an allowlist of technique slugs, and it was written when the ledger ended at
T016. Every owner-side technique the scout proposed afterwards — the Business
Profile's hours, services list, service area, booking link, the call baseline,
the review replies — was therefore excluded by construction, because a slug
invented later can never appear in a set written earlier. The review journal
ranked those profile fields as the highest-value action available on sixty
consecutive mornings; none of them was ever rendered into the one inbox that
could act on them, and nothing failed, so nothing said so.

So the first test below is not really about a set membership. It is a guard
against the same silence returning: if an owner-side Business Profile field
drops out of the card again, this fails loudly instead of the email quietly
getting shorter.

The second concern is order. The primary-category audit is the heaviest single
field on a profile and also the most dangerous one — the March 2026 core update
made careless category and business-name edits a leading cause of contractor
profile suspensions — so it must be read last, after the fields that cannot
hurt. An email has no other safety rail than the order its rows appear in.

Run: python3 -m growth.test_email_report   (from the repo root)
"""
import unittest
from unittest import mock

from . import email_report


def _tech(slug, tid, notes="first step: do the thing.", status="candidate"):
    return {"id": tid, "slug": slug, "name": slug.replace("_", " "),
            "status": status, "notes": notes}


# The fields recommendation 1 of the review journal has named since 2026-07-27.
# Losing any of these from the card is the regression this file exists to catch.
PROFILE_FIELDS = ("open_now_hours_and_saturday_estimate_window",
                  "gbp_services_list_and_job_photo_cadence",
                  "gbp_service_area_geography_pass",
                  "gbp_appointment_link_free_measurement",
                  "call_instrumentation_baseline")


class OwnerActionable(unittest.TestCase):
    def test_every_business_profile_field_reaches_the_owner(self):
        for slug in PROFILE_FIELDS:
            self.assertIn(slug, email_report.OWNER_ACTIONABLE,
                          f"{slug} is owner-only work that would never be shown to him")

    def test_the_high_variance_category_audit_is_read_last(self):
        order = email_report.OWNER_ACTION_ORDER
        self.assertEqual(order[-1], "gbp_category_and_qna_audit")
        for slug in PROFILE_FIELDS:
            self.assertLess(order.index(slug), order.index("gbp_category_and_qna_audit"),
                            f"{slug} cannot hurt the profile and must be offered first")

    def test_hours_come_before_everything_else(self):
        # A profile reading "closed" during working hours loses the click to
        # whoever is open, whatever else is right about it.
        self.assertEqual(email_report.OWNER_ACTION_ORDER[0],
                         "open_now_hours_and_saturday_estimate_window")

    def test_every_ordered_slug_is_actually_shown(self):
        # An entry in the order that is not in the allowlist is a typo that
        # would silently sort nothing.
        for slug in email_report.OWNER_ACTION_ORDER:
            self.assertIn(slug, email_report.OWNER_ACTIONABLE, slug)


class OwnerActionsCard(unittest.TestCase):
    def render(self, techs):
        with mock.patch.object(email_report.ledger, "load_techniques",
                               return_value=techs):
            return email_report._owner_actions_card()

    def test_the_card_orders_by_risk_not_by_ledger_id(self):
        # Deliberately handed to it in the order the ledger holds them, which
        # puts the dangerous field first.
        html = self.render([
            _tech("gbp_category_and_qna_audit", "T016"),
            _tech("gbp_services_list_and_job_photo_cadence", "T022"),
            _tech("open_now_hours_and_saturday_estimate_window", "T042"),
        ])
        self.assertLess(html.index("open now hours"), html.index("gbp category"))
        self.assertLess(html.index("gbp services list"), html.index("gbp category"))

    def test_an_unranked_owner_slug_still_appears(self):
        html = self.render([_tech("citations", "T009"),
                            _tech("open_now_hours_and_saturday_estimate_window", "T042")])
        self.assertIn("citations", html)
        self.assertIn("open now hours", html)

    def test_engineering_chores_stay_out_of_his_inbox(self):
        html = self.render([_tech("some_api_key_chore", "T099"),
                            _tech("citations", "T009")])
        self.assertNotIn("some api key chore", html)

    def test_an_active_technique_is_not_still_asked_for(self):
        html = self.render([_tech("open_now_hours_and_saturday_estimate_window",
                                  "T042", status="active")])
        self.assertEqual(html, "")

    def test_a_candidate_with_no_notes_has_nothing_to_say(self):
        html = self.render([_tech("citations", "T009", notes="")])
        self.assertEqual(html, "")

    def test_the_card_addresses_the_owner_not_the_developer(self):
        html = self.render([_tech("citations", "T009",
                                  notes="first step: confirm with Eric that Eric has the login.")])
        self.assertNotIn("Eric", html)
        self.assertIn("you", html)


if __name__ == "__main__":
    unittest.main()

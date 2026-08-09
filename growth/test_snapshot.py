#!/usr/bin/env python3
"""Tests for the snapshot's engine-version stamp.

Added 2026-08-09. The docroot is not a git checkout, so a commit on main is not
running until somebody copies it across, and nothing in the snapshot said which
version had produced it. Three consecutive reviews deduced the deployed version
from which optional keys were missing, and on 2026-08-09 that inference had to
untangle a *partial* deploy: techniques.py and templates.py were live from the
night before, while snapshot.py, gsc.py, metrics.py and scout.py were still the
2026-08-04 copies. Absence-of-a-key cannot see that, because it only exists
where a change happened to add a key.

`_code_fingerprint()` hashes the engine's own source so the reviewer can hash
the same files in its checkout and diff. These tests pin the properties that
comparison depends on: it changes when a source file changes, it does not
change when a test file does, it names growth_daily.py because that file has
its own way of being left behind, and it never raises — a snapshot that fails
to publish tells the reviewer nothing at all, which is worse than a snapshot
with no stamp on it.

No network and no droplet state.

Run: python3 -m growth.test_snapshot   (from the repo root)
"""
import os
import unittest
from unittest import mock

from . import snapshot as S


class CodeFingerprintTest(unittest.TestCase):

    def test_names_the_engine_modules_and_omits_tests(self):
        fp = S._code_fingerprint()
        self.assertIn("snapshot.py", fp["modules"])
        self.assertIn("techniques.py", fp["modules"])
        self.assertIn("gsc.py", fp["modules"])
        self.assertIn("metrics.py", fp["modules"])
        # Tests never run on the droplet, so their hashes would differ between
        # the two sides for reasons that mean nothing.
        self.assertNotIn("test_snapshot.py", fp["modules"])
        self.assertFalse([k for k in fp["modules"] if k.startswith("test_")])
        # Only Python. snapshot.json and JOURNAL.md live in this directory and
        # change every single morning; including them would make the stamp
        # differ on every run and say nothing about the code.
        self.assertFalse([k for k in fp["modules"] if not k.endswith(".py")])

    def test_includes_the_cli_that_sits_outside_the_package(self):
        fp = S._code_fingerprint()
        self.assertIn("../growth_daily.py", fp["modules"])

    def test_hashes_are_the_content_of_the_files(self):
        """The reviewer computes the other side of this comparison itself."""
        import hashlib
        fp = S._code_fingerprint()
        with open(os.path.join(S.HERE, "keywords.py"), "rb") as fh:
            expected = hashlib.sha256(fh.read()).hexdigest()[:12]
        self.assertEqual(fp["modules"]["keywords.py"], expected)

    def test_combined_moves_when_any_module_moves(self):
        first = S._code_fingerprint()
        real = S.os.listdir

        def one_fewer(path):
            names = real(path)
            return [n for n in names if n != "keywords.py"]

        with mock.patch.object(S.os, "listdir", one_fewer):
            second = S._code_fingerprint()
        self.assertNotIn("keywords.py", second["modules"])
        self.assertNotEqual(first["combined"], second["combined"])

    def test_combined_is_stable_across_calls(self):
        self.assertEqual(S._code_fingerprint()["combined"],
                         S._code_fingerprint()["combined"])

    def test_an_unreadable_file_is_skipped_rather_than_fatal(self):
        """Never take the bridge down over the diagnostic bolted to it."""
        real_open = open

        def deny_one(path, *a, **kw):
            if str(path).endswith("keywords.py"):
                raise OSError("permission denied")
            return real_open(path, *a, **kw)

        with mock.patch("builtins.open", deny_one):
            fp = S._code_fingerprint()
        self.assertNotIn("keywords.py", fp["modules"])
        self.assertIn("snapshot.py", fp["modules"])

    def test_a_missing_cli_is_skipped_rather_than_fatal(self):
        real_open = open

        def deny_cli(path, *a, **kw):
            if str(path).endswith("growth_daily.py"):
                raise OSError("no such file")
            return real_open(path, *a, **kw)

        with mock.patch("builtins.open", deny_cli):
            fp = S._code_fingerprint()
        self.assertNotIn("../growth_daily.py", fp["modules"])
        self.assertTrue(fp["combined"])

    def test_survives_the_pii_scrub_unchanged(self):
        """A 12-hex digest must not look like anything scrub() redacts."""
        fp = S._code_fingerprint()
        clean, found = S.scrub({"code_version": fp})
        self.assertEqual(clean["code_version"], fp)
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()

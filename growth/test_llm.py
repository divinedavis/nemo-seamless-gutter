#!/usr/bin/env python3
"""Tests for the two failures that killed steps in the 2026-07-30 run:
a 529 with no retry, and a JSON reply with an unescaped quote.

Run: python3 -m growth.test_llm   (from the repo root)
"""
import json
import unittest
import unittest.mock as mock
import urllib.error

from . import llm


class RepairTest(unittest.TestCase):
    def test_plain_json_survives_repair(self):
        blob = '{"h2": "Gutter repair", "paragraphs": ["one", "two"]}'
        self.assertEqual(json.loads(llm._repair(blob)), json.loads(blob))

    def test_unescaped_inner_quote(self):
        # The 2026-07-30 shape: a 5" profile written raw inside a string.
        blob = '{"h2": "We install 5" K-style gutter", "n": 2}'
        got = json.loads(llm._repair(blob))
        self.assertEqual(got["h2"], 'We install 5" K-style gutter')
        self.assertEqual(got["n"], 2)

    def test_quoted_phrase_mid_sentence(self):
        blob = '{"a": "homeowners say "my gutters overflow" every spring"}'
        got = json.loads(llm._repair(blob))
        self.assertIn("my gutters overflow", got["a"])

    def test_inch_marks_in_a_heading(self):
        # The shape this trade actually produces: 5" and 6" in one value.
        blob = '{"h2": "5" vs 6" Gutters", "n": 1}'
        got = json.loads(llm._repair(blob))
        self.assertEqual(got["h2"], '5" vs 6" Gutters')
        self.assertEqual(got["n"], 1)

    def test_raw_newline_and_tab(self):
        blob = '{"a": "line one\nline two\tend"}'
        self.assertEqual(json.loads(llm._repair(blob))["a"],
                         "line one\nline two\tend")

    def test_valid_escapes_preserved(self):
        blob = r'{"a": "he said \"hi\" and \\ left", "b": "c:\\tmp"}'
        got = json.loads(llm._repair(blob))
        self.assertEqual(got["a"], 'he said "hi" and \\ left')
        self.assertEqual(got["b"], "c:\\tmp")

    def test_call_json_recovers_broken_reply(self):
        broken = '{"h2": "The 5" profile", "paragraphs": ["a"]}'
        with mock.patch.object(llm, "call", return_value=broken):
            got = llm.call_json("sys", "prompt")
        self.assertEqual(got["paragraphs"], ["a"])

    def test_call_json_still_salvages_truncation(self):
        cut = '{"ideas": [{"name": "one"}, {"name": "tw'
        with mock.patch.object(llm, "call", return_value=cut):
            got = llm.call_json("sys", "prompt")
        self.assertEqual(got["ideas"][0]["name"], "one")


def _http_error(code):
    return urllib.error.HTTPError(
        llm.API_URL, code, "err", {},
        __import__("io").BytesIO(b'{"type":"error","error":{"type":"overloaded_error"}}'))


class RetryTest(unittest.TestCase):
    def setUp(self):
        self.sleeps = []
        p = mock.patch.object(llm.time, "sleep", self.sleeps.append)
        p.start()
        self.addCleanup(p.stop)

    def _run(self, side_effect, **kw):
        ok = mock.MagicMock()
        ok.__enter__.return_value.read.return_value = json.dumps(
            {"content": [{"type": "thinking", "thinking": "..."},
                         {"type": "text", "text": "done"}]}).encode()
        seq = [x if not isinstance(x, str) else ok for x in side_effect]
        with mock.patch.object(llm.urllib.request, "urlopen", side_effect=seq) as u:
            return llm.call("sys", "prompt", key="sk-test", **kw), u

    def test_529_then_success(self):
        out, u = self._run([_http_error(529), _http_error(529), "ok"])
        self.assertEqual(out, "done")
        self.assertEqual(u.call_count, 3)
        self.assertEqual(len(self.sleeps), 2)

    def test_gives_up_after_retries_and_names_the_cause(self):
        with self.assertRaises(RuntimeError) as cm:
            self._run([_http_error(529)] * 3, retries=2)
        self.assertIn("529", str(cm.exception))
        self.assertEqual(len(self.sleeps), 2)  # no sleep after the last attempt

    def test_permanent_error_is_not_retried(self):
        with self.assertRaises(RuntimeError) as cm:
            self._run([_http_error(401)])
        self.assertIn("401", str(cm.exception))
        self.assertEqual(self.sleeps, [])

    def test_billing_400_is_not_retried(self):
        # Both billing failures arrive as 400. An empty balance is an answer,
        # and retrying a spend cap is how the cap gets worse.
        self.assertNotIn(400, llm.RETRY_STATUS)
        with self.assertRaises(RuntimeError):
            self._run([_http_error(400)])
        self.assertEqual(self.sleeps, [])

    def test_network_error_is_retried(self):
        out, u = self._run([urllib.error.URLError("connection reset"), "ok"])
        self.assertEqual(out, "done")
        self.assertEqual(u.call_count, 2)

    def test_retry_after_header_is_honoured(self):
        e = _http_error(429)
        e.headers = {"retry-after": "7"}
        out, _ = self._run([e, "ok"])
        self.assertEqual(out, "done")
        self.assertEqual(self.sleeps, [7.0])


if __name__ == "__main__":
    unittest.main(verbosity=2)

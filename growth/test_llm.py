#!/usr/bin/env python3
"""Tests for the two failures that killed steps in the 2026-07-30 run:
a 529 with no retry, and a JSON reply with an unescaped quote.

Run: python3 -m growth.test_llm   (from the repo root)
"""
import json
import os
import tempfile
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
        with mock.patch.object(llm, "call_blocks", return_value=[broken]):
            got = llm.call_json("sys", "prompt")
        self.assertEqual(got["paragraphs"], ["a"])

    def test_call_json_still_salvages_truncation(self):
        cut = '{"ideas": [{"name": "one"}, {"name": "tw'
        with mock.patch.object(llm, "call_blocks", return_value=[cut]):
            got = llm.call_json("sys", "prompt")
        self.assertEqual(got["ideas"][0]["name"], "one")

    def test_call_json_ignores_braces_in_search_commentary(self):
        """Web search puts narration in an earlier text block than the answer.

        A brace in that narration used to drag the parse start into the prose,
        so the whole research call was lost.
        """
        narration = 'I will look for a {slug, name} shaped answer.'
        answer = '{"techniques": [{"slug": "one"}]}'
        with mock.patch.object(llm, "call_blocks",
                               return_value=[narration, answer]):
            got = llm.call_json("sys", "prompt")
        self.assertEqual(got["techniques"][0]["slug"], "one")

    def test_call_json_writes_unparseable_reply_to_disk(self):
        junk = "{{{ not json at all"
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(llm, "call_blocks", return_value=[junk]), \
                 mock.patch.object(llm, "DEBUG_DIR", tmp):
                with self.assertRaises(ValueError):
                    llm.call_json("sys", "prompt")
            dumped = os.listdir(tmp)
            self.assertEqual(len(dumped), 1)
            self.assertIn(junk, open(os.path.join(tmp, dumped[0])).read())

    def test_call_joins_blocks(self):
        with mock.patch.object(llm, "call_blocks", return_value=["a", "b"]):
            self.assertEqual(llm.call("sys", "prompt"), "ab")


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


def _reply(blocks, stop_reason="end_turn"):
    """A urlopen context manager returning one API reply."""
    ok = mock.MagicMock()
    ok.__enter__.return_value.read.return_value = json.dumps(
        {"content": blocks, "stop_reason": stop_reason}).encode()
    return ok


class PauseTurnTest(unittest.TestCase):
    """The 2026-08-29 and 2026-09-05 scout failures.

    With a server-side tool the API runs its own sampling loop and stops at 10
    iterations with `stop_reason: "pause_turn"`. The reply holds only the
    model's opening narration; the answer has not been generated yet. Returning
    it as if the turn were over is what produced "no parseable JSON object in
    reply: I'll research what's working right now...".
    """

    def setUp(self):
        self.sleeps = []
        p = mock.patch.object(llm.time, "sleep", self.sleeps.append)
        p.start()
        self.addCleanup(p.stop)

    def _run(self, replies, **kw):
        with mock.patch.object(llm.urllib.request, "urlopen",
                               side_effect=replies) as u:
            return llm.call_blocks("sys", "prompt", key="sk-test", **kw), u

    def test_paused_turn_is_resumed_and_all_text_kept(self):
        narration = {"type": "text", "text": "I'll research what's working."}
        search = {"type": "server_tool_use", "id": "s1", "name": "web_search"}
        answer = {"type": "text", "text": '{"techniques": []}'}
        out, u = self._run([_reply([narration, search], "pause_turn"),
                            _reply([answer])])
        self.assertEqual(u.call_count, 2)
        # Both legs are kept, answer last — call_json tries the last block first.
        self.assertEqual(out, ["I'll research what's working.",
                               '{"techniques": []}'])
        self.assertEqual(llm.LAST_STOP_REASON, "end_turn")

    def test_resume_sends_the_paused_turn_back_with_no_extra_user_message(self):
        content = [{"type": "text", "text": "searching"},
                   {"type": "server_tool_use", "id": "s1", "name": "web_search"}]
        _, u = self._run([_reply(content, "pause_turn"), _reply([])])
        sent = json.loads(u.call_args_list[1].args[0].data.decode())
        self.assertEqual([m["role"] for m in sent["messages"]],
                         ["user", "assistant"])
        # The server resumes off the trailing server-tool block; a "continue"
        # user turn would restart the model instead.
        self.assertEqual(sent["messages"][1]["content"], content)

    def test_a_turn_that_never_unpauses_stops_at_the_ceiling(self):
        paused = [_reply([{"type": "text", "text": "."}], "pause_turn")] * 20
        with mock.patch.object(llm, "MAX_CONTINUATIONS", 2):
            out, u = self._run(paused)
        self.assertEqual(u.call_count, 3)  # first call plus two continuations
        self.assertEqual(len(out), 3)

    def test_unpaused_reply_is_a_single_round_trip(self):
        out, u = self._run([_reply([{"type": "thinking", "thinking": "..."},
                                    {"type": "text", "text": "done"}])])
        self.assertEqual(u.call_count, 1)
        self.assertEqual(out, ["done"])

    def test_a_reply_with_no_stop_reason_is_not_treated_as_paused(self):
        ok = mock.MagicMock()
        ok.__enter__.return_value.read.return_value = json.dumps(
            {"content": [{"type": "text", "text": "done"}]}).encode()
        out, u = self._run([ok])
        self.assertEqual((out, u.call_count), (["done"], 1))

    def test_parse_failure_names_the_stop_reason(self):
        """So the next one is diagnosable from the journal, not the droplet."""
        with mock.patch.object(llm, "call_blocks", return_value=["prose"]), \
             mock.patch.object(llm, "LAST_STOP_REASON", "max_tokens"):
            with self.assertRaises(ValueError) as cm:
                llm.call_json("sys", "prompt")
        self.assertIn("stop_reason=max_tokens", str(cm.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)

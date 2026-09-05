#!/usr/bin/env python3
"""Shared Anthropic client for the growth engine.

The key already lives on the droplet in seo/.env (gen_article.py has used it
since June). Nothing here invents a second place to put credentials.
"""
import json
import os
import random
import re
import subprocess
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
API_URL = "https://api.anthropic.com/v1/messages"

# Opus for prose and research: this content goes on a real business's site
# under its own name, so the floor on quality matters more than the token cost
# of a few pages a week.
MODEL = os.environ.get("NEMO_GROWTH_MODEL", "claude-opus-5")

WEB_SEARCH = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 8}]


def load_key():
    v = os.environ.get("ANTHROPIC_API_KEY")
    if v:
        return v.strip()
    # seo/.env is the established home for this key on the droplet.
    for p in (os.path.join(HERE, "..", "seo", ".env"),
              os.path.join(HERE, ".anthropic_key")):
        p = os.path.abspath(p)
        if not os.path.exists(p):
            continue
        try:
            with open(p) as f:
                for line in f:
                    if line.startswith("ANTHROPIC_API_KEY="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
                    if p.endswith(".anthropic_key"):
                        return line.strip()
        except Exception:
            pass
    try:
        return subprocess.check_output(
            ["security", "find-generic-password", "-s", "legacy-scs-anthropic", "-w"],
            stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return None


# Replies come back as a thinking block followed by a text block, and thinking
# is billed against the same max_tokens budget. A request for 900 tokens spent
# 721 of them thinking and returned an empty string — which surfaced as "no
# JSON object in reply" and looked like a prompt bug rather than a budget one.
# Anything below this floor is raised rather than silently truncated.
MIN_MAX_TOKENS = 3000

# 529 (overloaded) killed three of eleven steps on 2026-07-30 — the api was busy
# for a few seconds and a whole morning's content went unwritten. These statuses
# are the API saying "not now", not "never": rate limits, gateway hiccups, and
# capacity. Retrying is also free, since an overloaded/limited request bills no
# tokens — only the attempt that succeeds costs anything, and that is the one
# unit of work the run was always going to pay for.
#
# 400 is deliberately absent, per the review agent's reasoning in ab7592e: both
# billing failures arrive as 400, and an empty balance or a self-imposed spend
# cap is an answer rather than a hiccup. Hammering a cap is how the cap gets
# worse. 401/403/404 are permanent for the same reason and raise immediately.
RETRY_STATUS = {408, 409, 425, 429, 500, 502, 503, 504, 529}
RETRIES = int(os.environ.get("NEMO_LLM_RETRIES", "5"))
BACKOFF = (2, 6, 15, 40, 75)  # seconds before attempt 2..6, plus jitter

# Where an unparseable reply is written so the failure can be read later
# instead of reproduced with another paid call.
DEBUG_DIR = os.environ.get("NEMO_LLM_DEBUG_DIR", "/tmp")


def _sleep_for(attempt, retry_after=None):
    """Wait before the next attempt. Honours Retry-After when the API sends it."""
    if retry_after:
        try:
            return min(float(retry_after), 120.0)
        except (TypeError, ValueError):
            pass
    base = BACKOFF[min(attempt, len(BACKOFF) - 1)]
    return base + random.uniform(0, base * 0.25)


def _post(body, key, timeout, attempts):
    """One request, retried on the transient statuses. Returns the parsed reply.

    Split out of call_blocks so a paused turn (below) can be resumed without
    duplicating the backoff logic. The error that finally escapes is the last
    one seen, so the report still names the cause.
    """
    data = json.dumps(body).encode()
    last = None
    for attempt in range(attempts):
        req = urllib.request.Request(
            API_URL, data=data,
            headers={"content-type": "application/json", "x-api-key": key,
                     "anthropic-version": "2023-06-01"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            detail = e.read()[:300].decode(errors="replace")
            last = RuntimeError(f"anthropic {e.code}: {detail}")
            if e.code not in RETRY_STATUS:
                raise last
            wait = _sleep_for(attempt, (e.headers or {}).get("retry-after"))
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            # Connection reset / DNS blip / read timeout — same class of problem
            # as a 529 from the caller's point of view.
            last = RuntimeError(f"anthropic request failed: {e}")
            wait = _sleep_for(attempt)

        if attempt == attempts - 1:
            break
        time.sleep(wait)
    raise last


# A reply that ends `pause_turn` is not finished. With a server-side tool, the
# API runs its own sampling loop and pauses at 10 iterations; the reply carries
# whatever was produced so far and the caller is expected to send it back to
# resume. The scout never did, so on 2026-08-29 and 2026-09-05 it kept only the
# model's opening narration — "I'll research what's working right now..." — and
# died in the JSON parser with no brace in sight, which reads like a prompt bug
# rather than a truncated conversation. Resume instead, with a ceiling so a
# model that pauses forever cannot bill forever.
MAX_CONTINUATIONS = int(os.environ.get("NEMO_LLM_CONTINUATIONS", "4"))

# The stop_reason of the last reply, so a parse failure can say whether the
# reply was finished, cut off at max_tokens, or still paused.
LAST_STOP_REASON = None


def call_blocks(system, prompt, max_tokens=4000, tools=None, timeout=240,
                key=None, retries=None):
    """One exchange. Returns the text blocks as a list.

    With web search on, a reply is a sequence of blocks — the model narrates
    ("I'll research what's working..."), searches, then answers. Only the last
    text block carries the answer, so a JSON caller needs them kept apart;
    call() joins them for everyone else.

    A `pause_turn` reply is resumed rather than returned, because the answer is
    in the part that has not been generated yet. Text from every leg is kept and
    returned in order, so the resumed answer is the last block either way.
    """
    global LAST_STOP_REASON
    max_tokens = max(max_tokens, MIN_MAX_TOKENS)
    key = key or load_key()
    if not key:
        raise RuntimeError(
            "no Anthropic key — expected ANTHROPIC_API_KEY in the environment "
            "or seo/.env on the droplet")
    messages = [{"role": "user", "content": prompt}]
    body = {"model": MODEL, "max_tokens": max_tokens, "system": system,
            "messages": messages}
    if tools:
        body["tools"] = tools
    attempts = (RETRIES if retries is None else retries) + 1

    texts = []
    LAST_STOP_REASON = None
    for _ in range(MAX_CONTINUATIONS + 1):
        resp = _post(body, key, timeout, attempts)
        content = resp.get("content", [])
        texts.extend(b.get("text", "") for b in content
                     if b.get("type") == "text")
        LAST_STOP_REASON = resp.get("stop_reason")
        if LAST_STOP_REASON != "pause_turn":
            return texts
        # Send the paused turn straight back. No "continue" message: the API
        # resumes off the trailing server-tool block, and an extra user turn
        # would restart the model instead of continuing it.
        messages = messages + [{"role": "assistant", "content": content}]
        body = dict(body, messages=messages)
    return texts


def call(system, prompt, **kw):
    """One message round-trip. Returns the concatenated text blocks."""
    return "".join(call_blocks(system, prompt, **kw))


def _salvage(blob):
    """Recover the usable prefix of a JSON object that got cut off mid-array.

    A research reply that hits max_tokens is truncated mid-string, and throwing
    the whole thing away loses a day of scouting over a missing brace. Walk the
    text backwards to the last position where the structure can be legally
    closed, close it, and keep whatever parsed.
    """
    for i in range(len(blob) - 1, 0, -1):
        if blob[i] not in "}]":
            continue
        head = blob[:i + 1]
        # close any array/object still open at this point, ignoring braces
        # that sit inside string literals
        depth, in_str, esc, stack = 0, False, False, []
        for ch in head:
            if esc:
                esc = False
                continue
            if ch == "\\" and in_str:
                esc = True
                continue
            if ch == '"':
                in_str = not in_str
                continue
            if in_str:
                continue
            if ch in "{[":
                stack.append(ch)
            elif ch in "}]" and stack:
                stack.pop()
        candidate = head + "".join("}" if c == "{" else "]" for c in reversed(stack))
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None


# Whitespace, then one of the characters that may legally follow a string.
_AFTER_STRING = re.compile(r'\s*(?:[,:}\]]|$)')


def _repair(blob):
    """Escape the characters a model leaves raw inside a JSON string.

    Prose about gutters quotes things — a 5" K-style profile, a homeowner
    saying "my gutters overflow" — and the model periodically writes that quote
    unescaped. The string ends early, the parser meets a word where it wanted a
    comma, and a whole page goes unwritten over one inch mark. ("Expecting ','
    delimiter: line 1 column 772" is exactly this, and _salvage cannot help:
    truncating back to the last closer throws away the object, not the typo.)

    Walks the text once and escapes any quote that is not followed by a
    delimiter, plus raw control characters, which are illegal in JSON strings.
    """
    out, in_str, i, n = [], False, 0, len(blob)
    while i < n:
        ch = blob[i]
        if not in_str:
            out.append(ch)
            if ch == '"':
                in_str = True
            i += 1
            continue
        if ch == "\\":
            # Keep valid escapes intact; a trailing lone backslash is dropped
            # rather than left to swallow the closing quote.
            if i + 1 < n:
                out.append(ch)
                out.append(blob[i + 1])
                i += 2
            else:
                i += 1
            continue
        if ch == '"':
            if _AFTER_STRING.match(blob, i + 1):
                out.append(ch)
                in_str = False
            else:
                out.append('\\"')
            i += 1
            continue
        if ch in "\n\r\t":
            out.append({"\n": "\\n", "\r": "\\r", "\t": "\\t"}[ch])
        elif ord(ch) < 0x20:
            out.append("\\u%04x" % ord(ch))
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def _extract(text):
    """Every parse strategy, tried against one chunk of text. None if all fail."""
    start, end = text.find("{"), text.rfind("}")
    if start < 0:
        return None
    blob = text[start:end + 1] if end > start else text[start:]
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        pass
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    # Repair first (a stray quote mid-object), then salvage (a reply cut
    # off at max_tokens), then both — truncation and a bad quote co-occur
    # in the same long research replies.
    for candidate in (_repair(blob), _repair(text[start:])):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    for source in (text[start:], _repair(text[start:])):
        rescued = _salvage(source)
        if rescued is not None:
            return rescued
    return None


def _dump_unparsed(blocks):
    """Keep an unparseable reply on disk.

    A scout parse failure used to leave nothing behind, so diagnosing one meant
    paying for another research call to try to reproduce it. Writing the reply
    down makes the next failure free to read.
    """
    try:
        path = os.path.join(DEBUG_DIR, "nemo-llm-unparsed-%d.txt" % time.time())
        with open(path, "w") as f:
            f.write("\n\n----- next text block -----\n\n".join(blocks))
        return path
    except OSError:
        return None


def call_json(system, prompt, **kw):
    """Same, but pull a JSON object out of the reply and parse it.

    The last text block is tried first: with web search on, the earlier blocks
    are the model narrating its research, and a brace in that prose would
    otherwise drag the parse start into the commentary. Earlier blocks and the
    whole joined reply are still tried, so a plain reply behaves as before.
    """
    blocks = call_blocks(system, prompt, **kw)
    if not blocks:
        raise ValueError("no text in reply")
    candidates = list(reversed(blocks))
    joined = "".join(blocks)
    if joined not in candidates:
        candidates.append(joined)
    for text in candidates:
        parsed = _extract(text)
        if parsed is not None:
            return parsed
    path = _dump_unparsed(blocks)
    where = f" (raw reply saved to {path})" if path else ""
    # The stop reason separates the three failures that look identical in the
    # journal: end_turn means the model answered in prose, max_tokens means the
    # budget ran out mid-answer, pause_turn means it is still mid-research and
    # MAX_CONTINUATIONS was too low. Without it every one of them reads as
    # "no parseable JSON object" and costs another paid call to tell apart.
    why = f" [stop_reason={LAST_STOP_REASON}]" if LAST_STOP_REASON else ""
    raise ValueError(
        f"no parseable JSON object in reply{why}{where}: {joined[:300]}")

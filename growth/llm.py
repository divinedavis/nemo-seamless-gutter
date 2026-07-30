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


def _sleep_for(attempt, retry_after=None):
    """Wait before the next attempt. Honours Retry-After when the API sends it."""
    if retry_after:
        try:
            return min(float(retry_after), 120.0)
        except (TypeError, ValueError):
            pass
    base = BACKOFF[min(attempt, len(BACKOFF) - 1)]
    return base + random.uniform(0, base * 0.25)


def call(system, prompt, max_tokens=4000, tools=None, timeout=240, key=None,
         retries=None):
    """One message round-trip. Returns the concatenated text blocks.

    Transient API failures are retried with exponential backoff; the error that
    finally escapes is the last one seen, so the report still names the cause.
    """
    max_tokens = max(max_tokens, MIN_MAX_TOKENS)
    key = key or load_key()
    if not key:
        raise RuntimeError(
            "no Anthropic key — expected ANTHROPIC_API_KEY in the environment "
            "or seo/.env on the droplet")
    body = {"model": MODEL, "max_tokens": max_tokens, "system": system,
            "messages": [{"role": "user", "content": prompt}]}
    if tools:
        body["tools"] = tools
    data = json.dumps(body).encode()
    attempts = (RETRIES if retries is None else retries) + 1

    last = None
    for attempt in range(attempts):
        req = urllib.request.Request(
            API_URL, data=data,
            headers={"content-type": "application/json", "x-api-key": key,
                     "anthropic-version": "2023-06-01"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                resp = json.loads(r.read().decode())
            return "".join(b.get("text", "") for b in resp.get("content", [])
                           if b.get("type") == "text")
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


def call_json(system, prompt, **kw):
    """Same, but pull a JSON object out of the reply and parse it."""
    text = call(system, prompt, **kw)
    start, end = text.find("{"), text.rfind("}")
    if start < 0:
        raise ValueError(f"no JSON object in reply: {text[:300]}")
    blob = text[start:end + 1] if end > start else text[start:]
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
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
        raise

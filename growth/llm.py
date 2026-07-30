#!/usr/bin/env python3
"""Shared Anthropic client for the growth engine.

The key already lives on the droplet in seo/.env (gen_article.py has used it
since June). Nothing here invents a second place to put credentials.
"""
import json
import os
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


# Transient server-side conditions. A 529 ("Overloaded") means the API was busy
# for a moment and says nothing about this account — on 2026-07-30 three of the
# day's eleven techniques, including the scout, died on one apiece and the run
# produced a single page. Retrying these is not the unbounded retry BUDGET.md
# rule 4 forbids, and it does not raise spend: a 529 bills nothing, so the only
# call that costs anything is the one that finally succeeds — the same one unit
# of work the run was always going to pay for.
#
# Deliberately NOT retried: 400 (both billing failures — an empty balance and a
# self-imposed cap are answers, not hiccups, and hammering a cap is how the cap
# gets worse) and 401/403/404.
RETRY_STATUS = {408, 429, 500, 502, 503, 504, 529}
RETRY_BACKOFF = (5, 20)  # seconds before attempt 2 and attempt 3


def call(system, prompt, max_tokens=4000, tools=None, timeout=240, key=None):
    """One message round-trip. Returns the concatenated text blocks."""
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
    headers = {"content-type": "application/json", "x-api-key": key,
               "anthropic-version": "2023-06-01"}

    for attempt, pause in enumerate((None,) + RETRY_BACKOFF):
        if pause is not None:
            time.sleep(pause)
        req = urllib.request.Request(API_URL, data=data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                resp = json.loads(r.read().decode())
            break
        except urllib.error.HTTPError as e:
            detail = f"anthropic {e.code}: {e.read()[:300].decode(errors='replace')}"
            if e.code not in RETRY_STATUS or attempt == len(RETRY_BACKOFF):
                raise RuntimeError(detail)
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt == len(RETRY_BACKOFF):
                raise RuntimeError(f"anthropic unreachable: {e}")
    return "".join(b.get("text", "") for b in resp.get("content", [])
                   if b.get("type") == "text")


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


def _escape_inner_quotes(blob):
    """Escape literal double quotes that appear inside a JSON string value.

    This trade writes 6" and 5" constantly, and a model asked for JSON will
    happily emit {"h2": "5" vs 6" Gutters"} — valid English, invalid JSON. It
    surfaces as `Expecting ',' delimiter` partway through line 1, which is what
    killed strengthen_pages on 2026-07-30 at char 771 and looks like a prompt
    bug rather than a punctuation one.

    _salvage cannot help: it only closes truncated structures, and this blob is
    corrupt in the middle rather than cut off at the end.

    The rule: inside a string, a quote is a closing quote only if the next
    non-space character is one of ,:}] — otherwise it is someone's inch mark.
    """
    out, in_str, esc = [], False, False
    for i, ch in enumerate(blob):
        if esc:
            out.append(ch)
            esc = False
            continue
        if ch == "\\":
            out.append(ch)
            esc = in_str
            continue
        if ch == '"':
            if not in_str:
                in_str = True
            else:
                nxt = re.match(r"\s*(.)", blob[i + 1:])
                if nxt and nxt.group(1) not in ",:}]":
                    out.append("\\")   # an inch mark, not the end of the string
                else:
                    in_str = False
        out.append(ch)
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
        import re
        m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
        try:
            return json.loads(_escape_inner_quotes(blob))
        except json.JSONDecodeError:
            pass
        rescued = _salvage(text[start:])
        if rescued is not None:
            return rescued
        raise

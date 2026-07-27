#!/usr/bin/env python3
"""Shared Anthropic client for the growth engine.

The key already lives on the droplet in seo/.env (gen_article.py has used it
since June). Nothing here invents a second place to put credentials.
"""
import json
import os
import subprocess
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
API_URL = "https://api.anthropic.com/v1/messages"

# Sonnet for prose and research: this content goes on a real business's site
# under its own name, so the floor on quality matters more than the token cost
# of a few pages a week.
MODEL = os.environ.get("NEMO_GROWTH_MODEL", "claude-sonnet-5")

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
    req = urllib.request.Request(
        API_URL, data=json.dumps(body).encode(),
        headers={"content-type": "application/json", "x-api-key": key,
                 "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"anthropic {e.code}: {e.read()[:300].decode(errors='replace')}")
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
        rescued = _salvage(text[start:])
        if rescued is not None:
            return rescued
        raise

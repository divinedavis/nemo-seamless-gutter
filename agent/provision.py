#!/usr/bin/env python3
"""Create or update the NEMO Seamless Gutter phone assistant on ElevenLabs Agents.

The system prompt lives in prompt.md and the facts it is allowed to state live in
knowledge.md; this script splices them together and pushes the result. It also
registers the three webhook tools that let the assistant read the real calendar
and book on the call. It is idempotent throughout: secrets, tools and the agent
are all matched by name and updated in place, so re-running after a prompt edit
just updates what is already live.

    export ELEVENLABS_API_KEY=$(security find-generic-password -a "$USER" -s nemo-elevenlabs -w)
    export NEMO_AGENT_TOKEN=$(security find-generic-password -a "$USER" -s nemo-agent-token -w)
    python3 agent/provision.py            # create or update
    python3 agent/provision.py --dry-run  # print the payload, touch nothing

NEMO_AGENT_TOKEN must match AGENT_TOKEN in server/.env on the droplet; it is what
lets the booking API prove a booking really came from the phone assistant.

Dependency-free (stdlib only), like the rest of the automation in this repo.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.elevenlabs.io/v1"
HERE = Path(__file__).resolve().parent
ID_FILE = HERE / "agent.id"

AGENT_NAME = "NEMO Seamless Gutter — Phone Assistant"

# Sarah: American, mature, reassuring. Reads as a competent front desk rather than
# a chirpy IVR. Swap the id here to change the voice everywhere.
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"

FIRST_MESSAGE = (
    "Thanks for calling NEMO Seamless Gutter, this is the assistant. "
    "How can I help you today?"
)

# Spoken when the call hits the duration cap.
DURATION_MESSAGE = (
    "I'm sorry, I have to let you go — please call us back at "
    "seven one seven, five seven eight, oh oh seven three."
)


def api_key() -> str:
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not key:
        sys.exit(
            "ELEVENLABS_API_KEY is not set. Run:\n"
            '  export ELEVENLABS_API_KEY=$(security find-generic-password '
            '-a "$USER" -s nemo-elevenlabs -w)'
        )
    return key


def request(method: str, path: str, key: str, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(f"{API}{path}", data=data, method=method)
    req.add_header("xi-api-key", key)
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode()
        sys.exit(f"{method} {path} failed: HTTP {e.code}\n{detail}")


SITE = "https://nemoseamlessgutter.com"
SECRET_NAME = "NEMO_AGENT_TOKEN"


def ensure_secret(key: str, value: str) -> str:
    """Store the booking token in ElevenLabs' secret store, return its id."""
    for s in request("GET", "/convai/secrets", key).get("secrets", []):
        if s.get("name") == SECRET_NAME:
            return s["secret_id"]
    created = request(
        "POST", "/convai/secrets", key, {"type": "new", "name": SECRET_NAME, "value": value}
    )
    return created["secret_id"]


def tool_configs(secret_id: str) -> list:
    return [
        {
            "type": "webhook",
            "name": "get_booking_info",
            "description": (
                "Get today's date, the next fourteen days with their weekday names and "
                "whether NEMO is open each day, the bookable service types and their ids, "
                "and the booking rules. Call this ONCE at the start of any conversation "
                "that touches scheduling, before you say or accept any date. Never work "
                "out yourself what date a weekday refers to — read it from this tool."
            ),
            "response_timeout_secs": 10,
            "api_schema": {"url": f"{SITE}/api/services", "method": "GET"},
        },
        {
            "type": "webhook",
            "name": "check_availability",
            "description": (
                "List the real open appointment times on one day for one service. Returns "
                "each open slot with a spoken label like '9:30 AM' and an exact 'start' "
                "value. Offer the caller the labels; keep the matching 'start' value to "
                "pass to book_appointment. An empty list means that day is full — offer "
                "another day."
            ),
            "response_timeout_secs": 15,
            "api_schema": {
                "url": f"{SITE}/api/availability",
                "method": "GET",
                "query_params_schema": {
                    "properties": {
                        "service": {
                            "type": "string",
                            "description": "Service id: 'estimate', 'cleaning' or 'consult'.",
                        },
                        "date": {
                            "type": "string",
                            "description": "The day to check, as YYYY-MM-DD, from get_booking_info.",
                        },
                    },
                    "required": ["service", "date"],
                },
            },
        },
        {
            "type": "webhook",
            "name": "book_appointment",
            "description": (
                "Actually book the appointment on NEMO's calendar and email Eric. Only "
                "call this after the caller has confirmed the day and time back to you, "
                "and you have read their phone number back correctly. This is real — it "
                "puts a job on a working person's calendar, so never call it to test, to "
                "hold a slot, or on a guess."
            ),
            "response_timeout_secs": 30,
            "api_schema": {
                "url": f"{SITE}/api/book",
                "method": "POST",
                "content_type": "application/json",
                "request_headers": {"x-agent-token": {"secret_id": secret_id}},
                "request_body_schema": {
                    "type": "object",
                    "properties": {
                        "service": {
                            "type": "string",
                            "description": "Service id: 'estimate', 'cleaning' or 'consult'.",
                        },
                        "start": {
                            "type": "string",
                            "description": "The exact 'start' value of the chosen slot from check_availability. Copy it verbatim; do not construct it.",
                        },
                        "name": {"type": "string", "description": "Caller's full name."},
                        "phone": {
                            "type": "string",
                            "description": "Callback number, digits only or as spoken, that you read back and they confirmed.",
                        },
                        "address": {
                            "type": "string",
                            "description": "Street address and town of the job. Required for 'estimate' and 'cleaning'; omit for 'consult'.",
                        },
                        "email": {
                            "type": "string",
                            "description": "Email address, only if they offer one. Leave out otherwise.",
                        },
                        "notes": {
                            "type": "string",
                            "description": "What is going on with the gutters, in the caller's own words.",
                        },
                    },
                    "required": ["service", "start", "name", "phone"],
                },
            },
        },
    ]


def ensure_tools(key: str, secret_id: str) -> list:
    existing = {t["tool_config"]["name"]: t["id"] for t in request("GET", "/convai/tools", key).get("tools", [])}
    ids = []
    for cfg in tool_configs(secret_id):
        body = {"tool_config": cfg}
        if cfg["name"] in existing:
            tool_id = existing[cfg["name"]]
            request("PATCH", f"/convai/tools/{tool_id}", key, body)
        else:
            tool_id = request("POST", "/convai/tools", key, body)["id"]
        ids.append(tool_id)
    return ids


def build_prompt() -> str:
    prompt = (HERE / "prompt.md").read_text(encoding="utf-8")
    knowledge = (HERE / "knowledge.md").read_text(encoding="utf-8")
    if "{{KNOWLEDGE}}" not in prompt:
        sys.exit("prompt.md is missing the {{KNOWLEDGE}} placeholder.")
    return prompt.replace("{{KNOWLEDGE}}", knowledge.strip())


def build_config(tool_ids: list | None = None) -> dict:
    return {
        "name": AGENT_NAME,
        "conversation_config": {
            "agent": {
                "prompt": {
                    "prompt": build_prompt(),
                    "tool_ids": tool_ids or [],
                    # Low temperature: this agent quotes a small business's facts
                    # back to real customers. Creativity is a defect here.
                    "temperature": 0.15,
                },
                "first_message": FIRST_MESSAGE,
                "language": "en",
            },
            "tts": {
                "voice_id": VOICE_ID,
                # Flash keeps time-to-first-word low, which matters a lot on a
                # phone call — the caller hears dead air otherwise. Note the API
                # rejects flash v2.5 here: English-language agents must use the
                # English turbo/flash v2 models.
                "model_id": "eleven_flash_v2",
                "stability": 0.5,
                "similarity_boost": 0.8,
                "speed": 1.0,
            },
            "turn": {
                # Callers on a cell in a truck pause a lot; don't talk over them.
                "turn_timeout": 8,
            },
            "conversation": {
                "text_only": False,
                "max_duration_seconds": 600,
            },
        },
    }


def find_existing(key: str) -> str | None:
    if ID_FILE.exists():
        cached = ID_FILE.read_text(encoding="utf-8").strip()
        if cached:
            return cached
    listing = request("GET", "/convai/agents", key)
    for a in listing.get("agents", []):
        if a.get("name") == AGENT_NAME:
            return a.get("agent_id")
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="print the payload and exit")
    args = ap.parse_args()

    if args.dry_run:
        config = build_config()
        prompt_len = len(config["conversation_config"]["agent"]["prompt"]["prompt"])
        print(json.dumps(config, indent=2)[:4000])
        print(f"\n... system prompt is {prompt_len} chars")
        print(f"... {len(tool_configs('<secret>'))} tools: " + ", ".join(t["name"] for t in tool_configs("<secret>")))
        return

    key = api_key()
    token = os.environ.get("NEMO_AGENT_TOKEN", "").strip()
    if not token:
        sys.exit(
            "NEMO_AGENT_TOKEN is not set. Run:\n"
            '  export NEMO_AGENT_TOKEN=$(security find-generic-password '
            '-a "$USER" -s nemo-agent-token -w)'
        )

    tool_ids = ensure_tools(key, ensure_secret(key, token))
    config = build_config(tool_ids)
    prompt_len = len(config["conversation_config"]["agent"]["prompt"]["prompt"])
    existing = find_existing(key)

    if existing:
        request("PATCH", f"/convai/agents/{existing}", key, config)
        agent_id = existing
        action = "updated"
    else:
        created = request("POST", "/convai/agents/create", key, config)
        agent_id = created.get("agent_id")
        action = "created"

    ID_FILE.write_text(agent_id + "\n", encoding="utf-8")
    print(f"{action} agent {agent_id} ({prompt_len} char prompt, {len(tool_ids)} tools)")
    print(f"  dashboard: https://elevenlabs.io/app/agents/{agent_id}")


if __name__ == "__main__":
    main()

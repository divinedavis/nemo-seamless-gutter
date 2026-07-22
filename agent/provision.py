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


# Tool names this script owns. Anything listed here that is no longer in
# tool_configs() gets deleted, so a retired tool doesn't linger in the workspace
# still pointed at a live endpoint. Keep old names here until they're gone.
MANAGED_TOOL_NAMES = {
    "send_message_to_eric",
    # Retired: the assistant must NOT book. It finds out what the customer wants
    # and emails it over; Eric rings them back and sets the time himself. Deleting
    # these rather than leaving them detached is deliberate — a tool sitting in the
    # workspace still points at a live endpoint and can be re-attached by accident.
    "check_openings",
    "book_appointment",
    "get_booking_info",
    "check_availability",
}


def tool_configs(secret_id: str) -> list:
    return [
        {
            "type": "webhook",
            "name": "send_message_to_eric",
            "description": (
                "Send the caller's details to Eric by email so he can call them back and "
                "arrange a time to come out. This is the goal of almost every call. Only "
                "send once you have their name, a callback number you have read back to "
                "them, and roughly when they said they are free. Sending is real — Eric "
                "reads these between jobs — so never send a test, never send twice for "
                "the same caller, and never send for someone who did not ask to be "
                "contacted."
            ),
            "response_timeout_secs": 30,
            "api_schema": {
                "url": f"{SITE}/api/lead",
                "method": "POST",
                "content_type": "application/json",
                "request_headers": {"x-agent-token": {"secret_id": secret_id}},
                "request_body_schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Caller's full name."},
                        "phone": {
                            "type": "string",
                            "description": "The callback number they confirmed when you read it back to them.",
                        },
                        "address": {
                            "type": "string",
                            "description": "Street address and town of the property. Needed for any on-site visit.",
                        },
                        "service": {
                            "type": "string",
                            "description": "What they want, in a few words - e.g. 'free on-site estimate for new seamless gutters', 'gutter cleaning', 'repair, gutters pulling away from the house'.",
                        },
                        "availability": {
                            "type": "string",
                            "description": "When they said they are generally free, in their own words - e.g. 'weekday mornings before eleven, or any time Saturday'. Never convert this into a specific date or appointment time.",
                        },
                        "notes": {
                            "type": "string",
                            "description": "What is going on with the gutters in the caller's own words, plus anything Eric should know before he calls: two storeys, dog in the yard, renting rather than owning, urgency.",
                        },
                        "caller_id": {
                            "type": "string",
                            "description": "The number they are calling from, if you have it. May differ from the callback number they give you.",
                        },
                    },
                    "required": ["name", "phone"],
                },
            },
        },
    ]


def ensure_tools(key: str, secret_id: str) -> tuple:
    """Create/update the tools we want. Returns (wanted_ids, retired_ids).

    Retired tools are returned rather than deleted here: the API refuses to delete
    a tool an agent still references, so the caller must update the agent first.
    """
    existing = {t["tool_config"]["name"]: t["id"] for t in request("GET", "/convai/tools", key).get("tools", [])}
    wanted = tool_configs(secret_id)
    wanted_names = {cfg["name"] for cfg in wanted}

    ids = []
    for cfg in wanted:
        body = {"tool_config": cfg}
        if cfg["name"] in existing:
            tool_id = existing[cfg["name"]]
            request("PATCH", f"/convai/tools/{tool_id}", key, body)
        else:
            tool_id = request("POST", "/convai/tools", key, body)["id"]
        ids.append(tool_id)

    retired = [
        (name, tid)
        for name, tid in existing.items()
        if name in MANAGED_TOOL_NAMES and name not in wanted_names
    ]
    return ids, retired



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

    tool_ids, retired = ensure_tools(key, ensure_secret(key, token))
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

    # Only now that the agent no longer references them can retired tools go.
    for name, tool_id in retired:
        request("DELETE", f"/convai/tools/{tool_id}", key)
        print(f"  removed retired tool {name}")

    ID_FILE.write_text(agent_id + "\n", encoding="utf-8")
    print(f"{action} agent {agent_id} ({prompt_len} char prompt, {len(tool_ids)} tools)")
    print(f"  dashboard: https://elevenlabs.io/app/agents/{agent_id}")


if __name__ == "__main__":
    main()

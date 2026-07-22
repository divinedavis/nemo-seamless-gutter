#!/usr/bin/env python3
"""Create or update the NEMO Seamless Gutter phone assistant on ElevenLabs Agents.

The system prompt lives in prompt.md and the facts it is allowed to state live in
knowledge.md; this script splices them together and pushes the result. It is
idempotent: it finds the agent by name (or by the id cached in agent.id) and
PATCHes it, so re-running after a prompt edit just updates the live agent.

    export ELEVENLABS_API_KEY=$(security find-generic-password -a "$USER" -s nemo-elevenlabs -w)
    python3 agent/provision.py            # create or update
    python3 agent/provision.py --dry-run  # print the payload, touch nothing

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


def build_prompt() -> str:
    prompt = (HERE / "prompt.md").read_text(encoding="utf-8")
    knowledge = (HERE / "knowledge.md").read_text(encoding="utf-8")
    if "{{KNOWLEDGE}}" not in prompt:
        sys.exit("prompt.md is missing the {{KNOWLEDGE}} placeholder.")
    return prompt.replace("{{KNOWLEDGE}}", knowledge.strip())


def build_config() -> dict:
    return {
        "name": AGENT_NAME,
        "conversation_config": {
            "agent": {
                "prompt": {
                    "prompt": build_prompt(),
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

    config = build_config()
    prompt_len = len(config["conversation_config"]["agent"]["prompt"]["prompt"])

    if args.dry_run:
        print(json.dumps(config, indent=2)[:4000])
        print(f"\n... system prompt is {prompt_len} chars")
        return

    key = api_key()
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
    print(f"{action} agent {agent_id} ({prompt_len} char prompt)")
    print(f"  dashboard: https://elevenlabs.io/app/agents/{agent_id}")


if __name__ == "__main__":
    main()

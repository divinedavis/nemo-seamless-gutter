#!/usr/bin/env python3
"""NEMO Seamless Gutter phone assistant — LiveKit worker.

Same behaviour as the ElevenLabs agent, different plumbing. Deepgram listens,
Claude Haiku 4.5 thinks, Speechify simba-3.2 (beatrice_32) speaks.

The system prompt is NOT duplicated here. It is spliced from ../prompt.md and
../knowledge.md exactly the way provision.py does it, so the two agents can
never drift apart. Edit those files; both agents pick the change up.

Run:  python agent.py dev     (local, connects to the self-hosted LiveKit)
      python agent.py start   (production, under pm2)
"""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from pathlib import Path

from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli, function_tool
from livekit.plugins import anthropic, elevenlabs, silero, speechify

log = logging.getLogger("nemo-agent")

HERE = Path(__file__).resolve().parent
AGENT_DIR = HERE.parent

SITE = os.environ.get("NEMO_SITE", "https://nemoseamlessgutter.com")
AGENT_TOKEN = os.environ["AGENT_TOKEN"]  # mirrors server/.env on the droplet

# Verbatim from provision.py:41 — the line callers actually hear first.
FIRST_MESSAGE = (
    "Hi, thanks for calling NEMO Seamless Gutter, this is the assistant. "
    "How can I help you today?"
)


def build_instructions() -> str:
    """Splice prompt.md + knowledge.md — identical logic to provision.py:200."""
    prompt = (AGENT_DIR / "prompt.md").read_text(encoding="utf-8")
    knowledge = (AGENT_DIR / "knowledge.md").read_text(encoding="utf-8")
    if "{{KNOWLEDGE}}" not in prompt:
        raise SystemExit("prompt.md is missing the {{KNOWLEDGE}} placeholder.")
    return prompt.replace("{{KNOWLEDGE}}", knowledge.strip())


class NemoAssistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=build_instructions())

    # 🔒 The ONE tool. The assistant does not book — it takes a message and Eric
    # rings them back. check_openings / book_appointment were deleted from the
    # ElevenLabs workspace on purpose; do not reintroduce them here.
    #
    # phone and availability have no defaults, so the model cannot call this
    # without them — the structural equivalent of `required: [phone, availability]`
    # in the ElevenLabs schema. `name` stays optional on purpose: a required name
    # field is what teaches the model to invent one.
    @function_tool()
    async def send_message_to_eric(
        self,
        phone: str,
        availability: str,
        name: str = "Not given",
        address: str = "",
        service: str = "",
        notes: str = "",
        caller_id: str = "",
    ) -> str:
        """Send the caller's details to Eric by email so he can call them back and
        arrange a time to come out. This is the goal of almost every call. The two
        things Eric actually needs are a CALLBACK NUMBER, read back and confirmed,
        and WHEN THEY ARE GENERALLY FREE — get both. Name, address and what is
        wrong are useful but optional; Eric can ask once he has them on the phone,
        so never lose a caller by holding out for them. Sending is real — Eric
        reads these between jobs — so never send a test, never send twice for the
        same caller, and never send for someone who did not ask to be contacted.

        Args:
            phone: The callback number they confirmed when you read it back to them.
            availability: When they said they are generally free, in their own words.
                Never convert it into a specific date or appointment time, and never
                invent it: if they truly would not say, pass
                'Not given - ask when you call'.
            name: Caller's name. Pass 'Not given' if they did not say it — never invent one.
            address: Street address and town of the property.
            service: What they want, in a few words.
            notes: What is going on with the gutters in the caller's own words, plus
                anything Eric should know before he calls.
            caller_id: The number they are calling from, if you have it.
        """
        payload = json.dumps({
            "name": name, "phone": phone, "address": address, "service": service,
            "availability": availability, "notes": notes, "caller_id": caller_id,
        }).encode()
        req = urllib.request.Request(
            f"{SITE}/api/lead",
            data=payload,
            headers={"Content-Type": "application/json", "x-agent-token": AGENT_TOKEN},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = json.load(r)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            log.error("send_message_to_eric failed: %s", e)
            # Name the failure plainly. The model must not paper over this — an
            # unsent lead reported as sent is the worst outcome on this line.
            return ("FAILED - the message did not send. Tell the caller you are "
                    "having trouble and read them Eric's number: seven one seven, "
                    "five seven eight, zero zero seven three.")

        log.info("lead sent: emailed=%s", body.get("emailed"))
        return body.get("message") or "Sent. Eric will call them back."


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    session = AgentSession(
        # ElevenLabs Scribe, not Deepgram: the ELEVENLABS_API_KEY already exists
        # (keychain nemo-elevenlabs) and already has a bill, so listening costs no
        # new vendor and no new credential. scribe_v2_realtime is the streaming
        # model — scribe_v1/v2 are batch and would add a turn of latency.
        stt=elevenlabs.STT(model="scribe_v2_realtime", language_code="en"),
        # Haiku 4.5, not Opus 5: this is slot-filling plus one tool call, and it
        # has to answer inside a second. Opus 5 thinks by default (latency + cost),
        # and with thinking disabled it can emit tool calls as plain text — the
        # call would "succeed" while send_message_to_eric never fires.
        llm=anthropic.LLM(model="claude-haiku-4-5"),
        tts=speechify.TTS(model="simba-3.2", voice_id="beatrice_32"),
        vad=silero.VAD.load(),
    )

    await session.start(agent=NemoAssistant(), room=ctx.room)
    await session.generate_reply(instructions=f"Say exactly: {FIRST_MESSAGE}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))

# NEMO phone assistant — LiveKit worker (IN PROGRESS, not live)

Rebuild of the phone assistant off ElevenLabs Agents so it can use Speechify's
`simba-3.2` voice. **The ElevenLabs agent on (717) 931-6485 is still the live one.**
Nothing here is serving calls yet.

Why the rebuild: ElevenLabs Agents only allows ElevenLabs voices. simba-3.2 scores
1,229 Elo vs `eleven_flash_v2`'s ≤1,081 — and flash_v2 is what the live agent runs,
because English agents reject flash_v2_5. LiveKit is the only path to that voice.

## Stack

| Layer | Choice | Why |
|---|---|---|
| STT | Deepgram `nova-3` | ~$0.0048/min |
| LLM | **Claude Haiku 4.5** | see below |
| TTS | Speechify `simba-3.2` / `beatrice_32` | voice chosen 2026-07-29 |
| Transport | self-hosted LiveKit + SIP ← Twilio | no LiveKit Cloud account needed |

**Haiku 4.5, not Opus 5, deliberately.** This is slot-filling plus one tool call and
has to answer inside a second. Opus 5 thinks by default (latency + $25/MTok output),
and with thinking disabled it can emit tool calls as *plain text* — the turn succeeds,
the caller is told Eric will ring back, and `send_message_to_eric` never fires. That is
the exact false-promise bug the ElevenLabs simulator caught twice.

## Behaviour is NOT defined here

`agent.py` splices `../prompt.md` + `../knowledge.md` through the same `{{KNOWLEDGE}}`
placeholder `provision.py` uses. One source of truth — edit those files and both agents
pick it up. Do not copy the prompt into this directory; divergent copies are how the
invented-date bug came back.

🔒 Carried over unchanged: the assistant does **not** book. One tool,
`send_message_to_eric` → `POST /api/lead`, with `phone` and `availability` as
required positional args (no defaults) and `name` optional on purpose — a required
name field teaches the model to invent one.

## Verified so far (2026-07-29)

- Speechify key live; `beatrice_32` + `simba-3.2` synthesizes through the plugin.
- `agent.py` imports; prompt splices to 17,081 chars; exactly one tool registered;
  required args are `phone` + `availability`.

## Still to do

1. **Deepgram API key** → keychain `nemo-deepgram`, then `DEEPGRAM_API_KEY` in the env.
2. `apt install redis-server` on the droplet — `livekit-sip` requires it. Not currently
   installed.
3. Install + configure `livekit-server` and `livekit-sip`; generate your own API
   key/secret (self-hosted needs no LiveKit account).
4. UFW: currently only 22/80/443. Needs 7880, 7881, SIP 5060, and a UDP media range.
   ⚠️ This partly reverses the 2026-07-23 hardening on a box serving six live sites.
5. Port the five simulator scenarios (`../README.md`) to LiveKit evals — price
   pressure, out-of-scope trade, prompt injection, out of area, injury. **Do not put
   this on a real number before these pass.**
6. Repoint Twilio `voice_url` from ElevenLabs to the LiveKit SIP trunk. Reversible.

## Known risk on this droplet

1 vCPU, 2 GB RAM, **no swap**, already running six nginx sites and three PM2 apps.
Realtime audio contends with the 6am `nemo-growth` run and `rentmap-scrape`; an OOM
has no swap to fall back on and could take the booking API on :3009 with it. A 2 GB
swapfile is the cheapest mitigation and is not yet in place.

## Run

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
export AGENT_TOKEN=...          # mirrors server/.env on the droplet
export SPEECHIFY_API_KEY=...    # keychain: nemo-speechify
export DEEPGRAM_API_KEY=...     # keychain: nemo-deepgram (not yet created)
export ANTHROPIC_API_KEY=...
.venv/bin/python agent.py dev
```

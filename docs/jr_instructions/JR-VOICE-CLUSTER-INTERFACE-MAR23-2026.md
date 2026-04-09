# JR INSTRUCTION: Voice Cluster Interface — Phone-to-Organism Loop

**Task ID**: VOICE-CLUSTER-001
**Priority**: P1
**SP**: 5
**Assigned Nodes**: redfin (ganudabot), bmasass (Whisper), sasass + sasass2 (voice terminal CLI)
**Council Vote**: Pending (TPM Easy Button — design ratified by Partner Mar 23 2026)
**Related**: DC-10 (no dispatcher pattern), TPM autonomy directives, Medicine Woman MCP

## Context

Partner's role is tie-breaker and idea fairy. The cluster should work autonomously, with Partner in the "outside loop" — reviewing changes, approving tie-breakers, and nudging direction via voice from his phone. No laptop required.

This is NOT a voice assistant. This is a command interface for a sovereign AI federation from a mobile device.

## Architecture: Three Components

### Component 1: Telegram Voice Message → Whisper Transcription (bmasass)

**What**: When @ganudabot receives a voice message (`.ogg` file from Telegram), it forwards to bmasass for Whisper transcription, then processes the transcribed text through the existing ganudabot command pipeline.

**Where**:
- ganudabot on redfin receives voice message via Telegram API
- Forwards audio to bmasass Whisper endpoint for transcription
- Transcribed text re-enters ganudabot's existing message handler

**Implementation**:

1. **Whisper Service on bmasass** — Deploy `whisper.cpp` or `mlx-whisper` (MLX-native, fast on M4 Max) as a simple HTTP endpoint:
   ```
   POST /transcribe
   Body: audio file (ogg/wav/mp3)
   Response: { "text": "transcribed text", "language": "en", "duration_ms": 3200 }
   ```
   - Model: `whisper-large-v3` (MLX quantized) or `whisper-medium` if memory constrained
   - Port: 8802 (next available on bmasass after Qwen3:8800, Llama:8801)
   - Systemd service: `whisper-transcribe.service`

2. **ganudabot voice handler** — In `/ganuda/telegram_bot/`, add voice message handler:
   ```python
   @bot.message_handler(content_types=['voice'])
   async def handle_voice(message):
       # 1. Download .ogg from Telegram
       # 2. POST to bmasass:8802/transcribe
       # 3. Reply with transcription for confirmation
       # 4. Route transcribed text through existing message handler
   ```

3. **Confirmation pattern**: Bot replies with the transcription first: "I heard: '{text}' — processing..." This lets Partner catch mistranscriptions before they become commands.

**Dependencies**:
- bmasass reachable from redfin (Tailscale: 100.103.27.106, confirmed working)
- Telegram bot already handles text commands — voice just adds a transcription step

### Component 2: Outside Loop — Review & Tie-Breaker Channel

**What**: A structured review flow where the organism posts items needing Partner's attention, and Partner can voice-reply to approve/reject/nudge.

**Where**: Existing @ganudabot Telegram chat (no new channels needed — keep it simple)

**Message Types**:

1. **TIE-BREAKER REQUEST** — Council deadlock or confidence < 0.50:
   ```
   🔶 TIE-BREAKER NEEDED
   Vote #abc123 | Confidence: 0.45
   Q: [question]

   Split: Coyote+Turtle say X, Spider+Raven say Y
   Eagle Eye abstained.

   Reply: "go X", "go Y", or "hold"
   ```

2. **REVIEW: Jr Completion** — When a Jr task completes, summary posted:
   ```
   ✅ Jr Task Complete: SKY-MONITOR-001
   Files changed: 2 | Lines: +187 -0
   [one-line summary]

   Reply: "approve", "tweak [what]", or "revert"
   ```

3. **NUDGE RECEIVED** — When Partner sends a voice command that's a suggestion, not a direct order:
   ```
   📝 Nudge logged: "look into whether the stereo pair can triangulate fireball altitude"
   Routed to: Council (next dawn mist) + Kanban (backlog)
   ```

**Implementation**:
- Add `review_router.py` to ganudabot — classifies Partner responses and routes:
  - "go [X]" / "approve" → execute
  - "hold" → park in review queue, revisit at dawn mist
  - "tweak [description]" → create Jr instruction from voice description
  - Free-form text → thermalize as nudge, route to council

### Component 3: Voice Terminal CLI on sasass + sasass2

**What**: Install a voice-to-terminal tool on the Mac nodes so Partner (or the organism) can speak commands locally when at the desk.

**Where**: sasass (192.168.132.241) and sasass2 (192.168.132.242), both macOS

**Tool**: `hear` (https://github.com/sveinbjornt/hear)
- Uses macOS built-in speech recognition — no external API, no cloud, sovereign
- CLI: `hear -i en` starts listening, outputs text to stdout
- Can pipe to any command: `hear -i en | ganuda-cli`
- Native macOS, zero dependencies beyond Xcode command line tools

**Installation**:
```bash
# On sasass and sasass2:
brew install hear  # if available, otherwise:
git clone https://github.com/sveinbjornt/hear.git
cd hear && make && sudo make install
```

**Integration with cluster**:
- Create `/ganuda/scripts/voice_command.sh` — wrapper that:
  1. Runs `hear` for voice capture
  2. Pipes transcription to ganudabot API or directly to consultation ring (:9400)
  3. Speaks response back via `say` (macOS built-in TTS)
- This gives Partner a local voice loop on the Mac nodes: speak → hear → process → say response

**Phase 2**: Wire `hear` output into Claude Code sessions on sasass/sasass2 for voice-driven coding.

## What NOT To Do

- Do NOT build a custom mobile app — Telegram IS the app
- Do NOT add authentication layers — Telegram chat ID is the auth (already verified in ganudabot)
- Do NOT make the organism wait for Partner — autonomy continues, review is async
- Do NOT transcribe on redfin — keep GPU free for vLLM/YOLO, use bmasass M4 Max for Whisper
- Do NOT create new Telegram channels/groups — keep it in the existing ganudabot DM

## Deployment Order

1. **Whisper endpoint on bmasass** (1 SP) — the transcription engine
2. **ganudabot voice handler** (1 SP) — wire voice messages to Whisper → existing pipeline
3. **Review router in ganudabot** (2 SP) — tie-breaker/review/nudge message classification
4. **`hear` on sasass + sasass2** (1 SP) — local voice terminal for desk work

Steps 1-2 give Partner voice-from-phone immediately. Step 3 adds the structured review loop. Step 4 adds local voice at the desk.

## Success Criteria

- [ ] Partner sends voice message to @ganudabot, receives transcription confirmation + response
- [ ] Whisper transcription < 3 seconds for a 30-second voice note
- [ ] Tie-breaker requests posted with clear options and one-word reply pattern
- [ ] Partner voice-replies "go with Coyote" and the pipeline executes
- [ ] Nudges thermalized and routed to council
- [ ] `hear` installed and functional on sasass + sasass2
- [ ] `voice_command.sh` wrapper pipes hear → cluster → say on Mac nodes
- [ ] Full loop: Partner speaks into phone → organism acts → Partner reviews result via voice

## Design Principles

- **Async by default**: Partner reviews when Partner reviews. The organism doesn't block.
- **Voice-first, text-fallback**: Everything that works by voice also works by typing.
- **Sovereign transcription**: Whisper runs on our hardware. No cloud STT.
- **Confirmation before action**: Transcription shown before executing. Mistranscriptions caught early.
- **The organism is not a secretary**: It works autonomously. This interface is for steering, not commanding.

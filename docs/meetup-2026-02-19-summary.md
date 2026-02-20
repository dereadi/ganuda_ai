# Meeting Summary: AI, VetAssist, etc.
**Date**: February 19, 2026, 11:52 CST
**Duration**: ~1hr 35min recorded (meeting was ~5hrs, not all recorded)
**Participants**: Darrell (host/TPM), Joe (veteran, 30% VA disability), Maik (homelab/5090s/n8n, listed as "Michael" on Google Meet)
**Transcription**: mlx-whisper large-v3-turbo on bmasass M4 Max (179 seconds)

---

## Key Discussion Topics

### 1. NVIDIA Persona Plex (Mike, 00:01-00:04)
- Real-time multimodal audio model that listens while talking (can be interrupted naturally)
- Produces natural filler words ("um", "you know") during thinking
- Mike's vision: tie Persona Plex into a larger reasoning model — voice front-end sends complex queries to 72B+ backend, reads results back conversationally
- Current TTS/STT too slow; Persona Plex is real-time, especially on 5090
- Not yet running — wants to integrate with n8n workflows

### 2. Maik's Homelab & Image Generation (00:04-00:20)
- **Hardware**: Two RTX 5090s (32GB each), AMD machines with 128GB shared memory, Samsung 9100 Pro 8TB NVMe, WD Blue 2TB on S1 nodes
- **Image generation**: ComfyUI with Z Image Turbo ("blows everything else out of the water" vs SD1.5, Pony, Flux), exported as API JSON for Open WebUI integration
- **Model management challenge**: ComfyUI holds models in memory indefinitely; needs idle timeout (10min) to auto-unload. SwarmUI does this automatically
- **Performance**: 5090 generates images in <5 seconds when model hot; 30s overhead to reload
- **Qwen 3.5**: Wants integrated VLM+coding+conversation in one model; 1-bit quant fits on single node, waiting for 4-bit safetensor release for vLLM
- **n8n Personal Assistant**: Telegram + webhook entry points, gatekeeper filtering, voice-to-text pipeline, research tools (Wikipedia, Hacker News, SearXNG, OpenWeatherMap), calculator, thinking model toggle
- **Cluster**: ~$20K spent in 2025 on hardware; Docker on every box for MCP servers

### 3. Thermal Memory System Explained (00:27-00:29)
- Darrell explained thermal memory to Joe and Mike:
  - Current conversation = 100 degrees (hot)
  - Degrades over time (95, 90, etc.)
  - Segments of conversations can stay hot while the whole conversation goes cold
  - Breadcrumbs provide persistent trail

### 4. VetAssist Live Demo & Testing (00:29-01:28)
- **Frontend issues**: CSS/styling broken on external access; hard refresh (Cmd+Shift+Delete) fixed it
- **Account creation**: Working — Joe was able to create account and start chatting
- **Chat working**: Joe asked about VA disability claims; deliberation step visible in responses
- **Persistent chat history**: Confirmed — chats saved on left sidebar, persists across sessions
- **Page load speed**: Needs improvement — Darrell noted "I've got to set up my web servers to make that faster"
- **FreeIPA sudo**: Tribe has sudo permissions on certain services through FreeIPA (not full system control)

### 5. Joe's VA Disability Situation (01:09-01:13)
**Current Rating**: 30% combined (VA math, not simple addition)
- **Service-connected (4 conditions, 10% each)**:
  1. Left lower extremity radiculopathy
  2. Lumbar strain with degenerative disc disease
  3. Left shoulder internal derangement
  4. Left knee internal derangement

- **Denied conditions (3)**:
  1. **Bilateral hearing loss** — denied despite being an aviation mechanic
  2. **Bilateral wrists** — denied because rollerblading fall documented in records, even though wrist damage was pre-existing from turning wrenches
  3. **Left ankle** — denied despite falling off an aircraft

- **Nexus argument for wrists**: Joe's wrists were already damaged from service (aviation mechanic, turning wrenches); the rollerblading incident aggravated pre-existing service-connected damage. Strong secondary service connection argument.

### 6. Military Records Request (01:00-01:18)
- Joe submitted EVETREX request through National Archives for military medical records
- Records not in digital OMPF — physical records being mailed
- 10-day processing window before status check available
- DD-214 was requested separately ~10 years ago
- **Action needed**: Wait for physical records, then scan/digitize for VetAssist upload

### 7. Claude Code vs OpenClaw (00:33-00:34)
- Darrell using Claude Code to build systems; Joe interested in same approach
- Maik considering OpenClaw but concerned about "bloat and risk"
- Consensus: Claude Code approach preferred — "love the concept [of OpenClaw], don't want to mess with the bloat"
- Darrell's approach: "an abstraction back where you just tell it what you want and trust the process — hands off, step away"

### 8. Meeting Platform Discussion (01:12-01:15)
- Google Meet UX frustrations: can't hide own screen while presenting, screen sharing quirks
- Zoom Pro pricing: $150/year for one user, $543 for more licenses
- Google Meet app for Mac: no official standalone app from Google in App Store

---

## Action Items

| # | Owner | Action | Priority | Notes |
|---|-------|--------|----------|-------|
| 1 | Joe | Wait for physical military records from EVETREX, then scan/digitize | HIGH | 10-day processing, then mailed |
| 2 | Joe | Use VetAssist calculator to understand VA math (4x10% = 30%) | MEDIUM | Calculator works without login |
| 3 | Joe | Explore secondary service connection argument for bilateral wrists | MEDIUM | Rollerblading fall aggravated pre-existing service damage |
| 4 | Darrell | Improve VetAssist web server performance (page load speed) | MEDIUM | Frontend slow on initial load |
| 5 | Darrell | Fix VetAssist CSS/styling issues on external access | MEDIUM | Required hard refresh to load properly |
| 6 | Darrell/Joe | Tentative work day Tuesday next week | LOW | Darrell rides motorcycle to Indian dealer for service, then work at Joe's |

---

## VetAssist Observations (from live testing)
- Chat endpoint functional with council deliberation
- Persistent session/history working
- Account creation flow working
- CSS/styling needs attention for external access
- Page load performance needs web server optimization
- Guardrail patterns recently hardened (same session, prior to meeting)

---

## Maik's Architecture (for reference)
- **n8n** (Docker on "Jill"): Core automation, Telegram bot, webhook API
- **Open WebUI** (Jill): Chat interface, ComfyUI image gen integration
- **ComfyUI** (on "Jack"): Image/video generation with Z Image Turbo
- **Supporting**: PostgreSQL, Redis, Qdrant, Grafana+InfluxDB, ChatterBox TTS, Whisper STT
- **Search**: SearXNG self-hosted
- **No durable memory yet** — hasn't figured that out; aware of Federation's thermal memory approach

---

*Transcribed by mlx-whisper large-v3-turbo on bmasass M4 Max (179s)*
*Summarized by Cherokee AI Federation TPM*

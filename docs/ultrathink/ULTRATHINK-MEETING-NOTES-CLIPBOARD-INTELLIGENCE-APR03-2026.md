# ULTRATHINK: Meeting Notes Extractor + Clipboard Intelligence

**Date**: April 3, 2026
**Triggered By**: Partner's flow state — "the middle two have a more immediate use for the non-techie folks"
**Context**: SAG Platform Tier 1 products. Council APPROVED three-tier strategy (#d246c53266c14d4c, 12-0-1)
**Sprint**: MOCHA — Make Our Cluster Hot Again
**Position in Catalog**: Products #3 and #4 (after Trimmer and Security Canary)

---

## 1. THE INSIGHT

The Subscription Trimmer and Desktop Security Canary are tools for people who already know they have a problem. They're powerful but they require a degree of technical self-awareness — you have to think "I should check my subscriptions" or "I should scan my machine."

The next two products flip that. They solve problems people don't realize they have. Everyone sits in meetings. Everyone copy-pastes. Nobody has a tool that makes those activities intelligent, searchable, and connected — because the existing tools all require you to send your data to someone else's cloud.

**The non-technical bar**: "My mom could use this." If the tool doesn't pass that test, it's not Tier 1 distribution material.

**The sovereign bar**: "Your meeting audio / clipboard contents never leave your machine." Every competitor (Otter.ai, Fireflies.ai, Alfred, Paste, Ditto) sends your data to the cloud. We don't.

---

## 2. PRODUCT A: MEETING NOTES EXTRACTOR — "What Did We Decide?"

### 2.1 The Problem

People sit in meetings for hours. They take terrible notes. They forget action items by the time they get back to their desk. They lose track of who said what and when. They have the same meeting again because nobody remembers what was decided.

Enterprise tools (Otter.ai, Fireflies.ai, Microsoft Copilot in Teams) solve this by recording everything and sending it to cloud servers for transcription and analysis. This means:
- Your confidential business conversations live on someone else's infrastructure
- Sensitive discussions about personnel, strategy, legal matters are being processed by third-party AI
- You have no control over retention, training data usage, or who accesses the transcripts
- You're paying $16-30/month per seat for the privilege

### 2.2 Our Solution

Record system audio locally → Whisper transcribes on local hardware → Local LLM extracts structured output → Nothing leaves your machine.

**Output structure** (what the user gets after every meeting):

```json
{
  "meeting": {
    "title": "Q2 Planning Review",
    "date": "2026-04-03",
    "duration_minutes": 47,
    "participants_detected": ["Speaker 1", "Speaker 2", "Speaker 3"]
  },
  "summary": "Three-paragraph summary of the meeting",
  "decisions": [
    {
      "decision": "Approved the Q2 budget with 10% increase",
      "decided_by": "Speaker 1",
      "timestamp": "00:12:34"
    }
  ],
  "action_items": [
    {
      "task": "Send revised proposal to client by Friday",
      "assigned_to": "Speaker 2",
      "deadline": "2026-04-04",
      "timestamp": "00:23:17"
    }
  ],
  "key_topics": [
    {
      "topic": "Budget allocation",
      "duration": "12 minutes",
      "sentiment": "positive"
    }
  ],
  "follow_ups": [
    "Schedule follow-up meeting for Monday to review client response"
  ],
  "full_transcript": "..."
}
```

### 2.3 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  AUDIO CAPTURE                                               │
│  PulseAudio/PipeWire monitor (Linux) or BlackHole (macOS)   │
│  Captures system audio + microphone → WAV chunks            │
└──────────────────────┬──────────────────────────────────────┘
                       │ WAV chunks (30-second segments)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  WHISPER TRANSCRIPTION                                       │
│  whisper-large-v3 on sasass (or redfin GPU)                 │
│  Streaming transcription with speaker diarization           │
│  Output: timestamped text segments with speaker labels      │
└──────────────────────┬──────────────────────────────────────┘
                       │ Timestamped transcript
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  LLM EXTRACTION                                              │
│  Qwen2.5-72B on redfin vLLM (or Gemma 4 4B for speed)      │
│  Structured prompt → JSON output                             │
│  Extracts: summary, decisions, action items, topics, moods  │
└──────────────────────┬──────────────────────────────────────┘
                       │ Structured JSON
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  OUTPUT                                                      │
│  HTML report (like Security Canary — single file, dark theme)│
│  JSON export (for SAG integration)                           │
│  Markdown (for pasting into docs/email)                      │
│  Notification: "Meeting notes ready — 3 action items found" │
└─────────────────────────────────────────────────────────────┘
```

### 2.4 What Already Exists

| Component | Status | Location |
|-----------|--------|----------|
| Whisper model | Installed on sasass | `/Users/Shared/ganuda/models/whisper` |
| Audio Jr | Running on redfin | `jr_status`: Audio Jr, whisper-large-v3 |
| vLLM (Qwen2.5-72B) | Running on redfin | Port 8000 |
| HTML report template | Built for Security Canary | Reusable pattern |
| FastAPI serving | Built for Trimmer + Stoneclad API | Reusable pattern |
| DMZ deployment | Proven pipeline | owlfin via sudo tee + systemctl |

### 2.5 What Needs To Be Built

1. **Audio capture module** — PulseAudio/PipeWire monitor source on Linux, BlackHole loopback on macOS. Segments audio into 30-second WAV chunks for streaming transcription.

2. **Whisper client** — sends WAV chunks to Whisper (local on sasass or API on redfin). Returns timestamped text with speaker labels. Speaker diarization via pyannote or whisperx.

3. **Extraction prompt** — structured LLM prompt that takes full transcript and returns the JSON schema above. This is the value layer — not just transcription but INTELLIGENCE about what was said.

4. **Report generator** — HTML + Markdown + JSON output. Action items highlighted. Decisions in boxes. Timeline on the side.

5. **CLI runner** — `python3 meeting_notes.py --record` starts recording. `Ctrl+C` or `--stop` ends recording and triggers processing. `--file audio.wav` processes existing audio.

6. **Tray app** (stretch) — system tray icon: click to start/stop recording. Green = recording. Red = processing. Blue = ready.

### 2.6 SAG Bridge

When SAG is live (Tier 2), meeting notes feed into the assistant:
- "What did we decide about the Q2 budget?" → SAG searches meeting notes
- "What action items are overdue?" → SAG tracks across meetings
- "Summarize all meetings this week" → SAG aggregates
- Meeting topics get thermal memory temperature — topics that come up repeatedly get hotter

### 2.7 The Competitive Edge

| Competitor | Price | Cloud Required | Training on Your Data |
|-----------|-------|---------------|----------------------|
| Otter.ai | $16/mo | Yes | Unclear |
| Fireflies.ai | $18/mo | Yes | "May use for improvement" |
| Microsoft Copilot | $30/mo | Yes (M365) | "Processed in Azure" |
| Grain | $19/mo | Yes | Yes (for features) |
| **Meeting Notes Extractor** | **Free** | **No** | **No — runs locally** |

### 2.8 Build Estimate

- Audio capture + Whisper client: 4-6 hours
- Extraction prompt + LLM integration: 2-3 hours
- Report generator: 2-3 hours
- CLI runner: 1-2 hours
- Testing with real meetings: 2-3 hours
- Deploy to DMZ as demo: 1-2 hours

**Total: ~2 days. Same cadence as Trimmer and Canary.**

---

## 3. PRODUCT B: CLIPBOARD INTELLIGENCE — "What Did I Copy?"

### 3.1 The Problem

Everyone copy-pastes dozens of times a day. URLs, code snippets, addresses, phone numbers, quotes, passwords, error messages, tracking numbers. By the end of the day, you can't find what you copied 3 hours ago. You re-Google the same thing. You re-copy the same snippet. You lose the URL you meant to save.

Existing clipboard managers (Alfred, Paste, Ditto, Maccy, CopyQ) solve the history problem. But they're dumb — they store everything as flat text with timestamps. No classification. No search by meaning. No "show me all the URLs I copied today" or "what was that error message from this morning?"

And the cloud-syncing ones (Windows Clipboard History synced to Microsoft, some Alfred workflows) send your clipboard to servers. Your clipboard contains passwords, API keys, personal messages, medical information, financial data. Sending that to a cloud service is a security liability that would make Crawdad lose sleep.

### 3.2 Our Solution

A background daemon that monitors the clipboard, classifies every entry with a local LLM, temperature-scores it based on usage frequency, and provides a searchable interface.

**Classification schema:**

```json
{
  "clip_id": "abc123",
  "content": "https://natesnewsletter.substack.com/p/your-ai-credentials...",
  "timestamp": "2026-04-03T14:23:17",
  "classification": {
    "type": "url",
    "subtype": "article",
    "domain": "substack.com",
    "tags": ["ai", "career", "skills"],
    "sensitivity": "low"
  },
  "temperature": 72.5,
  "access_count": 3,
  "last_accessed": "2026-04-03T16:45:00",
  "source_app": "Brave Browser",
  "is_sensitive": false
}
```

**Types the LLM classifies:**

| Type | Examples | Sensitivity |
|------|----------|-------------|
| url | Web links, API endpoints | Low |
| code | Code snippets, commands, queries | Low-Medium |
| credential | Passwords, API keys, tokens | HIGH — flag and encrypt |
| address | Physical addresses, email addresses | Medium |
| phone | Phone numbers | Medium |
| text | Notes, quotes, messages | Low |
| number | Tracking numbers, order IDs, account numbers | Medium |
| error | Error messages, stack traces | Low |
| image_ref | File paths to images | Low |
| json | JSON/YAML/XML data | Low-Medium |

### 3.3 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  CLIPBOARD MONITOR DAEMON                                    │
│  Polls clipboard every 500ms (or hooks into OS events)      │
│  Deduplicates (same content within 5 seconds = skip)        │
│  Stores raw content + timestamp + source app                │
└──────────────────────┬──────────────────────────────────────┘
                       │ New clipboard entry
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  FAST CLASSIFIER (regex-first, LLM-second)                   │
│  Step 1: Regex — URLs, emails, phone numbers, JSON, code    │
│          patterns. Handles 70% of clips without LLM cost.   │
│  Step 2: LLM — only for ambiguous content. Classifies type, │
│          tags, sensitivity. Batched every 30 seconds.        │
│  Step 3: Sensitivity gate — credentials auto-encrypted,     │
│          never stored in plain text.                         │
└──────────────────────┬──────────────────────────────────────┘
                       │ Classified clip
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  THERMAL CLIPBOARD STORE                                     │
│  SQLite (local, portable, no server needed)                  │
│  Temperature scoring: access_count × recency weight         │
│  Hot clips: accessed frequently, stay at top                │
│  Cold clips: not accessed in 7 days, archived               │
│  Sensitive clips: encrypted at rest (Fernet AES)            │
│  Retention: 30 days active, then archive                    │
└──────────────────────┬──────────────────────────────────────┘
                       │ Searchable history
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  INTERFACE (multiple options)                                 │
│  CLI: `clip search "API endpoint"` — keyword/semantic search│
│  Hotkey: Ctrl+Shift+V — smart paste menu with recent clips  │
│  Web: localhost:8502 — full searchable dashboard             │
│  API: GET /clips?type=url&today=true                         │
└─────────────────────────────────────────────────────────────┘
```

### 3.4 The Thermal Memory Connection

This is thermal memory at desktop scale. The exact same pattern:

| Thermal Memory (Stoneclad) | Clipboard Intelligence |
|---------------------------|----------------------|
| 96,000+ memories | Thousands of clipboard entries |
| Temperature scoring (0-100°C) | Temperature scoring (access frequency × recency) |
| Sacred memories (never decay) | Pinned clips (user-marked important) |
| Cold memories pruned (forgetting daemon) | Old clips archived after 30 days |
| CRAG validation | Sensitivity gate (credentials detected → encrypted) |
| HyDE-enhanced search | Semantic search across classified clips |

When we explain Stoneclad to non-technical people, Clipboard Intelligence IS the metaphor. "Your clipboard works like our AI's memory — things you use often stay hot, things you forget cool off, and sensitive things are always encrypted."

### 3.5 What Needs To Be Built

1. **Clipboard monitor daemon** — Python, cross-platform (pyperclip or platform-specific APIs). Polls every 500ms. Deduplicates. Records source app if detectable.

2. **Fast classifier** — regex-first for known patterns (URLs, emails, JSON, code). LLM-second for ambiguous content. Batched classification every 30 seconds to avoid hammering vLLM with every copy.

3. **Sensitivity gate** — detects passwords, API keys, tokens, SSH keys via regex patterns. Auto-encrypts with Fernet. Flags in UI. NEVER stores credentials in plain text.

4. **Thermal clipboard store** — SQLite database. Temperature calculation: `temp = access_count * 10 + recency_bonus`. Recency bonus decays daily. Archive after 30 days inactive.

5. **Search engine** — keyword search over content + tags. Semantic search via local embedding if available. Filter by type, date, sensitivity, temperature.

6. **CLI interface** — `clip search "substack"`, `clip list --today --type=url`, `clip pin <id>`, `clip clear --sensitive`.

7. **Hotkey daemon** (stretch) — system-wide Ctrl+Shift+V opens a smart paste menu showing recent clips categorized by type. Click to paste.

8. **Web dashboard** — localhost:8502, dark theme matching ganuda.us. Cards for recent clips. Search bar. Type filters. Temperature bar showing hot vs cold.

### 3.6 SAG Bridge

When SAG is live:
- "What was that URL I copied this morning?" → SAG searches clipboard history
- "Show me all the code I've been working with today" → filtered by type=code
- Clipboard context feeds into SAG's understanding of what you're working on RIGHT NOW
- Cross-meeting integration: copied text from a meeting chat → linked to meeting notes
- Cross-device: copy on your laptop, SAG holds it, paste on your phone (via WireGuard mesh, sovereign)

### 3.7 The Competitive Edge

| Competitor | Price | Cloud Sync | LLM Classification | Sovereign |
|-----------|-------|-----------|--------------------|-----------| 
| Alfred (Mac) | $34 once | Optional | No | Partially |
| Paste (Mac) | $4/mo | iCloud | No | No |
| Ditto (Windows) | Free | Optional | No | Yes (local) |
| CopyQ (Linux) | Free | No | No | Yes (local) |
| **Clipboard Intelligence** | **Free** | **No** | **Yes (local LLM)** | **Yes** |

Nobody else does LLM classification of clipboard content. Nobody else does temperature-scored retrieval. Nobody else detects and encrypts sensitive clips automatically. We're the only one that treats your clipboard as a knowledge base instead of a dumb FIFO buffer.

### 3.8 Build Estimate

- Clipboard monitor daemon: 2-3 hours
- Fast classifier (regex + LLM): 3-4 hours
- Sensitivity gate: 1-2 hours
- Thermal store (SQLite): 2-3 hours
- CLI interface: 2-3 hours
- Web dashboard: 2-3 hours
- Testing + demo data: 2-3 hours

**Total: ~2-3 days. Same cadence.**

---

## 4. CONVERGENCE — WHY THESE TWO TOGETHER

The Meeting Notes Extractor captures what happens in meetings.
Clipboard Intelligence captures what happens between meetings.
Together, they cover the full working day of a knowledge worker.

**The combined story for SAG:**
"Your assistant knows what was decided in your meetings, tracks who owes what, and remembers everything you've been working with today — because it watched your meetings and your clipboard. All on your machine. Nothing in the cloud."

That's not a tool suite. That's a **work memory** that runs locally. And that's exactly what SAG becomes — the intelligent layer that connects the work memory (meetings + clipboard + files + email) into a coherent assistant.

---

## 5. CONNECTIONS TO THE FRAMEWORK

### Dera/Derq
The clipboard is the smallest unit of cognitive capture — the thing you thought was important enough to copy. Meeting notes are the shared cognitive capture — what a group thought was important enough to say. Both are instantiations of attention, and attention is the mechanism by which Dera interacts with the world. Tools that capture and organize attention are tools that make Dera more coherent.

### Thermal Memory
Both products ARE thermal memory at human scale. The conceptual bridge between "96,000 temperature-scored memories in PostgreSQL" and "your clipboard history sorted by how often you use things" is zero. It's the same pattern. One is for the federation, the other is for you.

### The Bitter Lesson
Both products specify WHAT (capture and classify) and let the LLM figure out HOW. The extraction prompt doesn't tell the LLM how to summarize a meeting. It tells the LLM what to extract (decisions, actions, topics) and lets the model's intelligence handle the rest. As models get better, the same prompt produces better extraction. The product improves without code changes.

### Chiral Validation
Meeting notes extracted by the LLM should be validated by the human before action items are assigned. Clipboard sensitivity detection should be validated by the user before credentials are deleted. Neither tool acts unilaterally on sensitive decisions — the other hand always confirms.

### Energy Capacitor
Both products are designed for the Partner's rhythm. During a high-energy day, they capture everything. During a low-energy day, the searchable history means nothing is lost. The tools buffer cognitive output the same way the kanban buffers creative output.

---

## 6. RISK ANALYSIS (Pre-Coyote)

1. **Audio recording consent** — recording meetings without consent is illegal in many jurisdictions. The tool MUST show clear recording indicator. Default: record only your own microphone, not system audio. System audio capture requires explicit user action.

2. **Clipboard sensitivity** — even with encryption, storing clipboard history is a target. The sensitivity gate must be aggressive — better to flag a false positive than miss a real credential.

3. **Performance** — clipboard monitoring daemon must be invisible. <1% CPU. No perceptible delay when copying. The 500ms poll with dedup handles this. LLM batching every 30 seconds prevents GPU thrashing.

4. **Scope creep** — both products are simple. Don't add meeting scheduling, don't add clipboard sharing, don't add integrations. Ship the core. SAG handles the integrations later.

5. **Storage** — meeting audio files are large. Whisper transcription should run, then audio can be deleted or archived. Clipboard store should auto-prune after 30 days. Don't fill the user's disk.

---

## 7. IMPLEMENTATION SEQUENCE

### Week 1 (if starting now):
- **Day 1-2**: Meeting Notes Extractor core (audio capture + Whisper + extraction)
- **Day 2-3**: Meeting Notes report + CLI + deploy demo
- **Day 3-4**: Clipboard Intelligence core (monitor + classifier + store)
- **Day 4-5**: Clipboard CLI + web dashboard + deploy demo

### Deliverables:
- `ganuda.us/meeting-notes` — demo with a real transcribed meeting
- `ganuda.us/clipboard` — demo showing classified clipboard history
- `github.com/dereadi/meeting-notes-extractor` — open source
- `github.com/dereadi/clipboard-intelligence` — open source
- Two Substack posts
- Two LinkedIn posts
- Two more entries in the product catalog on ganuda.us

### After both ship:
The product catalog is: Trimmer, Canary, Meeting Notes, Clipboard Intelligence. Four free sovereign tools. Each one a distribution channel for SAG. Each one proving the thermal memory pattern works at human scale. Each one open source, live demo, blogged, and LinkedIn'd.

That's when SAG gets its public face. "You've been using our free tools. Want the brain that connects them all?"

---

## 8. THE LINE

Nate Jones: "Building agents is 80% plumbing and 20% model."

These products are the 80%. Audio capture, clipboard monitoring, text classification, structured extraction, HTML reports, CLI tools. Boring. Essential. The plumbing that makes intelligence useful.

The 20% — the LLM, the council, the thermal memory — that's already built. It's been running for 11 months. These products just point it at new problems.

**The platform isn't being built. It's being revealed.**

---

*"What if we built a bunch of useful products for desktop apps that link to an assistant?"*

*That's the whole play. Free tools, sovereign processing, thermal memory everywhere, SAG as the brain.*

*The flywheel starts with products people can touch.*

*For Seven Generations.*

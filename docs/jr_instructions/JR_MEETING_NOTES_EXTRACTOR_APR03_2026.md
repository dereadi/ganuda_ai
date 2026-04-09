# Jr Build Instruction: Meeting Notes Extractor — "What Did We Decide?"

## Priority: P1 — MOCHA Product Sprint, Product #3
## Date: April 3, 2026
## Requested By: Partner + TPM
## Target: Ship in 2-3 days
## Ultrathink: /ganuda/docs/ultrathink/ULTRATHINK-MEETING-NOTES-CLIPBOARD-INTELLIGENCE-APR03-2026.md

---

## What We're Building

Record a meeting locally, transcribe with Whisper, extract decisions/action items/topics with LLM. Nothing leaves the machine.

**Non-techie bar: "My mom could use this."**

## Phase 1: Core Pipeline (Day 1)

### Task 1A: Audio Capture Module

Build `/ganuda/products/meeting-notes/audio_capture.py`:

- Capture system audio via PulseAudio/PipeWire monitor source (Linux)
- Also capture microphone input
- Save as WAV chunks (30-second segments) for streaming transcription
- CLI: `python3 audio_capture.py --start` begins recording, `Ctrl+C` stops
- Also accept pre-recorded file: `--file meeting.wav`
- Use `sounddevice` or `pyaudio` library
- Print recording status to stdout every 10 seconds

### Task 1B: Whisper Transcription Client

Build `/ganuda/products/meeting-notes/transcriber.py`:

- Send WAV audio to Whisper for transcription
- Whisper model at: sasass (192.168.132.241) or use local whisper.cpp/faster-whisper
- If using remote Whisper, SSH tunnel or direct API call
- If local: use `faster-whisper` library (pip install faster-whisper)
- Output: timestamped text segments
- Speaker diarization if available (whisperx or pyannote)
- Return format:
```python
[
    {"start": 0.0, "end": 5.2, "text": "Let's start with the Q2 budget review", "speaker": "Speaker 1"},
    {"start": 5.3, "end": 12.1, "text": "I think we should increase by 10 percent", "speaker": "Speaker 2"},
]
```

### Task 1C: LLM Extraction

Build `/ganuda/products/meeting-notes/extractor.py`:

- Takes full transcript, sends to local vLLM (http://localhost:8000/v1/chat/completions)
- **USE THE VLLM TEMPLATE AT /ganuda/lib/jr_templates/vllm_client/** (when available) or copy pattern from /ganuda/products/subscription-trimmer/classifier.py
- System prompt extracts structured JSON:
  - Summary (3 paragraphs max)
  - Decisions (what, who decided, timestamp)
  - Action items (task, assigned to, deadline, timestamp)
  - Key topics (topic name, duration, sentiment)
  - Follow-ups (next steps)
- Parse JSON from LLM response (handle markdown code blocks)
- Model: /ganuda/models/qwen2.5-72b-instruct-awq

## Phase 2: Report + CLI (Day 2)

### Task 2A: Report Generator

Build `/ganuda/products/meeting-notes/report.py`:

- Generate single-file HTML report (ganuda.us dark theme — copy from Trimmer templates)
- Sections: Meeting Info, Summary, Decisions (boxed), Action Items (checklist), Topics, Full Transcript (collapsible)
- Each action item shows: task, assignee, deadline, timestamp link
- Each decision shows: what was decided, by whom, timestamp
- Save as `meeting-notes-YYYY-MM-DD-HHMM.html`
- Also generate Markdown version for pasting into docs/email

### Task 2B: CLI Runner

Build `/ganuda/products/meeting-notes/meeting_notes.py`:

```bash
python3 meeting_notes.py --record              # Start recording, Ctrl+C to stop and process
python3 meeting_notes.py --file meeting.wav    # Process existing audio file
python3 meeting_notes.py --no-llm              # Transcribe only, skip extraction
python3 meeting_notes.py --output notes.html   # Custom output path
python3 meeting_notes.py --quick               # Skip speaker diarization for speed
```

## Phase 3: Deploy + Launch (Day 3)

### Task 3A: Demo on DMZ
- Pre-record a demo meeting (Partner + TPM discussion, sanitized)
- Process it, generate report
- Serve demo at ganuda.us/meeting-notes
- FastAPI endpoint: GET / (report), GET /demo (pre-generated), POST /process (upload WAV)

### Task 3B: GitHub + Content
- dereadi/meeting-notes-extractor repo
- README with report screenshot
- Substack post: "Your Meeting Notes Stay on Your Machine. Otter.ai Can't Say That."
- LinkedIn post

## Constraints

- **Whisper runs LOCALLY** — no cloud transcription API
- **LLM runs locally** — vLLM on redfin, not external API
- **Audio NEVER stored permanently** — transcribe then delete WAV (user can override with --keep-audio)
- **Recording consent** — print clear warning: "RECORDING ACTIVE — ensure all participants consent"
- **Cross-platform** — Linux primary (PulseAudio/PipeWire), macOS secondary (BlackHole/SoundFlower)
- **Use reference patterns** — copy vLLM client from Trimmer classifier.py, HTML from Trimmer templates

## Success Criteria

- [ ] Audio capture records system audio + mic on Linux
- [ ] Whisper transcribes with timestamps
- [ ] LLM extracts decisions, action items, topics in structured JSON
- [ ] HTML report is clean and professional
- [ ] CLI works with --record, --file, --no-llm flags
- [ ] Demo deployed at ganuda.us/meeting-notes
- [ ] GitHub repo created
- [ ] Audio deleted after transcription by default

---

*"Your meeting audio never leaves your machine. Your decisions, action items, and topics — extracted locally by AI that runs on your hardware."*

*For Seven Generations.*

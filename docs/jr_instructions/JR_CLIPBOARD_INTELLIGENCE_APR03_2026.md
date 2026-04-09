# Jr Build Instruction: Clipboard Intelligence — "What Did I Copy?"

## Priority: P1 — MOCHA Product Sprint, Product #4
## Date: April 3, 2026
## Requested By: Partner + TPM
## Target: Ship in 2-3 days
## Ultrathink: /ganuda/docs/ultrathink/ULTRATHINK-MEETING-NOTES-CLIPBOARD-INTELLIGENCE-APR03-2026.md

---

## What We're Building

A background daemon that monitors your clipboard, classifies every entry with regex + local LLM, temperature-scores based on usage, and provides searchable history. Your clipboard becomes a knowledge base, not a FIFO buffer.

**Non-techie bar: "My mom could use this."**

## Phase 1: Monitor + Classify + Store (Day 1-2)

### Task 1A: Clipboard Monitor Daemon

Build `/ganuda/products/clipboard-intel/monitor.py`:

- Poll system clipboard every 500ms using `pyperclip` (cross-platform)
- Deduplicate: same content within 5 seconds = skip
- Record: content, timestamp, content length, content hash (for dedup)
- Detect source app if possible (optional — platform-specific)
- Run as background daemon: `python3 monitor.py --daemon`
- Graceful shutdown on SIGTERM/SIGINT
- Log new clips to stdout: `[14:23:17] New clip: url (142 chars)`

### Task 1B: Fast Classifier

Build `/ganuda/products/clipboard-intel/classifier.py`:

Two-stage classification for speed:

**Stage 1 — Regex (handles 70% of clips, zero LLM cost):**
```python
PATTERNS = {
    'url': r'https?://\S+',
    'email': r'[\w.-]+@[\w.-]+\.\w+',
    'phone': r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\./0-9]{7,15}',
    'ipv4': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
    'json': r'^\s*[\{\[]',
    'code': r'(def |class |import |function |const |var |let |SELECT |INSERT |CREATE )',
    'path': r'^[/~][\w/\-\.]+',
    'aws_key': r'AKIA[0-9A-Z]{16}',
    'api_key': r'(sk-|pk_|Bearer |token[=: ])',
    'ssh_key': r'-----BEGIN (RSA|OPENSSH|EC) PRIVATE KEY-----',
    'password_pattern': r'(password|passwd|pwd)[=: ]+\S+',
}
```

**Stage 2 — LLM (for ambiguous content, batched every 30 seconds):**
- Collect unclassified clips into a batch
- Send batch to vLLM with structured prompt:
  "Classify each clipboard entry. Return JSON array with: type, subtype, tags, sensitivity (low/medium/high)"
- **USE vLLM pattern from /ganuda/products/subscription-trimmer/classifier.py**
- Only call LLM for clips that regex couldn't classify

### Task 1C: Sensitivity Gate

Build `/ganuda/products/clipboard-intel/sensitivity.py`:

- Detect high-sensitivity content: passwords, API keys, tokens, SSH keys, credit card numbers
- When detected:
  - Encrypt the content with Fernet AES before storing
  - Flag as `is_sensitive = True`
  - Log WARNING: "Sensitive content detected (type: api_key) — encrypted at rest"
  - NEVER store plain-text credentials in the database
- Encryption key: auto-generated at `/ganuda/config/.clipboard_key`, permissions 600
- Same pattern as tribal_vision.py encrypted frame storage

### Task 1D: Thermal Clipboard Store

Build `/ganuda/products/clipboard-intel/store.py`:

- SQLite database at `~/.clipboard_intel/clips.db`
- Schema:
```sql
CREATE TABLE clips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_hash TEXT UNIQUE,
    content TEXT,           -- encrypted if sensitive
    content_preview TEXT,   -- first 100 chars, safe to display
    timestamp DATETIME,
    clip_type TEXT,         -- url, code, credential, text, etc.
    subtype TEXT,           -- article, snippet, password, etc.
    tags TEXT,              -- JSON array of tags
    sensitivity TEXT,       -- low, medium, high
    is_sensitive BOOLEAN DEFAULT FALSE,
    is_encrypted BOOLEAN DEFAULT FALSE,
    temperature REAL DEFAULT 50.0,
    access_count INTEGER DEFAULT 0,
    last_accessed DATETIME,
    is_pinned BOOLEAN DEFAULT FALSE,
    source_app TEXT
);
```
- Temperature calculation: `temp = min(100, (access_count * 10) + recency_bonus)`
  - recency_bonus: 40 if today, 30 if yesterday, 20 if this week, 10 if this month, 0 if older
- Auto-archive: clips not accessed in 30 days get temperature set to 0
- Pinned clips: temperature locked at 95 (sacred equivalent)

## Phase 2: Search + Interface (Day 2-3)

### Task 2A: Search Engine

Build `/ganuda/products/clipboard-intel/search.py`:

- Keyword search: `search("substack")` → all clips containing "substack"
- Type filter: `search(clip_type="url")` → all URLs
- Date filter: `search(today=True)`, `search(date="2026-04-03")`
- Temperature sort: hottest first (default) or chronological
- Sensitivity filter: `search(include_sensitive=False)` hides encrypted clips
- Return format: list of clip dicts with preview, type, temperature, timestamp

### Task 2B: CLI Interface

Build `/ganuda/products/clipboard-intel/clip.py`:

```bash
clip search "API endpoint"           # Keyword search
clip list --today                    # Today's clips
clip list --type url                 # All URLs
clip list --hot                      # Sorted by temperature
clip list --sensitive                # Show sensitive (requires confirmation)
clip pin <id>                        # Pin a clip (temperature → 95)
clip delete <id>                     # Delete a clip
clip clear --older-than 30d          # Prune old clips
clip stats                           # Show: total clips, by type, avg temp, storage used
clip export --today --format json    # Export clips
```

### Task 2C: Web Dashboard

Build `/ganuda/products/clipboard-intel/dashboard.py`:

- FastAPI app on port 8502
- GET / — HTML dashboard (ganuda.us dark theme)
- Dashboard shows:
  - Search bar at top
  - Stats cards: total clips, today's clips, hot clips, sensitive detected
  - Recent clips as cards: preview, type badge, temperature bar, timestamp
  - Type filter buttons: All | URLs | Code | Text | Sensitive
  - Each card: click to copy, pin button, delete button
- GET /api/clips — JSON API for clips (filtered, paginated)
- GET /api/stats — clip statistics
- Sensitive clips show "[ENCRYPTED]" with unlock button (requires confirmation)

## Phase 3: Deploy + Launch (Day 3)

### Task 3A: Demo on DMZ
- Run clipboard monitor on redfin for a few hours to collect real demo data
- Deploy dashboard at ganuda.us/clipboard
- Pre-loaded with sanitized demo data

### Task 3B: GitHub + Content
- dereadi/clipboard-intelligence repo
- README with dashboard screenshot
- Substack post: "Your Clipboard Is a Knowledge Base. You Just Can't Search It Yet."
- LinkedIn post

## Constraints

- **NEVER store credentials in plain text** — sensitivity gate is non-negotiable
- **Minimal CPU** — daemon must be invisible (<1% CPU). Regex first, LLM second.
- **SQLite, not PostgreSQL** — this runs on anyone's laptop, not a server
- **Cross-platform** — pyperclip handles Linux/macOS/Windows clipboard access
- **No cloud** — everything local. No sync to any server.
- **30-day retention** — auto-archive old clips. Don't fill the user's disk.
- **Use reference patterns** — copy vLLM client from Trimmer, HTML theme from Trimmer, encryption from tribal_vision

## Dependencies

```
pip install pyperclip cryptography fastapi uvicorn
```
No heavy deps. No torch. No GPU required for basic operation (regex handles 70%).
LLM classification is optional — works without it, just less intelligent tagging.

## Success Criteria

- [ ] Daemon monitors clipboard with <1% CPU
- [ ] Regex classifies 70%+ of clips without LLM
- [ ] Credentials detected and encrypted automatically
- [ ] SQLite store with temperature scoring
- [ ] CLI search returns relevant results
- [ ] Web dashboard shows clips with type badges and temperature
- [ ] Demo deployed at ganuda.us/clipboard
- [ ] GitHub repo created

---

*"Your clipboard is the smallest unit of your attention. We make it searchable, classified, and sovereign."*

*For Seven Generations.*

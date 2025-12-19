# Jr Build Instructions: Telegram Bot Enhanced Features

## Priority: HIGH - TPM Mobile Command Post

---

## Research Basis

Survey of GitHub telegram AI bots (December 2025):
- **chatgpt-telegram-bot** (3.5K stars): Multi-model, voice support
- **Master-AI-BOT** (264 stars): Voice recognition, DALL-E, group chat
- **pokitoki** (340 stars): Shortcuts (summarize, proofread), user management
- **gemini-ai-telegram-bot**: Plugin system, webhook support

**Key Features to Adopt:**
1. Voice message → Council query
2. Shortcuts for common operations
3. TPM approval workflow (CRITICAL GAP)
4. Semantic memory search
5. Specialist direct queries
6. Research paper notifications

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Telegram Bot (telegram_chief.py)                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   /council   │  │   /approve   │  │  /remember   │              │
│  │   Council    │  │   TPM Flow   │  │   Semantic   │              │
│  │   Queries    │  │   Commands   │  │   Search     │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                 │                       │
│         ▼                 ▼                 ▼                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Command Router                            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│         │                 │                 │                       │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐              │
│  │   /ask       │  │   /voice     │  │   /papers    │              │
│  │  Specialist  │  │   Voice→Text │  │   Research   │              │
│  │   Direct     │  │   →Council   │  │   Digest     │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    LLM Gateway (port 8080)                          │
│  /v1/council/vote  │  /v1/council/approve  │  /v1/memory/search    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Feature 1: TPM Approval Commands

**Commands:**
| Command | Description | Example |
|---------|-------------|---------|
| `/pending` | List pending TPM votes | `/pending` |
| `/approve <hash> [notes]` | Approve a vote | `/approve b24d79a3 Looks good` |
| `/reject <hash> <reason>` | Reject with reasoning | `/reject b24d79a3 Security concern not addressed` |
| `/clarify <hash> <context>` | Re-deliberate with context | `/clarify b24d79a3 We deployed specialist memory today` |
| `/audit <hash>` | Full audit trail for vote | `/audit b24d79a3` |

**Implementation:**
```python
# Add to telegram_chief.py

TPM_USER_IDS = [123456789]  # Authorized TPM telegram user IDs

def is_tpm_user(user_id: int) -> bool:
    """Check if user has TPM privileges"""
    return user_id in TPM_USER_IDS

async def pending_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all pending Council votes"""
    try:
        response = requests.get(
            f"{GATEWAY_URL}/v1/council/pending",
            headers={"X-API-Key": API_KEY},
            timeout=10
        )
        data = response.json()

        if data.get("pending_count", 0) == 0:
            await update.message.reply_text("No pending TPM votes")
            return

        lines = [f"Pending Votes ({data['pending_count']}):"]
        for vote in data["votes"][:10]:
            emoji = "[WARN]" if "CAUTION" in vote["recommendation"] else "[STOP]" if "REVIEW" in vote["recommendation"] else "[OK]"
            lines.append(f"\n{emoji} `{vote['audit_hash'][:12]}`")
            lines.append(f"   {vote['recommendation']}")
            lines.append(f"   _{vote['question'][:40]}..._")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def approve_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approve a pending vote: /approve <hash> [notes]"""
    if not is_tpm_user(update.effective_user.id):
        await update.message.reply_text("TPM authorization required")
        return

    args = context.args
    if not args:
        await update.message.reply_text("Usage: /approve <audit_hash> [notes]")
        return

    audit_hash = args[0]
    notes = " ".join(args[1:]) if len(args) > 1 else f"Approved by TPM via Telegram"

    try:
        response = requests.post(
            f"{GATEWAY_URL}/v1/council/approve",
            headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
            json={"audit_hash": audit_hash, "decision": "approved", "notes": notes},
            timeout=10
        )

        if response.ok:
            await update.message.reply_text(f"[OK] Approved `{audit_hash}`", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"[ERROR] {response.json().get('detail', 'Unknown error')}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def clarify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Re-deliberate with context: /clarify <hash> <context>"""
    if not is_tpm_user(update.effective_user.id):
        await update.message.reply_text("TPM authorization required")
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /clarify <audit_hash> <clarification context>")
        return

    audit_hash = args[0]
    clarification = " ".join(args[1:])

    thinking_msg = await update.message.reply_text("Re-deliberating with Council...")

    try:
        response = requests.post(
            f"{GATEWAY_URL}/v1/council/approve",
            headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
            json={
                "audit_hash": audit_hash,
                "decision": "clarify",
                "clarification_context": clarification
            },
            timeout=60
        )

        if response.ok:
            data = response.json()
            result = f"[OK] Re-deliberation complete\n"
            result += f"New hash: `{data['new_audit_hash']}`\n"
            result += f"New recommendation: {data['new_recommendation']}\n"
            result += f"Confidence: {data['new_confidence']:.0%}"
            await thinking_msg.edit_text(result, parse_mode="Markdown")
        else:
            await thinking_msg.edit_text(f"[ERROR] {response.json().get('detail')}")
    except Exception as e:
        await thinking_msg.edit_text(f"Error: {e}")


# Register handlers
application.add_handler(CommandHandler("pending", pending_command))
application.add_handler(CommandHandler("approve", approve_command))
application.add_handler(CommandHandler("reject", reject_command))  # Similar to approve
application.add_handler(CommandHandler("clarify", clarify_command))
```

---

## Feature 2: Semantic Memory Search (/remember)

**Commands:**
| Command | Description | Example |
|---------|-------------|---------|
| `/remember <query>` | Search thermal memory | `/remember specialist memory implementation` |
| `/recall <days> <query>` | Search with time filter | `/recall 7 security concerns` |

**Requires:** Embedding service (already deployed on sasass/sasass2)

**Implementation:**
```python
async def remember_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search thermal memory semantically: /remember <query>"""
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Usage: /remember <search query>")
        return

    thinking_msg = await update.message.reply_text("Searching tribal memory...")

    try:
        # Call embedding service for semantic search
        response = requests.post(
            f"{GATEWAY_URL}/v1/memory/search",
            headers={"X-API-Key": API_KEY},
            json={"query": query, "limit": 5, "min_similarity": 0.7},
            timeout=30
        )

        if not response.ok:
            await thinking_msg.edit_text("Memory search unavailable")
            return

        results = response.json().get("results", [])

        if not results:
            await thinking_msg.edit_text(f"No memories found for: _{query}_", parse_mode="Markdown")
            return

        lines = [f"Memories matching '{query[:30]}...':"]
        for i, mem in enumerate(results, 1):
            similarity = mem.get("similarity", 0)
            content = mem.get("content", "")[:150]
            created = mem.get("created_at", "")[:10]
            temp = mem.get("temperature", 0)

            emoji = "🔥" if temp > 80 else "🌡️" if temp > 50 else "❄️"
            lines.append(f"\n{i}. {emoji} ({similarity:.0%}) [{created}]")
            lines.append(f"   _{content}_...")

        await thinking_msg.edit_text("\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        await thinking_msg.edit_text(f"Error: {e}")
```

**Gateway Endpoint Needed:**
```python
@app.post("/v1/memory/search")
async def search_memory(request: MemorySearchRequest):
    """Semantic search across thermal memory"""
    # Get embedding for query
    query_embedding = get_embedding(request.query)

    with get_db() as conn:
        cur = conn.cursor()
        # pgvector cosine similarity search
        cur.execute("""
            SELECT original_content, temperature_score, created_at,
                   1 - (embedding <=> %s::vector) as similarity
            FROM thermal_memory_archive
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (query_embedding, query_embedding, request.limit))

        results = [
            {
                "content": row[0],
                "temperature": row[1],
                "created_at": row[2].isoformat(),
                "similarity": row[3]
            }
            for row in cur.fetchall()
            if row[3] >= request.min_similarity
        ]

    return {"results": results, "query": request.query}
```

---

## Feature 3: Specialist Direct Queries

**Commands:**
| Command | Description | Example |
|---------|-------------|---------|
| `/ask crawdad <question>` | Ask security specialist | `/ask crawdad Is this API secure?` |
| `/ask gecko <question>` | Ask technical specialist | `/ask gecko Performance implications?` |
| `/ask turtle <question>` | Ask wisdom keeper | `/ask turtle Long-term impact?` |
| `/ask eagle <question>` | Ask monitoring specialist | `/ask eagle Node health?` |

**Implementation:**
```python
SPECIALIST_ALIASES = {
    "crawdad": "crawdad", "security": "crawdad",
    "gecko": "gecko", "tech": "gecko", "performance": "gecko",
    "turtle": "turtle", "wisdom": "turtle", "7gen": "turtle",
    "eagle": "eagle_eye", "eagle_eye": "eagle_eye", "monitor": "eagle_eye",
    "spider": "spider", "integration": "spider",
    "raven": "raven", "strategy": "raven",
    "peace": "peace_chief", "chief": "peace_chief"
}

async def ask_specialist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask specific specialist: /ask <specialist> <question>"""
    args = context.args
    if len(args) < 2:
        specialists = ", ".join(set(SPECIALIST_ALIASES.keys()))
        await update.message.reply_text(f"Usage: /ask <specialist> <question>\nSpecialists: {specialists}")
        return

    specialist_input = args[0].lower()
    specialist = SPECIALIST_ALIASES.get(specialist_input)

    if not specialist:
        await update.message.reply_text(f"Unknown specialist: {specialist_input}")
        return

    question = " ".join(args[1:])

    thinking_msg = await update.message.reply_text(f"Asking {specialist.replace('_', ' ').title()}...")

    try:
        response = requests.post(
            f"{GATEWAY_URL}/v1/specialist/query",
            headers={"X-API-Key": API_KEY},
            json={"specialist": specialist, "question": question},
            timeout=30
        )

        if response.ok:
            data = response.json()
            result = f"**{data['specialist_name']}** ({data['role']}):\n\n"
            result += data['response']
            if data.get('concerns'):
                result += f"\n\n_Concerns: {', '.join(data['concerns'])}_"
            await thinking_msg.edit_text(result, parse_mode="Markdown")
        else:
            await thinking_msg.edit_text(f"Error: {response.json().get('detail')}")
    except Exception as e:
        await thinking_msg.edit_text(f"Error: {e}")


# Register handler
application.add_handler(CommandHandler("ask", ask_specialist_command))
```

---

## Feature 4: Voice Message Support

**Flow:**
1. User sends voice message
2. Bot transcribes using Whisper (local or API)
3. Transcription sent to Council
4. Response sent back as text

**Implementation:**
```python
from pydub import AudioSegment
import whisper  # or use API

# Load Whisper model (small for speed)
whisper_model = whisper.load_model("small")

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages - transcribe and send to Council"""
    voice = update.message.voice

    thinking_msg = await update.message.reply_text("Transcribing voice message...")

    try:
        # Download voice file
        voice_file = await voice.get_file()
        ogg_path = f"/tmp/voice_{update.message.id}.ogg"
        wav_path = f"/tmp/voice_{update.message.id}.wav"

        await voice_file.download_to_drive(ogg_path)

        # Convert to wav for Whisper
        audio = AudioSegment.from_ogg(ogg_path)
        audio.export(wav_path, format="wav")

        # Transcribe
        result = whisper_model.transcribe(wav_path)
        transcription = result["text"].strip()

        await thinking_msg.edit_text(f"Heard: _{transcription}_\n\nConsulting Council...", parse_mode="Markdown")

        # Send to Council
        council_response = await query_council(transcription, update.effective_user.first_name)

        # Format and send response
        formatted = format_council_response(council_response)
        await thinking_msg.edit_text(f"Voice: _{transcription}_\n\n{formatted}", parse_mode="Markdown")

        # Cleanup
        os.remove(ogg_path)
        os.remove(wav_path)

    except Exception as e:
        await thinking_msg.edit_text(f"Voice processing error: {e}")


# Register handler
application.add_handler(MessageHandler(filters.VOICE, voice_handler))
```

**Dependencies:**
```bash
pip install pydub openai-whisper
# or for API-based transcription:
pip install openai  # Use OpenAI Whisper API
```

---

## Feature 5: Research Paper Notifications

**Commands:**
| Command | Description | Example |
|---------|-------------|---------|
| `/papers` | Recent high-relevance papers | `/papers` |
| `/papers <days>` | Papers from last N days | `/papers 7` |
| `/paper <id>` | Full paper details | `/paper 42` |

**Daily Digest (6:30 AM after crawler):**
```python
import asyncio
from telegram import Bot

NOTIFICATION_CHAT_IDS = [TPM_CHAT_ID]  # Who gets paper notifications

async def send_paper_digest():
    """Send daily digest of high-relevance papers"""
    bot = Bot(token=BOT_TOKEN)

    # Get today's papers
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, title, relevance_score, temperature_score
            FROM ai_research_papers
            WHERE crawled_at > NOW() - INTERVAL '24 hours'
              AND relevance_score >= 70
            ORDER BY relevance_score DESC
            LIMIT 5
        """)
        papers = cur.fetchall()

    if not papers:
        return

    lines = ["📚 **Daily Research Digest**\n"]
    for paper_id, title, relevance, temp in papers:
        emoji = "🔥" if relevance >= 90 else "⭐" if relevance >= 80 else "📄"
        lines.append(f"{emoji} [{relevance}] {title[:60]}...")
        lines.append(f"   /paper {paper_id}")

    message = "\n".join(lines)

    for chat_id in NOTIFICATION_CHAT_IDS:
        await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")


# Schedule with APScheduler or systemd timer
```

---

## Feature 6: Shortcuts & Quick Commands

| Shortcut | Expands To | Description |
|----------|------------|-------------|
| `/health` | Node health summary | Quick cluster status |
| `/concerns` | Today's Council concerns | What the specialists flagged |
| `/summary` | Summarize last response | Condense long output |
| `/status` | Full system status | Services, memory, votes |

**Implementation:**
```python
async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick health check: /health"""
    try:
        # Get health from gateway
        response = requests.get(f"{GATEWAY_URL}/health", timeout=5)

        # Get service_health from DB
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT node_name, service_name, status
                FROM service_health
                WHERE last_check > NOW() - INTERVAL '10 minutes'
                ORDER BY node_name, service_name
            """)
            rows = cur.fetchall()

        lines = ["**Cluster Health**\n"]

        # Group by node
        current_node = None
        for node, service, status in rows:
            if node != current_node:
                lines.append(f"\n📍 **{node}**")
                current_node = node
            emoji = "✅" if status == "healthy" else "❌"
            lines.append(f"   {emoji} {service}")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Health check error: {e}")


async def concerns_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Today's Council concerns: /concerns"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT specialist_name, concern_type, COUNT(*)
            FROM council_concerns
            WHERE raised_at > NOW() - INTERVAL '24 hours'
            GROUP BY specialist_name, concern_type
            ORDER BY COUNT(*) DESC
        """)
        rows = cur.fetchall()

    if not rows:
        await update.message.reply_text("No concerns raised today")
        return

    lines = ["**Today's Council Concerns**\n"]
    for specialist, concern_type, count in rows:
        lines.append(f"• {specialist}: {concern_type} ({count}x)")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
```

---

## Feature 7: Group Chat Support

**Behavior:**
- In groups, bot only responds to @mentions or /commands
- Private chats: responds to all messages
- Group admins can configure behavior with /settings

```python
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages - different behavior for groups vs private"""
    message = update.message
    chat_type = message.chat.type

    # In groups, only respond to mentions or replies
    if chat_type in ("group", "supergroup"):
        bot_username = (await context.bot.get_me()).username

        is_mentioned = f"@{bot_username}" in message.text
        is_reply_to_bot = (
            message.reply_to_message and
            message.reply_to_message.from_user.id == context.bot.id
        )

        if not is_mentioned and not is_reply_to_bot:
            return  # Ignore message in group

        # Remove mention from text
        text = message.text.replace(f"@{bot_username}", "").strip()
    else:
        text = message.text

    # Process as Council query
    await process_council_query(update, text)
```

---

## Command Summary

| Command | Category | TPM Only | Description |
|---------|----------|----------|-------------|
| `/council <query>` | Core | No | Full Council deliberation |
| `/ask <specialist> <q>` | Core | No | Direct specialist query |
| `/pending` | TPM | Yes | List pending votes |
| `/approve <hash>` | TPM | Yes | Approve vote |
| `/reject <hash> <reason>` | TPM | Yes | Reject vote |
| `/clarify <hash> <ctx>` | TPM | Yes | Re-deliberate |
| `/remember <query>` | Memory | No | Search thermal memory |
| `/papers` | Research | No | Recent papers |
| `/health` | Status | No | Cluster health |
| `/concerns` | Status | No | Today's concerns |
| `/devices` | IoT | No | List IoT devices |
| `/help` | Meta | No | Command list |

---

## Deployment

### 1. Install Dependencies
```bash
pip install pydub openai-whisper python-telegram-bot requests
```

### 2. Update telegram_chief.py
Apply features incrementally, test each.

### 3. Environment Variables
```bash
export TELEGRAM_BOT_TOKEN="..."
export GATEWAY_URL="http://192.168.132.223:8080"
export API_KEY="ck-..."
export TPM_USER_IDS="123456789,987654321"
```

### 4. Systemd Service
```ini
[Unit]
Description=Cherokee AI Telegram Bot
After=network.target llm-gateway.service

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda/telegram_bot
Environment=TELEGRAM_BOT_TOKEN=...
ExecStart=/home/dereadi/cherokee_venv/bin/python3 telegram_chief.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## Success Criteria

- [ ] TPM approval commands working (/pending, /approve, /reject, /clarify)
- [ ] Semantic memory search (/remember)
- [ ] Specialist direct queries (/ask)
- [ ] Voice message transcription (optional - requires Whisper)
- [ ] Research paper notifications
- [ ] Shortcuts (/health, /concerns)
- [ ] Group chat behavior (mention-only)
- [ ] Systemd service running

---

*For Seven Generations*

# JR Instruction: Telegram Research Integration

**JR ID:** JR-TELEGRAM-RESEARCH-INTEGRATION-JAN28-2026
**Priority:** P0 - IMMEDIATE
**Assigned To:** Telegram Jr.
**Related:** JR-RESEARCH-PERSONA-SUPPORT-JAN28-2026
**Status:** READY TO IMPLEMENT - All infrastructure running

---

## Objective

Add `/research` command to Telegram Chief that triggers ii-researcher with the `telegram` persona (technical generalist).

## IMPORTANT: Infrastructure Already Running

- ✅ `research_worker.py` - Running (PID active)
- ✅ `research_file_watcher.py` - Running
- ✅ `ii-researcher.service` - Running
- ✅ `research_jobs` table - Exists in zammad_production
- ✅ `ResearchDispatcher` with Telegram callbacks - Ready
- ✅ `research_personas.py` with "telegram" persona - Ready

**Only missing: Command handler in telegram_chief.py**

---

## Context

The research persona system is already implemented:
- `/ganuda/lib/research_personas.py` - Defines persona prompts including `telegram` (technical generalist)
- `/ganuda/services/research_file_watcher.py` - Processes request files with persona support
- `/ganuda/vetassist/backend/app/api/v1/endpoints/research.py` - API endpoint accepts `persona` field

The Telegram bot (`telegram_chief.py`) routes questions to the 7-Specialist Council but has no deep research capability.

---

## Implementation

### Step 1: Add Research Command Handler

Edit `/ganuda/telegram_bot/telegram_chief.py`.

**Add after line ~448 (after help_command function):**

```python
async def research_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /research command - trigger deep research with technical persona"""
    user = update.effective_user
    chat_id = str(update.effective_chat.id)

    if not context.args:
        await update.message.reply_text(
            "Usage: /research <your question>\n\n"
            "Example: /research How do I debug PostgreSQL connection timeouts?\n\n"
            "Triggers deep web research (3-5 min). Uses technical generalist persona."
        )
        return

    question = " ".join(context.args)

    # Acknowledge
    await update.message.reply_text(
        f"🔍 Starting deep research...\n\n"
        f"Q: {question[:100]}{'...' if len(question) > 100 else ''}\n\n"
        f"Results in 3-5 minutes."
    )

    # Queue via ResearchDispatcher (supports Telegram callbacks)
    try:
        sys.path.insert(0, '/ganuda/lib')
        from research_dispatcher import ResearchDispatcher
        from research_personas import build_research_query

        dispatcher = ResearchDispatcher()

        # Build query with technical generalist persona
        full_query = build_research_query(question, "telegram")

        job_id = dispatcher.queue_research(
            query=full_query,
            requester_type="telegram",
            requester_id=f"{user.id}",
            callback_type="telegram",
            callback_target=chat_id,  # research_worker will notify this chat
            max_steps=5
        )

        await update.message.reply_text(
            f"✅ Research queued: {job_id}\n\n"
            f"I'll notify you when complete."
        )

    except Exception as e:
        logger.error(f"Research error: {e}")
        await update.message.reply_text(f"❌ Research error: {str(e)}")


async def results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /results command - check research results"""
    user = update.effective_user
    veteran_id = f"telegram-{user.id}"

    try:
        import requests
        response = requests.get(
            f"{RESEARCH_API_URL}/results/{veteran_id}",
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])

            if not results:
                await update.message.reply_text("No research results found. Try /research <question>")
                return

            # Show most recent result
            latest = results[0]
            answer = latest.get("summary", "")[:3500]  # Telegram limit
            question = latest.get("question", "")

            await update.message.reply_text(
                f"📚 Latest Research Result\n\n"
                f"Q: {question[:100]}\n\n"
                f"{answer}"
            )
        else:
            await update.message.reply_text(f"Failed to get results: {response.status_code}")

    except Exception as e:
        await update.message.reply_text(f"Error checking results: {str(e)}")
```

### Step 2: Register Command Handler

In the `main()` function (around line 715), add:

```python
    app.add_handler(CommandHandler("research", research_command))  # ADD THIS
```

Add it after the other CommandHandlers, before the MessageHandler.

### Step 3: Update Help Text

In `help_command` (around line 425), add to the help text:

```
/research <question> - Deep web research (technical)
```

### Step 4: Ensure TELEGRAM_BOT_TOKEN in research-worker.service

The worker needs the token to send notifications. Check:

```bash
grep TELEGRAM_BOT_TOKEN /etc/systemd/system/research-worker.service
```

If missing, add to the `[Service]` section:
```ini
Environment=TELEGRAM_BOT_TOKEN=7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8
```

Then: `sudo systemctl daemon-reload && sudo systemctl restart research-worker`

---

## Testing

### Test Research Trigger
```
/research How do I configure PostgreSQL connection pooling with pgbouncer?
```

**Expected:**
1. Bot acknowledges with research ID
2. 3-5 minutes later, results available via /results
3. Response uses technical language, includes commands/examples

### Test Results Check
```
/results
```

**Expected:**
- Shows latest research result with technical synthesis

---

## Service Restart

After implementation, restart the Telegram bot:

```bash
sudo systemctl restart telegram-chief
```

Or if running manually:
```bash
cd /ganuda/telegram_bot
./start_chief.sh
```

---

## Future Extensions

1. **Push notifications**: When research completes, proactively send to chat
2. **Research status polling**: Background task checks for new results
3. **Multiple results**: `/results all` to show recent 5 results
4. **Research history**: Track per-user research queries

---

FOR SEVEN GENERATIONS

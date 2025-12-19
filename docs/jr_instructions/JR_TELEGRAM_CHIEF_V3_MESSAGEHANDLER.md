# Jr Instructions: Add Message Handler to Telegram Chief v3

**Priority**: 1 (Critical)
**Assigned Jr**: it_triad_jr
**Target**: Patch telegram_chief_v3.py with missing message handler

---

## PROBLEM

The telegram_chief_v3.py bot only responds to /commands but not to regular text messages in the group chat. The original telegram_chief.py has a `MessageHandler` that catches all non-command text and routes it through the Council. This is missing from v3.

---

### Task 1: Add Helper Functions to v3 Bot

Edit `/ganuda/telegram_bot/telegram_chief_v3.py` and add these functions after the `TribeInterface` class (after line ~196):

```python
# Add after line 196 (after tribe = TribeInterface())

def classify_request(message: str) -> dict:
    """Classify user request type"""
    message_lower = message.lower()

    destructive = ['delete', 'remove', 'drop', 'truncate', 'destroy', 'wipe', 'clear']
    if any(k in message_lower for k in destructive):
        return {"type": "destructive", "tpm_wait": True, "timeout": 300, "confirm": True}

    actions = ['restart', 'start', 'stop', 'deploy', 'install', 'update', 'upgrade', 'run', 'execute']
    if any(k in message_lower for k in actions):
        return {"type": "action", "tpm_wait": True, "timeout": 300}

    critical = ['urgent', 'emergency', 'critical', 'down', 'crashed', 'failed', 'error']
    if any(k in message_lower for k in critical):
        return {"type": "critical", "tpm_wait": True, "timeout": 60}

    diagnostic = ['check', 'status', 'health', 'disk', 'memory', 'cpu', 'logs', 'show', 'list',
                  'nodes', 'ok', 'online', 'running', 'servers', 'cluster', 'alive', 'ping']
    if any(k in message_lower for k in diagnostic):
        return {"type": "diagnostic", "tpm_wait": False, "route_to": "eagle_eye"}

    return {"type": "query", "tpm_wait": False}


def format_council_response(result: dict, classification: dict) -> str:
    """Format council response for Telegram"""
    if "error" in result:
        return f"Error: {result['error']}"

    lines = []
    rec = result.get("recommendation", result.get("decision", "No decision"))
    conf = result.get("confidence", 0)

    if "PROCEED" in str(rec).upper():
        lines.append(f"[OK] {rec}")
    elif "CAUTION" in str(rec).upper():
        lines.append(f"[WARN] {rec}")
    else:
        lines.append(str(rec))

    lines.append(f"Confidence: {conf}%")

    concerns = result.get("concerns", [])
    if concerns:
        lines.append(f"\nConcerns:")
        for c in concerns[:3]:
            lines.append(f"  - {c}")

    return "\n".join(lines)
```

---

### Task 2: Add Message Handler Function

Add this async function before the `main()` function in `/ganuda/telegram_bot/telegram_chief_v3.py`:

```python
# Add before main() function

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages - route to Council"""
    user = update.effective_user
    message = update.message.text

    if not message:
        return

    # Check tribal knowledge first
    tribal_answer = lookup_tribal_knowledge(message)
    if tribal_answer:
        await update.message.reply_text(f"Tribal Knowledge:\n\n{tribal_answer}")
        return

    # Classify and route
    classification = classify_request(message)

    # For queries and diagnostics, consult the Council
    thinking_msg = await update.message.reply_text("Consulting the Council...")

    question = f"Telegram user {user.first_name} asks: {message}"
    result = tribe.query_council(question, include_responses=True)

    response = format_council_response(result, classification)

    try:
        await thinking_msg.edit_text(response)
    except:
        await update.message.reply_text(response)
```

---

### Task 3: Register MessageHandler in main()

Edit the `main()` function in `/ganuda/telegram_bot/telegram_chief_v3.py`. Add this line after the CommandHandler registrations (after line ~339):

```python
    # Add this line after the CommandHandler registrations
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
```

---

### Task 4: Restart the Bot

After patching, restart the bot:

```bash
pkill -f telegram_chief_v3.py
cd /ganuda/telegram_bot
export TELEGRAM_BOT_TOKEN='7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8'
nohup /home/dereadi/cherokee_venv/bin/python3 telegram_chief_v3.py > /ganuda/logs/telegram_chief_v3.log 2>&1 &
```

---

## SUCCESS CRITERIA

1. Bot responds to non-command text messages in group chat
2. Messages are routed to the Council
3. Bot returns formatted Council responses
4. Bot still responds to all /commands

---

*For Seven Generations - Cherokee AI Federation*

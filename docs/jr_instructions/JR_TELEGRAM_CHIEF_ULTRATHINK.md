# Jr Instructions: Telegram Chief - Full Tribe Integration

**Priority**: 1 (Critical - Bot Currently Broken)
**Assigned Jr**: Integration Jr.
**Target**: redfin `/ganuda/telegram_bot/telegram_chief.py`
**Issue**: Bot crashes due to missing `get_db()` method and needs enhanced capabilities

---

## ULTRATHINK ANALYSIS

### Current State

The telegram_chief bot (`/ganuda/telegram_bot/telegram_chief.py`) was working earlier this week but is now broken. The bot is a critical Tribe interface that allows:
- TPM oversight via Telegram
- Council voting and approval workflows
- Cluster status monitoring
- Direct specialist queries

### Root Cause: Missing Database Method

**BUG IDENTIFIED**: The `TribeInterface` class is missing the `get_db()` method that several commands require:

```python
# These commands all fail with AttributeError:
/health    -> tribe.get_db()  # LINE ~280
/concerns  -> tribe.get_db()  # LINE ~310
/remember  -> tribe.get_db()  # LINE ~340
```

### Enhancement Requirements

Flying Squirrel requested the telegram_chief be enhanced to:
1. **Read AND Write to thermal memory** (currently read-only)
2. **Open tickets** in Jr work queue
3. **Request work done** by specialists
4. **Better FARA integration** for vision capabilities
5. **Proactive notifications** to the group chat

---

### Task 1: Fix the Missing get_db() Method

Create `/ganuda/telegram_bot/tribe_interface_fix.py`:

```python
import psycopg2
from contextlib import contextmanager

class TribeInterface:
    """Interface to the 7-Specialist Council"""

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        self.db_config = {
            'host': '192.168.132.222',
            'database': 'zammad_production',
            'user': 'claude',
            'password': 'jawaseatlasers2'
        }

    @contextmanager
    def get_db(self):
        """Get database connection as context manager"""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            yield conn
        finally:
            if conn:
                conn.close()

    # ... rest of existing methods ...
```

---

### Task 2: Add Thermal Memory Write Capability

Create `/ganuda/telegram_bot/thermal_memory_methods.py`:

```python
def seed_memory(self, content: str, memory_type: str = "telegram_interaction",
                temperature: int = 70, tags: list = None) -> dict:
    """Write to thermal memory archive"""
    try:
        with self.get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO thermal_memory_archive (
                    memory_hash, original_content, current_stage,
                    temperature_score, sacred_pattern, metadata,
                    time_sense, created_at
                ) VALUES (
                    md5(%s || %s),
                    %s,
                    CASE WHEN %s > 80 THEN 'HOT' WHEN %s > 50 THEN 'WARM' ELSE 'COOL' END,
                    %s,
                    false,
                    %s,
                    'SEVEN_GENERATIONS',
                    NOW()
                ) RETURNING id
            """, (
                content, str(datetime.now()),
                content,
                temperature, temperature,
                temperature,
                json.dumps({"type": memory_type, "source": "telegram_chief", "tags": tags or []})
            ))
            memory_id = cur.fetchone()[0]
            conn.commit()
            return {"success": True, "memory_id": memory_id}
    except Exception as e:
        return {"error": str(e)}
```

Add new command `/seed`:

```python
async def seed_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Seed a memory: /seed <temperature> <content>"""
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "Usage: /seed <temperature> <content>\n"
            "Example: /seed 85 Important lesson learned today about X"
        )
        return

    try:
        temperature = int(args[0])
        if not 0 <= temperature <= 100:
            raise ValueError("Temperature must be 0-100")
    except ValueError:
        await update.message.reply_text("Temperature must be a number 0-100")
        return

    content = " ".join(args[1:])
    user = update.effective_user.first_name

    tribe = TribeInterface()
    result = tribe.seed_memory(
        content=f"[Telegram/{user}] {content}",
        memory_type="telegram_seed",
        temperature=temperature,
        tags=["telegram", "user_seeded"]
    )

    if result.get("success"):
        temp_label = "HOT" if temperature > 80 else "WARM" if temperature > 50 else "COOL"
        await update.message.reply_text(
            f"Memory seeded [{temp_label}]\n"
            f"ID: {result['memory_id']}\n"
            f"Temperature: {temperature}"
        )
    else:
        await update.message.reply_text(f"Error: {result.get('error')}")
```

---

### Task 3: Add Ticket Creation Capability

Create `/ganuda/telegram_bot/ticket_commands.py`:

```python
# Add method to TribeInterface
def create_ticket(self, title: str, description: str, priority: int = 2,
                  assigned_jr: str = None, requester: str = "telegram") -> dict:
    """Create a ticket in Jr work queue"""
    try:
        with self.get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO jr_work_queue (
                    task_id, title, description, assigned_jr,
                    priority, status, requester, created_at
                ) VALUES (
                    md5(%s || %s),
                    %s, %s, %s, %s, 'pending', %s, NOW()
                ) RETURNING task_id, title
            """, (
                title, str(datetime.now()),
                title, description, assigned_jr, priority, requester
            ))
            result = cur.fetchone()
            conn.commit()
            return {"success": True, "task_id": result[0], "title": result[1]}
    except Exception as e:
        return {"error": str(e)}
```

Add new command `/ticket`:

```python
JR_ASSIGNMENTS = {
    "infra": "Infrastructure Jr.",
    "software": "Software Engineer Jr.",
    "synthesis": "Synthesis Jr.",
    "integration": "Integration Jr.",
    "security": "Security Jr."
}

async def ticket_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create a ticket: /ticket <priority> <jr> <title>"""
    args = context.args
    if len(args) < 3:
        jrs = ", ".join(JR_ASSIGNMENTS.keys())
        await update.message.reply_text(
            "Usage: /ticket <priority 1-3> <jr> <title>\n"
            f"Jrs: {jrs}\n"
            "Example: /ticket 2 infra Check disk space on bluefin"
        )
        return

    try:
        priority = int(args[0])
        if not 1 <= priority <= 3:
            raise ValueError()
    except:
        await update.message.reply_text("Priority must be 1 (high), 2 (medium), or 3 (low)")
        return

    jr_key = args[1].lower()
    assigned_jr = JR_ASSIGNMENTS.get(jr_key)
    if not assigned_jr:
        await update.message.reply_text(f"Unknown Jr: {jr_key}")
        return

    title = " ".join(args[2:])
    user = update.effective_user.first_name

    tribe = TribeInterface()
    result = tribe.create_ticket(
        title=title,
        description=f"Created via Telegram by {user}",
        priority=priority,
        assigned_jr=assigned_jr,
        requester=f"telegram/{user}"
    )

    if result.get("success"):
        priority_label = ["", "HIGH", "MEDIUM", "LOW"][priority]
        await update.message.reply_text(
            f"Ticket Created [{priority_label}]\n"
            f"ID: {result['task_id'][:8]}...\n"
            f"Assigned: {assigned_jr}\n"
            f"Title: {title}"
        )
    else:
        await update.message.reply_text(f"Error: {result.get('error')}")
```

---

### Task 4: Add Jr Work Queue Status Command

Create `/ganuda/telegram_bot/jr_queue_commands.py`:

```python
async def jrs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check Jr work queue: /jrs [jr_name]"""
    jr_filter = context.args[0].lower() if context.args else None

    tribe = TribeInterface()
    try:
        with tribe.get_db() as conn:
            cur = conn.cursor()
            if jr_filter:
                assigned_jr = JR_ASSIGNMENTS.get(jr_filter, f"%{jr_filter}%")
                cur.execute("""
                    SELECT task_id, title, priority, status, assigned_jr
                    FROM jr_work_queue
                    WHERE assigned_jr ILIKE %s
                      AND status NOT IN ('completed', 'cancelled')
                    ORDER BY priority, created_at
                    LIMIT 10
                """, (assigned_jr if "%" in assigned_jr else f"%{assigned_jr}%",))
            else:
                cur.execute("""
                    SELECT task_id, title, priority, status, assigned_jr
                    FROM jr_work_queue
                    WHERE status NOT IN ('completed', 'cancelled')
                    ORDER BY priority, created_at
                    LIMIT 15
                """)
            rows = cur.fetchall()

        if not rows:
            await update.message.reply_text("No pending Jr tasks")
            return

        lines = ["Jr Work Queue:\n"]
        for task_id, title, priority, status, jr in rows:
            p_label = ["", "!", "!!", "!!!"][min(priority, 3)]
            s_emoji = {"pending": "...", "in_progress": ">>", "blocked": "XX"}.get(status, "?")
            jr_short = jr.split()[0] if jr else "?"
            lines.append(f"[{p_label}][{s_emoji}] {jr_short}: {title[:40]}")

        await update.message.reply_text("\n".join(lines))
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
```

---

### Task 5: Enhanced FARA Integration

Create `/ganuda/telegram_bot/fara_integration.py`:

```python
# Enhanced FARA vision integration - replaces /look command
async def fara_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """FARA capabilities: /fara <action> [args]

    Actions:
      look [question] - Analyze sasass screen
      quiz <topic> - Generate quiz questions
      remember <query> - Search FARA's memories
    """
    args = context.args
    if not args:
        await update.message.reply_text(
            "FARA Commands:\n"
            "/fara look [question] - What's on sasass screen?\n"
            "/fara quiz <topic> - Generate quiz\n"
            "/fara screenshot - Take sasass screenshot"
        )
        return

    action = args[0].lower()

    if action == "look":
        question = " ".join(args[1:]) if len(args) > 1 else "What do you see?"
        await do_fara_look(update, question)
    elif action == "quiz":
        topic = " ".join(args[1:]) if len(args) > 1 else "general knowledge"
        await do_fara_quiz(update, topic)
    elif action == "screenshot":
        await do_fara_screenshot(update)
    else:
        await update.message.reply_text(f"Unknown FARA action: {action}")


async def do_fara_look(update: Update, question: str):
    """Execute FARA look on sasass"""
    thinking_msg = await update.message.reply_text("FARA is looking... (~30 sec)")

    safe_question = question.replace("'", "'\"'\"'")
    cmd = f"ssh dereadi@192.168.132.241 \"python3 /Users/Shared/ganuda/scripts/fara_look.py '{safe_question}'\""

    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)

        output = stdout.decode()
        if "FARA Response:" in output:
            response = output.split("FARA Response:")[-1].strip()
            response = response.replace("=" * 60, "").strip()
            await thinking_msg.edit_text(f"FARA sees:\n\n{response[:3500]}")
        else:
            await thinking_msg.edit_text(f"FARA: {output[-1500:]}")

    except asyncio.TimeoutError:
        await thinking_msg.edit_text("FARA timed out - model loading takes ~30 seconds")
    except Exception as e:
        await thinking_msg.edit_text(f"FARA error: {str(e)}")


async def do_fara_screenshot(update: Update):
    """Take and send sasass screenshot"""
    thinking_msg = await update.message.reply_text("Capturing sasass screen...")

    try:
        # Capture screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        remote_path = f"/tmp/fara_screenshot_{timestamp}.png"
        local_path = f"/tmp/fara_screenshot_{timestamp}.png"

        # Take screenshot on sasass
        await asyncio.create_subprocess_shell(
            f"ssh dereadi@192.168.132.241 'screencapture -x {remote_path}'"
        )
        await asyncio.sleep(1)

        # Copy to local
        await asyncio.create_subprocess_shell(
            f"scp dereadi@192.168.132.241:{remote_path} {local_path}"
        )
        await asyncio.sleep(1)

        # Send photo
        with open(local_path, 'rb') as photo:
            await update.message.reply_photo(photo, caption="sasass screen capture")

        await thinking_msg.delete()

    except Exception as e:
        await thinking_msg.edit_text(f"Screenshot error: {e}")
```

---

### Task 6: Proactive Notifications

Create `/ganuda/telegram_bot/proactive_notifications.py`:

```python
# Proactive notification system for group messages
# Add to TribeInterface class
GROUP_CHAT_ID = os.environ.get('TELEGRAM_GROUP_CHAT_ID')  # Set this in start_chief.sh

async def send_group_notification(self, message: str, parse_mode: str = None):
    """Send notification to the Telegram group"""
    if not GROUP_CHAT_ID:
        return {"error": "GROUP_CHAT_ID not configured"}

    try:
        from telegram import Bot
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=message,
            parse_mode=parse_mode
        )
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}
```

Add HTTP endpoint for external notifications (so other services can notify via Telegram):

```python
# This would be a separate service or added to the gateway
# For now, add a command that can be triggered externally

async def notify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send notification (TPM only): /notify <message>"""
    # Check if user is TPM (you can add user ID check)
    message = " ".join(context.args)
    if not message:
        await update.message.reply_text("Usage: /notify <message>")
        return

    # This just echoes for now - could be enhanced to broadcast
    await update.message.reply_text(f"Notification: {message}")
```

---

### Task 7: Update start_chief.sh

Create `/ganuda/telegram_bot/start_chief.sh`:

```bash
# Startup script with all required environment variables
#!/bin/bash
# Cherokee Chief Telegram Bot Startup
# For Seven Generations - Cherokee AI Federation

export TELEGRAM_BOT_TOKEN='7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8'
export TELEGRAM_GROUP_CHAT_ID='-1001234567890'  # TODO: Get actual group ID
export GATEWAY_URL='http://localhost:8080'

cd /ganuda/telegram_bot

# Kill any existing instance
pkill -f telegram_chief.py 2>/dev/null
sleep 2

# Start with logging
echo "[$(date)] Starting Cherokee Chief Telegram Bot..."
/home/dereadi/cherokee_venv/bin/python3 telegram_chief.py >> /ganuda/logs/telegram_chief.log 2>&1 &

PID=$!
echo $PID > /ganuda/telegram_bot/telegram_chief.pid
echo "[$(date)] Bot started with PID $PID"
```

---

### Task 8: Register All New Commands

Create `/ganuda/telegram_bot/command_registry.py`:

```python
# Command handler registration for main()
def main():
    """Start the bot"""
    if not BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set")
        return

    print("=" * 50)
    print("Cherokee Chief Telegram Bot v3.0")
    print("Full Tribe Integration Edition")
    print("=" * 50)

    # Create application
    app = Application.builder().token(BOT_TOKEN).build()

    # Core commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status))

    # Council commands
    app.add_handler(CommandHandler("pending", pending))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("veto", veto))
    app.add_handler(CommandHandler("ask", ask_command))

    # Monitoring commands
    app.add_handler(CommandHandler("health", health_command))
    app.add_handler(CommandHandler("concerns", concerns_command))

    # Memory commands
    app.add_handler(CommandHandler("remember", remember_command))
    app.add_handler(CommandHandler("seed", seed_command))

    # Ticket/Jr commands
    app.add_handler(CommandHandler("ticket", ticket_command))
    app.add_handler(CommandHandler("jrs", jrs_command))

    # FARA commands
    app.add_handler(CommandHandler("look", look_command))
    app.add_handler(CommandHandler("fara", fara_command))

    # Callbacks and messages
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Commands registered:")
    print("  /start, /help, /status")
    print("  /pending, /approve, /veto, /ask")
    print("  /health, /concerns")
    print("  /remember, /seed")
    print("  /ticket, /jrs")
    print("  /look, /fara")
    print()
    print("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
```

---

### Task 9: Update tribal_knowledge.py

Create `/ganuda/telegram_bot/tribal_knowledge_update.py`:

```python
# BigMac and Dr. Joe context additions
TRIBAL_KNOWLEDGE = {
    # ... existing entries ...

    "drjoe": """Dr. Joe is a Tribe ally building his own instance on BigMac.
Reach him in the Cherokee Training Operations Telegram group.
His endpoint: http://100.116.27.89:9001/bigmac/ask
Deployment docs: /ganuda/drjoe/BIGMAC_DEPLOYMENT_SUMMARY.md""",

    "telegram": """Cherokee has two Telegram bots:
- @derpatobot - Training operations, SAG Resource AI
- Cherokee Chief (this bot) - Tribe interface, Council voting

Group: Cherokee Training Operations
Invite: https://t.me/+6P1jUzrYvHYyNTQx""",

    "fara": """FARA (Flexible Autonomous Response Agent) runs on sasass Mac Studio.
Capabilities:
- /look [question] - Analyze screen visually
- /fara screenshot - Capture sasass screen
- Vision model: Uses Qwen2-VL or similar multimodal

Scripts: /Users/Shared/ganuda/scripts/fara_*.py""",
}
```

---

## SUCCESS CRITERIA

1. Bot starts without errors
2. `/health` command works (shows cluster health)
3. `/remember` command searches thermal memory
4. `/seed` command writes to thermal memory
5. `/ticket` command creates Jr work queue items
6. `/jrs` command shows pending Jr tasks
7. `/fara look` captures and analyzes sasass screen
8. Bot responds to messages in the Cherokee Training Operations group
9. Dr. Joe can interact with the Tribe via Telegram

---

## TESTING CHECKLIST

```bash
# 1. Start the bot
cd /ganuda/telegram_bot
./start_chief.sh

# 2. Check it's running
ps aux | grep telegram_chief

# 3. Check logs for errors
tail -f /ganuda/logs/telegram_chief.log

# 4. Test in Telegram:
/start
/status
/health
/remember council
/seed 75 Test memory from Telegram
/ticket 2 infra Test ticket creation
/jrs
/look What's on screen?
```

---

## DEPENDENCIES

Ensure these are installed in cherokee_venv:
```bash
pip install python-telegram-bot psycopg2-binary requests
```

---

*For Seven Generations - Cherokee AI Federation*
*"The Tribe speaks through many channels"*

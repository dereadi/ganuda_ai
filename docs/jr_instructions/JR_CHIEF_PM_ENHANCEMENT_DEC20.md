# Jr Instructions: Chief PM Enhancement - December 20, 2025

**Priority**: 1
**Assigned Jr**: it_triad_jr
**Context**: Chief needs to be a proper PM - talk to Tribe, do PM work, send work to Jrs

---

## OBJECTIVE

Enhance Chief Telegram bot to function as a Project Manager:
1. **Tribe Communication** - Query Council (ALREADY WORKS)
2. **PM Work** - Create tickets, track status, manage events
3. **Jr Tasking** - Queue work for Jrs with instruction files

---

## CURRENT STATE

Chief runs at `/ganuda/telegram_bot/telegram_chief.py` (PID running on redfin)

**Working Commands:**
- `/ask` - Council query
- `/health` - Cluster status
- `/remember` - Write thermal memory
- `/look` - Search thermal memory
- `/pending`, `/approve`, `/veto` - TPM voting

**Files Created but NOT Integrated:**
- `jr_queue_commands.py` - /jrs command
- `ticket_commands.py` - /ticket command
- `fara_integration.py` - enhanced /fara
- `thermal_memory_methods.py` - seed_memory()
- `proactive_notifications.py` - group alerts
- `command_registry.py` - handler registration

---

## PART 1: INTEGRATE JR QUEUE COMMANDS

### Task 1.1: Add Jr Queue Functions to Chief

Add to `/ganuda/telegram_bot/telegram_chief.py` (before `main()` function):

```python
# ==================== JR QUEUE COMMANDS ====================

import psycopg2

DB_CONFIG = {
    "host": "192.168.132.222",
    "database": "zammad_production",
    "user": "claude",
    "password": "jawaseatlasers2"
}

def get_db():
    return psycopg2.connect(**DB_CONFIG)


async def jrs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Jr work queue status."""
    try:
        conn = get_db()
        cur = conn.cursor()

        # Get pending tasks
        cur.execute("""
            SELECT title, assigned_jr, priority, status, created_at
            FROM jr_work_queue
            WHERE status IN ('pending', 'in_progress')
            ORDER BY priority, created_at DESC
            LIMIT 10
        """)
        tasks = cur.fetchall()

        if not tasks:
            await update.message.reply_text("No pending Jr tasks in queue.")
            return

        msg = "**Jr Work Queue:**\n\n"
        for task in tasks:
            title, jr, priority, status, created = task
            emoji = "🔴" if priority == 1 else "🟡" if priority == 2 else "🟢"
            status_emoji = "⏳" if status == 'pending' else "🔧"
            msg += f"{emoji} {status_emoji} **{title}**\n"
            msg += f"   Assigned: {jr} | P{priority}\n\n"

        cur.close()
        conn.close()
        await update.message.reply_text(msg, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")


async def jr_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create a Jr task. Usage: /jr <title> | <instruction summary>"""
    if not context.args:
        await update.message.reply_text(
            "Usage: /jr <title> | <instruction summary>\n"
            "Example: /jr Fix login bug | Check auth.py line 45, handle null token"
        )
        return

    text = ' '.join(context.args)

    # Parse title and instructions
    if '|' in text:
        title, instructions = text.split('|', 1)
        title = title.strip()
        instructions = instructions.strip()
    else:
        title = text
        instructions = "See thermal memory for context"

    try:
        conn = get_db()
        cur = conn.cursor()

        # Create instruction file
        import hashlib
        from datetime import datetime

        task_hash = hashlib.md5(f"{title}{datetime.now()}".encode()).hexdigest()[:12]
        instruction_file = f"/ganuda/docs/jr_instructions/JR_TELEGRAM_{task_hash}.md"

        # Write instruction file
        instruction_content = f"""# Jr Task: {title}

**Created**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Source**: Telegram Chief
**Priority**: 2

---

## Instructions

{instructions}

---

## Context

Query thermal memory for related work.

---

*For Seven Generations*
"""
        with open(instruction_file, 'w') as f:
            f.write(instruction_content)

        # Insert into queue
        cur.execute("""
            INSERT INTO jr_work_queue (task_id, title, assigned_jr, priority, status, instruction_file, created_at)
            VALUES (md5(%s || NOW()::text), %s, 'it_triad_jr', 2, 'pending', %s, NOW())
            RETURNING task_id
        """, (title, title, instruction_file))

        task_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        await update.message.reply_text(
            f"Jr task created!\n\n"
            f"**Title:** {title}\n"
            f"**Task ID:** {task_id[:8]}...\n"
            f"**Assigned:** it_triad_jr\n"
            f"**File:** {instruction_file}"
        , parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"Error creating task: {str(e)}")
```

### Task 1.2: Register Jr Commands

Add to `main()` function after other CommandHandlers:

```python
    app.add_handler(CommandHandler("jrs", jrs_command))
    app.add_handler(CommandHandler("jr", jr_command))
```

---

## PART 2: ADD TICKET CREATION

### Task 2.1: Add Ticket Command

Add to telegram_chief.py:

```python
async def ticket_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create a support ticket. Usage: /ticket <title> | <description>"""
    if not context.args:
        await update.message.reply_text(
            "Usage: /ticket <title> | <description>\n"
            "Example: /ticket Gateway timeout | Users reporting 504 errors on /ask"
        )
        return

    text = ' '.join(context.args)

    if '|' in text:
        title, description = text.split('|', 1)
    else:
        title = text
        description = "Created via Telegram Chief"

    try:
        conn = get_db()
        cur = conn.cursor()

        # Insert ticket into duyuktv_tickets
        cur.execute("""
            INSERT INTO duyuktv_tickets (title, description, status, priority, created_at)
            VALUES (%s, %s, 'open', 'medium', NOW())
            RETURNING id
        """, (title.strip(), description.strip()))

        ticket_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        await update.message.reply_text(
            f"Ticket created!\n\n"
            f"**ID:** #{ticket_id}\n"
            f"**Title:** {title.strip()}\n"
            f"**Status:** Open"
        , parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")
```

### Task 2.2: Register Ticket Command

Add to `main()`:

```python
    app.add_handler(CommandHandler("ticket", ticket_command))
```

---

## PART 3: ADD THERMAL MEMORY SEED

### Task 3.1: Add Seed Command

```python
async def seed_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Seed thermal memory with important info. Usage: /seed <content>"""
    if not context.args:
        await update.message.reply_text("Usage: /seed <content to remember>")
        return

    content = ' '.join(context.args)

    try:
        conn = get_db()
        cur = conn.cursor()

        import hashlib
        memory_hash = hashlib.md5(f"{content}{datetime.now()}".encode()).hexdigest()

        cur.execute("""
            INSERT INTO thermal_memory_archive (memory_hash, original_content, current_stage, temperature_score)
            VALUES (%s, %s, 'WHITE_HOT', 95)
            RETURNING id
        """, (memory_hash, content))

        mem_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        await update.message.reply_text(f"Seeded thermal memory #{mem_id} as WHITE_HOT")

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")
```

### Task 3.2: Register Seed Command

```python
    app.add_handler(CommandHandler("seed", seed_command))
```

---

## PART 4: ADD PROACTIVE NOTIFICATIONS

### Task 4.1: Add Group Chat ID

Add to top of telegram_chief.py:

```python
GROUP_CHAT_ID = os.environ.get('TELEGRAM_GROUP_CHAT_ID', '-1003439875431')
```

### Task 4.2: Add Notification Function

```python
async def notify_group(app, message: str):
    """Send proactive notification to group chat."""
    try:
        await app.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=message,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Failed to notify group: {e}")
```

---

## PART 5: UPDATE HELP COMMAND

Replace the help_command function:

```python
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all available commands."""
    help_text = """
**Cherokee Chief Bot - PM Edition**

**Tribe Communication:**
/ask <question> - Query 7-Specialist Council
/health - Check cluster status
/concerns - Show specialist concerns

**Memory:**
/look <query> - Search thermal memory
/remember <text> - Quick save to memory
/seed <content> - Seed WHITE_HOT memory

**PM Work:**
/ticket <title> | <desc> - Create support ticket
/jrs - Show Jr work queue
/jr <title> | <instructions> - Create Jr task

**TPM Oversight:**
/pending - Votes awaiting TPM decision
/approve <hash> - Approve pending vote
/veto <hash> - Veto pending vote

**Other:**
/status - Gateway status
/help - This message

_For Seven Generations_
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')
```

---

## SUCCESS CRITERIA

1. `/jrs` shows pending Jr tasks from queue
2. `/jr <title> | <instructions>` creates task with instruction file
3. `/ticket <title> | <desc>` creates support ticket
4. `/seed <content>` writes WHITE_HOT memory
5. Help shows all new commands
6. Bot restarts cleanly with new features

---

## TESTING

```bash
# Restart Chief
cd /ganuda/telegram_bot
pkill -f telegram_chief.py
source /home/dereadi/cherokee_venv/bin/activate
nohup python3 telegram_chief.py > /tmp/chief.log 2>&1 &

# Test in Telegram:
/jrs
/jr Test task | This is a test instruction
/ticket Test ticket | Testing ticket creation
/seed This is a test memory seed
/help
```

---

## RESTART SCRIPT UPDATE

Update `/ganuda/telegram_bot/start_chief.sh`:

```bash
#!/bin/bash
export TELEGRAM_BOT_TOKEN="your_token_here"
export TELEGRAM_GROUP_CHAT_ID="-1003439875431"

cd /ganuda/telegram_bot
source /home/dereadi/cherokee_venv/bin/activate
python3 telegram_chief.py
```

---

*For Seven Generations - Cherokee AI Federation*

# Jr Task: Enhance Telegram Chief Bot for Full Tribal Interaction

**Task ID:** task-telegram-chief-enhance
**Priority:** P1
**Node:** redfin
**Created:** December 21, 2025
**Requested By:** Chief (via TPM)

---

## Context

The Chief needs to fully interact with the Cherokee AI Federation through Telegram. Currently the bot exists at `/ganuda/telegram_bot/telegram_chief.py` but is missing key features.

**Current Bot Status:** Running (PID 2289265)

**Existing Commands:**
- `/status` - Cluster health
- `/pending` - Pending approvals
- `/approve <hash>` - Approve decision
- `/veto <hash> <reason>` - Veto decision
- `/ask <question>` - Query Council
- `/remember <query>` - Search thermal memory
- `/look <topic>` - Tribal knowledge lookup
- `/health` - Quick health check
- `/concerns` - View specialist concerns

---

## Required Enhancements

### 1. Thermal Memory - Full Interaction

**Current:** `/remember` only searches
**Needed:**
- View hot memories (top 10)
- Get full memory content
- See memory relationships
- Understand temperature meaning

```python
# New commands to add:

async def hot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/hot - Show hottest memories"""
    # Query: SELECT * FROM thermal_memory_archive ORDER BY temperature_score DESC LIMIT 10

async def memory_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/memory <hash> - Get full memory details"""
    # Show full content, temperature, relationships, when created

async def explain_thermal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/thermal - Explain what thermal memory is"""
    # Return the plain language explanation
```

### 2. Ticket Creation

**Current:** No ticket capability
**Needed:** Create tickets in duyuktv_tickets table

```python
async def ticket_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/ticket <title> - Create a new ticket"""
    # INSERT INTO duyuktv_tickets (title, description, tribal_agent, status, priority)
    # VALUES (title, context, 'chief', 'open', 'normal')

async def mytickets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/mytickets - Show Chief's open tickets"""
    # Query tickets where tribal_agent = 'chief' or assigned_to = 'chief'

async def closeticket_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/close <ticket_id> <resolution>"""
    # Update ticket status to 'resolved'
```

### 3. Executive Jr (TPM Delegate)

**Current:** Chief talks to Council only
**Needed:** Route to Executive Jr for complex tasks

The Executive Jr should:
- Receive delegated tasks from Chief
- Break them into sub-tasks
- Coordinate with other Jrs
- Report progress back to Chief

```python
async def delegate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/delegate <task> - Assign task to Executive Jr"""
    # Create task announcement
    # Notify Executive Jr
    # Track progress

async def taskstatus_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/taskstatus - Check delegated task progress"""
```

### 4. Tribe-Wide Communication

**Current:** Only Council access
**Needed:** Direct communication with any specialist or Jr

```python
async def talk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/talk <specialist> <message> - Direct message to specialist"""
    # Route to specific specialist for response
    # Specialists: crawdad, gecko, turtle, eagle_eye, spider, peace_chief, raven

async def jr_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/jr <agent_id> <task> - Assign task to specific Jr"""
    # Check jr_agent_state for agent
    # Create task announcement specifically for that Jr

async def tribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/tribe - Show active tribe members"""
    # List all specialists + active Jrs with their status
```

### 5. Natural Language Understanding

**Current:** Commands only
**Needed:** Natural language for common requests

```python
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced natural language handler"""
    text = update.message.text.lower()

    # Thermal memory queries
    if "what do you remember about" in text:
        # Extract topic, run /remember
    elif "hot memories" in text or "important memories" in text:
        # Run /hot

    # Ticket creation
    elif "create a ticket" in text or "new ticket" in text:
        # Parse and run /ticket

    # Status queries
    elif "who is online" in text or "tribe status" in text:
        # Run /tribe

    # Delegate to Council for everything else
```

---

## Implementation Steps

1. **Backup current bot:**
   ```bash
   cp /ganuda/telegram_bot/telegram_chief.py /ganuda/telegram_bot/telegram_chief.py.backup_$(date +%Y%m%d)
   ```

2. **Add new commands** (one at a time, test each)

3. **Update help text** to show all commands

4. **Restart bot:**
   ```bash
   kill $(cat /ganuda/telegram_bot/telegram_chief.pid)
   cd /ganuda/telegram_bot && nohup python telegram_chief.py &
   ```

5. **Test with Chief** via Telegram

---

## Database Tables Used

| Table | Purpose |
|-------|---------|
| thermal_memory_archive | Memory queries |
| memory_relationships | Show related memories |
| duyuktv_tickets | Ticket CRUD |
| jr_agent_state | Jr status |
| jr_task_announcements | Task delegation |
| jr_task_bids | Task assignment |

---

## Success Criteria

Chief can via Telegram:
1. ✅ Search thermal memory (`/remember` exists)
2. ⬜ View hot memories and understand them
3. ⬜ Create and track tickets
4. ⬜ Delegate tasks to Executive Jr
5. ⬜ Talk directly to any specialist
6. ⬜ See who's online in the tribe
7. ⬜ Use natural language for common tasks

---

## Security Notes

- Chief is authorized for all commands
- Sensitive operations still require Council approval
- All interactions logged to thermal memory
- TPM notified of significant decisions

---

*For Seven Generations - Cherokee AI Federation*

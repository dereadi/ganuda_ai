# Jr Task: Enhance Telegram Bot with Contextual Memory

**Task ID:** task-telegram-context-001
**Priority:** P2 (Enhancement)
**Node:** redfin
**Created:** December 22, 2025
**TPM:** Cherokee AI Federation

---

## Problem Statement

The Telegram Chief bot (`telegram_chief.py`) currently operates statelessly:
- Each query is independent with no conversation history
- Hot thermal memories are not used to enrich context
- Jr task system status is not visible
- Recent Council decisions don't inform new queries

This makes conversations feel disconnected and misses valuable context.

---

## Current Architecture

```
User Message
     │
     ▼
classify_request() ─────► "diagnostic" ──► Eagle Eye (direct)
     │
     ▼
"action/query/critical"
     │
     ▼
tribe.query_council(question)  ← ONE-SHOT, NO CONTEXT
     │
     ▼
format_council_response()
     │
     ▼
User Response
```

---

## Proposed Enhancement

### 1. Thermal Memory Context Injection

Before calling the Council, fetch hot memories relevant to the query:

```python
def get_thermal_context(query: str, limit: int = 3) -> str:
    """Fetch hot thermal memories related to query."""
    try:
        conn = psycopg2.connect(
            host='192.168.132.222',
            database='zammad_production',
            user='claude',
            password='jawaseatlasers2'
        )
        with conn.cursor() as cur:
            # Search by keyword relevance and temperature
            search_pattern = '%' + '%'.join(query.split()[:5]) + '%'
            cur.execute("""
                SELECT LEFT(original_content, 300), temperature_score
                FROM thermal_memory_archive
                WHERE original_content ILIKE %s
                  AND temperature_score > 60
                ORDER BY temperature_score DESC, created_at DESC
                LIMIT %s
            """, (search_pattern, limit))

            rows = cur.fetchall()
            if rows:
                context = "Relevant thermal memories:\n"
                for content, temp in rows:
                    context += f"- [{temp:.0f}°] {content}\n"
                return context
        conn.close()
    except:
        pass
    return ""
```

### 2. Conversation Session Tracking

Store recent messages per user in thermal memory:

```python
# In handle_message()
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message.text

    # Get last 3 messages from this user (if any)
    session_context = get_session_context(user.id, limit=3)

    # Build enriched question
    thermal_context = get_thermal_context(message)

    question = f"""Telegram user {user.first_name} asks: {message}

Previous messages in session:
{session_context}

{thermal_context}
"""

    result = tribe.query_council(question)

    # Store this interaction for future context
    store_session_message(user.id, message, result.get('consensus', '')[:500])
```

### 3. Jr Task Status Integration

Add commands to view and interact with the Jr bidding system:

```python
async def tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View Jr task status: /tasks"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT task_id, task_type, status, assigned_to,
                       LEFT(task_content, 80) as summary
                FROM jr_task_announcements
                WHERE announced_at > NOW() - INTERVAL '7 days'
                ORDER BY announced_at DESC
                LIMIT 10
            """)
            rows = cur.fetchall()

        if not rows:
            await update.message.reply_text("No recent tasks")
            return

        lines = ["Recent Jr Tasks:\n"]
        for task_id, ttype, status, assigned, summary in rows:
            status_emoji = {"open": "OPEN", "assigned": "ASGN",
                          "in_progress": "PROG", "completed": "DONE",
                          "failed": "FAIL"}.get(status, "?")
            lines.append(f"[{status_emoji}] {task_id[:20]}")
            lines.append(f"   {ttype} → {assigned or 'unassigned'}")
            lines.append(f"   {summary}...\n")

        await update.message.reply_text("\n".join(lines))
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def agents_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View active Jr agents: /agents"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT agent_id, node_name, specialization,
                       last_active, success_rate
                FROM jr_agent_state
                WHERE last_active > NOW() - INTERVAL '30 minutes'
                ORDER BY node_name, agent_id
            """)
            rows = cur.fetchall()

        if not rows:
            await update.message.reply_text("No active agents in last 30 minutes")
            return

        lines = [f"{len(rows)} Active Jr Agents:\n"]
        for agent, node, spec, active, rate in rows:
            ago = (datetime.now() - active).seconds // 60 if active else "?"
            lines.append(f"[{node}] {agent}")
            lines.append(f"   {spec} | {rate:.0%} success | {ago}m ago\n")

        await update.message.reply_text("\n".join(lines))
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
```

### 4. Hot Memory Alerts

New memories above temperature threshold get pushed to Telegram:

```python
# In a background task or triggered by thermal memory insertion
async def notify_hot_memory(bot, memory_content: str, temperature: float):
    """Push notification for very hot memories."""
    if temperature >= 90:
        # Notify TPM channel about critical memory
        await bot.send_message(
            chat_id=TPM_CHAT_ID,  # Configure this
            text=f"[HOT MEMORY {temperature:.0f}°]\n{memory_content[:500]}"
        )
```

---

## New Commands Summary

| Command | Purpose |
|---------|---------|
| `/tasks` | View recent Jr task announcements |
| `/agents` | View active Jr bidding agents |
| `/hot` | View hottest thermal memories (temp > 85) |
| `/session` | Show your conversation history |
| `/clear` | Clear your session context |

---

## Implementation Steps

### Step 1: Add Database Helper

```python
import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)
```

### Step 2: Create Session Table

```sql
-- On bluefin
CREATE TABLE IF NOT EXISTS telegram_sessions (
    session_id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    user_name VARCHAR(100),
    message TEXT,
    response_summary TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_telegram_sessions_user ON telegram_sessions(user_id, timestamp DESC);

-- Auto-cleanup old sessions (keep 7 days)
-- Add to cron or pheromone_decay.sh
-- DELETE FROM telegram_sessions WHERE timestamp < NOW() - INTERVAL '7 days';
```

### Step 3: Modify TribeInterface Class

Add method to get_db():

```python
class TribeInterface:
    def get_db(self):
        return psycopg2.connect(**DB_CONFIG)
```

### Step 4: Register New Handlers

```python
# In main()
app.add_handler(CommandHandler("tasks", tasks_command))
app.add_handler(CommandHandler("agents", agents_command))
app.add_handler(CommandHandler("hot", hot_memories_command))
app.add_handler(CommandHandler("session", session_command))
app.add_handler(CommandHandler("clear", clear_session_command))
```

### Step 5: Update /help

Add new commands to help text.

---

## Testing

```bash
# Test thermal context injection
# Send message: "What do we know about T5?"
# Should include thermal memories about T5 in context

# Test Jr task visibility
# /tasks should show the 4 research tasks

# Test agent status
# /agents should show 5 active agents across 4 nodes

# Test session tracking
# Ask 3 questions, then /session should show history
```

---

## Success Criteria

1. [ ] Thermal memories enrich Council queries
2. [ ] /tasks shows Jr task announcements
3. [ ] /agents shows active bidding agents
4. [ ] Session context persists across messages
5. [ ] /clear resets user's session
6. [ ] Hot memory notifications work (temp > 90)

---

## Security Considerations (Crawdad Review)

- Session data is per-user, no cross-user leakage
- Thermal memory queries are read-only
- No destructive operations added
- Rate limiting should be added to prevent spam

---

## Related Documents

- `telegram_chief.py` - Current bot code
- `KB_JR_BIDDING_EXECUTOR_SYSTEM.md` - Jr system overview
- `KB_THERMAL_MEMORY_EXPLAINED.md` - Thermal memory concepts

---

*For Seven Generations - Cherokee AI Federation*

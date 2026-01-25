# Jr Task: Implement Telegram Bot Enhancements

**Task ID:** task-impl-telegram-001
**Priority:** P2 (Feature Enhancement)
**Created:** December 22, 2025
**TPM:** Cherokee AI Federation
**Based On:** task-telegram-context-001_impl_plan.md

---

## Overview

Enhance the Telegram Chief bot with contextual memory integration and new command capabilities.

---

## Implementation Tasks

### Task 1: Create telegram_sessions Table

Create database table for session tracking:

```sql
CREATE TABLE telegram_sessions (
    session_id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    chat_id BIGINT NOT NULL,
    start_time TIMESTAMP DEFAULT NOW(),
    last_activity TIMESTAMP DEFAULT NOW(),
    context_data JSONB DEFAULT '{}',
    active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_telegram_sessions_user ON telegram_sessions(user_id);
CREATE INDEX idx_telegram_sessions_chat ON telegram_sessions(chat_id);
```

### Task 2: Add Session Management to telegram_chief.py

**File:** `/ganuda/services/telegram_chief/telegram_chief.py`

Add session tracking methods:

```python
def get_or_create_session(self, user_id: int, chat_id: int) -> int:
    """Get existing session or create new one."""
    conn = self.get_db()
    with conn.cursor() as cur:
        # Check for existing active session
        cur.execute("""
            SELECT session_id FROM telegram_sessions
            WHERE user_id = %s AND chat_id = %s AND active = TRUE
            ORDER BY last_activity DESC LIMIT 1
        """, (user_id, chat_id))
        result = cur.fetchone()

        if result:
            session_id = result[0]
            cur.execute("""
                UPDATE telegram_sessions
                SET last_activity = NOW()
                WHERE session_id = %s
            """, (session_id,))
        else:
            cur.execute("""
                INSERT INTO telegram_sessions (user_id, chat_id)
                VALUES (%s, %s) RETURNING session_id
            """, (user_id, chat_id))
            session_id = cur.fetchone()[0]

        conn.commit()
        return session_id
```

### Task 3: Implement Thermal Memory Context Injection

Add thermal context to Council queries:

```python
def inject_thermal_context(self, session_id: int, query: str) -> str:
    """Inject relevant thermal memories into query context."""
    conn = self.get_db()
    with conn.cursor() as cur:
        # Get hot memories relevant to query
        cur.execute("""
            SELECT LEFT(original_content, 500), temperature_score
            FROM thermal_memory_archive
            WHERE original_content ILIKE %s
            ORDER BY temperature_score DESC
            LIMIT 3
        """, (f'%{query[:50]}%',))

        context = ""
        for content, temp in cur.fetchall():
            context += f"[Memory {temp:.0f}C]: {content}\n"

        return f"CONTEXT:\n{context}\n\nQUERY: {query}"
```

### Task 4: Add /tasks and /agents Commands

Add new command handlers:

```python
async def handle_tasks_command(self, update, context):
    """Show tasks from Jr system."""
    conn = self.get_db()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT task_id, task_type, status, LEFT(task_content, 100)
            FROM jr_task_announcements
            WHERE status IN ('open', 'assigned', 'in_progress')
            ORDER BY priority, announced_at DESC
            LIMIT 10
        """)
        tasks = cur.fetchall()

    if not tasks:
        await update.message.reply_text("No active tasks.")
        return

    msg = "Active Tasks:\n"
    for task_id, task_type, status, content in tasks:
        msg += f"\n{task_id} [{status}] ({task_type})\n  {content}...\n"

    await update.message.reply_text(msg)

async def handle_agents_command(self, update, context):
    """Show Jr agents status."""
    conn = self.get_db()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT agent_id, node_name, specialization,
                   last_active, success_rate
            FROM jr_agent_state
            ORDER BY last_active DESC
        """)
        agents = cur.fetchall()

    msg = "Jr Agents:\n"
    for agent_id, node, spec, active, rate in agents:
        status = "ONLINE" if active else "OFFLINE"
        msg += f"\n{agent_id} @ {node}\n  Spec: {spec}, Rate: {rate:.0%}\n"

    await update.message.reply_text(msg)
```

### Task 5: Fix get_db() in TribeInterface

**File:** `/ganuda/lib/tribe_interface.py`

Add missing method:

```python
def get_db(self):
    """Get database connection."""
    import psycopg2
    if not hasattr(self, '_db_conn') or self._db_conn.closed:
        self._db_conn = psycopg2.connect(
            host='192.168.132.222',
            database='zammad_production',
            user='claude',
            password='jawaseatlasers2'
        )
    return self._db_conn
```

### Task 6: Implement Hot Memory Notifications

Add temperature monitoring:

```python
async def check_hot_memories(self, context):
    """Check for hot memories (temp > 90) and notify."""
    conn = self.get_db()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT memory_hash, LEFT(original_content, 200), temperature_score
            FROM thermal_memory_archive
            WHERE temperature_score > 90
            AND created_at > NOW() - INTERVAL '1 hour'
            AND NOT notified
            ORDER BY temperature_score DESC
            LIMIT 5
        """)
        hot = cur.fetchall()

        if hot:
            for hash, content, temp in hot:
                await context.bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text=f"HOT MEMORY ALERT [{temp:.0f}C]:\n{content}"
                )
                cur.execute("""
                    UPDATE thermal_memory_archive
                    SET notified = TRUE
                    WHERE memory_hash = %s
                """, (hash,))
            conn.commit()
```

---

## Deployment Steps

1. Run SQL to create telegram_sessions table on bluefin
2. Update telegram_chief.py with session management
3. Add thermal context injection to Council queries
4. Register new /tasks and /agents commands
5. Fix TribeInterface.get_db()
6. Add hot memory notification background job
7. Restart Telegram Chief service
8. Test all new functionality

---

## Success Criteria

- [ ] telegram_sessions table exists and tracks user sessions
- [ ] /tasks command shows active Jr tasks
- [ ] /agents command shows Jr agent status
- [ ] Council queries include thermal memory context
- [ ] Hot memories (>90C) trigger admin notifications
- [ ] TribeInterface.get_db() works correctly

---

*For Seven Generations - Cherokee AI Federation*

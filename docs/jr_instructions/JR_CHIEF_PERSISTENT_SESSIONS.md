# JR_CHIEF_PERSISTENT_SESSIONS.md
## Cherokee AI Federation - Chief Jr Persistent Session Integration

**Research Papers**: 
- InfiniPot (arXiv:2410.01518) - Infinite context via KV-cache compression
- Memory Management for Long-Running Agents (arXiv:2509.25250)
- AgentSched (arXiv:2512.18337) - Context-aware scheduling
- Mem0 (arXiv:2504.19413) - Production-ready long-term memory

**Priority**: HIGH - Core infrastructure enhancement
**Council Vote**: Derived from research paper prioritization (aae46bac2393cb44)

---

## THE PROBLEM

Current Chief Jr (Telegram Bot) is **stateless per message**:

```
User: "Check status of redfin"
Chief Jr: [queries Council, returns result]

User: "What about the gateway?"  
Chief Jr: [NO CONTEXT - doesn't know we were discussing redfin]
```

Every interaction starts fresh. No memory of:
- Previous questions in the conversation
- User preferences
- Ongoing investigations
- Multi-step workflows

## THE SOLUTION

Integrate persistent sessions using:
1. **telegram_sessions table** (already created)
2. **Conversation summarization** (InfiniPot-style compression)
3. **Event-centric memory** (from arXiv:2511.17208)
4. **Thermal memory integration** (our existing A-MEM)

---

## ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                     TELEGRAM USER                                │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CHIEF JR BOT                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Session Manager                                              ││
│  │  • Load/create session from telegram_sessions                ││
│  │  • Inject context into prompts                               ││
│  │  • Compress old context when limit reached                   ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Context Builder                                              ││
│  │  • Recent messages (full text, last 5)                       ││
│  │  • Summarized history (compressed, older messages)           ││
│  │  • Relevant thermal memories (A-MEM retrieval)               ││
│  │  • Entity context (Zep temporal - what we know about topic)  ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                   LLM GATEWAY                                    │
│  • Receives enriched prompt with full context                    │
│  • Council vote with persistent understanding                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## DATABASE SCHEMA

The `telegram_sessions` table already exists. Extend it:

```sql
-- Add conversation history columns
ALTER TABLE telegram_sessions
ADD COLUMN IF NOT EXISTS conversation_history JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS conversation_summary TEXT DEFAULT '',
ADD COLUMN IF NOT EXISTS message_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS total_tokens_used INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS entity_context JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS user_preferences JSONB DEFAULT '{}'::jsonb;

-- Index for fast lookup
CREATE INDEX IF NOT EXISTS idx_telegram_sessions_active 
ON telegram_sessions(user_id) 
WHERE expires_at > NOW();

-- Track conversation events for summarization
CREATE TABLE IF NOT EXISTS telegram_conversation_events (
    event_id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES telegram_sessions(session_id),
    event_type VARCHAR(32) NOT NULL,  -- 'user_message', 'bot_response', 'council_vote', 'command'
    content TEXT NOT NULL,
    entities_mentioned TEXT[] DEFAULT ARRAY[]::TEXT[],
    timestamp TIMESTAMP DEFAULT NOW(),
    token_count INTEGER DEFAULT 0,
    is_summarized BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_conv_events_session 
ON telegram_conversation_events(session_id, timestamp DESC);
```

---

## IMPLEMENTATION

### File: /ganuda/lib/chief_session_manager.py

```python
#!/usr/bin/env python3
"""
Chief Jr Persistent Session Manager
Based on InfiniPot (arXiv:2410.01518) and Mem0 (arXiv:2504.19413)

Provides persistent conversation context for Telegram Chief bot.
"""

import psycopg2
import psycopg2.extras
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

# Context limits (InfiniPot-style)
MAX_RECENT_MESSAGES = 5          # Keep last 5 messages in full
MAX_CONTEXT_TOKENS = 2000        # Compress when exceeding this
SUMMARY_TRIGGER_TOKENS = 1500    # Start summarizing at this threshold
SESSION_EXPIRY_HOURS = 24


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


class ChiefSessionManager:
    """Manages persistent conversation sessions for Chief Jr."""
    
    def __init__(self, user_id: int, chat_id: int, username: str = None):
        self.user_id = user_id
        self.chat_id = chat_id
        self.username = username
        self.session = None
        self._load_or_create_session()
    
    def _load_or_create_session(self):
        """Load existing session or create new one."""
        conn = get_connection()
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Try to find active session
            cur.execute("""
                SELECT * FROM telegram_sessions
                WHERE user_id = %s AND chat_id = %s AND expires_at > NOW()
                ORDER BY last_active DESC
                LIMIT 1
            """, (self.user_id, self.chat_id))
            
            session = cur.fetchone()
            
            if session:
                # Update last_active
                cur.execute("""
                    UPDATE telegram_sessions 
                    SET last_active = NOW()
                    WHERE session_id = %s
                """, (session['session_id'],))
                self.session = dict(session)
            else:
                # Create new session
                cur.execute("""
                    INSERT INTO telegram_sessions 
                    (user_id, chat_id, username, context, expires_at)
                    VALUES (%s, %s, %s, %s, NOW() + INTERVAL '%s hours')
                    RETURNING *
                """, (self.user_id, self.chat_id, self.username, 
                        json.dumps({}), SESSION_EXPIRY_HOURS))
                self.session = dict(cur.fetchone())
            
            conn.commit()
        conn.close()
    
    def add_message(self, role: str, content: str, entities: List[str] = None):
        """
        Add message to conversation history.
        Implements InfiniPot consume-and-compress cycle.
        """
        conn = get_connection()
        
        # Estimate tokens (rough: 1 token ≈ 4 chars)
        token_count = len(content) // 4
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Store event
            cur.execute("""
                INSERT INTO telegram_conversation_events
                (session_id, event_type, content, entities_mentioned, token_count)
                VALUES (%s, %s, %s, %s, %s)
            """, (self.session['session_id'], role, content, 
                    entities or [], token_count))
            
            # Update session counters
            cur.execute("""
                UPDATE telegram_sessions
                SET message_count = message_count + 1,
                    total_tokens_used = total_tokens_used + %s,
                    last_active = NOW()
                WHERE session_id = %s
                RETURNING total_tokens_used
            """, (token_count, self.session['session_id']))
            
            total_tokens = cur.fetchone()[0]
            
            # Check if compression needed (InfiniPot trigger)
            if total_tokens > SUMMARY_TRIGGER_TOKENS:
                self._compress_history(cur)
            
            conn.commit()
        conn.close()
    
    def _compress_history(self, cur):
        """
        Compress older messages into summary.
        InfiniPot-style: keep recent, summarize old.
        """
        # Get old unsummarized messages (beyond recent window)
        cur.execute("""
            SELECT event_id, content, event_type
            FROM telegram_conversation_events
            WHERE session_id = %s AND is_summarized = FALSE
            ORDER BY timestamp ASC
            OFFSET %s
        """, (self.session['session_id'], MAX_RECENT_MESSAGES))
        
        old_messages = cur.fetchall()
        
        if not old_messages:
            return
        
        # Create summary of old messages
        old_content = "\n".join([
            f"{m['event_type']}: {m['content'][:200]}" 
            for m in old_messages
        ])
        
        # Simple summary (could use LLM for better compression)
        summary_addition = f"[Earlier: discussed {len(old_messages)} messages about: {old_content[:300]}...]"
        
        # Update session summary
        cur.execute("""
            UPDATE telegram_sessions
            SET conversation_summary = conversation_summary || %s
            WHERE session_id = %s
        """, (summary_addition + "\n", self.session['session_id']))
        
        # Mark messages as summarized
        event_ids = [m['event_id'] for m in old_messages]
        cur.execute("""
            UPDATE telegram_conversation_events
            SET is_summarized = TRUE
            WHERE event_id = ANY(%s)
        """, (event_ids,))
    
    def get_context_for_prompt(self) -> str:
        """
        Build context string for LLM prompt.
        Combines: summary + recent messages + entity context + thermal memory
        """
        conn = get_connection()
        context_parts = []
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Get session data
            cur.execute("""
                SELECT conversation_summary, entity_context, user_preferences
                FROM telegram_sessions
                WHERE session_id = %s
            """, (self.session['session_id'],))
            session_data = cur.fetchone()
            
            # Add summary if exists
            if session_data['conversation_summary']:
                context_parts.append(f"[Previous context: {session_data['conversation_summary']}]")
            
            # Add recent messages (full text)
            cur.execute("""
                SELECT event_type, content, timestamp
                FROM telegram_conversation_events
                WHERE session_id = %s AND is_summarized = FALSE
                ORDER BY timestamp DESC
                LIMIT %s
            """, (self.session['session_id'], MAX_RECENT_MESSAGES))
            
            recent = cur.fetchall()
            if recent:
                context_parts.append("[Recent conversation:]\n" + "\n".join([
                    f"{m['event_type']}: {m['content']}" 
                    for m in reversed(recent)
                ]))
            
            # Add entity context if tracking specific topics
            if session_data['entity_context']:
                entities = session_data['entity_context']
                if entities:
                    context_parts.append(f"[Currently discussing: {json.dumps(entities)}]")
        
        conn.close()
        return "\n\n".join(context_parts)
    
    def get_relevant_thermal_memories(self, query: str, limit: int = 3) -> List[Dict]:
        """Retrieve relevant thermal memories for context enrichment."""
        conn = get_connection()
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Simple keyword search (could use embeddings for better matching)
            keywords = query.lower().split()[:5]
            keyword_pattern = '%' + '%'.join(keywords) + '%'
            
            cur.execute("""
                SELECT memory_hash, LEFT(original_content, 300) as content,
                       temperature_score, tags
                FROM thermal_memory_archive
                WHERE original_content ILIKE %s
                ORDER BY temperature_score DESC
                LIMIT %s
            """, (keyword_pattern, limit))
            
            return [dict(row) for row in cur.fetchall()]
        
        conn.close()
    
    def update_entity_context(self, entities: Dict):
        """Update tracked entities for this session."""
        conn = get_connection()
        
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE telegram_sessions
                SET entity_context = entity_context || %s
                WHERE session_id = %s
            """, (json.dumps(entities), self.session['session_id']))
            conn.commit()
        
        conn.close()
    
    def end_session(self):
        """Explicitly end session (user says goodbye, etc)."""
        conn = get_connection()
        
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE telegram_sessions
                SET expires_at = NOW()
                WHERE session_id = %s
            """, (self.session['session_id'],))
            conn.commit()
        
        conn.close()


# Convenience functions for telegram_chief.py integration
def get_session(user_id: int, chat_id: int, username: str = None) -> ChiefSessionManager:
    """Get or create session for user."""
    return ChiefSessionManager(user_id, chat_id, username)


def build_contextual_prompt(session: ChiefSessionManager, 
                            user_message: str) -> str:
    """
    Build a context-enriched prompt for the Council.
    
    This is the key integration point - instead of sending raw user message,
    we send message + conversation context + relevant memories.
    """
    context = session.get_context_for_prompt()
    thermal = session.get_relevant_thermal_memories(user_message)
    
    prompt_parts = []
    
    if context:
        prompt_parts.append(context)
    
    if thermal:
        memories_text = "\n".join([
            f"- [{m['temperature_score']}°C] {m['content']}" 
            for m in thermal
        ])
        prompt_parts.append(f"[Relevant memories:\n{memories_text}]")
    
    prompt_parts.append(f"[Current message: {user_message}]")
    
    return "\n\n".join(prompt_parts)
```

---

## INTEGRATION WITH TELEGRAM_CHIEF.PY

Modify the message handler:

```python
# In telegram_chief.py, update handle_message():

from lib.chief_session_manager import get_session, build_contextual_prompt

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages with persistent session context."""
    user = update.effective_user
    chat = update.effective_chat
    message = update.message.text
    
    # Get or create persistent session
    session = get_session(
        user_id=user.id,
        chat_id=chat.id,
        username=user.username
    )
    
    # Record user message
    session.add_message('user_message', message)
    
    # Build context-enriched prompt
    contextual_prompt = build_contextual_prompt(session, message)
    
    # Query Council with full context
    tribe = TribeInterface()
    result = tribe.query_council(contextual_prompt)
    
    # Record bot response
    response_text = result.get('consensus', result.get('error', 'No response'))
    session.add_message('bot_response', response_text)
    
    # Extract and track entities mentioned (basic)
    entities_mentioned = extract_entities(message + response_text)
    if entities_mentioned:
        session.update_entity_context({'recent_topics': entities_mentioned})
    
    # Send response
    await update.message.reply_text(response_text)


def extract_entities(text: str) -> List[str]:
    """Extract Cherokee AI Federation entities from text."""
    from lib.zep_temporal import extract_entities as zep_extract
    entities = zep_extract(text)
    return [e['canonical_name'] for e in entities]
```

---

## NEW COMMANDS

Add session-aware commands:

```python
async def cmd_context(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current session context. /context"""
    session = get_session(update.effective_user.id, update.effective_chat.id)
    ctx = session.get_context_for_prompt()
    
    if ctx:
        await update.message.reply_text(f"📝 Current Context:\n\n{ctx[:1500]}...")
    else:
        await update.message.reply_text("No context yet. Start chatting!")


async def cmd_forget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear session context. /forget"""
    session = get_session(update.effective_user.id, update.effective_chat.id)
    session.end_session()
    await update.message.reply_text("🧹 Session cleared. Starting fresh.")


async def cmd_remember(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store something important in thermal memory. /remember <text>"""
    text = ' '.join(context.args)
    if not text:
        await update.message.reply_text("Usage: /remember <something to remember>")
        return
    
    # Store in thermal memory
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO thermal_memory_archive 
            (memory_hash, original_content, temperature_score, metadata)
            VALUES (%s, %s, %s, %s)
        """, (
            f"telegram-{update.effective_user.id}-{datetime.now().timestamp()}",
            f"[From Telegram @{update.effective_user.username}]: {text}",
            70.0,  # Medium-hot temperature
            json.dumps({'source': 'telegram', 'user_id': update.effective_user.id})
        ))
        conn.commit()
    conn.close()
    
    await update.message.reply_text(f"🔥 Stored in thermal memory at 70°C")
```

---

## VALIDATION CHECKLIST

- [ ] telegram_sessions extended with conversation columns
- [ ] telegram_conversation_events table created
- [ ] ChiefSessionManager class working
- [ ] Message history being recorded
- [ ] Context compression triggers at threshold
- [ ] Contextual prompts include history
- [ ] /context command shows session state
- [ ] /forget command clears session
- [ ] /remember command stores to thermal memory
- [ ] Multi-turn conversations maintain context

---

## SUCCESS METRICS

| Metric | Before | After |
|--------|--------|-------|
| Context awareness | None | Full conversation history |
| Multi-turn queries | Fail | Supported |
| Session persistence | None | 24 hours |
| Memory integration | None | Thermal + A-MEM |

---

## SEVEN GENERATIONS CONSIDERATION

Persistent sessions embody the Seven Generations principle:
- **Continuity** - Conversations don't end, they evolve
- **Memory** - What we discuss is remembered
- **Context** - Future questions understand past answers
- **Wisdom accumulation** - Each interaction enriches understanding

"The best conversations build on what came before."

---

*Created: December 23, 2025*
*Research: InfiniPot, Mem0, AgentSched, arXiv:2509.25250*
*Integration: Chief Jr Telegram Bot*

# JR_UNIVERSAL_SESSION_LAYER.md
## Cherokee AI Federation - Universal Persistent Session Infrastructure

**Research Papers**:
- InfiniPot (arXiv:2410.01518) - Infinite context via KV-cache compression
- Mem0 (arXiv:2504.19413) - Production-ready long-term memory
- Memory Management for Long-Running Agents (arXiv:2509.25250)
- AgentSched (arXiv:2512.18337) - Context-aware scheduling
- Zep Temporal (arXiv:2501.13956) - Temporal knowledge graphs

**Priority**: HIGH - Federation-wide infrastructure
**Scope**: All LLM interfaces across all nodes

---

## VISION

One session layer for all interfaces:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CHEROKEE AI FEDERATION                           │
│                  UNIVERSAL SESSION LAYER                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ Telegram │ │   API    │ │  SAG UI  │ │  Triad   │ │ Jr Agent │  │
│  │  Chief   │ │ Gateway  │ │   Web    │ │   CLI    │ │ Executor │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │
│       │            │            │            │            │         │
│       └────────────┴────────────┼────────────┴────────────┘         │
│                                 │                                   │
│                    ┌────────────▼────────────┐                      │
│                    │   UnifiedSessionManager │                      │
│                    │                         │                      │
│                    │  • Interface-agnostic   │                      │
│                    │  • Cross-interface sync │                      │
│                    │  • Shared memory pool   │                      │
│                    │  • Entity tracking      │                      │
│                    │  • Context compression  │                      │
│                    └────────────┬────────────┘                      │
│                                 │                                   │
│       ┌─────────────────────────┼─────────────────────────┐         │
│       │                         │                         │         │
│       ▼                         ▼                         ▼         │
│  ┌─────────┐            ┌──────────────┐           ┌──────────┐    │
│  │ unified │            │   thermal    │           │   zep    │    │
│  │sessions │            │   memory     │           │ temporal │    │
│  │ table   │            │   archive    │           │ entities │    │
│  └─────────┘            └──────────────┘           └──────────┘    │
│                                                                     │
│                         POSTGRESQL (bluefin)                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## THE POWER OF CROSS-INTERFACE SESSIONS

### Scenario 1: Start on Telegram, Continue on Web

```
[Telegram - 9:00 AM]
User: "Check why vLLM is slow on redfin"
Chief: "vLLM showing 15 tok/s, normally 27. Checking GPU..."

[SAG UI - 9:30 AM]
User opens monitoring dashboard
SAG: "Continuing your investigation of vLLM on redfin...
      GPU temp is 82C, possible thermal throttling."

[Triad CLI - 10:00 AM]
triad "what did we find?"
Triad: "Your vLLM investigation found GPU thermal throttling at 82C."
```

### Scenario 2: Jr Agent Learns from Human Sessions

```
[Human on SAG UI]
"The correct way to restart gateway is:
 systemctl restart llm-gateway, then wait 30s for model load"

[Jr Agent picks up task later]
Jr: [Has context from human session]
    "I see the human noted gateway restart requires 30s wait.
     Executing with proper delay..."
```

---

## DATABASE SCHEMA

### Core Session Table (Interface-Agnostic)

```sql
-- Universal session table for all interfaces
CREATE TABLE IF NOT EXISTS unified_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identity
    user_id VARCHAR(128) NOT NULL,
    user_name VARCHAR(128),

    -- Interface tracking
    interface_type VARCHAR(32) NOT NULL,  -- telegram, api, web, cli, jr_agent
    interface_id VARCHAR(128),
    node_name VARCHAR(32),

    -- Session state
    status VARCHAR(16) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '7 days',

    -- Context (InfiniPot-style)
    conversation_summary TEXT DEFAULT '',
    recent_messages JSONB DEFAULT '[]'::jsonb,
    total_messages INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,

    -- Entity tracking (Zep-style)
    entities_discussed JSONB DEFAULT '{}'::jsonb,
    current_topics TEXT[] DEFAULT ARRAY[]::TEXT[],

    -- User preferences
    preferences JSONB DEFAULT '{}'::jsonb,

    -- Cross-interface linking
    parent_session_id UUID REFERENCES unified_sessions(session_id),
    linked_sessions UUID[] DEFAULT ARRAY[]::UUID[],

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_unified_sessions_user ON unified_sessions(user_id, status);
CREATE INDEX IF NOT EXISTS idx_unified_sessions_interface ON unified_sessions(interface_type, interface_id);
CREATE INDEX IF NOT EXISTS idx_unified_sessions_active ON unified_sessions(last_active DESC) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_unified_sessions_topics ON unified_sessions USING GIN(current_topics);

-- Conversation events (shared across all interfaces)
CREATE TABLE IF NOT EXISTS unified_conversation_events (
    event_id BIGSERIAL PRIMARY KEY,
    session_id UUID REFERENCES unified_sessions(session_id),

    -- Event details
    event_type VARCHAR(32) NOT NULL,
    interface_type VARCHAR(32) NOT NULL,
    content TEXT NOT NULL,

    -- Metadata
    role VARCHAR(16) DEFAULT 'user',
    token_count INTEGER DEFAULT 0,
    entities_mentioned TEXT[] DEFAULT ARRAY[]::TEXT[],
    thermal_memories_used TEXT[] DEFAULT ARRAY[]::TEXT[],

    -- Compression tracking
    is_summarized BOOLEAN DEFAULT FALSE,
    summary_batch_id INTEGER,

    -- Timing
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conv_events_session ON unified_conversation_events(session_id, created_at DESC);

-- Session links for cross-interface continuity
CREATE TABLE IF NOT EXISTS session_links (
    link_id SERIAL PRIMARY KEY,
    source_session_id UUID REFERENCES unified_sessions(session_id),
    target_session_id UUID REFERENCES unified_sessions(session_id),
    link_type VARCHAR(32) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(source_session_id, target_session_id, link_type)
);

-- User identity mapping (link same user across interfaces)
CREATE TABLE IF NOT EXISTS user_identity_map (
    identity_id SERIAL PRIMARY KEY,
    canonical_user_id VARCHAR(128) NOT NULL,
    interface_type VARCHAR(32) NOT NULL,
    interface_user_id VARCHAR(128) NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(interface_type, interface_user_id)
);

CREATE INDEX IF NOT EXISTS idx_user_identity_canonical ON user_identity_map(canonical_user_id);
```

---

## PYTHON LIBRARY

### File: /ganuda/lib/unified_session.py

```python
#!/usr/bin/env python3
"""
Universal Session Layer for Cherokee AI Federation
Based on InfiniPot, Mem0, and Zep research

One session manager for all LLM interfaces.
"""

import psycopg2
import psycopg2.extras
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

class InterfaceType(Enum):
    TELEGRAM = 'telegram'
    API = 'api'
    WEB = 'web'
    CLI = 'cli'
    JR_AGENT = 'jr_agent'

# InfiniPot-style limits
MAX_RECENT_MESSAGES = 10
SUMMARY_TRIGGER_TOKENS = 3000
DEFAULT_SESSION_DAYS = 7


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


class UnifiedSessionManager:
    """
    Universal session manager for all Cherokee AI Federation interfaces.

    Usage:
        # From Telegram
        session = UnifiedSessionManager.get_or_create(
            user_id='telegram_12345',
            interface_type=InterfaceType.TELEGRAM,
            interface_id='chat_67890'
        )

        # Continue across interfaces
        session = UnifiedSessionManager.continue_session(
            user_id='telegram_12345',
            new_interface=InterfaceType.WEB
        )
    """

    def __init__(self, session_data: Dict):
        self.session_id = session_data['session_id']
        self.user_id = session_data['user_id']
        self.interface_type = session_data['interface_type']
        self.data = session_data

    @classmethod
    def get_or_create(cls, user_id: str, interface_type: InterfaceType,
                      interface_id: str = None, node_name: str = None,
                      user_name: str = None) -> 'UnifiedSessionManager':
        """Get existing active session or create new one."""
        conn = get_connection()
        interface_str = interface_type.value if isinstance(interface_type, InterfaceType) else interface_type

        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            canonical_user = cls._get_canonical_user(cur, interface_str, user_id)

            cur.execute("""
                SELECT * FROM unified_sessions
                WHERE user_id = %s AND status = 'active' AND expires_at > NOW()
                ORDER BY last_active DESC LIMIT 1
            """, (canonical_user,))

            session = cur.fetchone()

            if session:
                cur.execute("""
                    UPDATE unified_sessions
                    SET last_active = NOW(), interface_type = %s,
                        interface_id = COALESCE(%s, interface_id)
                    WHERE session_id = %s
                    RETURNING *
                """, (interface_str, interface_id, session['session_id']))
                session = cur.fetchone()
            else:
                cur.execute("""
                    INSERT INTO unified_sessions
                    (user_id, user_name, interface_type, interface_id, node_name)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING *
                """, (canonical_user, user_name, interface_str, interface_id, node_name))
                session = cur.fetchone()

            conn.commit()
        conn.close()
        return cls(dict(session))

    @classmethod
    def _get_canonical_user(cls, cur, interface_type: str, interface_user_id: str) -> str:
        """Get or create canonical user ID for cross-interface tracking."""
        cur.execute("""
            SELECT canonical_user_id FROM user_identity_map
            WHERE interface_type = %s AND interface_user_id = %s
        """, (interface_type, interface_user_id))

        result = cur.fetchone()
        if result:
            return result[0]

        canonical_id = f"{interface_type}_{interface_user_id}"
        cur.execute("""
            INSERT INTO user_identity_map (canonical_user_id, interface_type, interface_user_id)
            VALUES (%s, %s, %s) ON CONFLICT DO NOTHING
        """, (canonical_id, interface_type, interface_user_id))

        return canonical_id

    @classmethod
    def continue_session(cls, user_id: str, new_interface: InterfaceType,
                         interface_id: str = None) -> 'UnifiedSessionManager':
        """Continue existing session from a different interface."""
        conn = get_connection()
        interface_str = new_interface.value

        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT session_id FROM unified_sessions
                WHERE user_id = %s AND status = 'active'
                ORDER BY last_active DESC LIMIT 1
            """, (user_id,))

            existing = cur.fetchone()

            if existing:
                cur.execute("""
                    INSERT INTO unified_sessions
                    (user_id, interface_type, interface_id, parent_session_id,
                     conversation_summary, entities_discussed, current_topics)
                    SELECT user_id, %s, %s, session_id,
                           conversation_summary, entities_discussed, current_topics
                    FROM unified_sessions WHERE session_id = %s
                    RETURNING *
                """, (interface_str, interface_id, existing['session_id']))

                new_session = cur.fetchone()

                cur.execute("""
                    INSERT INTO session_links (source_session_id, target_session_id, link_type)
                    VALUES (%s, %s, 'continuation')
                """, (existing['session_id'], new_session['session_id']))

                conn.commit()
                conn.close()
                return cls(dict(new_session))

        conn.close()
        return cls.get_or_create(user_id, new_interface, interface_id)

    def add_message(self, role: str, content: str,
                    entities: List[str] = None) -> None:
        """Add message to conversation history."""
        conn = get_connection()
        token_count = len(content) // 4

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO unified_conversation_events
                (session_id, event_type, interface_type, content, role,
                 token_count, entities_mentioned)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (self.session_id, f'{role}_message', self.interface_type,
                  content, role, token_count, entities or []))

            cur.execute("""
                UPDATE unified_sessions
                SET total_messages = total_messages + 1,
                    total_tokens = total_tokens + %s,
                    last_active = NOW()
                WHERE session_id = %s
                RETURNING total_tokens
            """, (token_count, self.session_id))

            total_tokens = cur.fetchone()[0]

            if total_tokens > SUMMARY_TRIGGER_TOKENS:
                self._compress_history(cur)

            conn.commit()
        conn.close()

    def _compress_history(self, cur) -> None:
        """InfiniPot-style compression: summarize old, keep recent."""
        cur.execute("""
            SELECT event_id, content, role
            FROM unified_conversation_events
            WHERE session_id = %s AND is_summarized = FALSE
            ORDER BY created_at ASC
            OFFSET %s
        """, (self.session_id, MAX_RECENT_MESSAGES))

        old_messages = cur.fetchall()

        if not old_messages:
            return

        summary_parts = [f"{msg[2]}: {msg[1][:100]}..." for msg in old_messages[:5]]
        summary_text = f"[Compressed {len(old_messages)} messages: " + "; ".join(summary_parts) + "]"

        cur.execute("""
            UPDATE unified_sessions
            SET conversation_summary = conversation_summary || %s || E'\n'
            WHERE session_id = %s
        """, (summary_text, self.session_id))

        event_ids = [msg[0] for msg in old_messages]
        cur.execute("""
            UPDATE unified_conversation_events
            SET is_summarized = TRUE WHERE event_id = ANY(%s)
        """, (event_ids,))

    def get_context(self) -> Dict[str, Any]:
        """Get full context for LLM prompt."""
        conn = get_connection()
        context = {}

        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT conversation_summary, entities_discussed,
                       current_topics, parent_session_id
                FROM unified_sessions WHERE session_id = %s
            """, (self.session_id,))
            session = cur.fetchone()

            context['summary'] = session['conversation_summary'] or ''
            context['entities'] = session['entities_discussed'] or {}
            context['topics'] = session['current_topics'] or []

            cur.execute("""
                SELECT role, content, interface_type, created_at
                FROM unified_conversation_events
                WHERE session_id = %s AND is_summarized = FALSE
                ORDER BY created_at DESC LIMIT %s
            """, (self.session_id, MAX_RECENT_MESSAGES))

            context['recent_messages'] = [dict(row) for row in reversed(cur.fetchall())]

            if session['parent_session_id']:
                cur.execute("""
                    SELECT conversation_summary, interface_type
                    FROM unified_sessions WHERE session_id = %s
                """, (session['parent_session_id'],))
                parent = cur.fetchone()
                if parent:
                    context['cross_interface'] = {
                        'from_interface': parent['interface_type'],
                        'context': parent['conversation_summary'][:500]
                    }

        conn.close()
        return context

    def build_prompt_context(self) -> str:
        """Build formatted context string for LLM prompts."""
        ctx = self.get_context()
        parts = []

        if ctx.get('cross_interface'):
            parts.append(f"[Continued from {ctx['cross_interface']['from_interface']}: {ctx['cross_interface']['context']}]")

        if ctx['summary']:
            parts.append(f"[Previous context: {ctx['summary'][-1000:]}]")

        if ctx['topics']:
            parts.append(f"[Current topics: {', '.join(ctx['topics'][-5:])}]")

        if ctx['recent_messages']:
            msg_text = "\n".join([f"{m['role']}: {m['content']}" for m in ctx['recent_messages']])
            parts.append(f"[Recent conversation:\n{msg_text}]")

        return "\n\n".join(parts)


# =============================================================================
# INTERFACE-SPECIFIC ADAPTERS
# =============================================================================

class TelegramSessionAdapter:
    @staticmethod
    def get_session(user_id: int, chat_id: int, username: str = None):
        return UnifiedSessionManager.get_or_create(
            user_id=f"tg_{user_id}",
            interface_type=InterfaceType.TELEGRAM,
            interface_id=str(chat_id),
            user_name=username
        )

class APISessionAdapter:
    @staticmethod
    def get_session(api_key: str, client_id: str = None):
        return UnifiedSessionManager.get_or_create(
            user_id=f"api_{client_id or api_key[:16]}",
            interface_type=InterfaceType.API,
            interface_id=api_key[:16]
        )

class WebSessionAdapter:
    @staticmethod
    def get_session(session_cookie: str, username: str = None):
        return UnifiedSessionManager.get_or_create(
            user_id=f"web_{username or session_cookie[:16]}",
            interface_type=InterfaceType.WEB,
            interface_id=session_cookie,
            user_name=username
        )

class CLISessionAdapter:
    @staticmethod
    def get_session(username: str = None):
        import os
        user = username or os.environ.get('USER', 'unknown')
        return UnifiedSessionManager.get_or_create(
            user_id=f"cli_{user}",
            interface_type=InterfaceType.CLI,
            interface_id=f"{user}@{os.uname().nodename}"
        )

class JrAgentSessionAdapter:
    @staticmethod
    def get_session(agent_id: str, task_id: str = None):
        return UnifiedSessionManager.get_or_create(
            user_id=f"jr_{agent_id}",
            interface_type=InterfaceType.JR_AGENT,
            interface_id=task_id
        )
```

---

## INTEGRATION EXAMPLES

### Telegram Chief

```python
from lib.unified_session import TelegramSessionAdapter

async def handle_message(update, context):
    session = TelegramSessionAdapter.get_session(
        user_id=update.effective_user.id,
        chat_id=update.effective_chat.id
    )
    session.add_message('user', update.message.text)
    prompt_context = session.build_prompt_context()
    # Query Council with context...
```

### LLM Gateway API

```python
from lib.unified_session import APISessionAdapter

@app.post("/v1/chat/completions")
async def chat(request):
    session = APISessionAdapter.get_session(api_key)
    context = session.build_prompt_context()
    # Enrich messages with context...
```

### SAG UI Web

```python
from lib.unified_session import WebSessionAdapter, UnifiedSessionManager, InterfaceType

@app.route('/api/chat')
def web_chat():
    session = WebSessionAdapter.get_session(session_cookie, username)

    # Continue from Telegram if requested
    if request.json.get('continue_from_telegram'):
        session = UnifiedSessionManager.continue_session(
            user_id=session.user_id,
            new_interface=InterfaceType.WEB
        )
```

---

## VALIDATION CHECKLIST

- [ ] unified_sessions table created
- [ ] unified_conversation_events table created
- [ ] session_links table created
- [ ] user_identity_map table created
- [ ] UnifiedSessionManager class working
- [ ] All interface adapters functional
- [ ] Cross-interface session continuation working
- [ ] Context compression triggering correctly

---

## SEVEN GENERATIONS CONSIDERATION

The Universal Session Layer embodies continuity across:
- **Interfaces** - Start anywhere, continue anywhere
- **Time** - Days, weeks, months of context preserved
- **Users** - Knowledge shared appropriately
- **Agents** - Jr agents learn from human sessions

"Memory is not just recall, it is the thread that connects
 all our conversations into wisdom."

For Seven Generations - every interaction builds on the last.

---

*Created: December 23, 2025*
*Scope: Federation-wide infrastructure*
*Interfaces: Telegram, API, Web, CLI, Jr Agents*

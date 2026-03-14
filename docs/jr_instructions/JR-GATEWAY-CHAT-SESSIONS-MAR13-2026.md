# JR INSTRUCTION: Gateway Chat Sessions — Conversational Memory for the Council

**Task**: Add chat session model to the gateway so the council has conversational memory. Users can have multi-turn conversations where the council remembers prior messages and context. Adapted from jsdorn/MyBrain ChatSession + ChatMessage pattern.
**Priority**: P2
**Date**: 2026-03-13
**TPM**: Claude Opus
**Story Points**: 3
**Council Vote**: #4df2e34784f1b36c (0.874, APPROVED — pilot)
**Depends On**: Gateway (services/llm_gateway/gateway.py), bluefin PostgreSQL

## Context

Our gateway is stateless — every request starts fresh. When Joe asks "what's the ring budget?" and then follows up with "break it down by provider" — the council has no idea what "it" refers to. Joe's MyBrain stores chat sessions with message history and feeds context back to the LLM. We adopt this pattern as a pilot.

## Step 1: Create Chat Tables

```sql
-- Chat sessions
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) DEFAULT 'New Chat',
    api_key_id VARCHAR(64),          -- which API key created this session
    source_node VARCHAR(64),          -- node the session originated from
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Chat messages within sessions
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(16) NOT NULL,        -- 'user', 'assistant', 'system', 'tool'
    content TEXT NOT NULL,
    tool_name VARCHAR(128),           -- if role='tool', which tool was called
    tool_result JSONB,                -- tool execution result
    tokens_used INTEGER DEFAULT 0,
    latency_ms INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session
    ON chat_messages(session_id, created_at);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_api_key
    ON chat_sessions(api_key_id, updated_at DESC);
```

## Step 2: Add Session Support to Gateway

Add to gateway.py `ChatRequest` model:

```python
class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    max_tokens: int = 500
    temperature: float = 0.7
    model: Optional[str] = None
    session_id: Optional[str] = None  # NEW: pass session_id for continuity
```

Modify `chat_completions` endpoint:

```python
@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest, req: Request,
                           api_key: APIKeyInfo = Depends(validate_api_key)):
    session_id = request.session_id

    # If session_id provided, load history and prepend
    if session_id:
        history = load_session_messages(session_id, limit=20)
        # Prepend history before current messages
        full_messages = history + [{"role": m.role, "content": m.content}
                                   for m in request.messages]
    else:
        full_messages = [{"role": m.role, "content": m.content}
                        for m in request.messages]

    # ... existing vLLM dispatch with full_messages ...

    # After response, save to session
    if session_id:
        save_message(session_id, "user", request.messages[-1].content)
        save_message(session_id, "assistant", result_content)
    elif should_create_session(request):
        # Auto-create session for multi-turn potential
        new_session_id = create_session(api_key.key_id, req.client.host)
        save_message(new_session_id, "user", request.messages[-1].content)
        save_message(new_session_id, "assistant", result_content)
        # Return session_id in response for client to use
        result["session_id"] = str(new_session_id)

    return result
```

## Step 3: Session Management Endpoints

```python
@app.get("/v1/sessions")
async def list_sessions(api_key: APIKeyInfo = Depends(validate_api_key)):
    """List chat sessions for this API key."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, source_node, created_at, updated_at
        FROM chat_sessions
        WHERE api_key_id = %s
        ORDER BY updated_at DESC
        LIMIT 50
    """, (api_key.key_id,))
    sessions = [{"id": str(r[0]), "name": r[1], "source_node": r[2],
                 "created": str(r[3]), "updated": str(r[4])}
                for r in cur.fetchall()]
    cur.close(); conn.close()
    return {"sessions": sessions}


@app.get("/v1/sessions/{session_id}/messages")
async def get_session_messages(session_id: str,
                               api_key: APIKeyInfo = Depends(validate_api_key)):
    """Get all messages in a session."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, role, content, tool_name, tokens_used, created_at
        FROM chat_messages
        WHERE session_id = %s
        ORDER BY created_at ASC
    """, (session_id,))
    messages = [{"id": str(r[0]), "role": r[1], "content": r[2],
                 "tool": r[3], "tokens": r[4], "time": str(r[5])}
                for r in cur.fetchall()]
    cur.close(); conn.close()
    return {"session_id": session_id, "messages": messages}


@app.delete("/v1/sessions/{session_id}")
async def delete_session(session_id: str,
                         api_key: APIKeyInfo = Depends(validate_api_key)):
    """Delete a chat session and its messages."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("DELETE FROM chat_sessions WHERE id = %s AND api_key_id = %s",
                (session_id, api_key.key_id))
    conn.commit()
    cur.close(); conn.close()
    return {"status": "deleted", "session_id": session_id}
```

## Step 4: Update BigMac Scripts

Update `/Users/Shared/ganuda/scripts/ask.sh` to support sessions:

```bash
#!/bin/bash
# ask.sh — Quick chat with Cherokee Gateway
# Usage: ask.sh "your question"
# Usage: ask.sh -s <session_id> "follow up question"

GATEWAY="http://100.116.27.89:8080"
API_KEY="ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"
SESSION_FILE="/Users/Shared/ganuda/.last_session"

SESSION=""
if [ "$1" = "-s" ]; then
    SESSION="$2"
    shift 2
elif [ -f "$SESSION_FILE" ]; then
    SESSION=$(cat "$SESSION_FILE")
fi

if [ -z "$1" ]; then
    echo "Usage: ask.sh \"your question\""
    echo "       ask.sh -s <session_id> \"follow up\""
    exit 1
fi

SESSION_JSON=""
if [ -n "$SESSION" ]; then
    SESSION_JSON=", \"session_id\": \"$SESSION\""
fi

RESPONSE=$(curl -s --max-time 60 "${GATEWAY}/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${API_KEY}" \
    -d "{\"messages\": [{\"role\": \"user\", \"content\": \"$1\"}], \"max_tokens\": 500${SESSION_JSON}}")

# Extract and save session_id for next call
echo "$RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    sid = data.get('session_id', '')
    if sid:
        with open('$SESSION_FILE', 'w') as f:
            f.write(sid)
    if 'choices' in data:
        print(data['choices'][0]['message']['content'])
    else:
        print(json.dumps(data, indent=2))
except:
    print(sys.stdin.read())
" 2>/dev/null
```

Now Joe can have multi-turn conversations:
```
$ ask.sh "What's the ring budget?"
→ The ring budget is currently at 16 active rings...
$ ask.sh "Break it down by provider"
→ (council remembers context) By provider: local_bigmac: 5, toolset_thermal: 3...
```

## Step 5: Context Window Management

Session history is limited to prevent context bombs:

```python
def load_session_messages(session_id: str, limit: int = 20) -> list:
    """Load recent messages from session, capped at limit.

    Older messages are summarized if session grows large.
    """
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Count total messages
    cur.execute("SELECT COUNT(*) FROM chat_messages WHERE session_id = %s", (session_id,))
    total = cur.fetchone()[0]

    if total <= limit:
        # Return all
        cur.execute("""
            SELECT role, content FROM chat_messages
            WHERE session_id = %s ORDER BY created_at ASC
        """, (session_id,))
    else:
        # Return system summary of old + recent messages
        cur.execute("""
            SELECT role, content FROM chat_messages
            WHERE session_id = %s
            ORDER BY created_at DESC LIMIT %s
        """, (session_id, limit))
        # Reverse to chronological order
        rows = list(reversed(cur.fetchall()))
        cur.close(); conn.close()
        return [{"role": "system", "content": f"[Session has {total} messages. Showing most recent {limit}.]"}] + \
               [{"role": r[0], "content": r[1]} for r in rows]

    rows = cur.fetchall()
    cur.close(); conn.close()
    return [{"role": r[0], "content": r[1]} for r in rows]
```

## DO NOT

- Load unlimited session history into LLM context — cap at 20 messages
- Allow cross-API-key session access — sessions are scoped to the key that created them
- Store session data in thermals — sessions are operational, not memory
- Skip the ON DELETE CASCADE on chat_messages — orphaned messages will pile up
- Make sessions required — stateless requests must still work (session_id is optional)

## Acceptance Criteria

- chat_sessions and chat_messages tables created on bluefin
- Gateway accepts optional session_id in chat requests
- Multi-turn conversations work: context carries across requests
- Session management endpoints: list, get messages, delete
- BigMac ask.sh auto-tracks session for follow-up questions
- Context window capped at 20 messages
- No regression on stateless requests (no session_id = current behavior)
- Pilot: test with Joe from BigMac for 48 hours, measure before expanding

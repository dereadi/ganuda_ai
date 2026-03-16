# JR INSTRUCTION: Desktop Assistant Full Stack — Frontend + Chat Sessions + Voice

**Task**: Wire Joe's MyBrain React/Tailwind frontend to the Cherokee Gateway with multi-turn chat sessions and optional voice interface. One product, one instruction.
**Priority**: P1
**Date**: 2026-03-14 (combined from Jr #1381 + #1377 + #1382)
**TPM**: Claude Opus
**Story Points**: 8 (combined)
**Council Vote**: #4df2e34784f1b36c (Joe's MyBrain adoption, APPROVED)
**Depends On**: Gateway tool-call loop (DONE, Jr #1380), BigMac necklace (DONE, Jr #1378)
**Supersedes**: Jr #1381 (Frontend), #1377 (Chat Sessions), #1382 (Voice Interface)

## Why Combined

These three tasks are one product:
- Chat sessions without a frontend = unused DB tables
- Frontend without chat sessions = stateless, can't follow up
- Voice without frontend = no visual context

Ship them together. The frontend IS the desktop assistant.

## Architecture

```
Joe's React/Tailwind (BigMac :3001)
  → GatewayConnector (Tailscale to redfin:8080)
    → /v1/chat/completions (with session_id for multi-turn)
    → /v1/council/vote (for explicit council queries)
    → SSE /v1/events (push notifications, council vote alerts)
  ← Response rendered in ChatWindow
  ← Tool results rendered in Dashboard
  ← Voice via browser SpeechRecognition + Piper TTS
```

## Phase 1: Chat Sessions (Database)

On bluefin, create the session tables:

```sql
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) DEFAULT 'New Chat',
    api_key_id VARCHAR(64),
    source_node VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(16) NOT NULL,
    content TEXT NOT NULL,
    tool_name VARCHAR(128),
    tool_result JSONB,
    tokens_used INTEGER DEFAULT 0,
    latency_ms INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_api_key ON chat_sessions(api_key_id, updated_at DESC);
```

## Phase 2: Gateway Session Endpoints

Add to `/ganuda/services/llm_gateway/gateway.py`:

1. **Modify `ChatRequest`** — add optional `session_id: Optional[str] = None`
2. **Session management endpoints**:
   - `POST /v1/sessions` — create new session, returns session_id
   - `GET /v1/sessions` — list sessions for API key
   - `GET /v1/sessions/{id}/messages` — get message history
   - `DELETE /v1/sessions/{id}` — delete session
3. **In `/v1/chat/completions`**: if session_id provided, load last N messages from chat_messages table and prepend to request messages. Save new user message + assistant response to chat_messages.
4. **Context window**: Last 20 messages max. Summarize older messages via a "session summary" thermal if conversation exceeds 20 turns.

## Phase 3: Frontend Wiring (BigMac)

On BigMac, create `/Users/Shared/ganuda/services/desktop-assistant/`:

1. **GatewayConnector** (`gateway_connector.py`): Replaces Joe's OllamaConnector
   - `chat(message, session_id)` → POST to gateway `/v1/chat/completions`
   - `council_vote(question)` → POST to gateway `/v1/council/vote`
   - `search_thermals(query)` → calls thermal search ToolSet
   - API key from `/Users/Shared/ganuda/config/secrets.env` (LLM_GATEWAY_API_KEY)
   - Endpoint: `http://100.116.27.89:8080` (redfin Tailscale)

2. **Wire Joe's React components**:
   - `ChatWindow` → GatewayConnector.chat() with session_id
   - `NoteEditor` → thermal write via gateway
   - `SemanticSearch` → thermal memory search
   - `Dashboard` → gateway /health + fire-guard summary

3. **SSE notifications** (optional, Phase 3b):
   - Gateway pushes council vote alerts, fire-guard warnings
   - Frontend shows notification toast

## Phase 4: Voice Interface (Optional)

Browser-native voice, no server-side dependencies:

1. **Input**: `window.SpeechRecognition` (Web Speech API) — works in Chrome/Edge
2. **Output**: Piper TTS via local binary on BigMac, or browser `speechSynthesis` fallback
3. **Trigger**: Hold-to-talk button in ChatWindow, or wake word (stretch goal)
4. **Architecture**: Voice → text → GatewayConnector.chat() → text response → TTS

Voice is opt-in. The desktop assistant works without it.

## DO NOT

- Run a separate backend on BigMac — the gateway IS the backend
- Store secrets in the React frontend — all auth goes through GatewayConnector server-side
- Build a custom auth system — use existing LLM_GATEWAY_API_KEY
- Break Joe's existing MyBrain components — adapt them, don't rewrite
- Ship voice before chat sessions work — Phase 4 depends on Phases 1-3

## Acceptance Criteria

- [ ] Chat sessions table exists on bluefin
- [ ] Gateway supports session_id in /v1/chat/completions
- [ ] Multi-turn conversation works: "what's the ring budget?" followed by "break it down" retains context
- [ ] Joe's ChatWindow sends messages through GatewayConnector to gateway
- [ ] Session history persists across page reloads
- [ ] Dashboard shows gateway health + node status
- [ ] Voice input captures speech and sends as text (Phase 4)
- [ ] Anti-sycophancy prompt active in all desktop assistant chat (inherits from gateway)

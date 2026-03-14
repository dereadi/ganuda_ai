# JR INSTRUCTION: Desktop Assistant — Wire Joe's Frontend to Federation Gateway

**Task**: Connect Joe's MyBrain React/Tailwind frontend to the Cherokee Gateway so it becomes the federation's desktop assistant. Joe's ChatWindow talks to our council. His NoteEditor writes to thermals. His SemanticSearch queries our ToolSets. Two-way: the federation can also push notifications and council votes to the frontend.
**Priority**: P1
**Date**: 2026-03-13
**TPM**: Claude Opus
**Story Points**: 5
**Council Vote**: #4df2e34784f1b36c (Joe's MyBrain adoption, APPROVED)
**Depends On**: Gateway tool-call loop (JR-GATEWAY-TOOL-CALL-LOOP), chat sessions (JR-GATEWAY-CHAT-SESSIONS), Joe's MyBrain repo (github.com/jsdorn/MyBrain)

## Context

Joe built a React/Tailwind frontend with ChatWindow, NoteEditor, NoteList, SemanticSearch, SettingsPanel, and Dashboard components. His backend currently hits local Ollama and Qdrant. We redirect it to our gateway — now his UI talks to Qwen 72B + 7-specialist council + ToolSets + thermal memory + 21 rings across 7 nodes.

The frontend runs on BigMac. The gateway runs on redfin. Tailscale connects them.

## Step 1: Create Gateway Connector for Frontend

Replace Joe's OllamaConnector usage with a GatewayConnector in the Brain Web API.

Create `/Users/Shared/ganuda/lib/gateway_connector.py` (or add to Joe's `brain_web_api/connectors/`):

```python
"""Gateway connector — routes Joe's frontend to Cherokee Gateway.

Replaces direct Ollama calls with gateway dispatch.
Adds session tracking for conversational memory.
"""

import httpx
import json
from typing import Optional, AsyncGenerator

GATEWAY_URL = "http://100.116.27.89:8080"
API_KEY = None  # Loaded from secrets.env at startup


def _load_api_key():
    global API_KEY
    if API_KEY:
        return API_KEY
    try:
        with open("/Users/Shared/ganuda/config/secrets.env") as f:
            for line in f:
                if line.startswith("GATEWAY_API_KEY="):
                    API_KEY = line.strip().split("=", 1)[1]
                    return API_KEY
    except FileNotFoundError:
        pass
    # Fallback
    API_KEY = "ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"
    return API_KEY


async def chat(message: str, session_id: Optional[str] = None,
               use_tools: bool = True, max_tokens: int = 500) -> dict:
    """Send chat message through Cherokee Gateway.

    Returns: {"content": str, "session_id": str, "tool_calls": list}
    """
    api_key = _load_api_key()

    payload = {
        "messages": [{"role": "user", "content": message}],
        "max_tokens": max_tokens,
    }
    if session_id:
        payload["session_id"] = session_id
    if use_tools:
        payload["tools"] = True

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{GATEWAY_URL}/v1/chat/completions",
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=120.0,
        )
        resp.raise_for_status()
        data = resp.json()

        content = data["choices"][0]["message"]["content"]
        return {
            "content": content,
            "session_id": data.get("session_id", session_id),
            "tool_calls": data.get("tool_calls_made", []),
            "model": data.get("model", "cherokee-council"),
        }


async def council_vote(question: str, max_tokens: int = 500) -> dict:
    """Submit a question to the full council vote."""
    api_key = _load_api_key()

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{GATEWAY_URL}/v1/council/vote",
            json={"question": question, "max_tokens": max_tokens},
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=300.0,
        )
        resp.raise_for_status()
        return resp.json()


async def search_thermals(query: str, limit: int = 10) -> dict:
    """Search thermals via gateway ToolSet."""
    return await chat(
        f"Search thermals for: {query}",
        use_tools=True,
        max_tokens=600,
    )


async def get_health() -> dict:
    """Check gateway health."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{GATEWAY_URL}/health", timeout=5.0)
        return resp.json()
```

## Step 2: Update Frontend API Calls

Joe's ChatWindow.tsx has `// TODO: Implement actual API call` stubs. Wire them:

```typescript
// src/api/gateway.ts — Federation Gateway client

const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL || 'http://100.116.27.89:8080'
const API_KEY = import.meta.env.VITE_GATEWAY_API_KEY || ''

interface ChatResponse {
  content: string
  session_id?: string
  tool_calls_made?: Array<{ name: string; success: boolean; latency_ms: number }>
}

export async function sendMessage(sessionId: string, content: string): Promise<ChatResponse> {
  const resp = await fetch(`${GATEWAY_URL}/v1/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${API_KEY}`,
    },
    body: JSON.stringify({
      messages: [{ role: 'user', content }],
      session_id: sessionId,
      tools: true,
      max_tokens: 500,
    }),
  })
  const data = await resp.json()
  return {
    content: data.choices[0].message.content,
    session_id: data.session_id,
    tool_calls_made: data.tool_calls_made,
  }
}

export async function getSessions() {
  const resp = await fetch(`${GATEWAY_URL}/v1/sessions`, {
    headers: { 'Authorization': `Bearer ${API_KEY}` },
  })
  return resp.json()
}

export async function getSessionMessages(sessionId: string) {
  const resp = await fetch(`${GATEWAY_URL}/v1/sessions/${sessionId}/messages`, {
    headers: { 'Authorization': `Bearer ${API_KEY}` },
  })
  return resp.json()
}

export async function createSession(): Promise<string> {
  const resp = await fetch(`${GATEWAY_URL}/v1/sessions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${API_KEY}`,
    },
    body: JSON.stringify({ name: 'New Chat' }),
  })
  const data = await resp.json()
  return data.id
}

export async function getHealth() {
  const resp = await fetch(`${GATEWAY_URL}/health`)
  return resp.json()
}
```

## Step 3: Add CORS for BigMac

Update gateway.py CORS to allow BigMac's frontend:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",        # Local dev
        "http://100.106.9.80:3000",     # BigMac frontend via Tailscale
        "http://100.106.9.80:5173",     # Vite dev server on BigMac
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Step 4: Two-Way Communication — Gateway Push to Frontend

For the federation to push TO the frontend (council votes, alerts, dawn mist):

```typescript
// src/api/notifications.ts — SSE stream from gateway

export function subscribeToNotifications(onMessage: (event: any) => void) {
  const eventSource = new EventSource(
    `${GATEWAY_URL}/v1/notifications/stream?key=${API_KEY}`
  )

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data)
    onMessage(data)
  }

  return eventSource  // caller can close when unmounting
}
```

Gateway side — add SSE endpoint:

```python
from sse_starlette.sse import EventSourceResponse

@app.get("/v1/notifications/stream")
async def notification_stream(key: str = Query(...)):
    """Server-Sent Events stream for real-time notifications."""
    # Validate API key
    # ...

    async def event_generator():
        while True:
            # Check for new notifications (council votes, alerts, etc.)
            notifications = get_pending_notifications(key)
            for n in notifications:
                yield {"data": json.dumps(n)}
            await asyncio.sleep(5)

    return EventSourceResponse(event_generator())
```

## Step 5: Dashboard — Federation Health on BigMac

Wire Joe's Dashboard.tsx to show federation status:

```typescript
// Dashboard shows: gateway health, node status, ring count,
// recent council votes, thermal stats, active tasks

export async function getDashboardData() {
  const [health, thermalStats, taskStats] = await Promise.all([
    getHealth(),
    sendMessage('', 'thermal stats'),  // triggers thermal_stats tool
    sendMessage('', 'task stats'),      // triggers kanban_stats tool
  ])

  return { health, thermalStats, taskStats }
}
```

## Step 6: Environment Config on BigMac

Create `/Users/Shared/ganuda/web_frontend/.env`:

```
VITE_GATEWAY_URL=http://100.116.27.89:8080
VITE_GATEWAY_API_KEY=ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5
```

## DO NOT

- Expose the API key in production builds — use env vars, not hardcoded strings
- Skip CORS config — browser will block cross-origin requests without it
- Point the frontend at localhost on BigMac — it must hit redfin's Tailscale IP
- Build a new frontend from scratch — Joe's is 80% done, wire it
- Break Joe's standalone Ollama mode — keep it as a fallback config option

## Acceptance Criteria

- Joe's ChatWindow sends messages through Cherokee Gateway
- Tool calls visible in UI (shows which tools were invoked)
- Session history persists across page reloads
- Dashboard shows federation health, thermal stats, task stats
- Two-way: gateway can push notifications to frontend via SSE
- CORS configured for BigMac Tailscale IP
- Ollama fallback still works when gateway is unreachable
- Joe can ask "what tasks are overdue?" in his browser and get real data back

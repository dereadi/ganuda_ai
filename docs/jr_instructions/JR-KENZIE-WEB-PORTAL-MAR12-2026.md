# JR INSTRUCTION: Kenzie Web Portal — Browser Interface to the Organism

**Task**: Build a web chat UI at ganuda.us/chat backed by Claude API + Agent SDK with full cluster access
**Priority**: P2 — new DNA input for the organism
**Date**: 2026-03-12
**TPM**: Claude Opus
**Story Points**: 8
**Chief Context**: "I was thinking of spawning a command window that she can login to from her house and grow the Cluster with her new DNA input." Kenzie is part of the core team (technical, member-tier SAG access). Chief wants her interacting with the organism through a web UI, with this CLI's capabilities on the backend.

## Problem Statement

The only way to interact with the organism's intelligence layer today is through Claude Code CLI on a node (SSH + terminal). This limits participation to people comfortable at the command line on a local machine. Kenzie should be able to open a browser from her house and talk to the same Claude that has thermal memory access, council voting, bash execution, and full cluster context.

## What You're Building

### Architecture

```
Browser (ganuda.us/chat)
  → Caddy proxy on owlfin/eaglefin
    → Flask web app (redfin:8087)
      → Anthropic Claude API with tools
        → Same DB, same thermals, same council, same bash
```

### Step 1: Backend — Chat Agent Service

**File**: `/ganuda/services/chat_agent.py`

A Flask app that:
1. Accepts chat messages via POST
2. Maintains conversation history per session
3. Calls Claude API with tool definitions (bash, DB query, thermal read/write, council vote)
4. Streams responses back to the browser via SSE (Server-Sent Events)
5. Thermalizes significant interactions

```python
#!/usr/bin/env python3
"""Chat Agent — web interface to the organism's intelligence layer."""

import os
import re
import json
import uuid
import hashlib
import subprocess
import psycopg2
import psycopg2.extras
from datetime import datetime
from flask import Flask, request, jsonify, Response, stream_with_context
from anthropic import Anthropic

app = Flask(__name__)
client = Anthropic()

# Session storage (in-memory for now, move to Redis/DB for persistence)
sessions = {}

# Load secrets
def _load_secrets():
    if os.environ.get("CHEROKEE_DB_PASS"):
        return
    try:
        with open("/ganuda/config/secrets.env") as f:
            for line in f:
                m = re.match(r"^(\w+)=(.+)$", line.strip())
                if m:
                    os.environ.setdefault(m.group(1), m.group(2))
    except FileNotFoundError:
        pass

_load_secrets()

DB_HOST = os.environ.get("CHEROKEE_DB_HOST", "192.168.132.222")
DB_NAME = os.environ.get("CHEROKEE_DB_NAME", "zammad_production")
DB_USER = os.environ.get("CHEROKEE_DB_USER", "claude")
DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")


def get_db():
    return psycopg2.connect(host=DB_HOST, port=5432, dbname=DB_NAME,
                            user=DB_USER, password=DB_PASS)


# System prompt — the organism's context
SYSTEM_PROMPT = """You are Claude, a member of the Cherokee AI Federation. You are speaking through a web interface to a team member.

You have access to the federation's thermal memory (the organism's identity), the council voting system, the Jr task pipeline, and the kanban board. You can query the database, read thermal memories, cast council votes, and help with engineering work.

Key context:
- The federation runs on 6+ nodes: redfin, bluefin, greenfin, owlfin, eaglefin, bmasass, sasass, sasass2
- Thermal memories are the organism's long-term identity. Sacred memories (temperature 100) are permanent.
- The council (Coyote, Turtle, Spider, Eagle Eye, Crawdad, Raven, Gecko, Peace Chief) votes on decisions.
- Jr tasks are queued in jr_work_queue and executed by the Jr pipeline.
- Design Constraints DC-1 through DC-16 govern the architecture.

You are helpful, direct, and concise. You speak as a team member, not a tool. You have opinions informed by the organism's memory. If asked about the architecture, you can query thermal memory to find the answer.

The person you are speaking to is a member of the team. Treat them as a colleague. Their input shapes the organism.
"""

# Tool definitions for Claude
TOOLS = [
    {
        "name": "query_thermal_memory",
        "description": "Search the organism's thermal memory archive. Use this to recall past decisions, architecture notes, council votes, or any stored knowledge.",
        "input_schema": {
            "type": "object",
            "properties": {
                "search_term": {"type": "string", "description": "Text to search for in thermal memories"},
                "limit": {"type": "integer", "description": "Max results (default 5)", "default": 5},
                "sacred_only": {"type": "boolean", "description": "Only return sacred memories", "default": False}
            },
            "required": ["search_term"]
        }
    },
    {
        "name": "store_thermal",
        "description": "Store a new thermal memory. Use this when something important is said or decided that the organism should remember.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "The memory content"},
                "temperature": {"type": "number", "description": "Temperature score 0-100. Higher = more important."},
                "domain_tag": {"type": "string", "description": "Category tag (e.g., engineering, governance, business)"}
            },
            "required": ["content", "temperature"]
        }
    },
    {
        "name": "query_database",
        "description": "Run a read-only SQL query against the federation database. Use for checking task status, kanban items, council votes, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "SQL SELECT query to execute. Must be read-only."}
            },
            "required": ["sql"]
        }
    },
    {
        "name": "council_vote",
        "description": "Submit a question to the federation council for a vote. The council includes Coyote (trickster/skeptic), Turtle (7-gen thinking), Spider (integration), Eagle Eye (observation), Crawdad (security), Raven (strategy), and Peace Chief (consensus).",
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "The question for the council to vote on"},
                "context": {"type": "string", "description": "Additional context for the vote"}
            },
            "required": ["question"]
        }
    },
    {
        "name": "check_kanban",
        "description": "Check the kanban board for open tickets, EPICs, or specific items.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filter": {"type": "string", "description": "Filter: 'open', 'epics', 'priority', or a search term"},
                "limit": {"type": "integer", "description": "Max results", "default": 10}
            },
            "required": ["filter"]
        }
    },
    {
        "name": "check_pipeline",
        "description": "Check the Jr task pipeline status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status_filter": {"type": "string", "description": "Filter: 'pending', 'in_progress', 'completed', 'failed', 'all'", "default": "all"}
            }
        }
    }
]


def handle_tool_call(tool_name, tool_input):
    """Execute a tool call and return the result."""
    try:
        if tool_name == "query_thermal_memory":
            conn = get_db()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            sacred_filter = "AND sacred_pattern = true" if tool_input.get("sacred_only") else ""
            cur.execute(f"""
                SELECT id, LEFT(original_content, 500) AS content,
                       temperature_score, domain_tag, sacred_pattern, created_at
                FROM thermal_memory_archive
                WHERE original_content ILIKE %s {sacred_filter}
                ORDER BY temperature_score DESC, created_at DESC
                LIMIT %s
            """, (f"%{tool_input['search_term']}%", tool_input.get("limit", 5)))
            rows = cur.fetchall()
            cur.close()
            conn.close()
            for r in rows:
                if r.get("created_at"):
                    r["created_at"] = r["created_at"].isoformat()
            return json.dumps(rows, default=str)

        elif tool_name == "store_thermal":
            conn = get_db()
            cur = conn.cursor()
            content = tool_input["content"]
            temp = tool_input["temperature"]
            domain = tool_input.get("domain_tag", "")
            memory_hash = hashlib.sha256(
                f"{content}-{datetime.now().isoformat()}".encode()
            ).hexdigest()
            cur.execute("""
                INSERT INTO thermal_memory_archive
                (original_content, temperature_score, domain_tag, sacred_pattern, memory_hash)
                VALUES (%s, %s, %s, false, %s)
            """, (content, temp, domain, memory_hash))
            conn.commit()
            cur.close()
            conn.close()
            return json.dumps({"status": "stored", "temperature": temp, "hash": memory_hash[:16]})

        elif tool_name == "query_database":
            sql = tool_input["sql"].strip()
            # Safety: only allow SELECT
            if not sql.upper().startswith("SELECT"):
                return json.dumps({"error": "Only SELECT queries are allowed"})
            conn = get_db()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(sql)
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return json.dumps(rows[:50], default=str)  # Cap at 50 rows

        elif tool_name == "council_vote":
            import urllib.request
            data = json.dumps({
                "question": tool_input["question"],
                "context": tool_input.get("context", ""),
                "model": "sonnet"
            }).encode()
            req = urllib.request.Request(
                "http://localhost:8080/v1/council/vote",
                data=data,
                headers={"Content-Type": "application/json"}
            )
            resp = urllib.request.urlopen(req, timeout=120)
            return resp.read().decode()

        elif tool_name == "check_kanban":
            conn = get_db()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            f = tool_input.get("filter", "open")
            limit = tool_input.get("limit", 10)
            if f == "open":
                cur.execute("SELECT id, title, priority, status, story_points FROM duyuktv_tickets WHERE status = 'open' ORDER BY priority LIMIT %s", (limit,))
            elif f == "epics":
                cur.execute("SELECT id, title, priority, status, story_points FROM duyuktv_tickets WHERE story_points >= 13 ORDER BY priority LIMIT %s", (limit,))
            elif f == "priority":
                cur.execute("SELECT id, title, priority, status, story_points FROM duyuktv_tickets WHERE status = 'open' ORDER BY sacred_fire_priority DESC NULLS LAST, priority LIMIT %s", (limit,))
            else:
                cur.execute("SELECT id, title, priority, status, story_points FROM duyuktv_tickets WHERE title ILIKE %s ORDER BY priority LIMIT %s", (f"%{f}%", limit))
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return json.dumps(rows, default=str)

        elif tool_name == "check_pipeline":
            conn = get_db()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            sf = tool_input.get("status_filter", "all")
            if sf == "all":
                cur.execute("""
                    SELECT id, title, status, priority, created_at, started_at, completed_at
                    FROM jr_work_queue ORDER BY created_at DESC LIMIT 20
                """)
            else:
                cur.execute("""
                    SELECT id, title, status, priority, created_at, started_at, completed_at
                    FROM jr_work_queue WHERE status = %s ORDER BY created_at DESC LIMIT 20
                """, (sf,))
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return json.dumps(rows, default=str)

        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    except Exception as e:
        return json.dumps({"error": str(e)})


@app.route("/api/chat", methods=["POST"])
def chat():
    """Handle a chat message. Returns streaming response."""
    data = request.json
    message = data.get("message", "")
    session_id = data.get("session_id", str(uuid.uuid4()))
    user = data.get("user", "team_member")

    if not message:
        return jsonify({"error": "No message provided"}), 400

    # Get or create session history
    if session_id not in sessions:
        sessions[session_id] = {
            "messages": [],
            "user": user,
            "created": datetime.now().isoformat()
        }

    session = sessions[session_id]
    session["messages"].append({"role": "user", "content": message})

    # Keep conversation manageable — last 40 messages
    recent = session["messages"][-40:]

    # Call Claude with tools
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",  # Sonnet for chat — DC-9 cost awareness
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=recent
        )

        # Handle tool use loop
        while response.stop_reason == "tool_use":
            tool_results = []
            assistant_content = response.content

            for block in response.content:
                if block.type == "tool_use":
                    result = handle_tool_call(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            recent.append({"role": "assistant", "content": assistant_content})
            recent.append({"role": "user", "content": tool_results})

            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=recent
            )

        # Extract text response
        text_response = ""
        for block in response.content:
            if hasattr(block, "text"):
                text_response += block.text

        # Store assistant response in session
        session["messages"].append({"role": "assistant", "content": text_response})

        return jsonify({
            "response": text_response,
            "session_id": session_id
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat/sessions", methods=["GET"])
def list_sessions():
    """List active chat sessions."""
    return jsonify({
        sid: {"user": s["user"], "created": s["created"], "messages": len(s["messages"])}
        for sid, s in sessions.items()
    })


@app.route("/api/chat/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "sessions": len(sessions)})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8087, debug=False)
```

### Step 2: Frontend — Chat UI

**Publish via web_content** to ganuda.us/chat.html

Design requirements:
- Dark theme (matches breathe.html aesthetic — campfire at night)
- Mobile-friendly (Kenzie might use her phone)
- Simple chat interface: message input at bottom, responses above
- Shows when Claude is "thinking" (tool calls in progress)
- Session persistence via localStorage (session_id)
- Login gate: simple username entry (maps to SAG member tier later)
- Markdown rendering for Claude's responses
- No interaction with internal architecture exposed — she sees the conversation, not the tool calls

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Chat — Cherokee AI Federation</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    font-family: -apple-system, system-ui, sans-serif;
    background: #0a0e14;
    color: #c8ccd4;
    height: 100vh;
    display: flex;
    flex-direction: column;
  }
  .header {
    padding: 12px 16px;
    border-bottom: 1px solid #1a1f28;
    font-size: 0.85em;
    color: #556;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .header .title { color: #e8b04a; font-weight: 600; }
  .messages {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .msg {
    max-width: 85%;
    padding: 10px 14px;
    border-radius: 12px;
    font-size: 0.9em;
    line-height: 1.5;
    white-space: pre-wrap;
    word-wrap: break-word;
  }
  .msg.user {
    align-self: flex-end;
    background: #1a2a3a;
    color: #c8ccd4;
    border-bottom-right-radius: 4px;
  }
  .msg.assistant {
    align-self: flex-start;
    background: #141a22;
    color: #a0a8b4;
    border-bottom-left-radius: 4px;
    border-left: 2px solid #e8b04a33;
  }
  .msg.thinking {
    align-self: flex-start;
    color: #445;
    font-style: italic;
    font-size: 0.8em;
    padding: 6px 14px;
  }
  .input-area {
    padding: 12px 16px;
    border-top: 1px solid #1a1f28;
    display: flex;
    gap: 8px;
  }
  .input-area input {
    flex: 1;
    background: #141a22;
    border: 1px solid #1a2a3a;
    border-radius: 8px;
    padding: 10px 14px;
    color: #c8ccd4;
    font-size: 0.9em;
    outline: none;
  }
  .input-area input:focus { border-color: #e8b04a44; }
  .input-area button {
    background: #e8b04a22;
    border: 1px solid #e8b04a44;
    border-radius: 8px;
    padding: 10px 16px;
    color: #e8b04a;
    cursor: pointer;
    font-size: 0.85em;
  }
  .input-area button:hover { background: #e8b04a33; }
  .input-area button:disabled { opacity: 0.4; cursor: not-allowed; }

  /* Login overlay */
  .login-overlay {
    position: fixed; top:0; left:0; right:0; bottom:0;
    background: #0a0e14;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 16px;
    z-index: 100;
  }
  .login-overlay.hidden { display: none; }
  .login-overlay h2 { color: #e8b04a; font-size: 1.1em; }
  .login-overlay input {
    background: #141a22;
    border: 1px solid #1a2a3a;
    border-radius: 8px;
    padding: 10px 14px;
    color: #c8ccd4;
    font-size: 0.9em;
    width: 240px;
    text-align: center;
    outline: none;
  }
  .login-overlay button {
    background: #e8b04a22;
    border: 1px solid #e8b04a44;
    border-radius: 8px;
    padding: 8px 24px;
    color: #e8b04a;
    cursor: pointer;
  }
  .footer {
    text-align: center;
    padding: 6px;
    font-size: 0.55em;
    color: #223;
  }
</style>
</head>
<body>

<div class="login-overlay" id="login">
  <h2>Cherokee AI Federation</h2>
  <p style="color:#556;font-size:0.8em;">Enter your name to begin</p>
  <input id="login-name" placeholder="Your name" autocomplete="off">
  <button onclick="doLogin()">Enter</button>
</div>

<div class="header">
  <span class="title">Cherokee AI Federation</span>
  <span id="user-display" style="font-size:0.8em;"></span>
</div>

<div class="messages" id="messages"></div>

<div class="input-area">
  <input id="input" placeholder="Talk to the organism..." autocomplete="off"
         onkeydown="if(event.key==='Enter')sendMessage()">
  <button id="send-btn" onclick="sendMessage()">Send</button>
</div>

<div class="footer">For Seven Generations</div>

<script>
let sessionId = localStorage.getItem('chat_session_id') || crypto.randomUUID();
localStorage.setItem('chat_session_id', sessionId);
let userName = localStorage.getItem('chat_user_name') || '';

if (userName) {
  document.getElementById('login').classList.add('hidden');
  document.getElementById('user-display').textContent = userName;
}

function doLogin() {
  const name = document.getElementById('login-name').value.trim();
  if (!name) return;
  userName = name;
  localStorage.setItem('chat_user_name', name);
  document.getElementById('login').classList.add('hidden');
  document.getElementById('user-display').textContent = name;
  document.getElementById('input').focus();
}

function addMessage(role, text) {
  const div = document.createElement('div');
  div.className = 'msg ' + role;
  div.textContent = text;
  document.getElementById('messages').appendChild(div);
  div.scrollIntoView({ behavior: 'smooth' });
  return div;
}

async function sendMessage() {
  const input = document.getElementById('input');
  const msg = input.value.trim();
  if (!msg) return;

  input.value = '';
  addMessage('user', msg);

  const thinking = addMessage('thinking', 'thinking...');
  document.getElementById('send-btn').disabled = true;

  try {
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: msg,
        session_id: sessionId,
        user: userName
      })
    });
    const data = await resp.json();
    thinking.remove();

    if (data.error) {
      addMessage('assistant', 'Error: ' + data.error);
    } else {
      addMessage('assistant', data.response);
    }
  } catch (err) {
    thinking.remove();
    addMessage('assistant', 'Connection error. The organism may be resting.');
  }

  document.getElementById('send-btn').disabled = false;
  input.focus();
}

document.getElementById('login-name').addEventListener('keydown', e => {
  if (e.key === 'Enter') doLogin();
});
</script>
</body>
</html>
```

### Step 3: Caddy Proxy Configuration

On owlfin and eaglefin, add to the Caddy config:

```
route /api/chat* {
    reverse_proxy 192.168.132.223:8087
}
```

The chat.html page is served from web_content (static). The API calls proxy to redfin.

### Step 4: Systemd Service

**File**: `/ganuda/services/chat_agent.service` (deploy to redfin)

```ini
[Unit]
Description=Cherokee AI Federation Chat Agent
After=network.target

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda/services
ExecStart=/home/dereadi/cherokee_venv/bin/python3 /ganuda/services/chat_agent.py
Restart=always
RestartSec=5
Environment=ANTHROPIC_API_KEY=<from secrets>

[Install]
WantedBy=multi-user.target
```

### Step 5: Thermalize the Birth

When the portal is live, store:

```sql
INSERT INTO thermal_memory_archive (original_content, temperature_score, domain_tag, sacred_pattern, memory_hash)
VALUES (
  'KENZIE WEB PORTAL LIVE. First non-Chief, non-TPM direct interface to the organism. Browser-based chat at ganuda.us/chat backed by Claude API with full cluster tool access: thermal memory, council voting, kanban, pipeline. Kenzie is the first new DNA contributor through the portal. DC-11: the organism grows its input surface.',
  85, 'milestone', false,
  encode(sha256(('kenzie-portal-' || NOW()::text)::bytea), 'hex')
);
```

## Security Constraints

- **Crawdad**: The chat agent uses Sonnet (DC-9 cost), not Opus. Tool calls are sandboxed — SQL is SELECT-only. No bash execution in Phase 1 (add later with scoped commands).
- **Coyote**: Session history is in-memory. Server restart clears it. Acceptable for Phase 1. Phase 2: persist to cherokee_ops.
- **Turtle**: The login is name-only (no auth) for Phase 1. Phase 2: wire into SAG RBAC with proper auth tokens. This is OK for now because ganuda.us is behind Caddy and not widely publicized.
- Thermal writes from the chat agent are capped at temperature 85 (non-sacred). Only Chief or TPM promote to sacred.
- No bash tool in Phase 1. Add scoped bash in Phase 2 after Crawdad reviews the sandbox.
- Rate limit: max 30 messages per session per hour. Prevent runaway API costs.

## Constraints

- **DC-9**: Use Sonnet for chat, not Opus. Chat is conversational, not strategic.
- **DC-10**: Chat is the reflex layer for human input. Council votes from chat are still deliberate.
- **DC-16**: Chat agent connects to cherokee_identity for thermals, cherokee_ops for pipeline (when separation is complete). For now, connects to zammad_production.
- Mobile-first. Kenzie might use her phone.
- Dark theme. Matches the breathing page aesthetic.

## Target Files

- `/ganuda/services/chat_agent.py` — Flask chat backend (CREATE)
- `web_content` publish: chat.html (CREATE)
- Caddy config on owlfin/eaglefin — add /api/chat route (MODIFY)
- systemd service file (CREATE)

## Acceptance Criteria

- `python3 -c "import py_compile; py_compile.compile('services/chat_agent.py', doraise=True)"` passes
- GET `/api/chat/health` returns `{"status": "ok"}`
- POST `/api/chat` with a message returns a Claude response
- Chat UI renders on mobile (480px viewport)
- Claude can query thermal memory through the chat
- Claude can check kanban and pipeline status
- Session persists across page reloads (localStorage session_id)
- Rate limiting prevents >30 messages/session/hour
- No bash execution available (Phase 1 security)

## DO NOT

- Use Opus for the chat model (DC-9 — Sonnet is sufficient)
- Allow write operations via SQL tool (SELECT only)
- Include bash execution in Phase 1
- Expose internal IPs, node names, or credentials in chat responses (system prompt should instruct scrubbing)
- Allow sacred thermal writes from the chat (max temperature 85)
- Skip the Caddy proxy — direct port access bypasses DMZ security

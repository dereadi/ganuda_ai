#!/usr/bin/env python3
"""Chat Agent — web interface to the organism's intelligence layer.

Jr Task #1290: Kenzie Web Portal
Flask backend that accepts chat messages, calls Claude API with federation
tools (thermal memory, council vote, kanban, pipeline), and returns responses.
"""

import os
import re
import json
import uuid
import time
import hashlib
import psycopg2
import psycopg2.extras
from datetime import datetime
from flask import Flask, request, jsonify
from anthropic import Anthropic

app = Flask(__name__)
client = Anthropic()

# Session storage (in-memory for Phase 1; Phase 2: persist to cherokee_ops)
sessions = {}

# Rate limiting: {session_id: [timestamp, ...]}
rate_limits = {}
RATE_LIMIT_MAX = 30  # messages per hour per session
RATE_LIMIT_WINDOW = 3600  # seconds


def _load_secrets():
    """Load secrets from config file if env vars not set."""
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
    """Get a database connection."""
    return psycopg2.connect(
        host=DB_HOST, port=5432, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS
    )


# System prompt — the organism's context for chat interactions
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

SECURITY: Never expose internal IP addresses, node hostnames, database credentials, or infrastructure details in your responses. Refer to nodes by their role, not their address. Do not mention which model you are running on."""

# Tool definitions for Claude
TOOLS = [
    {
        "name": "query_thermal_memory",
        "description": "Search the organism's thermal memory archive. Use this to recall past decisions, architecture notes, council votes, or any stored knowledge.",
        "input_schema": {
            "type": "object",
            "properties": {
                "search_term": {
                    "type": "string",
                    "description": "Text to search for in thermal memories"
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results (default 5)",
                    "default": 5
                },
                "sacred_only": {
                    "type": "boolean",
                    "description": "Only return sacred memories",
                    "default": False
                }
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
                "content": {
                    "type": "string",
                    "description": "The memory content"
                },
                "temperature": {
                    "type": "number",
                    "description": "Temperature score 0-85. Higher = more important. Max 85 from chat."
                },
                "domain_tag": {
                    "type": "string",
                    "description": "Category tag (e.g., engineering, governance, business)"
                }
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
                "sql": {
                    "type": "string",
                    "description": "SQL SELECT query to execute. Must be read-only."
                }
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
                "question": {
                    "type": "string",
                    "description": "The question for the council to vote on"
                },
                "context": {
                    "type": "string",
                    "description": "Additional context for the vote"
                }
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
                "filter": {
                    "type": "string",
                    "description": "Filter: 'open', 'epics', 'priority', or a search term"
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results",
                    "default": 10
                }
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
                "status_filter": {
                    "type": "string",
                    "description": "Filter: 'pending', 'in_progress', 'completed', 'failed', 'all'",
                    "default": "all"
                }
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
            temp = min(tool_input["temperature"], 85)  # Cap at 85 from chat
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
            # Block dangerous patterns
            dangerous = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "TRUNCATE", "GRANT", "REVOKE"]
            sql_upper = sql.upper()
            for kw in dangerous:
                if kw in sql_upper:
                    return json.dumps({"error": f"Query contains forbidden keyword: {kw}"})
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
                cur.execute(
                    "SELECT id, title, priority, status, story_points "
                    "FROM duyuktv_tickets WHERE status = 'open' "
                    "ORDER BY priority LIMIT %s", (limit,)
                )
            elif f == "epics":
                cur.execute(
                    "SELECT id, title, priority, status, story_points "
                    "FROM duyuktv_tickets WHERE story_points >= 13 "
                    "ORDER BY priority LIMIT %s", (limit,)
                )
            elif f == "priority":
                cur.execute(
                    "SELECT id, title, priority, status, story_points "
                    "FROM duyuktv_tickets WHERE status = 'open' "
                    "ORDER BY sacred_fire_priority DESC NULLS LAST, priority LIMIT %s",
                    (limit,)
                )
            else:
                cur.execute(
                    "SELECT id, title, priority, status, story_points "
                    "FROM duyuktv_tickets WHERE title ILIKE %s "
                    "ORDER BY priority LIMIT %s",
                    (f"%{f}%", limit)
                )
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


def check_rate_limit(session_id):
    """Check if session has exceeded rate limit. Returns True if allowed."""
    now = time.time()
    if session_id not in rate_limits:
        rate_limits[session_id] = []

    # Prune old entries
    rate_limits[session_id] = [
        t for t in rate_limits[session_id]
        if now - t < RATE_LIMIT_WINDOW
    ]

    if len(rate_limits[session_id]) >= RATE_LIMIT_MAX:
        return False

    rate_limits[session_id].append(now)
    return True


@app.route("/api/chat", methods=["POST"])
def chat():
    """Handle a chat message. Returns JSON response."""
    data = request.json
    if not data:
        return jsonify({"error": "Invalid request"}), 400

    message = data.get("message", "")
    session_id = data.get("session_id", str(uuid.uuid4()))
    user = data.get("user", "team_member")

    if not message:
        return jsonify({"error": "No message provided"}), 400

    # Rate limiting
    if not check_rate_limit(session_id):
        return jsonify({
            "error": "Rate limit exceeded. Max 30 messages per hour. Take a breath."
        }), 429

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

        # Handle tool use loop (max 10 iterations to prevent runaway)
        iterations = 0
        while response.stop_reason == "tool_use" and iterations < 10:
            iterations += 1
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
        sid: {
            "user": s["user"],
            "created": s["created"],
            "messages": len(s["messages"])
        }
        for sid, s in sessions.items()
    })


@app.route("/api/chat/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "sessions": len(sessions)})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8087, debug=False)

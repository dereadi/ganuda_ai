```python
#!/usr/bin/env python3
"""Browser Ring API — Tiny backend for bidirectional browser ring.

Runs on redfin. Caddy proxies /api/ring/* to this service.
Three actions only (v1): approve_draft, reject_draft, flag_attention.
"""

import hashlib
import json
import os
import re
import secrets
from datetime import datetime, timedelta
from functools import wraps

import psycopg2
import psycopg2.extras
from flask import Flask, request, jsonify

app = Flask(__name__)

DB_HOST = os.environ.get("CHEROKEE_DB_HOST", "192.168.132.222")
DB_NAME = os.environ.get("CHEROKEE_DB_NAME", "zammad_production")
DB_USER = os.environ.get("CHEROKEE_DB_USER", "claude")
DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")

# v1 action whitelist (Coyote condition)
ALLOWED_ACTIONS = {"approve_draft", "reject_draft", "flag_attention"}
# Rate limit: max 60 actions per hour (Spider condition)
RATE_LIMIT = 60


def _load_secrets():
    global DB_PASS
    if not DB_PASS:
        try:
            with open("/ganuda/config/secrets.env") as f:
                for line in f:
                    m = re.match(r"^(\w+)=(.+)$", line.strip())
                    if m:
                        os.environ[m.group(1)] = m.group(2)
            DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")
        except FileNotFoundError:
            pass


def get_db():
    _load_secrets()
    return psycopg2.connect(host=DB_HOST, port=5432, dbname=DB_NAME,
                            user=DB_USER, password=DB_PASS)


def require_auth(f):
    """Verify bearer token. War Chief condition: auth gate before any inbound."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            cookie_token = request.cookies.get("ring_token", "")
            if not cookie_token:
                return jsonify({"error": "unauthorized"}), 401
            token = cookie_token
        else:
            token = auth.split(" ", 1)[1]

        token_hash = hashlib.sha256(token.encode()).hexdigest()
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""SELECT user_id, ring_tier FROM browser_ring_tokens
            WHERE token_hash = %s AND active = true
            AND (expires_at IS NULL OR expires_at > NOW())""", (token_hash,))
        row = cur.fetchone()
        if not row:
            cur.close()
            conn.close()
            return jsonify({"error": "invalid_token"}), 401

        # Update last_used
        cur.execute("UPDATE browser_ring_tokens SET last_used = NOW() WHERE token_hash = %s", (token_hash,))
        conn.commit()
        cur.close()
        conn.close()

        request.ring_user = row["user_id"]
        request.ring_tier = row["ring_tier"]
        return f(*args, **kwargs)
    return decorated


def check_rate_limit(user_id):
    """Spider condition: max 60 actions per hour."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""SELECT COUNT(*) FROM browser_ring_actions
        WHERE user_id = %s AND created_at > NOW() - INTERVAL '1 hour'""", (user_id,))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count < RATE_LIMIT


@app.route("/api/ring/action", methods=["POST"])
@require_auth
def ring_action():
    """Execute a browser ring action.

    POST JSON: {"action": "approve_draft", "target_type": "linkedin_draft", "target_id": 5}
    """
    # CSRF check (Coyote condition)
    if request.content_type != "application/json":
        return jsonify({"error": "content_type_must_be_json"}), 400

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "invalid_json"}), 400

    action = data.get("action", "")
    target_type = data.get("target_type", "")
    target_id = data.get("target_id")

    # Whitelist validation (Coyote condition — no freeform input)
    if action not in ALLOWED_ACTIONS:
        return jsonify({"error": f"action_not_allowed: {action}",
                        "allowed": list(ALLOWED_ACTIONS)}), 400

    if not isinstance(target_id, int):
        return jsonify({"error": "target_id must be integer"}), 400

    # Rate limit
    if not check_rate_limit(request.ring_user):
        return jsonify({"error": "rate_limit_exceeded"}), 429

    # Execute action
    conn = get_db()
    cur = conn.cursor()

    result = {}
    if action == "approve_draft" and target_type == "linkedin_draft":
        cur.execute("UPDATE linkedin_drafts SET status = 'approved' WHERE id = %s AND status = 'pending' RETURNING id", (target_id,))
        row = cur.fetchone()
        result = {"approved": bool(row), "draft_id": target_id}

    elif action == "reject_draft" and target_type == "linkedin_draft":
        cur.execute("UPDATE linkedin_drafts SET status = 'rejected' WHERE id = %s AND status = 'pending' RETURNING id", (target_id,))
        row = cur.fetchone()
        result = {"rejected": bool(row), "draft_id": target_id}

    elif action == "flag_attention":
        result = {"flagged": True, "target_type": target_type, "target_id": target_id}

    # Log action (Turtle condition — all actions logged with undo capability)
    cur.execute("""INSERT INTO browser_ring_actions (user_id, action_type, target_type, target_id, payload, provenance)
        VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb)""",
        (request.ring_user, action, target_type, target_id,
         json.dumps(data), json.dumps({"ring_tier": request.ring_tier, "ip": request.remote_addr})))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"ok": True, "action": action, "result": result})


@app.route("/api/ring/undo", methods=["POST"])
@require_auth
def ring_undo():
    """Undo a browser ring action within 5 minutes (Turtle condition)."""
    data = request.get_json(silent=True)
    if not data or "action_id" not in data:
        return jsonify({"error": "action_id required"}), 400

    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""SELECT * FROM browser_ring_actions
        WHERE id = %s AND user_id = %s AND undone_at IS NULL
        AND created_at > NOW() - INTERVAL '5 minutes'""",
        (data["action_id"], request.ring_user))
    action = cur.fetchone()

    if not action:
        cur.close()
        conn.close()
        return jsonify({"error": "action not found or undo window expired"}), 404

    # Reverse the action
    if action["action_type"] == "approve_draft" and action["target_type"] == "linkedin_draft":
        cur.execute("UPDATE linkedin_drafts SET status = 'pending' WHERE id = %s", (action["target_id"],))
    elif action["action_type"] == "reject_draft" and action["target_type"] == "linkedin_draft":
        cur.execute("UPDATE linkedin_drafts SET status = 'pending' WHERE id = %s", (action["target_id"],))

    cur.execute("UPDATE browser_ring_actions SET undone_at = NOW(), undo_reason = %s WHERE id = %s",
                (data.get("reason", "user_undo"), action["id"]))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"ok": True, "undone": action["id"]})


@app.route("/api/ring/pending", methods=["GET"])
@require_auth
def ring_pending():
    """Get items pending Chief action."""
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Pending LinkedIn drafts
    cur.execute("""SELECT id, source_type, LEFT(draft_content, 200) as preview,
        array_to_string(hashtags, ', ') as tags
        FROM linkedin_drafts WHERE status = 'pending' ORDER BY id""")
    drafts = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify({"drafts": drafts})


@app.route("/api/ring/generate-token", methods=["POST"])
def generate_token():
    """Generate a new auth token. Called internally by TPM, not exposed to public.

    This endpoint should only be accessible from localhost/internal network.
    """
    if request.remote_addr not in ("127.0.0.1", "::1", "192.168.132.223"):
        return jsonify({"error": "internal_only"}), 403
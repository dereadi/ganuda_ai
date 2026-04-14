#!/usr/bin/env python3
"""
Claude Code Analytics API — Sovereign ShipCard Fork
Cherokee AI Federation — For the Seven Generations

Receives parsed analytics from nodes, stores in PostgreSQL, serves dashboard.
Port 9500, LAN-only.

Usage:
    python3 analytics_api.py
"""

import json
import os
import sys
from datetime import datetime

sys.path.insert(0, '/ganuda/lib')
sys.path.insert(0, '/ganuda/config')

from flask import Flask, request, jsonify, render_template_string
from ganuda_db import get_connection, managed_connection

app = Flask(__name__)


def store_stats(stats: dict):
    """Store parsed analytics in PostgreSQL."""
    tokens = stats.get("total_tokens", {})
    with managed_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO claude_code_stats
                (node, collected_at, total_sessions, tokens_input, tokens_output,
                 tokens_cache_create, tokens_cache_read, total_cost_usd,
                 models, projects, tool_calls, date_range, file_count, raw_stats)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            stats.get("node", "unknown"),
            stats.get("collected_at", datetime.now().isoformat()),
            stats.get("total_sessions", 0),
            tokens.get("input", 0),
            tokens.get("output", 0),
            tokens.get("cache_create", 0),
            tokens.get("cache_read", 0),
            stats.get("total_cost_usd", 0),
            json.dumps(stats.get("models", {})),
            json.dumps(stats.get("projects", {})),
            json.dumps(stats.get("tool_calls", {})),
            json.dumps(stats.get("date_range", {})),
            stats.get("file_count", 0),
            json.dumps(stats),
        ))


def get_latest_per_node() -> list:
    """Get most recent stats for each node."""
    with managed_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT ON (node)
                node, collected_at, total_sessions, tokens_input, tokens_output,
                tokens_cache_create, tokens_cache_read, total_cost_usd,
                models, projects, tool_calls, date_range, file_count
            FROM claude_code_stats
            ORDER BY node, collected_at DESC
        """)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_federation_summary() -> dict:
    """Aggregate across all nodes."""
    nodes = get_latest_per_node()
    total_sessions = 0
    total_cost = 0.0
    total_input = 0
    total_output = 0
    total_cache_create = 0
    total_cache_read = 0
    all_models = {}
    all_tools = {}

    for n in nodes:
        total_sessions += n["total_sessions"] or 0
        total_cost += float(n["total_cost_usd"] or 0)
        total_input += n["tokens_input"] or 0
        total_output += n["tokens_output"] or 0
        total_cache_create += n["tokens_cache_create"] or 0
        total_cache_read += n["tokens_cache_read"] or 0

        models = n["models"] if isinstance(n["models"], dict) else json.loads(n["models"] or "{}")
        for m, ms in models.items():
            if m not in all_models:
                all_models[m] = {"sessions": 0, "cost": 0.0}
            all_models[m]["sessions"] += ms.get("sessions", 0)
            all_models[m]["cost"] += ms.get("cost", 0)

        tools = n["tool_calls"] if isinstance(n["tool_calls"], dict) else json.loads(n["tool_calls"] or "{}")
        for t, c in tools.items():
            all_tools[t] = all_tools.get(t, 0) + c

    return {
        "node_count": len(nodes),
        "total_sessions": total_sessions,
        "total_cost_usd": round(total_cost, 2),
        "total_tokens": {
            "input": total_input, "output": total_output,
            "cache_create": total_cache_create, "cache_read": total_cache_read,
        },
        "models": dict(sorted(all_models.items(), key=lambda x: -x[1]["cost"])),
        "tool_calls": dict(sorted(all_tools.items(), key=lambda x: -x[1])[:20]),
        "nodes": [{
            "node": n["node"],
            "sessions": n["total_sessions"],
            "cost": float(n["total_cost_usd"] or 0),
            "collected_at": str(n["collected_at"]),
        } for n in nodes],
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/api/stats", methods=["POST"])
def post_stats():
    """Accept parser output JSON, store in DB."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body"}), 400
    store_stats(data)
    return jsonify({"status": "stored", "node": data.get("node")}), 201


@app.route("/api/summary")
def api_summary():
    """Federation-wide summary."""
    return jsonify(get_federation_summary())


@app.route("/api/node/<name>")
def api_node(name):
    """Latest stats for a specific node."""
    nodes = get_latest_per_node()
    for n in nodes:
        if n["node"] == name or name in n["node"]:
            return jsonify(n, default=str)
    return jsonify({"error": "Node not found"}), 404


@app.route("/dashboard")
def dashboard():
    """HTML dashboard."""
    summary = get_federation_summary()
    return render_template_string(DASHBOARD_HTML, s=summary)


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# ---------------------------------------------------------------------------
# Dashboard HTML
# ---------------------------------------------------------------------------

DASHBOARD_HTML = """<!DOCTYPE html>
<html><head>
<title>Claude Code Analytics — Stoneclad Federation</title>
<style>
body { font-family: 'Segoe UI', system-ui, sans-serif; background: #0d1117; color: #c9d1d9; margin: 0; padding: 20px; }
h1 { color: #58a6ff; border-bottom: 1px solid #30363d; padding-bottom: 10px; }
h2 { color: #8b949e; margin-top: 30px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
.card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; }
.card .value { font-size: 2em; color: #58a6ff; font-weight: bold; }
.card .label { color: #8b949e; font-size: 0.9em; margin-top: 5px; }
table { border-collapse: collapse; width: 100%; margin: 10px 0; }
th, td { text-align: left; padding: 8px 12px; border-bottom: 1px solid #21262d; }
th { color: #8b949e; font-weight: normal; }
td { color: #c9d1d9; }
.cost { color: #f0883e; font-weight: bold; }
.bar { background: #1f6feb; height: 8px; border-radius: 4px; display: inline-block; }
footer { margin-top: 40px; color: #484f58; font-size: 0.8em; border-top: 1px solid #21262d; padding-top: 10px; }
</style>
</head><body>
<h1>Claude Code Analytics</h1>
<p>Stoneclad Federation — Sovereign Analytics (ShipCard Fork)</p>

<div class="grid">
  <div class="card"><div class="value">{{ s.node_count }}</div><div class="label">Nodes</div></div>
  <div class="card"><div class="value">{{ s.total_sessions }}</div><div class="label">Sessions</div></div>
  <div class="card"><div class="value cost">${{ "%.2f"|format(s.total_cost_usd) }}</div><div class="label">Est. Cost</div></div>
  <div class="card"><div class="value">{{ "{:,}".format(s.total_tokens.input + s.total_tokens.output) }}</div><div class="label">Tokens (in+out)</div></div>
</div>

<h2>By Node</h2>
<table>
<tr><th>Node</th><th>Sessions</th><th>Cost</th><th>Last Collected</th></tr>
{% for n in s.nodes %}
<tr><td>{{ n.node }}</td><td>{{ n.sessions }}</td><td class="cost">${{ "%.2f"|format(n.cost) }}</td><td>{{ n.collected_at[:19] }}</td></tr>
{% endfor %}
</table>

<h2>By Model</h2>
<table>
<tr><th>Model</th><th>Sessions</th><th>Cost</th></tr>
{% for m, ms in s.models.items() %}
<tr><td>{{ m }}</td><td>{{ ms.sessions }}</td><td class="cost">${{ "%.2f"|format(ms.cost) }}</td></tr>
{% endfor %}
</table>

<h2>Tool Calls</h2>
<table>
<tr><th>Tool</th><th>Count</th><th></th></tr>
{% for t, c in s.tool_calls.items() %}
{% set max_calls = s.tool_calls.values()|list|first if s.tool_calls else 1 %}
<tr><td>{{ t }}</td><td>{{ "{:,}".format(c) }}</td><td><span class="bar" style="width: {{ (c / max_calls * 200)|int }}px"></span></td></tr>
{% endfor %}
</table>

<footer>Generated by Sovereign Claude Code Analytics — Cherokee AI Federation — For the Seven Generations</footer>
</body></html>"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9500, debug=False)

# Jr Instruction: Team Orientation Guide Page

**Task**: Create a team orientation page at ganuda.us/team.html for new members (Kensie, Maik, future hires)
**Priority**: 6
**Story Points**: 3
**Epic**: #1974

## Context

New team members need a quick reference for the federation. This page explains the node map, key services, how to access things, and the Cherokee governance philosophy at a high level. Published to web_content like other pages.

## Steps

### Step 1: Create the orientation page generator

Create `/ganuda/scripts/generate_team_page.py`

```python
#!/usr/bin/env python3
"""Generate team orientation page for ganuda.us/team.html."""

import hashlib
import os
import re
import psycopg2
from datetime import datetime

DB_HOST = os.environ.get("CHEROKEE_DB_HOST", "192.168.132.222")
DB_NAME = os.environ.get("CHEROKEE_DB_NAME", "zammad_production")
DB_USER = os.environ.get("CHEROKEE_DB_USER", "claude")
DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")

html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Team Orientation</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family: -apple-system, system-ui, sans-serif; background:#0a0e14; color:#c8ccd4; padding:16px; max-width:700px; margin:0 auto; }
  h1 { font-size:1.3em; color:#e8b04a; margin-bottom:16px; }
  h2 { font-size:1em; color:#7aafff; margin:16px 0 8px; }
  .card { background:#151a22; border-radius:8px; padding:14px; margin-bottom:12px; }
  .node { display:grid; grid-template-columns:100px 1fr; gap:4px; font-size:0.85em; padding:4px 0; border-bottom:1px solid #1a2030; }
  .node:last-child { border-bottom:none; }
  .node-name { font-weight:600; color:#fa7; }
  .node-desc { color:#999; }
  ul { padding-left:20px; font-size:0.85em; line-height:1.6; }
  li { margin-bottom:4px; }
  .principle { font-size:0.85em; padding:6px 0; border-bottom:1px solid #1a2030; }
  .principle:last-child { border-bottom:none; }
  .dc-num { color:#e8b04a; font-weight:600; min-width:40px; display:inline-block; }
  a { color:#7aafff; }
</style>
</head>
<body>
<h1>Cherokee AI Federation — Team Orientation</h1>

<div class="card">
<h2>Node Map</h2>
<div class="node"><span class="node-name">redfin</span><span class="node-desc">GPU compute (RTX PRO 6000 96GB). vLLM, Gateway, Jr Executor, SAG. .223</span></div>
<div class="node"><span class="node-name">bluefin</span><span class="node-desc">PostgreSQL, VLM (Qwen2-VL), YOLO, optic-nerve. RTX 5070. .222</span></div>
<div class="node"><span class="node-name">greenfin</span><span class="node-desc">Embedding server, OpenObserve monitoring, FreeIPA bridge. .224</span></div>
<div class="node"><span class="node-name">owlfin</span><span class="node-desc">DMZ web server (primary), Caddy. .170 mgmt / .30.2 DMZ</span></div>
<div class="node"><span class="node-name">eaglefin</span><span class="node-desc">DMZ web server (failover), Caddy. .84 mgmt / .30.3 DMZ</span></div>
<div class="node"><span class="node-name">bmasass</span><span class="node-desc">M4 Max 128GB, MLX DeepSeek-R1 70B. Mobile node (Tailscale). .21</span></div>
</div>

<div class="card">
<h2>Key Services</h2>
<ul>
<li><strong>Gateway</strong> (redfin:8080) — routes all LLM requests, council voting, Two Wolves audit</li>
<li><strong>vLLM</strong> (redfin:8000) — Qwen2.5-72B-Instruct-AWQ, primary reasoning engine</li>
<li><strong>SAG</strong> (redfin:5000) — Flask API for federation management</li>
<li><strong>Jr Executor</strong> (redfin) — autonomous task worker, TEG decomposition</li>
<li><strong>PostgreSQL</strong> (bluefin:5432) — central database (zammad_production)</li>
<li><strong>Embedding</strong> (greenfin:8003) — BGE-large-en-v1.5, 1024d semantic search</li>
<li><strong>FreeIPA</strong> (silverfin:192.168.10.10) — identity, SSSD sudo, via greenfin bridge</li>
</ul>
</div>

<div class="card">
<h2>Getting Started</h2>
<ul>
<li>SSH to nodes via 192.168.132.x (ask Chief for credentials)</li>
<li>Code lives in <code>/ganuda</code> on Linux, <code>/Users/Shared/ganuda</code> on macOS</li>
<li>Python venv on redfin: <code>cherokee_venv</code>. Other nodes use system python3.</li>
<li>Secrets in <code>/ganuda/config/secrets.env</code> — never commit</li>
<li>Jr instructions go in <code>/ganuda/docs/jr_instructions/</code></li>
<li>Check <a href="/status.html">Status Page</a> for live cluster state</li>
</ul>
</div>

<div class="card">
<h2>Design Constraints (DC-1 through DC-11)</h2>
<div class="principle"><span class="dc-num">DC-1</span> Lazy Awareness — minimal energy for awareness</div>
<div class="principle"><span class="dc-num">DC-6</span> Gradient Principle — specialization is gravity, not boundary</div>
<div class="principle"><span class="dc-num">DC-7</span> Noyawisgi — transforms under pressure, collapse produces next species</div>
<div class="principle"><span class="dc-num">DC-9</span> Waste Heat Limit — compute only what matters</div>
<div class="principle"><span class="dc-num">DC-10</span> Reflex Principle — autonomous response at each timescale</div>
<div class="principle"><span class="dc-num">DC-11</span> Macro Polymorphism — same governance pattern repeats at every scale</div>
</div>

<div style="text-align:center; margin-top:16px; font-size:0.7em; color:#444;">
  <a href="/index.html" style="color:#556; text-decoration:none;">Back to Ops Console</a>
</div>
</body>
</html>"""


if __name__ == "__main__":
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

    content_hash = hashlib.sha256(html.encode()).hexdigest()
    conn = psycopg2.connect(host=DB_HOST, port=5432, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cur = conn.cursor()
    cur.execute("""INSERT INTO web_content (site, path, content, content_type, content_hash, published, updated_at)
        VALUES ('ganuda.us', '/team.html', %s, 'text/html', %s, true, NOW())
        ON CONFLICT (site, path) DO UPDATE SET content = %s, content_hash = %s, updated_at = NOW()""",
        (html, content_hash, html, content_hash))
    conn.commit()
    cur.close()
    conn.close()
    print(f"Team page published ({len(html)} bytes)")
```

## Verification

1. Run: `cd /ganuda && python3 scripts/generate_team_page.py`
2. Check: page visible at ganuda.us/team.html

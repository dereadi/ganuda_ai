#!/usr/bin/env python3
"""Generate node health dashboard for ganuda.us/health.html."""

import hashlib
import os
import socket
import psycopg2
from datetime import datetime


DB_HOST = os.environ.get("CHEROKEE_DB_HOST", "192.168.132.222")
DB_NAME = os.environ.get("CHEROKEE_DB_NAME", "zammad_production")
DB_USER = os.environ.get("CHEROKEE_DB_USER", "claude")
DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")

NODES = {
    "redfin": {
        "ip": "192.168.132.223",
        "services": [
            ("vLLM", 8000),
            ("Gateway", 8080),
            ("SAG", 5000),
        ]
    },
    "bluefin": {
        "ip": "192.168.132.222",
        "services": [
            ("PostgreSQL", 5432),
            ("VLM", 8090),
            ("YOLO", 8091),
            ("VLM Adapter", 8092),
        ]
    },
    "greenfin": {
        "ip": "192.168.132.224",
        "services": [
            ("Embedding", 8003),
        ]
    },
    "owlfin": {
        "ip": "192.168.132.170",
        "services": [
            ("Caddy", 80),
        ]
    },
    "eaglefin": {
        "ip": "192.168.132.84",
        "services": [
            ("Caddy", 80),
        ]
    },
    "bmasass": {
        "ip": "192.168.132.21",
        "services": [
            ("MLX DeepSeek", 8800),
        ]
    },
}


def check_port(ip, port, timeout=3):
    """Return True if TCP port is reachable."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, port))
        s.close()
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def gather_health():
    results = {}
    for node, info in NODES.items():
        ip = info["ip"]
        node_up = check_port(ip, 22, timeout=2)
        services = []
        for svc_name, port in info["services"]:
            up = check_port(ip, port) if node_up else False
            services.append((svc_name, port, up))
        results[node] = {"ip": ip, "node_up": node_up, "services": services}
    return results


def render_html(health):
    now = datetime.now().strftime("%Y-%m-%d %H:%M CT")
    nodes_html = ""
    for node, info in health.items():
        node_color = "#4a7" if info["node_up"] else "#d44"
        node_icon = "&#9679;" if info["node_up"] else "&#9888;"
        svcs_html = ""
        for svc_name, port, up in info["services"]:
            svc_color = "#4a7" if up else "#d44"
            svc_icon = "&#10003;" if up else "&#10007;"
            svcs_html += f'<div class="svc"><span style="color:{svc_color}">{svc_icon}</span> {svc_name} :{port}</div>\n'
        nodes_html += f"""<div class="card">
  <h2 style="color:{node_color}">{node_icon} {node} <span class="ip">{info['ip']}</span></h2>
  {svcs_html}
</div>\n"""

    total_up = sum(1 for n in health.values() if n["node_up"])
    total_svcs = sum(1 for n in health.values() for _, _, up in n["services"] if up)
    total_svcs_all = sum(len(n["services"]) for n in health.values())

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="60">
<title>Node Health</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: -apple-system, system-ui, sans-serif; background:#0a0e14; color:#c8ccd4; padding:16px; max-width:600px; margin:0 auto; }}
  h1 {{ font-size:1.3em; color:#e8b04a; margin-bottom:4px; }}
  .subtitle {{ font-size:0.8em; color:#666; margin-bottom:16px; }}
  .summary {{ font-size:0.9em; margin-bottom:16px; color:#7aafff; }}
  .card {{ background:#151a22; border-radius:8px; padding:12px; margin-bottom:10px; }}
  .card h2 {{ font-size:0.95em; margin-bottom:6px; }}
  .ip {{ font-size:0.75em; color:#556; font-weight:normal; }}
  .svc {{ font-size:0.82em; padding:3px 0; padding-left:8px; }}
</style>
</head>
<body>
<h1>Node Health</h1>
<div class="subtitle">Last checked: {now} &mdash; auto-refreshes every 60s</div>
<div class="summary">{total_up}/{len(health)} nodes up &mdash; {total_svcs}/{total_svcs_all} services responding</div>
{nodes_html}
<div style="text-align:center; margin-top:16px; font-size:0.7em; color:#444;">
  <a href="/index.html" style="color:#556; text-decoration:none;">Back to Ops Console</a>
</div>
</body>
</html>"""
    return html


def publish(html):
    content_hash = hashlib.sha256(html.encode()).hexdigest()
    conn = psycopg2.connect(host=DB_HOST, port=5432, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cur = conn.cursor()
    cur.execute("""INSERT INTO web_content (site, path, content, content_type, content_hash, published, updated_at)
        VALUES ('ganuda.us', '/health.html', %s, 'text/html', %s, true, NOW())
        ON CONFLICT (site, path) DO UPDATE SET content = %s, content_hash = %s, updated_at = NOW()""",
        (html, content_hash, html, content_hash))
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    if not DB_PASS:
        import re
        try:
            with open("/ganuda/config/secrets.env") as f:
                for line in f:
                    m = re.match(r"^(\w+)=(.+)$", line.strip())
                    if m:
                        os.environ[m.group(1)] = m.group(2)
            DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")
        except FileNotFoundError:
            pass

    health = gather_health()
    html = render_html(health)
    publish(html)
    total_up = sum(1 for n in health.values() if n["node_up"])
    total_svcs = sum(1 for n in health.values() for _, _, up in n["services"] if up)
    print(f"Health page published: {total_up}/{len(health)} nodes, {total_svcs} services up")
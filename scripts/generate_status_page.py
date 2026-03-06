#!/usr/bin/env python3
"""
Generate the Federation Status Page — Chief's visibility into the organism.

Pulls live stats from the database, formats as HTML, publishes via web_content.
Run on a timer or on-demand. Chief can bookmark ganuda.us/status on his phone.
"""

import psycopg2
import os
from datetime import datetime

DB_HOST = os.environ.get("CHEROKEE_DB_HOST", "192.168.132.222")
DB_NAME = os.environ.get("CHEROKEE_DB_NAME", "zammad_production")
DB_USER = os.environ.get("CHEROKEE_DB_USER", "claude")
DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")


def gather_stats():
    conn = psycopg2.connect(host=DB_HOST, port=5432, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cur = conn.cursor()
    stats = {}

    # Jr tasks by status
    cur.execute("SELECT status, COUNT(*) FROM jr_work_queue GROUP BY status")
    stats["jr"] = dict(cur.fetchall())

    # Recent completions (last 12h)
    cur.execute("""SELECT title, completed_at FROM jr_work_queue
        WHERE completed_at > NOW() - INTERVAL '12 hours' AND title NOT LIKE '[TEG]%'
        ORDER BY completed_at DESC LIMIT 12""")
    stats["jr_recent"] = [(r[0], r[1].strftime("%H:%M") if r[1] else "") for r in cur.fetchall()]

    # In progress right now
    cur.execute("""SELECT title FROM jr_work_queue WHERE status = 'in_progress'
        AND title NOT LIKE '[TEG]%' ORDER BY started_at DESC LIMIT 8""")
    stats["jr_active"] = [r[0] for r in cur.fetchall()]

    # Kanban
    cur.execute("SELECT status, COUNT(*) FROM duyuktv_tickets GROUP BY status")
    stats["kanban"] = dict(cur.fetchall())

    # Thermal memory
    cur.execute("SELECT COUNT(*) FROM thermal_memory_archive")
    stats["thermal_total"] = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM thermal_memory_archive WHERE sacred_pattern = true")
    stats["thermal_sacred"] = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM thermal_memory_archive WHERE created_at > NOW() - INTERVAL '12 hours'")
    stats["thermal_new"] = cur.fetchone()[0]

    # Council votes
    cur.execute("SELECT COUNT(*) FROM council_votes")
    stats["votes_total"] = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM council_votes WHERE voted_at > NOW() - INTERVAL '24 hours'")
    stats["votes_24h"] = cur.fetchone()[0]

    # Recent epics
    cur.execute("""SELECT id, title, status FROM duyuktv_tickets
        WHERE title LIKE 'EPIC%' ORDER BY id DESC LIMIT 8""")
    stats["epics"] = cur.fetchall()

    cur.close()
    conn.close()
    return stats


def render_html(stats):
    try:
        import sys
        sys.path.insert(0, "/ganuda")
        from scripts.web_nav import nav_html
        nav = nav_html("Status")
    except ImportError:
        nav = ""
    now = datetime.now().strftime("%Y-%m-%d %H:%M CT")

    jr_done = stats["jr"].get("completed", 0)
    jr_active = stats["jr"].get("in_progress", 0)
    jr_pending = stats["jr"].get("pending", 0)
    kanban_open = stats["kanban"].get("open", 0) + stats["kanban"].get("in_progress", 0)
    kanban_done = stats["kanban"].get("completed", 0)
    kanban_backlog = stats["kanban"].get("backlog", 0)

    # Active work list
    active_html = ""
    if stats["jr_active"]:
        for t in stats["jr_active"]:
            active_html += f'<div class="item active">{t}</div>\n'
    else:
        active_html = '<div class="item">No active tasks — organism at rest</div>'

    # Recent completions
    recent_html = ""
    for title, ts in stats["jr_recent"]:
        recent_html += f'<div class="item done"><span class="time">{ts}</span> {title}</div>\n'
    if not recent_html:
        recent_html = '<div class="item">No recent completions</div>'

    # Epics
    epics_html = ""
    for eid, title, status in stats["epics"]:
        icon = {"completed": "&#10003;", "open": "&#9675;", "in_progress": "&#9654;", "backlog": "&#8943;"}.get(status, "?")
        color = {"completed": "#4a7", "open": "#7af", "in_progress": "#fa7", "backlog": "#888"}.get(status, "#888")
        clean_title = title.replace("EPIC: ", "").replace("EPIC:", "")
        epics_html += f'<div class="item" style="border-left:3px solid {color}; padding-left:8px">{icon} {clean_title}</div>\n'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="60">
<title>Federation Status</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: -apple-system, system-ui, sans-serif; background:#0a0e14; color:#c8ccd4; padding:16px; max-width:600px; margin:0 auto; }}
  h1 {{ font-size:1.3em; color:#e8b04a; margin-bottom:4px; }}
  .subtitle {{ font-size:0.8em; color:#666; margin-bottom:16px; }}
  .card {{ background:#151a22; border-radius:8px; padding:12px; margin-bottom:12px; }}
  .card h2 {{ font-size:0.95em; color:#7aafff; margin-bottom:8px; }}
  .stats {{ display:grid; grid-template-columns: repeat(3, 1fr); gap:8px; margin-bottom:8px; }}
  .stat {{ text-align:center; }}
  .stat .num {{ font-size:1.6em; font-weight:700; color:#e8b04a; }}
  .stat .label {{ font-size:0.7em; color:#888; }}
  .item {{ font-size:0.82em; padding:4px 0; border-bottom:1px solid #1a2030; }}
  .item:last-child {{ border-bottom:none; }}
  .item.active {{ color:#fa7; }}
  .item.done {{ color:#6b8; }}
  .time {{ color:#556; font-size:0.85em; margin-right:6px; }}
  .pulse {{ display:inline-block; width:8px; height:8px; background:#4a7; border-radius:50%; margin-right:6px; animation: pulse 2s infinite; }}
  @keyframes pulse {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.3; }} }}
  .sacred {{ color:#e8b04a; font-size:0.75em; }}
</style>
</head>
<body>
{{nav}}
<h1>&#127793; Cherokee AI Federation</h1>
<div class="subtitle">Last updated: {now} &mdash; auto-refreshes every 60s</div>

<div class="card">
  <h2>Organism Vitals</h2>
  <div class="stats">
    <div class="stat"><div class="num">{stats['thermal_total']:,}</div><div class="label">Memories</div></div>
    <div class="stat"><div class="num">{stats['thermal_sacred']:,}</div><div class="label sacred">&#10025; Sacred</div></div>
    <div class="stat"><div class="num">{stats['votes_total']:,}</div><div class="label">Council Votes</div></div>
  </div>
  <div class="stats">
    <div class="stat"><div class="num">{stats['thermal_new']}</div><div class="label">New (12h)</div></div>
    <div class="stat"><div class="num">{stats['votes_24h']}</div><div class="label">Votes (24h)</div></div>
    <div class="stat"><div class="num">{jr_done}</div><div class="label">Jr Tasks Done</div></div>
  </div>
</div>

<div class="card">
  <h2><span class="pulse"></span>Working Now</h2>
  {active_html}
</div>

<div class="card">
  <h2>Recently Completed</h2>
  {recent_html}
</div>

<div class="card">
  <h2>Kanban</h2>
  <div class="stats">
    <div class="stat"><div class="num">{kanban_open}</div><div class="label">Active</div></div>
    <div class="stat"><div class="num">{kanban_backlog}</div><div class="label">Backlog</div></div>
    <div class="stat"><div class="num">{kanban_done}</div><div class="label">Done</div></div>
  </div>
</div>

<div class="card">
  <h2>Epics</h2>
  {epics_html}
</div>

<div style="text-align:center; margin-top:16px; font-size:0.7em; color:#444;">
  For Seven Generations &mdash; DC-1 through DC-11
</div>
</body>
</html>"""
    html = html.replace("{nav}", nav)
    return html


def publish(html):
    """Push to web_content for materializer deployment."""
    conn = psycopg2.connect(host=DB_HOST, port=5432, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cur = conn.cursor()

    import hashlib
    content_hash = hashlib.sha256(html.encode()).hexdigest()
    cur.execute("""INSERT INTO web_content (site, path, content, content_type, content_hash, published, updated_at)
        VALUES ('ganuda.us', '/status.html', %s, 'text/html', %s, true, NOW())
        ON CONFLICT (site, path) DO UPDATE SET content = %s, content_hash = %s, updated_at = NOW()""",
        (html, content_hash, html, content_hash))

    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    # Load secrets if not in env
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

    stats = gather_stats()
    html = render_html(stats)
    publish(html)
    print(f"Status page published to /status ({len(html)} bytes)")
    print(f"  Memories: {stats['thermal_total']:,} ({stats['thermal_sacred']:,} sacred)")
    print(f"  Jr tasks: {stats['jr'].get('completed',0)} done, {stats['jr'].get('in_progress',0)} active")
    print(f"  Kanban: {stats['kanban'].get('open',0)+stats['kanban'].get('in_progress',0)} active, {stats['kanban'].get('completed',0)} done")

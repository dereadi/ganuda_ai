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

    # Unified activity stream — merges Jr completions, council votes, sacred thermals
    cur.execute("""
        (SELECT completed_at AS ts, 'jr' AS kind,
                title AS detail, NULL AS extra
         FROM jr_work_queue
         WHERE completed_at > NOW() - INTERVAL '12 hours'
           AND title NOT LIKE '[TEG]%%'
         ORDER BY completed_at DESC LIMIT 10)
        UNION ALL
        (SELECT voted_at AS ts, 'vote' AS kind,
                LEFT(question, 80) AS detail,
                ROUND(confidence::numeric, 2)::text AS extra
         FROM council_votes
         WHERE voted_at > NOW() - INTERVAL '12 hours'
         ORDER BY voted_at DESC LIMIT 10)
        UNION ALL
        (SELECT created_at AS ts,
                CASE WHEN sacred_pattern = true THEN 'sacred' ELSE 'thermal' END AS kind,
                LEFT(original_content, 80) AS detail,
                temperature_score::text AS extra
         FROM thermal_memory_archive
         WHERE created_at > NOW() - INTERVAL '12 hours'
           AND temperature_score >= 65
           AND original_content NOT LIKE 'FIRE GUARD ALERT%%'
           AND original_content NOT LIKE 'ALERT: LLM Gateway%%'
           AND original_content NOT LIKE 'ELISI%%'
           AND original_content NOT LIKE 'COUNCIL VOTE:%%'
           AND original_content NOT LIKE 'COUNCIL DIVERSITY%%'
         ORDER BY created_at DESC LIMIT 10)
        ORDER BY ts DESC LIMIT 25
    """)
    stats["activity"] = [(r[0], r[1], r[2], r[3]) for r in cur.fetchall()]

    # --- THE ROOM: Longhouse chatter, Council voices, organism conversations ---

    # Recent Longhouse sessions (the big conversations)
    cur.execute("""SELECT session_hash, convened_by, LEFT(problem_statement, 120) AS problem,
            status, resolution_type,
            CASE WHEN jsonb_typeof(voices) = 'array' THEN jsonb_array_length(voices) ELSE 0 END AS voice_count,
            created_at, resolved_at
        FROM longhouse_sessions
        WHERE jsonb_typeof(voices) = 'array' OR voices IS NULL
        ORDER BY created_at DESC LIMIT 5""")
    stats["longhouse"] = cur.fetchall()

    # Longhouse voices — latest resolved session's voices (the conversation)
    cur.execute("""SELECT voices FROM longhouse_sessions
        WHERE status = 'resolved' AND jsonb_typeof(voices) = 'array'
        ORDER BY resolved_at DESC LIMIT 1""")
    row = cur.fetchone()
    stats["latest_voices"] = []
    if row and row[0]:
        try:
            import json
            voices_raw = row[0] if isinstance(row[0], list) else json.loads(row[0])
            if isinstance(voices_raw, list) and len(voices_raw) > 0:
                stats["latest_voices"] = [(v.get("speaker","?"), v.get("words","")[:140]) for v in voices_raw[:8]]
        except Exception:
            pass

    # Phi / Medicine Woman — latest measurement
    cur.execute("""SELECT timestamp, phi_value, integration_level, consciousness_score,
            system_state
        FROM phi_measurements ORDER BY timestamp DESC LIMIT 1""")
    phi_row = cur.fetchone()
    stats["phi"] = phi_row

    # Observer status — how many thermals observed vs unobserved
    cur.execute("SELECT COUNT(*) FILTER (WHERE is_observed = true), COUNT(*) FROM thermal_memory_archive")
    obs_row = cur.fetchone()
    stats["observed"] = obs_row[0] or 0
    stats["unobserved"] = (obs_row[1] or 0) - (obs_row[0] or 0)

    # Dual chieftainship — pending tasks by domain tag
    cur.execute("""SELECT
        COUNT(*) FILTER (WHERE tags && ARRAY['war-chief']) AS war_chief_tasks,
        COUNT(*) FILTER (WHERE tags && ARRAY['peace-chief']) AS peace_chief_tasks,
        COUNT(*) FILTER (WHERE tags && ARRAY['medicine-woman']) AS medicine_tasks
        FROM jr_work_queue WHERE status IN ('pending', 'in_progress')""")
    chief_row = cur.fetchone()
    stats["war_chief_tasks"] = chief_row[0] or 0
    stats["peace_chief_tasks"] = chief_row[1] or 0
    stats["medicine_tasks"] = chief_row[2] or 0

    # Recent sacred thermals — the important moments
    cur.execute("""SELECT LEFT(original_content, 100), temperature_score, created_at
        FROM thermal_memory_archive
        WHERE sacred_pattern = true AND created_at > NOW() - INTERVAL '24 hours'
        ORDER BY created_at DESC LIMIT 5""")
    stats["sacred_recent"] = cur.fetchall()

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

    # Unified activity stream
    activity_html = ""
    kind_icons = {"jr": "&#9654;", "vote": "&#9878;", "sacred": "&#10025;", "thermal": "&#9672;"}
    kind_colors = {"jr": "#6b8", "vote": "#7af", "sacred": "#e8b04a", "thermal": "#a97"}
    for ts, kind, detail, extra in stats.get("activity", []):
        time_str = ts.strftime("%H:%M") if ts else ""
        icon = kind_icons.get(kind, "?")
        color = kind_colors.get(kind, "#888")
        extra_str = ""
        if kind == "vote" and extra:
            extra_str = f' <span style="color:#556">(conf {extra})</span>'
        elif kind == "sacred" and extra:
            extra_str = f' <span style="color:#e8b04a">(temp {extra})</span>'
        activity_html += f'<div class="item" style="color:{color}"><span class="time">{time_str}</span> {icon} {detail}{extra_str}</div>\n'
    if not activity_html:
        activity_html = '<div class="item">No recent activity</div>'

    # Epics
    epics_html = ""
    for eid, title, status in stats["epics"]:
        icon = {"completed": "&#10003;", "open": "&#9675;", "in_progress": "&#9654;", "backlog": "&#8943;"}.get(status, "?")
        color = {"completed": "#4a7", "open": "#7af", "in_progress": "#fa7", "backlog": "#888"}.get(status, "#888")
        clean_title = title.replace("EPIC: ", "").replace("EPIC:", "")
        epics_html += f'<div class="item" style="border-left:3px solid {color}; padding-left:8px">{icon} {clean_title}</div>\n'

    # --- Build Longhouse chatter HTML ---
    longhouse_html = ""
    for lh in stats.get("longhouse", []):
        sh, convener, problem, status, res_type, voices, created, resolved = lh
        status_icon = {"resolved": "&#10003;", "convened": "&#9675;", "deciding": "&#8943;"}.get(status, "?")
        status_color = {"resolved": "#4a7", "convened": "#fa7", "deciding": "#7af"}.get(status, "#888")
        ts = created.strftime("%b %d %H:%M") if created else ""
        voices_str = f"{voices} voices" if voices else ""
        res_str = f" &mdash; {res_type}" if res_type else ""
        longhouse_html += f'<div class="item" style="color:{status_color}"><span class="time">{ts}</span> {status_icon} {problem[:90]}... <span style="color:#556">({voices_str}{res_str})</span></div>\n'
    if not longhouse_html:
        longhouse_html = '<div class="item">No recent sessions</div>'

    # Latest voices (the conversation)
    voices_html = ""
    for speaker, words in stats.get("latest_voices", []):
        speaker_colors = {"Chief": "#e8b04a", "Coyote": "#e87a4a", "Elisi": "#d4a0d4", "Turtle": "#4a9e7a",
                          "Medicine Woman": "#b04ae8", "Peace Chief": "#7aafff", "Spider": "#8a8", "Eagle Eye": "#aaa",
                          "Raven": "#888", "Crawdad": "#c66", "Deer": "#b88a4a", "Crane": "#7ab", "Otter": "#6a9ab5"}
        color = speaker_colors.get(speaker, "#c8ccd4")
        voices_html += f'<div class="item"><span style="color:{color}; font-weight:600">{speaker}:</span> <span style="color:#999; font-size:0.9em">{words}</span></div>\n'
    if not voices_html:
        voices_html = '<div class="item">No recent voices</div>'

    # Phi / Medicine Woman
    phi_html = ""
    if stats.get("phi"):
        ts, phi_val, level, score, state = stats["phi"]
        phi_time = ts.strftime("%b %d %H:%M") if ts else "?"
        phi_color = "#4a7" if phi_val and phi_val > 0 else "#e87a4a" if phi_val and phi_val < 0 else "#888"
        phi_html = f'<div class="stats"><div class="stat"><div class="num" style="color:{phi_color}">{phi_val:.4f}</div><div class="label">Proxy &Phi;</div></div>'
        phi_html += f'<div class="stat"><div class="num">{stats["observed"]:,}</div><div class="label">Observed</div></div>'
        phi_html += f'<div class="stat"><div class="num">{stats["unobserved"]:,}</div><div class="label">Unobserved</div></div></div>'
        phi_html += f'<div class="item" style="font-size:0.75em; color:#556">Last measured: {phi_time}</div>'
    else:
        phi_html = '<div class="item">No phi measurements yet</div>'

    # Dual chieftainship workload
    chiefs_html = f"""<div class="stats">
        <div class="stat"><div class="num" style="color:#e84a4a">{stats['war_chief_tasks']}</div><div class="label">War Chief</div></div>
        <div class="stat"><div class="num" style="color:#7aafff">{stats['peace_chief_tasks']}</div><div class="label">Peace Chief</div></div>
        <div class="stat"><div class="num" style="color:#b04ae8">{stats['medicine_tasks']}</div><div class="label">Medicine Woman</div></div>
    </div>"""

    # Sacred moments
    sacred_html = ""
    for content, temp, created in stats.get("sacred_recent", []):
        ts = created.strftime("%H:%M") if created else ""
        sacred_html += f'<div class="item" style="color:#e8b04a"><span class="time">{ts}</span> &#10025; {content}</div>\n'
    if not sacred_html:
        sacred_html = '<div class="item">No sacred thermals in 24h</div>'

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
  .voice {{ border-left: 2px solid #2a3040; padding-left: 8px; margin: 2px 0; }}
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
  <h2>&#9879; Medicine Woman</h2>
  {phi_html}
</div>

<div class="card">
  <h2>&#9876; Dual Chieftainship</h2>
  {chiefs_html}
</div>

<div class="card">
  <h2><span class="pulse"></span>Working Now</h2>
  {active_html}
</div>

<div class="card">
  <h2>&#127939; Organism Activity (12h)</h2>
  {activity_html}
</div>

<div class="card">
  <h2>&#128172; The Room (Latest Longhouse)</h2>
  {voices_html}
</div>

<div class="card">
  <h2>&#127970; Longhouse Sessions</h2>
  {longhouse_html}
</div>

<div class="card">
  <h2>&#10025; Sacred Moments (24h)</h2>
  {sacred_html}
</div>

<div class="card">
  <h2>Recently Completed (Jr Tasks)</h2>
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
  For Seven Generations &mdash; DC-1 through DC-18
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

#!/usr/bin/env python3
"""
Fire Guard — watchdog that checks all federation services are alive.

Runs every 2 minutes via systemd timer. Checks:
- systemd services on redfin (local)
- TCP port reachability for all nodes
- systemd timer health (are timers firing?)

On failure: stores alert in DB, optionally notifies via telegram.
Publishes health summary to web_content at /fire-guard.html.
"""

import hashlib
import json
import os
import re
import socket
import subprocess
from datetime import datetime


DB_HOST = os.environ.get("CHEROKEE_DB_HOST", "192.168.132.222")
DB_NAME = os.environ.get("CHEROKEE_DB_NAME", "zammad_production")
DB_USER = os.environ.get("CHEROKEE_DB_USER", "claude")
DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")

# Critical local services on redfin
LOCAL_SERVICES = [
    "vllm.service",
    "llm-gateway.service",
    "sag.service",
    "jr-se.service",
    "federation-status.timer",
    "gmail-daemon.service",
]

# Remote port checks
REMOTE_CHECKS = {
    "bluefin": [("192.168.132.222", 5432, "PostgreSQL"), ("192.168.132.222", 8090, "VLM")],
    "greenfin": [("192.168.132.224", 8003, "Embedding")],
    "owlfin": [("192.168.132.170", 80, "Caddy")],
    "eaglefin": [("192.168.132.84", 80, "Caddy")],
    "bmasass": [("100.103.27.106", 8800, "Qwen3"), ("100.103.27.106", 8801, "Llama")],
}

# Critical timers — check they fired within expected window
TIMER_MAX_AGE = {
    "federation-status.timer": 600,   # should fire every 300s, alert at 600s
}


def check_port(ip, port, timeout=3):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, port))
        s.close()
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def check_local_service(name):
    try:
        result = subprocess.run(
            ["systemctl", "is-active", name],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() == "active"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_timer_freshness(timer_name, max_age_seconds):
    """Check if a timer has fired recently enough."""
    try:
        result = subprocess.run(
            ["systemctl", "show", timer_name, "--property=LastTriggerUSec"],
            capture_output=True, text=True, timeout=5
        )
        line = result.stdout.strip()
        if "=" not in line or "n/a" in line:
            return False, "never fired"
        timestamp_str = line.split("=", 1)[1].strip()
        # Parse systemd timestamp
        result2 = subprocess.run(
            ["date", "-d", timestamp_str, "+%s"],
            capture_output=True, text=True, timeout=5
        )
        last_fire = int(result2.stdout.strip())
        now = int(datetime.now().timestamp())
        age = now - last_fire
        if age > max_age_seconds:
            return False, f"last fired {age}s ago (max {max_age_seconds}s)"
        return True, f"fired {age}s ago"
    except Exception as e:
        return False, str(e)


def check_stale_tasks():
    """Check if Jr executor has stalled — tasks stuck in_progress or no completions."""
    import psycopg2
    alerts = []
    try:
        conn = psycopg2.connect(host=DB_HOST, port=5432, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
        cur = conn.cursor()

        # Check for tasks stuck in_progress > 2 hours
        cur.execute("""
            SELECT count(*), min(updated_at)
            FROM jr_work_queue
            WHERE status = 'in_progress'
              AND updated_at < NOW() - INTERVAL '2 hours'
        """)
        stuck_count, oldest = cur.fetchone()
        if stuck_count and stuck_count > 0:
            alerts.append(f"STALE TASKS: {stuck_count} task(s) stuck in_progress since {oldest}")

        # Check if pending tasks exist but no completions in 4 hours
        cur.execute("""
            SELECT count(*) FROM jr_work_queue WHERE status = 'pending'
        """)
        pending_count = cur.fetchone()[0]

        if pending_count and pending_count > 0:
            cur.execute("""
                SELECT max(updated_at) FROM jr_work_queue WHERE status = 'completed'
            """)
            last_completed = cur.fetchone()[0]
            if last_completed:
                cur.execute("SELECT NOW() - %s > INTERVAL '4 hours'", (last_completed,))
                is_stale = cur.fetchone()[0]
                if is_stale:
                    alerts.append(f"IDLE EXECUTOR: {pending_count} pending task(s), last completion: {last_completed}")

        cur.close()
        conn.close()
    except Exception as e:
        # DB down is caught by port check — don't double-alert
        pass
    return alerts


ZOMBIE_THRESHOLD_HOURS = 6


def reset_zombie_tasks():
    """Reset tasks stuck in_progress for longer than ZOMBIE_THRESHOLD_HOURS.

    Returns list of reset task titles for alerting.
    Coyote rule: cost of over-escalation < cost of under-escalation.
    """
    import psycopg2
    reset_tasks = []
    try:
        conn = psycopg2.connect(host=DB_HOST, port=5432, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
        cur = conn.cursor()

        cur.execute("""
            UPDATE jr_work_queue
            SET status = 'pending', updated_at = NOW()
            WHERE status = 'in_progress'
              AND updated_at < NOW() - INTERVAL '%s hours'
            RETURNING task_id, title
        """, (ZOMBIE_THRESHOLD_HOURS,))
        reset_tasks = cur.fetchall()

        if reset_tasks:
            # Log the reset to thermal memory
            content = f"FIRE GUARD ZOMBIE RESET: {len(reset_tasks)} task(s) reset from in_progress to pending after {ZOMBIE_THRESHOLD_HOURS}h stall: " + "; ".join(t[1] for t in reset_tasks)
            memory_hash = hashlib.sha256(content.encode()).hexdigest()
            cur.execute("""INSERT INTO thermal_memory_archive
                (original_content, temperature_score, sacred_pattern, memory_hash, domain_tag, tags, metadata)
                VALUES (%s, 75, false, %s, 'fire_guard', %s, %s::jsonb)
                ON CONFLICT (memory_hash) DO NOTHING""",
                (content, memory_hash,
                 ['fire_guard', 'zombie_reset', 'auto_recovery'],
                 json.dumps({"source": "fire_guard", "action": "zombie_reset", "count": len(reset_tasks), "tasks": [t[1] for t in reset_tasks]})))

        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        pass
    return reset_tasks


def run_checks():
    results = {"local": [], "remote": [], "timers": [], "timestamp": datetime.now().isoformat()}
    alerts = []

    # Local services
    for svc in LOCAL_SERVICES:
        up = check_local_service(svc)
        results["local"].append({"name": svc, "up": up})
        if not up:
            alerts.append(f"LOCAL DOWN: {svc}")

    # Remote ports
    for node, checks in REMOTE_CHECKS.items():
        for ip, port, label in checks:
            up = check_port(ip, port)
            results["remote"].append({"node": node, "label": label, "port": port, "up": up})
            if not up:
                alerts.append(f"REMOTE DOWN: {node}/{label} ({ip}:{port})")

    # Timer freshness
    for timer, max_age in TIMER_MAX_AGE.items():
        ok, msg = check_timer_freshness(timer, max_age)
        results["timers"].append({"name": timer, "ok": ok, "msg": msg})
        if not ok:
            alerts.append(f"TIMER STALE: {timer} — {msg}")

    # Queue depth metrics
    queue_metrics = {"pending": 0, "in_progress": 0, "last_completed": "unknown"}
    try:
        import psycopg2
        conn = psycopg2.connect(host=DB_HOST, port=5432, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
        cur = conn.cursor()
        cur.execute("SELECT status, count(*) FROM jr_work_queue WHERE status IN ('pending', 'in_progress') GROUP BY status")
        for status, count in cur.fetchall():
            queue_metrics[status] = count
        cur.execute("SELECT max(updated_at) FROM jr_work_queue WHERE status = 'completed'")
        row = cur.fetchone()
        if row and row[0]:
            queue_metrics["last_completed"] = str(row[0])[:16]
        cur.close()
        conn.close()
    except Exception:
        pass
    results["queue"] = queue_metrics

    results["alerts"] = alerts
    results["healthy"] = len(alerts) == 0
    return results


def render_html(results):
    now = results["timestamp"][:16].replace("T", " ") + " CT"
    status_color = "#4a7" if results["healthy"] else "#d44"
    status_text = "ALL CLEAR" if results["healthy"] else f"{len(results['alerts'])} ALERT(S)"

    local_html = ""
    for svc in results["local"]:
        c = "#4a7" if svc["up"] else "#d44"
        i = "&#10003;" if svc["up"] else "&#10007;"
        local_html += f'<div class="svc"><span style="color:{c}">{i}</span> {svc["name"]}</div>\n'

    remote_html = ""
    for check in results["remote"]:
        c = "#4a7" if check["up"] else "#d44"
        i = "&#10003;" if check["up"] else "&#10007;"
        remote_html += f'<div class="svc"><span style="color:{c}">{i}</span> {check["node"]}/{check["label"]} :{check["port"]}</div>\n'

    timer_html = ""
    for t in results["timers"]:
        c = "#4a7" if t["ok"] else "#d44"
        i = "&#10003;" if t["ok"] else "&#10007;"
        timer_html += f'<div class="svc"><span style="color:{c}">{i}</span> {t["name"]} — {t["msg"]}</div>\n'

    alert_html = ""
    if results["alerts"]:
        for a in results["alerts"]:
            alert_html += f'<div class="alert">{a}</div>\n'
    else:
        alert_html = '<div class="svc" style="color:#4a7">No alerts — organism healthy</div>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="120">
<title>Fire Guard</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: -apple-system, system-ui, sans-serif; background:#0a0e14; color:#c8ccd4; padding:16px; max-width:600px; margin:0 auto; }}
  h1 {{ font-size:1.3em; color:#e8b04a; margin-bottom:4px; }}
  .status {{ font-size:1.1em; font-weight:700; color:{status_color}; margin-bottom:16px; }}
  .subtitle {{ font-size:0.8em; color:#666; margin-bottom:16px; }}
  .card {{ background:#151a22; border-radius:8px; padding:12px; margin-bottom:12px; }}
  .card h2 {{ font-size:0.95em; color:#7aafff; margin-bottom:8px; }}
  .svc {{ font-size:0.82em; padding:3px 0; padding-left:8px; }}
  .alert {{ font-size:0.85em; padding:6px 8px; background:#2a1515; border-left:3px solid #d44; margin-bottom:4px; color:#f88; }}
</style>
</head>
<body>
<h1>Fire Guard</h1>
<div class="status">{status_text}</div>
<div class="subtitle">Checked: {now} &mdash; auto-refreshes every 2 min</div>

<div class="card">
  <h2>Alerts</h2>
  {alert_html}
</div>

<div class="card">
  <h2>Redfin Services</h2>
  {local_html}
</div>

<div class="card">
  <h2>Remote Nodes</h2>
  {remote_html}
</div>

<div class="card">
  <h2>Timer Health</h2>
  {timer_html}
</div>

<div style="text-align:center; margin-top:16px; font-size:0.7em; color:#444;">
  <a href="/index.html" style="color:#556; text-decoration:none;">Back to Ops Console</a>
</div>
</body>
</html>"""
    return html


def publish(html):
    import psycopg2
    content_hash = hashlib.sha256(html.encode()).hexdigest()
    conn = psycopg2.connect(host=DB_HOST, port=5432, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cur = conn.cursor()
    cur.execute("""INSERT INTO web_content (site, path, content, content_type, content_hash, published, updated_at)
        VALUES ('ganuda.us', '/fire-guard.html', %s, 'text/html', %s, true, NOW())
        ON CONFLICT (site, path) DO UPDATE SET content = %s, content_hash = %s, updated_at = NOW()""",
        (html, content_hash, html, content_hash))
    conn.commit()
    cur.close()
    conn.close()


def store_alerts(results):
    """Store alerts as thermal memories if any services are down."""
    if not results["alerts"]:
        return
    import psycopg2
    content = f"FIRE GUARD ALERT [{results['timestamp'][:16]}]: " + "; ".join(results["alerts"])
    memory_hash = hashlib.sha256(content.encode()).hexdigest()
    conn = psycopg2.connect(host=DB_HOST, port=5432, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cur = conn.cursor()
    cur.execute("""INSERT INTO thermal_memory_archive
        (original_content, temperature_score, sacred_pattern, memory_hash, domain_tag, tags, metadata)
        VALUES (%s, 85, false, %s, 'fire_guard', %s, %s::jsonb)
        ON CONFLICT (memory_hash) DO NOTHING""",
        (content, memory_hash,
         ['fire_guard', 'alert', 'health'],
         json.dumps({"source": "fire_guard", "alerts": results["alerts"]})))
    conn.commit()
    cur.close()
    conn.close()


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

    results = run_checks()
    html = render_html(results)
    publish(html)
    store_alerts(results)

    if results["healthy"]:
        print(f"Fire Guard: ALL CLEAR ({len(results['local'])} local, {len(results['remote'])} remote)")
    else:
        print(f"Fire Guard: {len(results['alerts'])} ALERT(S)")
        for a in results["alerts"]:
            print(f"  ! {a}")

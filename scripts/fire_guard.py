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
import time
from datetime import datetime

# DC-15 Refractory support
try:
    import sys
    sys.path.insert(0, '/ganuda/lib')
    from refractory_state import RefractoryManager
    _REFRACTORY_AVAILABLE = True
except ImportError:
    _REFRACTORY_AVAILABLE = False


DB_HOST = os.environ.get("CHEROKEE_DB_HOST", "192.168.132.222")
DB_NAME = os.environ.get("CHEROKEE_DB_NAME", "zammad_production")
DB_USER = os.environ.get("CHEROKEE_DB_USER", "claude")
DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")

# ── Emergency Brake (Foundation Agents GAP 7, Longhouse c4e68ce0fcea60a3) ──
BRAKE_STATE_FILE = "/ganuda/state/emergency_brake.json"
EMERGENCY_THRESHOLDS = {
    "jr_failure_rate_1h": 0.5,         # >50% Jr failures in last hour
    "thermal_write_rate_1m": 100,      # >100 thermals/minute (runaway)
    "cpu_percent": 95,                 # sustained >95% CPU
    "disk_percent": 95,                # >95% disk usage
    "postgres_connections": 90,        # >90 active connections
}
BRAKE_AUTO_DISENGAGE_MINUTES = 30
ANOMALY_WINDOW_SECONDS = 300           # 5 minutes
ANOMALY_THRESHOLD = 3                  # 3+ anomalies across different subsystems = brake

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

# Known-down state file — prevents repeated alerts for same service
KNOWN_DOWN_FILE = "/ganuda/logs/fire_guard_known_down.json"


def load_brake_state():
    """Load emergency brake state from file."""
    try:
        with open(BRAKE_STATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"brake_engaged": False, "engaged_at": None, "engaged_by": None,
                "reason": None, "auto_disengage_at": None, "history": []}


def save_brake_state(state):
    """Save emergency brake state to file."""
    os.makedirs(os.path.dirname(BRAKE_STATE_FILE), exist_ok=True)
    with open(BRAKE_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def engage_brake(reason, engaged_by="fire_guard", auto_disengage=True):
    """Engage the emergency brake. Halts new Jr task execution."""
    state = load_brake_state()
    if state["brake_engaged"]:
        return False  # already engaged
    now = datetime.now().isoformat()
    state["brake_engaged"] = True
    state["engaged_at"] = now
    state["engaged_by"] = engaged_by
    state["reason"] = reason
    if auto_disengage:
        from datetime import timedelta
        disengage_at = (datetime.now() + timedelta(minutes=BRAKE_AUTO_DISENGAGE_MINUTES)).isoformat()
        state["auto_disengage_at"] = disengage_at
    else:
        state["auto_disengage_at"] = None
    state["history"].append({
        "action": "engaged", "at": now, "by": engaged_by, "reason": reason
    })
    # Keep history bounded
    if len(state["history"]) > 100:
        state["history"] = state["history"][-100:]
    save_brake_state(state)
    print(f"  EMERGENCY BRAKE ENGAGED by {engaged_by}: {reason}")
    return True


def disengage_brake(disengaged_by="fire_guard"):
    """Disengage the emergency brake."""
    state = load_brake_state()
    if not state["brake_engaged"]:
        return False  # not engaged
    now = datetime.now().isoformat()
    state["brake_engaged"] = False
    state["engaged_at"] = None
    state["engaged_by"] = None
    state["reason"] = None
    state["auto_disengage_at"] = None
    state["history"].append({
        "action": "disengaged", "at": now, "by": disengaged_by
    })
    if len(state["history"]) > 100:
        state["history"] = state["history"][-100:]
    save_brake_state(state)
    print(f"  EMERGENCY BRAKE DISENGAGED by {disengaged_by}")
    return True


def check_auto_disengage():
    """Check if auto-disengage time has passed and conditions have resolved."""
    state = load_brake_state()
    if not state["brake_engaged"] or not state["auto_disengage_at"]:
        return
    try:
        disengage_time = datetime.fromisoformat(state["auto_disengage_at"])
        if datetime.now() >= disengage_time:
            disengage_brake("auto_disengage")
    except (ValueError, TypeError):
        pass


def check_emergency_thresholds():
    """Check all emergency thresholds. Returns list of breached thresholds."""
    breaches = []
    import psycopg2

    # CPU check
    try:
        with open('/proc/loadavg') as f:
            load_1m = float(f.read().split()[0])
        cpu_count = os.cpu_count() or 1
        cpu_pct = (load_1m / cpu_count) * 100
        if cpu_pct > EMERGENCY_THRESHOLDS["cpu_percent"]:
            breaches.append(f"CPU load {cpu_pct:.0f}% > {EMERGENCY_THRESHOLDS['cpu_percent']}%")
    except Exception:
        pass

    # Disk check
    try:
        st = os.statvfs('/')
        disk_pct = ((st.f_blocks - st.f_bfree) / st.f_blocks) * 100
        if disk_pct > EMERGENCY_THRESHOLDS["disk_percent"]:
            breaches.append(f"Disk {disk_pct:.0f}% > {EMERGENCY_THRESHOLDS['disk_percent']}%")
    except Exception:
        pass

    # DB-dependent checks
    try:
        conn = psycopg2.connect(host=DB_HOST, port=5432, dbname=DB_NAME, user=DB_USER, password=DB_PASS, connect_timeout=5)
        cur = conn.cursor()

        # Jr failure rate in last hour
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'cancelled' AND updated_at > NOW() - INTERVAL '1 hour') as failed,
                COUNT(*) FILTER (WHERE updated_at > NOW() - INTERVAL '1 hour' AND status IN ('completed', 'cancelled')) as total
            FROM jr_work_queue
        """)
        failed, total = cur.fetchone()
        if total and total > 2:
            rate = failed / total
            if rate > EMERGENCY_THRESHOLDS["jr_failure_rate_1h"]:
                breaches.append(f"Jr failure rate {rate:.0%} > {EMERGENCY_THRESHOLDS['jr_failure_rate_1h']:.0%} ({failed}/{total} in 1h)")

        # Thermal write rate (last minute)
        cur.execute("""
            SELECT COUNT(*) FROM thermal_memory_archive
            WHERE created_at > NOW() - INTERVAL '1 minute'
        """)
        thermal_rate = cur.fetchone()[0]
        if thermal_rate > EMERGENCY_THRESHOLDS["thermal_write_rate_1m"]:
            breaches.append(f"Thermal write rate {thermal_rate}/min > {EMERGENCY_THRESHOLDS['thermal_write_rate_1m']}/min")

        # Active postgres connections
        cur.execute("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
        active_conns = cur.fetchone()[0]
        if active_conns > EMERGENCY_THRESHOLDS["postgres_connections"]:
            breaches.append(f"Postgres active connections {active_conns} > {EMERGENCY_THRESHOLDS['postgres_connections']}")

        cur.close()
        conn.close()
    except Exception:
        pass  # DB down is caught elsewhere

    return breaches


def check_anomaly_cluster():
    """Coyote circuit breaker: 3+ anomalies across different subsystems in 5 min = brake.

    Uses the current run_checks results stored in the known-down file to track
    anomaly history across Fire Guard runs.
    """
    anomaly_file = "/ganuda/state/anomaly_history.json"
    now = time.time()
    try:
        with open(anomaly_file) as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        history = []

    return history, anomaly_file, now


def record_anomalies(alerts, anomaly_file, now):
    """Record current anomalies and check if cluster threshold is breached."""
    try:
        with open(anomaly_file) as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        history = []

    # Categorize alerts by subsystem
    for alert in alerts:
        subsystem = "unknown"
        if "LOCAL" in alert:
            subsystem = "local_service"
        elif "REMOTE" in alert:
            subsystem = "remote_node"
        elif "TIMER" in alert:
            subsystem = "timer"
        elif "STALE" in alert or "IDLE" in alert:
            subsystem = "executor"
        history.append({"subsystem": subsystem, "alert": alert, "at": now})

    # Prune old entries outside window
    cutoff = now - ANOMALY_WINDOW_SECONDS
    history = [h for h in history if h["at"] > cutoff]

    # Write back
    os.makedirs(os.path.dirname(anomaly_file), exist_ok=True)
    with open(anomaly_file, 'w') as f:
        json.dump(history, f)

    # Check: 3+ distinct subsystems with anomalies in window
    subsystems_hit = set(h["subsystem"] for h in history)
    if len(subsystems_hit) >= ANOMALY_THRESHOLD:
        return True, f"Coyote circuit breaker: {len(subsystems_hit)} subsystems anomalous in {ANOMALY_WINDOW_SECONDS}s ({', '.join(sorted(subsystems_hit))})"
    return False, None


def load_known_down():
    try:
        with open(KNOWN_DOWN_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_known_down(state):
    try:
        with open(KNOWN_DOWN_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass


def check_postgres_db(host, port=5432, timeout=5):
    """Check PostgreSQL by actually connecting, not just TCP socket.

    Eliminates false-positive alerts where socket check fails but DB is up.
    DC-16 Phase 1 fix.
    """
    import psycopg2
    try:
        conn = psycopg2.connect(
            host=host, port=port,
            dbname=os.environ.get("CHEROKEE_DB_NAME", DB_NAME),
            user=os.environ.get("CHEROKEE_DB_USER", DB_USER),
            password=os.environ.get("CHEROKEE_DB_PASS", DB_PASS),
            connect_timeout=timeout
        )
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return True
    except Exception:
        return False


def check_port(ip, port, timeout=3, retries=3):
    for attempt in range(retries):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((ip, port))
            s.close()
            return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            if attempt < retries - 1:
                time.sleep(1)
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
            if label == "PostgreSQL":
                up = check_postgres_db(ip, port)
            else:
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
    import argparse
    parser = argparse.ArgumentParser(description="Fire Guard — federation watchdog")
    parser.add_argument("--brake", choices=["on", "off", "status"],
                        help="Emergency brake: on=engage, off=disengage, status=report")
    parser.add_argument("--brake-reason", default="Manual engagement by Partner",
                        help="Reason for engaging brake (used with --brake on)")
    args = parser.parse_args()

    # Handle brake CLI commands immediately (no DB needed)
    if args.brake == "on":
        engage_brake(args.brake_reason, engaged_by="partner_manual", auto_disengage=False)
        print("Emergency brake ENGAGED. Jr executor will not start new tasks.")
        print("Use --brake off to release.")
        sys.exit(0)
    elif args.brake == "off":
        disengage_brake("partner_manual")
        print("Emergency brake DISENGAGED. Jr executor resuming normal operations.")
        sys.exit(0)
    elif args.brake == "status":
        state = load_brake_state()
        if state["brake_engaged"]:
            print(f"BRAKE ENGAGED since {state['engaged_at']} by {state['engaged_by']}")
            print(f"Reason: {state['reason']}")
            if state["auto_disengage_at"]:
                print(f"Auto-disengage at: {state['auto_disengage_at']}")
        else:
            print("Brake NOT engaged. Normal operations.")
        if state["history"]:
            print(f"\nLast 5 events:")
            for evt in state["history"][-5:]:
                print(f"  {evt['at']} — {evt['action']} by {evt['by']}" +
                      (f" ({evt.get('reason', '')})" if evt.get('reason') else ""))
        sys.exit(0)

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

    # DC-15: Load governance state for refractory flag
    _refractory_enabled = False
    try:
        with open('/ganuda/daemons/.governance_state.json') as _gf:
            _gstate = json.load(_gf)
            _refractory_enabled = _gstate.get('dc15_refractory_enabled', False)
    except Exception:
        pass

    _refractory = None
    if _REFRACTORY_AVAILABLE and _refractory_enabled:
        _refractory = RefractoryManager()

    # ── Emergency Brake: auto-disengage check ──
    check_auto_disengage()

    results = run_checks()

    # ── Emergency Brake: threshold checks ──
    threshold_breaches = check_emergency_thresholds()
    if threshold_breaches:
        reason = "; ".join(threshold_breaches)
        engaged = engage_brake(reason, engaged_by="threshold_auto", auto_disengage=True)
        if engaged:
            results["alerts"].append(f"EMERGENCY BRAKE ENGAGED: {reason}")

    # ── Emergency Brake: Coyote anomaly cluster ──
    if results["alerts"]:
        anomaly_triggered, anomaly_reason = record_anomalies(
            results["alerts"], "/ganuda/state/anomaly_history.json", time.time()
        )
        if anomaly_triggered:
            engaged = engage_brake(anomaly_reason, engaged_by="coyote_circuit_breaker", auto_disengage=True)
            if engaged:
                results["alerts"].append(f"COYOTE CIRCUIT BREAKER: {anomaly_reason}")

    # Known-down debounce: only alert on NEW failures and recoveries
    known_down = load_known_down()
    current_down = set(results["alerts"])
    previous_down = set(known_down.get("alerts", []))

    new_failures = current_down - previous_down
    recoveries = previous_down - current_down

    # Update known-down state
    save_known_down({
        "alerts": list(current_down),
        "since": known_down.get("since", results["timestamp"]) if current_down else None,
        "updated": results["timestamp"],
    })

    # Log recoveries
    for r in sorted(recoveries):
        print(f"  RECOVERED: {r}")

    # DC-15: Record alerts and check refractory state
    if _refractory and new_failures:
        for _ in new_failures:
            _refractory.record_alert()
        if not _refractory.should_alert():
            print(f"Fire Guard: REFRACTORY — {len(new_failures)} new alert(s) observed but suppressed")
            try:
                with open('/ganuda/logs/refractory_metrics.json', 'w') as mf:
                    json.dump(_refractory.get_metrics(), mf, indent=2)
            except Exception:
                pass
            # Still publish health page (observation), but skip alert storage
            html = render_html(results)
            publish(html)
            import sys
            sys.exit(0)

    html = render_html(results)
    publish(html)

    # Only store alerts for NEW failures (debounce)
    if new_failures:
        debounced_results = dict(results)
        debounced_results["alerts"] = sorted(new_failures)
        store_alerts(debounced_results)

    # DC-15: Write refractory metrics
    if _refractory:
        try:
            with open('/ganuda/logs/refractory_metrics.json', 'w') as mf:
                json.dump(_refractory.get_metrics(), mf, indent=2)
        except Exception:
            pass

    if results["healthy"]:
        print(f"Fire Guard: ALL CLEAR ({len(results['local'])} local, {len(results['remote'])} remote)")
        if recoveries:
            print(f"  {len(recoveries)} service(s) recovered this cycle")
    else:
        new_count = len(new_failures)
        total_count = len(results["alerts"])
        if new_failures:
            print(f"Fire Guard: {total_count} ALERT(S) ({new_count} NEW)")
            for a in sorted(new_failures):
                print(f"  ! {a}")
            if total_count > new_count:
                print(f"  ({total_count - new_count} known-down, suppressed)")
        else:
            print(f"Fire Guard: {total_count} ALERT(S) (all known-down, no new notifications)")

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

import csv
import hashlib
import json
import os
import re
import socket
import subprocess
import time
from datetime import datetime, timedelta

# DC-15 Refractory support
try:
    import sys
    sys.path.insert(0, '/ganuda/lib')
    from refractory_state import RefractoryManager
    _REFRACTORY_AVAILABLE = True
except ImportError:
    _REFRACTORY_AVAILABLE = False


DB_HOST = os.environ.get("CHEROKEE_DB_HOST", os.environ.get('CHEROKEE_DB_HOST', '10.100.0.2'))
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

# ── RSS Memory Tracking ──
RSS_HISTORY_FILE = "/ganuda/state/rss_history.csv"
RSS_GROWTH_THRESHOLD = 0.20  # 20% growth from 24h baseline triggers alert
RSS_WINDOW_HOURS = 24
RSS_REPORT_DAYS = 7

# Systemd service names to monitor for RSS
RSS_MONITORED_SERVICES = {
    "consultation-ring": "consultation-ring.service",
    "gateway": "llm-gateway.service",
    "jr-executor": "jr-se.service",
    "jr-bidding-daemon": "jr-bidding-daemon.service",
    "db-query-monitor": "db-query-monitor.service",
    "fire-guard": "fire-guard.service",
}

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
    "bluefin": [("10.100.0.2", 5432, "PostgreSQL"), ("10.100.0.2", 8090, "VLM")],
    "greenfin": [("192.168.132.224", 8003, "Embedding")],
    "owlfin": [("192.168.132.170", 80, "Caddy")],
    "eaglefin": [("192.168.132.84", 80, "Caddy")],
    "bmasass": [("100.103.27.106", 8800, "Qwen3"), ("100.103.27.106", 8801, "Llama")],
    "sasass": [("192.168.132.241", 11434, "Ollama")],
    "sasass2": [("192.168.132.242", 11434, "Ollama")],
    "redfin_consultation": [("127.0.0.1", 9400, "ConsultationRing")],
    # Camera health — Long Man Tribal Vision P-3 (MOCHA Apr 2 2026)
    "camera_office": [("192.168.132.181", 554, "Camera_RTSP")],
    "camera_traffic": [("192.168.132.182", 554, "Camera_RTSP")],
}

# Critical timers — check they fired within expected window
TIMER_MAX_AGE = {
    "federation-status.timer": 600,   # should fire every 300s, alert at 600s
}

# Known-down state file — prevents repeated alerts for same service
KNOWN_DOWN_FILE = "/ganuda/logs/fire_guard_known_down.json"

# ── Sleep Schedule: skip checks for Mac nodes during overnight hours (CT) ──
SLEEP_SCHEDULE_HOSTS = {"192.168.132.241", "192.168.132.242"}  # sasass, sasass2
QUIET_HOURS = (22, 6)  # start hour, end hour (inclusive of start, exclusive of end)


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
        conn.commit()  # explicit commit before close
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
        conn.commit()  # explicit commit before close
        conn.close()
        return True
    except Exception:
        return False


def check_ollama_health(host, port=11434, timeout=5):
    """Deep health check for Ollama API — verifies service responds, not just TCP.

    Hits /api/tags to confirm Ollama is alive and can list models.
    Returns (alive: bool, model_count: int, models: list).
    """
    import urllib.request
    import json as json_mod
    try:
        req = urllib.request.Request(f"http://{host}:{port}/api/tags")
        resp = urllib.request.urlopen(req, timeout=timeout)
        data = json_mod.loads(resp.read())
        models = [m.get("name", "?") for m in data.get("models", [])]
        return True, len(models), models
    except Exception:
        return False, 0, []


def check_consultation_ring_health(host="127.0.0.1", port=9400, timeout=5):
    """Deep health check for Consultation Ring service.

    Checks config enabled flag first — if disabled, returns status "disabled"
    without attempting connection (Turtle's kill switch).
    If enabled, hits GET /health to confirm service is alive.
    Returns (status: str, stats: dict).
      status: "disabled" | "healthy" | "down"
      stats: {"consultations_today": N, "consultations_this_hour": N} or {}
    """
    import urllib.request
    import json as json_mod
    import yaml

    # Check config enabled flag first
    try:
        with open("/ganuda/lib/harness/config.yaml") as f:
            config = yaml.safe_load(f)
        cr_config = config.get("consultation_ring", {})
        if not cr_config.get("enabled", False):
            return "disabled", {}
    except Exception:
        # If we can't read config, fall through to health check
        pass

    # Service is enabled — hit the health endpoint
    try:
        req = urllib.request.Request(f"http://{host}:{port}/health")
        resp = urllib.request.urlopen(req, timeout=timeout)
        data = json_mod.loads(resp.read())
        stats = {}
        if "consultations_today" in data:
            stats["consultations_today"] = data["consultations_today"]
        if "consultations_this_hour" in data:
            stats["consultations_this_hour"] = data["consultations_this_hour"]
        return "healthy", stats
    except Exception:
        return "down", {}


def check_port(ip, port, timeout=3, retries=3):
    # Tailscale IPs (100.x.x.x) get longer timeout — mobile nodes have variable latency
    effective_timeout = 5 if ip.startswith("100.") else timeout
    for attempt in range(retries):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(effective_timeout)
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
        conn.commit()  # explicit commit before close
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


def get_service_pid(systemd_name):
    """Get the MainPID of a systemd service. Returns int or None."""
    try:
        result = subprocess.run(
            ["systemctl", "show", systemd_name, "--property=MainPID"],
            capture_output=True, text=True, timeout=5
        )
        line = result.stdout.strip()
        if "=" in line:
            pid = int(line.split("=", 1)[1])
            return pid if pid > 0 else None
    except (subprocess.TimeoutExpired, ValueError, FileNotFoundError):
        pass
    return None


def read_rss_kb(pid):
    """Read VmRSS from /proc/<pid>/status. Returns RSS in KB or None."""
    try:
        with open(f"/proc/{pid}/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    # Format: "VmRSS:    123456 kB"
                    return int(line.split()[1])
    except (FileNotFoundError, PermissionError, IndexError, ValueError):
        pass
    return None


def load_rss_history(max_age_hours=None):
    """Load RSS history from CSV. Optionally filter to max_age_hours."""
    rows = []
    if not os.path.exists(RSS_HISTORY_FILE):
        return rows
    cutoff = None
    if max_age_hours is not None:
        cutoff = (datetime.now() - timedelta(hours=max_age_hours)).isoformat()
    try:
        with open(RSS_HISTORY_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if cutoff and row.get("timestamp", "") < cutoff:
                    continue
                rows.append(row)
    except (FileNotFoundError, csv.Error):
        pass
    return rows


def append_rss_readings(readings):
    """Append RSS readings to history CSV. Creates file with header if needed."""
    os.makedirs(os.path.dirname(RSS_HISTORY_FILE), exist_ok=True)
    write_header = not os.path.exists(RSS_HISTORY_FILE) or os.path.getsize(RSS_HISTORY_FILE) == 0
    try:
        with open(RSS_HISTORY_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(["timestamp", "service_name", "pid", "rss_kb"])
            for r in readings:
                writer.writerow([r["timestamp"], r["service_name"], r["pid"], r["rss_kb"]])
    except OSError:
        pass


def prune_rss_history(max_age_hours=168):
    """Prune RSS history older than max_age_hours (default 7 days).

    Rewrites the CSV keeping only recent entries.
    """
    rows = load_rss_history(max_age_hours=max_age_hours)
    if not rows:
        return
    try:
        with open(RSS_HISTORY_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "service_name", "pid", "rss_kb"])
            for row in rows:
                writer.writerow([row["timestamp"], row["service_name"], row["pid"], row["rss_kb"]])
    except OSError:
        pass


def check_rss_growth(current_readings):
    """Check if any service RSS has grown >20% from its 24h baseline.

    Baseline = first reading for that service+pid in the 24h window.
    Returns list of alert strings.
    """
    alerts = []
    history = load_rss_history(max_age_hours=RSS_WINDOW_HOURS)

    # Build baselines: first reading per (service, pid) in window
    baselines = {}
    for row in history:
        key = (row["service_name"], row["pid"])
        if key not in baselines:
            try:
                baselines[key] = int(row["rss_kb"])
            except (ValueError, KeyError):
                pass

    for reading in current_readings:
        key = (reading["service_name"], str(reading["pid"]))
        baseline = baselines.get(key)
        if baseline is None or baseline == 0:
            continue  # no baseline yet, skip
        current_rss = reading["rss_kb"]
        growth = (current_rss - baseline) / baseline
        if growth > RSS_GROWTH_THRESHOLD:
            growth_pct = growth * 100
            alerts.append(
                f"RSS GROWTH: {reading['service_name']} grew {growth_pct:.0f}% "
                f"({baseline} KB -> {current_rss} KB, pid {reading['pid']}) "
                f"over {RSS_WINDOW_HOURS}h window"
            )
    return alerts


def collect_rss_readings():
    """Collect current RSS readings for all monitored services.

    Returns list of dicts: {timestamp, service_name, pid, rss_kb}
    """
    readings = []
    now = datetime.now().isoformat()
    for name, systemd_unit in RSS_MONITORED_SERVICES.items():
        pid = get_service_pid(systemd_unit)
        if pid is None:
            continue
        rss_kb = read_rss_kb(pid)
        if rss_kb is None:
            continue
        readings.append({
            "timestamp": now,
            "service_name": name,
            "pid": pid,
            "rss_kb": rss_kb,
        })
    return readings


def send_rss_alert(alert_msg):
    """Send RSS growth alert via alert_manager (Slack primary, Telegram fallback)."""
    try:
        sys.path.insert(0, '/ganuda/lib')
        from alert_manager import alert_medium
        alert_medium(
            "Memory Growth Detected",
            alert_msg,
            source='fire_guard',
            alert_type='rss_growth_' + hashlib.md5(alert_msg.encode()).hexdigest()[:8]
        )
    except Exception as e:
        print(f"  RSS alert send failed: {e}")


def generate_memory_report():
    """Generate a markdown summary of RSS trends over the past 7 days.

    Compatible with owl-debt-reckoning consumption.
    """
    history = load_rss_history(max_age_hours=RSS_REPORT_DAYS * 24)
    if not history:
        return "# Fire Guard Memory Report\n\nNo RSS data available.\n"

    # Organize by service
    from collections import defaultdict
    by_service = defaultdict(list)
    for row in history:
        try:
            by_service[row["service_name"]].append({
                "timestamp": row["timestamp"],
                "pid": row["pid"],
                "rss_kb": int(row["rss_kb"]),
            })
        except (ValueError, KeyError):
            continue

    now = datetime.now()
    report_start = (now - timedelta(days=RSS_REPORT_DAYS)).strftime("%Y-%m-%d")
    report_end = now.strftime("%Y-%m-%d")

    lines = [
        f"# Fire Guard Memory Report",
        f"",
        f"Period: {report_start} to {report_end}",
        f"Generated: {now.strftime('%Y-%m-%d %H:%M')} CT",
        f"",
    ]

    if not by_service:
        lines.append("No RSS data collected during this period.")
        return "\n".join(lines) + "\n"

    lines.append("## Service RSS Summary")
    lines.append("")
    lines.append("| Service | Samples | Min (KB) | Max (KB) | Current (KB) | Growth | PIDs |")
    lines.append("|---------|---------|----------|----------|--------------|--------|------|")

    for svc in sorted(by_service.keys()):
        entries = by_service[svc]
        rss_values = [e["rss_kb"] for e in entries]
        pids_seen = sorted(set(e["pid"] for e in entries))
        min_rss = min(rss_values)
        max_rss = max(rss_values)
        first_rss = rss_values[0]
        last_rss = rss_values[-1]
        if first_rss > 0:
            growth_pct = ((last_rss - first_rss) / first_rss) * 100
            growth_str = f"{growth_pct:+.1f}%"
        else:
            growth_str = "N/A"
        pid_str = ", ".join(str(p) for p in pids_seen)
        lines.append(
            f"| {svc} | {len(entries)} | {min_rss:,} | {max_rss:,} | {last_rss:,} | {growth_str} | {pid_str} |"
        )

    lines.append("")

    # Flag services with restarts (PID changes)
    restarts = []
    for svc, entries in by_service.items():
        pids = [e["pid"] for e in entries]
        unique_pids = list(dict.fromkeys(pids))  # preserves order
        if len(unique_pids) > 1:
            restarts.append(f"- **{svc}**: {len(unique_pids)} PIDs observed ({', '.join(str(p) for p in unique_pids)})")
    if restarts:
        lines.append("## Service Restarts Detected")
        lines.append("")
        lines.extend(restarts)
        lines.append("")

    # Flag services with >20% growth
    growth_alerts = []
    for svc, entries in by_service.items():
        # Only check within same PID
        pid_groups = defaultdict(list)
        for e in entries:
            pid_groups[e["pid"]].append(e["rss_kb"])
        for pid, values in pid_groups.items():
            if len(values) < 2 or values[0] == 0:
                continue
            growth = (values[-1] - values[0]) / values[0]
            if growth > RSS_GROWTH_THRESHOLD:
                growth_alerts.append(
                    f"- **{svc}** (pid {pid}): {growth*100:.0f}% growth ({values[0]:,} KB -> {values[-1]:,} KB)"
                )
    if growth_alerts:
        lines.append("## Growth Alerts (>{:.0f}% in window)".format(RSS_GROWTH_THRESHOLD * 100))
        lines.append("")
        lines.extend(growth_alerts)
        lines.append("")

    return "\n".join(lines) + "\n"


def is_quiet_hours():
    """Check if current time (CT) is within quiet hours for sleep-scheduled hosts."""
    hour = datetime.now().hour
    start, end = QUIET_HOURS
    if start > end:
        # Wraps midnight: e.g. 22:00 - 06:00
        return hour >= start or hour < end
    else:
        return start <= hour < end


def run_checks():
    results = {"local": [], "remote": [], "timers": [], "timestamp": datetime.now().isoformat()}
    alerts = []
    quiet = is_quiet_hours()
    quiet_skipped = False

    # Local services
    for svc in LOCAL_SERVICES:
        up = check_local_service(svc)
        results["local"].append({"name": svc, "up": up})
        if not up:
            alerts.append(f"LOCAL DOWN: {svc}")

    # Remote ports
    for node, checks in REMOTE_CHECKS.items():
        for ip, port, label in checks:
            # Sleep schedule: skip Mac nodes during quiet hours
            if quiet and ip in SLEEP_SCHEDULE_HOSTS:
                if not quiet_skipped:
                    print(f"  QUIET HOURS: skipping sleep-scheduled hosts ({', '.join(sorted(SLEEP_SCHEDULE_HOSTS))})")
                    quiet_skipped = True
                results["remote"].append({"node": node, "label": label, "port": port, "up": True, "status": "sleeping"})
                continue
            if label == "PostgreSQL":
                up = check_postgres_db(ip, port)
                results["remote"].append({"node": node, "label": label, "port": port, "up": up})
                if not up:
                    alerts.append(f"REMOTE DOWN: {node}/{label} ({ip}:{port})")
            elif label == "ConsultationRing":
                status, stats = check_consultation_ring_health(ip, port)
                entry = {"node": node, "label": label, "port": port, "up": status == "healthy", "status": status}
                entry.update(stats)
                results["remote"].append(entry)
                if status == "down":
                    alerts.append(f"REMOTE DOWN: {node}/{label} ({ip}:{port})")
                # "disabled" is intentional — not an alert
            elif label == "Ollama":
                alive, model_count, models = check_ollama_health(ip, port)
                detail = f"{model_count} models loaded" if alive else "NOT RESPONDING"
                results["remote"].append({"node": node, "label": label, "port": port, "up": alive, "model_count": model_count, "models": models})
                if not alive:
                    alerts.append(f"REMOTE DOWN: {node}/{label} ({ip}:{port})")
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
        conn.commit()  # explicit commit before close
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
        extra = ""
        if check["label"] == "ConsultationRing":
            cr_status = check.get("status", "down")
            if cr_status == "disabled":
                c = "#888"
                i = "&#8212;"  # em dash for disabled
                extra = " (disabled)"
            elif cr_status == "healthy":
                stats_parts = []
                if "consultations_today" in check:
                    stats_parts.append(f"{check['consultations_today']} today")
                if "consultations_this_hour" in check:
                    stats_parts.append(f"{check['consultations_this_hour']} this hour")
                if stats_parts:
                    extra = f' ({", ".join(stats_parts)})'
        elif check["label"] == "Ollama" and check["up"] and check.get("model_count", 0) > 0:
            extra = f' ({check["model_count"]} models)'
        if check.get("status") == "sleeping":
            c = "#888"
            i = "&#9790;"  # crescent moon for sleeping
            extra = " (quiet hours)"
        remote_html += f'<div class="svc"><span style="color:{c}">{i}</span> {check["node"]}/{check["label"]} :{check["port"]}{extra}</div>\n'

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
    parser.add_argument("--memory-report", action="store_true",
                        help="Generate markdown RSS memory report (7 days) for owl-debt-reckoning")
    args = parser.parse_args()

    # Handle memory report CLI immediately
    if args.memory_report:
        report = generate_memory_report()
        print(report)
        sys.exit(0)

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

    # ── RSS Memory Tracking ──
    try:
        rss_readings = collect_rss_readings()
        if rss_readings:
            # Check for growth before appending (so current reading doesn't skew baseline)
            rss_alerts = check_rss_growth(rss_readings)
            # Append current readings to history
            append_rss_readings(rss_readings)
            # Send alerts for any RSS growth detected
            for rss_alert in rss_alerts:
                send_rss_alert(rss_alert)
                results["alerts"].append(rss_alert)
                print(f"  ! {rss_alert}")
        # Prune old data once per run (cheap — only rewrites if needed)
        prune_rss_history(max_age_hours=RSS_REPORT_DAYS * 24)
    except Exception as e:
        print(f"  RSS tracking error (non-fatal): {e}")

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

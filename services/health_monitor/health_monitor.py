#!/usr/bin/env python3
"""
Cherokee AI Distributed Health Monitor
Deploy to: /ganuda/services/health_monitor/health_monitor.py
Schedule: Every 2 minutes via cron
"""

import os
import sys
import socket
import subprocess
import requests
import psycopg2
import json
from datetime import datetime

sys.path.insert(0, '/ganuda/lib')
try:
    from alert_manager import alert_critical, alert_service_down
    HAS_ALERT_MANAGER = True
except ImportError:
    HAS_ALERT_MANAGER = False

# Database config
DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "user": "claude",
    "password": os.environ.get('CHEROKEE_DB_PASS', ''),
    "database": "zammad_production"
}

# Gateway for notifications
GATEWAY_URL = "http://192.168.132.223:8080"
API_KEY = "ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"

# Detect current node
def get_current_node():
    try:
        ips = subprocess.getoutput("hostname -I")
        if "192.168.132.223" in ips:
            return "redfin"
        elif "192.168.132.222" in ips:
            return "bluefin"
        elif "192.168.132.224" in ips:
            return "greenfin"
        elif "192.168.132.241" in ips:
            return "sasass"
        elif "192.168.132.242" in ips:
            return "sasass2"
    except:
        pass
    return socket.gethostname()

CURRENT_NODE = get_current_node()

# Service definitions
SERVICES = {
    "redfin": [
        {"name": "vLLM", "check_type": "http", "url": "http://localhost:8000/health", "restart_cmd": None, "critical": True},
        {"name": "LLM Gateway", "check_type": "http", "url": "http://localhost:8080/health",
         "restart_cmd": "cd /ganuda/services/llm_gateway && pkill -f 'uvicorn gateway:app' 2>/dev/null; sleep 2; /ganuda/services/llm_gateway/venv/bin/uvicorn gateway:app --host 0.0.0.0 --port 8080 &",
         "critical": True},
        {"name": "SAG UI", "check_type": "http", "url": "http://localhost:4000", "restart_cmd": None, "critical": True},
        {"name": "VetAssist Backend", "check_type": "http", "url": "http://localhost:8001/api/v1/health", "restart_cmd": None, "critical": True},
        {"name": "VetAssist Frontend", "check_type": "http", "url": "http://localhost:3000", "restart_cmd": None, "critical": True},
# DISABLED Dec 2025 - telegram bot now managed by systemd (derpatobot.service)
    ],
    "bluefin": [
        {"name": "PostgreSQL", "check_type": "postgres", "restart_cmd": None, "critical": True},
    ],
    "greenfin": [
        {"name": "Node Health", "check_type": "ping", "restart_cmd": None, "critical": False},
    ],
}

MAX_RESTART_ATTEMPTS = 3


def check_http(url, timeout=10):
    try:
        start = datetime.now()
        resp = requests.get(url, timeout=timeout)
        elapsed_ms = int((datetime.now() - start).total_seconds() * 1000)
        return resp.status_code == 200, elapsed_ms, None if resp.status_code == 200 else f"HTTP {resp.status_code}"
    except Exception as e:
        return False, 0, str(e)[:200]


def check_process(process_name):
    try:
        result = subprocess.run(["pgrep", "-f", process_name], capture_output=True, timeout=5)
        return result.returncode == 0, 0, None if result.returncode == 0 else "Process not found"
    except Exception as e:
        return False, 0, str(e)[:200]


def check_postgres():
    try:
        start = datetime.now()
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return True, int((datetime.now() - start).total_seconds() * 1000), None
    except Exception as e:
        return False, 0, str(e)[:200]


def check_service(service):
    check_type = service.get("check_type", "http")
    if check_type == "http":
        return check_http(service["url"])
    elif check_type == "process":
        return check_process(service["process_name"])
    elif check_type == "postgres":
        return check_postgres()
    elif check_type == "ping":
        return True, 0, None
    return False, 0, f"Unknown check type: {check_type}"


def restart_service(service):
    restart_cmd = service.get("restart_cmd")
    if not restart_cmd:
        return False
    try:
        subprocess.Popen(restart_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except:
        return False


def update_health(node, service_name, status, response_ms, error, restarted):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO service_health (node_name, service_name, status, last_check, last_healthy, consecutive_failures, restart_attempts, error_message)
            VALUES (%s, %s, %s, NOW(), CASE WHEN %s = 'healthy' THEN NOW() ELSE NULL END,
                    CASE WHEN %s = 'healthy' THEN 0 ELSE 1 END, CASE WHEN %s THEN 1 ELSE 0 END, %s)
            ON CONFLICT (node_name, service_name) DO UPDATE SET
                status = %s, last_check = NOW(),
                last_healthy = CASE WHEN %s = 'healthy' THEN NOW() ELSE service_health.last_healthy END,
                consecutive_failures = CASE WHEN %s = 'healthy' THEN 0 ELSE service_health.consecutive_failures + 1 END,
                restart_attempts = CASE WHEN %s THEN service_health.restart_attempts + 1 ELSE service_health.restart_attempts END,
                last_restart = CASE WHEN %s THEN NOW() ELSE service_health.last_restart END,
                error_message = %s
        """, (node, service_name, status, status, status, restarted, error,
              status, status, status, restarted, restarted, error))

        cur.execute("""
            INSERT INTO health_check_log (node_name, service_name, status, response_time_ms, error_message)
            VALUES (%s, %s, %s, %s, %s)
        """, (node, service_name, status, response_ms, error))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"  DB error: {e}")


def send_alert(service_name, node, error, critical):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        priority = "P1" if critical else "P2"
        cur.execute("""
            INSERT INTO tpm_notifications (priority, category, title, message, source_system)
            VALUES (%s, 'health', %s, %s, 'health_monitor')
        """, (priority, f"Service DOWN: {service_name} on {node}", f"Error: {error}\nManual intervention required."))

        cur.execute("""
            INSERT INTO thermal_memory_archive (memory_hash, original_content, temperature_score, metadata)
            VALUES (%s, %s, 95.0, %s)
        """, (f"health-{node}-{service_name}-{datetime.now().strftime('%Y%m%d%H%M')}",
              f"ALERT: {service_name} on {node} DOWN - {error}",
              json.dumps({"type": "health_alert", "node": node, "service": service_name})))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"  Alert error: {e}")


def get_restart_attempts(node, service_name):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT restart_attempts FROM service_health WHERE node_name = %s AND service_name = %s", (node, service_name))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else 0
    except:
        return 0


def run_checks():
    print(f"[{datetime.now()}] Health check on {CURRENT_NODE}")

    services = SERVICES.get(CURRENT_NODE, [])
    if not services:
        print(f"  No services for {CURRENT_NODE}")
        return

    for svc in services:
        name = svc["name"]
        healthy, ms, error = check_service(svc)

        if healthy:
            print(f"  ✓ {name} ({ms}ms)")
            update_health(CURRENT_NODE, name, "healthy", ms, None, False)
        else:
            print(f"  ✗ {name}: {error}")
            attempts = get_restart_attempts(CURRENT_NODE, name)

            if svc.get("restart_cmd") and attempts < MAX_RESTART_ATTEMPTS:
                print(f"    Self-healing attempt {attempts + 1}/{MAX_RESTART_ATTEMPTS}")
                restarted = restart_service(svc)
                update_health(CURRENT_NODE, name, "restarting", 0, error, restarted)
            else:
                if attempts >= MAX_RESTART_ATTEMPTS or not svc.get("restart_cmd"):
                    print(f"    ⚠ Alerting TPM")
                    send_alert(name, CURRENT_NODE, error, svc.get("critical", False))
                update_health(CURRENT_NODE, name, "failed", 0, error, False)

    print(f"[{datetime.now()}] Done")


if __name__ == "__main__":
    run_checks()

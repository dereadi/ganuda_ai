# Jr Instruction: Moltbook Health Check Script

**Kanban**: #1811
**Priority**: 5
**Story Points**: 3
**use_rlm**: false
**assigned_jr**: Software Engineer Jr.

---

## Overview

Create a Python health check script for the moltbook-proxy service. The script checks service status, port responsiveness, and memory usage. When unhealthy conditions are detected, results are logged to the thermal_memory_archive table for federation awareness. Designed to run via cron every 5 minutes.

---

## Steps

### Step 1: Create the health check script

Create `/ganuda/scripts/moltbook_health_check.py`

```python
#!/usr/bin/env python3
"""
Moltbook Proxy Health Check
Kanban #1811 - Cherokee AI Federation

Checks moltbook-proxy service health and logs failures to thermal memory.

Usage:
    python3 /ganuda/scripts/moltbook_health_check.py

Cron (every 5 minutes):
    */5 * * * * /usr/bin/python3 /ganuda/scripts/moltbook_health_check.py >> /var/log/moltbook-health.log 2>&1
"""

import hashlib
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

import psycopg2

DB_HOST = "192.168.132.222"
DB_NAME = "zammad_production"
DB_USER = "claude"
MOLTBOOK_SERVICE = "moltbook-proxy.service"
MOLTBOOK_PORT = 3000
HEALTH_TIMEOUT_SECONDS = 5


def check_service_active():
    """Check if moltbook-proxy.service is active via systemctl."""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", MOLTBOOK_SERVICE],
            capture_output=True, text=True, timeout=10
        )
        status = result.stdout.strip()
        return status == "active", status
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return False, f"error: {e}"


def check_port_responds():
    """Check if the proxy port responds to an HTTP request."""
    url = f"http://localhost:{MOLTBOOK_PORT}/"
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=HEALTH_TIMEOUT_SECONDS) as resp:
            return True, resp.status
    except urllib.error.URLError as e:
        return False, f"connection failed: {e.reason}"
    except Exception as e:
        return False, f"error: {e}"


def check_memory_usage():
    """Get memory usage of the moltbook-proxy process in MB."""
    try:
        result = subprocess.run(
            ["systemctl", "show", MOLTBOOK_SERVICE, "--property=MemoryCurrent"],
            capture_output=True, text=True, timeout=10
        )
        line = result.stdout.strip()
        if "=" in line:
            value = line.split("=", 1)[1]
            if value == "[not set]" or value == "infinity":
                return None, "memory tracking not available"
            memory_bytes = int(value)
            memory_mb = memory_bytes / (1024 * 1024)
            return memory_mb, f"{memory_mb:.1f} MB"
        return None, "could not parse memory info"
    except (subprocess.TimeoutExpired, ValueError) as e:
        return None, f"error: {e}"


def log_to_thermal_memory(health_report):
    """Log unhealthy status to thermal_memory_archive."""
    db_pass = os.environ.get("CHEROKEE_DB_PASS", "")

    content = (
        f"MOLTBOOK HEALTH CHECK FAILURE at {health_report['timestamp']}\n"
        f"Service active: {health_report['service_active']} ({health_report['service_status']})\n"
        f"Port responds: {health_report['port_responds']} ({health_report['port_status']})\n"
        f"Memory: {health_report['memory_status']}\n"
    )
    memory_hash = hashlib.sha256(content.encode()).hexdigest()

    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=db_pass
        )
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO thermal_memory_archive
                (original_content, temperature_score, sacred_pattern, memory_hash, metadata, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (memory_hash) DO NOTHING
            """,
            (
                content,
                60,
                False,
                memory_hash,
                json.dumps({
                    "source": "moltbook_health_check",
                    "service": MOLTBOOK_SERVICE,
                    "health_report": health_report,
                }),
                datetime.now(timezone.utc),
            )
        )
        conn.commit()
        print(f"Logged to thermal_memory_archive (hash: {memory_hash[:12]}...)")
    except Exception as e:
        print(f"WARNING: Failed to log to DB: {e}")
    finally:
        if conn:
            conn.close()


def main():
    now = datetime.now(timezone.utc).isoformat()
    print(f"[{now}] Moltbook health check starting...")

    service_ok, service_status = check_service_active()
    port_ok, port_status = check_port_responds()
    memory_mb, memory_status = check_memory_usage()

    health_report = {
        "timestamp": now,
        "service_active": service_ok,
        "service_status": service_status,
        "port_responds": port_ok,
        "port_status": str(port_status),
        "memory_mb": memory_mb,
        "memory_status": memory_status,
    }

    is_healthy = service_ok and port_ok
    status_label = "HEALTHY" if is_healthy else "UNHEALTHY"
    print(f"  Service: {service_status}")
    print(f"  Port {MOLTBOOK_PORT}: {port_status}")
    print(f"  Memory: {memory_status}")
    print(f"  Status: {status_label}")

    if not is_healthy:
        log_to_thermal_memory(health_report)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
```

---

## Verification

1. Confirm file exists at `/ganuda/scripts/moltbook_health_check.py`
2. Validate syntax: `python3 -c "import ast; ast.parse(open('/ganuda/scripts/moltbook_health_check.py').read())"`
3. Confirm script checks: service status, port response, and memory usage
4. Confirm DB connection uses host=192.168.132.222, user=claude, dbname=zammad_production
5. Confirm thermal_memory_archive INSERT uses correct schema: original_content, temperature_score, sacred_pattern, memory_hash, metadata
6. Confirm script exits 1 on unhealthy, 0 on healthy (suitable for cron/monitoring)

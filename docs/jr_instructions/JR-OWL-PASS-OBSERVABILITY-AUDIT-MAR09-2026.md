# Jr Instruction: Owl Pass Observability Audit

## Context
Eagle Eye request from Longhouse open floor. Council voted PROCEED. Eagle Eye: "We monitor services but not our monitoring." Need a meta-audit that checks whether all monitoring components are actually running and producing fresh data.

## Task
Create an observability audit script that checks the health and freshness of every monitoring component in the federation.

## Create `/ganuda/scripts/observability_audit_owlpass.py`

```python
#!/usr/bin/env python3
"""Owl Pass Observability Audit — Monitor the monitors.

Eagle Eye: "We monitor services but not our monitoring."
Council vote PROCEED. Longhouse open floor request.

Checks every timer, daemon, and monitoring component for:
- Is it running?
- When did it last produce output?
- Is the output fresh enough?
"""
import subprocess
import json
import hashlib
from datetime import datetime, timedelta

# Monitoring components to audit
# (name, check_type, check_detail, max_age_hours)
MONITORS = [
    {
        "name": "Fire Guard Timer",
        "type": "timer",
        "unit": "fire-guard.timer",
        "service": "fire-guard.service",
        "node": "redfin",
        "ssh": None,
        "max_age_minutes": 5,  # runs every 2 min
    },
    {
        "name": "Safety Canary Timer",
        "type": "timer",
        "unit": "safety-canary.timer",
        "service": "safety-canary.service",
        "node": "redfin",
        "ssh": None,
        "max_age_hours": 25,  # runs daily 3 AM
    },
    {
        "name": "Council Dawn Mist Timer",
        "type": "timer",
        "unit": "council-dawn-mist.timer",
        "service": "council-dawn-mist.service",
        "node": "redfin",
        "ssh": None,
        "max_age_hours": 25,  # runs daily 6:15 AM
    },
    {
        "name": "Credential Scanner Timer",
        "type": "timer",
        "unit": "credential-scanner.timer",
        "service": "credential-scanner.service",
        "node": "redfin",
        "ssh": None,
        "max_age_hours": 170,  # runs weekly Sat 2 AM
    },
    {
        "name": "Owl Debt Reckoning Timer",
        "type": "timer",
        "unit": "owl-debt-reckoning.timer",
        "service": "owl-debt-reckoning.service",
        "node": "redfin",
        "ssh": None,
        "max_age_hours": 170,  # runs weekly Wed 5 AM
    },
    {
        "name": "GPU Power Monitor",
        "type": "service",
        "unit": "gpu-power-monitor.service",
        "node": "redfin",
        "ssh": None,
        "max_age_minutes": None,  # persistent service, just check running
    },
    {
        "name": "OpenObserve",
        "type": "service",
        "unit": "openobserve",
        "node": "greenfin",
        "ssh": "dereadi@10.100.0.3",
        "max_age_minutes": None,
    },
    {
        "name": "Promtail",
        "type": "port",
        "port": 9080,
        "node": "greenfin",
        "ip": "10.100.0.3",
        "max_age_minutes": None,
    },
    {
        "name": "Embedding Server",
        "type": "port",
        "port": 8003,
        "node": "greenfin",
        "ip": "10.100.0.3",
        "max_age_minutes": None,
    },
    {
        "name": "Jr Executor (Pipeline A)",
        "type": "service",
        "unit": "jr-se.service",
        "node": "redfin",
        "ssh": None,
        "max_age_minutes": None,
    },
]

# Thermal memory freshness checks
THERMAL_CHECKS = [
    {"domain_tag": "fire_guard", "name": "Fire Guard Thermals", "max_age_minutes": 5},
    {"domain_tag": "safety_canary", "name": "Safety Canary Thermals", "max_age_hours": 25},
    {"domain_tag": "dawn_mist", "name": "Dawn Mist Thermals", "max_age_hours": 25},
]


def run_cmd(cmd, timeout=15):
    """Run command, return (success, stdout, stderr)."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "TIMEOUT"


def check_timer(monitor):
    """Check if a systemd timer is active and when it last fired."""
    ssh = monitor.get("ssh")
    unit = monitor["unit"]

    if ssh:
        cmd_active = f"ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no {ssh} 'systemctl is-active {unit}'"
        cmd_last = f"ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no {ssh} 'systemctl show {monitor[\"service\"]} --property=ExecMainStartTimestamp --value'"
    else:
        cmd_active = f"systemctl is-active {unit}"
        cmd_last = f"systemctl show {monitor['service']} --property=ExecMainStartTimestamp --value"

    ok, stdout, _ = run_cmd(cmd_active)
    is_active = stdout.strip() == "active"

    ok2, last_run_str, _ = run_cmd(cmd_last)
    last_run = last_run_str.strip() if ok2 and last_run_str.strip() else None

    return {"active": is_active, "last_run": last_run}


def check_service(monitor):
    """Check if a systemd service is running."""
    ssh = monitor.get("ssh")
    unit = monitor["unit"]

    if ssh:
        cmd = f"ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no {ssh} 'systemctl is-active {unit}'"
    else:
        cmd = f"systemctl is-active {unit}"

    ok, stdout, _ = run_cmd(cmd)
    return {"active": stdout.strip() == "active"}


def check_port(monitor):
    """Check if a port is reachable."""
    ip = monitor["ip"]
    port = monitor["port"]
    cmd = f"timeout 5 bash -c 'echo > /dev/tcp/{ip}/{port}' 2>/dev/null"
    ok, _, _ = run_cmd(cmd)
    return {"reachable": ok}


def check_thermal_freshness(check, conn):
    """Check if a domain_tag has fresh entries in thermal memory."""
    cur = conn.cursor()
    cur.execute("""SELECT MAX(id), COUNT(*) FROM thermal_memory_archive
        WHERE domain_tag = %s""", (check["domain_tag"],))
    row = cur.fetchone()
    cur.close()

    if not row or not row[0]:
        return {"exists": False, "count": 0, "latest_id": None}

    return {"exists": True, "count": row[1], "latest_id": row[0]}


def main():
    print(f"=== OWL PASS OBSERVABILITY AUDIT ===")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Auditing {len(MONITORS)} monitors + {len(THERMAL_CHECKS)} thermal domains")
    print()

    results = []
    issues = []

    # Phase 1: Monitor component checks
    print("--- Monitor Components ---")
    for monitor in MONITORS:
        name = monitor["name"]
        mtype = monitor["type"]

        if mtype == "timer":
            status = check_timer(monitor)
            if not status["active"]:
                issues.append(f"TIMER DOWN: {name} on {monitor['node']}")
                print(f"  FAIL  {name}: timer not active")
            else:
                print(f"  OK    {name}: active (last: {status.get('last_run', 'unknown')})")
        elif mtype == "service":
            status = check_service(monitor)
            if not status["active"]:
                issues.append(f"SERVICE DOWN: {name} on {monitor['node']}")
                print(f"  FAIL  {name}: not running")
            else:
                print(f"  OK    {name}: running")
        elif mtype == "port":
            status = check_port(monitor)
            if not status["reachable"]:
                issues.append(f"PORT UNREACHABLE: {name} ({monitor['ip']}:{monitor['port']})")
                print(f"  FAIL  {name}: port {monitor['port']} unreachable on {monitor['ip']}")
            else:
                print(f"  OK    {name}: port {monitor['port']} reachable")

        results.append({"name": name, "type": mtype, "node": monitor.get("node"), **status})

    # Phase 2: Thermal memory freshness
    print(f"\n--- Thermal Memory Freshness ---")
    try:
        import psycopg2
        secrets = {}
        with open("/ganuda/config/secrets.env") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    secrets[k.strip()] = v.strip()

        conn = psycopg2.connect(host="192.168.132.222", port=5432, dbname="zammad_production",
                                user="claude", password=secrets.get("CHEROKEE_DB_PASS", ""))

        for check in THERMAL_CHECKS:
            status = check_thermal_freshness(check, conn)
            if not status["exists"]:
                issues.append(f"NO THERMALS: {check['name']} (domain={check['domain_tag']})")
                print(f"  FAIL  {check['name']}: no entries found")
            else:
                print(f"  OK    {check['name']}: {status['count']} entries (latest id: {status['latest_id']})")
            results.append({"name": check["name"], "type": "thermal", **status})

        # Phase 3: Database health
        print(f"\n--- Database Health ---")
        cur = conn.cursor()

        # Total thermal memories
        cur.execute("SELECT COUNT(*) FROM thermal_memory_archive")
        total_thermals = cur.fetchone()[0]
        print(f"  Thermal memories: {total_thermals}")

        # Council votes in last 24h
        cur.execute("SELECT COUNT(*) FROM council_votes WHERE COALESCE(voted_at, created_at) > NOW() - INTERVAL '24 hours'")
        recent_votes = cur.fetchone()[0]
        print(f"  Council votes (24h): {recent_votes}")

        # Jr queue state
        cur.execute("SELECT status, COUNT(*) FROM jr_work_queue GROUP BY status")
        queue_state = {row[0]: row[1] for row in cur.fetchall()}
        print(f"  Jr queue: {queue_state}")

        cur.close()
        conn.close()
    except Exception as e:
        issues.append(f"DATABASE: Cannot connect ({e})")
        print(f"  FAIL  Database connection: {e}")

    # Phase 4: Log volume check
    print(f"\n--- Log Health ---")
    ok, stdout, _ = run_cmd("du -sh /ganuda/logs/ 2>/dev/null")
    if ok:
        print(f"  Log directory size: {stdout.split()[0] if stdout else 'unknown'}")
    ok, stdout, _ = run_cmd("ls -la /ganuda/logs/*.log 2>/dev/null | wc -l")
    if ok:
        print(f"  Log files: {stdout.strip()}")

    # Summary
    print(f"\n=== AUDIT SUMMARY ===")
    ok_count = len(results) - len(issues)
    print(f"  Components checked: {len(results)}")
    print(f"  Healthy: {ok_count}")
    print(f"  Issues: {len(issues)}")
    for issue in issues:
        print(f"    - {issue}")

    # Store in thermal memory
    try:
        import psycopg2
        secrets = {}
        with open("/ganuda/config/secrets.env") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    secrets[k.strip()] = v.strip()

        content = f"OWL PASS OBSERVABILITY AUDIT: {len(results)} components checked. {ok_count} healthy, {len(issues)} issues. Run: {datetime.now().isoformat()}"
        memory_hash = hashlib.sha256(content.encode()).hexdigest()

        conn = psycopg2.connect(host="192.168.132.222", port=5432, dbname="zammad_production",
                                user="claude", password=secrets.get("CHEROKEE_DB_PASS", ""))
        cur = conn.cursor()
        cur.execute("""INSERT INTO thermal_memory_archive
            (original_content, temperature_score, sacred_pattern, memory_hash, domain_tag, tags, metadata)
            VALUES (%s, 70, false, %s, 'observability_audit', %s, %s::jsonb)
            ON CONFLICT (memory_hash) DO NOTHING""",
            (content, memory_hash,
             ["observability", "owl_pass", "eagle_eye"],
             json.dumps({"issues": issues, "ok_count": ok_count, "total": len(results)})))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"  (thermal store failed: {e})")


if __name__ == "__main__":
    main()
```

## Acceptance Criteria
- Checks all systemd timers (fire-guard, safety-canary, dawn-mist, credential-scanner, owl-debt-reckoning)
- Checks persistent services (gpu-power-monitor, openobserve, jr-se)
- Checks port reachability (promtail:9080, embedding:8003)
- Checks thermal memory freshness per domain_tag
- Reports database health (thermal count, recent votes, Jr queue state)
- Reports log directory size
- Summary with issue count and details
- Results stored in thermal memory
- Uses FreeIPA SSH for remote checks (WireGuard IPs)

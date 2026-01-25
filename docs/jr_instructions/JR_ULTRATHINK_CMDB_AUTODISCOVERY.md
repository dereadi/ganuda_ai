# Jr Ultrathink Instructions: CMDB Auto-Discovery System

**Task ID:** JR-CMDB-AUTODISCOVERY-001
**Priority:** High (P1)
**Assigned Specialist:** Gecko (Technical Integration) + Eagle Eye (Monitoring)
**Date:** 2025-12-25
**Ultrathink Analysis:** Complete

---

## ULTRATHINK ANALYSIS

### Problem Statement

We have 8 CMDB entries registered manually, but:

1. **Static Data Decay**: Entries show "status: running" but services may have crashed
2. **Coverage Gaps**: Many services not in CMDB (health monitors, cron jobs, daemons)
3. **Drift Detection**: No way to detect when CMDB disagrees with reality
4. **Manual Updates**: Humans must remember to update CMDB after changes

### Current CMDB State Analysis

```
CMDB Entries: 8
├── redfin (5): vllm, llm_gateway, sag_ui, kanban, grafana
├── bluefin (2): postgresql, redis
└── greenfin (1): promtail

Missing from CMDB (known running):
├── redfin: hive_mind_bidding, health_monitor, cherokee_monitor
├── bluefin: pheromone_decay cron, backup scripts
├── greenfin: loki, node_exporter
├── sasass: mlx inference (when active)
└── sasass2: mlx inference (when active)
```

**Gap: ~15+ services not tracked in CMDB**

### Seven Generations Impact

**Without auto-discovery:**
- CMDB becomes stale within days
- False confidence in infrastructure state
- Incident response hindered by outdated info
- Tribal knowledge of "what runs where" exists only in memory

**With auto-discovery:**
- CMDB is living documentation
- Drift detected immediately
- New services auto-registered
- Infrastructure self-documents for future generations

### Discovery Methods

| Method | What It Finds | Complexity |
|--------|---------------|------------|
| `systemctl list-units` | Systemd services | Low |
| `ss -tlnp` / `netstat` | Listening ports | Low |
| `ps aux` | Running processes | Low |
| `crontab -l` | Scheduled jobs | Low |
| Docker/Podman inspect | Containers | Medium |
| Service health endpoints | Actual availability | Medium |
| Network scan | All responding IPs | High |

### Architecture Decision

**Push vs Pull Model:**

**Option A: Pull (Central Discovery)**
- Central script SSHs to each node, discovers, updates CMDB
- Pros: Single source of truth, consistent discovery
- Cons: SSH dependency, single point of failure

**Option B: Push (Agent-based)**
- Agent on each node discovers locally, pushes to CMDB
- Pros: Resilient, real-time updates
- Cons: Agent deployment, coordination

**Option C: Hybrid**
- Lightweight agent for real-time health
- Central discovery for deep scans
- Best of both worlds

**DECISION:** Option C - Hybrid. Deploy lightweight heartbeat agent on each node, with central deep discovery running hourly.

---

## EXECUTION PLAN

### Phase 1: Node Discovery Agent

Create `/ganuda/lib/node_discovery_agent.py` to run on each Linux node:

```python
#!/usr/bin/env python3
"""
Cherokee AI Federation - Node Discovery Agent
Discovers local services and updates CMDB.
Runs via systemd timer every 5 minutes.
"""

import subprocess
import socket
import json
import psycopg2
import hashlib
from datetime import datetime
import os
import re

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

NODE_NAME = socket.gethostname()

def get_systemd_services():
    """Get all running systemd services."""
    result = subprocess.run(
        ['systemctl', 'list-units', '--type=service', '--state=running', '--no-pager', '--plain'],
        capture_output=True, text=True
    )
    services = []
    for line in result.stdout.strip().split('\n')[1:]:  # Skip header
        if line.strip():
            parts = line.split()
            if parts:
                service_name = parts[0].replace('.service', '')
                # Filter to relevant services
                if any(x in service_name.lower() for x in [
                    'cherokee', 'ganuda', 'vllm', 'llm', 'hive', 'sag',
                    'postgresql', 'redis', 'grafana', 'loki', 'promtail',
                    'node_exporter', 'kanban'
                ]):
                    services.append({
                        'name': service_name,
                        'type': 'systemd',
                        'status': 'running'
                    })
    return services

def get_listening_ports():
    """Get all listening TCP ports."""
    result = subprocess.run(
        ['ss', '-tlnp'],
        capture_output=True, text=True
    )
    ports = []
    for line in result.stdout.strip().split('\n')[1:]:
        match = re.search(r':(\d+)\s', line)
        if match:
            port = int(match.group(1))
            # Filter to interesting ports
            if port in [3000, 3001, 4000, 5000, 5432, 5555, 6379, 8000, 8080, 9090, 9100]:
                # Try to identify process
                proc_match = re.search(r'users:\(\("([^"]+)"', line)
                proc_name = proc_match.group(1) if proc_match else 'unknown'
                ports.append({
                    'port': port,
                    'process': proc_name
                })
    return ports

def get_cron_jobs():
    """Get scheduled cron jobs for dereadi user."""
    try:
        result = subprocess.run(
            ['crontab', '-l', '-u', 'dereadi'],
            capture_output=True, text=True
        )
        jobs = []
        for line in result.stdout.strip().split('\n'):
            if line.strip() and not line.startswith('#'):
                # Extract script name from cron line
                parts = line.split()
                if len(parts) >= 6:
                    command = ' '.join(parts[5:])
                    jobs.append({
                        'schedule': ' '.join(parts[:5]),
                        'command': command[:100],  # Truncate
                        'type': 'cron'
                    })
        return jobs
    except:
        return []

def check_service_health(port, path='/health'):
    """Check if a service health endpoint responds."""
    try:
        import urllib.request
        url = f'http://localhost:{port}{path}'
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.status == 200
    except:
        return False

def update_cmdb(service_name, service_type, status, port=None, path=None, extra_meta=None):
    """Update or create CMDB entry."""
    cmdb_id = f"CMDB-{service_name}-{NODE_NAME}"

    content = f"""# CMDB: {service_name} on {NODE_NAME}

**CMDB ID:** {cmdb_id}
**Type:** {service_type}
**Status:** {status}
**Last Verified:** {datetime.now().isoformat()}
**Discovery Method:** auto-discovery-agent

## Service Details
- **Node:** {NODE_NAME}
- **Port:** {port or 'N/A'}
- **Path:** {path or 'N/A'}
"""

    metadata = {
        "cmdb_type": service_type,
        "cmdb_id": cmdb_id,
        "service_name": service_name,
        "node": NODE_NAME,
        "port": port,
        "status": status,
        "path": path,
        "last_verified": datetime.now().isoformat(),
        "discovery_method": "auto-discovery-agent",
        "owner": "dereadi"
    }
    if extra_meta:
        metadata.update(extra_meta)

    memory_hash = hashlib.sha256(f"{cmdb_id}-{datetime.now().isoformat()}".encode()).hexdigest()[:16]

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Check if entry exists
        cur.execute("""
            SELECT id, metadata->>'status' as old_status
            FROM thermal_memory_archive
            WHERE 'cmdb_entry' = ANY(tags)
            AND metadata->>'cmdb_id' = %s
        """, (cmdb_id,))
        existing = cur.fetchone()

        if existing:
            old_status = existing[1]
            # Update existing entry
            cur.execute("""
                UPDATE thermal_memory_archive
                SET original_content = %s,
                    metadata = %s,
                    last_access = NOW(),
                    temperature_score = CASE
                        WHEN %s != %s THEN 0.95  -- Status change = hot
                        ELSE 0.7
                    END
                WHERE id = %s
            """, (content, json.dumps(metadata), status, old_status, existing[0]))

            # Log status change
            if old_status != status:
                print(f"STATUS CHANGE: {cmdb_id} {old_status} -> {status}")

        else:
            # Create new entry
            cur.execute("""
                INSERT INTO thermal_memory_archive
                (memory_hash, original_content, current_stage, temperature_score,
                 created_at, tags, metadata, keywords)
                VALUES (%s, %s, 'warm', 0.8, NOW(),
                        ARRAY['cmdb_entry', %s, %s], %s, %s)
                RETURNING id
            """, (
                memory_hash,
                content,
                service_type,
                NODE_NAME,
                json.dumps(metadata),
                [service_name.lower(), NODE_NAME.lower(), service_type.lower()]
            ))
            entry_id = cur.fetchone()[0]
            print(f"NEW ENTRY: {cmdb_id} (ID: {entry_id})")

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print(f"CMDB update error: {e}")
        return False

def discover_and_update():
    """Main discovery routine."""
    print(f"\n{'='*60}")
    print(f"Node Discovery Agent - {NODE_NAME}")
    print(f"Time: {datetime.now().isoformat()}")
    print('='*60)

    # Discover systemd services
    services = get_systemd_services()
    print(f"\nSystemd services found: {len(services)}")
    for svc in services:
        update_cmdb(svc['name'], 'service', svc['status'])

    # Discover listening ports
    ports = get_listening_ports()
    print(f"Listening ports found: {len(ports)}")
    for p in ports:
        # Only create entries for unmatched ports
        # (services already handled above)
        pass

    # Discover cron jobs
    crons = get_cron_jobs()
    print(f"Cron jobs found: {len(crons)}")
    for cron in crons:
        # Extract script name from command
        script_name = cron['command'].split('/')[-1].split()[0] if '/' in cron['command'] else 'cron_job'
        update_cmdb(
            f"cron_{script_name}",
            'cron',
            'scheduled',
            extra_meta={'schedule': cron['schedule'], 'command': cron['command']}
        )

    # Check health endpoints for known services
    health_checks = [
        ('llm_gateway', 8080, '/health'),
        ('vllm', 8000, '/health'),
        ('sag_ui', 4000, '/'),
        ('grafana', 3000, '/api/health'),
        ('kanban', 3001, '/'),
    ]

    for name, port, path in health_checks:
        if check_service_health(port, path):
            update_cmdb(name, 'service', 'running', port=port)
        else:
            # Check if we have an entry that says running
            pass  # Let the existing entry age out or mark degraded

    print(f"\nDiscovery complete.")

if __name__ == '__main__':
    discover_and_update()
```

### Phase 2: Systemd Timer for Agent

Create `/ganuda/systemd/node-discovery.service`:

```ini
[Unit]
Description=Cherokee AI Node Discovery Agent
After=network.target postgresql.service

[Service]
Type=oneshot
User=dereadi
ExecStart=/usr/bin/python3 /ganuda/lib/node_discovery_agent.py
StandardOutput=append:/ganuda/logs/node_discovery.log
StandardError=append:/ganuda/logs/node_discovery.log
```

Create `/ganuda/systemd/node-discovery.timer`:

```ini
[Unit]
Description=Run Node Discovery Agent every 5 minutes

[Timer]
OnBootSec=1min
OnUnitActiveSec=5min
AccuracySec=1min

[Install]
WantedBy=timers.target
```

### Phase 3: Central Deep Discovery

Create `/ganuda/scripts/federation_deep_discovery.py` to run from tpm-macbook:

```python
#!/usr/bin/env python3
"""
Cherokee AI Federation - Deep Discovery
Runs centrally, SSHs to each node for comprehensive discovery.
Scheduled hourly via cron on tpm-macbook.
"""

import subprocess
import json
import psycopg2
from datetime import datetime
import hashlib

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

FEDERATION_NODES = {
    'redfin': '192.168.132.223',
    'bluefin': '192.168.132.222',
    'greenfin': '192.168.132.224',
}

def ssh_command(host, command):
    """Execute command on remote host via SSH."""
    try:
        result = subprocess.run(
            ['ssh', '-o', 'ConnectTimeout=10', f'dereadi@{host}', command],
            capture_output=True, text=True, timeout=30
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except:
        return None

def discover_node(node_name, ip):
    """Deep discovery for a single node."""
    print(f"\n{'='*40}")
    print(f"Discovering: {node_name} ({ip})")
    print('='*40)

    discoveries = []

    # 1. Systemd services
    output = ssh_command(ip, "systemctl list-units --type=service --state=running --no-pager --plain | grep -E 'cherokee|ganuda|vllm|llm|hive|sag|postgresql|redis|grafana|loki|promtail|node_exporter|kanban'")
    if output:
        for line in output.split('\n'):
            if line.strip():
                service_name = line.split()[0].replace('.service', '')
                discoveries.append({
                    'type': 'service',
                    'name': service_name,
                    'status': 'running',
                    'node': node_name
                })

    # 2. Listening ports
    output = ssh_command(ip, "ss -tlnp 2>/dev/null | grep -E ':3000|:3001|:4000|:5432|:6379|:8000|:8080|:9090|:9100'")
    if output:
        for line in output.split('\n'):
            if ':' in line:
                # Parse port and process
                import re
                port_match = re.search(r':(\d+)\s', line)
                proc_match = re.search(r'users:\(\("([^"]+)"', line)
                if port_match:
                    discoveries.append({
                        'type': 'port',
                        'port': int(port_match.group(1)),
                        'process': proc_match.group(1) if proc_match else 'unknown',
                        'node': node_name
                    })

    # 3. Disk usage
    output = ssh_command(ip, "df -h /ganuda 2>/dev/null | tail -1")
    if output:
        parts = output.split()
        if len(parts) >= 5:
            discoveries.append({
                'type': 'storage',
                'name': 'ganuda_storage',
                'size': parts[1],
                'used': parts[2],
                'available': parts[3],
                'percent': parts[4],
                'node': node_name
            })

    # 4. Memory usage
    output = ssh_command(ip, "free -h | grep Mem")
    if output:
        parts = output.split()
        if len(parts) >= 3:
            discoveries.append({
                'type': 'resource',
                'name': 'memory',
                'total': parts[1],
                'used': parts[2],
                'node': node_name
            })

    # 5. GPU (for redfin)
    if node_name == 'redfin':
        output = ssh_command(ip, "nvidia-smi --query-gpu=name,memory.total,memory.used,utilization.gpu --format=csv,noheader 2>/dev/null")
        if output:
            parts = output.split(',')
            if len(parts) >= 4:
                discoveries.append({
                    'type': 'hardware',
                    'name': 'gpu',
                    'model': parts[0].strip(),
                    'vram_total': parts[1].strip(),
                    'vram_used': parts[2].strip(),
                    'utilization': parts[3].strip(),
                    'node': node_name
                })

    return discoveries

def update_cmdb_batch(discoveries):
    """Update CMDB with all discoveries."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    for d in discoveries:
        cmdb_id = f"CMDB-{d['name']}-{d['node']}"
        cmdb_type = d['type']
        status = d.get('status', 'discovered')

        content = f"""# CMDB: {d['name']} on {d['node']}

**CMDB ID:** {cmdb_id}
**Type:** {cmdb_type}
**Status:** {status}
**Last Verified:** {datetime.now().isoformat()}
**Discovery Method:** federation-deep-discovery

## Details
{json.dumps(d, indent=2)}
"""

        metadata = {
            "cmdb_type": cmdb_type,
            "cmdb_id": cmdb_id,
            "service_name": d['name'],
            "node": d['node'],
            "status": status,
            "last_verified": datetime.now().isoformat(),
            "discovery_method": "federation-deep-discovery",
            "details": d
        }

        memory_hash = hashlib.sha256(f"{cmdb_id}-{datetime.now().isoformat()}".encode()).hexdigest()[:16]

        # Upsert
        cur.execute("""
            SELECT id FROM thermal_memory_archive
            WHERE 'cmdb_entry' = ANY(tags)
            AND metadata->>'cmdb_id' = %s
        """, (cmdb_id,))
        existing = cur.fetchone()

        if existing:
            cur.execute("""
                UPDATE thermal_memory_archive
                SET original_content = %s,
                    metadata = %s,
                    last_access = NOW(),
                    temperature_score = 0.75
                WHERE id = %s
            """, (content, json.dumps(metadata), existing[0]))
        else:
            cur.execute("""
                INSERT INTO thermal_memory_archive
                (memory_hash, original_content, current_stage, temperature_score,
                 created_at, tags, metadata, keywords)
                VALUES (%s, %s, 'warm', 0.8, NOW(),
                        ARRAY['cmdb_entry', %s, %s], %s, %s)
            """, (
                memory_hash,
                content,
                cmdb_type,
                d['node'],
                json.dumps(metadata),
                [d['name'].lower(), d['node'].lower(), cmdb_type.lower()]
            ))

    conn.commit()
    conn.close()
    print(f"\nUpdated {len(discoveries)} CMDB entries")

def detect_drift():
    """Detect CMDB entries that may be stale."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Find entries not updated in last hour
    cur.execute("""
        SELECT metadata->>'cmdb_id',
               metadata->>'node',
               metadata->>'status',
               metadata->>'last_verified'
        FROM thermal_memory_archive
        WHERE 'cmdb_entry' = ANY(tags)
        AND (metadata->>'last_verified')::timestamp < NOW() - INTERVAL '2 hours'
        ORDER BY metadata->>'last_verified'
    """)

    stale = cur.fetchall()
    conn.close()

    if stale:
        print(f"\n{'!'*60}")
        print(f"DRIFT DETECTED: {len(stale)} stale CMDB entries")
        print('!'*60)
        for cmdb_id, node, status, verified in stale:
            print(f"  {cmdb_id}: {status} (last seen: {verified})")

    return stale

def main():
    print(f"\n{'='*60}")
    print(f"Federation Deep Discovery")
    print(f"Time: {datetime.now().isoformat()}")
    print('='*60)

    all_discoveries = []

    for node_name, ip in FEDERATION_NODES.items():
        discoveries = discover_node(node_name, ip)
        all_discoveries.extend(discoveries)
        print(f"  Found {len(discoveries)} items on {node_name}")

    if all_discoveries:
        update_cmdb_batch(all_discoveries)

    # Check for drift
    detect_drift()

    print(f"\nDeep discovery complete. Total items: {len(all_discoveries)}")

if __name__ == '__main__':
    main()
```

### Phase 4: Drift Alert Integration

Create `/ganuda/lib/cmdb_drift_alerter.py`:

```python
#!/usr/bin/env python3
"""
Alert when CMDB drift is detected.
Integrates with thermal memory for persistent alerting.
"""

import psycopg2
import json
import hashlib
from datetime import datetime

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

def check_and_alert():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Find services marked running but not verified recently
    cur.execute("""
        SELECT metadata->>'cmdb_id',
               metadata->>'node',
               metadata->>'service_name',
               metadata->>'last_verified'
        FROM thermal_memory_archive
        WHERE 'cmdb_entry' = ANY(tags)
        AND metadata->>'status' = 'running'
        AND metadata->>'cmdb_type' = 'service'
        AND (metadata->>'last_verified')::timestamp < NOW() - INTERVAL '30 minutes'
    """)

    stale_services = cur.fetchall()

    if stale_services:
        alert_content = f"""# CMDB Drift Alert

**Alert Time:** {datetime.now().isoformat()}
**Severity:** Warning

## Stale Service Entries

The following services are marked as 'running' in CMDB but haven't been verified recently:

| CMDB ID | Node | Service | Last Verified |
|---------|------|---------|---------------|
"""
        for cmdb_id, node, service, verified in stale_services:
            alert_content += f"| {cmdb_id} | {node} | {service} | {verified} |\n"

        alert_content += """
## Recommended Actions

1. Check if services are actually running: `systemctl status <service>`
2. If running, verify discovery agent is functioning
3. If not running, update CMDB status to 'stopped'
4. Investigate root cause of service failure
"""

        # Store alert in thermal memory
        memory_hash = hashlib.sha256(f"drift-alert-{datetime.now().isoformat()}".encode()).hexdigest()[:16]

        cur.execute("""
            INSERT INTO thermal_memory_archive
            (memory_hash, original_content, current_stage, temperature_score,
             created_at, tags, metadata, keywords)
            VALUES (%s, %s, 'hot', 0.95, NOW(),
                    ARRAY['alert', 'cmdb_drift', 'infrastructure'], %s,
                    ARRAY['drift', 'cmdb', 'stale', 'alert'])
            RETURNING id
        """, (
            memory_hash,
            alert_content,
            json.dumps({
                'alert_type': 'cmdb_drift',
                'stale_count': len(stale_services),
                'affected_nodes': list(set(s[1] for s in stale_services))
            })
        ))

        alert_id = cur.fetchone()[0]
        conn.commit()
        print(f"DRIFT ALERT created: Memory ID {alert_id}")
        print(f"Stale services: {len(stale_services)}")

    else:
        print("No CMDB drift detected.")

    conn.close()

if __name__ == '__main__':
    check_and_alert()
```

---

## DEPLOYMENT STEPS

### On Each Linux Node (redfin, bluefin, greenfin):

```bash
# 1. Deploy discovery agent
scp /Users/Shared/ganuda/lib/node_discovery_agent.py dereadi@NODE:/ganuda/lib/

# 2. Deploy systemd units
scp /Users/Shared/ganuda/systemd/node-discovery.* dereadi@NODE:/tmp/
ssh dereadi@NODE "sudo mv /tmp/node-discovery.* /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable --now node-discovery.timer"

# 3. Verify timer active
ssh dereadi@NODE "systemctl status node-discovery.timer"
```

### On tpm-macbook:

```bash
# 1. Deploy deep discovery script
cp /Users/Shared/ganuda/scripts/federation_deep_discovery.py /Users/Shared/ganuda/scripts/

# 2. Add to crontab
crontab -e
# Add: 0 * * * * /usr/bin/python3 /Users/Shared/ganuda/scripts/federation_deep_discovery.py >> /Users/Shared/ganuda/logs/deep_discovery.log 2>&1
```

---

## VALIDATION STEPS

```bash
# 1. Run discovery agent manually on redfin
ssh dereadi@192.168.132.223 "python3 /ganuda/lib/node_discovery_agent.py"

# 2. Check CMDB count increased
ssh dereadi@192.168.132.222 "PGPASSWORD=jawaseatlasers2 psql -h 127.0.0.1 -U claude -d zammad_production -c \"SELECT COUNT(*) FROM thermal_memory_archive WHERE 'cmdb_entry' = ANY(tags);\""

# 3. Run deep discovery from macbook
python3 /Users/Shared/ganuda/scripts/federation_deep_discovery.py

# 4. Check for drift detection
python3 /Users/Shared/ganuda/lib/cmdb_drift_alerter.py

# 5. Verify timer running
ssh dereadi@192.168.132.223 "systemctl list-timers | grep discovery"
```

---

## ACCEPTANCE CRITERIA

1. [ ] `node_discovery_agent.py` deployed to all 3 Linux nodes
2. [ ] Systemd timer running on all 3 Linux nodes
3. [ ] `federation_deep_discovery.py` deployed to tpm-macbook
4. [ ] Cron job scheduled for hourly deep discovery
5. [ ] CMDB entry count increased from 8 to 15+
6. [ ] `cmdb_drift_alerter.py` deployed and tested
7. [ ] New services auto-registered (verify with new service deploy)
8. [ ] Drift detection working (stop a service, verify alert)

---

## DEPENDENCIES

- Python 3.x with psycopg2 on all nodes
- SSH key access from tpm-macbook to all Linux nodes
- PostgreSQL access to bluefin
- sudo access for systemd unit installation

---

## ESTIMATED COMPLEXITY

High - Multiple scripts, cross-node deployment, systemd integration, alert system.

---

*For Seven Generations - Cherokee AI Federation*

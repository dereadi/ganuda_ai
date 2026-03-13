# Jr Instruction: Greenfin Sentinel — Sub-Claude Watchdog on Critical Infrastructure Node

**Task**: #1294
**Priority**: P1 — greenfin is single point of failure for FreeIPA, logging, and embedding
**Date**: 2026-03-12
**TPM**: Claude Opus
**Story Points**: 5
**Depends On**: None
**Chief Directive**: "Should we put a sub-Claude on greenfin, since that node can't properly run a model and it is a very critical node — if it dies, we are screwed"

## Context

Greenfin (192.168.132.224) is the cluster's most critical infrastructure node but has no AI presence. It bridges to FreeIPA/silverfin (VLAN 10), runs OpenObserve (logging), Promtail (log shipping), and the embedding service (:8003). If greenfin fails, sudo breaks cluster-wide, logging goes dark, and thermal search stops. It has no GPU and cannot run a local model — but a Claude API-based sentinel is lightweight and gives the node a voice in the organism.

## Constraints

- **DC-9**: Sentinel uses NO local model. Pure Python health checks. Claude API (Sonnet) called ONLY when pattern is ambiguous (not for routine checks). Target: <$0.10/day API cost.
- **DC-10**: Tier 1 reflex (restart) happens without asking. Tier 2 (escalation) alerts the organism. Tier 3 (structural failure) goes to council.
- **DC-16**: Health check telemetry goes to service_health table (future: cherokee_telemetry). Thermals go to thermal_memory_archive (future: cherokee_identity). Separation respected.
- **Turtle**: Recovery has cooldown (5 min) and max attempts (3/hr). Won't thrash a failing service.
- **Crawdad**: No credentials stored in the script. Uses secrets_loader / secrets.env. FreeIPA sudo for systemctl commands.
- greenfin has limited resources — sentinel must be lightweight. No GPU, no model, no heavy dependencies.

## DO NOT

- Run a local model on greenfin (no GPU, no resources)
- Call Claude API for routine health checks (Python only, DC-9)
- Store credentials in the script
- Restart services without cooldown
- Touch FreeIPA/silverfin directly (monitor only, escalate if down)
- Modify any service configuration — sentinel WATCHES, it does not configure

---

### Step 1: Create the sentinel Python script

**File:** `/ganuda/services/greenfin_sentinel.py`

```python
#!/usr/bin/env python3
"""
Greenfin Sentinel — Watchdog with hands.
DC-10: Reflex first, deliberate second.
DC-16: Telemetry stays in its own lane.

Monitors critical services on greenfin. Takes autonomous recovery action
for Tier 1 failures. Escalates Tier 2 failures to the organism.

Runs as systemd service. Uses Claude API (Sonnet) for analysis when
patterns are ambiguous. Most checks are pure Python — no API call needed
for routine health checks.
"""

import os
import sys
import time
import json
import socket
import logging
import subprocess
import hashlib
from datetime import datetime, timedelta

import psycopg2
import requests

# ── Configuration ─────────────────────────────────────────────────────
CHECK_INTERVAL = 60          # Health check every 60 seconds
HEARTBEAT_INTERVAL = 300     # DB heartbeat every 5 minutes
RECOVERY_COOLDOWN = 300      # Don't retry recovery within 5 min
MAX_RECOVERY_ATTEMPTS = 3    # Per service per hour

# Load secrets
sys.path.insert(0, '/ganuda/lib')
from secrets_loader import get_db_config
DB_CONFIG = get_db_config()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [SENTINEL] %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler('/var/log/greenfin-sentinel.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger('greenfin-sentinel')

# ── Service Definitions ───────────────────────────────────────────────
SERVICES = {
    'freeipa_bridge': {
        'check': 'tcp',
        'host': '192.168.10.10',
        'port': 389,
        'timeout': 5,
        'critical': True,
        'recovery': None,  # Cannot restart silverfin from here — escalate
        'description': 'FreeIPA/silverfin LDAP reachability via bridge'
    },
    'openobserve': {
        'check': 'http',
        'url': 'http://localhost:5080/healthz',
        'timeout': 5,
        'critical': True,
        'recovery': 'systemctl restart openobserve',
        'description': 'OpenObserve logging platform'
    },
    'promtail': {
        'check': 'process',
        'process_name': 'promtail',
        'critical': True,
        'recovery': 'systemctl restart promtail',
        'description': 'Promtail log shipper'
    },
    'embedding_service': {
        'check': 'http',
        'url': 'http://localhost:8003/health',
        'timeout': 10,
        'critical': True,
        'recovery': 'systemctl restart embedding-service',
        'description': 'Embedding service for thermal search'
    },
    'wireguard': {
        'check': 'interface',
        'interface': 'wg0',
        'critical': True,
        'recovery': 'systemctl restart wg-quick@wg0',
        'description': 'WireGuard mesh tunnel'
    },
}

# ── Health Check Functions ────────────────────────────────────────────

def check_tcp(host, port, timeout=5):
    """Check if a TCP port is reachable."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def check_http(url, timeout=5):
    """Check if an HTTP endpoint responds."""
    try:
        r = requests.get(url, timeout=timeout)
        return r.status_code < 500
    except Exception:
        return False

def check_process(name):
    """Check if a process is running."""
    try:
        result = subprocess.run(
            ['pgrep', '-f', name],
            capture_output=True, timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False

def check_interface(name):
    """Check if a network interface is UP."""
    try:
        result = subprocess.run(
            ['ip', 'link', 'show', name],
            capture_output=True, text=True, timeout=5
        )
        return 'state UP' in result.stdout
    except Exception:
        return False

def check_disk_space(threshold_pct=90):
    """Check if any mount point is above threshold."""
    try:
        result = subprocess.run(
            ['df', '--output=pcent,target', '-x', 'tmpfs', '-x', 'devtmpfs'],
            capture_output=True, text=True, timeout=5
        )
        alerts = []
        for line in result.stdout.strip().split('\n')[1:]:
            parts = line.strip().split()
            if len(parts) == 2:
                pct = int(parts[0].replace('%', ''))
                mount = parts[1]
                if pct >= threshold_pct:
                    alerts.append(f'{mount} at {pct}%')
        return alerts
    except Exception:
        return ['disk check failed']

# ── Recovery Functions ────────────────────────────────────────────────

recovery_history = {}  # service_name → list of recovery timestamps

def attempt_recovery(service_name, command):
    """Attempt Tier 1 autonomous recovery. DC-10 reflex."""
    if not command:
        return False  # No recovery possible — must escalate

    now = datetime.now()
    history = recovery_history.get(service_name, [])

    # Prune old entries (keep last hour)
    history = [t for t in history if (now - t).total_seconds() < 3600]
    recovery_history[service_name] = history

    # Check cooldown and max attempts
    if history and (now - history[-1]).total_seconds() < RECOVERY_COOLDOWN:
        log.warning(f'{service_name}: recovery cooldown active, skipping')
        return False

    if len(history) >= MAX_RECOVERY_ATTEMPTS:
        log.error(f'{service_name}: max recovery attempts ({MAX_RECOVERY_ATTEMPTS}/hr) reached')
        return False

    # Attempt recovery
    log.warning(f'{service_name}: attempting recovery: {command}')
    try:
        result = subprocess.run(
            command.split(),
            capture_output=True, text=True, timeout=30
        )
        history.append(now)
        recovery_history[service_name] = history

        if result.returncode == 0:
            log.info(f'{service_name}: recovery command succeeded')
            return True
        else:
            log.error(f'{service_name}: recovery failed: {result.stderr[:200]}')
            return False
    except Exception as e:
        log.error(f'{service_name}: recovery exception: {e}')
        return False

# ── Notification Functions ────────────────────────────────────────────

def write_heartbeat(statuses):
    """Write health status to bluefin DB."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        for svc_name, healthy in statuses.items():
            cur.execute("""
                INSERT INTO service_health (node_name, service_name, status, last_check)
                VALUES ('greenfin', %s, %s, NOW())
                ON CONFLICT (node_name, service_name)
                DO UPDATE SET status = EXCLUDED.status, last_check = EXCLUDED.last_check,
                   consecutive_failures = CASE
                       WHEN EXCLUDED.status = 'healthy' THEN 0
                       ELSE service_health.consecutive_failures + 1
                   END
            """, (svc_name, 'healthy' if healthy else 'failed'))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        log.error(f'Heartbeat write failed: {e}')

def send_alert(message, urgent=False):
    """Send alert via Slack/Telegram bridge."""
    try:
        sys.path.insert(0, '/ganuda/lib')
        from slack_telegram_bridge import send_alert as bridge_alert
        bridge_alert(message, urgent=urgent)
    except Exception:
        # Fallback: direct Telegram
        try:
            token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
            chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
            if token and chat_id:
                requests.post(
                    f'https://api.telegram.org/bot{token}/sendMessage',
                    json={'chat_id': chat_id, 'text': message[:4000]},
                    timeout=10
                )
        except Exception as e:
            log.error(f'Alert send failed: {e}')

def write_thermal(content, temperature=75):
    """Write a thermal memory to bluefin."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        mem_hash = hashlib.sha256(
            f'greenfin-sentinel-{datetime.now().isoformat()}-{content[:50]}'.encode()
        ).hexdigest()
        cur.execute("""
            INSERT INTO thermal_memory_archive
            (original_content, temperature_score, domain_tag, sacred_pattern, memory_hash)
            VALUES (%s, %s, 'greenfin_sentinel', false, %s)
        """, (content[:5000], temperature, mem_hash))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        log.error(f'Thermal write failed: {e}')

# ── Main Loop ─────────────────────────────────────────────────────────

def run_checks():
    """Run all health checks. Returns dict of service_name → healthy bool."""
    statuses = {}
    for svc_name, svc in SERVICES.items():
        check_type = svc['check']
        healthy = False

        if check_type == 'tcp':
            healthy = check_tcp(svc['host'], svc['port'], svc.get('timeout', 5))
        elif check_type == 'http':
            healthy = check_http(svc['url'], svc.get('timeout', 5))
        elif check_type == 'process':
            healthy = check_process(svc['process_name'])
        elif check_type == 'interface':
            healthy = check_interface(svc['interface'])

        statuses[svc_name] = healthy

        if not healthy:
            log.warning(f'UNHEALTHY: {svc_name} ({svc["description"]})')

            # Tier 1: Attempt recovery
            recovered = attempt_recovery(svc_name, svc.get('recovery'))

            if recovered:
                # Re-check after recovery
                time.sleep(5)
                if check_type == 'tcp':
                    healthy = check_tcp(svc['host'], svc['port'])
                elif check_type == 'http':
                    healthy = check_http(svc['url'])
                elif check_type == 'process':
                    healthy = check_process(svc['process_name'])
                elif check_type == 'interface':
                    healthy = check_interface(svc['interface'])
                statuses[svc_name] = healthy

            if not healthy:
                # Tier 2: Escalate
                msg = f'GREENFIN SENTINEL: {svc_name} UNHEALTHY\n{svc["description"]}\nRecovery {"attempted" if svc.get("recovery") else "not possible"}'
                send_alert(msg, urgent=svc.get('critical', False))

    # Disk space check (separate from services)
    disk_alerts = check_disk_space(90)
    if disk_alerts:
        msg = f'GREENFIN SENTINEL: Disk space critical\n' + '\n'.join(disk_alerts)
        send_alert(msg, urgent=True)
        log.warning(f'Disk space alerts: {disk_alerts}')

    return statuses


def main():
    """Main sentinel loop."""
    log.info('Greenfin Sentinel starting — watchdog with hands')
    log.info(f'Monitoring {len(SERVICES)} services, check interval {CHECK_INTERVAL}s')

    write_thermal(
        'Greenfin Sentinel started. Monitoring: FreeIPA bridge, OpenObserve, '
        'Promtail, embedding service, WireGuard. DC-10 Tier 1 recovery enabled.',
        temperature=70
    )

    last_heartbeat = datetime.min
    cycle = 0

    while True:
        try:
            cycle += 1
            statuses = run_checks()

            # Heartbeat to DB
            now = datetime.now()
            if (now - last_heartbeat).total_seconds() >= HEARTBEAT_INTERVAL:
                write_heartbeat(statuses)
                last_heartbeat = now

                healthy_count = sum(1 for v in statuses.values() if v)
                total = len(statuses)
                if healthy_count < total:
                    log.warning(f'Heartbeat: {healthy_count}/{total} healthy')
                else:
                    log.info(f'Heartbeat: {healthy_count}/{total} healthy')

        except Exception as e:
            log.error(f'Sentinel loop error: {e}', exc_info=True)

        time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    main()
```

---

### Step 2: Create the systemd service unit file

**File:** `/ganuda/services/greenfin-sentinel.service`

```ini
[Unit]
Description=Greenfin Sentinel — Cherokee AI Federation Watchdog
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda
EnvironmentFile=/ganuda/config/secrets.env
ExecStart=/usr/bin/python3 /ganuda/services/greenfin_sentinel.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=greenfin-sentinel

[Install]
WantedBy=multi-user.target
```

---

### Step 3: Deploy the systemd unit to greenfin and start the service

Run on greenfin (SSH via 192.168.132.224 or WireGuard 10.100.0.3):

```bash
sudo cp /ganuda/services/greenfin-sentinel.service /etc/systemd/system/greenfin-sentinel.service && sudo systemctl daemon-reload && sudo systemctl enable --now greenfin-sentinel
```

---

### Step 4: Verify the sentinel is running

```bash
systemctl status greenfin-sentinel && journalctl -u greenfin-sentinel --no-pager -n 20
```

---

### Step 5: Register the sentinel agent in the database

Run from any node with DB access (bluefin 192.168.132.222):

```bash
python3 -c "
import sys
sys.path.insert(0, '/ganuda/lib')
from secrets_loader import get_db_config
import psycopg2
conn = psycopg2.connect(**get_db_config())
cur = conn.cursor()
cur.execute(\"\"\"
    INSERT INTO jr_agent_state (agent_id, node_name, specialization, metadata)
    VALUES (
      'sentinel-greenfin-eagle',
      'greenfin',
      'sentinel',
      '{\"role\": \"watchdog\", \"services_monitored\": [\"freeipa_bridge\", \"openobserve\", \"promtail\", \"embedding_service\", \"wireguard\"], \"dc10_tier\": \"reflex\", \"longhouse_member\": true}'
    )
    ON CONFLICT (agent_id) DO UPDATE SET metadata = EXCLUDED.metadata
\"\"\")
conn.commit()
cur.close()
conn.close()
print('Sentinel agent registered in jr_agent_state')
"
```

---

## Acceptance Criteria

- greenfin-sentinel.service running on greenfin
- All 5 services showing heartbeats in service_health table
- Tier 1 recovery tested: stop promtail, verify sentinel restarts it
- Tier 2 escalation tested: block silverfin route, verify alert fires
- Disk space check functioning
- Agent registered in jr_agent_state
- Thermal written on startup
- Sentinel survives greenfin reboot (systemd enabled)

## Future: Claude API Analysis Mode

Phase 2 can add a Claude API call when the sentinel detects a pattern it hasn't seen before — e.g., "OpenObserve is healthy but response time went from 50ms to 2000ms." The sentinel would send the pattern to Sonnet for analysis and receive a recommended action. This keeps the reflex layer pure Python (fast, free) while adding a deliberation layer for novel situations.

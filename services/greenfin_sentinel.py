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
# JR Instruction: Telegram Anomaly Alerting

**JR ID:** JR-TELEGRAM-ANOMALY-ALERTS-JAN28-2026
**Priority:** P1
**Assigned To:** Eagle Eye Jr. + Backend Jr.
**Related:** ULTRATHINK-COUNCIL-RESEARCH-INTEGRATION-JAN28-2026

---

## Objective

Alert TPM via Telegram when strange behavior is detected on the Cherokee AI channel or infrastructure. Proactive visibility - don't wait for users to report problems.

---

## Alert Categories

| Category | Examples | Severity |
|----------|----------|----------|
| **Security** | Failed auth attempts, unusual API patterns, blocklist triggers | 🔴 High |
| **Performance** | vLLM latency spike, research timeout, Council slow response | 🟡 Medium |
| **Errors** | Service crashes, database connection failures, job failures | 🔴 High |
| **Anomaly** | Unusual message volume, repeated queries, new user surge | 🟡 Medium |
| **Threshold** | Queue depth > 10, memory usage > 90%, disk space low | 🟡 Medium |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Alert Sources                       │
├──────────┬──────────┬──────────┬──────────┬────────┤
│ Gateway  │ Research │ Council  │ Telegram │ System │
│ Logs     │ Worker   │ Votes    │ Bot      │ Metrics│
└────┬─────┴────┬─────┴────┬─────┴────┬─────┴───┬────┘
     │          │          │          │         │
     └──────────┴──────────┴──────────┴─────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │    Alert Aggregator     │
              │                         │
              │ - Deduplicate           │
              │ - Rate limit (no spam)  │
              │ - Severity filter       │
              │ - Context enrichment    │
              └───────────┬─────────────┘
                          │
                          ▼
              ┌─────────────────────────┐
              │  Telegram Alert Push    │
              │                         │
              │  Chat: TPM Channel      │
              │  Format: Structured     │
              │  Actionable: Yes        │
              └─────────────────────────┘
```

---

## Implementation

### Step 1: Create Alert Module

Create `/ganuda/lib/alert_manager.py`:

```python
"""
Alert Manager - Push anomaly alerts to Telegram.
Cherokee AI Federation - For Seven Generations
"""

import os
import time
import logging
import requests
from datetime import datetime
from typing import Optional
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = os.environ.get(
    'TELEGRAM_BOT_TOKEN',
    '7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8'
)
ALERT_CHAT_ID = os.environ.get(
    'TELEGRAM_ALERT_CHAT_ID',
    '-1003439875431'  # TPM group chat
)

# Rate limiting: alert_type -> last_sent_timestamp
_alert_cooldowns = defaultdict(float)
COOLDOWN_SECONDS = {
    'critical': 60,      # 1 min between same critical alerts
    'high': 300,         # 5 min between same high alerts
    'medium': 900,       # 15 min between same medium alerts
    'low': 3600,         # 1 hour between same low alerts
}

# Severity emojis
SEVERITY_EMOJI = {
    'critical': '🚨',
    'high': '🔴',
    'medium': '🟡',
    'low': '🔵',
    'info': 'ℹ️',
}


def send_alert(
    title: str,
    message: str,
    severity: str = 'medium',
    source: str = 'system',
    alert_type: str = None,
    context: dict = None
) -> bool:
    """
    Send alert to Telegram TPM channel.

    Args:
        title: Short alert title
        message: Alert details
        severity: critical, high, medium, low, info
        source: Which component raised the alert
        alert_type: For deduplication (e.g., 'vllm_timeout')
        context: Additional context dict

    Returns:
        True if sent, False if rate-limited or failed
    """
    alert_type = alert_type or f"{source}_{title}".lower().replace(' ', '_')

    # Check rate limit
    cooldown = COOLDOWN_SECONDS.get(severity, 300)
    last_sent = _alert_cooldowns.get(alert_type, 0)
    now = time.time()

    if now - last_sent < cooldown:
        logger.debug(f"Alert {alert_type} rate-limited")
        return False

    # Build message
    emoji = SEVERITY_EMOJI.get(severity, '⚠️')
    timestamp = datetime.now().strftime('%H:%M:%S')

    text = f"{emoji} *{title}*\n"
    text += f"_{severity.upper()} | {source} | {timestamp}_\n\n"
    text += f"{message}\n"

    if context:
        text += "\n*Context:*\n"
        for k, v in list(context.items())[:5]:
            text += f"• {k}: `{v}`\n"

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": ALERT_CHAT_ID,
                "text": text,
                "parse_mode": "Markdown"
            },
            timeout=10
        )

        if response.status_code == 200:
            _alert_cooldowns[alert_type] = now
            logger.info(f"Alert sent: {title}")
            return True
        else:
            logger.error(f"Alert failed: {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"Alert exception: {e}")
        return False


# Convenience functions for common alerts
def alert_critical(title: str, message: str, source: str = 'system', **kwargs):
    return send_alert(title, message, 'critical', source, **kwargs)

def alert_high(title: str, message: str, source: str = 'system', **kwargs):
    return send_alert(title, message, 'high', source, **kwargs)

def alert_medium(title: str, message: str, source: str = 'system', **kwargs):
    return send_alert(title, message, 'medium', source, **kwargs)

def alert_low(title: str, message: str, source: str = 'system', **kwargs):
    return send_alert(title, message, 'low', source, **kwargs)


# Pre-built alert types
def alert_service_down(service_name: str, error: str = None):
    """Alert when a service goes down."""
    return alert_critical(
        f"Service Down: {service_name}",
        f"{service_name} is not responding.\n\nError: {error or 'Connection failed'}",
        source='health-check',
        alert_type=f'service_down_{service_name}'
    )

def alert_high_latency(service_name: str, latency_ms: int, threshold_ms: int):
    """Alert when latency exceeds threshold."""
    return alert_medium(
        f"High Latency: {service_name}",
        f"Response time: {latency_ms}ms (threshold: {threshold_ms}ms)",
        source='performance',
        alert_type=f'high_latency_{service_name}',
        context={'latency_ms': latency_ms, 'threshold_ms': threshold_ms}
    )

def alert_job_failed(job_type: str, job_id: str, error: str):
    """Alert when a background job fails."""
    return alert_high(
        f"Job Failed: {job_type}",
        f"Job {job_id} failed.\n\nError: {error[:200]}",
        source=job_type,
        alert_type=f'job_failed_{job_type}',
        context={'job_id': job_id}
    )

def alert_security(title: str, details: str, context: dict = None):
    """Security-related alert (always high priority)."""
    return alert_high(
        f"Security: {title}",
        details,
        source='crawdad',
        alert_type=f'security_{title.lower().replace(" ", "_")}',
        context=context
    )

def alert_anomaly(title: str, details: str, metric: str = None, value: float = None):
    """Anomaly detection alert."""
    ctx = {}
    if metric:
        ctx['metric'] = metric
    if value is not None:
        ctx['value'] = value
    return alert_medium(
        f"Anomaly: {title}",
        details,
        source='eagle-eye',
        alert_type=f'anomaly_{title.lower().replace(" ", "_")}',
        context=ctx
    )


if __name__ == "__main__":
    # Test alert
    send_alert(
        "Alert System Test",
        "This is a test alert from the alert manager.",
        severity='info',
        source='test',
        context={'test': True, 'timestamp': datetime.now().isoformat()}
    )
    print("Test alert sent!")
```

---

### Step 2: Integrate with Research Worker

Edit `/ganuda/services/research_worker.py`:

```python
# Add import
from alert_manager import alert_job_failed, alert_high_latency

# In process_job(), add failure alerting:
def process_job(...):
    start_time = time.time()

    try:
        # ... existing code ...

        # Check for high latency
        elapsed_ms = int((time.time() - start_time) * 1000)
        if elapsed_ms > 180000:  # 3 minutes
            alert_high_latency('ii-researcher', elapsed_ms, 180000)

    except Exception as e:
        fail_job(job_id, str(e))
        alert_job_failed('research', job_id, str(e))  # NEW
```

---

### Step 3: Integrate with Gateway

Edit `/ganuda/services/llm_gateway/gateway.py`:

```python
from alert_manager import alert_service_down, alert_high_latency, alert_security

# In health check or vLLM calls:
async def check_vllm_health():
    try:
        start = time.time()
        response = await client.get(f"{VLLM_URL}/health")
        latency_ms = int((time.time() - start) * 1000)

        if latency_ms > 5000:
            alert_high_latency('vLLM', latency_ms, 5000)

        return True
    except Exception as e:
        alert_service_down('vLLM', str(e))
        return False

# In API key validation:
def validate_api_key(key: str, request: Request):
    # ... existing validation ...

    if not valid:
        alert_security(
            "Invalid API Key Attempt",
            f"Failed authentication attempt from {request.client.host}",
            context={'ip': request.client.host, 'key_prefix': key[:8]}
        )
```

---

### Step 4: Integrate with Telegram Bot

Edit `/ganuda/telegram_bot/telegram_chief.py`:

```python
from alert_manager import alert_anomaly

# Track message rates for anomaly detection
message_counts = defaultdict(int)
last_count_reset = time.time()

async def handle_message(update, context):
    global last_count_reset, message_counts

    user_id = update.effective_user.id

    # Reset counts every hour
    if time.time() - last_count_reset > 3600:
        message_counts.clear()
        last_count_reset = time.time()

    message_counts[user_id] += 1

    # Alert on unusual activity
    if message_counts[user_id] == 50:  # 50 msgs/hour threshold
        alert_anomaly(
            "High Message Volume",
            f"User {user_id} sent 50+ messages in the past hour",
            metric='messages_per_hour',
            value=message_counts[user_id]
        )

    # ... rest of handler ...
```

---

### Step 5: Create Health Check Daemon

Create `/ganuda/services/health_monitor.py`:

```python
#!/usr/bin/env python3
"""
Health Monitor - Periodic health checks with Telegram alerts.
Cherokee AI Federation - For Seven Generations
"""

import time
import requests
import logging
import psycopg2

logging.basicConfig(level=logging.INFO, format='%(asctime)s [HealthMonitor] %(message)s')

import sys
sys.path.insert(0, '/ganuda/lib')
from alert_manager import alert_service_down, alert_high_latency, alert_medium

SERVICES = [
    ('vLLM', 'http://localhost:8000/health', 5000),
    ('Gateway', 'http://localhost:8080/health', 2000),
    ('ii-researcher', 'http://localhost:8090/health', 3000),
]

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

CHECK_INTERVAL = 60  # seconds


def check_service(name: str, url: str, latency_threshold_ms: int) -> bool:
    try:
        start = time.time()
        response = requests.get(url, timeout=10)
        latency_ms = int((time.time() - start) * 1000)

        if response.status_code != 200:
            alert_service_down(name, f"HTTP {response.status_code}")
            return False

        if latency_ms > latency_threshold_ms:
            alert_high_latency(name, latency_ms, latency_threshold_ms)

        return True

    except requests.exceptions.Timeout:
        alert_service_down(name, "Request timeout")
        return False
    except Exception as e:
        alert_service_down(name, str(e))
        return False


def check_database() -> bool:
    try:
        start = time.time()
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        latency_ms = int((time.time() - start) * 1000)

        if latency_ms > 1000:
            alert_high_latency('PostgreSQL', latency_ms, 1000)

        return True
    except Exception as e:
        alert_service_down('PostgreSQL', str(e))
        return False


def check_queue_depth() -> bool:
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM research_jobs WHERE status = 'pending'")
        pending = cur.fetchone()[0]
        cur.close()
        conn.close()

        if pending > 10:
            alert_medium(
                "Research Queue Backup",
                f"{pending} research jobs pending",
                source='eagle-eye',
                context={'pending_jobs': pending}
            )
            return False

        return True
    except:
        return True  # Don't alert on check failure


def main():
    logging.info("Health Monitor starting...")
    logging.info(f"Check interval: {CHECK_INTERVAL}s")

    while True:
        for name, url, threshold in SERVICES:
            check_service(name, url, threshold)

        check_database()
        check_queue_depth()

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
```

---

### Step 6: Systemd Service for Health Monitor

Create `/etc/systemd/system/health-monitor.service`:

```ini
[Unit]
Description=Cherokee Health Monitor
After=network.target

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/services
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
Environment=PYTHONPATH=/ganuda/lib
Environment=TELEGRAM_BOT_TOKEN=7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8
ExecStart=/home/dereadi/cherokee_venv/bin/python -u /ganuda/services/health_monitor.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo cp health-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now health-monitor
```

---

## Testing

### Test 1: Manual Alert
```bash
cd /ganuda/lib
python alert_manager.py
```
Should send test alert to Telegram.

### Test 2: Service Down Simulation
```bash
# Stop vLLM temporarily
sudo systemctl stop vllm

# Wait 60 seconds for health check
# Should receive "Service Down: vLLM" alert

# Restart
sudo systemctl start vllm
```

### Test 3: High Latency
Add artificial delay to a service, verify latency alert fires.

---

## Alert Examples

**Service Down:**
```
🚨 *Service Down: vLLM*
_CRITICAL | health-check | 20:15:32_

vLLM is not responding.

Error: Connection refused

*Context:*
• service: vLLM
• url: http://localhost:8000/health
```

**Security Alert:**
```
🔴 *Security: Invalid API Key Attempt*
_HIGH | crawdad | 20:18:45_

Failed authentication attempt from 192.168.1.100

*Context:*
• ip: 192.168.1.100
• key_prefix: badkey12
```

**Anomaly:**
```
🟡 *Anomaly: High Message Volume*
_MEDIUM | eagle-eye | 20:22:10_

User 12345678 sent 50+ messages in the past hour

*Context:*
• metric: messages_per_hour
• value: 52
```

---

## Files Summary

| File | Action |
|------|--------|
| `/ganuda/lib/alert_manager.py` | CREATE |
| `/ganuda/services/health_monitor.py` | CREATE |
| `/ganuda/services/research_worker.py` | MODIFY |
| `/ganuda/services/llm_gateway/gateway.py` | MODIFY |
| `/ganuda/telegram_bot/telegram_chief.py` | MODIFY |
| `/etc/systemd/system/health-monitor.service` | CREATE |

---

FOR SEVEN GENERATIONS

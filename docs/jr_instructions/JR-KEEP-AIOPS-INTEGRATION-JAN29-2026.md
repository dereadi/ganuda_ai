# JR Instruction: Keep AIOps Self-Healing Integration

**JR ID:** JR-KEEP-AIOPS-INTEGRATION-JAN29-2026
**Priority:** P0 - CRITICAL
**Assigned To:** Infrastructure Jr.
**Related:** ULTRATHINK-CLUSTER-INFRA-ENHANCEMENT-JAN29-2026
**Council Vote:** 7-0 APPROVE

---

## Objective

Deploy Keep AIOps platform for automated alert management and self-healing infrastructure actions.

---

## Problem

- Manual intervention required for service restarts
- No automated Jr task retries
- Alert fatigue from uncorrelated notifications

---

## Solution

Keep provides:
- Unified alert dashboard
- YAML workflows for automation ("GitHub Actions for monitoring")
- 100+ integrations including Prometheus, Grafana, Telegram
- Self-healing remediation actions

---

## Implementation

### Step 1: Deploy Keep via Docker

On bluefin (192.168.132.222):

```bash
# Create Keep database
sudo -u postgres psql -c "CREATE DATABASE keep;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE keep TO claude;"

# Create Keep directories
mkdir -p /ganuda/config/keep/workflows
mkdir -p /ganuda/data/keep

# Deploy Keep
docker run -d \
  --name keep \
  --restart unless-stopped \
  -p 3001:3000 \
  -e DATABASE_CONNECTION_STRING="postgresql://claude:jawaseatlasers2@localhost/keep" \
  -e SECRET_MANAGER_DIRECTORY="/keep/secrets" \
  -e KEEP_PROVIDERS="telegram,prometheus,webhook" \
  -v /ganuda/config/keep:/keep/config \
  -v /ganuda/data/keep:/keep/data \
  keephq/keep:latest
```

### Step 2: Create Telegram Provider Config

Create `/ganuda/config/keep/providers/telegram.yaml`:

```yaml
id: telegram-cherokee
type: telegram
config:
  bot_token: "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
  default_chat_id: "-1003439875431"
```

### Step 3: Create Self-Healing Workflows

**Workflow 1: Auto-Restart Crashed Services**

Create `/ganuda/config/keep/workflows/service-restart.yaml`:

```yaml
workflow:
  id: auto-restart-service
  description: Automatically restart crashed Cherokee AI services
  disabled: false

  triggers:
    - type: alert
      filters:
        - key: alertname
          value: ServiceDown
        - key: severity
          value: critical

  steps:
    - name: log-incident
      provider:
        type: console
        with:
          message: "Service {{ alert.labels.service }} down on {{ alert.labels.host }}"

    - name: restart-service
      provider:
        type: ssh
        config:
          host: "{{ alert.labels.host }}"
          username: dereadi
          key_file: /home/dereadi/.ssh/id_rsa
        with:
          command: "sudo systemctl restart {{ alert.labels.service }}"

    - name: wait-for-recovery
      provider:
        type: mock
        with:
          seconds: 30

    - name: verify-service
      provider:
        type: ssh
        config:
          host: "{{ alert.labels.host }}"
          username: dereadi
        with:
          command: "systemctl is-active {{ alert.labels.service }}"

    - name: notify-tpm
      provider:
        type: telegram
        with:
          chat_id: "-1003439875431"
          message: |
            🔧 *Auto-Remediation Complete*

            Service: `{{ alert.labels.service }}`
            Host: `{{ alert.labels.host }}`
            Action: Restarted
            Status: {{ steps.verify-service.results.stdout }}
```

**Workflow 2: Jr Task Retry**

Create `/ganuda/config/keep/workflows/jr-task-retry.yaml`:

```yaml
workflow:
  id: jr-task-retry
  description: Retry failed Jr tasks that may succeed on second attempt
  disabled: false

  triggers:
    - type: alert
      filters:
        - key: alertname
          value: JrTaskFailed
        - key: retryable
          value: "true"

  steps:
    - name: retry-task
      provider:
        type: webhook
        with:
          url: "http://localhost:8080/api/jr/retry"
          method: POST
          body:
            task_id: "{{ alert.labels.task_id }}"

    - name: notify
      provider:
        type: telegram
        with:
          message: "🔄 Retrying Jr task {{ alert.labels.task_id }}"
```

**Workflow 3: High Memory Alert**

Create `/ganuda/config/keep/workflows/memory-alert.yaml`:

```yaml
workflow:
  id: high-memory-cleanup
  description: Alert and optionally cleanup on high memory usage
  disabled: false

  triggers:
    - type: alert
      filters:
        - key: alertname
          value: HighMemoryUsage

  steps:
    - name: get-top-processes
      provider:
        type: ssh
        config:
          host: "{{ alert.labels.host }}"
        with:
          command: "ps aux --sort=-%mem | head -10"

    - name: notify-with-context
      provider:
        type: telegram
        with:
          message: |
            ⚠️ *High Memory on {{ alert.labels.host }}*

            Usage: {{ alert.labels.value }}%

            Top Processes:
            ```
            {{ steps.get-top-processes.results.stdout }}
            ```
```

### Step 4: Connect health_monitor.py to Keep

Edit `/ganuda/services/health_monitor.py` to send alerts to Keep:

```python
KEEP_WEBHOOK_URL = "http://localhost:3001/api/alerts"

def send_to_keep(alert: dict):
    """Send alert to Keep for processing."""
    try:
        requests.post(
            KEEP_WEBHOOK_URL,
            json=alert,
            timeout=5
        )
    except Exception as e:
        logging.error(f"Failed to send to Keep: {e}")

# In check_service(), add:
if not healthy:
    send_to_keep({
        "alertname": "ServiceDown",
        "severity": "critical",
        "service": service_name,
        "host": "redfin",
        "message": f"{service_name} is not responding"
    })
```

### Step 5: Create Systemd Service

Create `/etc/systemd/system/keep.service`:

```ini
[Unit]
Description=Keep AIOps Platform
After=docker.service
Requires=docker.service

[Service]
Type=simple
Restart=always
RestartSec=10
ExecStart=/usr/bin/docker start -a keep
ExecStop=/usr/bin/docker stop keep

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable keep
```

---

## Testing

1. Access Keep UI:
   ```
   http://192.168.132.222:3001
   ```

2. Trigger test alert:
   ```bash
   curl -X POST http://localhost:3001/api/alerts \
     -H "Content-Type: application/json" \
     -d '{"alertname": "TestAlert", "severity": "info", "message": "Test"}'
   ```

3. Simulate service down:
   ```bash
   sudo systemctl stop research-worker
   # Wait for health check
   # Should auto-restart and notify
   ```

---

## Files Summary

| File | Action |
|------|--------|
| `/ganuda/config/keep/providers/telegram.yaml` | CREATE |
| `/ganuda/config/keep/workflows/service-restart.yaml` | CREATE |
| `/ganuda/config/keep/workflows/jr-task-retry.yaml` | CREATE |
| `/ganuda/config/keep/workflows/memory-alert.yaml` | CREATE |
| `/ganuda/services/health_monitor.py` | MODIFY - send to Keep |
| `/etc/systemd/system/keep.service` | CREATE |

---

## Keep UI Access

- URL: http://192.168.132.222:3001
- Default credentials: Set on first login

---

FOR SEVEN GENERATIONS

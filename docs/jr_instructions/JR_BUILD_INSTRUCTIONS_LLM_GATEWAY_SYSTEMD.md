# Jr Build Instructions: LLM Gateway Systemd Service

**Priority**: HIGH  
**Phase**: 3 - Hardening & Packaging  
**Assigned To**: Gecko Jr (Technical Integration)  
**Date**: December 13, 2025

## Objective

Convert the LLM Gateway from manual startup to a proper systemd service for:
- Automatic startup on boot
- Automatic restart on failure
- Proper logging via journald
- Clean shutdown handling
- Resource limits and security hardening

## Current State

- **Location**: `/ganuda/services/llm_gateway/gateway.py`
- **Version**: v1.3.0
- **Port**: 8080
- **Current Run Method**: Manual uvicorn from cherokee_venv
- **Dependencies**: FastAPI, uvicorn, httpx, psycopg2

## Implementation Steps

### Step 1: Create Service File

```bash
ssh dereadi@192.168.132.223 "sudo tee /etc/systemd/system/llm-gateway.service << 'SERVICEEOF'
[Unit]
Description=Cherokee AI LLM Gateway v1.3
Documentation=https://github.com/dereadi/llm-gateway
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/services/llm_gateway
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
Environment=PYTHONPATH=/ganuda/services/llm_gateway:/ganuda/services/notifications
ExecStart=/home/dereadi/cherokee_venv/bin/python -m uvicorn gateway:app --host 0.0.0.0 --port 8080 --workers 2
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=llm-gateway

# Security hardening
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/ganuda /tmp /var/log
PrivateTmp=yes

# Resource limits
MemoryMax=4G
CPUQuota=200%

[Install]
WantedBy=multi-user.target
SERVICEEOF"
```

### Step 2: Stop Current Manual Process

```bash
# Find and stop current process
ssh dereadi@192.168.132.223 "pkill -f 'uvicorn gateway:app.*8080' || echo 'No process to kill'"

# Verify stopped
ssh dereadi@192.168.132.223 "pgrep -f 'gateway.*8080' || echo 'Gateway stopped'"
```

### Step 3: Enable and Start Service

```bash
ssh dereadi@192.168.132.223 "sudo systemctl daemon-reload && \
  sudo systemctl enable llm-gateway.service && \
  sudo systemctl start llm-gateway.service && \
  sudo systemctl status llm-gateway.service"
```

### Step 4: Verify Service

```bash
# Check service status
ssh dereadi@192.168.132.223 "sudo systemctl status llm-gateway"

# Check health endpoint
ssh dereadi@192.168.132.223 "curl -s http://localhost:8080/health | jq"

# Check logs
ssh dereadi@192.168.132.223 "sudo journalctl -u llm-gateway -n 20"
```

### Step 5: Test Auto-Restart

```bash
# Kill the process - systemd should restart it
ssh dereadi@192.168.132.223 "sudo pkill -f 'uvicorn gateway:app'"

# Wait 10 seconds
sleep 10

# Verify it restarted
ssh dereadi@192.168.132.223 "sudo systemctl status llm-gateway --no-pager"
```

## Service Management Commands

```bash
# Start
sudo systemctl start llm-gateway

# Stop
sudo systemctl stop llm-gateway

# Restart
sudo systemctl restart llm-gateway

# Reload config (graceful)
sudo systemctl reload llm-gateway

# View logs (follow)
sudo journalctl -u llm-gateway -f

# View logs (last hour)
sudo journalctl -u llm-gateway --since "1 hour ago"

# Check status
sudo systemctl status llm-gateway
```

## Rollback Procedure

If service fails to start:

```bash
# Disable service
sudo systemctl disable llm-gateway
sudo systemctl stop llm-gateway

# Revert to manual
cd /ganuda/services/llm_gateway
source /home/dereadi/cherokee_venv/bin/activate
nohup uvicorn gateway:app --host 0.0.0.0 --port 8080 > /tmp/llm_gateway.log 2>&1 &

# Check logs for errors
sudo journalctl -u llm-gateway -n 50 --no-pager
```

## Log Rotation

Journald handles log rotation automatically. To configure retention:

```bash
# Edit /etc/systemd/journald.conf
sudo tee -a /etc/systemd/journald.conf << 'JOURNALEOF'
# Cherokee AI LLM Gateway log retention
SystemMaxUse=2G
SystemMaxFileSize=100M
MaxRetentionSec=30day
JOURNALEOF

# Restart journald
sudo systemctl restart systemd-journald
```

## Monitoring Integration

Add to Grafana/Prometheus:

```yaml
# prometheus.yml scrape config
- job_name: 'llm-gateway'
  static_configs:
    - targets: ['192.168.132.223:8080']
  metrics_path: '/metrics'  # If metrics endpoint exists
```

## Success Criteria

- [ ] Service file created at `/etc/systemd/system/llm-gateway.service`
- [ ] Service enabled (starts on boot)
- [ ] Service running and healthy
- [ ] Auto-restart working (kill test passes)
- [ ] Logs visible in journald
- [ ] Health endpoint responding
- [ ] CMDB updated with service status

## Post-Deployment

Update thermal memory:

```sql
INSERT INTO thermal_memory_archive (memory_hash, original_content, current_stage, temperature_score, sacred_pattern)
VALUES (
    'LLM-GATEWAY-SYSTEMD-DEPLOYED',
    'LLM Gateway v1.3 deployed as systemd service on redfin. Auto-start on boot, auto-restart on failure. Security hardened with NoNewPrivileges, ProtectSystem, MemoryMax=4G.',
    'FRESH',
    96.0,
    true
);
```

---

FOR SEVEN GENERATIONS - Production services ensure continuity.

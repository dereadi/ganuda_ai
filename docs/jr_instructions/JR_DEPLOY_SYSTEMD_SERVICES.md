# Jr Instruction: Deploy All Systemd Services

**Priority**: P1 (Phase 3 Critical)
**Phase**: 3 - Hardening & Packaging
**Assigned To**: Gecko Jr (Technical Integration)
**Date**: December 23, 2025
**Status**: READY FOR EXECUTION

---

## Mission

Deploy systemd services for ALL Cherokee AI Federation core services on redfin. This enables:
- Automatic startup on boot
- Automatic restart on failure
- Proper logging via journald
- Clean shutdown handling
- Resource limits and security hardening

---

## Current State

| Service | Port | Current Run Method | systemd Status |
|---------|------|-------------------|----------------|
| vLLM (Nemotron-9B) | 8000 | Manual nohup | NOT DEPLOYED |
| LLM Gateway v1.3 | 8080 | Manual nohup | NOT DEPLOYED |
| Jr Bidding Daemon | - | Manual nohup | NOT DEPLOYED |
| Jr Task Executor | - | Manual nohup | NOT DEPLOYED |
| Telegram Chief Bot | - | Manual nohup | NOT DEPLOYED |

---

## Service Files to Create

### Service 1: vLLM (Port 8000)

**File**: `/etc/systemd/system/vllm.service`

```ini
[Unit]
Description=Cherokee AI vLLM Server (Nemotron-9B)
Documentation=https://docs.vllm.ai
After=network.target
Wants=network.target

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/home/dereadi
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
Environment=CUDA_VISIBLE_DEVICES=0
ExecStart=/home/dereadi/cherokee_venv/bin/python -m vllm.entrypoints.openai.api_server \
    --model nvidia/NVIDIA-Nemotron-Nano-9B-v2 \
    --port 8000 \
    --gpu-memory-utilization 0.60 \
    --trust-remote-code
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=vllm

# Resource limits
MemoryMax=80G
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
```

### Service 2: LLM Gateway (Port 8080)

**File**: `/etc/systemd/system/llm-gateway.service`

```ini
[Unit]
Description=Cherokee AI LLM Gateway v1.3
Documentation=https://github.com/dereadi/ganuda-federation
After=network.target vllm.service postgresql.service
Wants=vllm.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/services/llm_gateway
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
Environment=PYTHONPATH=/ganuda/services/llm_gateway:/ganuda/services/notifications:/ganuda/lib
ExecStart=/home/dereadi/cherokee_venv/bin/python -m uvicorn gateway:app --host 0.0.0.0 --port 8080 --workers 2
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=llm-gateway

# Security hardening (relaxed for compatibility)
NoNewPrivileges=yes
PrivateTmp=yes

# Resource limits
MemoryMax=4G
CPUQuota=200%

[Install]
WantedBy=multi-user.target
```

### Service 3: Jr Bidding Daemon

**File**: `/etc/systemd/system/jr-bidding.service`

```ini
[Unit]
Description=Cherokee AI Jr Bidding Daemon
After=network.target llm-gateway.service postgresql.service
Wants=llm-gateway.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/jr_executor
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
Environment=PYTHONPATH=/ganuda/lib
ExecStart=/home/dereadi/cherokee_venv/bin/python jr_bidding_daemon.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=jr-bidding

[Install]
WantedBy=multi-user.target
```

### Service 4: Jr Task Executor

**File**: `/etc/systemd/system/jr-executor.service`

```ini
[Unit]
Description=Cherokee AI Jr Task Executor
After=network.target llm-gateway.service jr-bidding.service
Wants=jr-bidding.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/jr_executor
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
Environment=PYTHONPATH=/ganuda/lib
ExecStart=/home/dereadi/cherokee_venv/bin/python jr_task_executor.py --agent-id jr-redfin-gecko
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=jr-executor

[Install]
WantedBy=multi-user.target
```

### Service 5: Telegram Chief Bot

**File**: `/etc/systemd/system/telegram-chief.service`

```ini
[Unit]
Description=Cherokee AI Telegram Chief Bot
After=network.target llm-gateway.service
Wants=llm-gateway.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/services/telegram_chief
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
Environment=PYTHONPATH=/ganuda/lib
ExecStart=/home/dereadi/cherokee_venv/bin/python telegram_chief.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=telegram-chief

[Install]
WantedBy=multi-user.target
```

---

## Deployment Script

Create and run this script on redfin:

```bash
#!/bin/bash
# Cherokee AI Federation - Systemd Deployment Script
# Date: December 23, 2025

set -e

echo "=== Cherokee AI Systemd Deployment ==="
echo "Date: $(date)"
echo ""

# Step 1: Create service files
echo "[1/6] Creating vLLM service file..."
sudo tee /etc/systemd/system/vllm.service << 'EOF'
[Unit]
Description=Cherokee AI vLLM Server (Nemotron-9B)
After=network.target

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/home/dereadi
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
Environment=CUDA_VISIBLE_DEVICES=0
ExecStart=/home/dereadi/cherokee_venv/bin/python -m vllm.entrypoints.openai.api_server --model nvidia/NVIDIA-Nemotron-Nano-9B-v2 --port 8000 --gpu-memory-utilization 0.60 --trust-remote-code
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=vllm
MemoryMax=80G
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF

echo "[2/6] Creating LLM Gateway service file..."
sudo tee /etc/systemd/system/llm-gateway.service << 'EOF'
[Unit]
Description=Cherokee AI LLM Gateway v1.3
After=network.target vllm.service
Wants=vllm.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/services/llm_gateway
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
Environment=PYTHONPATH=/ganuda/services/llm_gateway:/ganuda/services/notifications:/ganuda/lib
ExecStart=/home/dereadi/cherokee_venv/bin/python -m uvicorn gateway:app --host 0.0.0.0 --port 8080 --workers 2
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=llm-gateway
NoNewPrivileges=yes
PrivateTmp=yes
MemoryMax=4G
CPUQuota=200%

[Install]
WantedBy=multi-user.target
EOF

echo "[3/6] Creating Jr Bidding service file..."
sudo tee /etc/systemd/system/jr-bidding.service << 'EOF'
[Unit]
Description=Cherokee AI Jr Bidding Daemon
After=network.target llm-gateway.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/jr_executor
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
Environment=PYTHONPATH=/ganuda/lib
ExecStart=/home/dereadi/cherokee_venv/bin/python jr_bidding_daemon.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=jr-bidding

[Install]
WantedBy=multi-user.target
EOF

echo "[4/6] Creating Jr Executor service file..."
sudo tee /etc/systemd/system/jr-executor.service << 'EOF'
[Unit]
Description=Cherokee AI Jr Task Executor
After=network.target llm-gateway.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/jr_executor
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
Environment=PYTHONPATH=/ganuda/lib
ExecStart=/home/dereadi/cherokee_venv/bin/python jr_task_executor.py --agent-id jr-redfin-gecko
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=jr-executor

[Install]
WantedBy=multi-user.target
EOF

echo "[5/6] Creating Telegram Chief service file..."
sudo tee /etc/systemd/system/telegram-chief.service << 'EOF'
[Unit]
Description=Cherokee AI Telegram Chief Bot
After=network.target llm-gateway.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/services/telegram_chief
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
Environment=PYTHONPATH=/ganuda/lib
ExecStart=/home/dereadi/cherokee_venv/bin/python telegram_chief.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=telegram-chief

[Install]
WantedBy=multi-user.target
EOF

echo "[6/6] Reloading systemd..."
sudo systemctl daemon-reload

echo ""
echo "=== Service files created ==="
echo "Review with: ls -la /etc/systemd/system/{vllm,llm-gateway,jr-*,telegram-*}.service"
echo ""
echo "To deploy (will stop current processes):"
echo "  1. Stop manual processes:"
echo "     pkill -f 'vllm.entrypoints'"
echo "     pkill -f 'uvicorn gateway:app'"
echo "     pkill -f 'jr_bidding_daemon'"
echo "     pkill -f 'jr_task_executor'"
echo "     pkill -f 'telegram_chief'"
echo ""
echo "  2. Enable and start services:"
echo "     sudo systemctl enable --now vllm"
echo "     sudo systemctl enable --now llm-gateway"
echo "     sudo systemctl enable --now jr-bidding"
echo "     sudo systemctl enable --now jr-executor"
echo "     sudo systemctl enable --now telegram-chief"
echo ""
echo "  3. Check status:"
echo "     sudo systemctl status vllm llm-gateway jr-bidding jr-executor telegram-chief"
```

---

## Execution Order

**CRITICAL**: Execute in this order to avoid breaking running services:

### Phase A: Create Service Files (Non-Disruptive)
```bash
# SSH to redfin and create the deployment script
ssh dereadi@192.168.132.223 "cat > /ganuda/scripts/deploy_systemd.sh << 'SCRIPT'
# [paste deployment script here]
SCRIPT
chmod +x /ganuda/scripts/deploy_systemd.sh"

# Run the script to create service files only
ssh dereadi@192.168.132.223 "/ganuda/scripts/deploy_systemd.sh"
```

### Phase B: Verify Service Files
```bash
# Check all service files exist
ssh dereadi@192.168.132.223 "ls -la /etc/systemd/system/{vllm,llm-gateway,jr-*,telegram-*}.service"

# Validate syntax
ssh dereadi@192.168.132.223 "sudo systemd-analyze verify /etc/systemd/system/vllm.service 2>&1 | head -5"
```

### Phase C: Stop Manual & Start Systemd (During Maintenance Window)
```bash
# 1. Stop ALL manual processes
ssh dereadi@192.168.132.223 "pkill -f 'vllm.entrypoints' || true"
ssh dereadi@192.168.132.223 "pkill -f 'uvicorn gateway:app' || true"
ssh dereadi@192.168.132.223 "pkill -f 'jr_bidding_daemon' || true"
ssh dereadi@192.168.132.223 "pkill -f 'jr_task_executor' || true"
ssh dereadi@192.168.132.223 "pkill -f 'telegram_chief' || true"

# 2. Wait for processes to stop
sleep 5

# 3. Enable and start in dependency order
ssh dereadi@192.168.132.223 "sudo systemctl enable --now vllm"
sleep 30  # vLLM needs time to load model
ssh dereadi@192.168.132.223 "sudo systemctl enable --now llm-gateway"
sleep 5
ssh dereadi@192.168.132.223 "sudo systemctl enable --now jr-bidding"
ssh dereadi@192.168.132.223 "sudo systemctl enable --now jr-executor"
ssh dereadi@192.168.132.223 "sudo systemctl enable --now telegram-chief"

# 4. Verify all running
ssh dereadi@192.168.132.223 "sudo systemctl status vllm llm-gateway jr-bidding jr-executor telegram-chief --no-pager"
```

---

## Verification Checklist

```bash
# Check each service is running
ssh dereadi@192.168.132.223 "sudo systemctl is-active vllm llm-gateway jr-bidding jr-executor telegram-chief"

# Check health endpoints
ssh dereadi@192.168.132.223 "curl -s http://localhost:8080/health | jq -r '.status'"

# Check logs
ssh dereadi@192.168.132.223 "sudo journalctl -u llm-gateway -n 5 --no-pager"

# Test auto-restart
ssh dereadi@192.168.132.223 "sudo pkill -f 'uvicorn gateway:app'; sleep 10; curl -s http://localhost:8080/health"
```

---

## Service Management Quick Reference

```bash
# View all Cherokee services
sudo systemctl list-units 'vllm*' 'llm-gateway*' 'jr-*' 'telegram-*'

# View logs (real-time)
sudo journalctl -f -u vllm -u llm-gateway -u jr-bidding -u jr-executor -u telegram-chief

# Restart all services
sudo systemctl restart vllm llm-gateway jr-bidding jr-executor telegram-chief

# Stop all services (maintenance)
sudo systemctl stop telegram-chief jr-executor jr-bidding llm-gateway vllm

# Start all services (post-maintenance)
sudo systemctl start vllm && sleep 30 && sudo systemctl start llm-gateway jr-bidding jr-executor telegram-chief
```

---

## Rollback Procedure

If systemd services fail:

```bash
# 1. Stop all services
sudo systemctl stop telegram-chief jr-executor jr-bidding llm-gateway vllm

# 2. Disable services
sudo systemctl disable telegram-chief jr-executor jr-bidding llm-gateway vllm

# 3. Start manual processes
cd /home/dereadi
nohup /home/dereadi/cherokee_venv/bin/python -m vllm.entrypoints.openai.api_server \
    --model nvidia/NVIDIA-Nemotron-Nano-9B-v2 --port 8000 \
    --gpu-memory-utilization 0.60 --trust-remote-code > /home/dereadi/logs/vllm.log 2>&1 &

cd /ganuda/services/llm_gateway
nohup /home/dereadi/cherokee_venv/bin/python -m uvicorn gateway:app \
    --host 0.0.0.0 --port 8080 > /home/dereadi/logs/gateway.log 2>&1 &

# Jr services and Telegram can restart manually as needed
```

---

## Post-Deployment

### Update Thermal Memory

```sql
INSERT INTO thermal_memory_archive (memory_hash, original_content, temperature_score, metadata)
VALUES (
    'systemd-services-deployed-20251223',
    'SYSTEMD SERVICES DEPLOYED - Dec 23, 2025

5 Cherokee AI services converted from manual nohup to systemd:
1. vllm.service - Nemotron-9B inference (port 8000)
2. llm-gateway.service - API Gateway (port 8080)
3. jr-bidding.service - Jr agent bidding daemon
4. jr-executor.service - Jr task executor
5. telegram-chief.service - Telegram bot

All services configured for:
- Auto-start on boot
- Auto-restart on failure
- Logging via journald
- Proper dependency ordering

Service management: systemctl {start|stop|restart|status} <service>
Logs: journalctl -u <service>

Phase 3 Hardening: COMPLETE',
    95.0,
    '{"type": "deployment", "phase": 3, "services": 5, "node": "redfin"}'::jsonb
);
```

### Update CMDB

```sql
UPDATE hardware_inventory
SET notes = notes || E'\n[2025-12-23] Systemd services deployed: vllm, llm-gateway, jr-bidding, jr-executor, telegram-chief'
WHERE hostname = 'redfin';
```

---

## Success Criteria

- [ ] All 5 service files created in /etc/systemd/system/
- [ ] daemon-reload completed successfully
- [ ] All services enabled (starts on boot)
- [ ] All services running and healthy
- [ ] Auto-restart test passes (kill & verify restart)
- [ ] Health endpoints responding
- [ ] Logs visible in journald
- [ ] Thermal memory updated
- [ ] CMDB updated

---

## Seven Generations Consideration

Converting to systemd services ensures the Cherokee AI Federation survives:
- Reboots (planned and unplanned)
- Process crashes (auto-restart)
- Operator absence (self-healing)

Production infrastructure that runs itself.

For Seven Generations.

---

*Phase 3: Hardening & Packaging*
*Task: Systemd Services Deployment*
*Target Node: redfin (192.168.132.223)*

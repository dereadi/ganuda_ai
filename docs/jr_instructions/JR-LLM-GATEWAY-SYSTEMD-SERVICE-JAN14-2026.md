# Jr Instructions: Deploy LLM Gateway as Systemd Service

**Task ID**: GATEWAY-SYSTEMD-001
**Priority**: HIGH (P1)
**Date**: January 14, 2026
**Target Node**: redfin (192.168.132.223)
**Assigned To**: TPM (manual sudo required)
**Reason**: Gateway needs auto-start/restart, depends on vLLM

---

## Problem Statement

LLM Gateway (port 8080) currently runs via `nohup` - if the system reboots, it stays dead.

The Gateway is the single entry point for all inference - Jrs, Council votes, SAG UI all depend on it.

---

## Solution

Deploy Gateway as a systemd service with:
- Dependency on vLLM service (`After=vllm.service`)
- Auto-start on boot
- Auto-restart on failure
- Proper logging via journald

---

## Prerequisites

- vLLM must be deployed as systemd service first (see JR-VLLM-SYSTEMD-SERVICE-JAN14-2026.md)
- Verify vllm.service is running: `systemctl is-active vllm`

---

## Step 1: Verify Gateway Location

```bash
# SSH to redfin
ssh dereadi@192.168.132.223

# Find gateway.py
ls -la /ganuda/services/llm_gateway/

# Verify venv exists
ls -la /ganuda/services/llm_gateway/venv/bin/python
```

---

## Step 2: Create Systemd Service File

```bash
sudo tee /etc/systemd/system/llm-gateway.service << 'EOF'
[Unit]
Description=Cherokee AI LLM Gateway (OpenAI-Compatible + Council)
Documentation=file:///ganuda/docs/kb/KB-LLM-GATEWAY.md
After=network.target vllm.service
Wants=vllm.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/services/llm_gateway
Environment=PATH=/ganuda/services/llm_gateway/venv/bin:/usr/bin:/bin
Environment=PYTHONPATH=/ganuda/lib:/ganuda/services/llm_gateway
ExecStart=/ganuda/services/llm_gateway/venv/bin/python gateway.py
Restart=on-failure
RestartSec=15
StandardOutput=journal
StandardError=journal
SyslogIdentifier=llm-gateway

[Install]
WantedBy=multi-user.target
EOF
```

---

## Step 3: Kill Existing Gateway Process

```bash
# Find and kill any running gateway
pkill -f "gateway.py"

# Verify
ps aux | grep gateway | grep -v grep && echo "Still running!" || echo "Clean"
```

---

## Step 4: Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable (start on boot)
sudo systemctl enable llm-gateway

# Start now
sudo systemctl start llm-gateway

# Check status
sudo systemctl status llm-gateway --no-pager
```

---

## Step 5: Verify Service

```bash
# Health check
curl -s http://localhost:8080/health

# List models (proxied from vLLM)
curl -s http://localhost:8080/v1/models | head -10

# Check Council endpoint
curl -s http://localhost:8080/v1/council/history | head -10
```

---

## Step 6: Test Auto-Restart

```bash
# Kill the process
sudo pkill -f "gateway.py"

# Wait 20 seconds (RestartSec=15 + buffer)
sleep 20

# Verify it restarted
sudo systemctl is-active llm-gateway
curl -s http://localhost:8080/health
```

---

## Service Management Commands

```bash
# View status
sudo systemctl status llm-gateway

# View logs (real-time)
sudo journalctl -u llm-gateway -f

# View logs (last 100 lines)
sudo journalctl -u llm-gateway -n 100 --no-pager

# Restart
sudo systemctl restart llm-gateway

# Stop (maintenance)
sudo systemctl stop llm-gateway
```

---

## Full Stack Restart Order

If both vLLM and Gateway are down:

```bash
# 1. Start vLLM first (takes 2-3 min for model load)
sudo systemctl start vllm
sleep 180  # Wait for model to load

# 2. Verify vLLM
curl -s http://localhost:8000/v1/models | head -5

# 3. Start Gateway
sudo systemctl start llm-gateway

# 4. Verify Gateway
curl -s http://localhost:8080/health
```

---

## Rollback Plan

If systemd service fails:

```bash
# Disable service
sudo systemctl disable llm-gateway
sudo systemctl stop llm-gateway

# Fall back to manual start
cd /ganuda/services/llm_gateway
source venv/bin/activate
nohup python gateway.py > /home/dereadi/logs/llm_gateway.log 2>&1 &
```

---

## Success Criteria

- [ ] Service file created at `/etc/systemd/system/llm-gateway.service`
- [ ] Service enabled (starts on boot)
- [ ] Service running (`systemctl is-active llm-gateway` returns "active")
- [ ] curl localhost:8080/health returns healthy
- [ ] curl localhost:8080/v1/models returns model list
- [ ] Auto-restart test passes

---

## Post-Deployment: Update Thermal Memory

```sql
INSERT INTO triad_shared_memories (content, temperature, source_triad, tags, access_level)
VALUES (
  'LLM GATEWAY SYSTEMD SERVICE DEPLOYED - January 14, 2026

Gateway is now managed by systemd:
- Service: llm-gateway.service
- Port: 8080
- Depends on: vllm.service
- Auto-start: YES (on boot, after vLLM)
- Auto-restart: YES (on failure, 15s delay)
- Logs: journalctl -u llm-gateway

STARTUP ORDER: vLLM → Gateway → IT Triad
All three are now systemd services.

Endpoints:
- /v1/chat/completions - OpenAI-compatible
- /v1/council/vote - 7-Specialist Council
- /v1/models - Model list
- /health - Health check

For Seven Generations.',
  95, 'tpm',
  ARRAY['gateway', 'systemd', 'deployment', 'january-2026'],
  'federation'
);
```

---

*For Seven Generations*

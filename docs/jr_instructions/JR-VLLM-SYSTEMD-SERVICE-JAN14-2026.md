# Jr Instructions: Deploy vLLM as Systemd Service

**Task ID**: VLLM-SYSTEMD-001
**Priority**: HIGH (P1)
**Date**: January 14, 2026
**Target Node**: redfin (192.168.132.223)
**Assigned To**: TPM (manual sudo required)
**Reason**: vLLM needs auto-start/restart to survive reboots

---

## Problem Statement

vLLM currently runs via `nohup` - if the system reboots (as happened Jan 14 for FreeIPA), it stays dead until manually restarted.

This is unacceptable for production infrastructure. All Jrs depend on vLLM through the Gateway.

---

## Solution

Deploy vLLM as a systemd service with:
- Auto-start on boot (After=network.target)
- Auto-restart on failure (Restart=on-failure)
- GPU dependency awareness
- Proper logging via journald

---

## Step 1: Find Current vLLM Configuration

```bash
# SSH to redfin
ssh dereadi@192.168.132.223

# Find the model and parameters currently in use
ps aux | grep vllm | grep -v grep

# Check existing startup script
ls -la /home/dereadi/*.sh /ganuda/scripts/start*.sh 2>/dev/null

# Check log for startup params
head -50 /home/dereadi/logs/vllm.log 2>/dev/null
```

---

## Step 2: Create Systemd Service File

```bash
sudo tee /etc/systemd/system/vllm.service << 'EOF'
[Unit]
Description=vLLM OpenAI-Compatible Inference Server
Documentation=https://docs.vllm.ai/
After=network.target

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/home/dereadi
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
Environment=HF_HOME=/home/dereadi/.cache/huggingface
ExecStart=/home/dereadi/cherokee_venv/bin/python -m vllm.entrypoints.openai.api_server \
  --model nvidia/Llama-3.1-Nemotron-Nano-8B-v2 \
  --port 8000 \
  --trust-remote-code \
  --max-model-len 65536
Restart=on-failure
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=vllm

# GPU access
SupplementaryGroups=video render

[Install]
WantedBy=multi-user.target
EOF
```

**NOTE**: Adjust `--model` parameter if using a different model. Check thermal memory or `/home/dereadi/logs/vllm.log` for the actual model path.

---

## Step 3: Kill Existing vLLM Process

```bash
# Find and kill any running vLLM
pkill -f "vllm.entrypoints"

# Verify
ps aux | grep vllm | grep -v grep && echo "Still running!" || echo "Clean"
```

---

## Step 4: Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable (start on boot)
sudo systemctl enable vllm

# Start now
sudo systemctl start vllm

# Check status (may take 2-3 min for model load)
sudo systemctl status vllm --no-pager
```

---

## Step 5: Monitor Startup

```bash
# Watch logs during model loading
sudo journalctl -u vllm -f

# Wait for "Uvicorn running on http://0.0.0.0:8000"
# Press Ctrl+C when ready

# Verify
curl -s http://localhost:8000/v1/models | head -5
nvidia-smi --query-gpu=memory.used --format=csv
```

---

## Step 6: Test Auto-Restart

```bash
# Kill the process (simulating crash)
sudo pkill -f "vllm.entrypoints"

# Wait 35 seconds (RestartSec=30 + buffer)
sleep 35

# Verify it restarted
sudo systemctl is-active vllm
curl -s http://localhost:8000/health 2>/dev/null || echo "Still loading..."
```

---

## Service Management Commands

```bash
# View status
sudo systemctl status vllm

# View logs (real-time)
sudo journalctl -u vllm -f

# View logs (last 100 lines)
sudo journalctl -u vllm -n 100 --no-pager

# Restart
sudo systemctl restart vllm

# Stop (maintenance)
sudo systemctl stop vllm

# Disable (prevent auto-start)
sudo systemctl disable vllm
```

---

## Rollback Plan

If systemd service fails:

```bash
# Disable service
sudo systemctl disable vllm
sudo systemctl stop vllm

# Fall back to manual start
cd /home/dereadi
source cherokee_venv/bin/activate
nohup python -m vllm.entrypoints.openai.api_server \
  --model nvidia/Llama-3.1-Nemotron-Nano-8B-v2 \
  --port 8000 \
  --trust-remote-code \
  > /home/dereadi/logs/vllm.log 2>&1 &
```

---

## Success Criteria

- [ ] Service file created at `/etc/systemd/system/vllm.service`
- [ ] Service enabled (starts on boot)
- [ ] Service running (`systemctl is-active vllm` returns "active")
- [ ] VRAM shows ~25-30GB used
- [ ] curl localhost:8000/v1/models returns model list
- [ ] Auto-restart test passes (kill → restart within 35s)

---

## Post-Deployment: Update Thermal Memory

```sql
INSERT INTO triad_shared_memories (content, temperature, source_triad, tags, access_level)
VALUES (
  'VLLM SYSTEMD SERVICE DEPLOYED - January 14, 2026

vLLM is now managed by systemd:
- Service: vllm.service
- Model: nvidia/Llama-3.1-Nemotron-Nano-8B-v2
- Port: 8000
- Auto-start: YES (on boot)
- Auto-restart: YES (on failure, 30s delay)
- Logs: journalctl -u vllm

This ensures inference continues even after:
- System reboots
- Process crashes
- Kernel panics

Previous issue: Jan 14 reboot for FreeIPA left cluster down.
Root cause: vLLM was nohup, not systemd.

For Seven Generations.',
  95, 'tpm',
  ARRAY['vllm', 'systemd', 'deployment', 'january-2026'],
  'federation'
);
```

---

*For Seven Generations*

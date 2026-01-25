# Jr Instructions: Restart AI Cluster on Redfin

**Task ID**: REDFIN-RESTART-001
**Priority**: P0 - CRITICAL
**Date**: January 14, 2026
**Target Node**: redfin (192.168.132.223)
**Assigned To**: TPM (manual - requires sudo)
**Reason**: AI cluster down after reboot for FreeIPA installation

---

## Problem Statement

After rebooting redfin for FreeIPA client installation (SSSD purge/reinstall), all AI services are down:
- vLLM (port 8000) - NOT RUNNING
- LLM Gateway (port 8080) - NOT RUNNING
- IT Triad daemon - systemd service exists but not started

No VRAM being used according to `nvidia-smi`.

---

## Architecture Reference

From thermal memory (Jan 13 consolidation):
- **vLLM**: Nemotron Nano 9B v2, port 8000, ~27 tok/sec, 131K context
- **Gateway**: port 8080, routes all inference, Jrs observe requests
- **IT Triad**: systemd service `it-triad.service`, polls thermal memory for missions

---

## Step 1: SSH to Redfin and Assess

```bash
# Check what's running
nvidia-smi
ps aux | grep -E "vllm|gateway|it_triad" | grep -v grep
systemctl is-active it-triad
```

---

## Step 2: Start vLLM

Find and run the vLLM startup script:

```bash
# Look for existing startup script
ls -la /home/dereadi/*.sh /ganuda/scripts/*.sh 2>/dev/null | head -20

# Or check logs for previous command
cat /home/dereadi/logs/vllm.log 2>/dev/null | head -20

# If no script exists, start manually:
cd /home/dereadi
source cherokee_venv/bin/activate

# Start vLLM with Nemotron Nano 9B v2
nohup python -m vllm.entrypoints.openai.api_server \
  --model nvidia/Llama-3.1-Nemotron-Nano-8B-v2 \
  --port 8000 \
  --trust-remote-code \
  > /home/dereadi/logs/vllm.log 2>&1 &

# Wait for model load (2-3 min for 9B model)
sleep 10
tail -f /home/dereadi/logs/vllm.log
# Press Ctrl+C when you see "Uvicorn running on..."
```

---

## Step 3: Verify vLLM

```bash
# Check port 8000
curl -s http://localhost:8000/v1/models | head -5

# Check VRAM usage (should be ~25-30GB for Nemotron)
nvidia-smi --query-gpu=memory.used,memory.total --format=csv
```

---

## Step 4: Start LLM Gateway

```bash
cd /ganuda/services/llm_gateway
source venv/bin/activate

nohup python gateway.py > /home/dereadi/logs/llm_gateway.log 2>&1 &

# Verify
sleep 3
curl -s http://localhost:8080/health
```

---

## Step 5: Restart IT Triad Daemon

```bash
# IT Triad is already a systemd service
sudo systemctl restart it-triad
sudo systemctl status it-triad --no-pager

# Check logs
sudo journalctl -u it-triad -n 20 --no-pager
```

---

## Step 6: Full Verification

```bash
# All services check
echo "=== VRAM Usage ==="
nvidia-smi --query-gpu=memory.used,memory.total --format=csv

echo "=== vLLM (port 8000) ==="
curl -s http://localhost:8000/v1/models | python3 -m json.tool | head -10

echo "=== Gateway (port 8080) ==="
curl -s http://localhost:8080/health

echo "=== IT Triad ==="
systemctl is-active it-triad

echo "=== All Processes ==="
ps aux | grep -E "vllm|gateway|it_triad" | grep -v grep
```

---

## Success Criteria

- [ ] nvidia-smi shows ~25-30GB VRAM used
- [ ] curl localhost:8000/v1/models returns model list
- [ ] curl localhost:8080/health returns healthy
- [ ] systemctl is-active it-triad returns "active"

---

## Post-Restart: Update Thermal Memory

```sql
INSERT INTO triad_shared_memories (content, temperature, source_triad, tags, access_level)
VALUES (
  'AI CLUSTER RESTARTED - January 14, 2026

After redfin reboot for FreeIPA client installation:
- vLLM: RUNNING (port 8000, Nemotron Nano 9B v2)
- Gateway: RUNNING (port 8080)
- IT Triad: RUNNING (systemd service)

VRAM: ~25-30GB used

All inference routes through Gateway API.

For Seven Generations.',
  90, 'tpm',
  ARRAY['redfin', 'restart', 'vllm', 'gateway', 'january-2026'],
  'federation'
);
```

---

## FUTURE ACTION: Create Systemd Services

To prevent manual restarts after reboots, we need systemd services for:
1. vLLM (vllm.service)
2. LLM Gateway (llm-gateway.service)

See: JR-VLLM-SYSTEMD-SERVICE.md (to be created)

---

*For Seven Generations*

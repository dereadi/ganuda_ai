# Jr Build Instructions: Operational Runbooks (5 Failure Scenarios)

**Priority**: HIGH  
**Phase**: 3 - Hardening & Packaging  
**Assigned To**: IT Triad Jr  
**Date**: December 13, 2025

## Objective

Complete the 5 critical failure scenario runbooks for Cherokee AI Federation operations. We have 3 started, need 2 more, and need to enhance existing ones.

## Runbook Location

`/ganuda/runbooks/`

## Existing Runbooks (Need Enhancement)
1. NODE_UNREACHABLE.md ✅ (good, add thermal memory logging)
2. GPU_WEDGED.md ✅ (needs recovery commands)
3. DB_CONNECTION_EXHAUSTED.md ✅ (needs connection pool tuning)

## Missing Runbooks (Create These)
4. LLM_GATEWAY_DOWN.md
5. THERMAL_MEMORY_CORRUPTION.md

---

## Runbook 4: LLM Gateway Down

```bash
ssh dereadi@192.168.132.223 "cat > /ganuda/runbooks/LLM_GATEWAY_DOWN.md << 'RUNBOOK'
# RUNBOOK: LLM Gateway Down

## Symptoms
- curl http://192.168.132.223:8080/health returns error
- Council votes failing
- API requests timing out
- Grafana shows gateway unhealthy

## Severity
**P1** - Core service down, all AI features unavailable

## Diagnosis

### Step 1: Check Service Status
\`\`\`bash
systemctl status llm-gateway
journalctl -u llm-gateway -n 50 --no-pager
\`\`\`

### Step 2: Check Port Binding
\`\`\`bash
ss -tlnp | grep 8080
\`\`\`

### Step 3: Check vLLM Backend
\`\`\`bash
curl -s http://localhost:8000/health
ps aux | grep vllm
\`\`\`

### Step 4: Check Database Connectivity
\`\`\`bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c \"SELECT 1\"
\`\`\`

## Resolution Steps

### Scenario A: Service Not Running
\`\`\`bash
sudo systemctl restart llm-gateway
sleep 10
curl -s http://localhost:8080/health | jq .
\`\`\`

### Scenario B: Port Conflict
\`\`\`bash
# Find what's using 8080
sudo lsof -i :8080
# Kill if stale process
sudo kill -9 <PID>
sudo systemctl restart llm-gateway
\`\`\`

### Scenario C: vLLM Backend Down
\`\`\`bash
# Restart vLLM
sudo systemctl restart vllm  # if systemd
# OR
pkill -f vllm
cd /ganuda/services/vllm && ./start_vllm.sh
\`\`\`

### Scenario D: Database Unreachable
- See DB_CONNECTION_EXHAUSTED.md
- Gateway will recover once DB is available

### Scenario E: Out of Memory
\`\`\`bash
free -h
# If OOM, restart with reduced workers
sudo systemctl stop llm-gateway
# Edit service to use --workers 1
sudo systemctl start llm-gateway
\`\`\`

## Verification
\`\`\`bash
curl -s http://192.168.132.223:8080/health | jq .
# Should show status: healthy
\`\`\`

## Post-Incident
\`\`\`bash
# Log to thermal memory
ssh dereadi@192.168.132.222 \"PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production -c \\\"
INSERT INTO thermal_memory_archive (memory_hash, original_content, current_stage, temperature_score)
VALUES ('INCIDENT-GATEWAY-\$(date +%Y%m%d%H%M)', 'LLM Gateway incident: [DESCRIBE CAUSE AND RESOLUTION]', 'FRESH', 90.0);
\\\"\"
\`\`\`

---
Cherokee AI Federation | FOR SEVEN GENERATIONS
RUNBOOK"
echo "LLM_GATEWAY_DOWN.md created"
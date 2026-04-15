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
```bash
systemctl status llm-gateway
journalctl -u llm-gateway -n 50 --no-pager
```

### Step 2: Check Port Binding
```bash
ss -tlnp | grep 8080
```

### Step 3: Check vLLM Backend
```bash
curl -s http://localhost:8000/health
ps aux | grep vllm
```

### Step 4: Check Database Connectivity
```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT 1"
```

## Resolution Steps

### Scenario A: Service Not Running
```bash
sudo systemctl restart llm-gateway
sleep 10
curl -s http://localhost:8080/health | jq .
```

### Scenario B: Port Conflict
```bash
sudo lsof -i :8080
sudo kill -9 <PID>
sudo systemctl restart llm-gateway
```

### Scenario C: vLLM Backend Down
```bash
sudo systemctl restart vllm
# OR
pkill -f vllm
cd /ganuda/services/vllm && ./start_vllm.sh
```

### Scenario D: Out of Memory
```bash
free -h
sudo systemctl stop llm-gateway
# Edit service to use --workers 1
sudo systemctl start llm-gateway
```

## Verification
```bash
curl -s http://192.168.132.223:8080/health | jq .
```

## Post-Incident
Log to thermal memory after resolution.

---
Cherokee AI Federation | FOR SEVEN GENERATIONS

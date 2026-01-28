# JR Instruction: Operational Runbooks for Incident Response

**JR ID:** JR-RUNBOOKS-INCIDENT-RESPONSE-JAN28-2026
**Priority:** P2
**Assigned To:** IT Triad Jr.
**Ultrathink:** ULTRATHINK-PHASE3-PRODUCTION-HARDENING-JAN28-2026.md

---

## Objective

Create operational runbooks for common incident scenarios to enable fast, consistent incident response.

---

## Files to Create

| File | Scenario |
|------|----------|
| `/ganuda/runbooks/RUNBOOK-GPU-WEDGED.md` | GPU memory issues, vLLM stuck |
| `/ganuda/runbooks/RUNBOOK-JR-STUCK.md` | Jr worker not processing tasks |
| `/ganuda/runbooks/RUNBOOK-LLM-TIMEOUT.md` | vLLM latency/timeout issues |
| `/ganuda/runbooks/RUNBOOK-DB-CONNECTION.md` | PostgreSQL connectivity issues |

---

## Runbook: GPU Wedged

Create `/ganuda/runbooks/RUNBOOK-GPU-WEDGED.md`:

```markdown
# RUNBOOK: GPU Wedged / vLLM Unresponsive

## Symptoms
- vLLM requests timing out
- nvidia-smi shows 100% utilization with no throughput
- GPU memory not releasing after requests complete
- Gateway /health shows vllm: "unhealthy"

## Diagnosis

1. Check vLLM service status:
   ```bash
   systemctl status vllm.service
   journalctl -u vllm -n 50 --no-pager
   ```

2. Check GPU state:
   ```bash
   nvidia-smi
   nvidia-smi -q | head -50
   ```

3. Check for zombie processes:
   ```bash
   ps aux | grep -E "vllm|python.*vllm"
   ```

4. Check API responsiveness:
   ```bash
   curl -s http://localhost:8000/health
   time curl -s -X POST http://localhost:8000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model":"nvidia/NVIDIA-Nemotron-Nano-9B-v2","messages":[{"role":"user","content":"test"}],"max_tokens":5}'
   ```

## Resolution

### Level 1: Graceful Restart
```bash
sudo systemctl restart vllm
# Wait 30s for model to load
sleep 30
curl http://localhost:8000/health
```

### Level 2: Forced Restart with GPU Reset
```bash
sudo systemctl stop vllm
sleep 10
sudo nvidia-smi -r  # Reset GPU
sleep 5
sudo systemctl start vllm
```

### Level 3: Nuclear Option (Maintenance Window)
```bash
# Schedule downtime first!
sudo systemctl stop vllm llm-gateway
sudo rmmod nvidia_uvm nvidia_drm nvidia_modeset nvidia
sleep 5
sudo modprobe nvidia
sudo systemctl start vllm llm-gateway
```

## Prevention
- Monitor GPU memory: alert at 90% utilization
- Set request timeouts in gateway (30s default)
- Implement circuit breaker for repeated failures
- Schedule weekly vLLM restarts during low-traffic window

## Escalation
If Level 2 doesn't resolve:
1. Page on-call engineer
2. Check thermal throttling: `nvidia-smi -q -d TEMPERATURE`
3. Review recent code changes to vLLM config
```

---

## Runbook: Jr Worker Stuck

Create `/ganuda/runbooks/RUNBOOK-JR-STUCK.md`:

```markdown
# RUNBOOK: Jr Worker Not Processing Tasks

## Symptoms
- Tasks stuck in "pending" status
- jr_work_queue has old pending tasks
- No activity in Jr logs

## Diagnosis

1. Check pending tasks:
   ```bash
   psql -h 192.168.132.222 -U claude -d zammad_production -c \
     "SELECT id, title, status, assigned_jr, created_at
      FROM jr_work_queue
      WHERE status = 'pending'
      ORDER BY created_at DESC LIMIT 10;"
   ```

2. Check Jr worker process:
   ```bash
   ps aux | grep jr_queue_worker
   systemctl status jr-se jr-it-triad jr-research jr-infra
   ```

3. Check Jr logs:
   ```bash
   journalctl -u jr-se --since "1 hour ago" --no-pager | tail -50
   # Or if running via nohup:
   tail -100 /ganuda/logs/se_jr_worker.log
   ```

4. Check LLM gateway connectivity:
   ```bash
   curl http://localhost:8080/health
   ```

## Resolution

### Level 1: Restart Jr Worker
```bash
# If systemd managed:
sudo systemctl restart jr-se

# If nohup:
pkill -f "jr_queue_worker.py Software Engineer Jr."
cd /ganuda/jr_executor
nohup python -u jr_queue_worker.py "Software Engineer Jr." > /ganuda/logs/se_jr_worker.log 2>&1 &
```

### Level 2: Check Dependencies
```bash
# Verify LLM gateway
curl http://localhost:8080/v1/models

# Verify database
psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT 1;"

# Verify vLLM
curl http://localhost:8000/health
```

### Level 3: Clear Stuck Tasks
```bash
# Mark ancient pending tasks as cancelled
psql -h 192.168.132.222 -U claude -d zammad_production -c \
  "UPDATE jr_work_queue
   SET status = 'cancelled', error_message = 'Timed out - worker stuck'
   WHERE status = 'pending'
   AND created_at < NOW() - INTERVAL '24 hours';"
```

## Prevention
- Use systemd services (auto-restart on failure)
- Monitor pending task count: alert if > 10 for > 1 hour
- Implement heartbeat checks in worker

## Escalation
1. Check if multiple Jr types are stuck (system-wide issue)
2. Review gateway and vLLM logs for root cause
3. Page on-call if critical tasks blocked
```

---

## Runbook: LLM Timeout

Create `/ganuda/runbooks/RUNBOOK-LLM-TIMEOUT.md`:

```markdown
# RUNBOOK: vLLM Latency / Timeout Issues

## Symptoms
- API requests taking > 30s
- Gateway returning 504 timeout errors
- Slow Council votes

## Diagnosis

1. Check current latency:
   ```bash
   time curl -s -X POST http://localhost:8000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model":"nvidia/NVIDIA-Nemotron-Nano-9B-v2","messages":[{"role":"user","content":"Say hello"}],"max_tokens":10}'
   ```

2. Check GPU utilization:
   ```bash
   nvidia-smi dmon -s puc  # Power, Utilization, Clocks
   ```

3. Check concurrent requests:
   ```bash
   ss -tnp | grep 8000 | wc -l  # Active connections to vLLM
   ```

4. Check vLLM queue:
   ```bash
   curl http://localhost:8000/metrics | grep requests
   ```

## Resolution

### Level 1: Reduce Concurrent Load
```bash
# Temporarily pause Jr workers
sudo systemctl stop jr-se jr-it-triad jr-research jr-infra
# Let queue drain
sleep 60
sudo systemctl start jr-se
```

### Level 2: Adjust vLLM Parameters
Edit vLLM service to reduce max concurrent:
```bash
# Add to ExecStart: --max-num-seqs 32 (from 64)
sudo systemctl daemon-reload
sudo systemctl restart vllm
```

### Level 3: Scale Horizontally
If single GPU can't handle load:
- Consider queuing requests with priority
- Implement request batching
- Add second GPU or node

## Prevention
- Monitor P95 latency: alert if > 20s
- Implement request timeout in clients (30s)
- Use Council confidence to short-circuit low-value queries
- Cache frequent queries in thermal memory

## Escalation
If sustained high latency during normal load:
1. Check for memory leaks in vLLM
2. Review model size vs GPU memory
3. Consider model quantization
```

---

## Runbook: Database Connection Issues

Create `/ganuda/runbooks/RUNBOOK-DB-CONNECTION.md`:

```markdown
# RUNBOOK: PostgreSQL Connection Issues

## Symptoms
- Jrs failing with "could not connect to server"
- Thermal memory operations timing out
- "too many connections" errors

## Diagnosis

1. Test connectivity:
   ```bash
   psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT 1;"
   ```

2. Check connection count:
   ```bash
   psql -h 192.168.132.222 -U claude -d zammad_production -c \
     "SELECT count(*) FROM pg_stat_activity WHERE datname = 'zammad_production';"
   ```

3. Check for blocked queries:
   ```bash
   psql -h 192.168.132.222 -U claude -d zammad_production -c \
     "SELECT pid, state, query, wait_event_type
      FROM pg_stat_activity
      WHERE datname = 'zammad_production' AND state != 'idle';"
   ```

4. Check network:
   ```bash
   nc -zv 192.168.132.222 5432
   ping -c 3 192.168.132.222
   ```

## Resolution

### Level 1: Clear Idle Connections
```bash
psql -h 192.168.132.222 -U claude -d zammad_production -c \
  "SELECT pg_terminate_backend(pid)
   FROM pg_stat_activity
   WHERE datname = 'zammad_production'
   AND state = 'idle'
   AND state_change < NOW() - INTERVAL '30 minutes';"
```

### Level 2: Check pg_hba.conf
On bluefin:
```bash
sudo cat /etc/postgresql/*/main/pg_hba.conf | grep -E "192.168|redfin"
# Ensure: host zammad_production claude 192.168.132.0/24 md5
```

### Level 3: Restart PostgreSQL (Maintenance Window)
On bluefin:
```bash
sudo systemctl restart postgresql
```

## Prevention
- Set connection pool limits in Jr code
- Configure idle connection timeout in pg
- Monitor connection count: alert at 80% of max
- Use connection pooler (PgBouncer) for high load

## Escalation
1. Check disk space on bluefin
2. Review PostgreSQL logs: /var/log/postgresql/
3. Contact DBA if persistent issues
```

---

## Verification

```bash
# Confirm runbook files exist
ls -la /ganuda/runbooks/

# Test runbook commands work
nvidia-smi
curl http://localhost:8080/health
psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT 1;"
```

---

FOR SEVEN GENERATIONS

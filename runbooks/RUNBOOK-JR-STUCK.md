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

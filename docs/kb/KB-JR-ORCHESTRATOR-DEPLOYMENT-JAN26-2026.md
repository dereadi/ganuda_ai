# KB Article: Jr Orchestrator Deployment

**ID:** KB-2026-0126-002
**Date:** 2026-01-26
**Category:** Infrastructure / Deployment
**Status:** Active
**Node:** redfin (192.168.132.223)

---

## Summary

The Jr Orchestrator is a systemd-managed daemon that spawns and monitors all Jr worker processes with graduated priority queue allocation. It replaces the previous single-worker systemd service with a unified orchestrator pattern.

---

## Architecture

### Worker Types Managed
| Jr Type | Log File |
|---------|----------|
| Software Engineer Jr. | `/ganuda/logs/software_engineer_jr._worker.log` |
| Research Jr. | `/ganuda/logs/research_jr._worker.log` |
| Infrastructure Jr. | `/ganuda/logs/infrastructure_jr._worker.log` |
| it_triad_jr | `/ganuda/logs/it_triad_jr_worker.log` |

### Health Monitoring
- Database heartbeat checks via `jr_status` table
- 120-second timeout before worker restart
- Exponential backoff on restarts (2^n seconds)

### Priority Queue
See KB-COOPERBENCH-MULTI-AGENT-RESEARCH-JAN26-2026 for why we use one-Jr-one-task pattern instead of cooperative multi-agent.

---

## Deployment

### Prerequisites
- PostgreSQL accessible at 192.168.132.222 (bluefin)
- Python venv at `/home/dereadi/cherokee_venv`
- Log directory `/ganuda/logs` writable by dereadi

### Deploy Command
```bash
sudo bash /ganuda/scripts/deploy_jr_orchestrator.sh
```

### What the Script Does
1. Creates systemd unit file at `/ganuda/scripts/systemd/jr-orchestrator.service`
2. Symlinks to `/etc/systemd/system/`
3. Reloads systemd daemon
4. Stops any old jr_queue_worker processes
5. Disables old jr-queue-worker service
6. Enables and starts jr-orchestrator

---

## Operations

### Check Status
```bash
systemctl status jr-orchestrator
```

### View Logs
```bash
# Orchestrator main log
tail -f /ganuda/logs/jr_orchestrator.log

# Individual worker logs
tail -f /ganuda/logs/software_engineer_jr._worker.log
tail -f /ganuda/logs/research_jr._worker.log
```

### Restart
```bash
sudo systemctl restart jr-orchestrator
```

### Check Worker Heartbeats
```sql
SELECT jr_name, status, last_seen,
       NOW() - last_seen as age
FROM jr_status
ORDER BY last_seen DESC;
```

---

## Troubleshooting

### Worker Restart Loop
**Symptom:** Worker keeps restarting every few seconds

**Cause:** Stale heartbeat in `jr_status` table (> 120s old)

**Fix:**
```sql
UPDATE jr_status
SET last_seen = NOW()
WHERE jr_name = 'Research Jr.';
```

### Permission Denied on Log File
**Symptom:** `PermissionError: [Errno 13] Permission denied`

**Cause:** Log file created by root during failed start

**Fix:**
```bash
sudo chown dereadi:dereadi /ganuda/logs/jr_orchestrator.log
```

### RuntimeError: dictionary keys changed
**Symptom:** Orchestrator crashes during health check

**Cause:** Dict iteration while modifying

**Fix:** Already fixed in current code - wraps iterations in `list()`

---

## Files

| File | Purpose |
|------|---------|
| `/ganuda/jr_executor/jr_orchestrator.py` | Main orchestrator code |
| `/ganuda/lib/graduated_token_bucket.py` | Priority queue logic |
| `/ganuda/scripts/deploy_jr_orchestrator.sh` | Deployment script |
| `/ganuda/scripts/systemd/jr-orchestrator.service` | Systemd unit |

---

## Related KB Articles
- KB-COOPERBENCH-MULTI-AGENT-RESEARCH-JAN26-2026

---

## CMDB Entry

**Service Name:** jr-orchestrator
**Type:** systemd service
**Node:** redfin
**Port:** N/A (subprocess manager)
**Dependencies:** PostgreSQL (bluefin:5432)
**Deployed:** 2026-01-25
**Owner:** Cherokee AI Federation

---

## For Seven Generations

This orchestrator ensures our Jr workers run reliably without manual intervention. When a worker fails, it restarts automatically. When we add new Jr types, they can be added to the `JR_TYPES` list and the orchestrator will manage them.

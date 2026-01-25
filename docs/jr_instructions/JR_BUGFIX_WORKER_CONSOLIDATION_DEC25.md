# Jr Instruction: Worker Daemon Consolidation and False Completion Bugfix

**Created:** December 25, 2025 (Christmas)
**Priority:** 1 (CRITICAL BLOCKER)
**Type:** Bug Fix
**Assigned:** it_triad_jr
**Status:** URGENT

---

## Problem Statement

Multiple competing worker daemons are running simultaneously, causing:
1. **Race conditions** on task pickup
2. **False task completions** - tasks marked 'completed' without work being done
3. **Process confusion** - unclear which worker is authoritative

### Current Competing Processes (on redfin)
```
- jr_queue_worker.py (it_triad_jr)        # /ganuda/jr_executor/
- jr_task_executor.py (jr-redfin-gecko)   # /ganuda/lib/ - Started Dec 24
- jr_task_executor_v2.py (jr-redfin-gecko) # /ganuda/lib/ - Started Dec 24
- it_triad_cli.py --pm                    # /home/dereadi/it_triad/ - Dec 09
- chiefs_agent_daemon.py                  # /home/dereadi/it_triad/ - Dec 06
- jr_agent_daemon.py                      # /home/dereadi/it_triad/ - Dec 08
- jr_cli.py --daemon                      # Dec 18
- jr_bidding_daemon.py (multiple)         # /ganuda/lib/
```

### Evidence of Bug
Tasks 59, 60, 61 were marked 'completed' in seconds without any actual work:
- Created: 11:40:33, Completed: 11:40:37 (4 seconds!)
- No database tables created despite instructions to create them
- Result just says "Task completed" with no actual output

---

## Required Fix

### Phase 1: Stop All Competing Daemons

Stop ALL worker/executor daemons EXCEPT the canonical one:

```bash
# Kill all competing Jr workers
pkill -f 'jr_task_executor'
pkill -f 'it_triad_cli.py --pm'
pkill -f 'jr_agent_daemon'
pkill -f 'jr_cli.py --daemon'
pkill -f 'jr_bidding_daemon'

# Keep only:
# - jr_queue_worker.py (canonical worker)
# - chiefs_agent_daemon.py (human approval routing)
```

### Phase 2: Fix jr_queue_worker.py Error Handling

Current broken pattern (line ~77):
```python
except Exception as e:
    print(f"[{self.jr_name}] Worker error: {e}")
    time.sleep(POLL_INTERVAL)  # <-- Just continues, task status unchanged
```

Fix to properly mark task as failed:
```python
except Exception as e:
    print(f"[{self.jr_name}] Worker error: {e}")
    import traceback
    traceback.print_exc()
    
    # Mark task as failed, not silently skip
    if 'task' in locals():
        self.client.update_task_status(
            task['task_id'], 
            'failed', 
            error_message=str(e)
        )
    
    time.sleep(POLL_INTERVAL)
```

### Phase 3: Add update_task_status to JrQueueClient

Add to /ganuda/jr_executor/jr_queue_client.py:
```python
def update_task_status(self, task_id: str, status: str, 
                       error_message: str = None,
                       result: dict = None):
    """Update task status with optional error or result."""
    with self.conn.cursor() as cur:
        if status == 'failed':
            cur.execute("""
                UPDATE jr_work_queue 
                SET status = 'failed',
                    error_message = %s,
                    updated_at = NOW()
                WHERE task_id = %s
            """, (error_message, task_id))
        elif status == 'completed':
            cur.execute("""
                UPDATE jr_work_queue 
                SET status = 'completed',
                    completed_at = NOW(),
                    result = %s,
                    updated_at = NOW()
                WHERE task_id = %s
            """, (json.dumps(result or {}), task_id))
        else:
            cur.execute("""
                UPDATE jr_work_queue 
                SET status = %s,
                    status_message = %s,
                    updated_at = NOW()
                WHERE task_id = %s
            """, (status, error_message, task_id))
        self.conn.commit()
```

### Phase 4: Verify TaskExecutor Has process_queue_task

Ensure /ganuda/jr_executor/task_executor.py line 112 has:
```python
def process_queue_task(self, task: Dict) -> Dict[str, Any]:
    # This method MUST exist and process Jr work queue tasks
```

If missing, check for cached .pyc files:
```bash
rm -rf /ganuda/jr_executor/__pycache__/*
rm -rf /home/dereadi/cherokee_venv/lib/python3.12/site-packages/__pycache__/*
```

### Phase 5: Create Systemd Service for Canonical Worker

Create /home/dereadi/.config/systemd/user/jr-queue-worker.service:
```ini
[Unit]
Description=Cherokee AI Jr Queue Worker - it_triad_jr
After=network.target postgresql.service

[Service]
Type=simple
WorkingDirectory=/ganuda/jr_executor
ExecStart=/home/dereadi/cherokee_venv/bin/python3 -u jr_queue_worker.py it_triad_jr
Restart=always
RestartSec=30
StandardOutput=append:/ganuda/logs/jr_queue_worker.log
StandardError=append:/ganuda/logs/jr_queue_worker.log

[Install]
WantedBy=default.target
```

Enable:
```bash
systemctl --user daemon-reload
systemctl --user enable jr-queue-worker
systemctl --user start jr-queue-worker
```

---

## Validation Checklist

- [ ] All competing worker daemons killed
- [ ] Only jr-queue-worker.service running
- [ ] Error handling updated in jr_queue_worker.py
- [ ] update_task_status method added to JrQueueClient
- [ ] process_queue_task method verified present
- [ ] Cache cleared
- [ ] Test task submitted and properly processed OR properly failed
- [ ] Tasks 59, 60, 61 picked up and ACTUALLY executed (tables created)

---

## After Fix: Verify Hive Mind Tasks

After consolidation, verify tasks are actually executing:
```sql
-- Check task status
SELECT id, title, status, completed_at FROM jr_work_queue WHERE id >= 59;

-- Check if tables were created
SELECT table_name FROM information_schema.tables 
WHERE table_schema='public' 
AND (table_name LIKE '%collective%' OR table_name LIKE '%macro_agent%');
```

If tables exist, the bug is fixed.

---

**For Seven Generations - No false completions, only true work.**

*Priority 1 because this blocks all Jr task execution*

# Jr Instruction: Executor P0 — Atomic Task Locking + Worker Lifecycle

**Task ID:** EXECUTOR-P0-LOCKING-LIFECYCLE-001
**Assigned:** Software Engineer Jr.
**Priority:** P0 (Critical — prevents data corruption and stale workers)
**Created:** 2026-02-03
**TPM:** Claude Opus 4.5
**Council Vote:** APPROVED 7/7 (audit hash: 38a517d5c204a4e7)
**Depends on:** None

---

## Context

During live monitoring of Jr tasks #547-549 on Feb 2, 2026, two critical failures were observed:

1. **Worker Contention** — 5+ SWE Jr worker processes race on the same task because `get_pending_tasks()` uses a plain SELECT with no row-level locking. Multiple workers claim and execute the same task simultaneously.

2. **Stale Workers** — Worker processes running since Jan 28-31 loaded old `rlm_executor.py` without the override logic added later. These stale workers never pick up code changes because Python modules are imported once at startup. Files went to staging instead of target paths.

### Council Conditions (Incorporated)
- **Crawdad (Security):** All queries must use parameterized queries — VERIFIED: existing code already uses `%s` placeholders via psycopg2, no string interpolation.
- **Gecko (Performance):** Load test after deployment to verify no latency regression from `FOR UPDATE SKIP LOCKED`.
- **Eagle Eye (Monitoring):** Log worker restart events and task claim conflicts.

### Files to Modify

1. `/ganuda/jr_executor/jr_queue_client.py` — Add `FOR UPDATE SKIP LOCKED` to task claiming
2. `/ganuda/jr_executor/jr_queue_worker.py` — Add max-tasks-per-child with auto-restart

---

## Step 1: Atomic Task Claiming with FOR UPDATE SKIP LOCKED

Modify: `/ganuda/jr_executor/jr_queue_client.py`

### 1A: Replace `get_pending_tasks()` method (lines 84-103)

The current implementation does a plain SELECT, which means multiple workers can see and claim the same tasks. Replace with a single atomic claim-and-return query.

Replace the `get_pending_tasks` method with:

```python
def get_pending_tasks(self, limit: int = 1) -> List[Dict]:
    """
    Atomically claim pending tasks assigned to this Jr.
    Uses SELECT FOR UPDATE SKIP LOCKED to prevent worker contention.

    Args:
        limit: Maximum number of tasks to claim (default 1)

    Returns:
        List of task dictionaries (already claimed as in_progress)
    """
    conn = self._get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Atomic claim: SELECT + UPDATE in one transaction
            # SKIP LOCKED ensures other workers skip tasks being claimed
            cur.execute("""
                WITH claimable AS (
                    SELECT id
                    FROM jr_work_queue
                    WHERE assigned_jr = %s
                      AND status IN ('pending', 'assigned')
                    ORDER BY sacred_fire_priority DESC, priority ASC, created_at ASC
                    LIMIT %s
                    FOR UPDATE SKIP LOCKED
                )
                UPDATE jr_work_queue wq
                SET status = 'in_progress',
                    started_at = NOW(),
                    status_message = 'Claimed by worker (atomic lock)'
                FROM claimable
                WHERE wq.id = claimable.id
                RETURNING wq.id, wq.task_id, wq.title, wq.description,
                          wq.priority, wq.sacred_fire_priority,
                          wq.instruction_file, wq.instruction_content,
                          wq.parameters, wq.seven_gen_impact, wq.tags,
                          wq.created_at, wq.use_rlm
            """, (self.jr_name, limit))
            rows = cur.fetchall()
            conn.commit()
            if rows:
                print(f"[JrQueue] Atomically claimed {len(rows)} task(s)")
            return rows
    except Exception as e:
        conn.rollback()
        raise
```

### 1B: Simplify `claim_task()` method (lines 105-129)

Since `get_pending_tasks()` now atomically claims tasks, `claim_task()` becomes a no-op check. Replace it with a verification function:

```python
def claim_task(self, task_id: int) -> bool:
    """
    Verify a task is claimed by this Jr (already done by get_pending_tasks).
    Kept for backward compatibility.

    Args:
        task_id: The task's database ID

    Returns:
        True if task is in_progress and owned by this Jr
    """
    try:
        rows = self._execute("""
            SELECT id FROM jr_work_queue
            WHERE id = %s AND assigned_jr = %s AND status = 'in_progress'
        """, (task_id, self.jr_name))
        return len(rows) > 0
    except Exception as e:
        print(f"[JrQueue] Failed to verify task {task_id}: {e}")
        return False
```

---

## Step 2: Worker Max-Tasks-Per-Child with Hot Reload

Modify: `/ganuda/jr_executor/jr_queue_worker.py`

### 2A: Add configuration constants (after line 23)

Add after `HEARTBEAT_INTERVAL = 60`:

```python
MAX_TASKS_PER_CHILD = 10  # Worker restarts after processing this many tasks
WORKER_VERSION = "2.0.0-p0"  # Track worker version for stale detection
```

### 2B: Add task counter and version tracking to __init__ (after line 35)

Add after `self.current_task = None`:

```python
self.tasks_processed = 0
self.worker_version = WORKER_VERSION
self.start_time = datetime.now()
print(f"[{self.jr_name}] Worker version: {WORKER_VERSION}")
```

### 2C: Modify the main run() loop

In the `run()` method, after the task is completed or failed (after the try/except block around `self.executor.process_queue_task(task)`, approximately line 167), add the task counter check:

After `traceback.print_exc()` and the mark-failed block (line 167), add:

```python
                    # Increment task counter
                    self.tasks_processed += 1
                    print(f"[{self.jr_name}] Tasks processed: {self.tasks_processed}/{MAX_TASKS_PER_CHILD}")

                    # Check if worker should restart for code freshness
                    if self.tasks_processed >= MAX_TASKS_PER_CHILD:
                        print(f"[{self.jr_name}] Reached max tasks ({MAX_TASKS_PER_CHILD}). Restarting for code freshness...")
                        self.running = False
                        break
```

### 2D: Add restart logic at the bottom of the file

Replace the `if __name__ == "__main__"` block (lines 192-199) with:

```python
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 jr_queue_worker.py 'Jr Name'")
        sys.exit(1)

    jr_name = sys.argv[1]

    # Auto-restart loop: worker restarts after MAX_TASKS_PER_CHILD tasks
    # This ensures fresh module imports (eliminates stale worker class)
    restart_count = 0
    while True:
        restart_count += 1
        print(f"[{jr_name}] Starting worker (run #{restart_count})...")
        worker = JrQueueWorker(jr_name)
        worker.run()

        # If worker stopped due to SIGTERM/SIGINT, don't restart
        if not worker.running and worker.tasks_processed < MAX_TASKS_PER_CHILD:
            print(f"[{jr_name}] Worker stopped by signal. Exiting.")
            break

        # If worker hit max tasks, reimport modules and restart
        print(f"[{jr_name}] Reloading modules for fresh code...")
        import importlib
        import jr_queue_client
        import task_executor
        importlib.reload(jr_queue_client)
        importlib.reload(task_executor)
        from jr_queue_client import JrQueueClient
        from task_executor import TaskExecutor

        time.sleep(2)  # Brief pause before restart
```

### 2E: Remove the separate `claim_task` call from the worker

In the `run()` method, the worker currently calls `get_pending_tasks()` then separately claims. Since `get_pending_tasks()` now atomically claims, remove the separate claim call if one exists. The current code at line 118 calls `self.executor.process_queue_task(task)` directly after getting tasks, which is correct — no separate claim_task call exists in the worker.

---

## Step 3: Update systemd service for auto-restart

Modify: `/ganuda/scripts/systemd/jr-queue-worker.service`

Verify the systemd unit has `Restart=always` so that if the worker process exits (from Python-level restart), systemd restarts it. If the service file already has `Restart=always`, this step is done.

If the service does NOT restart on exit, add:

```ini
[Service]
Restart=always
RestartSec=5
```

**Note:** The Python-level restart loop (Step 2D) handles the normal max-tasks restart. Systemd `Restart=always` is the safety net for unexpected crashes.

---

## Step 4: Verify

After deploying, verify the changes work:

```bash
# 1. Check worker version
ps aux | grep jr_queue_worker | grep -v grep

# 2. Check that tasks are being claimed atomically (look for "atomic lock" in logs)
journalctl -u jr-queue-worker -n 50 --no-pager | grep -i "atomic\|claimed\|version"

# 3. Queue a test task and verify only one worker processes it
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
INSERT INTO jr_work_queue (task_id, title, description, assigned_jr, priority, status, instruction_content, use_rlm)
VALUES ('TEST-LOCKING-001', 'Test Task Locking', 'Verify atomic claiming works', 'Software Engineer Jr.', 3, 'pending', 'Echo test: verify single worker claims this task', false);
"

# 4. Wait 60 seconds, then verify exactly one completion (not multiple):
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT id, status, started_at, completed_at FROM jr_work_queue WHERE task_id = 'TEST-LOCKING-001';
"
```

---

## Acceptance Criteria

1. `get_pending_tasks()` uses `SELECT FOR UPDATE SKIP LOCKED` — no worker contention
2. `claim_task()` is a verification-only function (backward compatible)
3. Worker restarts after `MAX_TASKS_PER_CHILD` (10) tasks processed
4. Module reimport on restart eliminates stale worker class
5. Worker version logged on startup (`WORKER_VERSION`)
6. Task counter logged after each task completion
7. Systemd service supports auto-restart on exit
8. All queries remain parameterized (Crawdad security condition)
9. No latency regression from locking (Gecko performance condition)
10. Restart events visible in journalctl logs (Eagle Eye monitoring condition)

---

## Rollback

If issues arise, revert to the original `get_pending_tasks()` (plain SELECT) and remove the max-tasks-per-child loop. The original code is in git at the current HEAD.

---

*For Seven Generations*
*Cherokee AI Federation — Jr Executor Architecture Team*

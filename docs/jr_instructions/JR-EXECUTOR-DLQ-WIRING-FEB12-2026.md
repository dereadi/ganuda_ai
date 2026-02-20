# Jr Instruction: Executor DLQ Wiring — Connect Dead Letter Queue to Failure Path

**Kanban**: #1750 (Executor P1: Dead Letter Queue + Auto-Escalation)
**Sacred Fire Priority**: 13
**Story Points**: 8
**River Cycle**: RC-2026-02A
**Long Man Step**: BUILD

## Context

A previous attempt (#692, Feb 10) **partially succeeded**:
- `jr_executor/dlq_manager.py` — EXISTS, complete, 4 escalation levels ✅
- `jr_executor/dlq_retry_poller.py` — EXISTS, complete ✅
- Wiring into `task_executor.py` — FAILED (`SEARCH_NOT_FOUND`, wrong search string)

**What remains:**
1. Create the `jr_failed_tasks_dlq` database table (never created)
2. Wire DLQ into `jr_queue_worker.py` failure path (the actual worker loop)
3. Add DLQ convenience methods to `jr_queue_client.py`

Current failure path in jr_queue_worker.py is a DEAD END: exception → `fail_task()` → task marked failed → never retried. The DLQ adds retry with exponential backoff and escalation to TPM/Council.

**IMPORTANT**: The wiring goes into `jr_queue_worker.py` (the worker loop), NOT `task_executor.py` (the step executor). The worker decides what to do when a task fails — the executor just reports success/failure.

## Steps

### Step 1: Create Database Migration Script

Create `/ganuda/scripts/migrations/create_dlq_table.py`

```python
#!/usr/bin/env python3
"""Create the jr_failed_tasks_dlq table for Dead Letter Queue.

Kanban #1750 — Executor DLQ Wiring
Run once: python3 /ganuda/scripts/migrations/create_dlq_table.py

For Seven Generations
"""

import sys
sys.path.insert(0, '/ganuda')
from lib.secrets_loader import get_db_config
import psycopg2

def create_table():
    """Create the DLQ table if it doesn't exist."""
    db = get_db_config()
    conn = psycopg2.connect(**db)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS jr_failed_tasks_dlq (
            id SERIAL PRIMARY KEY,
            original_task_id INTEGER NOT NULL REFERENCES jr_work_queue(id),
            failure_reason TEXT NOT NULL,
            failure_traceback TEXT,
            step_number INTEGER,
            retry_count INTEGER DEFAULT 0,
            max_retries INTEGER DEFAULT 3,
            escalation_level INTEGER DEFAULT 0,
            assigned_escalation_target VARCHAR(100),
            resolution_status VARCHAR(50) DEFAULT 'unresolved',
            resolution_notes TEXT,
            next_retry_timestamp TIMESTAMP,
            last_retry_timestamp TIMESTAMP,
            resolved_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_dlq_resolution_status
            ON jr_failed_tasks_dlq(resolution_status);

        CREATE INDEX IF NOT EXISTS idx_dlq_next_retry
            ON jr_failed_tasks_dlq(next_retry_timestamp)
            WHERE resolution_status = 'retrying';

        CREATE INDEX IF NOT EXISTS idx_dlq_original_task
            ON jr_failed_tasks_dlq(original_task_id);

        CREATE INDEX IF NOT EXISTS idx_dlq_escalation
            ON jr_failed_tasks_dlq(escalation_level)
            WHERE escalation_level >= 2;
    """)

    conn.commit()
    print("[DLQ Migration] jr_failed_tasks_dlq table created successfully")

    # Verify
    cur.execute("SELECT COUNT(*) FROM jr_failed_tasks_dlq")
    count = cur.fetchone()[0]
    print(f"[DLQ Migration] Table has {count} existing entries")

    cur.close()
    conn.close()

if __name__ == '__main__':
    create_table()
    print("[DLQ Migration] Done — For Seven Generations")
```

### Step 2: Wire DLQ into jr_queue_worker.py Failure Path

File: `jr_executor/jr_queue_worker.py`

```python
<<<<<<< SEARCH
                        else:
                            error_msg = result.get('error', 'Unknown error')
                            print(f"[{self.jr_name}] Task failed: {error_msg}")
                            # Mark as failed explicitly
                            self.client.fail_task(task['id'], error_msg, result)  # Use integer id
                    except Exception as task_error:
                        # Task execution error - mark as FAILED, not skip
                        error_msg = f"Task execution error: {task_error}"
                        print(f"[{self.jr_name}] {error_msg}")
                        traceback.print_exc()
                        try:
                            self.client.fail_task(task['id'], error_msg)  # Use integer id
                        except Exception as mark_error:
                            print(f"[{self.jr_name}] Could not mark task as failed: {mark_error}")
=======
                        else:
                            error_msg = result.get('error', 'Unknown error')
                            print(f"[{self.jr_name}] Task failed: {error_msg}")
                            # DLQ integration: route failures for retry + escalation
                            try:
                                sys.path.insert(0, '/ganuda')
                                from jr_executor.dlq_manager import send_to_dlq
                                dlq_id = send_to_dlq(
                                    task_id=task['id'],
                                    failure_reason=error_msg,
                                    failure_traceback=result.get('traceback'),
                                )
                                print(f"[{self.jr_name}] Task {task['id']} routed to DLQ (entry {dlq_id})")
                            except Exception as dlq_err:
                                print(f"[{self.jr_name}] DLQ routing failed ({dlq_err}), falling back to fail_task")
                                self.client.fail_task(task['id'], error_msg, result)
                    except Exception as task_error:
                        # Task execution error - route through DLQ for retry
                        error_msg = f"Task execution error: {task_error}"
                        print(f"[{self.jr_name}] {error_msg}")
                        traceback.print_exc()
                        try:
                            sys.path.insert(0, '/ganuda')
                            from jr_executor.dlq_manager import send_to_dlq
                            send_to_dlq(
                                task_id=task['id'],
                                failure_reason=error_msg,
                                failure_traceback=traceback.format_exc(),
                            )
                        except Exception as dlq_err:
                            print(f"[{self.jr_name}] DLQ routing failed ({dlq_err}), falling back to fail_task")
                            try:
                                self.client.fail_task(task['id'], error_msg)
                            except Exception as mark_error:
                                print(f"[{self.jr_name}] Could not mark task as failed: {mark_error}")
>>>>>>> REPLACE
```

### Step 3: Add DLQ Methods to jr_queue_client.py

File: `jr_executor/jr_queue_client.py`

```python
<<<<<<< SEARCH
    def get_my_workload(self) -> Dict:
        """
        Get this Jr's current workload summary.

        Returns:
            Dictionary with task counts by status
        """
        result = self._execute("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'in_progress') as active,
                COUNT(*) FILTER (WHERE status IN ('pending', 'assigned')) as queued,
                COUNT(*) FILTER (WHERE status = 'completed' AND completed_at > NOW() - INTERVAL '24 hours') as completed_24h,
                COUNT(*) FILTER (WHERE status = 'blocked') as blocked
            FROM jr_work_queue
            WHERE assigned_jr = %s
        """, (self.jr_name,))
        return dict(result[0]) if result else {}
=======
    def get_my_workload(self) -> Dict:
        """
        Get this Jr's current workload summary.

        Returns:
            Dictionary with task counts by status
        """
        result = self._execute("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'in_progress') as active,
                COUNT(*) FILTER (WHERE status IN ('pending', 'assigned')) as queued,
                COUNT(*) FILTER (WHERE status = 'completed' AND completed_at > NOW() - INTERVAL '24 hours') as completed_24h,
                COUNT(*) FILTER (WHERE status = 'blocked') as blocked
            FROM jr_work_queue
            WHERE assigned_jr = %s
        """, (self.jr_name,))
        return dict(result[0]) if result else {}

    def get_dlq_summary(self) -> Dict:
        """
        Get Dead Letter Queue summary for monitoring.

        Returns:
            Dictionary with DLQ counts by status
        """
        result = self._execute("""
            SELECT
                COUNT(*) FILTER (WHERE d.resolution_status = 'unresolved') as unresolved,
                COUNT(*) FILTER (WHERE d.resolution_status = 'retrying') as retrying,
                COUNT(*) FILTER (WHERE d.escalation_level = 2) as escalated_tpm,
                COUNT(*) FILTER (WHERE d.escalation_level = 3) as escalated_council,
                COUNT(*) FILTER (WHERE d.resolution_status = 'resolved') as resolved
            FROM jr_failed_tasks_dlq d
        """)
        return dict(result[0]) if result else {}

    def requeue_from_dlq(self, task_id: int) -> bool:
        """
        Re-queue a failed task by resetting its status to pending.

        Args:
            task_id: The original task ID from jr_work_queue

        Returns:
            True if task was re-queued
        """
        try:
            self._execute("""
                UPDATE jr_work_queue
                SET status = 'pending',
                    error_message = NULL,
                    started_at = NULL,
                    completed_at = NULL,
                    progress_percent = 0,
                    status_message = 'Re-queued from DLQ'
                WHERE id = %s
            """, (task_id,), fetch=False)
            return True
        except Exception as e:
            print(f"[JrQueue] Failed to requeue task {task_id} from DLQ: {e}")
            return False
>>>>>>> REPLACE
```

## Verification

After step 1, verify the table exists:

```text
python3 /ganuda/scripts/migrations/create_dlq_table.py
```

After all steps, verify the wiring by checking imports resolve:

```text
python3 -c "from jr_executor.dlq_manager import send_to_dlq, get_tasks_ready_for_retry; print('DLQ imports OK')"
```

## What This Does NOT Cover

- Starting dlq_retry_poller.py as a systemd service (Chief deploys .service files)
- Telegram notification on escalation to TPM (separate enhancement)
- Council escalation workflow (Level 3 — future sprint)
- DLQ dashboard in SAG UI (separate kanban item)

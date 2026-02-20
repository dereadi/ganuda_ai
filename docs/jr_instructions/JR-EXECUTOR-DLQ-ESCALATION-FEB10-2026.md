# Jr Instruction: Executor Dead Letter Queue + Auto-Escalation
*Kanban: #1750 | Priority: P1 | Estimated: 16-23 hours*
*Reference: PostgreSQL-backed DLQ pattern*
*Depends on: Nothing (standalone)*

## Objective
Add a Dead Letter Queue (DLQ) to the Jr executor so failed tasks are captured, retried with exponential backoff, and escalated to TPM or Council when retries are exhausted.

## Step 1: Create DLQ Schema

Create `/ganuda/scripts/sql/create_dlq_tables.sql`

```text
-- Dead Letter Queue for failed Jr tasks
-- Captures failures, tracks retries, escalates when exhausted
-- For Seven Generations

CREATE TABLE IF NOT EXISTS jr_failed_tasks_dlq (
    id SERIAL PRIMARY KEY,
    original_task_id INTEGER REFERENCES jr_work_queue(id),
    failure_reason TEXT NOT NULL,
    failure_traceback TEXT,
    step_number INTEGER,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    last_retry_timestamp TIMESTAMP,
    next_retry_timestamp TIMESTAMP,
    escalation_level INTEGER DEFAULT 0,
    -- 0: pending retry, 1: retrying, 2: escalated to TPM, 3: escalated to council
    assigned_escalation_target VARCHAR(128),
    resolution_status VARCHAR(32) DEFAULT 'unresolved',
    -- unresolved, retrying, resolved, wontfix
    resolution_notes TEXT,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_dlq_task_id ON jr_failed_tasks_dlq(original_task_id);
CREATE INDEX idx_dlq_status ON jr_failed_tasks_dlq(resolution_status);
CREATE INDEX idx_dlq_escalation ON jr_failed_tasks_dlq(escalation_level);
CREATE INDEX idx_dlq_next_retry ON jr_failed_tasks_dlq(next_retry_timestamp) WHERE resolution_status = 'unresolved';

-- View for monitoring
CREATE OR REPLACE VIEW jr_dlq_dashboard AS
SELECT
    d.id as dlq_id,
    d.original_task_id,
    q.title as task_title,
    q.assigned_jr,
    d.failure_reason,
    d.retry_count,
    d.max_retries,
    d.escalation_level,
    CASE d.escalation_level
        WHEN 0 THEN 'pending_retry'
        WHEN 1 THEN 'retrying'
        WHEN 2 THEN 'escalated_tpm'
        WHEN 3 THEN 'escalated_council'
    END as escalation_label,
    d.resolution_status,
    d.next_retry_timestamp,
    d.created_at
FROM jr_failed_tasks_dlq d
LEFT JOIN jr_work_queue q ON q.id = d.original_task_id
ORDER BY d.escalation_level DESC, d.created_at DESC;
```

## Step 2: Create DLQ Manager Module

Create `/ganuda/jr_executor/dlq_manager.py`

```python
"""
Dead Letter Queue Manager for Cherokee Jr Executor
Handles failed task capture, exponential retry, and escalation routing.

Escalation Levels:
  0 - Pending retry (auto)
  1 - Retrying (auto, exponential backoff)
  2 - Escalated to TPM (manual resolution required)
  3 - Escalated to Council (governance decision)

For Seven Generations
"""

import psycopg2
import traceback
from datetime import datetime, timedelta
from typing import Optional


def get_db_connection():
    """Get database connection using federation credentials."""
    import os
    password = os.environ.get('DB_PASSWORD', 'TYDo5U2NVkXqQ8DHuhIpvRgLUrXf2iZE')
    return psycopg2.connect(
        host='192.168.132.222',
        port=5432,
        user='claude',
        password=password,
        dbname='zammad_production'
    )


def send_to_dlq(task_id: int, failure_reason: str, step_number: Optional[int] = None,
                 failure_traceback: Optional[str] = None) -> int:
    """Send a failed task to the Dead Letter Queue.

    Returns the DLQ entry ID.
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()

        # Check if this task already has a DLQ entry
        cur.execute(
            "SELECT id, retry_count, max_retries FROM jr_failed_tasks_dlq "
            "WHERE original_task_id = %s AND resolution_status = 'unresolved' "
            "ORDER BY created_at DESC LIMIT 1",
            (task_id,)
        )
        existing = cur.fetchone()

        if existing:
            dlq_id, retry_count, max_retries = existing
            new_retry_count = retry_count + 1

            if new_retry_count >= max_retries:
                # Exhausted retries — escalate to TPM
                cur.execute(
                    "UPDATE jr_failed_tasks_dlq SET "
                    "retry_count = %s, failure_reason = %s, failure_traceback = %s, "
                    "escalation_level = 2, assigned_escalation_target = 'TPM', "
                    "last_retry_timestamp = NOW(), updated_at = NOW() "
                    "WHERE id = %s",
                    (new_retry_count, failure_reason, failure_traceback, dlq_id)
                )
                print(f"[DLQ] Task {task_id} exhausted {max_retries} retries — ESCALATED TO TPM")
            else:
                # Schedule next retry with exponential backoff
                backoff_seconds = (2 ** new_retry_count) * 60  # 2min, 4min, 8min
                next_retry = datetime.now() + timedelta(seconds=backoff_seconds)
                cur.execute(
                    "UPDATE jr_failed_tasks_dlq SET "
                    "retry_count = %s, failure_reason = %s, failure_traceback = %s, "
                    "escalation_level = 1, next_retry_timestamp = %s, "
                    "last_retry_timestamp = NOW(), resolution_status = 'retrying', "
                    "updated_at = NOW() "
                    "WHERE id = %s",
                    (new_retry_count, failure_reason, failure_traceback, next_retry, dlq_id)
                )
                print(f"[DLQ] Task {task_id} retry {new_retry_count}/{max_retries} — next at {next_retry}")

            conn.commit()
            return dlq_id
        else:
            # First failure — create DLQ entry with retry scheduled
            next_retry = datetime.now() + timedelta(minutes=2)
            cur.execute(
                "INSERT INTO jr_failed_tasks_dlq "
                "(original_task_id, failure_reason, failure_traceback, step_number, "
                "retry_count, next_retry_timestamp, resolution_status) "
                "VALUES (%s, %s, %s, %s, 1, %s, 'retrying') RETURNING id",
                (task_id, failure_reason, failure_traceback, step_number, next_retry)
            )
            dlq_id = cur.fetchone()[0]
            conn.commit()
            print(f"[DLQ] Task {task_id} entered DLQ (id={dlq_id}) — retry in 2 minutes")
            return dlq_id
    finally:
        conn.close()


def get_tasks_ready_for_retry() -> list:
    """Return DLQ entries that are due for retry."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT d.id, d.original_task_id, q.title, d.retry_count "
            "FROM jr_failed_tasks_dlq d "
            "JOIN jr_work_queue q ON q.id = d.original_task_id "
            "WHERE d.resolution_status = 'retrying' "
            "AND d.next_retry_timestamp <= NOW() "
            "ORDER BY d.next_retry_timestamp ASC"
        )
        return cur.fetchall()
    finally:
        conn.close()


def resolve_dlq_entry(dlq_id: int, resolution_notes: str = '', status: str = 'resolved'):
    """Mark a DLQ entry as resolved."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE jr_failed_tasks_dlq SET "
            "resolution_status = %s, resolution_notes = %s, "
            "resolved_at = NOW(), updated_at = NOW() "
            "WHERE id = %s",
            (status, resolution_notes, dlq_id)
        )
        conn.commit()
        print(f"[DLQ] Entry {dlq_id} resolved: {status}")
    finally:
        conn.close()


def get_dlq_summary() -> dict:
    """Return summary statistics for the DLQ dashboard."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE resolution_status = 'unresolved') as unresolved,
                COUNT(*) FILTER (WHERE resolution_status = 'retrying') as retrying,
                COUNT(*) FILTER (WHERE escalation_level = 2) as escalated_tpm,
                COUNT(*) FILTER (WHERE escalation_level = 3) as escalated_council,
                COUNT(*) FILTER (WHERE resolution_status = 'resolved') as resolved
            FROM jr_failed_tasks_dlq
        """)
        row = cur.fetchone()
        return {
            'unresolved': row[0],
            'retrying': row[1],
            'escalated_tpm': row[2],
            'escalated_council': row[3],
            'resolved': row[4]
        }
    finally:
        conn.close()
```

## Step 3: Integrate DLQ into Task Executor

File: `/ganuda/jr_executor/task_executor.py`

Find the main task execution loop where exceptions are caught (around the `execute_step` or `execute_task` method). Add DLQ integration:

<<<<<<< SEARCH
        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] Task {task_id} failed: {error_msg}")
=======
        except Exception as e:
            error_msg = str(e)
            tb = traceback.format_exc()
            print(f"[ERROR] Task {task_id} failed: {error_msg}")

            # Send to Dead Letter Queue for retry/escalation
            try:
                from dlq_manager import send_to_dlq
                dlq_id = send_to_dlq(
                    task_id=task_id,
                    failure_reason=error_msg,
                    failure_traceback=tb,
                    step_number=getattr(self, '_current_step', None)
                )
            except Exception as dlq_err:
                print(f"[WARN] DLQ submission failed: {dlq_err}")
>>>>>>> REPLACE

## Step 4: Add DLQ Retry Poller

Create `/ganuda/jr_executor/dlq_retry_poller.py`

```python
"""
DLQ Retry Poller — checks for tasks due for retry and re-queues them.
Run as a lightweight background loop or cron job.
For Seven Generations
"""

import time
from dlq_manager import get_tasks_ready_for_retry, resolve_dlq_entry


def poll_and_retry(interval_seconds=60):
    """Poll the DLQ for tasks ready to retry."""
    print("[DLQ Poller] Starting retry polling loop")
    while True:
        try:
            tasks = get_tasks_ready_for_retry()
            for dlq_id, task_id, title, retry_count in tasks:
                print(f"[DLQ Poller] Retrying task {task_id}: {title} (attempt {retry_count})")

                # Re-queue the task by resetting its status
                from dlq_manager import get_db_connection
                conn = get_db_connection()
                try:
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE jr_work_queue SET status = 'pending', "
                        "updated_at = NOW() WHERE id = %s",
                        (task_id,)
                    )
                    conn.commit()
                finally:
                    conn.close()

        except Exception as e:
            print(f"[DLQ Poller] Error: {e}")

        time.sleep(interval_seconds)


if __name__ == '__main__':
    poll_and_retry()
```

## Validation
- `jr_failed_tasks_dlq` table exists with proper indexes
- `jr_dlq_dashboard` view returns data
- Intentionally failing a task results in DLQ entry
- After 3 failures, escalation_level = 2 (TPM)
- `get_dlq_summary()` returns accurate counts

## Notes
- Schema creation requires TPM to run SQL (Jr cannot CREATE TABLE)
- Retry poller can be added to existing executor service or run standalone
- Future: add Telegram webhook for L2+ escalations
- Future: integrate with step-level checkpointing (#1751) for granular recovery

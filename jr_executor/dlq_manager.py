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
    """Get database connection using federation secrets_loader."""
    import sys
    sys.path.insert(0, '/ganuda')
    from lib.secrets_loader import get_db_config
    return psycopg2.connect(**get_db_config())


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
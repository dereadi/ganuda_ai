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
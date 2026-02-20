# Jr Instruction: Add DLQ Methods to jr_queue_client.py

**Kanban**: #1750 (Executor DLQ Wiring — continued)
**Sacred Fire Priority**: 13
**Long Man Step**: BUILD (recursive — migration script created by #714, client methods skipped)

## Context

The DLQ table migration script was created by Jr #714. Now add DLQ convenience methods to the queue client.

## Steps

### Step 1: Add DLQ methods after get_my_workload

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

    def close(self):
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
        """Get Dead Letter Queue summary for monitoring."""
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
        """Re-queue a failed task by resetting its status to pending."""
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

    def close(self):
>>>>>>> REPLACE
```

## Verification

```text
python3 -c "
import sys; sys.path.insert(0, '/ganuda')
from jr_executor.jr_queue_client import JrQueueClient
c = JrQueueClient('test')
assert hasattr(c, 'get_dlq_summary'), 'Missing get_dlq_summary'
assert hasattr(c, 'requeue_from_dlq'), 'Missing requeue_from_dlq'
c.close()
print('OK: DLQ methods present in jr_queue_client.py')
"
```

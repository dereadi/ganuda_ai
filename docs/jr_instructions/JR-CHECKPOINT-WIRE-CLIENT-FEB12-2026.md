# Jr Instruction: Add Checkpoint Methods to jr_queue_client.py

**Kanban**: #1751 (Executor Checkpointing — continued)
**Sacred Fire Priority**: 13
**Long Man Step**: BUILD (recursive — migration script created by #715, client methods skipped)

## Context

The checkpoint tables migration script was created by Jr #715. Now add checkpoint save/load/cleanup methods to the queue client.

## Steps

### Step 1: Add checkpoint methods before close()

File: `jr_executor/jr_queue_client.py`

```python
<<<<<<< SEARCH
    def close(self):
        """Close database connection."""
        if self._conn and not self._conn.closed:
            self._conn.close()
=======
    def save_checkpoint(self, task_id: int, last_completed_step: int,
                        total_steps: int = None, checkpoint_data: Dict = None) -> bool:
        """Save a checkpoint for a task so it can resume on retry."""
        try:
            self._execute("""
                INSERT INTO jr_task_checkpoints
                    (task_id, last_completed_step, total_steps, checkpoint_data)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (task_id) DO UPDATE SET
                    last_completed_step = EXCLUDED.last_completed_step,
                    total_steps = COALESCE(EXCLUDED.total_steps, jr_task_checkpoints.total_steps),
                    checkpoint_data = EXCLUDED.checkpoint_data,
                    updated_at = NOW()
            """, (
                task_id,
                last_completed_step,
                total_steps,
                json.dumps(checkpoint_data) if checkpoint_data else None,
            ), fetch=False)
            return True
        except Exception as e:
            print(f"[JrQueue] Failed to save checkpoint for task {task_id}: {e}")
            return False

    def get_last_checkpoint(self, task_id: int) -> Optional[Dict]:
        """Get the last checkpoint for a task (for resume-from-failure)."""
        try:
            rows = self._execute("""
                SELECT last_completed_step, total_steps, checkpoint_data
                FROM jr_task_checkpoints
                WHERE task_id = %s
            """, (task_id,))
            if rows:
                return dict(rows[0])
            return None
        except Exception as e:
            print(f"[JrQueue] Failed to get checkpoint for task {task_id}: {e}")
            return None

    def cleanup_checkpoints(self, task_id: int) -> bool:
        """Remove checkpoints after a task completes successfully."""
        try:
            self._execute("""
                DELETE FROM jr_task_checkpoints WHERE task_id = %s
            """, (task_id,), fetch=False)
            return True
        except Exception as e:
            print(f"[JrQueue] Failed to cleanup checkpoints for task {task_id}: {e}")
            return False

    def close(self):
        """Close database connection."""
        if self._conn and not self._conn.closed:
            self._conn.close()
>>>>>>> REPLACE
```

## Verification

```text
python3 -c "
import sys; sys.path.insert(0, '/ganuda')
from jr_executor.jr_queue_client import JrQueueClient
c = JrQueueClient('test')
assert hasattr(c, 'save_checkpoint'), 'Missing save_checkpoint'
assert hasattr(c, 'get_last_checkpoint'), 'Missing get_last_checkpoint'
assert hasattr(c, 'cleanup_checkpoints'), 'Missing cleanup_checkpoints'
c.close()
print('OK: Checkpoint methods present in jr_queue_client.py')
"
```

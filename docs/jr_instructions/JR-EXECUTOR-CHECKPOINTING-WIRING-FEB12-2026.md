# Jr Instruction: Executor Checkpointing — Wire Step-Level Tracking + Resume

**Kanban**: #1751 (Executor P2: Step-Level Checkpointing + Crash Recovery)
**Sacred Fire Priority**: 13
**Story Points**: 13
**River Cycle**: RC-2026-02A
**Long Man Step**: BUILD
**Depends On**: #1750 (DLQ Wiring) — DLQ table must exist for escalation

## Context

The task executor already has two methods for step tracking that were **written but NEVER CALLED**:

- `_record_step_result()` at task_executor.py:2332 — records step outcomes to `jr_step_rewards` table
- `_step_already_succeeded()` at task_executor.py:2358 — checks if a step already passed (for retry idempotency)

These methods reference a `jr_step_rewards` table that **does not exist** in the database.

The `execute_steps()` method at task_executor.py:216 runs steps in a loop but:
- Does NOT call `_record_step_result()` after each step
- Does NOT call `_step_already_succeeded()` before each step
- Does NOT support resume-from-checkpoint on retry

This instruction creates the tables and wires the existing methods into the execution loop.

## Steps

### Step 1: Create Checkpoint Tables Migration

Create `/ganuda/scripts/migrations/create_checkpoint_tables.py`

```python
#!/usr/bin/env python3
"""Create step tracking and checkpoint tables for executor resume capability.

Kanban #1751 — Executor Checkpointing
Run once: python3 /ganuda/scripts/migrations/create_checkpoint_tables.py

For Seven Generations
"""

import sys
sys.path.insert(0, '/ganuda')
from lib.secrets_loader import get_db_config
import psycopg2

def create_tables():
    """Create step rewards and checkpoint tables."""
    db = get_db_config()
    conn = psycopg2.connect(**db)
    cur = conn.cursor()

    # Table 1: Step-level execution rewards (referenced by _record_step_result)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jr_step_rewards (
            id SERIAL PRIMARY KEY,
            task_id INTEGER NOT NULL,
            step_number INTEGER NOT NULL,
            step_type VARCHAR(50),
            target_file TEXT,
            step_content_hash VARCHAR(64),
            execution_result VARCHAR(20) NOT NULL DEFAULT 'pending',
            execution_time_ms INTEGER,
            error_detail TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(task_id, step_number)
        );

        CREATE INDEX IF NOT EXISTS idx_step_rewards_task
            ON jr_step_rewards(task_id);

        CREATE INDEX IF NOT EXISTS idx_step_rewards_result
            ON jr_step_rewards(execution_result);
    """)

    # Table 2: Task-level checkpoints (for resume-from-failure)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jr_task_checkpoints (
            id SERIAL PRIMARY KEY,
            task_id INTEGER NOT NULL,
            last_completed_step INTEGER NOT NULL DEFAULT 0,
            total_steps INTEGER,
            checkpoint_data JSONB,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(task_id)
        );

        CREATE INDEX IF NOT EXISTS idx_checkpoints_task
            ON jr_task_checkpoints(task_id);
    """)

    conn.commit()
    print("[Checkpoint Migration] Tables created: jr_step_rewards, jr_task_checkpoints")

    # Verify
    for table in ['jr_step_rewards', 'jr_task_checkpoints']:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"[Checkpoint Migration] {table}: {count} rows")

    cur.close()
    conn.close()

if __name__ == '__main__':
    create_tables()
    print("[Checkpoint Migration] Done — For Seven Generations")
```

### Step 2: Wire Step Recording into execute_steps Loop

File: `jr_executor/task_executor.py`

```python
<<<<<<< SEARCH
        for step in steps:
            result = self.execute(step)
            results.append(result)

            # Phase 10: Register completed step for potential rollback
            if result.get('success') and saga_tx and self.saga_manager:
=======
        for step_index, step in enumerate(steps):
            # Phase 11: Check if step already succeeded (retry idempotency)
            task_id = getattr(self, '_current_task_id', None)
            if task_id and self._step_already_succeeded(task_id, step_index):
                print(f"[CHECKPOINT] Step {step_index} already succeeded, skipping")
                results.append({'success': True, 'skipped': True, 'checkpoint_hit': True})
                continue

            import time as _time
            _step_start = _time.time()
            result = self.execute(step)
            _step_elapsed_ms = int((_time.time() - _step_start) * 1000)
            results.append(result)

            # Phase 11: Record step result for checkpoint tracking
            if task_id:
                self._record_step_result(
                    task_id=task_id,
                    step_number=step_index,
                    step_type=step.get('type', 'unknown'),
                    target_file=step.get('path', step.get('filepath', '')),
                    result=result,
                    execution_time_ms=_step_elapsed_ms,
                )

            # Phase 10: Register completed step for potential rollback
            if result.get('success') and saga_tx and self.saga_manager:
>>>>>>> REPLACE
```

### Step 3: Add Checkpoint Methods to jr_queue_client.py

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
        """
        Save a checkpoint for a task so it can resume on retry.

        Args:
            task_id: The task's database ID
            last_completed_step: Index of the last successfully completed step
            total_steps: Total number of steps in the task
            checkpoint_data: Optional metadata to store with the checkpoint

        Returns:
            True if checkpoint was saved
        """
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
        """
        Get the last checkpoint for a task (for resume-from-failure).

        Args:
            task_id: The task's database ID

        Returns:
            Dict with last_completed_step and checkpoint_data, or None
        """
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
        """
        Remove checkpoints after a task completes successfully.

        Args:
            task_id: The task's database ID

        Returns:
            True if cleanup succeeded
        """
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

After step 1, verify tables exist:

```text
python3 /ganuda/scripts/migrations/create_checkpoint_tables.py
```

After all steps, verify the wiring resolves:

```text
python3 -c "
import sys; sys.path.insert(0, '/ganuda')
from jr_executor.jr_queue_client import JrQueueClient
c = JrQueueClient('test')
print('save_checkpoint:', hasattr(c, 'save_checkpoint'))
print('get_last_checkpoint:', hasattr(c, 'get_last_checkpoint'))
print('cleanup_checkpoints:', hasattr(c, 'cleanup_checkpoints'))
c.close()
print('All checkpoint methods present')
"
```

## What This Does NOT Cover

- Full resume-from-failure in jr_queue_worker.py (Phase 2 — worker needs to call get_last_checkpoint and skip steps)
- Automatic checkpoint cleanup on task completion (needs worker integration)
- Step reward analytics dashboard in SAG
- MAGRPO reward signal integration (separate learning tracker)

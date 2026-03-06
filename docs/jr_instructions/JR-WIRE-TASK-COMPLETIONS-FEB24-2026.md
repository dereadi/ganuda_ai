# Jr Instruction: Wire jr_task_completions into Executor Pipeline

**Task ID**: #1888
**Priority**: 3 (SFP 25)
**Assigned Jr**: Software Engineer Jr.
**Target File**: `/ganuda/jr_executor/jr_queue_client.py`

## Objective

The `jr_task_completions` table exists but has ZERO rows. Wire `complete_task()` and `fail_task()` methods to INSERT a completion record after their existing UPDATE statements. This gives us analytics on Jr agent performance (success rates, durations, difficulty estimates).

## Table Schema Reference

```text
jr_task_completions:
  completion_id  SERIAL PRIMARY KEY
  task_id        VARCHAR(64) NOT NULL
  agent_id       VARCHAR(64) NOT NULL
  estimated_difficulty  DOUBLE PRECISION  (nullable)
  actual_duration       INTERVAL          (nullable)
  success               BOOLEAN DEFAULT true
  completed_at          TIMESTAMP DEFAULT now()
```

## Implementation

Two SEARCH/REPLACE edits in the same file.

---

File: `/ganuda/jr_executor/jr_queue_client.py`

### Edit 1: complete_task() — insert completion record after UPDATE

<<<<<<< SEARCH
            self._execute("""
                UPDATE jr_work_queue
                SET status = 'completed',
                    progress_percent = 100,
                    completed_at = NOW(),
                    result = %s,
                    artifacts = %s,
                    status_message = 'Task completed successfully'
                WHERE id = %s AND assigned_jr = %s
            """, (
                json.dumps(result) if result else None,
                processed_artifacts,
                task_id,
                self.jr_name
            ), fetch=False)
            return True
=======
            self._execute("""
                UPDATE jr_work_queue
                SET status = 'completed',
                    progress_percent = 100,
                    completed_at = NOW(),
                    result = %s,
                    artifacts = %s,
                    status_message = 'Task completed successfully'
                WHERE id = %s AND assigned_jr = %s
            """, (
                json.dumps(result) if result else None,
                processed_artifacts,
                task_id,
                self.jr_name
            ), fetch=False)

            # Record completion analytics
            try:
                self._execute("""
                    INSERT INTO jr_task_completions
                        (task_id, agent_id, actual_duration, success)
                    SELECT
                        id::text,
                        assigned_jr,
                        NOW() - started_at,
                        true
                    FROM jr_work_queue
                    WHERE id = %s AND assigned_jr = %s
                """, (task_id, self.jr_name), fetch=False)
            except Exception:
                pass  # completion tracking is non-critical

            return True
>>>>>>> REPLACE

### Edit 2: fail_task() — insert failure record after UPDATE

<<<<<<< SEARCH
            self._execute("""
                UPDATE jr_work_queue
                SET status = 'failed',
                    completed_at = NOW(),
                    error_message = %s,
                    result = %s,
                    status_message = 'Task failed'
                WHERE id = %s AND assigned_jr = %s
            """, (
                error_message,
                json.dumps(result) if result else None,
                task_id,
                self.jr_name
            ), fetch=False)
            return True
=======
            self._execute("""
                UPDATE jr_work_queue
                SET status = 'failed',
                    completed_at = NOW(),
                    error_message = %s,
                    result = %s,
                    status_message = 'Task failed'
                WHERE id = %s AND assigned_jr = %s
            """, (
                error_message,
                json.dumps(result) if result else None,
                task_id,
                self.jr_name
            ), fetch=False)

            # Record failure analytics
            try:
                self._execute("""
                    INSERT INTO jr_task_completions
                        (task_id, agent_id, actual_duration, success)
                    SELECT
                        id::text,
                        assigned_jr,
                        NOW() - started_at,
                        false
                    FROM jr_work_queue
                    WHERE id = %s AND assigned_jr = %s
                """, (task_id, self.jr_name), fetch=False)
            except Exception:
                pass  # failure tracking is non-critical

            return True
>>>>>>> REPLACE

## Verification

After applying edits, confirm with:

```text
python3 -c "import ast; ast.parse(open('/ganuda/jr_executor/jr_queue_client.py').read()); print('SYNTAX OK')"
```

Then verify by running a test task through the executor and checking:

```text
SELECT * FROM jr_task_completions ORDER BY completed_at DESC LIMIT 5;
```

## Design Notes

- Uses INSERT...SELECT from `jr_work_queue` to get `started_at` for duration calculation, avoiding an extra query
- Wrapped in try/except so completion tracking never blocks actual task completion
- `estimated_difficulty` left NULL for now — future enhancement can wire in council difficulty estimates from the task metadata
- `task_id` cast to text since `jr_work_queue.id` is integer but `jr_task_completions.task_id` is varchar(64)

# Jr Instruction: Executor P2 — Step-Level Checkpointing + Pre-Execution Guardrails

**Task ID:** EXECUTOR-P2-CHECKPOINT-GUARDRAILS-001
**Assigned:** Software Engineer Jr.
**Priority:** P2 (Medium — enables resume-from-failure and catches bad instructions early)
**Created:** 2026-02-03
**TPM:** Claude Opus 4.5
**Council Vote:** APPROVED 7/7 (audit hash: 38a517d5c204a4e7)
**Depends on:** EXECUTOR-P0-LOCKING-LIFECYCLE-001

---

## Context

When a Jr worker crashes or times out mid-task, all progress is lost. The task restarts from scratch on the next attempt. This wastes tokens and time, especially for multi-step tasks with 5+ file operations.

Additionally, some tasks fail immediately due to bad instruction files (missing import references, non-writable target paths, invalid JSON in parameters). These failures are predictable and should be caught before execution begins.

### Source Projects
- LangGraph `PostgresSaver` (step-level checkpointing to PostgreSQL)
- OpenAI Agents SDK (pre-execution guardrails and validation)

### Council Conditions (Incorporated)
- **Gecko (Performance):** Checkpoint writes should be batched — don't write a checkpoint for trivial steps.
- **Eagle Eye (Monitoring):** Checkpoint history must be queryable for debugging.
- **Turtle (7Gen):** Consider storage growth — implement checkpoint cleanup after task completion.

### Files to Modify
1. New SQL table: `jr_task_checkpoints`
2. `/ganuda/jr_executor/jr_queue_client.py` — Add checkpoint methods
3. `/ganuda/jr_executor/task_executor.py` — Add checkpoint calls after each step + pre-execution validation

---

## Step 1: Create Checkpoint Table

Run on bluefin (192.168.132.222) against `zammad_production`:

```sql
CREATE TABLE IF NOT EXISTS jr_task_checkpoints (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL,
    step_number INTEGER NOT NULL,
    step_type VARCHAR(50),
    step_description TEXT,
    step_result JSONB,
    files_written JSONB DEFAULT '[]',
    executor_state JSONB,
    checkpoint_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(task_id, step_number)
);

CREATE INDEX IF NOT EXISTS idx_checkpoints_task
    ON jr_task_checkpoints(task_id);

COMMENT ON TABLE jr_task_checkpoints IS 'Step-level checkpoints for Jr task execution. Enables resume-from-failure. Pattern: LangGraph PostgresSaver.';
COMMENT ON COLUMN jr_task_checkpoints.executor_state IS 'Serialized executor state at this checkpoint. Includes variables, partial results, and context needed to resume.';
COMMENT ON COLUMN jr_task_checkpoints.files_written IS 'JSONB array of file paths written up to this checkpoint. Used for saga rollback if needed.';
```

Verify:
```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "\d jr_task_checkpoints"
```

---

## Step 2: Add Checkpoint Methods to Queue Client

Modify: `/ganuda/jr_executor/jr_queue_client.py`

Add these methods to the `JrQueueClient` class:

```python
def save_checkpoint(self, task_id: int, step_number: int, step_type: str,
                    step_description: str, step_result: dict = None,
                    files_written: list = None, executor_state: dict = None) -> bool:
    """
    Save a checkpoint after completing a step.
    Uses UPSERT to handle re-execution of the same step.

    Args:
        task_id: The task's database ID
        step_number: Sequential step number (1-based)
        step_type: Type of step (file_write, command, api_call, etc.)
        step_description: Human-readable description of what was done
        step_result: Result data from the step
        files_written: Cumulative list of files written so far
        executor_state: Serialized state needed to resume from this point

    Returns:
        True if checkpoint was saved
    """
    try:
        self._execute("""
            INSERT INTO jr_task_checkpoints
                (task_id, step_number, step_type, step_description,
                 step_result, files_written, executor_state)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (task_id, step_number) DO UPDATE SET
                step_type = EXCLUDED.step_type,
                step_description = EXCLUDED.step_description,
                step_result = EXCLUDED.step_result,
                files_written = EXCLUDED.files_written,
                executor_state = EXCLUDED.executor_state,
                checkpoint_at = NOW()
        """, (
            task_id, step_number, step_type, step_description,
            json.dumps(step_result) if step_result else None,
            json.dumps(files_written) if files_written else None,
            json.dumps(executor_state) if executor_state else None
        ), fetch=False)
        return True
    except Exception as e:
        print(f"[JrQueue] Failed to save checkpoint: {e}")
        return False

def get_last_checkpoint(self, task_id: int) -> Optional[Dict]:
    """
    Get the last checkpoint for a task (for resume-from-failure).

    Args:
        task_id: The task's database ID

    Returns:
        Checkpoint dict or None if no checkpoints exist
    """
    try:
        rows = self._execute("""
            SELECT * FROM jr_task_checkpoints
            WHERE task_id = %s
            ORDER BY step_number DESC
            LIMIT 1
        """, (task_id,))
        return dict(rows[0]) if rows else None
    except Exception as e:
        print(f"[JrQueue] Failed to get checkpoint: {e}")
        return None

def cleanup_checkpoints(self, task_id: int) -> int:
    """
    Remove checkpoints after task completes successfully.
    Called to manage storage growth (Turtle 7Gen condition).

    Args:
        task_id: The task's database ID

    Returns:
        Number of checkpoints removed
    """
    try:
        return self._execute(
            "DELETE FROM jr_task_checkpoints WHERE task_id = %s",
            (task_id,),
            fetch=False
        )
    except Exception as e:
        print(f"[JrQueue] Failed to cleanup checkpoints: {e}")
        return 0
```

---

## Step 3: Add Pre-Execution Guardrails to Task Executor

Modify: `/ganuda/jr_executor/task_executor.py`

Read the current file first to understand its structure, then add a `validate_before_execution()` method.

Add this method to the `TaskExecutor` class:

```python
def validate_before_execution(self, task: dict) -> dict:
    """
    Pre-execution guardrails: validate task before running.
    Catches predictable failures before wasting tokens.

    Returns:
        dict with 'valid': bool, 'errors': list, 'warnings': list
    """
    errors = []
    warnings = []

    # 1. Check instruction file exists (if specified)
    instruction_file = task.get('instruction_file')
    if instruction_file:
        import os
        if not os.path.exists(instruction_file):
            errors.append(f"Instruction file not found: {instruction_file}")
        elif os.path.getsize(instruction_file) == 0:
            errors.append(f"Instruction file is empty: {instruction_file}")

    # 2. Check instruction content is non-empty
    instruction_content = task.get('instruction_content')
    if not instruction_file and not instruction_content:
        errors.append("No instruction file or content provided")

    # 3. Validate parameters JSON (if present)
    parameters = task.get('parameters')
    if parameters:
        if isinstance(parameters, str):
            try:
                import json
                json.loads(parameters)
            except json.JSONDecodeError as e:
                errors.append(f"Invalid parameters JSON: {e}")

    # 4. Check use_rlm flag vs RLM availability
    if task.get('use_rlm'):
        rlm_executor_path = '/ganuda/lib/rlm_executor.py'
        import os
        if not os.path.exists(rlm_executor_path):
            errors.append(f"use_rlm=True but RLM executor not found: {rlm_executor_path}")

    # 5. Check target paths in instruction content (basic check)
    if instruction_content:
        import re
        paths = re.findall(r'/ganuda/[\w/.-]+', str(instruction_content))
        for path in paths[:5]:  # Check first 5 paths only
            import os
            parent = os.path.dirname(path)
            if parent and not os.path.exists(parent):
                warnings.append(f"Parent directory doesn't exist: {parent}")

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }
```

Then in the `process_queue_task()` method (or equivalent), call this validation before executing:

```python
# Pre-execution guardrails
validation = self.validate_before_execution(task)
if not validation['valid']:
    error_msg = "Pre-execution validation failed: " + "; ".join(validation['errors'])
    print(f"[TaskExecutor] {error_msg}")
    return {
        'success': False,
        'error': error_msg,
        'validation_errors': validation['errors'],
        'validation_warnings': validation['warnings']
    }

if validation['warnings']:
    print(f"[TaskExecutor] Warnings: {validation['warnings']}")
```

---

## Step 4: Add Checkpoint Calls to Worker

Modify: `/ganuda/jr_executor/jr_queue_worker.py`

### 4A: After successful task completion (before calling `complete_task`)

Add checkpoint cleanup:

```python
# Clean up checkpoints after successful completion (Turtle 7Gen: manage storage)
self.client.cleanup_checkpoints(task['id'])
```

### 4B: Check for existing checkpoint on task start

Before calling `self.executor.process_queue_task(task)`, check if a checkpoint exists:

```python
# Check for existing checkpoint (resume-from-failure)
checkpoint = self.client.get_last_checkpoint(task['id'])
if checkpoint:
    print(f"[{self.jr_name}] Found checkpoint at step {checkpoint['step_number']} for task {task['id']}")
    task['_resume_from_step'] = checkpoint['step_number']
    task['_checkpoint_state'] = checkpoint.get('executor_state')
```

**Note:** The task executor will need to honor `_resume_from_step` by skipping already-completed steps. This is a future enhancement — for now, logging the checkpoint existence is sufficient to validate the infrastructure.

---

## Step 5: Verify

```bash
# 1. Verify table exists
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "\d jr_task_checkpoints"

# 2. Test guardrails with a task that has a missing instruction file
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
INSERT INTO jr_work_queue (task_id, title, description, assigned_jr, priority, status, instruction_file, use_rlm)
VALUES ('TEST-GUARD-001', 'Test Guardrails', 'Should fail pre-execution validation', 'Software Engineer Jr.', 3, 'pending',
'/nonexistent/path/instruction.md', true);
"

# 3. Wait for worker, then verify it failed with validation error (not execution error)
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT id, status, error_message FROM jr_work_queue WHERE task_id = 'TEST-GUARD-001';
"
# Expected: status=failed, error_message contains 'Pre-execution validation failed'

# 4. Test checkpoint save/retrieve
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
INSERT INTO jr_task_checkpoints (task_id, step_number, step_type, step_description)
VALUES (999, 1, 'test', 'Test checkpoint');
SELECT * FROM jr_task_checkpoints WHERE task_id = 999;
DELETE FROM jr_task_checkpoints WHERE task_id = 999;
"
```

---

## Acceptance Criteria

1. `jr_task_checkpoints` table exists with UNIQUE(task_id, step_number) constraint
2. `save_checkpoint()` uses UPSERT (handles re-execution)
3. `get_last_checkpoint()` returns most recent checkpoint for resume
4. `cleanup_checkpoints()` removes checkpoints after success (Turtle storage condition)
5. `validate_before_execution()` catches: missing instruction file, empty content, invalid JSON, missing RLM executor
6. Pre-execution validation runs BEFORE any LLM calls or file operations
7. Validation failures reported clearly in task error_message
8. Checkpoint history queryable via SQL (Eagle Eye monitoring condition)
9. No checkpoint writes for trivial steps (Gecko performance condition) — handled by caller logic
10. All queries use parameterized placeholders

---

## Rollback

```sql
DROP TABLE IF EXISTS jr_task_checkpoints;
```

Remove `validate_before_execution()` method and checkpoint calls. No other tables affected.

---

*For Seven Generations*
*Cherokee AI Federation — Jr Executor Architecture Team*

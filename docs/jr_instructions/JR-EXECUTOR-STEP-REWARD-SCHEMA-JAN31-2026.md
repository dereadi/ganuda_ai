# Jr Instruction: Step-Level Reward Schema & Tracking Infrastructure

**Task ID:** EXECUTOR-STEP-REWARD-001
**Assigned To:** Software Engineer Jr
**Priority:** P1
**Created:** January 31, 2026
**Depends On:** None (standalone foundation)
**Estimated Steps:** 8

---

## Objective

Implement the database schema and basic tracking infrastructure for step-level rewards in the Jr executor. This is the foundation that enables all subsequent RL reward improvements (implicit PRM, step-aware retry, multi-agent credit assignment).

---

## Context

The Jan 30 postmortem (KB-JR-EXECUTOR-SEARCH-REPLACE-POSTMORTEM-JAN30-2026) identified that our binary pass/fail reward signal causes:
1. No credit assignment between steps
2. Retry mechanism re-applies ALL steps (causing duplicates)
3. No learning signal for which step patterns work

This task creates the schema and tracking hooks. It does NOT implement the reward model itself (that's Phase 1 of the ultrathink, pending Research Jr analysis).

---

## Steps

### Step 1: Create migration SQL

**File:** `/ganuda/sql/jr_step_rewards_schema.sql`

```sql
-- Jr Step-Level Reward Tracking
-- Part of RL Reward Architecture Upgrade (Ultrathink Jan 31, 2026)

-- Step execution log with reward placeholders
CREATE TABLE IF NOT EXISTS jr_step_rewards (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL,
    step_number INTEGER NOT NULL,
    step_type VARCHAR(30) NOT NULL,
    target_file VARCHAR(500),
    step_content_hash VARCHAR(64),
    execution_result VARCHAR(20) DEFAULT 'pending',
    implicit_reward FLOAT,
    verified_outcome VARCHAR(20),
    retry_decision VARCHAR(20),
    execution_time_ms INTEGER,
    error_detail TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(task_id, step_number)
);

-- Exploration tracking for curiosity-driven task selection
CREATE TABLE IF NOT EXISTS jr_exploration_log (
    id SERIAL PRIMARY KEY,
    jr_type VARCHAR(50) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    novelty_score FLOAT,
    curiosity_bonus FLOAT,
    task_outcome VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_step_rewards_task ON jr_step_rewards(task_id);
CREATE INDEX IF NOT EXISTS idx_step_rewards_type ON jr_step_rewards(step_type);
CREATE INDEX IF NOT EXISTS idx_step_rewards_outcome ON jr_step_rewards(execution_result);
CREATE INDEX IF NOT EXISTS idx_exploration_jr ON jr_exploration_log(jr_type, created_at);
```

### Step 2: Run migration on bluefin

```bash
psql -h 192.168.132.222 -U claude -d zammad_production -f /ganuda/sql/jr_step_rewards_schema.sql
```

Verify tables exist:
```bash
psql -h 192.168.132.222 -U claude -d zammad_production -c "\dt jr_step*"
psql -h 192.168.132.222 -U claude -d zammad_production -c "\dt jr_exploration*"
```

### Step 3: Add step tracking to task_executor.py

**File:** `/ganuda/jr_executor/task_executor.py`

Add a new method `_record_step_result` that logs each step execution to `jr_step_rewards`:

<<<<<<< SEARCH
    def _audit_file_operation(self, operation: str, path: str, size: int, backup_path: str):
=======
    def _record_step_result(self, task_id: int, step_number: int, step_type: str,
                            target_file: str, result: dict, execution_time_ms: int):
        """Record step-level execution result for reward tracking."""
        try:
            import hashlib
            step_hash = hashlib.sha256(
                f"{task_id}:{step_number}:{step_type}:{target_file}".encode()
            ).hexdigest()

            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO jr_step_rewards
                    (task_id, step_number, step_type, target_file, step_content_hash,
                     execution_result, execution_time_ms, error_detail)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (task_id, step_number) DO UPDATE SET
                    execution_result = EXCLUDED.execution_result,
                    execution_time_ms = EXCLUDED.execution_time_ms,
                    error_detail = EXCLUDED.error_detail,
                    updated_at = NOW()
            """, (
                task_id, step_number, step_type, target_file, step_hash,
                'success' if result.get('success') else 'failed',
                execution_time_ms,
                result.get('error', None)
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            # Step recording must never block task execution
            logging.getLogger(__name__).warning(f"Step recording failed: {e}")

    def _audit_file_operation(self, operation: str, path: str, size: int, backup_path: str):
>>>>>>> REPLACE
```

### Step 4: Wire step tracking into _execute_search_replace

**File:** `/ganuda/jr_executor/task_executor.py`

After each SEARCH/REPLACE execution, call `_record_step_result`. Add timing around the editor call:

```python
import time
start_time = time.time()
result = editor.apply_search_replace(filepath, search_text, replace_text)
elapsed_ms = int((time.time() - start_time) * 1000)

# Record step result
if hasattr(self, '_record_step_result') and hasattr(self, '_current_task_id'):
    self._record_step_result(
        task_id=self._current_task_id,
        step_number=self._current_step_number,
        step_type='search_replace',
        target_file=filepath,
        result=result,
        execution_time_ms=elapsed_ms
    )
```

### Step 5: Wire step tracking into bash execution

Similarly wire `_record_step_result` into the bash command execution path, recording step_type='bash'.

### Step 6: Add step_content_hash for idempotency

The `step_content_hash` in the schema enables future idempotency checks. Before executing a step, the executor can check:

```python
def _step_already_succeeded(self, task_id, step_number):
    """Check if this step already succeeded (for retry idempotency)."""
    try:
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()
        cur.execute("""
            SELECT execution_result FROM jr_step_rewards
            WHERE task_id = %s AND step_number = %s AND execution_result = 'success'
        """, (task_id, step_number))
        result = cur.fetchone()
        conn.close()
        return result is not None
    except Exception:
        return False  # On error, assume not succeeded (safe default)
```

This is the **foundation for fixing Postmortem Root Cause #4** (duplicate content from retries).

### Step 7: Add task_id tracking to executor

Ensure `self._current_task_id` and `self._current_step_number` are set during task execution so step recording knows which task/step it's working on.

### Step 8: Verify with a test task

Queue a simple test task and verify that `jr_step_rewards` receives entries:

```sql
SELECT task_id, step_number, step_type, execution_result, execution_time_ms
FROM jr_step_rewards
ORDER BY created_at DESC LIMIT 10;
```

---

## Output Artifacts

1. `/ganuda/sql/jr_step_rewards_schema.sql` — Migration file
2. Modified `/ganuda/jr_executor/task_executor.py` — Step tracking hooks
3. Populated `jr_step_rewards` table with at least one test run

---

## Success Criteria

- Both tables created on bluefin
- Step recording works for both bash and search_replace step types
- Step recording failures never block task execution (isolated try/except)
- At least one task run produces entries in jr_step_rewards
- `_step_already_succeeded` query returns correct results

---

## Security Notes

- `step_content_hash` is a SHA-256 of step metadata, NOT step content (no PII)
- `error_detail` may contain file paths — same security posture as jr_work_queue.error_message
- No new credentials or secrets required

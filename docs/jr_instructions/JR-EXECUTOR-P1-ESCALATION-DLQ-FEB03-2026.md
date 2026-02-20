# Jr Instruction: Executor P1 — Structured Escalation + Dead Letter Queue

**Task ID:** EXECUTOR-P1-ESCALATION-DLQ-001
**Assigned:** Software Engineer Jr.
**Priority:** P1 (High — enables TPM oversight and stops infinite retry loops)
**Created:** 2026-02-03
**TPM:** Claude Opus 4.5
**Council Vote:** APPROVED 7/7 (audit hash: 38a517d5c204a4e7)
**Depends on:** EXECUTOR-P0-LOCKING-LIFECYCLE-001

---

## Context

When a Jr hits unrecoverable errors (command timeouts, import failures, schema mismatches), it currently retries in a loop with no way to escalate to the TPM or human operator. Task #548 (VA Linking Verify, Feb 2 2026) demonstrated this — it entered a timeout/retry loop with no escape hatch.

This instruction adds two complementary patterns:
- **Structured Escalation** — Jr packages failure context into an escalation record routed to the TPM via Telegram alert
- **Dead Letter Queue (DLQ)** — Tasks that fail 3 times move to a DLQ table instead of cycling forever

### Source Projects
- OpenAI Agents SDK (Handoffs pattern for structured escalation)
- Celery (Dead Letter Queue pattern for failed task routing)

### Council Conditions (Incorporated)
- **Crawdad (Security):** Parameterized queries only. Escalation records must not expose raw credentials or tokens.
- **Eagle Eye (Monitoring):** DLQ entries must be visible in admin dashboard or Telegram alerts.
- **Peace Chief (Consensus):** Implement rollback plan — ability to move DLQ tasks back to main queue.

### Files to Modify
1. `/ganuda/jr_executor/jr_queue_client.py` — Add `escalate_task()` and `move_to_dlq()` methods
2. `/ganuda/jr_executor/jr_queue_worker.py` — Add retry counter and escalation logic
3. New SQL table: `jr_escalation_queue` and `jr_dead_letter_queue`

---

## Step 1: Create Database Tables

Run on bluefin (192.168.132.222) against `zammad_production`:

```sql
-- Escalation Queue: Tasks that need TPM or human attention
CREATE TABLE IF NOT EXISTS jr_escalation_queue (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES jr_work_queue(id),
    escalation_type VARCHAR(50) NOT NULL DEFAULT 'unrecoverable_error',
    assigned_jr VARCHAR(255),
    error_message TEXT,
    error_context JSONB,
    retry_count INTEGER DEFAULT 0,
    original_instruction_file TEXT,
    suggested_action TEXT,
    escalated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolved_by VARCHAR(255),
    resolution_notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_escalation_unresolved
    ON jr_escalation_queue(escalated_at)
    WHERE resolved_at IS NULL;

COMMENT ON TABLE jr_escalation_queue IS 'Tasks escalated to TPM or human operator for intervention. Pattern: OpenAI Agents SDK Handoffs.';

-- Dead Letter Queue: Tasks that failed too many times
CREATE TABLE IF NOT EXISTS jr_dead_letter_queue (
    id SERIAL PRIMARY KEY,
    original_task_id INTEGER NOT NULL,
    task_title VARCHAR(500),
    assigned_jr VARCHAR(255),
    instruction_file TEXT,
    instruction_content TEXT,
    parameters JSONB,
    failure_history JSONB NOT NULL DEFAULT '[]',
    total_attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    moved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    requeued_at TIMESTAMPTZ,
    requeued_by VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_dlq_pending
    ON jr_dead_letter_queue(moved_at)
    WHERE requeued_at IS NULL;

COMMENT ON TABLE jr_dead_letter_queue IS 'Tasks that failed 3+ times. Can be requeued after TPM review. Pattern: Celery DLQ.';
```

Verify:
```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "\dt jr_escalation_queue; \dt jr_dead_letter_queue"
```

---

## Step 2: Add Escalation and DLQ Methods to Queue Client

Modify: `/ganuda/jr_executor/jr_queue_client.py`

Add these methods to the `JrQueueClient` class (after the `block_task` method):

```python
def escalate_task(self, task_id: int, error_message: str, error_context: dict = None,
                  suggested_action: str = None) -> bool:
    """
    Escalate a task to the TPM/human review queue.
    Called when Jr hits an unrecoverable error that needs human intervention.

    Args:
        task_id: The task's database ID
        error_message: What went wrong
        error_context: Additional context (stack trace, partial results, etc.)
        suggested_action: What the Jr thinks should happen next

    Returns:
        True if escalation was recorded
    """
    try:
        # Get task details for escalation record
        task_rows = self._execute(
            "SELECT instruction_file, title FROM jr_work_queue WHERE id = %s",
            (task_id,)
        )
        instruction_file = task_rows[0].get('instruction_file') if task_rows else None

        # Sanitize error_context: remove any credential-like values
        safe_context = {}
        if error_context:
            for k, v in error_context.items():
                v_str = str(v)
                if any(secret in k.lower() for secret in ['password', 'token', 'secret', 'key', 'credential']):
                    safe_context[k] = '[REDACTED]'
                elif any(secret in v_str.lower() for secret in ['password=', 'token=', 'bearer ']):
                    safe_context[k] = '[REDACTED - contains credential]'
                else:
                    safe_context[k] = v

        # Count previous attempts
        retry_rows = self._execute(
            "SELECT COUNT(*) as cnt FROM jr_escalation_queue WHERE task_id = %s",
            (task_id,)
        )
        retry_count = retry_rows[0]['cnt'] if retry_rows else 0

        self._execute("""
            INSERT INTO jr_escalation_queue
                (task_id, escalation_type, assigned_jr, error_message,
                 error_context, retry_count, original_instruction_file, suggested_action)
            VALUES (%s, 'unrecoverable_error', %s, %s, %s, %s, %s, %s)
        """, (
            task_id, self.jr_name, error_message,
            json.dumps(safe_context) if safe_context else None,
            retry_count, instruction_file, suggested_action
        ), fetch=False)

        # Mark the task as blocked
        self._execute("""
            UPDATE jr_work_queue
            SET status = 'blocked',
                status_message = %s
            WHERE id = %s AND assigned_jr = %s
        """, (
            f"ESCALATED: {error_message[:200]}",
            task_id, self.jr_name
        ), fetch=False)

        print(f"[JrQueue] Task {task_id} escalated to TPM: {error_message[:100]}")
        return True
    except Exception as e:
        print(f"[JrQueue] Failed to escalate task {task_id}: {e}")
        return False

def move_to_dlq(self, task_id: int, failure_history: list, last_error: str) -> bool:
    """
    Move a repeatedly failing task to the Dead Letter Queue.
    Called when retry_count >= MAX_RETRIES.

    Args:
        task_id: The task's database ID
        failure_history: List of dicts with error details from each attempt
        last_error: Most recent error message

    Returns:
        True if task was moved to DLQ
    """
    try:
        # Get full task details before moving
        task_rows = self._execute(
            """SELECT id, title, instruction_file, instruction_content,
                      parameters, assigned_jr
               FROM jr_work_queue WHERE id = %s""",
            (task_id,)
        )
        if not task_rows:
            print(f"[JrQueue] Task {task_id} not found for DLQ move")
            return False

        task = task_rows[0]

        # Insert into DLQ
        self._execute("""
            INSERT INTO jr_dead_letter_queue
                (original_task_id, task_title, assigned_jr,
                 instruction_file, instruction_content, parameters,
                 failure_history, total_attempts, last_error)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            task_id, task.get('title'), task.get('assigned_jr'),
            task.get('instruction_file'), task.get('instruction_content'),
            json.dumps(task.get('parameters')) if task.get('parameters') else None,
            json.dumps(failure_history), len(failure_history), last_error
        ), fetch=False)

        # Mark original task as failed with DLQ reference
        self._execute("""
            UPDATE jr_work_queue
            SET status = 'failed',
                completed_at = NOW(),
                error_message = %s,
                status_message = 'Moved to Dead Letter Queue after repeated failures'
            WHERE id = %s
        """, (
            f"DLQ: {last_error[:500]}",
            task_id
        ), fetch=False)

        print(f"[JrQueue] Task {task_id} moved to DLQ after {len(failure_history)} failures")
        return True
    except Exception as e:
        print(f"[JrQueue] Failed to move task {task_id} to DLQ: {e}")
        return False

def requeue_from_dlq(self, dlq_id: int, requeued_by: str = "TPM") -> bool:
    """
    Move a task from DLQ back to the main queue for retry.
    Used by TPM after fixing the underlying issue.

    Args:
        dlq_id: The DLQ entry ID
        requeued_by: Who authorized the requeue

    Returns:
        True if task was requeued
    """
    try:
        dlq_rows = self._execute(
            "SELECT * FROM jr_dead_letter_queue WHERE id = %s AND requeued_at IS NULL",
            (dlq_id,)
        )
        if not dlq_rows:
            return False

        dlq = dlq_rows[0]

        # Reset the original task to pending
        self._execute("""
            UPDATE jr_work_queue
            SET status = 'pending',
                error_message = NULL,
                status_message = %s,
                started_at = NULL,
                completed_at = NULL,
                progress_percent = 0
            WHERE id = %s
        """, (
            f"Requeued from DLQ by {requeued_by}",
            dlq['original_task_id']
        ), fetch=False)

        # Mark DLQ entry as requeued
        self._execute("""
            UPDATE jr_dead_letter_queue
            SET requeued_at = NOW(), requeued_by = %s
            WHERE id = %s
        """, (requeued_by, dlq_id), fetch=False)

        print(f"[JrQueue] DLQ entry {dlq_id} requeued (task {dlq['original_task_id']})")
        return True
    except Exception as e:
        print(f"[JrQueue] Failed to requeue DLQ entry {dlq_id}: {e}")
        return False
```

**Important:** Add `import json` at the top of `jr_queue_client.py` if not already present.

---

## Step 3: Add Retry Counter and Escalation Logic to Worker

Modify: `/ganuda/jr_executor/jr_queue_worker.py`

### 3A: Add configuration constant (after existing constants)

```python
MAX_RETRIES = 3  # Move to DLQ after this many failures
```

### 3B: Add retry tracking dict to __init__

Add after `self.current_task = None`:

```python
self.failure_counts = {}  # {task_id: [error1, error2, ...]}
```

### 3C: Modify the task failure handling

In the `run()` method, replace the current failure handling blocks. When a task fails, instead of just marking it failed, check the retry count:

After the existing `self.client.fail_task(task['id'], error_msg, result)` call (line 158), wrap it with retry logic:

```python
                        else:
                            error_msg = result.get('error', 'Unknown error')
                            print(f"[{self.jr_name}] Task failed: {error_msg}")

                            # Track failure for DLQ logic
                            tid = task['id']
                            if tid not in self.failure_counts:
                                self.failure_counts[tid] = []
                            self.failure_counts[tid].append({
                                'error': error_msg,
                                'timestamp': datetime.now().isoformat(),
                                'attempt': len(self.failure_counts[tid]) + 1
                            })

                            if len(self.failure_counts[tid]) >= MAX_RETRIES:
                                # Move to Dead Letter Queue
                                print(f"[{self.jr_name}] Task {tid} failed {MAX_RETRIES} times. Moving to DLQ.")
                                self.client.move_to_dlq(
                                    tid,
                                    failure_history=self.failure_counts[tid],
                                    last_error=error_msg
                                )
                                del self.failure_counts[tid]
                            else:
                                # Escalate if error looks unrecoverable
                                unrecoverable_keywords = ['import', 'module', 'schema', 'permission', 'not found']
                                if any(kw in error_msg.lower() for kw in unrecoverable_keywords):
                                    self.client.escalate_task(
                                        tid, error_msg,
                                        error_context={'result': str(result)[:1000]},
                                        suggested_action='Check instruction file for import/path errors'
                                    )
                                else:
                                    # Regular failure — mark and let it retry on next poll
                                    self.client.fail_task(tid, error_msg, result)
```

### 3D: Similarly update the exception handler (around line 159-167)

Replace the bare exception handler for task execution errors:

```python
                    except Exception as task_error:
                        error_msg = f"Task execution error: {task_error}"
                        print(f"[{self.jr_name}] {error_msg}")
                        traceback.print_exc()

                        tid = task['id']
                        if tid not in self.failure_counts:
                            self.failure_counts[tid] = []
                        self.failure_counts[tid].append({
                            'error': error_msg,
                            'timestamp': datetime.now().isoformat(),
                            'attempt': len(self.failure_counts[tid]) + 1
                        })

                        if len(self.failure_counts[tid]) >= MAX_RETRIES:
                            self.client.move_to_dlq(
                                tid,
                                failure_history=self.failure_counts[tid],
                                last_error=error_msg
                            )
                            del self.failure_counts[tid]
                        else:
                            try:
                                self.client.escalate_task(
                                    tid, error_msg,
                                    error_context={'traceback': traceback.format_exc()[:2000]},
                                    suggested_action='Execution exception — review traceback'
                                )
                            except Exception as esc_error:
                                print(f"[{self.jr_name}] Escalation also failed: {esc_error}")
                                try:
                                    self.client.fail_task(tid, error_msg)
                                except:
                                    pass
```

---

## Step 4: Add Telegram Alert for Escalations (Optional Enhancement)

If the Telegram bot is available, add a notification when tasks are escalated. Create a small helper at the top of `jr_queue_worker.py`:

```python
def _send_escalation_alert(task_title: str, error_msg: str, task_id: int):
    """Send Telegram alert to TPM about escalated task."""
    try:
        import requests
        requests.post(
            "http://localhost:8443/api/alert",
            json={
                "level": "warning",
                "source": "jr-executor",
                "message": f"⚠️ Task Escalated: {task_title}\nTask ID: {task_id}\nError: {error_msg[:200]}"
            },
            timeout=5
        )
    except Exception:
        pass  # Don't fail the worker if alerting fails
```

Call this after `self.client.escalate_task()` succeeds.

**Note:** This is optional. If the Telegram alert endpoint isn't available, skip this step. The escalation is still recorded in the database.

---

## Step 5: Verify

```bash
# 1. Verify tables exist
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "\d jr_escalation_queue; \d jr_dead_letter_queue"

# 2. Test escalation (queue a task that will fail)
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
INSERT INTO jr_work_queue (task_id, title, description, assigned_jr, priority, status, instruction_content, use_rlm)
VALUES ('TEST-ESC-001', 'Test Escalation', 'This task should fail and escalate', 'Software Engineer Jr.', 3, 'pending',
'Step 1: Import nonexistent_module_that_does_not_exist', false);
"

# 3. Wait for worker to process, then check escalation queue
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT id, task_id, error_message, escalated_at FROM jr_escalation_queue ORDER BY escalated_at DESC LIMIT 5;
"

# 4. Check DLQ (after 3 failures)
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT id, original_task_id, task_title, total_attempts, last_error, moved_at FROM jr_dead_letter_queue ORDER BY moved_at DESC LIMIT 5;
"
```

---

## Acceptance Criteria

1. `jr_escalation_queue` table exists with correct schema
2. `jr_dead_letter_queue` table exists with correct schema
3. `escalate_task()` creates escalation record and marks task as blocked
4. `move_to_dlq()` moves task to DLQ after 3 failures
5. `requeue_from_dlq()` allows TPM to return tasks to main queue (Peace Chief rollback condition)
6. Credential redaction in escalation context (Crawdad security condition)
7. Escalation and DLQ events visible in database queries (Eagle Eye monitoring condition)
8. Worker stops infinite retry loops — tasks either escalate or go to DLQ
9. All queries use parameterized placeholders (no SQL injection)
10. Optional: Telegram alert fires on escalation

---

## Rollback

To revert: DROP the two new tables and restore the original `jr_queue_worker.py` failure handling (simple `fail_task()` call). No other tables are modified.

```sql
DROP TABLE IF EXISTS jr_escalation_queue;
DROP TABLE IF EXISTS jr_dead_letter_queue;
```

---

*For Seven Generations*
*Cherokee AI Federation — Jr Executor Architecture Team*

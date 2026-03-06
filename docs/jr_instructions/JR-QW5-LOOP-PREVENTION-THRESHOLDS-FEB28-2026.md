# QW-5: Loop Prevention Thresholds in Jr Executor

**Kanban**: #1911
**Priority**: P1 — Reliability Quick Win (Legion adoption)
**Assigned**: Software Engineer Jr.

---

## Context

Currently tasks that fail repeatedly keep retrying (MAX_RETRIES=2 per attempt, but the queue worker can re-claim indefinitely). Legion uses MAX_ATTEMPTS_PER_LAYER=3, MAX_ESCALATIONS=2, then permanently_failed. We add an `escalation_count` field to jr_work_queue and check it before claiming tasks. After 3 total failures, mark as `permanently_failed` instead of re-queuing.

## Step 1: Add escalation_count column

This is a database migration. The Jr executor cannot run DDL directly, so this step documents the SQL that TPM will apply.

Note: TPM must run this SQL manually on bluefin:

```text
ALTER TABLE jr_work_queue ADD COLUMN IF NOT EXISTS escalation_count INTEGER DEFAULT 0;
```

## Step 2: Add loop prevention check in task_executor.py

File: `/ganuda/jr_executor/task_executor.py`

````text
<<<<<<< SEARCH
    # Phase 11: Self-Healing Retry Configuration
    # Council vote 6428bcda34efc7f9 — Turtle: bounded retry for sustainability
    MAX_RETRIES = 2
=======
    # Phase 11: Self-Healing Retry Configuration
    # Council vote 6428bcda34efc7f9 — Turtle: bounded retry for sustainability
    MAX_RETRIES = 2

    # QW-5: Loop Prevention (Legion adoption, kanban #1911)
    # After this many total failures, mark permanently_failed
    MAX_ESCALATION_COUNT = 3
>>>>>>> REPLACE
````

## Step 3: Add escalation increment method

File: `/ganuda/jr_executor/task_executor.py`

````text
<<<<<<< SEARCH
    def __init__(self, jr_type: str = "it_triad_jr"):
=======
    def increment_escalation(self, task_id: int) -> int:
        """Increment escalation_count and return new value.
        QW-5: Loop Prevention (kanban #1911).
        """
        import psycopg2
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            cur.execute("""
                UPDATE jr_work_queue
                SET escalation_count = COALESCE(escalation_count, 0) + 1
                WHERE id = %s
                RETURNING escalation_count
            """, (task_id,))
            row = cur.fetchone()
            conn.commit()
            conn.close()
            return row[0] if row else 0
        except Exception:
            return 0

    def check_permanently_failed(self, task_id: int) -> bool:
        """Check if task has exceeded max escalations.
        If so, mark permanently_failed and return True.
        QW-5: Loop Prevention (kanban #1911).
        """
        import psycopg2
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            cur.execute("""
                SELECT escalation_count FROM jr_work_queue WHERE id = %s
            """, (task_id,))
            row = cur.fetchone()
            if row and (row[0] or 0) >= self.MAX_ESCALATION_COUNT:
                cur.execute("""
                    UPDATE jr_work_queue
                    SET status = 'permanently_failed',
                        error_message = 'Exceeded max escalation count (' || %s || '). Loop prevention triggered.'
                    WHERE id = %s
                """, (str(self.MAX_ESCALATION_COUNT), task_id))
                conn.commit()
                conn.close()
                return True
            conn.close()
            return False
        except Exception:
            return False

    def __init__(self, jr_type: str = "it_triad_jr"):
>>>>>>> REPLACE
````

## Verification

After applying:
1. `grep 'MAX_ESCALATION_COUNT' /ganuda/jr_executor/task_executor.py` shows the constant (value: 3)
2. `grep 'increment_escalation\|check_permanently_failed' /ganuda/jr_executor/task_executor.py` shows both methods
3. Methods use COALESCE for backward compatibility (column may be NULL on old rows)
4. Tasks exceeding 3 failures get status='permanently_failed' with descriptive error_message

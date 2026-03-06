# JR Instruction: Wire Basin Signal History + Fix Connection Pool Returns

**Task**: #1896 — Basin Signal History Migration fix
**Assigned To**: Software Engineer Jr.
**Priority**: P2 (tech debt)
**Date**: 2026-02-26

## Context

The `basin_signal_history` table exists in the database (deployed Feb 22) but `tpm_autonomic_v2.py` never writes to it. Signals are detected and sent to thermal memory + Telegram, but the history table stays empty (0 rows). Additionally, the connection pool migration was half-completed — `get_db()` and `put_db()` exist, but 6 functions still call `conn.close()` instead of `put_db(conn)`, which destroys pooled connections.

## Step 1: Fix connection pool returns (6 functions)

File: `/ganuda/daemons/tpm_autonomic_v2.py`

Replace `conn.close()` with `put_db(conn)` in all 6 functions, wrapped in try/finally for safety.

### SR Block 1 — fetch_pending_tasks

File: `/ganuda/daemons/tpm_autonomic_v2.py`

```
<<<<<<< SEARCH
def fetch_pending_tasks(limit=5):
    """Fetch pending tasks from jr_work_queue, oldest first by priority."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, task_id, title, instruction_file, assigned_jr, priority,
               sacred_fire_priority, use_rlm, parameters, created_at
        FROM jr_work_queue
        WHERE status = 'pending'
        ORDER BY priority ASC, created_at ASC
        LIMIT %s
    """, (limit,))
    tasks = cur.fetchall()
    cur.close()
    conn.close()
    return tasks
=======
def fetch_pending_tasks(limit=5):
    """Fetch pending tasks from jr_work_queue, oldest first by priority."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, task_id, title, instruction_file, assigned_jr, priority,
                   sacred_fire_priority, use_rlm, parameters, created_at
            FROM jr_work_queue
            WHERE status = 'pending'
            ORDER BY priority ASC, created_at ASC
            LIMIT %s
        """, (limit,))
        tasks = cur.fetchall()
        cur.close()
        return tasks
    finally:
        put_db(conn)
>>>>>>> REPLACE
```

### SR Block 2 — claim_task

File: `/ganuda/daemons/tpm_autonomic_v2.py`

```
<<<<<<< SEARCH
def claim_task(task_id):
    """Atomically claim a task (pending → in_progress) with row locking."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE jr_work_queue
        SET status = 'in_progress', started_at = NOW(), updated_at = NOW(),
            status_message = 'Claimed by TPM Autonomic Daemon v2'
        WHERE id = %s AND status = 'pending'
        RETURNING id
    """, (task_id,))
    claimed = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return claimed is not None
=======
def claim_task(task_id):
    """Atomically claim a task (pending → in_progress) with row locking."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE jr_work_queue
            SET status = 'in_progress', started_at = NOW(), updated_at = NOW(),
                status_message = 'Claimed by TPM Autonomic Daemon v2'
            WHERE id = %s AND status = 'pending'
            RETURNING id
        """, (task_id,))
        claimed = cur.fetchone()
        conn.commit()
        cur.close()
        return claimed is not None
    finally:
        put_db(conn)
>>>>>>> REPLACE
```

### SR Block 3 — complete_task

File: `/ganuda/daemons/tpm_autonomic_v2.py`

```
<<<<<<< SEARCH
def complete_task(task_id, result_data=None):
    """Mark task as completed."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE jr_work_queue
        SET status = 'completed', completed_at = NOW(), updated_at = NOW(),
            result = %s, status_message = 'Completed by TPM Autonomic Daemon v2'
        WHERE id = %s
    """, (json.dumps(result_data or {}), task_id))
    conn.commit()
    cur.close()
    conn.close()
=======
def complete_task(task_id, result_data=None):
    """Mark task as completed."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE jr_work_queue
            SET status = 'completed', completed_at = NOW(), updated_at = NOW(),
                result = %s, status_message = 'Completed by TPM Autonomic Daemon v2'
            WHERE id = %s
        """, (json.dumps(result_data or {}), task_id))
        conn.commit()
        cur.close()
    finally:
        put_db(conn)
>>>>>>> REPLACE
```

### SR Block 4 — fail_task

File: `/ganuda/daemons/tpm_autonomic_v2.py`

```
<<<<<<< SEARCH
def fail_task(task_id, error_msg):
    """Mark task as failed."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE jr_work_queue
        SET status = 'failed', completed_at = NOW(), updated_at = NOW(),
            error_message = %s, status_message = 'Failed in TPM Autonomic Daemon v2'
        WHERE id = %s
    """, (error_msg[:2000], task_id))
    conn.commit()
    cur.close()
    conn.close()
=======
def fail_task(task_id, error_msg):
    """Mark task as failed."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE jr_work_queue
            SET status = 'failed', completed_at = NOW(), updated_at = NOW(),
                error_message = %s, status_message = 'Failed in TPM Autonomic Daemon v2'
            WHERE id = %s
        """, (error_msg[:2000], task_id))
        conn.commit()
        cur.close()
    finally:
        put_db(conn)
>>>>>>> REPLACE
```

### SR Block 5 — log_thermal_memory

File: `/ganuda/daemons/tpm_autonomic_v2.py`

```
<<<<<<< SEARCH
def log_thermal_memory(content, temperature=75.0, sacred=False):
    """Store a thermal memory record."""
    conn = get_db()
    cur = conn.cursor()
    memory_hash = hashlib.sha256(content.encode()).hexdigest()
    cur.execute("""
        INSERT INTO thermal_memory_archive
        (original_content, temperature_score, sacred_pattern, memory_hash,
         metadata, created_at)
        VALUES (%s, %s, %s, %s, %s, NOW())
        ON CONFLICT (memory_hash) DO NOTHING
    """, (
        content[:10000],
        temperature,
        sacred,
        memory_hash,
        json.dumps({"source": "tpm_autonomic_v2", "timestamp": datetime.utcnow().isoformat()})
    ))
    conn.commit()
    cur.close()
    conn.close()
=======
def log_thermal_memory(content, temperature=75.0, sacred=False):
    """Store a thermal memory record."""
    conn = get_db()
    try:
        cur = conn.cursor()
        memory_hash = hashlib.sha256(content.encode()).hexdigest()
        cur.execute("""
            INSERT INTO thermal_memory_archive
            (original_content, temperature_score, sacred_pattern, memory_hash,
             metadata, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            ON CONFLICT (memory_hash) DO NOTHING
        """, (
            content[:10000],
            temperature,
            sacred,
            memory_hash,
            json.dumps({"source": "tpm_autonomic_v2", "timestamp": datetime.utcnow().isoformat()})
        ))
        conn.commit()
        cur.close()
    finally:
        put_db(conn)
>>>>>>> REPLACE
```

### SR Block 6 — check_basin_signals

File: `/ganuda/daemons/tpm_autonomic_v2.py`

```
<<<<<<< SEARCH
    cur.close()
    conn.close()
    return signals


# ── Telegram Notification ──────────────────────────────────────────────────
=======
    cur.close()
    put_db(conn)
    return signals


# ── Telegram Notification ──────────────────────────────────────────────────
>>>>>>> REPLACE
```

## Step 2: Wire basin signal INSERT into history table

After signals are detected and before they are returned, insert each one into `basin_signal_history`.

File: `/ganuda/daemons/tpm_autonomic_v2.py`

```
<<<<<<< SEARCH
    cur.close()
    put_db(conn)
    return signals
=======
    # Write detected signals to basin_signal_history for trend analysis
    for s in signals:
        cur.execute("""
            INSERT INTO basin_signal_history
            (signal_type, signal_value, threshold, detail, escalated, detected_at)
            VALUES (%s, %s, %s, %s, false, NOW())
        """, (s["type"], s["value"], s["threshold"], s["detail"][:2000]))
    if signals:
        conn.commit()

    cur.close()
    put_db(conn)
    return signals
>>>>>>> REPLACE
```

## Step 3: Mark escalated signals in history

When signals escalate to council, update the `escalated` flag.

File: `/ganuda/daemons/tpm_autonomic_v2.py`

```
<<<<<<< SEARCH
                if len(signals) >= BASIN_THRESHOLDS["phase_transition_threshold"]:
                    await self._escalate_to_council(signals)
=======
                if len(signals) >= BASIN_THRESHOLDS["phase_transition_threshold"]:
                    # Mark escalated signals in basin_signal_history
                    esc_conn = get_db()
                    try:
                        esc_cur = esc_conn.cursor()
                        for s in signals:
                            esc_cur.execute("""
                                UPDATE basin_signal_history SET escalated = true
                                WHERE signal_type = %s AND detected_at > NOW() - INTERVAL '5 minutes'
                                  AND escalated = false
                            """, (s["type"],))
                        esc_conn.commit()
                        esc_cur.close()
                    finally:
                        put_db(esc_conn)
                    await self._escalate_to_council(signals)
>>>>>>> REPLACE
```

## Verification

After executor applies these changes:

1. All 6 functions use `put_db(conn)` instead of `conn.close()` — connection pool integrity restored.
2. `check_basin_signals()` inserts detected signals into `basin_signal_history` — no more empty table.
3. Escalated signals get `escalated = true` flag.
4. No new imports needed — all dependencies already present.
5. The daemon must be restarted after deploy: `sudo systemctl restart tpm-autonomic` (manual step, not automated).

# Jr Instruction: Fire Guard Zombie Task Auto-Reset

## Context
Tasks grabbed by the executor can get stuck in_progress permanently if the executor crashes mid-task or fails silently. These zombie tasks block the queue because the executor skips tasks already in_progress. Council vote #22437c1f — Coyote: "A stalled executor is a zombie: heart beating, nobody home." Turtle concern honored: make it generic, time-based, not service-specific.

## Task
Add a zombie task auto-reset to Fire Guard that resets tasks stuck in_progress back to pending after a configurable threshold.

## File: `/ganuda/scripts/fire_guard.py`

### Step 1: Add zombie reset function

After the `check_stale_tasks` function, add:

```
<<<<<<< SEARCH
def run_checks():
=======
ZOMBIE_THRESHOLD_HOURS = 6


def reset_zombie_tasks():
    """Reset tasks stuck in_progress for longer than ZOMBIE_THRESHOLD_HOURS.

    Returns list of reset task titles for alerting.
    Coyote rule: cost of over-escalation < cost of under-escalation.
    """
    import psycopg2
    reset_tasks = []
    try:
        conn = psycopg2.connect(host=DB_HOST, port=5432, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
        cur = conn.cursor()

        cur.execute("""
            UPDATE jr_work_queue
            SET status = 'pending', updated_at = NOW()
            WHERE status = 'in_progress'
              AND updated_at < NOW() - INTERVAL '%s hours'
            RETURNING task_id, title
        """, (ZOMBIE_THRESHOLD_HOURS,))
        reset_tasks = cur.fetchall()

        if reset_tasks:
            # Log the reset to thermal memory
            content = f"FIRE GUARD ZOMBIE RESET: {len(reset_tasks)} task(s) reset from in_progress to pending after {ZOMBIE_THRESHOLD_HOURS}h stall: " + "; ".join(t[1] for t in reset_tasks)
            memory_hash = hashlib.sha256(content.encode()).hexdigest()
            cur.execute("""INSERT INTO thermal_memory_archive
                (original_content, temperature_score, sacred_pattern, memory_hash, domain_tag, tags, metadata)
                VALUES (%s, 75, false, %s, 'fire_guard', %s, %s::jsonb)
                ON CONFLICT (memory_hash) DO NOTHING""",
                (content, memory_hash,
                 ['fire_guard', 'zombie_reset', 'auto_recovery'],
                 json.dumps({"source": "fire_guard", "action": "zombie_reset", "count": len(reset_tasks), "tasks": [t[1] for t in reset_tasks]})))

        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        pass
    return reset_tasks


def run_checks():
>>>>>>> REPLACE
```

### Step 2: Wire zombie reset into run_checks

Add after the stale task detection block (after `check_stale_tasks` call):

```
<<<<<<< SEARCH
    results["alerts"] = alerts
    results["healthy"] = len(alerts) == 0
=======
    # Zombie task auto-reset (self-healing)
    reset_tasks = reset_zombie_tasks()
    if reset_tasks:
        alerts.append(f"ZOMBIE RESET: {len(reset_tasks)} task(s) auto-reset to pending after {ZOMBIE_THRESHOLD_HOURS}h stall")
    results["zombie_resets"] = [t[1] for t in reset_tasks]

    results["alerts"] = alerts
    results["healthy"] = len(alerts) == 0
>>>>>>> REPLACE
```

## Acceptance Criteria
- Tasks in_progress > 6 hours are automatically reset to pending
- Reset is logged to thermal memory (temperature 75, not sacred)
- Reset generates a Fire Guard alert (visible on health page)
- DB failure does NOT crash Fire Guard
- Threshold is configurable via ZOMBIE_THRESHOLD_HOURS constant

## IMPORTANT
- This instruction DEPENDS on JR-FIRE-GUARD-STALE-TASK-DETECTION-MAR08-2026.md being applied first
- The SEARCH block for `def run_checks():` must match the state AFTER that instruction is applied
- If in doubt, find the `def run_checks():` line and insert before it

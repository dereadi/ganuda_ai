# Jr Instruction: Fire Guard Stale Task Detection

## Context
Fire Guard checks if services are alive (systemd is-active) but NOT if they're productive. jr-se.service ran for 19 hours with 4 zombied tasks stuck in_progress while Fire Guard reported ALL CLEAR. Council vote #22437c1f, 0.40 confidence, 4 concerns honored.

## Task
Add a stale task check to Fire Guard that detects when the Jr executor is running but not processing work.

## Requirements
1. Query jr_work_queue for tasks stuck in_progress longer than a threshold
2. Query jr_work_queue for the last completed task timestamp
3. Alert if: tasks are in_progress AND oldest in_progress task is > 2 hours old
4. Alert if: pending tasks exist AND last completion was > 4 hours ago
5. DO NOT hardcode to jr-se specifically — use generic column names (status, updated_at)

## File: `/ganuda/scripts/fire_guard.py`

### Step 1: Add the stale task check function

After the `check_timer_freshness` function (line 98), add:

```
<<<<<<< SEARCH
def run_checks():
=======
def check_stale_tasks():
    """Check if Jr executor has stalled — tasks stuck in_progress or no completions."""
    import psycopg2
    alerts = []
    try:
        conn = psycopg2.connect(host=DB_HOST, port=5432, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
        cur = conn.cursor()

        # Check for tasks stuck in_progress > 2 hours
        cur.execute("""
            SELECT count(*), min(updated_at)
            FROM jr_work_queue
            WHERE status = 'in_progress'
              AND updated_at < NOW() - INTERVAL '2 hours'
        """)
        stuck_count, oldest = cur.fetchone()
        if stuck_count and stuck_count > 0:
            alerts.append(f"STALE TASKS: {stuck_count} task(s) stuck in_progress since {oldest}")

        # Check if pending tasks exist but no completions in 4 hours
        cur.execute("""
            SELECT count(*) FROM jr_work_queue WHERE status = 'pending'
        """)
        pending_count = cur.fetchone()[0]

        if pending_count and pending_count > 0:
            cur.execute("""
                SELECT max(updated_at) FROM jr_work_queue WHERE status = 'completed'
            """)
            last_completed = cur.fetchone()[0]
            if last_completed:
                cur.execute("SELECT NOW() - %s > INTERVAL '4 hours'", (last_completed,))
                is_stale = cur.fetchone()[0]
                if is_stale:
                    alerts.append(f"IDLE EXECUTOR: {pending_count} pending task(s), last completion: {last_completed}")

        cur.close()
        conn.close()
    except Exception as e:
        # DB down is caught by port check — don't double-alert
        pass
    return alerts


def run_checks():
>>>>>>> REPLACE
```

### Step 2: Wire stale task alerts into run_checks

```
<<<<<<< SEARCH
    results["alerts"] = alerts
    results["healthy"] = len(alerts) == 0
=======
    # Stale task detection (productivity check)
    stale_alerts = check_stale_tasks()
    for sa in stale_alerts:
        alerts.append(sa)

    results["alerts"] = alerts
    results["healthy"] = len(alerts) == 0
>>>>>>> REPLACE
```

### Step 3: Add stale tasks to HTML output

In the `render_html` function, the alerts section already renders all alerts generically. No change needed — the new alerts flow through the existing alert rendering.

## Acceptance Criteria
- Fire Guard alerts when tasks are stuck in_progress > 2 hours
- Fire Guard alerts when pending tasks exist but no completions in 4 hours
- DB connection failure does NOT cause Fire Guard to crash (silent catch)
- Existing heartbeat/port checks are unchanged
- Alert text includes count and timestamp for diagnostics

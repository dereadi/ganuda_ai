# Jr Instruction: Fire Guard Queue Depth Metric on Health Page

## Context
Fire Guard health page shows service up/down and alerts but no queue metrics. After the stale task and zombie reset features, the health page should show queue state so operators can see at a glance if work is flowing.

## Task
Add a queue depth section to the Fire Guard health page HTML showing pending, in_progress, and last completion time.

## File: `/ganuda/scripts/fire_guard.py`

### Step 1: Add queue metrics collection to run_checks

Inside `run_checks()`, after the zombie reset block and before `results["alerts"] = alerts`:

```
<<<<<<< SEARCH
    results["alerts"] = alerts
    results["healthy"] = len(alerts) == 0
    return results
=======
    # Queue depth metrics
    queue_metrics = {"pending": 0, "in_progress": 0, "last_completed": "unknown"}
    try:
        import psycopg2
        conn = psycopg2.connect(host=DB_HOST, port=5432, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
        cur = conn.cursor()
        cur.execute("SELECT status, count(*) FROM jr_work_queue WHERE status IN ('pending', 'in_progress') GROUP BY status")
        for status, count in cur.fetchall():
            queue_metrics[status] = count
        cur.execute("SELECT max(updated_at) FROM jr_work_queue WHERE status = 'completed'")
        row = cur.fetchone()
        if row and row[0]:
            queue_metrics["last_completed"] = str(row[0])[:16]
        cur.close()
        conn.close()
    except Exception:
        pass
    results["queue"] = queue_metrics

    results["alerts"] = alerts
    results["healthy"] = len(alerts) == 0
    return results
>>>>>>> REPLACE
```

### Step 2: Add queue section to HTML render

In `render_html`, after the Timer Health card div and before the back link div:

```
<<<<<<< SEARCH
<div style="text-align:center; margin-top:16px; font-size:0.7em; color:#444;">
=======
<div class="card">
  <h2>Jr Work Queue</h2>
  <div class="svc">Pending: {results.get('queue', {}).get('pending', '?')}</div>
  <div class="svc">In Progress: {results.get('queue', {}).get('in_progress', '?')}</div>
  <div class="svc">Last Completed: {results.get('queue', {}).get('last_completed', '?')}</div>
</div>

<div style="text-align:center; margin-top:16px; font-size:0.7em; color:#444;">
>>>>>>> REPLACE
```

## Acceptance Criteria
- Fire Guard health page shows pending count, in_progress count, last completion time
- DB failure shows "?" rather than crashing
- Queue section appears between Timer Health and the back link

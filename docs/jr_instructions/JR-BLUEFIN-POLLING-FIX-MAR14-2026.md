# JR INSTRUCTION: Bluefin Polling Fix — LISTEN/NOTIFY for jr_status + sag_events

**Task**: Replace pathological sequential scan polling on jr_status (6.1M scans, 16 rows) and sag_events (1.96M scans, 0 rows) with PostgreSQL LISTEN/NOTIFY or exponential backoff.
**Priority**: P2
**Date**: 2026-03-14
**TPM**: Claude Opus
**Story Points**: 3
**Council Vote**: Pending (TPM Easy Button — performance)
**Depends On**: None

## Problem Statement

Two tables on bluefin are being polled at extreme rates:

| Table | Rows | Sequential Scans | Problem |
|-------|------|-------------------|---------|
| jr_status | 16 | 6,100,000+ | Polling every fraction of a second |
| sag_events | 0 | 1,960,000+ | Polling an empty table millions of times |

Stats were reset Feb 13 — this is ~30 days of accumulation. That's:
- jr_status: ~2.4 scans/second, 24/7
- sag_events: ~0.75 scans/second, 24/7

Each scan is trivially fast (16 rows / 0 rows), but the cumulative overhead is:
- Lock acquisition/release on every scan
- Buffer cache churn (evicting useful pages)
- pg_stat counter updates
- Shared memory contention with real queries

## Fix A: Identify the Pollers

**Step 1**: Find what's polling these tables:

```sql
-- Enable pg_stat_statements if not already
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Find the queries hitting these tables
SELECT query, calls, mean_exec_time, total_exec_time
FROM pg_stat_statements
WHERE query ILIKE '%jr_status%' OR query ILIKE '%sag_events%'
ORDER BY calls DESC;
```

**Step 2**: Find the client source:

```sql
-- Check active connections polling these tables
SELECT pid, client_addr, application_name, query, state
FROM pg_stat_activity
WHERE query ILIKE '%jr_status%' OR query ILIKE '%sag_events%';
```

Document which service/script is doing the polling before changing anything.

## Fix B: LISTEN/NOTIFY for jr_status (Preferred)

Replace polling with event-driven notification:

**1. Add notification trigger on jr_status**:

```sql
CREATE OR REPLACE FUNCTION notify_jr_status_change()
RETURNS trigger AS $$
BEGIN
    PERFORM pg_notify('jr_status_changed', json_build_object(
        'task_id', NEW.task_id,
        'status', NEW.status,
        'updated_at', NEW.updated_at
    )::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_jr_status_notify
    AFTER INSERT OR UPDATE ON jr_status
    FOR EACH ROW
    EXECUTE FUNCTION notify_jr_status_change();
```

**2. Modify the polling service** (find it in Step A) to use LISTEN:

```python
import psycopg2
import select

conn = psycopg2.connect(...)
conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
curs = conn.cursor()
curs.execute("LISTEN jr_status_changed;")

while True:
    # Block until notification arrives (with 30s timeout for health check)
    if select.select([conn], [], [], 30) == ([], [], []):
        # Timeout — do periodic health check if needed
        continue
    else:
        conn.poll()
        while conn.notifies:
            notify = conn.notifies.pop(0)
            payload = json.loads(notify.payload)
            # Process the status change
            handle_status_change(payload)
```

Zero scans when idle. Instant notification on change.

## Fix C: Disable or Backoff sag_events Polling

sag_events has **zero rows** and 1.96M scans. Nothing is writing to it.

**Option 1 (Preferred)**: Find and disable the poller entirely. If SAG isn't actively using this table, the polling service should be stopped or the polling loop commented out.

**Option 2**: If the poller must stay, add exponential backoff:

```python
import time

poll_interval = 1.0  # Start at 1 second
MAX_INTERVAL = 30.0  # Cap at 30 seconds
BACKOFF_FACTOR = 1.5

while True:
    results = query_sag_events()
    if results:
        poll_interval = 1.0  # Reset on activity
        process(results)
    else:
        poll_interval = min(poll_interval * BACKOFF_FACTOR, MAX_INTERVAL)
    time.sleep(poll_interval)
```

This would reduce scans from ~0.75/s to ~0.03/s (30s interval) when idle.

**Option 3**: Add LISTEN/NOTIFY same as jr_status if sag_events will be used in the future.

## Fix D: Reset Stats After Fix

After the polling fixes are deployed:

```sql
-- Reset table-level stats to get clean baseline
SELECT pg_stat_reset();
```

Check after 24 hours:
```sql
SELECT relname, seq_scan, seq_tup_read, idx_scan
FROM pg_stat_user_tables
WHERE relname IN ('jr_status', 'sag_events')
ORDER BY seq_scan DESC;
```

Target: jr_status < 1,000 scans/day, sag_events < 100 scans/day.

## Files to Modify

| File | Change |
|------|--------|
| Find the jr_status poller (likely in `/ganuda/scripts/` or `/ganuda/services/`) | Replace polling loop with LISTEN/NOTIFY |
| Find the sag_events poller (likely SAG-related service) | Disable or add backoff |
| Bluefin DB | Add notification trigger on jr_status |

## DO NOT

- Drop or modify the jr_status or sag_events tables — just change how they're queried
- Use LISTEN/NOTIFY for high-throughput writes (it's for low-frequency events like status changes)
- Remove the polling service entirely without understanding what depends on it
- Reset pg_stat_statements before documenting the current polling queries

## Acceptance Criteria

- [ ] Polling source identified for both tables (service name, PID, script path)
- [ ] jr_status uses LISTEN/NOTIFY instead of polling loop
- [ ] sag_events poller disabled or running at ≤ 30s intervals
- [ ] After 24 hours: jr_status seq_scan < 1,000/day
- [ ] After 24 hours: sag_events seq_scan < 100/day
- [ ] No regression in Jr task execution (status changes still detected)

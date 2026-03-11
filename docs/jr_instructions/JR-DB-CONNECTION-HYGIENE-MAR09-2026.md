# JR INSTRUCTION: Database Connection Hygiene — Prevent Executor Freeze

**Task**: Fix connection leak that causes Jr executor to freeze
**Priority**: P1 — this is the root cause of orphaned tasks
**Date**: 2026-03-09
**TPM**: Claude Opus

## Root Cause

The Jr executor (`jr_queue_worker.py`) uses `jr_queue_client.py` which caches a persistent DB connection via `_get_connection()`. The `get_pending_tasks()` method runs `SELECT ... FOR UPDATE SKIP LOCKED` but other code paths don't always commit/close transactions cleanly. Over time:

1. Threads accumulate with `idle in transaction` state
2. Connection pool on bluefin fills up
3. Main poll loop blocks on a held lock
4. Process freezes — systemd thinks it's alive (sleeping state), doesn't restart
5. All in_progress tasks become orphans

## Acceptance Criteria

### 1. PostgreSQL server-side guard (bluefin)
Set `idle_in_transaction_session_timeout = 300000` (5 minutes, in ms) in postgresql.conf on bluefin.
This kills any connection that sits `idle in transaction` for 5+ minutes. Safety net.

SQL to apply without restart:
```sql
ALTER SYSTEM SET idle_in_transaction_session_timeout = '300000';
SELECT pg_reload_conf();
```

Verify: `SHOW idle_in_transaction_session_timeout;` should return `5min` or `300000`.

### 2. Connection context manager in jr_queue_client.py
Modify `/ganuda/jr_executor/jr_queue_client.py`:

In `_execute()`, wrap the DB call in a try/finally that ensures commit or rollback:
```python
def _execute(self, query, params=None, fetch=True):
    conn = self._get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if fetch:
                result = cur.fetchall()
                conn.commit()
                return result
            conn.commit()
            return cur.rowcount
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            self._conn = None  # Force reconnect on next call
        raise
```

Also add a `close()` method check — ensure `self.client.close()` in the worker loop's finally block actually closes the connection.

### 3. Systemd watchdog for frozen process
Add `WatchdogSec=300` to `/etc/systemd/system/jr-se.service` and have the worker send `sd_notify("WATCHDOG=1")` on each poll cycle. If the process freezes for 5 minutes, systemd kills and restarts it.

Alternative (simpler): Add `TimeoutStartSec=300` and `RuntimeMaxSec=3600` to force-restart every hour.

## Target Files
- `/ganuda/jr_executor/jr_queue_client.py` — connection handling
- `/etc/systemd/system/jr-se.service` — watchdog config (needs sudo)
- PostgreSQL config on bluefin — idle_in_transaction timeout

## Constraints
- Do NOT change the `FOR UPDATE SKIP LOCKED` pattern — it's correct for concurrent workers
- Do NOT add connection pooling (pgbouncer) yet — overkill for current scale
- Test with `python3 -c "import py_compile; py_compile.compile('jr_queue_client.py', doraise=True)"`

## Evaluation
- After 1 hour of running, executor should have < 5 threads (not 65)
- `pg_stat_activity` should show 0 connections in `idle in transaction` for > 5 minutes
- Executor logs should show continuous poll activity (no 5-hour silences)

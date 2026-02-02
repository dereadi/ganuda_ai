# KB: Jr Queue Client Transaction Leak

**KB ID:** KB-JR-QUEUE-TRANSACTION-LEAK-JAN27-2026
**Created:** 2026-01-27
**Category:** Database / Connection Management
**Severity:** P0 (CRITICAL)
**Status:** Documented - Fix Pending

## Summary

Jr workers polling the queue left database connections in "idle in transaction" state, causing connection pool exhaustion and blocking VetAssist dashboard.

## Root Cause

In `/ganuda/jr_executor/jr_queue_client.py`, the `_execute()` method only calls `conn.commit()` when `fetch=False` (for INSERT/UPDATE). For SELECT queries (`fetch=True`), the connection was returned without commit, leaving it in transaction state.

```python
# BUGGY CODE
def _execute(self, query: str, params: tuple = None, fetch: bool = True) -> Any:
    conn = self._get_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, params)
        if fetch:
            return cur.fetchall()  # BUG: No commit!
        conn.commit()
        return cur.rowcount
```

## Why This Matters

1. **PostgreSQL default behavior**: psycopg2 connections have `autocommit=False` by default
2. **Transaction isolation**: Even SELECT queries start a transaction when autocommit is off
3. **Connection pooling**: Idle transactions hold locks and prevent connection reuse
4. **Cascade effect**: Multiple Jr workers polling = multiple stuck connections = pool exhaustion

## Symptoms

- Dashboard hangs on loading
- Database queries timeout
- `pg_stat_activity` shows many `idle in transaction` connections
- Jr workers appear to work but tasks don't progress

## Diagnostic Query

```sql
SELECT pid,
       now() - xact_start as tx_age,
       state,
       SUBSTRING(query, 1, 80) as query
FROM pg_stat_activity
WHERE state = 'idle in transaction'
ORDER BY xact_start;
```

## Immediate Remediation

```sql
-- Kill all idle in transaction connections from Jr workers
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle in transaction'
AND query LIKE '%jr_work_queue%';
```

## Prevention

1. **Always commit after reads**: Even SELECT queries should call `conn.commit()` or use autocommit
2. **Use context managers**: Ensure connections are properly closed in finally blocks
3. **Monitor idle transactions**: Add alerting for connections stuck > 30 seconds
4. **Connection timeouts**: Configure `idle_in_transaction_session_timeout` in PostgreSQL

## Related JRs

- JR-QUEUE-002: Fix Jr Queue Client Transaction Leak (the fix)

## Lessons Learned

1. PostgreSQL transactions are implicit when autocommit=False
2. Polling loops are particularly dangerous for transaction leaks
3. Connection issues cascade quickly with multiple workers
4. Always verify connection state after refactoring database code

---

FOR SEVEN GENERATIONS

# JR Instruction: Fix Jr Queue Client Transaction Leak

**JR ID:** JR-QUEUE-002
**Priority:** P0 (CRITICAL)
**Created:** 2026-01-27
**Author:** TPM via Claude Code
**Council Vote:** 31653da1507b46ec
**Assigned To:** Software Engineer Jr.
**Effort:** Low

## Problem Statement

Jr workers polling the queue are leaving database connections in "idle in transaction" state. This causes connection pool exhaustion and blocks database operations for other services (including VetAssist dashboard).

**Root Cause:** In `jr_queue_client.py`, the `_execute()` method only calls `conn.commit()` when `fetch=False`. For SELECT queries (`fetch=True`), the connection is returned without commit, leaving it in transaction state.

## Impact

- Dashboard hangs on loading
- Database connections exhausted
- All Jr workers blocked waiting for connections
- System-wide degradation

## Required Implementation

### 1. Fix Transaction Leak in jr_queue_client.py

MODIFY: `/ganuda/jr_executor/jr_queue_client.py`

**Current code (lines 49-57):**
```python
def _execute(self, query: str, params: tuple = None, fetch: bool = True) -> Any:
    """Execute a query and optionally fetch results."""
    conn = self._get_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, params)
        if fetch:
            return cur.fetchall()
        conn.commit()
        return cur.rowcount
```

**Fixed code:**
```python
def _execute(self, query: str, params: tuple = None, fetch: bool = True) -> Any:
    """Execute a query and optionally fetch results."""
    conn = self._get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if fetch:
                result = cur.fetchall()
                conn.commit()  # CRITICAL: Commit after SELECT to close transaction
                return result
            conn.commit()
            return cur.rowcount
    except Exception as e:
        conn.rollback()  # Rollback on error to release locks
        raise
```

### 2. Alternative: Use Autocommit for Read Operations

If the above fix causes issues, consider using autocommit mode for the connection:

```python
def _get_connection(self):
    """Get a database connection with autocommit for reads."""
    if self._conn is None or self._conn.closed:
        self._conn = psycopg2.connect(self._connection_string)
        self._conn.autocommit = True  # Prevents idle in transaction
    return self._conn
```

**Warning:** Autocommit changes behavior for write operations. Only use if all writes are explicitly wrapped in transactions.

## Verification

```bash
# 1. Check for idle in transaction connections (should be 0 or minimal)
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT count(*) as idle_in_transaction
FROM pg_stat_activity
WHERE state = 'idle in transaction'
AND application_name LIKE '%jr%';"

# 2. Monitor connections over 60 seconds
for i in {1..6}; do
  echo "=== Check $i ==="
  PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
  SELECT pid, now() - xact_start as tx_age, state, SUBSTRING(query, 1, 60) as query
  FROM pg_stat_activity
  WHERE state = 'idle in transaction'
  ORDER BY xact_start;" 2>/dev/null
  sleep 10
done

# 3. Test dashboard loads
curl -s https://vetassist.ganuda.us/dashboard -o /dev/null -w "%{http_code} in %{time_total}s\n"
```

## Rollback Procedure

If the fix causes issues:

```bash
# Restore from git
cd /ganuda
git checkout jr_executor/jr_queue_client.py
```

---

FOR SEVEN GENERATIONS

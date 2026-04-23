# KB — TPMQueueManager._execute Commit Bug (Silent Task Loss)

**Filed:** 2026-04-21 by TPM
**Severity:** High (silent data loss)
**Status:** FIXED in commit

## Symptom

Tasks dispatched via `TPMQueueManager.add_task()` silently disappear after the call returns. The function returns a valid task ID (`RETURNING id` comes back with a number), but subsequent queries against `jr_work_queue` find no row at that ID. Sequence `jr_work_queue_id_seq` is advanced (consumed values), but rows are absent.

**Historical manifestation:** "Ghost tasks" — TPM dispatches something, reports a kanban ID, worker never picks it up, later investigation finds no evidence the ticket existed. Assumed to be dispatch-format issues or worker filter bugs. Actually was this.

**Trigger case (Apr 20 2026):** TPM dispatched OTel O7 and O8 (task IDs 1567, 1568 returned). Neither was ever executed. Morning-after diagnosis (Apr 21) found sequence at 1568 but MAX(id) = 1566 — proof that INSERTs were attempted, RETURNING id fired, but rows never committed.

## Root Cause

`/ganuda/jr_executor/tpm_queue_manager.py:39-46` (pre-fix):

```python
def _execute(self, query: str, params: tuple = None, fetch: bool = True) -> Any:
    conn = self._get_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, params)
        if fetch:
            return cur.fetchall()   # <-- returns WITHOUT commit
        conn.commit()                # <-- only commits when fetch=False
        return cur.rowcount
```

For `INSERT ... RETURNING id`, `fetch=True` (so `.fetchall()` can retrieve the ID). The function returns without committing. The transaction stays open on the connection. When the script exits or the connection is otherwise closed, psycopg2 auto-rolls back uncommitted transactions. Row vanishes. Sequence value is not rolled back (sequences are non-transactional in PostgreSQL).

Why `_execute` was written this way is unclear — likely an oversight during original implementation, with the author assuming `fetch=True` was only for SELECT (which doesn't need commit).

## Fix

Always commit after execute, regardless of `fetch` mode:

```python
def _execute(self, query: str, params: tuple = None, fetch: bool = True) -> Any:
    conn = self._get_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, params)
        result = cur.fetchall() if fetch else cur.rowcount
        conn.commit()
        return result
```

## Verification

Post-fix sanity test:
```python
mgr = TPMQueueManager()
tid = mgr.add_task(title="BUG-FIX SANITY CHECK ...", assigned_jr="it_triad_jr", ...)
# verify row actually exists
cur.execute("SELECT id, status FROM jr_work_queue WHERE id = %s", (tid,))
assert cur.fetchone() is not None  # passed
```

Confirmed: row 1570 persisted after add_task() returned. Sequence + MAX(id) aligned at 1570.

## Historical Scope

**Any task ever dispatched via `TPMQueueManager.add_task()` since the class was written has been at risk of silent loss.** Tasks dispatched via other paths (`jr_queue_client.py`, direct SQL, other managers) are unaffected. The two OTel atomic tasks (O1 config YAML, O9 redaction tests) that successfully landed last night went through the correct path (likely `jr_queue_client` or a script using direct INSERT+commit).

Sequence gaps in `jr_work_queue_id_seq` are evidence of past incidents — values consumed without corresponding rows. Example: 1567, 1568 lost Apr 20 2026. Likely many more historically.

## Secondary Lesson

The SELECT case (`fetch=True` for a genuine SELECT) also benefits from the always-commit fix: long-held read transactions can cause MVCC bloat. The fix is cleaner in all cases.

## Related

- Jr instruction files were correct (`/ganuda/docs/jr_instructions/JR-OTEL-O7-*.md`, `JR-OTEL-O8-*.md`). The code that SHOULD have been written by Jr was valid. Problem was never-dispatched, not Jr-failed.
- Motivates reviewing any other internal helper that uses `psycopg2` + fetchall + manual commit. Look for the asymmetric commit pattern.

## Apr 21 2026 resolution

1. Bug fixed (one-line commit always)
2. Sanity-tested with task #1570
3. O7 instrumentation applied directly by TPM to `jr_queue_worker.py`
4. O8 instrumentation applied directly by TPM to `services/memory_api/server.py`
5. Separate post-fork OTel fix (BatchSpanProcessor thread doesn't survive uvicorn worker fork) added as `@app.on_event("startup")` in memory_api
6. O8 verified end-to-end: span + both histograms flowing in collector
7. O7 verification pending natural Jr worker cycle (50-task auto-restart)

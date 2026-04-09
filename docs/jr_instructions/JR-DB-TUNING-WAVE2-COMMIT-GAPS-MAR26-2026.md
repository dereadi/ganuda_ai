# JR INSTRUCTION: DB Tuning Wave 2 — conn.commit() Gap Audit & Fix

**Task ID**: DB-TUNE-002
**Priority**: P0
**SP**: 5
**Epic**: DB-HEALTH-EPIC
**Longhouse Session**: 2710dbfcdab99b43

## Context

The #1 cause of the 15-30% rollback rates is application code closing psycopg2 connections without committing the transaction first. In PostgreSQL, an uncommitted transaction = a rollback, even for read-only SELECTs. This inflates rollback stats and wastes DB resources.

**91 instances found across the codebase.** This instruction covers the critical and high-priority fixes.

## The Pattern

**BAD** (causes rollback):
```python
conn = get_connection()
cur = conn.cursor()
cur.execute("SELECT ...")
result = cur.fetchall()
conn.close()  # Transaction never committed → PostgreSQL logs a ROLLBACK
```

**GOOD** (clean close):
```python
conn = get_connection()
cur = conn.cursor()
cur.execute("SELECT ...")
result = cur.fetchall()
conn.commit()  # Explicitly close the transaction
conn.close()
```

**BEST** (resilient):
```python
conn = get_connection()
try:
    cur = conn.cursor()
    cur.execute("SELECT ...")
    result = cur.fetchall()
    conn.commit()
except Exception:
    conn.rollback()
    raise
finally:
    conn.close()
```

## CRITICAL FIXES (Do First)

### 1. `/ganuda/jr_executor/dlq_manager.py` — Lines 112, 156

Two finally blocks close connections without commit. Both are read-only but still cause rollback stats.

**Line ~108-112** (`get_tasks_ready_for_retry`):
```python
# BEFORE:
finally:
    conn.close()

# AFTER:
finally:
    try:
        conn.commit()
    except Exception:
        pass
    conn.close()
```

**Line ~152-156** (`get_dlq_summary`):
Same fix pattern.

### 2. `/ganuda/telegram_bot/telegram_chief_v3.py` — Lines 69-77

Context manager yields connection without commit guarantee:

```python
# BEFORE:
def get_db(self):
    conn = None
    try:
        conn = psycopg2.connect(**self.db_config)
        yield conn
    finally:
        if conn:
            conn.close()

# AFTER:
def get_db(self):
    conn = None
    try:
        conn = psycopg2.connect(**self.db_config)
        yield conn
        conn.commit()  # Commit if no exception
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
```

### 3. `/ganuda/telegram_bot/tribe_interface_fix.py` — Lines 25-29

Same context manager pattern. Apply same fix as #2.

### 4. `/ganuda/jr_executor/consultation_responder.py` — Line 21

Early return closes connection without commit:

```python
# BEFORE:
if not consultations:
    cur.close(); conn.close()
    return

# AFTER:
if not consultations:
    conn.commit()
    cur.close(); conn.close()
    return
```

### 5. `/ganuda/scripts/council_dawn_mist.py` — Lines 351-354

Already covered in JR-DAWN-MIST-SSL-FIX-MAR25-2026. Ensure that fix is applied.

## HIGH PRIORITY FIXES

### 6. `/ganuda/jr_executor/task_executor.py` — Lines 2244, 2780

Two connection opens without commit:
- Line ~2244: table verification check (SELECT)
- Line ~2780: retry idempotency check (SELECT)

Add `conn.commit()` before `conn.close()` in both.

### 7. `/ganuda/jr_executor/jr_orchestrator.py` — Line 101

Health check reader. Add commit before close.

### 8. `/ganuda/jr_executor/jr_learning_store.py` — Line 103

Learning retrieval. Add commit before close.

### 9. `/ganuda/daemons/memory_jr_autonomic.py` — Lines 182, 254

Two cursor.close() calls without conn.commit(). Add commit before cursor close.

### 10. `/ganuda/jr_executor/thermal_poller.py` — Line 48

Thermal poll read. Add commit before close.

### 11. `/ganuda/jr_executor/session_tracker.py` — Line 115

Session lookup. Add commit before close.

### 12. `/ganuda/telegram_bot/status_notifier.py` — Line 196

Status check. Add commit before close.

### 13. `/ganuda/telegram_bot/semantic_search.py` — Line 44

Search query. Add commit before close.

### 14. `/ganuda/jr_executor/extract_skills_inventory.py` — Line 85

Skills read. Add commit before close.

## MEDIUM PRIORITY: Standardize ganuda_db Connection Helper

After all individual fixes, update `/ganuda/lib/ganuda_db/__init__.py` to add a context manager that enforces commit/rollback:

```python
from contextlib import contextmanager

@contextmanager
def managed_connection(retries=3):
    """Context manager that guarantees commit or rollback."""
    conn = get_connection(retries=retries)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

Then gradually migrate all callers to:
```python
from ganuda_db import managed_connection

with managed_connection() as conn:
    cur = conn.cursor()
    cur.execute("SELECT ...")
    # Auto-commits on clean exit, auto-rollbacks on exception
```

This is a FUTURE migration — do NOT block Wave 2 on it. Fix the individual sites first.

## Verification

After deploying fixes, reset stats and monitor:

```sql
-- Reset stats to get clean baseline
SELECT pg_stat_reset();

-- Wait 24 hours, then check
SELECT datname, xact_commit, xact_rollback,
       ROUND(100.0 * xact_rollback / NULLIF(xact_commit + xact_rollback, 0), 2) as rollback_pct
FROM pg_stat_database
WHERE datname IN ('zammad_production', 'triad_federation', 'enhanced_memory')
ORDER BY rollback_pct DESC;
```

**Target**: All databases under 5% rollback rate within 48 hours of deployment.

## Constraints

- Do NOT change query logic — only add commit/rollback/close handling
- Do NOT remove finally blocks — make them resilient
- Test each fix individually: restart the affected service, check journalctl for errors
- Prioritize write paths over read paths (write rollbacks lose data, read rollbacks just waste resources)

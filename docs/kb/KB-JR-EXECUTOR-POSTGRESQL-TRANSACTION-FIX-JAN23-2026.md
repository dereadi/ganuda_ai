# KB: Jr Task Executor PostgreSQL Transaction Fix

**KB ID:** KB-JR-EXECUTOR-POSTGRESQL-TRANSACTION-FIX-JAN23-2026
**Date:** January 23, 2026
**Category:** Infrastructure / Bug Fix
**Status:** Resolved

## Problem Summary

The Jr task executor (`/ganuda/jr_executor/jr_task_executor.py`) would enter a cascading failure state where all database operations fail with:

```
current transaction is aborted, commands ignored until end of transaction block
```

Once in this state, the executor could not recover and all tasks would fail.

## Root Cause

PostgreSQL connections in psycopg2 operate in transaction mode by default. When a SQL statement fails, the transaction enters an "aborted" state. All subsequent statements on that connection fail until `conn.rollback()` is called.

The executor's error handlers caught exceptions but did not call `rollback()`, leaving the connection in the aborted state. The `_get_connection()` method did include a rollback call, but it was not sufficient when errors occurred mid-transaction in various methods.

## Affected Methods

1. `get_assigned_tasks()` - line 249
2. `start_task()` - line 266
3. `complete_task()` - line 948
4. `fail_task()` - line 965
5. `log_to_thermal_memory()` - line 992
6. `_query_thermal_memory()` - line 312
7. `_record_fara_mistake()` - line 857
8. `_get_fara_rules()` - line 692

## Solution

Created `/ganuda/scripts/patch_executor_rollback.py` which adds explicit `conn.rollback()` calls to all error handlers.

**Pattern applied:**

```python
# BEFORE (broken)
except Exception as e:
    print(f"Error: {e}")

# AFTER (fixed)
except Exception as e:
    print(f"Error: {e}")
    try:
        if conn and not conn.closed:
            conn.rollback()
    except:
        pass
```

## How to Apply Fix

1. Stop the executor:
   ```bash
   pkill -f jr_task_executor
   ```

2. Run the patch script:
   ```bash
   /home/dereadi/cherokee_venv/bin/python3 /ganuda/scripts/patch_executor_rollback.py
   ```

3. Reset stuck tasks:
   ```sql
   UPDATE jr_task_announcements
   SET status = 'assigned'
   WHERE status = 'in_progress';
   ```

4. Restart the executor:
   ```bash
   /ganuda/scripts/start_jr_executor.sh "Infrastructure Jr." bluefin
   ```

## Files Created/Modified

| File | Purpose |
|------|---------|
| `/ganuda/scripts/patch_executor_rollback.py` | Automated patch script |
| `/ganuda/scripts/start_jr_executor.sh` | Robust startup script |
| `/ganuda/services/jr-executor/jr-executor.service` | Systemd service file |
| `/ganuda/jr_executor/jr_task_executor.py.backup-*` | Backup before patch |

## Systemd Service Setup

To enable automatic restart on failure:

```bash
sudo cp /ganuda/services/jr-executor/jr-executor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable jr-executor
sudo systemctl start jr-executor
```

## Prevention

For future database code in the Cherokee AI Federation:

1. **Always rollback on error** in psycopg2 connections
2. **Use connection as context manager** when possible:
   ```python
   with psycopg2.connect(**config) as conn:
       with conn.cursor() as cur:
           cur.execute(...)
   # Auto-commit on success, auto-rollback on exception
   ```
3. **Consider autocommit=True** for simple read operations
4. **Test error paths** to ensure graceful recovery

## Verification

Check executor is healthy:
```bash
# Process running
ps aux | grep jr_task_executor

# Recent log activity
tail -20 /var/log/ganuda/jr-executor-infra.log

# Task processing
psql -h bluefin -U claude -d zammad_production -c \
  "SELECT task_id, status FROM jr_task_announcements ORDER BY announced_at DESC LIMIT 5;"
```

---

**FOR SEVEN GENERATIONS** - Resilient infrastructure serves all generations.

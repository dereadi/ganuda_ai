# Jr Instruction: Fix PostgreSQL Transaction Rollback in Task Executor

**Task ID:** EXECUTOR-ROLLBACK-FIX-001
**Priority:** P0 (Critical - blocking all Jr task execution)
**Assigned To:** Infrastructure Jr (bluefin)
**Date:** January 23, 2026
**Estimated Effort:** 30 minutes

## Problem Statement

The Jr task executor at `/ganuda/jr_executor/jr_task_executor.py` has a PostgreSQL transaction bug. When any database operation fails (SQL error, constraint violation, etc.), the connection enters an "aborted transaction" state. Subsequent queries fail with:

```
current transaction is aborted, commands ignored until end of transaction block
```

This blocks ALL Jr task execution on the affected node.

## Root Cause

The error handlers in database methods catch exceptions and log them, but do NOT call `conn.rollback()` to reset the transaction state. The affected methods are:

1. `get_assigned_tasks()` - lines 249-251
2. `start_task()` - lines 265-266
3. `complete_task()` - lines 946-948
4. `fail_task()` - lines 963-965
5. `log_to_thermal_memory()` - lines 990-992
6. `_record_fara_mistake()` - lines 854-857
7. `_query_thermal_memory()` - lines 310-312
8. `_get_fara_rules()` - lines 689-692

## Required Fix

Add explicit `conn.rollback()` in EVERY exception handler that involves database operations.

### Pattern to Apply

**BEFORE (broken):**
```python
except Exception as e:
    print(f"[{self.agent_id}] Error completing task: {e}")
```

**AFTER (fixed):**
```python
except Exception as e:
    print(f"[{self.agent_id}] Error completing task: {e}")
    try:
        conn.rollback()
    except:
        pass
```

## Specific Changes Required

### 1. Fix `get_assigned_tasks()` (around line 249)

```python
        except Exception as e:
            print(f"[{self.agent_id}] Error fetching tasks: {e}")
            try:
                if self._conn:
                    self._conn.rollback()
            except:
                pass
            return []
```

### 2. Fix `start_task()` (around line 265)

```python
        except Exception as e:
            print(f"[{self.agent_id}] Error starting task: {e}")
            try:
                conn.rollback()
            except:
                pass
```

### 3. Fix `complete_task()` (around line 946)

```python
        except Exception as e:
            print(f"[{self.agent_id}] Error completing task: {e}")
            try:
                conn.rollback()
            except:
                pass
```

### 4. Fix `fail_task()` (around line 963)

```python
        except Exception as e:
            print(f"[{self.agent_id}] Error marking task failed: {e}")
            try:
                conn.rollback()
            except:
                pass
```

### 5. Fix `log_to_thermal_memory()` (around line 990)

```python
        except Exception as e:
            print(f"[{self.agent_id}] Error logging to thermal memory: {e}")
            try:
                conn.rollback()
            except:
                pass
```

### 6. Fix `_record_fara_mistake()` (around line 854)

```python
        except Exception as e:
            try:
                conn.rollback()
            except:
                pass
```

### 7. Fix `_query_thermal_memory()` (around line 310)

```python
        except Exception as e:
            print(f"[{self.agent_id}] Thermal query error: {e}")
            try:
                conn.rollback()
            except:
                pass
        return "No relevant memories found."
```

### 8. Fix `_get_fara_rules()` (around line 689)

```python
        except Exception as e:
            try:
                conn.rollback()
            except:
                pass
```

## Testing

After applying the fix:

1. Restart the executor on bluefin:
   ```bash
   pkill -f "jr_task_executor.py.*bluefin"
   cd /ganuda/jr_executor
   nohup python3 jr_task_executor.py "Infrastructure Jr." bluefin > /var/log/ganuda/jr-executor-bluefin.log 2>&1 &
   ```

2. Check if pending tasks are picked up:
   ```sql
   SELECT task_id, status, assigned_to
   FROM jr_task_announcements
   WHERE status IN ('pending', 'assigned')
   ORDER BY announced_at DESC;
   ```

3. Monitor logs for transaction errors:
   ```bash
   tail -f /var/log/ganuda/jr-executor-bluefin.log | grep -i "transaction\|rollback"
   ```

## Success Criteria

- [ ] Executor picks up HYBRID-VISION-001 task
- [ ] Task completes (success or failure with clear error)
- [ ] No "transaction aborted" errors in logs
- [ ] Subsequent tasks continue processing

## KB Article

After fix is verified, create KB article:
- `KB-POSTGRESQL-TRANSACTION-ROLLBACK-PATTERN-JAN23-2026.md`
- Document the pattern for future code

---

**FOR SEVEN GENERATIONS** - Resilient infrastructure serves all generations.

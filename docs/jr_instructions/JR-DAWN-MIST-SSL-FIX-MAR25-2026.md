# JR INSTRUCTION: Dawn Mist SSL Retry Fix

**Task ID**: DB-HEALTH-001
**Priority**: P0
**SP**: 1
**Longhouse Session**: 2710dbfcdab99b43
**Council Vote**: a91e34ac2d19f1f6
**Blocking**: Thermal silence (7 days), dawn mist fails every morning at 06:15 AM CT

## The Problem

`council-dawn-mist.service` crashes every morning with:

```
psycopg2.OperationalError: SSL connection has been closed unexpectedly
```

The crash happens at `/ganuda/scripts/council_dawn_mist.py` line 353 in the `finally` block:

```python
finally:
    if conn:
        conn.commit()  # explicit commit before close  <-- CRASHES HERE
        conn.close()
```

The SSL connection drops during the council vote (which takes several seconds on the deep path via bmasass). By the time the `finally` block runs `conn.commit()`, the connection is dead.

This is the SAME bug pattern already fixed in `specialist_council.py` (commit `48f5286`). That fix added `conn.commit()` calls immediately after write operations, before the connection has time to go stale. But `council_dawn_mist.py` was never patched.

## The Fix

### Step 1: Wrap the finally block with a try/except

**File**: `/ganuda/scripts/council_dawn_mist.py`, lines 351-354

Replace:
```python
finally:
    if conn:
        conn.commit()  # explicit commit before close
        conn.close()
```

With:
```python
finally:
    if conn:
        try:
            conn.commit()
        except Exception as e:
            logger.warning(f"[DAWN MIST] conn.commit() in finally failed (non-fatal): {e}")
        try:
            conn.close()
        except Exception:
            pass
```

### Step 2: Add explicit commits after each write operation

Search the file for ALL `cur.execute` calls that perform INSERT, UPDATE, or DELETE. After each one (or after a logical batch), add `conn.commit()` immediately. Do NOT wait for the `finally` block.

Known write operations to find:
- Any `safe_thermal_write()` calls (these manage their own connection, so skip these)
- Any direct `cur.execute("INSERT ...")` or `cur.execute("UPDATE ...")` patterns

### Step 3: Verify the connection is still alive before the council vote

The council vote (`sc.vote(...)`) takes the longest. Add a connection health check after it returns:

```python
# After the council vote returns, verify our DB connection is still alive
try:
    cur.execute("SELECT 1")
except psycopg2.OperationalError:
    logger.warning("[DAWN MIST] DB connection dropped during council vote, reconnecting")
    conn = get_connection()
    cur = conn.cursor()
```

## Test

```bash
sudo systemctl restart council-dawn-mist.service
journalctl -u council-dawn-mist.service -n 50 --no-pager
```

Success = service completes without `SSL connection has been closed unexpectedly`.

## Constraints

- Do NOT change the council vote logic, only the DB connection handling
- Do NOT remove the `finally` block, just make it resilient
- The `get_connection()` function in `ganuda_db` already has retry logic for initial connection — use it for reconnection too

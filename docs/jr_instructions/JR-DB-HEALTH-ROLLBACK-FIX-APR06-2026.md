# JR INSTRUCTION: DB Health — Rollback Rate Fix

**Task ID**: DB-HEALTH-ROLLBACK-001
**Priority**: P1
**SP**: 5
**Assigned Node**: bluefin (DB host) + redfin (daemon code)
**Dawn Mist Signal**: Vote #41a6a37921e82673 — 11.31% rollback rate on zammad_production (SLA: <5%)

## Problem

The `zammad_production` database has an 11.34% rollback rate (430,555 rollbacks / 3.8M transactions). Root cause: `thermal_memory_archive` has 2,047,342 updates against 96,757 rows — multiple daemons updating the same rows every cycle (staleness scores, temperature, last_access). Application-level rollbacks from bare `except: conn.rollback()` patterns inflate the counter silently.

## Task A: Add Missing Indexes (2 SP)

### A1: Index on jr_task_announcements
```sql
-- 153K sequential scans, zero index scans
-- Connect to zammad_production on bluefin
CREATE INDEX CONCURRENTLY idx_jr_task_announcements_status 
ON jr_task_announcements (status, created_at DESC);
```

### A2: Index on elisi_state
```sql
-- 90K sequential scans on a 3-row table, zero index usage
CREATE INDEX CONCURRENTLY idx_elisi_state_key 
ON elisi_state (state_key);
```

### A3: Investigate idx_tma_temporal_state
```sql
-- This index reads 3.96B tuples from 41K scans — very low selectivity
-- Check what it covers:
SELECT indexdef FROM pg_indexes WHERE indexname = 'idx_tma_temporal_state';

-- Check selectivity:
SELECT temporal_state, COUNT(*) FROM thermal_memory_archive GROUP BY temporal_state;

-- If >90% of rows have the same temporal_state value, this index is useless
-- Replace with a PARTIAL index:
-- DROP INDEX idx_tma_temporal_state;
-- CREATE INDEX CONCURRENTLY idx_tma_temporal_state_active 
--   ON thermal_memory_archive (temporal_state) WHERE temporal_state != 'current';
```

**Verification**: After creating indexes, run:
```sql
SELECT relname, seq_scan, idx_scan FROM pg_stat_user_tables 
WHERE relname IN ('jr_task_announcements', 'elisi_state') ORDER BY relname;
```
Confirm idx_scan is increasing on subsequent queries.

## Task B: Audit Daemon Rollback Patterns (2 SP)

The following daemons write to `thermal_memory_archive` and likely have bare `except: conn.rollback()`:

1. `/ganuda/daemons/sacred_fire_daemon.py`
2. `/ganuda/daemons/memory_consolidation_daemon.py`
3. `/ganuda/daemons/staleness_scorer.py`
4. `/ganuda/daemons/sanctuary_state.py`
5. `/ganuda/lib/ganuda_db/__init__.py` (safe_thermal_write)

**For each file**, search for `rollback()` calls. Before every `conn.rollback()`, add a logger.warning:

```python
# BEFORE (bad — silent rollback)
except Exception:
    conn.rollback()

# AFTER (good — logged rollback)  
except Exception as e:
    logger.warning(f"ROLLBACK in {__name__}: {e}")
    conn.rollback()
```

Do NOT change the rollback behavior — just add visibility. We need to see which daemons are rolling back and why before we optimize.

## Task C: Batch Thermal Updates (1 SP)

The `staleness_scorer.py` daemon updates every row in `thermal_memory_archive` every cycle. Instead of N individual UPDATEs, batch into a single statement:

```python
# BEFORE (N updates, N transactions)
for memory in memories:
    cur.execute("UPDATE thermal_memory_archive SET freshness_score = %s WHERE id = %s", 
                (score, memory['id']))
    conn.commit()

# AFTER (1 update, 1 transaction)
updates = [(score, memory['id']) for memory in memories]
cur.executemany("UPDATE thermal_memory_archive SET freshness_score = %s WHERE id = %s", updates)
conn.commit()
```

**Reference pattern**: See `/ganuda/lib/ganuda_db/__init__.py` for how `safe_thermal_write` handles transactions.

## Acceptance Criteria

- [ ] Indexes A1 and A2 created successfully
- [ ] A3 selectivity investigated, partial index created if warranted
- [ ] All rollback() calls in 5 daemon files have logger.warning before them
- [ ] staleness_scorer.py uses batched updates
- [ ] Rollback rate measured 24h after deploy — target: <5%

## Rollback Plan

Indexes can be dropped with `DROP INDEX CONCURRENTLY`. Logger additions are additive (no behavior change). Batch update can be reverted to individual updates.

---

*For Seven Generations.*

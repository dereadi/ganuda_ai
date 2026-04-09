# JR INSTRUCTION: Fire Guard DBA Health Checks

**Task**: Add database-level health metrics to Fire Guard's emergency threshold checks
**Priority**: P1 (operational hardening — DB is single point of failure)
**Date**: 2026-03-29
**TPM**: Claude Opus
**Story Points**: 3
**Depends On**: fire_guard.py (LIVE), db_query_monitor.py (LIVE), PostgreSQL on bluefin (LIVE)
**References**: DB Tuning Waves 1-4 (Mar 26), project_internal_slas.md (query floor 500ms, rollback <5%, connection util <80%)

## Problem Statement

Fire Guard checks if PostgreSQL is reachable (TCP port 5432) and counts active connections. But it has no visibility into database HEALTH:

- A query running for 10 minutes won't trigger an alert
- Autovacuum not running for a week won't trigger an alert
- Cache hit ratio dropping to 50% won't trigger an alert
- Connection pool at 95% capacity won't trigger an alert
- Deadlocks happening every minute won't trigger an alert

`db_query_monitor.py` handles long-running query alerts separately, but Fire Guard — the central health authority — is blind to DBA-level signals. When Fire Guard says "all green," Chief should be able to trust that includes the database.

## Task 1: Add DBA Thresholds to EMERGENCY_THRESHOLDS (0.5 SP)

**File**: `/ganuda/scripts/fire_guard.py`

Add to the `EMERGENCY_THRESHOLDS` dict (line 41):

```python
EMERGENCY_THRESHOLDS = {
    # ... existing thresholds ...
    "postgres_connections": 90,        # existing
    # NEW DBA thresholds
    "postgres_connection_pct": 80,     # % of max_connections (SLA: <80%)
    "postgres_cache_hit_pct_min": 95,  # cache hit ratio floor (below = disk thrashing)
    "postgres_longest_query_sec": 120, # longest running query (SLA: 2 min max)
    "postgres_rollback_pct": 5,        # rollback rate floor (SLA: <5%)
    "postgres_vacuum_stale_hours": 48, # hours since last autovacuum on any table
    "postgres_deadlocks_1h": 3,        # deadlocks in last hour
}
```

## Task 2: Implement DBA Health Checks (2 SP)

**File**: `/ganuda/scripts/fire_guard.py`

Add a new function `check_dba_health()` that runs inside `check_emergency_thresholds()`, after the existing DB-dependent checks (line 202).

```python
def check_dba_health(cur, breaches):
    """DBA-level health checks. cur is an open cursor on the triad_federation DB."""

    # 1. Connection utilization (% of max_connections)
    try:
        cur.execute("SHOW max_connections")
        max_conns = int(cur.fetchone()[0])
        cur.execute("SELECT count(*) FROM pg_stat_activity")
        current_conns = cur.fetchone()[0]
        pct = (current_conns / max_conns) * 100
        if pct > EMERGENCY_THRESHOLDS["postgres_connection_pct"]:
            breaches.append(f"Postgres connection utilization {pct:.0f}% > {EMERGENCY_THRESHOLDS['postgres_connection_pct']}% ({current_conns}/{max_conns})")
    except Exception as e:
        logger.warning(f"DBA check (connection_pct) failed: {e}")

    # 2. Cache hit ratio
    try:
        cur.execute("""
            SELECT
                CASE WHEN (sum(heap_blks_hit) + sum(heap_blks_read)) > 0
                THEN sum(heap_blks_hit)::float / (sum(heap_blks_hit) + sum(heap_blks_read)) * 100
                ELSE 100 END
            FROM pg_statio_user_tables
        """)
        cache_hit = cur.fetchone()[0]
        if cache_hit < EMERGENCY_THRESHOLDS["postgres_cache_hit_pct_min"]:
            breaches.append(f"Postgres cache hit ratio {cache_hit:.1f}% < {EMERGENCY_THRESHOLDS['postgres_cache_hit_pct_min']}% (disk thrashing)")
    except Exception as e:
        logger.warning(f"DBA check (cache_hit) failed: {e}")

    # 3. Longest running query
    try:
        cur.execute("""
            SELECT EXTRACT(EPOCH FROM (NOW() - query_start))::int, left(query, 80)
            FROM pg_stat_activity
            WHERE state = 'active'
              AND query NOT ILIKE '%pg_stat%'
              AND query_start IS NOT NULL
            ORDER BY query_start ASC
            LIMIT 1
        """)
        row = cur.fetchone()
        if row and row[0] > EMERGENCY_THRESHOLDS["postgres_longest_query_sec"]:
            breaches.append(f"Postgres query running {row[0]}s > {EMERGENCY_THRESHOLDS['postgres_longest_query_sec']}s: {row[1]}")
    except Exception as e:
        logger.warning(f"DBA check (longest_query) failed: {e}")

    # 4. Rollback rate (last hour)
    try:
        cur.execute("""
            SELECT xact_commit, xact_rollback
            FROM pg_stat_database
            WHERE datname = current_database()
        """)
        row = cur.fetchone()
        if row and (row[0] + row[1]) > 0:
            rollback_pct = (row[1] / (row[0] + row[1])) * 100
            if rollback_pct > EMERGENCY_THRESHOLDS["postgres_rollback_pct"]:
                breaches.append(f"Postgres rollback rate {rollback_pct:.1f}% > {EMERGENCY_THRESHOLDS['postgres_rollback_pct']}% (SLA breach)")
    except Exception as e:
        logger.warning(f"DBA check (rollback_rate) failed: {e}")

    # 5. Autovacuum staleness
    try:
        cur.execute("""
            SELECT schemaname || '.' || relname,
                   EXTRACT(EPOCH FROM (NOW() - COALESCE(last_autovacuum, last_vacuum)))::int / 3600
            FROM pg_stat_user_tables
            WHERE n_live_tup > 10000
              AND (last_autovacuum IS NOT NULL OR last_vacuum IS NOT NULL)
            ORDER BY COALESCE(last_autovacuum, last_vacuum) ASC NULLS FIRST
            LIMIT 1
        """)
        row = cur.fetchone()
        if row and row[1] and row[1] > EMERGENCY_THRESHOLDS["postgres_vacuum_stale_hours"]:
            breaches.append(f"Postgres autovacuum stale: {row[0]} last vacuumed {row[1]:.0f}h ago > {EMERGENCY_THRESHOLDS['postgres_vacuum_stale_hours']}h")
    except Exception as e:
        logger.warning(f"DBA check (vacuum_stale) failed: {e}")

    # 6. Deadlocks (cumulative counter — compare to baseline)
    try:
        cur.execute("""
            SELECT deadlocks FROM pg_stat_database WHERE datname = current_database()
        """)
        deadlocks = cur.fetchone()[0]
        # Store in state file for delta comparison
        # For now, just check if non-zero (cumulative, so this needs baseline tracking)
        # TODO: Track delta via fire_guard state file
        if deadlocks > 0:
            logger.info(f"Postgres cumulative deadlocks: {deadlocks}")
    except Exception as e:
        logger.warning(f"DBA check (deadlocks) failed: {e}")
```

### Integration point

In `check_emergency_thresholds()` (line 202), after the existing DB checks, add:

```python
    # DBA health checks (same connection)
    check_dba_health(cur, breaches)
```

This reuses the existing connection instead of opening a new one.

## Task 3: Add DBA Summary to Health Page (0.5 SP)

In `render_html()`, add a DBA section that shows current values (not just alerts). This lets the health page at ganuda.us show:

- Connection utilization: 45/200 (22%)
- Cache hit ratio: 99.2%
- Longest query: 3s
- Rollback rate: 0.1%
- Last vacuum: 2h ago

Add these as metrics to the `results` dict from `run_checks()`, then render in the HTML template. Pattern follows the existing RSS memory section.

## Verification

1. Deploy and wait for next Fire Guard cycle (2 min)
2. Check health page — DBA section should appear with current values
3. Verify no false positives — clean DB should show all green
4. Intentionally test (on a test connection):
   - Run `SELECT pg_sleep(130)` — should trigger longest_query alert
   - Verify it shows up in #fire-guard Slack
5. Confirm thresholds align with internal SLAs:
   - Connection util <80% (from project_internal_slas.md)
   - Query floor converging toward 500ms (db_query_monitor handles the fine-grained tracking, Fire Guard handles the emergency ceiling)
   - Rollback <5%

## Notes

- `db_query_monitor.py` already handles per-query alerting (>90s queries, weekly top-15 report). Fire Guard's DBA checks are the EMERGENCY layer — coarser thresholds, faster cadence (2 min vs db_query_monitor's own cycle).
- Deadlock tracking needs baseline delta, not absolute count. First pass logs cumulative. Follow-up task can add delta tracking via the fire guard state file.
- All checks use `pg_stat_*` views — read-only, no locks, negligible overhead.

---

FOR SEVEN GENERATIONS

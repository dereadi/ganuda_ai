# Jr Instruction: DC-16 Phase 1 — Database Reflex Layer (Quick Wins) (FIXED)

**Task #:** 1288
**Title:** DC-16 Phase 1: Database Reflex Layer
**Date:** March 12, 2026
**Priority:** P1 — prerequisite for DC-16 separation, zero risk, immediate benefit
**Story Points:** 3
**Depends On:** None
**Council Vote:** cf4ac0aeddc7eb75 (DC-16 Longhouse, 0.858) + e878fe42772ed12d (Tier 1 unanimous)
**Replaces:** JR-DC16-PHASE1-DB-REFLEX-MAR11-2026.md (reformatted for SmartExtract)

## Context

thermal_memory_archive has 18 indexes on 174 MB of table data, producing 1,366 MB of index bloat.
6 indexes have zero scans ever. Every thermal INSERT triggers 18 index writes. jr_work_queue has
28,834 sequential scans without a composite index on its hottest query pattern. health_check_log has
404K rows with zero index usage and no retention policy. Fire Guard writes false-positive alerts at
temperature 100 to permanent identity storage because the TCP socket check on port 5432 sometimes
fails even though psycopg2 connects fine (different auth/protocol paths).

## Constraints

- Use `DROP INDEX IF EXISTS` and `CREATE INDEX CONCURRENTLY`. No table locks.
- Do NOT touch sacred or canonical memories. Only drop indexes confirmed at zero scans.
- Retention DELETE only removes rows older than threshold. Verify row counts after.
- All SQL runs on bluefin (192.168.132.222) PostgreSQL, database `zammad_production`, user `claude`.
- Do NOT delete from thermal_memory_archive (identity tier — never purge).
- Do NOT modify table structure (no ALTER TABLE ADD/DROP COLUMN — that is Phase 2+).
- Do NOT run DELETE without WHERE clause.

## Steps

### Step 1: Drop unused indexes on thermal_memory_archive

These 6 indexes have ZERO scans. They cost writes and give nothing back.

```sql
DROP INDEX IF EXISTS idx_thermal_memory_phase_coherence;
DROP INDEX IF EXISTS idx_thermal_keywords;
DROP INDEX IF EXISTS idx_thermal_tags;
DROP INDEX IF EXISTS idx_thermal_valid_range;
DROP INDEX IF EXISTS idx_thermal_source_node;
DROP INDEX IF EXISTS idx_thermal_source_triad;
```

### Step 2: Verify remaining indexes on thermal_memory_archive

```sql
SELECT indexrelname, idx_scan
FROM pg_stat_user_indexes
WHERE relname = 'thermal_memory_archive'
ORDER BY idx_scan;
```

### Step 3: Tune autovacuum on thermal_memory_archive

Default scale_factor 0.2 means vacuum triggers after ~18.5K dead tuples on 92K rows.
Set to 0.01 so it triggers after ~930 dead tuples. Much more responsive for a high-write table.

```sql
ALTER TABLE thermal_memory_archive SET (
  autovacuum_vacuum_scale_factor = 0.01,
  autovacuum_analyze_scale_factor = 0.005,
  autovacuum_vacuum_cost_delay = 2
);
```

### Step 4: Verify autovacuum settings

```sql
SELECT reloptions FROM pg_class WHERE relname = 'thermal_memory_archive';
```

### Step 5: Retention purge for health_check_log

404K rows, zero index usage, 38 MB. Keep 7 days.

```sql
DELETE FROM health_check_log WHERE created_at < NOW() - INTERVAL '7 days';
```

### Step 6: Verify health_check_log retention

```sql
SELECT COUNT(*), MIN(created_at), MAX(created_at) FROM health_check_log;
```

### Step 7: Tag health_check_log retention policy

```sql
COMMENT ON TABLE health_check_log IS 'Retention: 7 days. DC-16 telemetry tier. Auto-purge older rows.';
```

### Step 8: Retention purge for fedattn tables

222K rows each, 34 MB and 28 MB. Keep 30 days.

```sql
DELETE FROM fedattn_contributions WHERE created_at < NOW() - INTERVAL '30 days';
DELETE FROM fedattn_sessions WHERE created_at < NOW() - INTERVAL '30 days';
```

### Step 9: Verify fedattn retention

```sql
SELECT 'fedattn_sessions' AS tbl, COUNT(*) FROM fedattn_sessions
UNION ALL
SELECT 'fedattn_contributions', COUNT(*) FROM fedattn_contributions;
```

### Step 10: Tag fedattn retention policy

```sql
COMMENT ON TABLE fedattn_sessions IS 'Retention: 30 days. DC-16 telemetry tier.';
COMMENT ON TABLE fedattn_contributions IS 'Retention: 30 days. DC-16 telemetry tier.';
```

### Step 11: Create composite index on jr_work_queue for status+created_at queries

28,834 seq scans on this table. Most queries filter by status and order by created_at.

```sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jr_work_queue_status_created
ON jr_work_queue (status, created_at DESC);
```

### Step 12: Create partial composite index on jr_work_queue for pending poll

The TPM daemon polling pattern filters status='pending' and orders by priority, created_at.

```sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jr_work_queue_status_priority
ON jr_work_queue (status, priority ASC, created_at ASC)
WHERE status = 'pending';
```

### Step 13: Verify jr_work_queue indexes

```sql
SELECT indexrelname, idx_scan
FROM pg_stat_user_indexes
WHERE relname = 'jr_work_queue';
```

### Step 14: Fix Fire Guard false positive — replace TCP socket check with psycopg2 for PostgreSQL

The issue: Fire Guard uses `check_port(ip, 5432)` via TCP socket to check bluefin PostgreSQL.
The socket check sometimes returns false (connection refused or timeout) while psycopg2 connects
and queries fine. Replace with a real DB connection test for the PostgreSQL entry only.

Add a `check_postgres_db` function after the existing `check_port` function, then update
the bluefin REMOTE_CHECKS entry to use `"PostgreSQL-DB"` as a signal for the new check path.

**File:** `/ganuda/scripts/fire_guard.py`

```python
def check_postgres_db(host, port=5432, timeout=5):
    """Check PostgreSQL by actually connecting, not just TCP socket.

    Eliminates false-positive alerts where socket check fails but DB is up.
    DC-16 Phase 1 fix.
    """
    import psycopg2
    try:
        conn = psycopg2.connect(
            host=host, port=port,
            dbname=os.environ.get("CHEROKEE_DB_NAME", "zammad_production"),
            user=os.environ.get("CHEROKEE_DB_USER", "claude"),
            password=os.environ.get("CHEROKEE_DB_PASS", ""),
            connect_timeout=timeout
        )
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return True
    except Exception:
        return False
```

### Step 15: Wire check_postgres_db into Fire Guard remote checks

In `/ganuda/scripts/fire_guard.py`, find the `run_checks()` function. In the remote port
check loop, add a special case: when `label == "PostgreSQL"`, call `check_postgres_db(ip, port)`
instead of `check_port(ip, port)`.

**Modify:** `/ganuda/scripts/fire_guard.py`

Find this block in `run_checks()`:
```python
    # Remote ports
    for node, checks in REMOTE_CHECKS.items():
        for ip, port, label in checks:
            up = check_port(ip, port)
```

Replace with:
```python
    # Remote ports
    for node, checks in REMOTE_CHECKS.items():
        for ip, port, label in checks:
            if label == "PostgreSQL":
                up = check_postgres_db(ip, port)
            else:
                up = check_port(ip, port)
```

### Step 16: Thermalize DC-16 Phase 1 results

```sql
INSERT INTO thermal_memory_archive (original_content, temperature_score, domain_tag, sacred_pattern, memory_hash)
VALUES (
  'DC-16 Phase 1 complete. Dropped 6 unused indexes (~17 MB reclaimed, 6 fewer index writes per INSERT). Tuned autovacuum (scale_factor 0.01). Retention applied: health_check_log 7d, fedattn 30d. Added jr_work_queue composite indexes. Fixed Fire Guard TCP socket false positive with psycopg2 connection test.',
  72, 'infrastructure', false,
  encode(sha256(('DC-16-Phase1-' || NOW()::text)::bytea), 'hex')
);
```

## Acceptance Criteria

1. `SELECT count(*) FROM pg_stat_user_indexes WHERE relname = 'thermal_memory_archive'` returns 12 (was 18).
2. `SELECT reloptions FROM pg_class WHERE relname = 'thermal_memory_archive'` shows custom autovacuum settings.
3. `SELECT count(*) FROM health_check_log` is less than 50,000 (was 404K).
4. `SELECT indexrelname FROM pg_stat_user_indexes WHERE relname = 'jr_work_queue'` shows new composite indexes.
5. No new `FIRE GUARD ALERT.*bluefin/PostgreSQL` thermals after fix deployed (monitor for 1 hour).
6. Thermal result stored (Step 16).

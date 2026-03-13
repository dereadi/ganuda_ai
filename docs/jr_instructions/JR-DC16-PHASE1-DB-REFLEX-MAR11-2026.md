# JR INSTRUCTION: DC-16 Phase 1 — Database Reflex Layer (Quick Wins)

**Task**: Drop unused indexes, tune autovacuum, create retention policies, fix Fire Guard false positive, add jr_work_queue composite index
**Priority**: P1 — prerequisite for DC-16 separation, zero risk, immediate benefit
**Date**: 2026-03-11
**TPM**: Claude Opus
**Story Points**: 3
**Depends On**: None
**Council Vote**: cf4ac0aeddc7eb75 (DC-16 Longhouse, 0.858) + e878fe42772ed12d (Tier 1 unanimous)

## Problem Statement

thermal_memory_archive has 18 indexes on 174 MB of table data, producing 1,366 MB of index bloat. 6 indexes have zero scans ever. Every thermal INSERT triggers 18 index writes. jr_work_queue has 28,834 sequential scans without a composite index on its hottest query pattern. health_check_log has 404K rows with zero index usage and no retention policy. Fire Guard writes false-positive alerts at temperature 100 to permanent identity storage because pg_isready returns "no response" while psycopg2 connects fine.

## What You're Building

### Step 1: Drop Unused Indexes on thermal_memory_archive

Connect to bluefin (192.168.132.222) PostgreSQL as claude user.

```sql
-- These 6 indexes have ZERO scans. They cost writes and give nothing back.
DROP INDEX IF EXISTS idx_thermal_memory_phase_coherence;  -- 5.7 MB, 0 scans
DROP INDEX IF EXISTS idx_thermal_keywords;                 -- 2.9 MB, 0 scans
DROP INDEX IF EXISTS idx_thermal_tags;                     -- 2.7 MB, 0 scans
DROP INDEX IF EXISTS idx_thermal_valid_range;              -- 1.9 MB, 0 scans
DROP INDEX IF EXISTS idx_thermal_source_node;              -- 1.9 MB, 0 scans
DROP INDEX IF EXISTS idx_thermal_source_triad;             -- 1.9 MB, 0 scans
```

After dropping, verify: `SELECT indexrelname, idx_scan FROM pg_stat_user_indexes WHERE relname = 'thermal_memory_archive' ORDER BY idx_scan;`

Should show 12 remaining indexes, all with scan counts > 0.

### Step 2: Tune Autovacuum on thermal_memory_archive

```sql
-- Default scale_factor 0.2 means vacuum triggers after ~18.5K dead tuples on 92K rows
-- Set to 0.01: triggers after ~930 dead tuples. Much more responsive.
ALTER TABLE thermal_memory_archive SET (
  autovacuum_vacuum_scale_factor = 0.01,
  autovacuum_analyze_scale_factor = 0.005,
  autovacuum_vacuum_cost_delay = 2
);
```

Verify: `SELECT reloptions FROM pg_class WHERE relname = 'thermal_memory_archive';`

### Step 3: Retention Policy for health_check_log

```sql
-- 404K rows, zero index usage, 38 MB. Keep 7 days.
DELETE FROM health_check_log WHERE created_at < NOW() - INTERVAL '7 days';

-- Verify remaining count
SELECT COUNT(*), MIN(created_at), MAX(created_at) FROM health_check_log;
```

Then add a note as a comment for the future retention daemon:
```sql
COMMENT ON TABLE health_check_log IS 'Retention: 7 days. DC-16 telemetry tier. Auto-purge older rows.';
```

### Step 4: Retention Policy for fedattn_sessions and fedattn_contributions

```sql
-- 222K rows each, 34 MB and 28 MB. Keep 30 days.
DELETE FROM fedattn_contributions WHERE created_at < NOW() - INTERVAL '30 days';
DELETE FROM fedattn_sessions WHERE created_at < NOW() - INTERVAL '30 days';

SELECT COUNT(*) FROM fedattn_sessions;
SELECT COUNT(*) FROM fedattn_contributions;

COMMENT ON TABLE fedattn_sessions IS 'Retention: 30 days. DC-16 telemetry tier.';
COMMENT ON TABLE fedattn_contributions IS 'Retention: 30 days. DC-16 telemetry tier.';
```

### Step 5: Composite Index on jr_work_queue

```sql
-- 28,834 seq scans on this table. Most queries filter by status + order by created_at.
CREATE INDEX CONCURRENTLY idx_jr_work_queue_status_created
ON jr_work_queue (status, created_at DESC);

-- Also useful for the TPM daemon polling pattern
CREATE INDEX CONCURRENTLY idx_jr_work_queue_status_priority
ON jr_work_queue (status, priority ASC, created_at ASC)
WHERE status = 'pending';
```

Verify: `SELECT indexrelname, idx_scan FROM pg_stat_user_indexes WHERE relname = 'jr_work_queue';`

### Step 6: Fix Fire Guard False Positive

The issue: Fire Guard uses `pg_isready -h 192.168.132.222 -p 5432` to check bluefin PostgreSQL. pg_isready returns "no response" but psycopg2 connects and queries successfully. Different auth paths.

Find the Fire Guard health check code in `/ganuda/scripts/fire_guard.py`. Locate the PostgreSQL check for bluefin. Replace the pg_isready check with a lightweight psycopg2 connection test:

```python
# INSTEAD OF: subprocess pg_isready
# USE: actual DB connection test
import psycopg2

def check_postgres(host, port=5432, timeout=5):
    """Check PostgreSQL by actually connecting, not just pg_isready."""
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

This eliminates the false-positive alerts that write temperature 100 thermals to permanent identity storage for a non-event.

### Step 7: Thermalize Results

```sql
INSERT INTO thermal_memory_archive (original_content, temperature_score, domain_tag, sacred_pattern, memory_hash)
VALUES (
  'DC-16 Phase 1 complete. Dropped 6 unused indexes (~17 MB reclaimed, 6 fewer index writes per INSERT). Tuned autovacuum (scale_factor 0.01). Retention applied: health_check_log 7d, fedattn 30d. Added jr_work_queue composite indexes. Fixed Fire Guard pg_isready false positive.',
  72, 'infrastructure', false,
  encode(sha256(('DC-16-Phase1-' || NOW()::text)::bytea), 'hex')
);
```

## Constraints

- **DC-16**: This is the reflex layer. Quick wins. Zero risk.
- **DC-7**: Do NOT touch sacred or canonical memories. Only drop indexes confirmed at zero scans.
- **Turtle**: Use `DROP INDEX IF EXISTS` and `CREATE INDEX CONCURRENTLY`. No table locks.
- **Crawdad**: Retention DELETE only removes rows older than threshold. Verify row counts after.
- All work on bluefin (192.168.132.222) PostgreSQL.
- Fire Guard fix must be tested: verify the false positive stops appearing in thermal_memory_archive after the change.

## Target Files

- bluefin PostgreSQL: 6 index drops, 1 ALTER TABLE, 3 DELETE + COMMENT, 2 CREATE INDEX (SQL only)
- `/ganuda/scripts/fire_guard.py` — replace pg_isready with psycopg2 check (MODIFY)

## Acceptance Criteria

- `SELECT count(*) FROM pg_stat_user_indexes WHERE relname = 'thermal_memory_archive'` returns 12 (was 18)
- `SELECT reloptions FROM pg_class WHERE relname = 'thermal_memory_archive'` shows custom autovacuum settings
- `SELECT count(*) FROM health_check_log` < 50,000 (was 404K)
- `SELECT indexrelname FROM pg_stat_user_indexes WHERE relname = 'jr_work_queue'` shows new composite indexes
- No new `FIRE GUARD ALERT.*bluefin/PostgreSQL` thermals after fix deployed (monitor for 1 hour)
- Thermal result stored

## DO NOT

- Drop any index with scan count > 0
- Touch sacred or canonical memories
- Delete from thermal_memory_archive (identity — never purge)
- Modify table structure (no ALTER TABLE ADD/DROP COLUMN — that's Phase 2+)
- Run DELETE without WHERE clause

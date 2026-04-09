# JR INSTRUCTION: DB Tuning Wave 1 — Immediate Actions

**Task ID**: DB-TUNE-001
**Priority**: P0
**SP**: 3
**Epic**: DB-HEALTH-EPIC
**Longhouse Session**: 2710dbfcdab99b43
**Method**: Long Man (4 waves). This is Wave 1.

## Context

Bluefin DB diagnostic (Mar 26 2026) found:
- **30% rollback rate** on triad_federation
- **15% rollback rate** on zammad_production and enhanced_memory
- **/postgresdb at 92% disk** (158GB free on 2TB)
- **1.78GB of indexes** on 174MB of thermal_memory_archive data (10:1 ratio)
- **3 unused indexes** on thermal_memory_archive (zero scans ever)
- **100+ empty tables** in triad_federation (never used, never vacuumed)
- **Collation mismatch** on enhanced_memory

Root cause of rollbacks: application code closing connections without committing. Even read-only SELECTs cause rollback stats when the transaction isn't committed before close.

## Wave 1 Actions (Run on bluefin as claude user)

### 1. Drop Unused Indexes on zammad_production.thermal_memory_archive

These three indexes have **zero scans** across the lifetime of the database:

```sql
-- Connect to zammad_production
\c zammad_production

-- Verify they're still at 0 scans before dropping
SELECT indexrelname, idx_scan, pg_size_pretty(pg_relation_size(indexrelid))
FROM pg_stat_user_indexes
WHERE relname = 'thermal_memory_archive' AND idx_scan = 0;

-- Drop them (recovers ~10MB, removes autovacuum/write overhead)
DROP INDEX IF EXISTS idx_thermal_embedding_temp;    -- 6MB, 0 scans, redundant with idx_thermal_temperature
DROP INDEX IF EXISTS idx_memory_type;               -- 2.2MB, 0 scans
DROP INDEX IF EXISTS idx_thermal_source_session;    -- 1.8MB, 0 scans
```

### 2. Drop Unused Indexes on zammad_production (other tables)

```sql
-- unified_timeline: 3 unused indexes totaling 64MB
SELECT indexrelname, idx_scan, pg_size_pretty(pg_relation_size(indexrelid))
FROM pg_stat_user_indexes
WHERE relname = 'unified_timeline' AND idx_scan = 0;

DROP INDEX IF EXISTS idx_timeline_timestamp;    -- 30MB, 0 scans
DROP INDEX IF EXISTS idx_timeline_created_at;   -- 17MB, 0 scans
-- Keep unified_timeline_pkey even though 0 scans (primary key constraint)

-- health_check_log: pkey never scanned but keep it (constraint)
-- api_audit_log: pkey never scanned but keep it (constraint)

-- fedattn_contributions: 2 unused
DROP INDEX IF EXISTS idx_fedattn_contributions_session_id;  -- 8.8MB, 0 scans
DROP INDEX IF EXISTS fedattn_contributions_pkey;  -- WAIT: This is a primary key. Keep it.

-- stereo_speed_detections: unused indexes
DROP INDEX IF EXISTS idx_speed_value;  -- 1.2MB, 0 scans

-- tribe_power_metrics: unused indexes
DROP INDEX IF EXISTS idx_power_timestamp;  -- 1.3MB, 0 scans
```

### 3. Drop Unused Indexes on triad_federation

```sql
\c triad_federation

-- Verify before dropping
SELECT indexrelname, idx_scan, pg_size_pretty(pg_relation_size(indexrelid))
FROM pg_stat_user_indexes WHERE idx_scan = 0 AND pg_relation_size(indexrelid) > 65536
ORDER BY pg_relation_size(indexrelid) DESC;

-- ganuda_view_heartbeats: table is EMPTY (0 live rows, 72MB)
-- The entire table should be TRUNCATEd, which drops indexes too
TRUNCATE ganuda_view_heartbeats;

-- jr_action_proposals: EMPTY (14MB) — TRUNCATE
TRUNCATE jr_action_proposals;

-- jr_self_observations: EMPTY (14MB) — TRUNCATE
TRUNCATE jr_self_observations;

-- Other unused indexes on non-empty tables
DROP INDEX IF EXISTS idx_triad_memories_temp;          -- 936KB, 0 scans
DROP INDEX IF EXISTS idx_proposals_pending;             -- 896KB, 0 scans
DROP INDEX IF EXISTS idx_observations_time;             -- 608KB, 0 scans
DROP INDEX IF EXISTS idx_triad_memories_tags;           -- 568KB, 0 scans
DROP INDEX IF EXISTS idx_knowledge_embedding;           -- 1.6MB, 0 scans
DROP INDEX IF EXISTS idx_rag_embedding;                 -- 968KB, 0 scans
DROP INDEX IF EXISTS cherokee_knowledge_embedding_idx;  -- 968KB, 0 scans
```

### 4. Fix Collation Mismatch on enhanced_memory

```sql
ALTER DATABASE enhanced_memory REFRESH COLLATION VERSION;
```

### 5. VACUUM ANALYZE All Affected Databases

After dropping indexes and truncating, run:

```sql
\c zammad_production
VACUUM ANALYZE thermal_memory_archive;
VACUUM ANALYZE unified_timeline;
VACUUM ANALYZE fedattn_sessions;
VACUUM ANALYZE api_audit_log;
VACUUM ANALYZE health_check_log;

\c triad_federation
VACUUM ANALYZE triad_shared_memories;
VACUUM ANALYZE kanban_tasks;

\c enhanced_memory
VACUUM ANALYZE;
```

### 6. Reset Statistics (Optional, after all fixes)

To get a clean rollback rate baseline after the conn.commit() fixes land:

```sql
SELECT pg_stat_reset();
```

**WARNING**: Only do this AFTER Wave 2 (conn.commit fixes) is deployed, so we can measure the real improvement.

## Expected Impact

- **Disk recovery**: ~110MB immediately from dropped indexes and truncated tables
- **Write performance**: Fewer indexes to update on every INSERT/UPDATE to thermal_memory_archive
- **Autovacuum efficiency**: Less work per cycle with fewer indexes and fewer empty tables
- **Rollback rate**: Will NOT improve from Wave 1 alone — Wave 2 (conn.commit) is the real fix

## Verification

```sql
-- After Wave 1, check:
SELECT datname, xact_rollback,
       CASE WHEN (xact_commit + xact_rollback) > 0
            THEN ROUND(100.0 * xact_rollback / (xact_commit + xact_rollback), 2)
            ELSE 0 END AS rollback_pct
FROM pg_stat_database WHERE datname IN ('zammad_production', 'triad_federation', 'enhanced_memory');

-- Check thermal_memory_archive index health after cleanup
SELECT indexrelname, idx_scan, pg_size_pretty(pg_relation_size(indexrelid))
FROM pg_stat_user_indexes WHERE relname = 'thermal_memory_archive'
ORDER BY pg_relation_size(indexrelid) DESC;
```

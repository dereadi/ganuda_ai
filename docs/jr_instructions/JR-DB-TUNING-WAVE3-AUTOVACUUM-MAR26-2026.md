# JR INSTRUCTION: DB Tuning Wave 3 — Autovacuum & Table Hygiene

**Task ID**: DB-TUNE-003
**Priority**: P1
**SP**: 2
**Epic**: DB-HEALTH-EPIC

## Context

Most tables outside thermal_memory_archive have **never been autovacuumed**. The default autovacuum settings (threshold=50, scale_factor=0.2) are fine for most tables, but several high-write tables need per-table tuning, and the triad_federation database is 80% empty tables that should be cleaned up.

## 1. Per-Table Autovacuum Tuning (zammad_production)

### fedattn_sessions (198K rows, never vacuumed, 5K dead tuples)

```sql
\c zammad_production

-- This table gets constant inserts. Lower the threshold.
ALTER TABLE fedattn_sessions SET (
    autovacuum_vacuum_threshold = 1000,
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_threshold = 500,
    autovacuum_analyze_scale_factor = 0.02
);

VACUUM ANALYZE fedattn_sessions;
```

### api_audit_log (62K rows, never vacuumed)

```sql
ALTER TABLE api_audit_log SET (
    autovacuum_vacuum_threshold = 500,
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_threshold = 200,
    autovacuum_analyze_scale_factor = 0.02
);

VACUUM ANALYZE api_audit_log;
```

### health_check_log (68K rows, never vacuumed)

```sql
ALTER TABLE health_check_log SET (
    autovacuum_vacuum_threshold = 500,
    autovacuum_vacuum_scale_factor = 0.1
);

VACUUM ANALYZE health_check_log;
```

### thermal_memory_archive (95K rows, autovacuum working but HNSW reindex needed)

The IVFFlat index `idx_thermal_embedding_cosine` is 1.3GB for 95K rows. After the unused index drops in Wave 1, reindex:

```sql
-- This will take a few minutes and temporarily block writes
REINDEX INDEX CONCURRENTLY idx_thermal_embedding_cosine;
```

**WARNING**: `REINDEX CONCURRENTLY` requires PostgreSQL 12+. Verify version first:
```sql
SELECT version();
```

If version < 12, schedule the REINDEX during a low-traffic window (Sunday 3 AM).

## 2. triad_federation Cleanup

### Empty Tables Audit

triad_federation has **100+ empty tables** consuming ~105MB of disk (table structures + indexes on empty data). Most were created for features that were later moved to zammad_production or never implemented.

**Tables with data (KEEP):**
- `triad_shared_memories` (23K rows, 57MB) — active
- `kanban_tasks` (69 rows) — active
- `cmdb_ansible_runs` (41 rows) — active
- `cmdb_nodes` (6 rows) — active
- `project_specifications` (4 rows) — active

**Tables that are EMPTY but may be referenced by code:**

Before dropping any table, verify no code references it:

```bash
cd /ganuda
grep -r "TABLE_NAME" lib/ daemons/ scripts/ services/ jr_executor/ telegram_bot/ --include="*.py" -l
```

**Safe to TRUNCATE (recovers space, keeps schema):**
- `ganuda_view_heartbeats` (72MB, 0 rows) — heartbeat agent writes here but data is stale
- `jr_action_proposals` (14MB, 0 rows)
- `jr_self_observations` (14MB, 0 rows)

**Consider DROP for tables with no code references:**
Run the grep check above for each table. If no hits, the table is dead weight. But **do NOT drop without the grep check** — some tables may be created by migrations that will recreate them.

### VACUUM the database

```sql
\c triad_federation
VACUUM FULL ANALYZE;
```

**NOTE**: `VACUUM FULL` rewrites the entire table and reclaims disk space. It takes an exclusive lock, so schedule during low traffic. Regular `VACUUM ANALYZE` is safe anytime but doesn't reclaim disk.

## 3. enhanced_memory Cleanup

This database appears to be largely unused (tiny tables, collation mismatch). After Wave 1 fixes the collation:

```sql
\c enhanced_memory
VACUUM ANALYZE;
```

If investigation confirms no active code uses this database, consider marking it for deprecation.

## Verification

After all Wave 3 changes:

```sql
-- Check autovacuum is now touching the configured tables
SELECT relname, last_autovacuum, autovacuum_count, n_dead_tup
FROM pg_stat_user_tables
WHERE relname IN ('fedattn_sessions', 'api_audit_log', 'health_check_log', 'thermal_memory_archive')
ORDER BY relname;

-- Check disk usage improvement
SELECT pg_size_pretty(pg_database_size('zammad_production')) as zammad,
       pg_size_pretty(pg_database_size('triad_federation')) as triad,
       pg_size_pretty(pg_database_size('enhanced_memory')) as enhanced;
```

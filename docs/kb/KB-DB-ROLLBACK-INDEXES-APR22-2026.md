# KB — DB Health Indexes Migration (Apr 22 2026)

**Filed:** 2026-04-22 by TPM
**Closes kanban duyuktv #1579** (redispatched-from-1498, DB Health: rollback-rate fix indexes)
**Status:** SHIPPED to production

## Scope

Add missing non-PK hot-path indexes on `jr_task_announcements` + `elisi_state` and drop a redundant index. Migration executed as a single transaction against zammad_production on bluefin (10.100.0.2).

## Changes

### jr_task_announcements

| Index | Change | Purpose |
|---|---|---|
| `idx_jr_task_announcements_status` (status, announced_at DESC) | **pre-existing** — kept | Hot path: "get next open task by status, ordered by recency" |
| `idx_jr_task_announcements_assigned_to` (assigned_to) WHERE assigned_to IS NOT NULL | **ADDED** | Hot path: "what tasks is JR X working?" — partial index skips NULL (unassigned) rows |
| `idx_jr_task_announcements_task_type` (task_type, status) | **ADDED** | Hot path: "get open tasks of type Y" — dispatcher capability matching |

### elisi_state

| Index | Change | Purpose |
|---|---|---|
| `idx_elisi_state_key` (key) | **DROPPED** | Redundant — `elisi_state_pkey` already provides btree on `key`. Was wasting disk + slowing writes with no read benefit |
| `idx_elisi_state_updated_at` (updated_at DESC) | **ADDED** | Hot path: staleness-scoring queries filtering by `updated_at > cutoff` |

## Verification

```sql
SELECT indexname, indexdef FROM pg_indexes
WHERE tablename IN ('jr_task_announcements','elisi_state')
ORDER BY tablename, indexname;
```

Returns all 6 expected indexes:
- `elisi_state_pkey`
- `idx_elisi_state_updated_at`
- `idx_jr_task_announcements_assigned_to`
- `idx_jr_task_announcements_status`
- `idx_jr_task_announcements_task_type`
- `jr_task_announcements_pkey`

## Why this matters

Original JR-DB-HEALTH-ROLLBACK-FIX-APR06-2026.md flagged that high rollback rates correlated with missing indexes on hot-path queries. Task #1498 (the original attempt) failed via Jr. Scope was split into two atomic replacements:
- #1579 (this KB) — the index migration
- #1580 — logger.warning before conn.rollback() in daemons (still pending)

## Monitoring

Expected observations over the next 24 hours:
- `pg_stat_user_indexes.idx_scan` count > 0 for all three new indexes
- Reduced sequential scan rate on jr_task_announcements for type/assigned-to queries
- Reduced sequential scan rate on elisi_state for updated_at-range queries

Check via:
```sql
SELECT indexrelname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname='public' AND relname IN ('jr_task_announcements','elisi_state');
```

## Rollback

Single-statement rollback if any index causes regression:
```sql
DROP INDEX IF EXISTS idx_jr_task_announcements_assigned_to;
DROP INDEX IF EXISTS idx_jr_task_announcements_task_type;
DROP INDEX IF EXISTS idx_elisi_state_updated_at;
CREATE INDEX idx_elisi_state_key ON elisi_state (key);  -- restore redundant index if needed
```

## Cross-references

- Original failed attempt: kanban #1498 (JR failed, scope too big)
- Redispatch ticket: kanban #1579 (this KB's work)
- Companion ticket: kanban #1580 (rollback logging sweep) — still pending
- Source design: /ganuda/docs/jr_instructions/JR-DB-HEALTH-ROLLBACK-FIX-APR06-2026.md

## Apr 22 2026 TPM

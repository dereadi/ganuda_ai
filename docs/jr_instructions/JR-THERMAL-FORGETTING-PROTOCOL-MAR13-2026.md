# JR-THERMAL-FORGETTING-PROTOCOL-MAR13-2026

## Task: Thermal Forgetting Protocol — Active Memory Pruning

**Priority**: 1 (Critical)
**Source**: Longhouse c4e68ce0fcea60a3 (consensus with standing dissent), Foundation Agents GAP 3
**Kanban**: FA-GAP3-001
**Design Constraints**: DC-9 (Waste Heat Limit), DC-14 (Three-Body Memory)

## Context

126,000+ thermal memories. 1.3GB HNSW pgvector index. 18 indexes, 6 unused. Nothing is ever deleted. Temperature decays but cold memories accumulate forever. The Foundation Agents paper cites Lyfe Agents and TiM (Think-in-Memory) for active forgetting. Turtle: "Not everything deserves to be remembered — this is wisdom."

## Current State

```sql
-- As of Mar 13 2026:
-- thermal_memory_archive: ~126K rows
-- Data: 174 MB
-- Indexes: 1,366 MB (8x the data!)
-- HNSW embedding index: 1.3 GB alone
-- Sacred thermals: ~1,400 (sacred_pattern = true)
-- Growth rate: ~600/day baseline, spikes to 31K/week
```

## What to Build

### 1. Forgetting Criteria (the pruning rules)

A thermal memory is eligible for forgetting when ALL of these are true:
- `temperature_score < 10` (cold — hasn't been accessed or referenced in a long time)
- `sacred_pattern = false` (never sacred — sacred thermals are NEVER forgotten)
- `access_count < 3` (rarely accessed — not useful)
- `created_at < NOW() - INTERVAL '30 days'` (at least 30 days old)
- NOT referenced by any `thermal_relationships` or `thermal_entity_links` row
- NOT referenced by any `council_votes.responses` JSONB (thermal context injected into votes)

### 2. Forgetting Script

Create `/ganuda/scripts/thermal_forget.py`:

```python
# Phase 1: ARCHIVE, don't delete
# Move eligible thermals to a cold_thermal_archive table (same schema, no indexes)
# This is reversible — Turtle's wisdom: "archive before you forget"

# Phase 2 (future): After 90 days in cold archive with zero access, DELETE

# The script should:
# 1. Query eligible thermals using criteria above
# 2. INSERT INTO cold_thermal_archive SELECT ...
# 3. DELETE FROM thermal_memory_archive WHERE id IN (archived_ids)
# 4. Log: how many archived, how much space freed, timestamp
# 5. REINDEX the HNSW index if >1000 rows were removed (expensive but necessary)
```

### 3. Cold Archive Table

```sql
CREATE TABLE IF NOT EXISTS cold_thermal_archive (
    LIKE thermal_memory_archive INCLUDING ALL
);
-- NO HNSW index on cold archive. That's the whole point.
-- Keep a basic btree on id and created_at for retrieval if needed.
```

### 4. Systemd Timer

`/ganuda/config/systemd/thermal-forget.timer` — run weekly, Sunday 3 AM CT (after ritual-review).

### 5. Drop Unused Indexes

Query `pg_stat_user_indexes` for thermal_memory_archive indexes with `idx_scan = 0`. Drop them. Each unused index is dead weight on every INSERT.

## Files to Create
- `/ganuda/scripts/thermal_forget.py` — the forgetting script
- `/ganuda/config/systemd/thermal-forget.service` — systemd unit
- `/ganuda/config/systemd/thermal-forget.timer` — weekly timer

## Files to Read (for context)
- `/ganuda/scripts/fire_guard.py` — understand thermal_memory_archive access patterns
- `/ganuda/lib/specialist_council.py` — understand how thermals are injected into council context (RAG)

## Acceptance Criteria
1. Cold archive table created with no HNSW index
2. Forgetting script moves eligible thermals (cold + not sacred + low access + old + no references)
3. Sacred thermals are NEVER touched — add explicit guard with loud logging if sacred thermal is in candidate set
4. Script logs: count archived, space freed, duration
5. Unused indexes identified and dropped (with council approval if >100MB)
6. HNSW reindex triggered if >1000 rows removed
7. Timer configured for weekly Sunday 3 AM

## What NOT to Do
- Do NOT delete sacred thermals. Ever. Under any condition. This is a hard invariant.
- Do NOT delete thermals referenced by council votes. Those are the audit trail.
- Do NOT skip the cold archive phase. Delete comes in Phase 2 after 90 days of cold storage.
- Do NOT reindex HNSW on every run. Only when >1000 rows removed (it's expensive).
- Do NOT run during business hours. Sunday 3 AM only.

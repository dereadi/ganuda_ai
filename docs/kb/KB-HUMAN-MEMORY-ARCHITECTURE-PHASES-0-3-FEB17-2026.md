# KB: Human Memory Architecture — Phases 0-3
**Date**: February 17, 2026
**Kanban**: #1813
**Sprint**: RC-2026-02E
**Story Points**: 13

## Summary

The Human Memory Architecture project applies neuroscience principles to the Cherokee AI Federation's thermal memory system. Four phases were deployed on Feb 17 2026, each addressing a different aspect of how biological memory systems maintain integrity.

## Phase 0: Retrieval Access Logging

**Neuroscience basis**: Every act of remembering is also an act of rewriting. Tracking access patterns reveals which memories are being modified most.

**Implementation**: Both semantic search and keyword fallback paths in `specialist_council.py` now increment `access_count` and update `last_access` on every retrieval.

```sql
UPDATE thermal_memory_archive
SET access_count = COALESCE(access_count, 0) + 1,
    last_access = NOW()
WHERE id = ANY(retrieved_ids)
```

**Location**: specialist_council.py lines 180-189 (semantic) and 382-391 (keyword fallback)

## Phase 1: Ripple Retrieval

**Neuroscience basis**: Memory activation spreads through associative networks — recalling one memory activates linked memories.

**Implementation**: After primary retrieval, follows `memory_links` graph to find connected memories and adds them to results if above similarity threshold.

**Location**: specialist_council.py (Phase 1 block after Phase 0)

## Phase 2: Reliability Inversion (Temperature Reliability Penalty)

**Neuroscience basis**: Memories recalled frequently undergo reconsolidation each time, introducing drift. A memory accessed 200 times is LESS reliable than one accessed 3 times.

**Implementation**: Frequently-accessed memories receive a similarity penalty during RAG scoring:

```python
penalty = min((access_count - 2) * 0.02, 0.30)
adjusted_sim = sim * (1.0 - penalty)
```

| Access Count | Penalty |
|-------------|---------|
| 0-2 | 0% (normal) |
| 3 | 2% |
| 10 | 16% |
| 15+ | 30% (capped) |

**Exemptions**: Sacred memories (`sacred_pattern=true`) are NEVER penalized — they are deliberately protected from reconsolidation drift.

**Location**: specialist_council.py, between `conn.close()` and Phase 1 ripple retrieval

## Phase 3: Co-Retrieval Tracking

**Neuroscience basis**: When memories are recalled together, they undergo linked reconsolidation — each memory's context "contaminates" the other. Suspiciously co-dependent memory clusters indicate potential contamination.

**Implementation**: Logs which memories are retrieved together using a deterministic `group_hash` (SHA256 of sorted memory IDs, truncated to 16 chars).

**Table**: `memory_co_retrieval`
```sql
CREATE TABLE memory_co_retrieval (
    id SERIAL PRIMARY KEY,
    group_hash VARCHAR(16) NOT NULL,
    memory_ids INTEGER[] NOT NULL,
    query_preview TEXT,
    retrieved_at TIMESTAMP DEFAULT NOW()
);
```

**Analysis query** (future use):
```sql
SELECT group_hash, COUNT(*) as freq
FROM memory_co_retrieval
GROUP BY group_hash
HAVING COUNT(*) > 10
ORDER BY freq DESC
```

**Location**: specialist_council.py line 190 (primary semantic search path only)

## Deployment Notes

- Phase 3 Jr task stalled due to non-unique SEARCH block (two identical Phase 0 blocks at lines 180 and 382). Applied directly by TPM.
- pgvector query was extended with `access_count` and `sacred_pattern` columns for Phase 2.
- All changes are in specialist_council.py — gateway restart required after deployment.
- Phase 3 INSERT is wrapped in try/except so it's non-fatal if table doesn't exist.

## Schema Changes
- `memory_co_retrieval` table created (Feb 17 2026)
- `access_count` and `last_access` columns already existed in thermal_memory_archive

For Seven Generations.

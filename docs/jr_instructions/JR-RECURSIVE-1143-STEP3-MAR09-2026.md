# [RECURSIVE] Thermal Memory Canonical Flag DC-14 Phase 1 - Step 3

**Parent Task**: #1143
**Auto-decomposed**: 2026-03-09T14:30:13.408862
**Original Step Title**: Increment retrieval_count on access

---

### Step 3: Increment retrieval_count on access

After the retrieval query fetches results, add a count increment:

```
<<<<<<< SEARCH
            memories = cur.fetchall()
=======
            memories = cur.fetchall()
            # Track retrieval frequency (DC-14 Phase 2 input — Coyote circuit breaker)
            if memories:
                memory_ids = [m[0] for m in memories if m[0]]
                if memory_ids:
                    cur.execute("UPDATE thermal_memory_archive SET retrieval_count = COALESCE(retrieval_count, 0) + 1 WHERE id = ANY(%s)", (memory_ids,))
                    conn.commit()
>>>>>>> REPLACE
```

## Acceptance Criteria
- `canonical` BOOLEAN column exists on thermal_memory_archive (default FALSE)
- `superseded_by` INTEGER column exists (nullable FK to self)
- `retrieval_count` INTEGER column exists (default 0)
- Canonical memories sort above non-canonical at equal similarity
- Every retrieval increments retrieval_count on accessed memories
- DB failure in count increment does NOT crash retrieval (existing silent catch)
- Migration is idempotent (IF NOT EXISTS on all DDL)
- Reversibility: DROP COLUMN canonical, superseded_by, retrieval_count restores prior state completely

## Dependencies
- None — this is Phase 1, no prerequisites
- Phase 2 (retrieval-heats-memory) will USE retrieval_count as input signal
- Phase 3 (compress-not-delete) will USE superseded_by for chain linking

# Jr Instruction: Co-Retrieval Tracking (Phase 3)

**Kanban**: #1813
**Priority**: 8
**Assigned Jr**: Software Engineer Jr.
**use_rlm**: false
**Sprint**: RC-2026-02E

## Context

Neuroscience insight: when memories are recalled together, they undergo linked reconsolidation — each memory's context "contaminates" the other. If Memory A and Memory B are always retrieved together, the system starts treating them as a single unit even if they're independent facts.

Phase 3 tracks co-retrieval patterns by logging which memories are retrieved together. This builds the data we need to detect "contamination windows" — pairs of memories that are suspiciously co-dependent.

This extends the Phase 0 retrieval logging to include co-retrieval group tracking.

## Step 1: Extend Phase 0 logging to track co-retrieval groups

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
        # Phase 0: Log retrieval access for reconsolidation tracking (#1813)
        if rows:
            mem_ids = [r[0] for r in rows]
            cur.execute("""
                UPDATE thermal_memory_archive
                SET access_count = COALESCE(access_count, 0) + 1,
                    last_access = NOW()
                WHERE id = ANY(%s)
            """, (mem_ids,))
            conn.commit()
=======
        # Phase 0: Log retrieval access for reconsolidation tracking (#1813)
        if rows:
            mem_ids = [r[0] for r in rows]
            cur.execute("""
                UPDATE thermal_memory_archive
                SET access_count = COALESCE(access_count, 0) + 1,
                    last_access = NOW()
                WHERE id = ANY(%s)
            """, (mem_ids,))

            # Phase 3: Log co-retrieval group for contamination window detection (#1813)
            # Records which memories were retrieved together in the same query.
            import hashlib as _hl
            group_hash = _hl.sha256(','.join(str(m) for m in sorted(mem_ids)).encode()).hexdigest()[:16]
            try:
                cur.execute("""
                    INSERT INTO memory_co_retrieval (group_hash, memory_ids, query_preview, retrieved_at)
                    VALUES (%s, %s, %s, NOW())
                """, (group_hash, mem_ids, question[:200]))
            except Exception:
                pass  # Table may not exist yet — non-fatal

            conn.commit()
>>>>>>> REPLACE

## Verification

After deployment, the `memory_co_retrieval` table needs to be created on bluefin:

```text
PGPASSWORD='TYDo5U2NVkXqQ8DHuhIpvRgLUrXf2iZE' psql -h 192.168.132.222 -U claude -d zammad_production -c "
CREATE TABLE IF NOT EXISTS memory_co_retrieval (
    id SERIAL PRIMARY KEY,
    group_hash VARCHAR(16) NOT NULL,
    memory_ids INTEGER[] NOT NULL,
    query_preview TEXT,
    retrieved_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_co_retrieval_group ON memory_co_retrieval(group_hash);
CREATE INDEX IF NOT EXISTS idx_co_retrieval_time ON memory_co_retrieval(retrieved_at);
"
```

After a few council queries, verify data is flowing:

```text
PGPASSWORD='TYDo5U2NVkXqQ8DHuhIpvRgLUrXf2iZE' psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT COUNT(*), COUNT(DISTINCT group_hash) as unique_groups FROM memory_co_retrieval;"
```

## Notes

- group_hash is a deterministic hash of sorted memory IDs — same set of memories = same hash
- This lets us query: "which memory groups are retrieved together most often?"
- Future analysis: `SELECT group_hash, COUNT(*) as freq FROM memory_co_retrieval GROUP BY group_hash HAVING COUNT(*) > 10 ORDER BY freq DESC` — identifies suspiciously co-dependent memory clusters
- The INSERT is wrapped in try/except so the Jr task succeeds even if the table doesn't exist yet (TPM creates it manually)
- query_preview stores first 200 chars of the question for debugging

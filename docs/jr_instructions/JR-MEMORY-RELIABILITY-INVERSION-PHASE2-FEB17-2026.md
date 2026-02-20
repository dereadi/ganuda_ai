# Jr Instruction: Memory Reliability Inversion (Phase 2)

**Kanban**: #1813
**Priority**: 9
**Assigned Jr**: Software Engineer Jr.
**use_rlm**: false
**Sprint**: RC-2026-02E

## Context

Neuroscience insight: memories recalled frequently undergo reconsolidation each time, introducing drift. A memory accessed 200 times is LESS reliable than one accessed 3 times — each retrieval is a chance for the surrounding context to modify the memory.

In our system, high `access_count` memories dominate RAG results because they're "hot" — but they may be the LEAST reliable. This is Temperature Reliability Inversion: the most-accessed memories are the most drifted.

Phase 2 adds a reliability penalty to frequently-accessed memories during RAG scoring. Sacred memories (sacred_pattern=true) are exempt — they are deliberately protected from reconsolidation drift.

## Step 1: Add access_count to the pgvector query

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
        cur.execute("""
            SELECT id, LEFT(original_content, 800), temperature_score,
                   1 - (embedding <=> %s::vector) as similarity
            FROM thermal_memory_archive
            WHERE embedding IS NOT NULL
              AND temperature_score >= %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (str(query_embedding), min_temperature, str(query_embedding), limit))
=======
        cur.execute("""
            SELECT id, LEFT(original_content, 800), temperature_score,
                   1 - (embedding <=> %s::vector) as similarity,
                   COALESCE(access_count, 0) as access_count,
                   COALESCE(sacred_pattern, false) as sacred
            FROM thermal_memory_archive
            WHERE embedding IS NOT NULL
              AND temperature_score >= %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (str(query_embedding), min_temperature, str(query_embedding), limit))
>>>>>>> REPLACE

## Step 2: Apply reliability penalty after Phase 0 logging

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
        conn.close()

        if not rows:
            return _keyword_fallback(question, limit)

        # Phase 1: Ripple retrieval — expand result set via memory_links graph (#1813)
=======
        conn.close()

        if not rows:
            return _keyword_fallback(question, limit)

        # Phase 2: Reliability inversion — penalize frequently-accessed memories (#1813)
        # Reconsolidation drift: each access is a chance for context contamination.
        # Sacred memories exempt (deliberately protected from drift).
        # Max penalty: 30% for memories accessed 15+ times.
        adjusted_rows = []
        for row in rows:
            mem_id, content, temp, sim = row[0], row[1], row[2], row[3]
            acc_count = row[4] if len(row) > 4 else 0
            is_sacred = row[5] if len(row) > 5 else False
            if is_sacred or acc_count <= 2:
                adjusted_rows.append((mem_id, content, temp, sim))
            else:
                penalty = min((acc_count - 2) * 0.02, 0.30)
                adjusted_sim = sim * (1.0 - penalty)
                adjusted_rows.append((mem_id, content, temp, adjusted_sim))
        rows = adjusted_rows
        print(f"[RAG] Reliability: {sum(1 for r in rows if len(rows) > 0)} memories scored, penalties applied to high-access non-sacred")

        # Phase 1: Ripple retrieval — expand result set via memory_links graph (#1813)
>>>>>>> REPLACE

## Notes

- Penalty formula: `adjusted_sim = sim * (1.0 - min((access_count - 2) * 0.02, 0.30))`
- 0-2 accesses: no penalty (normal retrieval)
- 3 accesses: 2% penalty
- 10 accesses: 16% penalty
- 15+ accesses: 30% cap (never fully suppress a memory)
- Sacred memories (sacred_pattern=true): always exempt — these are TPM/council protected
- The penalty affects RANKING order, not filtering — penalized memories still appear, just lower
- Rows are converted to plain tuples (4-element) after scoring, preserving downstream compatibility

# Jr Instruction: Phase 1 — Spreading Activation Ripple Retrieval

**Kanban**: #1813
**Priority**: 8
**Assigned Jr**: Software Engineer Jr.
**use_rlm**: false
**Sprint**: RC-2026-02E

## Context

Phase 0 (retrieval logging) adds access_count/last_access tracking. Phase 1 adds **ripple retrieval** — when primary memories are retrieved, traverse the `memory_links` graph to find associated memories. This implements Collins & Loftus (1975) spreading activation, adapted from the Vestige repo.

The `memory_links` table has 8,058 edges connecting memories via `source_hash`/`target_hash` (joined to `thermal_memory_archive.memory_hash`). Each edge has a `similarity_score` (0-1). Ripple retrieval does BFS traversal with decay, returning associated memories ranked by activation level.

IMPORTANT: This is purely ADDITIVE. It expands the retrieval set. It does NOT modify memory content. It does NOT create false memories.

## Step 1: Add a ripple retrieval function to specialist_council.py

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
def _keyword_fallback(question: str, limit: int = 5) -> str:
    """Fallback keyword search when embedding service is unavailable."""
=======
def _ripple_retrieve(primary_hashes: list, conn, max_hops: int = 2, decay: float = 0.7, threshold: float = 0.1) -> list:
    """
    Spreading activation on memory_links graph.
    Given primary retrieved memory hashes, traverse edges to find associated memories.
    Returns list of (memory_id, content, temp, activation_level) tuples.
    Adapted from Collins & Loftus (1975) via Vestige repo.
    Phase 1 of Human Memory Architecture (#1813).
    """
    if not primary_hashes:
        return []

    visited = {}  # hash -> best activation seen
    for h in primary_hashes:
        visited[h] = 1.0  # primary results have activation 1.0

    queue = [(h, 1.0, 0) for h in primary_hashes]  # (hash, activation, hops)
    ripple_hashes = {}  # hash -> activation (only non-primary)

    cur = conn.cursor()
    while queue:
        current_hash, current_activation, hops = queue.pop(0)
        if hops >= max_hops:
            continue

        # Get outgoing edges (bidirectional — check both directions)
        cur.execute("""
            SELECT target_hash, similarity_score FROM memory_links
            WHERE source_hash = %s AND similarity_score > %s
            UNION
            SELECT source_hash, similarity_score FROM memory_links
            WHERE target_hash = %s AND similarity_score > %s
        """, (current_hash, threshold, current_hash, threshold))

        for target_hash, edge_strength in cur.fetchall():
            propagated = current_activation * edge_strength * decay
            if propagated < threshold:
                continue
            if target_hash in visited and visited[target_hash] >= propagated:
                continue
            visited[target_hash] = propagated
            if target_hash not in [h for h in primary_hashes]:
                ripple_hashes[target_hash] = propagated
            queue.append((target_hash, propagated, hops + 1))

    if not ripple_hashes:
        return []

    # Fetch memory content for ripple results
    hash_list = list(ripple_hashes.keys())
    cur.execute("""
        SELECT id, LEFT(original_content, 800), temperature_score, memory_hash
        FROM thermal_memory_archive
        WHERE memory_hash = ANY(%s)
          AND temperature_score >= 20
    """, (hash_list,))

    results = []
    for row in cur.fetchall():
        mem_id, content, temp, mem_hash = row
        activation = ripple_hashes.get(mem_hash, 0.0)
        results.append((mem_id, content, temp, activation))

    # Log ripple access for Phase 0 tracking
    if results:
        ripple_ids = [r[0] for r in results]
        cur.execute("""
            UPDATE thermal_memory_archive
            SET access_count = COALESCE(access_count, 0) + 1,
                last_access = NOW()
            WHERE id = ANY(%s)
        """, (ripple_ids,))
        conn.commit()

    # Sort by activation descending, limit to top 3
    results.sort(key=lambda r: r[3], reverse=True)
    return results[:3]


def _keyword_fallback(question: str, limit: int = 5) -> str:
    """Fallback keyword search when embedding service is unavailable."""
>>>>>>> REPLACE

## Step 2: Integrate ripple retrieval into the semantic search path

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
        if not rows:
            return _keyword_fallback(question, limit)

        # Phase 2b: Cross-encoder reranking (retrieve broad, rerank precise)
=======
        if not rows:
            return _keyword_fallback(question, limit)

        # Phase 1: Ripple retrieval — expand result set via memory_links graph (#1813)
        try:
            ripple_conn = psycopg2.connect(**DB_CONFIG)
            primary_hashes = []
            for r in rows:
                # Look up memory_hash for each retrieved memory
                rcur = ripple_conn.cursor()
                rcur.execute("SELECT memory_hash FROM thermal_memory_archive WHERE id = %s", (r[0],))
                hash_row = rcur.fetchone()
                if hash_row:
                    primary_hashes.append(hash_row[0])
                rcur.close()

            ripple_results = _ripple_retrieve(primary_hashes, ripple_conn)
            if ripple_results:
                # Append ripple results to primary results with activation as score
                rows = list(rows) + ripple_results
                print(f"[RAG] Ripple: +{len(ripple_results)} associated memories via spreading activation")
            ripple_conn.close()
        except Exception as e:
            print(f"[RAG] Ripple retrieval skipped (non-fatal): {e}")

        # Phase 2b: Cross-encoder reranking (retrieve broad, rerank precise)
>>>>>>> REPLACE

## Step 3: Add schema columns to memory_links for edge reinforcement

This step requires database access. Run these SQL commands on bluefin:

```text
ALTER TABLE memory_links ADD COLUMN IF NOT EXISTS last_activated TIMESTAMP;
ALTER TABLE memory_links ADD COLUMN IF NOT EXISTS activation_count INTEGER DEFAULT 0;
```

## Verification

After deployment, run a council query and check for ripple output:

```text
curl -s http://192.168.132.223:8080/v1/council/vote -H "Content-Type: application/json" -H "Authorization: Bearer ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5" -d '{"question": "What happened during the February 13 power outage?", "context": "Phase 1 ripple retrieval test"}'
```

Check logs for `[RAG] Ripple:` output showing associated memories were found.

Then verify memory_links schema update:

```text
PGPASSWORD='TYDo5U2NVkXqQ8DHuhIpvRgLUrXf2iZE' psql -h 192.168.132.222 -U claude -d zammad_production -c "\d memory_links"
```

Should show `last_activated` and `activation_count` columns.

## Notes

- Decay factor 0.7 per hop means: hop 1 gets 70% of parent activation, hop 2 gets 49%, hop 3 would get 34% (below threshold for most edges)
- Max 2 hops keeps it fast — at most 2 edge traversals per primary memory
- Threshold 0.1 prunes weak edges early
- Bidirectional search (checks both source_hash and target_hash) because association goes both ways
- Results capped at top 3 to avoid overwhelming the context window
- All ripple results also get access_count incremented (Phase 0 logging)
- Cross-encoder reranking on the EXPANDED set ensures ripple results compete fairly with primary results
- Does NOT modify memory content — purely additive retrieval expansion
- Does NOT create new memories or links — only traverses existing links

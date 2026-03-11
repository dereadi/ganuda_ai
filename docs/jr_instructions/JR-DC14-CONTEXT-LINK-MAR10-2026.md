# JR INSTRUCTION: DC-14 Context Link — Proactive Associative Firing Between Thermal Basins

**Task**: DC14-CONTEXT-LINK
**Priority**: P2
**Estimated SP**: 5
**Assigned**: Software Engineer Jr.
**Created**: 2026-03-10
**Design Ref**: /ganuda/docs/design/DC-14-THREE-BODY-MEMORY-MAR09-2026.md

## Objective

Build `/ganuda/lib/context_link.py` — the associative firing module for DC-14 Three-Body Memory. When any thermal is accessed, this module finds semantically adjacent thermals. Watershed, not railroad: associations flow downhill along natural similarity gradients. Every link carries a zero-trust signature so receivers can verify provenance.

Critical safety constraints from Council review:
- **Coyote**: Inhibition rules prevent seizure cascades. Max chain depth, relevance threshold, hard cutoffs.
- **Crawdad (Wolf 1)**: PII/credential/secret thermals NEVER auto-fire. They are invisible to context link.
- **Sacred isolation**: Sacred thermals only associate with other sacred thermals.

## Structured Replacement Blocks

### Create: `/ganuda/lib/context_link.py`

```python
#!/usr/bin/env python3
"""DC-14 Context Link — Proactive associative firing between thermal memory basins.

Three-Body Memory sub-check #2: when any thermal is accessed, auto-fetch
semantically adjacent thermals. Watershed topology — associations flow
downhill along similarity gradients.

Council constraints honored:
  - Coyote: max_hops chain depth limit, relevance threshold, cascade prevention
  - Crawdad Wolf 1: PII/credential/secret thermals never auto-fire
  - Sacred isolation: sacred thermals only link to sacred thermals

Usage:
    from lib.context_link import get_associated_thermals, get_link_signature, verify_link

CLI test mode:
    python3 /ganuda/lib/context_link.py --test
"""

import hashlib
import os
import random
import sys
import time
from typing import Optional

import psycopg2
import psycopg2.extras

# ---------------------------------------------------------------------------
# DB configuration — use secrets_loader if available, else env fallback
# ---------------------------------------------------------------------------

def _get_db_config() -> dict:
    try:
        sys.path.insert(0, '/ganuda/lib')
        from secrets_loader import get_db_config
        cfg = get_db_config()
        return {
            'host': cfg['host'],
            'database': cfg['dbname'],
            'user': cfg['user'],
            'password': cfg['password'],
            'port': cfg.get('port', 5432),
        }
    except Exception:
        return {
            'host': os.environ.get('CHEROKEE_DB_HOST', '192.168.132.222'),
            'database': os.environ.get('CHEROKEE_DB_NAME', 'zammad_production'),
            'user': os.environ.get('CHEROKEE_DB_USER', 'claude'),
            'password': os.environ.get('CHEROKEE_DB_PASS', ''),
            'port': int(os.environ.get('CHEROKEE_DB_PORT', '5432')),
        }

# ---------------------------------------------------------------------------
# Constants — Coyote inhibition parameters
# ---------------------------------------------------------------------------

MAX_HOPS_CEILING = 3          # Absolute max chain depth (seizure prevention)
EMBEDDING_THRESHOLD = 0.7     # Minimum cosine similarity for embedding path
TAG_OVERLAP_THRESHOLD = 2     # Minimum shared tags for fallback path
PII_BLOCK_TAGS = frozenset(['pii', 'credential', 'secret'])  # Crawdad Wolf 1


def _connect():
    return psycopg2.connect(**_get_db_config())


# ---------------------------------------------------------------------------
# Core: associative retrieval
# ---------------------------------------------------------------------------

def get_associated_thermals(
    thermal_id: int,
    max_hops: int = 1,
    max_results: int = 3,
) -> list[dict]:
    """Find semantically adjacent thermals for a given thermal memory ID.

    Strategy:
      1. If the source thermal has a populated embedding, use pgvector cosine
         similarity against other embedded thermals (threshold > 0.7).
      2. Else fall back to tag overlap (>= 2 shared tags) + domain_tag match.

    Inhibition rules (Coyote):
      - max_hops clamped to [1, MAX_HOPS_CEILING]. Prevents runaway cascades.
      - Results below relevance threshold are suppressed.
      - PII/credential/secret thermals are excluded (Crawdad Wolf 1).
      - Sacred source thermals only return other sacred thermals.

    Returns list of dicts sorted by similarity_score descending.
    """
    max_hops = max(1, min(max_hops, MAX_HOPS_CEILING))
    conn = _connect()
    try:
        return _fetch_associations(conn, thermal_id, max_hops, max_results, _depth=0)
    finally:
        conn.close()


def _fetch_associations(
    conn,
    thermal_id: int,
    max_hops: int,
    max_results: int,
    _depth: int,
) -> list[dict]:
    """Recursive association fetcher with depth-limited inhibition."""
    if _depth >= max_hops:
        return []

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        # Fetch source thermal metadata
        cur.execute("""
            SELECT id, memory_hash, embedding IS NOT NULL AS has_embedding,
                   sacred_pattern, tags, domain_tag
            FROM thermal_memory_archive
            WHERE id = %s
        """, (thermal_id,))
        source = cur.fetchone()
        if not source:
            return []

        source_sacred = bool(source['sacred_pattern'])
        source_tags = source['tags'] or []
        source_domain = source['domain_tag']
        has_embedding = source['has_embedding']

        # --- Build exclusion for PII tags (Crawdad Wolf 1) ---
        pii_filter = " AND NOT (tags && ARRAY['pii','credential','secret']::text[])"

        # --- Sacred isolation ---
        sacred_filter = ""
        if source_sacred:
            sacred_filter = " AND sacred_pattern = true"

        results = []

        if has_embedding:
            # Path 1: pgvector cosine similarity
            cur.execute(f"""
                SELECT id, memory_hash, temperature_score, domain_tag, tags,
                       LEFT(original_content, 200) AS snippet,
                       1 - (embedding <=> (
                           SELECT embedding FROM thermal_memory_archive WHERE id = %s
                       )) AS similarity_score
                FROM thermal_memory_archive
                WHERE id != %s
                  AND embedding IS NOT NULL
                  {pii_filter}
                  {sacred_filter}
                ORDER BY embedding <=> (
                    SELECT embedding FROM thermal_memory_archive WHERE id = %s
                )
                LIMIT %s
            """, (thermal_id, thermal_id, thermal_id, max_results * 2))

            for row in cur.fetchall():
                sim = float(row['similarity_score'])
                if sim >= EMBEDDING_THRESHOLD:
                    results.append(_row_to_dict(row, sim))

        else:
            # Path 2: tag overlap + domain match fallback
            if source_tags:
                cur.execute(f"""
                    SELECT id, memory_hash, temperature_score, domain_tag, tags,
                           LEFT(original_content, 200) AS snippet,
                           (
                               SELECT COUNT(*)
                               FROM unnest(tags) t
                               WHERE t = ANY(%s)
                           ) AS tag_overlap
                    FROM thermal_memory_archive
                    WHERE id != %s
                      AND tags IS NOT NULL
                      AND array_length(tags, 1) > 0
                      {pii_filter}
                      {sacred_filter}
                    ORDER BY tag_overlap DESC, temperature_score DESC
                    LIMIT %s
                """, (list(source_tags), thermal_id, max_results * 3))

                for row in cur.fetchall():
                    overlap = int(row['tag_overlap'])
                    if overlap >= TAG_OVERLAP_THRESHOLD:
                        # Normalize overlap to 0-1 range
                        max_possible = max(len(source_tags), 1)
                        sim = min(1.0, overlap / max_possible)
                        results.append(_row_to_dict(row, sim))

            # Boost domain matches not already captured
            if source_domain:
                existing_ids = {r['id'] for r in results}
                cur.execute(f"""
                    SELECT id, memory_hash, temperature_score, domain_tag, tags,
                           LEFT(original_content, 200) AS snippet
                    FROM thermal_memory_archive
                    WHERE id != %s
                      AND domain_tag = %s
                      {pii_filter}
                      {sacred_filter}
                    ORDER BY temperature_score DESC
                    LIMIT %s
                """, (thermal_id, source_domain, max_results))

                for row in cur.fetchall():
                    if row['id'] not in existing_ids:
                        results.append(_row_to_dict(row, 0.5))

        # Sort by similarity descending, trim to max_results
        results.sort(key=lambda r: r['similarity_score'], reverse=True)
        results = results[:max_results]

        # Recursive hop (depth + 1) — merge children but respect total budget
        if _depth + 1 < max_hops and results:
            child_budget = max(1, max_results // len(results))
            seen_ids = {thermal_id} | {r['id'] for r in results}
            for r in list(results):
                children = _fetch_associations(
                    conn, r['id'], max_hops, child_budget, _depth + 1
                )
                for child in children:
                    if child['id'] not in seen_ids:
                        results.append(child)
                        seen_ids.add(child['id'])

            results.sort(key=lambda r: r['similarity_score'], reverse=True)
            results = results[:max_results]

    return results


def _row_to_dict(row, similarity: float) -> dict:
    return {
        'id': row['id'],
        'memory_hash': row['memory_hash'],
        'temperature_score': float(row['temperature_score']) if row['temperature_score'] else 0.0,
        'domain_tag': row['domain_tag'],
        'tags': list(row['tags']) if row['tags'] else [],
        'snippet': row['snippet'] or '',
        'similarity_score': round(similarity, 4),
    }


# ---------------------------------------------------------------------------
# Zero-trust link signatures
# ---------------------------------------------------------------------------

def get_link_signature(source_id: int, dest_id: int) -> str:
    """Generate a zero-trust signature for a context link.

    Returns sha256 of "{source_hash}:{dest_hash}:{timestamp}".
    The timestamp is integer epoch seconds — deterministic within the same second.
    """
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT memory_hash FROM thermal_memory_archive WHERE id = %s",
                (source_id,)
            )
            src = cur.fetchone()
            cur.execute(
                "SELECT memory_hash FROM thermal_memory_archive WHERE id = %s",
                (dest_id,)
            )
            dst = cur.fetchone()
            if not src or not dst:
                raise ValueError(f"Thermal ID not found: source={source_id}, dest={dest_id}")
            ts = int(time.time())
            payload = f"{src[0]}:{dst[0]}:{ts}"
            return hashlib.sha256(payload.encode()).hexdigest()
    finally:
        conn.close()


def verify_link(source_id: int, dest_id: int, signature: str, max_age_seconds: int = 300) -> bool:
    """Verify a context link signature within a time window.

    Recomputes the signature for each second in [now - max_age_seconds, now]
    and checks for a match. Default window: 5 minutes.
    """
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT memory_hash FROM thermal_memory_archive WHERE id = %s",
                (source_id,)
            )
            src = cur.fetchone()
            cur.execute(
                "SELECT memory_hash FROM thermal_memory_archive WHERE id = %s",
                (dest_id,)
            )
            dst = cur.fetchone()
            if not src or not dst:
                return False
            now = int(time.time())
            for ts in range(now, now - max_age_seconds - 1, -1):
                payload = f"{src[0]}:{dst[0]}:{ts}"
                if hashlib.sha256(payload.encode()).hexdigest() == signature:
                    return True
            return False
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# CLI test mode
# ---------------------------------------------------------------------------

def _test():
    """Pick a random thermal and show its associations."""
    print("DC-14 Context Link — Test Mode")
    print("=" * 60)
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, memory_hash, LEFT(original_content, 80),
                       temperature_score, sacred_pattern, domain_tag, tags
                FROM thermal_memory_archive
                WHERE temperature_score >= 50
                  AND NOT (tags && ARRAY['pii','credential','secret']::text[])
                ORDER BY random()
                LIMIT 1
            """)
            row = cur.fetchone()
            if not row:
                print("No thermals found with temperature >= 50.")
                return

            tid, mhash, snippet, temp, sacred, domain, tags = row
            print(f"Source thermal: #{tid}")
            print(f"  hash:    {mhash}")
            print(f"  temp:    {temp}")
            print(f"  sacred:  {sacred}")
            print(f"  domain:  {domain}")
            print(f"  tags:    {tags}")
            print(f"  snippet: {snippet}")
            print()

        # Test 1-hop associations
        results = get_associated_thermals(tid, max_hops=1, max_results=3)
        print(f"Associated thermals (1-hop, max 3):")
        if not results:
            print("  (none found above threshold)")
        for r in results:
            print(f"  #{r['id']} sim={r['similarity_score']:.4f} "
                  f"temp={r['temperature_score']:.0f} domain={r['domain_tag']}")
            print(f"    tags: {r['tags']}")
            print(f"    snippet: {r['snippet'][:80]}")
            print()

        # Test signature
        if results:
            dest_id = results[0]['id']
            sig = get_link_signature(tid, dest_id)
            verified = verify_link(tid, dest_id, sig)
            print(f"Link signature: {sig[:32]}...")
            print(f"Verified: {verified}")

    finally:
        conn.close()
    print("=" * 60)
    print("Context Link: OPERATIONAL")


if __name__ == '__main__':
    if '--test' in sys.argv:
        _test()
    else:
        print("Usage: python3 /ganuda/lib/context_link.py --test")
        print("  Or import: from lib.context_link import get_associated_thermals")
```

## Acceptance Criteria

1. `get_associated_thermals(thermal_id)` returns a list of dicts with keys: `id`, `memory_hash`, `temperature_score`, `domain_tag`, `tags`, `snippet`, `similarity_score`. Sorted by `similarity_score` descending.
2. Embedding path: uses `1 - (embedding <=> source_embedding)` via pgvector. Only returns results with similarity > 0.7.
3. Fallback path: when source has no embedding, uses tag overlap (>= 2 shared tags) + domain_tag match. Tag overlap normalized to 0-1 range.
4. **Coyote inhibition**: `max_hops` is clamped to [1, 3]. Recursive hop merges children but never exceeds `max_results` total. No runaway cascades.
5. **Crawdad Wolf 1**: Thermals with tags containing `pii`, `credential`, or `secret` are excluded from ALL queries. They never auto-fire.
6. **Sacred isolation**: If the source thermal has `sacred_pattern = true`, only other sacred thermals are returned.
7. `get_link_signature(source_id, dest_id)` returns a sha256 hex digest of `{source_hash}:{dest_hash}:{timestamp}`.
8. `verify_link(source_id, dest_id, signature)` returns True if the signature matches any timestamp within the last 300 seconds.
9. `python3 /ganuda/lib/context_link.py --test` picks a random hot thermal and prints its associations.
10. Module uses `secrets_loader.get_db_config()` when available, falls back to env vars.
11. No new pip dependencies — uses only psycopg2 and stdlib.
12. Module is importable: `from lib.context_link import get_associated_thermals`.

## Gotchas

- The embedding column is `embedding`, NOT `embedding_vector`. Check the actual column name if queries fail.
- `tags` is `text[]` (PostgreSQL array), not JSON. Use `ARRAY[...]::text[]` syntax and `&&` (overlap) operator.
- The `sacred_pattern` column may be NULL for older thermals. Treat NULL as false (`bool(source['sacred_pattern'])`).
- The `tags && ARRAY[...]::text[]` filter will fail if `tags` is NULL. The PII filter works because NULL `&&` anything is false in PostgreSQL, but be aware.
- `domain_tag` can be NULL. The domain fallback path should only activate when the source has a non-NULL domain.
- pgvector `<=>` is cosine DISTANCE (0 = identical). Similarity = `1 - distance`. Threshold 0.7 similarity = distance < 0.3.
- The verify_link brute-force over 300 seconds is intentional — keeps the interface stateless. For high-throughput use, store the timestamp alongside the signature.
- DO NOT add an index on `embedding` — pgvector indexes are expensive and a separate kanban item.
- Connection per call is acceptable for this module's usage pattern (low-frequency associative firing, not hot path). Do not pool.

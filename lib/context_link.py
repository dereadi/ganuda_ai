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
import sys
import time

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
            'host': os.environ.get('CHEROKEE_DB_HOST', os.environ.get('CHEROKEE_DB_HOST', '10.100.0.2')),
            'database': os.environ.get('CHEROKEE_DB_NAME', 'zammad_production'),
            'user': os.environ.get('CHEROKEE_DB_USER', 'claude'),
            'password': os.environ.get('CHEROKEE_DB_PASS', ''),
            'port': int(os.environ.get('CHEROKEE_DB_PORT', '5432')),
        }


# ---------------------------------------------------------------------------
# Constants — Coyote inhibition parameters
# ---------------------------------------------------------------------------

MAX_HOPS_CEILING = 3
EMBEDDING_THRESHOLD = 0.7
TAG_OVERLAP_THRESHOLD = 2
PII_BLOCK_TAGS = frozenset(['pii', 'credential', 'secret'])

_PII_FILTER = " AND NOT (tags && ARRAY['pii','credential','secret']::text[])"


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
      1. If source has a populated embedding, use pgvector cosine similarity (> 0.7).
      2. Else fall back to tag overlap (>= 2 shared) + domain_tag match.

    Inhibition (Coyote): max_hops clamped to [1,3]. PII excluded. Sacred isolation.
    """
    max_hops = max(1, min(max_hops, MAX_HOPS_CEILING))
    conn = _connect()
    try:
        return _fetch_associations(conn, thermal_id, max_hops, max_results, _depth=0)
    finally:
        conn.commit()  # explicit commit before close
        conn.close()


def _fetch_associations(conn, thermal_id, max_hops, max_results, _depth):
    if _depth >= max_hops:
        return []

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT id, memory_hash, embedding IS NOT NULL AS has_embedding,
                   sacred_pattern, tags, domain_tag
            FROM thermal_memory_archive WHERE id = %s
        """, (thermal_id,))
        source = cur.fetchone()
        if not source:
            return []

        source_sacred = bool(source['sacred_pattern'])
        source_tags = source['tags'] or []
        source_domain = source['domain_tag']
        has_embedding = source['has_embedding']

        sacred_filter = " AND sacred_pattern = true" if source_sacred else ""
        results = []

        if has_embedding:
            cur.execute(f"""
                SELECT id, memory_hash, temperature_score, domain_tag, tags,
                       LEFT(original_content, 200) AS snippet,
                       1 - (embedding <=> (
                           SELECT embedding FROM thermal_memory_archive WHERE id = %s
                       )) AS similarity_score
                FROM thermal_memory_archive
                WHERE id != %s AND embedding IS NOT NULL
                  {_PII_FILTER}{sacred_filter}
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
            if source_tags:
                cur.execute(f"""
                    SELECT id, memory_hash, temperature_score, domain_tag, tags,
                           LEFT(original_content, 200) AS snippet,
                           (SELECT COUNT(*) FROM unnest(tags) t WHERE t = ANY(%s))
                               AS tag_overlap
                    FROM thermal_memory_archive
                    WHERE id != %s AND tags IS NOT NULL AND array_length(tags, 1) > 0
                      {_PII_FILTER}{sacred_filter}
                    ORDER BY tag_overlap DESC, temperature_score DESC
                    LIMIT %s
                """, (list(source_tags), thermal_id, max_results * 3))

                for row in cur.fetchall():
                    overlap = int(row['tag_overlap'])
                    if overlap >= TAG_OVERLAP_THRESHOLD:
                        max_possible = max(len(source_tags), 1)
                        sim = min(1.0, overlap / max_possible)
                        results.append(_row_to_dict(row, sim))

            if source_domain:
                existing_ids = {r['id'] for r in results}
                cur.execute(f"""
                    SELECT id, memory_hash, temperature_score, domain_tag, tags,
                           LEFT(original_content, 200) AS snippet
                    FROM thermal_memory_archive
                    WHERE id != %s AND domain_tag = %s
                      {_PII_FILTER}{sacred_filter}
                    ORDER BY temperature_score DESC LIMIT %s
                """, (thermal_id, source_domain, max_results))

                for row in cur.fetchall():
                    if row['id'] not in existing_ids:
                        results.append(_row_to_dict(row, 0.5))

        results.sort(key=lambda r: r['similarity_score'], reverse=True)
        results = results[:max_results]

        # Recursive hop — merge children, respect budget
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
    """Generate sha256 of '{source_hash}:{dest_hash}:{epoch_seconds}'."""
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT memory_hash FROM thermal_memory_archive WHERE id = %s",
                (source_id,),
            )
            src = cur.fetchone()
            cur.execute(
                "SELECT memory_hash FROM thermal_memory_archive WHERE id = %s",
                (dest_id,),
            )
            dst = cur.fetchone()
            if not src or not dst:
                raise ValueError(
                    f"Thermal ID not found: source={source_id}, dest={dest_id}"
                )
            ts = int(time.time())
            return hashlib.sha256(f"{src[0]}:{dst[0]}:{ts}".encode()).hexdigest()
    finally:
        conn.commit()  # explicit commit before close
        conn.close()


def verify_link(
    source_id: int,
    dest_id: int,
    signature: str,
    max_age_seconds: int = 300,
) -> bool:
    """Verify a link signature within a rolling time window (default 5 min)."""
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT memory_hash FROM thermal_memory_archive WHERE id = %s",
                (source_id,),
            )
            src = cur.fetchone()
            cur.execute(
                "SELECT memory_hash FROM thermal_memory_archive WHERE id = %s",
                (dest_id,),
            )
            dst = cur.fetchone()
            if not src or not dst:
                return False
            now = int(time.time())
            for ts in range(now, now - max_age_seconds - 1, -1):
                candidate = hashlib.sha256(
                    f"{src[0]}:{dst[0]}:{ts}".encode()
                ).hexdigest()
                if candidate == signature:
                    return True
            return False
    finally:
        conn.commit()  # explicit commit before close
        conn.close()


# ---------------------------------------------------------------------------
# CLI test mode
# ---------------------------------------------------------------------------

def _test():
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
                ORDER BY random() LIMIT 1
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
    finally:
        conn.commit()  # explicit commit before close
        conn.close()

    results = get_associated_thermals(tid, max_hops=1, max_results=3)
    print(f"Associated thermals (1-hop, max 3):")
    if not results:
        print("  (none found above threshold)")
    for r in results:
        print(
            f"  #{r['id']} sim={r['similarity_score']:.4f} "
            f"temp={r['temperature_score']:.0f} domain={r['domain_tag']}"
        )
        print(f"    tags: {r['tags']}")
        print(f"    snippet: {r['snippet'][:80]}")
        print()

    if results:
        dest_id = results[0]['id']
        sig = get_link_signature(tid, dest_id)
        verified = verify_link(tid, dest_id, sig)
        print(f"Link signature: {sig[:32]}...")
        print(f"Verified: {verified}")

    print("=" * 60)
    print("Context Link: OPERATIONAL")


if __name__ == '__main__':
    if '--test' in sys.argv:
        _test()
    else:
        print("Usage: python3 /ganuda/lib/context_link.py --test")
        print("  Or import: from lib.context_link import get_associated_thermals")

#!/usr/bin/env python3
"""KG Batch Auto-Relate — Populate thermal_relationships from embedding similarity.

S-PATH-RAG P-2: Build the graph that path search will traverse.
Jr Task: #1448
Council Vote: S-PATH-RAG APPROVED 12-1-0

Processes all embedded thermal memories and creates relationships:
1. semantically_near (cosine similarity > 0.75, top-5 per node)
2. temporal_sequence (same domain, within 1 hour)
3. sacred_cluster (all sacred thermals interconnected)

Checkpoints progress for resume-on-crash.
"""

import json
import logging
import os
import sys
import time

sys.path.insert(0, "/ganuda/lib")

import numpy as np
from ganuda_db import get_connection
from kg_edge_embedder import compute_edge_embedding, get_type_embedding


def parse_pgvector(val):
    """Convert pgvector string '[0.1,0.2,...]' to list of floats."""
    if val is None:
        return None
    if isinstance(val, (list, np.ndarray)):
        return list(val)
    if isinstance(val, str):
        return [float(x) for x in val.strip("[]").split(",")]
    return list(val)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("kg_batch_relate")

CHECKPOINT_FILE = "/ganuda/state/kg_batch_relate_checkpoint.json"
BATCH_SIZE = 500
SIMILARITY_THRESHOLD = 0.85
SIMILARITY_TOP_K = 5
TEMPORAL_WINDOW_SECONDS = 3600  # 1 hour
SKIP_EDGE_EMBEDDINGS = True  # Backfill later for speed


def load_checkpoint():
    try:
        with open(CHECKPOINT_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        return {"phase": "semantic", "last_id": 0, "edges_created": 0, "started": time.time()}


def save_checkpoint(ckpt):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(ckpt, f, indent=2)


def create_edge(cur, source_id, target_id, rel_type, confidence, provenance, source_emb=None, target_emb=None):
    """Create a relationship edge with edge embedding."""
    # Check if edge already exists
    cur.execute("""
        SELECT id FROM thermal_relationships
        WHERE source_memory_id = %s AND target_memory_id = %s AND relationship_type = %s
    """, (source_id, target_id, rel_type))
    if cur.fetchone():
        return False  # Already exists

    # Compute edge embedding if we have node embeddings (skip if SKIP_EDGE_EMBEDDINGS for speed)
    edge_emb = None
    if not SKIP_EDGE_EMBEDDINGS and source_emb is not None and target_emb is not None:
        edge_emb = compute_edge_embedding(
            source_emb if isinstance(source_emb, list) else list(source_emb),
            target_emb if isinstance(target_emb, list) else list(target_emb),
            rel_type,
        )

    cur.execute("""
        INSERT INTO thermal_relationships
            (source_memory_id, target_memory_id, relationship_type, confidence, provenance, edge_embedding)
        VALUES (%s, %s, %s, %s, %s, %s::vector)
    """, (source_id, target_id, rel_type, confidence, provenance,
          str(edge_emb) if edge_emb else None))
    return True


def phase_semantic(conn, ckpt):
    """Phase 1: semantically_near — top-K similar thermals per node."""
    cur = conn.cursor()

    # Count total embedded thermals
    cur.execute("SELECT COUNT(*) FROM thermal_memory_archive WHERE embedding IS NOT NULL")
    total = cur.fetchone()[0]
    logger.info(f"Phase SEMANTIC: {total} embedded thermals to process (starting from id>{ckpt['last_id']})")

    # Process in batches
    processed = 0
    edges = 0

    while True:
        cur.execute("""
            SELECT id, embedding
            FROM thermal_memory_archive
            WHERE embedding IS NOT NULL AND id > %s
            ORDER BY id
            LIMIT %s
        """, (ckpt["last_id"], BATCH_SIZE))

        batch = cur.fetchall()
        if not batch:
            break

        for mem_id, mem_emb in batch:
            # Find top-K most similar thermals using pgvector IVFFlat index
            # Pass the embedding vector directly for index-optimized kNN
            cur.execute("SET ivfflat.probes = 10")
            cur.execute("""
                SELECT id, embedding,
                       1 - (embedding <=> %s::vector) as similarity
                FROM thermal_memory_archive
                WHERE embedding IS NOT NULL AND id != %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, (mem_emb, mem_id, mem_emb, SIMILARITY_TOP_K))

            neighbors = cur.fetchall()
            for neighbor_id, neighbor_emb, similarity in neighbors:
                if similarity >= SIMILARITY_THRESHOLD:
                    created = create_edge(
                        cur, mem_id, neighbor_id, "semantically_near",
                        round(float(similarity), 4), "kg_batch_relate",
                        parse_pgvector(mem_emb), parse_pgvector(neighbor_emb),
                    )
                    if created:
                        edges += 1

            processed += 1
            ckpt["last_id"] = mem_id

            if processed % BATCH_SIZE == 0:
                conn.commit()
                # Get actual count from DB for accuracy
                cur.execute("SELECT COUNT(*) FROM thermal_relationships WHERE relationship_type = 'semantically_near'")
                actual_edges = cur.fetchone()[0]
                ckpt["edges_created"] = actual_edges
                save_checkpoint(ckpt)
                logger.info(f"  Semantic: {processed}/{total} processed, {actual_edges} edges in DB")

        conn.commit()
        save_checkpoint(ckpt)

    logger.info(f"Phase SEMANTIC complete: {processed} thermals, {ckpt['edges_created']} total edges")
    ckpt["phase"] = "temporal"
    ckpt["last_id"] = 0
    save_checkpoint(ckpt)


def phase_temporal(conn, ckpt):
    """Phase 2: temporal_sequence — same domain, within 1 hour."""
    cur = conn.cursor()

    # Get all domain tags with counts
    cur.execute("""
        SELECT domain_tag, COUNT(*) FROM thermal_memory_archive
        WHERE domain_tag IS NOT NULL
        GROUP BY domain_tag
        HAVING COUNT(*) > 1
        ORDER BY COUNT(*) DESC
    """)
    domains = cur.fetchall()
    logger.info(f"Phase TEMPORAL: {len(domains)} domain tags to process")

    edges = 0
    for domain_tag, count in domains:
        # Get thermals in this domain ordered by time
        cur.execute("""
            SELECT id, created_at, embedding
            FROM thermal_memory_archive
            WHERE domain_tag = %s AND embedding IS NOT NULL
            ORDER BY created_at
        """, (domain_tag,))
        thermals = cur.fetchall()

        # Create temporal edges between sequential thermals within window
        for i in range(len(thermals) - 1):
            curr_id, curr_time, curr_emb = thermals[i]
            next_id, next_time, next_emb = thermals[i + 1]

            if next_time and curr_time:
                delta = abs((next_time - curr_time).total_seconds())
                if delta <= TEMPORAL_WINDOW_SECONDS:
                    confidence = max(0.5, 1.0 - (delta / TEMPORAL_WINDOW_SECONDS))
                    created = create_edge(
                        cur, curr_id, next_id, "temporal_sequence",
                        round(confidence, 4), "kg_batch_relate",
                        parse_pgvector(curr_emb), parse_pgvector(next_emb),
                    )
                    if created:
                        edges += 1

        if edges > 0 and edges % 500 == 0:
            conn.commit()
            logger.info(f"  Temporal: {edges} edges so far")

    conn.commit()
    ckpt["edges_created"] += edges
    ckpt["phase"] = "sacred"
    ckpt["last_id"] = 0
    save_checkpoint(ckpt)
    logger.info(f"Phase TEMPORAL complete: {edges} edges")


def phase_sacred(conn, ckpt):
    """Phase 3: sacred_cluster — interconnect sacred thermals."""
    cur = conn.cursor()

    cur.execute("""
        SELECT id, embedding FROM thermal_memory_archive
        WHERE sacred_pattern = true AND embedding IS NOT NULL
        ORDER BY id
    """)
    sacred = cur.fetchall()
    logger.info(f"Phase SACRED: {len(sacred)} sacred thermals to interconnect")

    edges = 0
    # Connect each sacred to its top-3 most similar sacred thermals
    for i, (src_id, src_emb) in enumerate(sacred):
        cur.execute("""
            SELECT t2.id, t2.embedding,
                   1 - (t1.embedding <=> t2.embedding) as similarity
            FROM thermal_memory_archive t1, thermal_memory_archive t2
            WHERE t1.id = %s AND t2.id != t1.id
              AND t2.sacred_pattern = true AND t2.embedding IS NOT NULL
            ORDER BY t1.embedding <=> t2.embedding
            LIMIT 3
        """, (src_id,))

        for tgt_id, tgt_emb, sim in cur.fetchall():
            created = create_edge(
                cur, src_id, tgt_id, "sacred_cluster",
                round(float(sim), 4), "kg_batch_relate",
                parse_pgvector(src_emb), parse_pgvector(tgt_emb),
            )
            if created:
                edges += 1

    conn.commit()
    ckpt["edges_created"] += edges
    ckpt["phase"] = "done"
    save_checkpoint(ckpt)
    logger.info(f"Phase SACRED complete: {edges} edges")


def main():
    conn = get_connection()
    ckpt = load_checkpoint()

    logger.info(f"Starting KG batch relate — phase={ckpt['phase']}, last_id={ckpt['last_id']}, edges_so_far={ckpt['edges_created']}")

    if ckpt["phase"] == "semantic":
        phase_semantic(conn, ckpt)
    if ckpt["phase"] == "temporal":
        phase_temporal(conn, ckpt)
    if ckpt["phase"] == "sacred":
        phase_sacred(conn, ckpt)

    # Final stats
    cur = conn.cursor()
    cur.execute("""
        SELECT relationship_type, COUNT(*), AVG(confidence)::numeric(4,2)
        FROM thermal_relationships
        WHERE valid_until IS NULL
        GROUP BY relationship_type
        ORDER BY count DESC
    """)
    logger.info("\nFINAL KG STATS:")
    total = 0
    for rtype, count, avg_conf in cur.fetchall():
        logger.info(f"  {rtype}: {count} edges (avg confidence {avg_conf})")
        total += count
    logger.info(f"  TOTAL: {total} edges")

    # Edge embedding coverage
    cur.execute("""
        SELECT COUNT(*), COUNT(edge_embedding)
        FROM thermal_relationships
    """)
    tot, with_emb = cur.fetchone()
    logger.info(f"  Edge embeddings: {with_emb}/{tot} ({with_emb/tot*100:.0f}%)" if tot > 0 else "  No edges")

    # Isolated nodes
    cur.execute("""
        SELECT COUNT(*) FROM thermal_memory_archive t
        WHERE t.embedding IS NOT NULL
          AND NOT EXISTS (
            SELECT 1 FROM thermal_relationships r
            WHERE r.source_memory_id = t.id OR r.target_memory_id = t.id
          )
    """)
    isolated = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM thermal_memory_archive WHERE embedding IS NOT NULL")
    embedded = cur.fetchone()[0]
    logger.info(f"  Isolated nodes: {isolated}/{embedded} ({isolated/embedded*100:.0f}%)" if embedded > 0 else "  No embedded nodes")

    conn.close()


if __name__ == "__main__":
    main()

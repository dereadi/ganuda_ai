"""
Conway-Smith Phase 1 Backfill — embeddings + recurrence-links.

Council vote: 8762850ef4b652c7
Companion ticket: duyuktv #2165
Migration: docs/schema/MIGRATION-COUNCIL-RECURRENCE-TELEMETRY-APR28-2026.sql

Two passes against the 9,221 historical council_votes rows:
  Pass 1: populate question_embedding (currently 0/9221 populated). Batch through
          the embedding service at :8003 (1024-dim).
  Pass 2: populate vote_recurrence_links via per-vote KNN search using the
          ivfflat index. For each vote B, find prior similar votes A
          (cosine similarity > threshold), insert (A, B) pairs.

recurrence_index semantics: for row (A, B), recurrence_index = count of votes
similar to B that occurred before B (B's position in its own recurrence chain,
1-indexed). Same value for all rows sharing B (some redundancy, simplifies
querying).

Concerns absorbed (Council vote 8762850ef4b652c7):
  Crawdad: same-DB encryption posture, no external transmission of decision logic.
  Eagle Eye: schema landed first; this script writes to existing columns/tables.
  Spider: read-only on council_votes, INSERT-only on vote_recurrence_links —
          no impact on Gateway routing.
  Gecko: ivfflat index used for KNN; per-vote query <100ms expected.
  Turtle 7GEN: rollback = DELETE FROM vote_recurrence_links; UPDATE council_votes
              SET question_embedding = NULL.
"""

import os
import sys
import time
import logging
from typing import List, Tuple

import psycopg2
import requests

sys.path.insert(0, "/ganuda")
from lib.secrets_loader import get_db_config

EMBEDDING_URL = os.environ.get(
    "EMBEDDING_URL", "http://192.168.132.224:8003/v1/embeddings"
)
EMBEDDING_BATCH = 32
# Phase 1.5 (Apr 28 PM): raised threshold to filter the heavy near-duplicate
# tail (avg_sim was 0.997 in Phase 1), and raised TOP_K to remove the cap
# clamping that saturated 7,999 votes at recurrence_index=50.
SIMILARITY_THRESHOLD = 0.85
TOP_K_PER_VOTE = 200

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("backfill_recurrence")


def get_conn():
    return psycopg2.connect(**get_db_config())


def embed_batch(texts: List[str]) -> List[List[float]]:
    """Call the embedding service. Returns list of 1024-dim vectors."""
    if not texts:
        return []
    resp = requests.post(EMBEDDING_URL, json={"texts": texts}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data["embeddings"]


def vector_to_pg_literal(vec: List[float]) -> str:
    """Format Python list as pgvector literal: '[0.1,0.2,...]'."""
    return "[" + ",".join(f"{x:.6f}" for x in vec) + "]"


def pass_1_embed() -> int:
    """Populate question_embedding for all council_votes where it is NULL.

    Returns count of rows updated.
    """
    log.info("=== Pass 1: embedding backfill ===")
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT vote_id, question
        FROM council_votes
        WHERE question_embedding IS NULL
          AND question IS NOT NULL
          AND length(question) > 0
        ORDER BY vote_id ASC
        """
    )
    rows = cur.fetchall()
    total = len(rows)
    log.info(f"rows to embed: {total}")
    if total == 0:
        cur.close()
        conn.close()
        return 0

    updated = 0
    t0 = time.time()
    for batch_start in range(0, total, EMBEDDING_BATCH):
        batch = rows[batch_start : batch_start + EMBEDDING_BATCH]
        vote_ids = [r[0] for r in batch]
        # Truncate questions to 4000 chars; embedding service has its own limits
        # and recurrence semantics work fine on the prefix.
        questions = [(r[1] or "")[:4000] for r in batch]

        try:
            vecs = embed_batch(questions)
        except Exception as e:
            log.error(f"batch starting at {vote_ids[0]} failed: {e}")
            continue

        if len(vecs) != len(vote_ids):
            log.error(f"vec count mismatch for batch {vote_ids[0]}: got {len(vecs)} expected {len(vote_ids)}")
            continue

        # Update in a single transaction per batch
        for vid, vec in zip(vote_ids, vecs):
            literal = vector_to_pg_literal(vec)
            cur.execute(
                "UPDATE council_votes SET question_embedding = %s::vector WHERE vote_id = %s",
                (literal, vid),
            )
        conn.commit()
        updated += len(vote_ids)

        if batch_start % (EMBEDDING_BATCH * 10) == 0:
            elapsed = time.time() - t0
            rate = updated / elapsed if elapsed > 0 else 0
            log.info(f"  progress {updated}/{total} ({rate:.1f}/s)")

    elapsed = time.time() - t0
    log.info(f"Pass 1 complete: {updated}/{total} embedded in {elapsed:.1f}s")
    cur.close()
    conn.close()
    return updated


def pass_2_recurrence_links() -> int:
    """Populate vote_recurrence_links via per-vote KNN search.

    For each vote B (ordered by voted_at), find prior votes A with cosine
    similarity > threshold using the ivfflat index. Insert (A, B) pairs.
    Compute recurrence_index = count of similar prior votes for B.
    """
    log.info("=== Pass 2: recurrence-link backfill ===")
    conn = get_conn()
    cur = conn.cursor()

    # Truncate target table — full backfill is idempotent
    cur.execute("TRUNCATE TABLE vote_recurrence_links")
    conn.commit()
    log.info("truncated vote_recurrence_links")

    # Iterate votes in chronological order
    cur.execute(
        """
        SELECT vote_id, voted_at
        FROM council_votes
        WHERE question_embedding IS NOT NULL
        ORDER BY voted_at ASC, vote_id ASC
        """
    )
    votes = cur.fetchall()
    total = len(votes)
    log.info(f"votes with embeddings: {total}")

    inserted = 0
    skipped_no_neighbors = 0
    t0 = time.time()

    knn_cur = conn.cursor()
    for i, (vote_id_b, voted_at_b) in enumerate(votes):
        # KNN search via ivfflat index — find top-K most-similar prior votes.
        # Use cosine distance: smaller = more similar. similarity = 1 - distance.
        knn_cur.execute(
            """
            SELECT
              vote_id,
              1 - (question_embedding <=> (
                SELECT question_embedding FROM council_votes WHERE vote_id = %s
              )) AS sim
            FROM council_votes
            WHERE vote_id != %s
              AND voted_at < %s
              AND question_embedding IS NOT NULL
            ORDER BY question_embedding <=> (
              SELECT question_embedding FROM council_votes WHERE vote_id = %s
            )
            LIMIT %s
            """,
            (vote_id_b, vote_id_b, voted_at_b, vote_id_b, TOP_K_PER_VOTE),
        )
        neighbors = [(vid, sim) for vid, sim in knn_cur.fetchall() if sim > SIMILARITY_THRESHOLD]

        if not neighbors:
            skipped_no_neighbors += 1
            continue

        recurrence_index = len(neighbors)  # B's count of similar prior votes

        # Insert (a, b) pairs — a < b because all neighbors are prior in time.
        # But vote_id_a < vote_id_b is the CHECK constraint, not voted_at;
        # filter by vote_id ordering for safety.
        rows_to_insert = []
        for vote_id_a, sim in neighbors:
            if vote_id_a >= vote_id_b:
                continue  # CHECK constraint: vote_id_a < vote_id_b
            rows_to_insert.append((vote_id_a, vote_id_b, sim, recurrence_index))

        if not rows_to_insert:
            skipped_no_neighbors += 1
            continue

        knn_cur.executemany(
            """
            INSERT INTO vote_recurrence_links
              (vote_id_a, vote_id_b, semantic_similarity, recurrence_index, linked_at)
            VALUES (%s, %s, %s, %s, NOW())
            ON CONFLICT (vote_id_a, vote_id_b) DO NOTHING
            """,
            rows_to_insert,
        )
        inserted += len(rows_to_insert)

        if i % 500 == 0:
            conn.commit()
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            log.info(
                f"  vote {i+1}/{total} ({rate:.1f} votes/s, {inserted} links inserted, "
                f"{skipped_no_neighbors} no-neighbor)"
            )

    conn.commit()
    knn_cur.close()
    cur.close()
    conn.close()

    elapsed = time.time() - t0
    log.info(
        f"Pass 2 complete: {inserted} links from {total} votes in {elapsed:.1f}s "
        f"({skipped_no_neighbors} votes had no qualifying neighbors)"
    )
    return inserted


def summary():
    """Final summary stats."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM council_votes WHERE question_embedding IS NOT NULL")
    embedded = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM vote_recurrence_links")
    links = cur.fetchone()[0]
    cur.execute("SELECT count(DISTINCT vote_id_b) FROM vote_recurrence_links")
    distinct_recurring = cur.fetchone()[0]
    cur.execute(
        "SELECT round(avg(recurrence_index)::numeric, 2), max(recurrence_index) FROM vote_recurrence_links"
    )
    avg_idx, max_idx = cur.fetchone()
    cur.execute(
        "SELECT round(avg(semantic_similarity)::numeric, 4), round(min(semantic_similarity)::numeric, 4), "
        "round(max(semantic_similarity)::numeric, 4) FROM vote_recurrence_links"
    )
    avg_sim, min_sim, max_sim = cur.fetchone()
    cur.close()
    conn.close()

    log.info("=== Summary ===")
    log.info(f"  votes with embeddings: {embedded}")
    log.info(f"  recurrence links: {links}")
    log.info(f"  distinct recurring votes (votes with at least one prior similar vote): {distinct_recurring}")
    log.info(f"  recurrence_index avg/max: {avg_idx} / {max_idx}")
    log.info(f"  similarity avg/min/max: {avg_sim} / {min_sim} / {max_sim}")


if __name__ == "__main__":
    pass_1_embed()
    pass_2_recurrence_links()
    summary()

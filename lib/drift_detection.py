#!/usr/bin/env python3
"""
Drift Detection — Phase 2B: Coherence Circuit Breakers
Council Vote #8367

Provides:
  - Specialist coherence measurement (embeddings vs anchor memories)
  - Circuit breaker state machine (CLOSED / HALF_OPEN / OPEN)
  - Health recording after each council vote
  - Confidence adjustment based on circuit breaker states

Embedding model: all-MiniLM-L6-v2 (sentence-transformers)
Already used in the RAG pipeline — small, fast, deterministic.

DB: specialist_health table on bluefin (192.168.132.222)
    Created by JR-DRIFT-PHASE1A-SQL migration.

Cherokee AI Federation — For the Seven Generations
"""

import logging
import psycopg2
import numpy as np
from typing import Dict, Optional, List, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('drift_detection')

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

# All 7 council specialists
SPECIALIST_IDS = [
    'crawdad', 'gecko', 'turtle', 'eagle_eye',
    'spider', 'peace_chief', 'raven'
]

# =============================================================================
# Embedding model — singleton, loaded once on first use
# =============================================================================

_embedding_model = None


def _get_embedding_model():
    """Lazy-load sentence-transformers model as module singleton."""
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded embedding model: all-MiniLM-L6-v2")
        except ImportError:
            logger.error(
                "sentence-transformers not installed. "
                "Run: pip install sentence-transformers"
            )
            raise
    return _embedding_model


def _cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors. Returns 0.0-1.0."""
    dot = np.dot(vec_a, vec_b)
    norm = np.linalg.norm(vec_a) * np.linalg.norm(vec_b)
    if norm == 0:
        return 0.0
    return float(max(0.0, min(1.0, dot / norm)))


# =============================================================================
# 1. measure_specialist_coherence
# =============================================================================

def measure_specialist_coherence(specialist_id: str) -> float:
    """
    Compare a specialist's recent thermal memories (last 30 days) to their
    anchor memory using sentence-transformer embeddings.

    Returns cosine similarity float 0.0 - 1.0.
    Returns 1.0 if no anchor or no recent memories (assume healthy if no data).

    NOTE: This is intended for batch/sanctuary-state use, NOT real-time.
    The embedding model load + DB query + encode takes 2-5 seconds.
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Fetch anchor memory for this specialist
        cur.execute("""
            SELECT original_content
            FROM thermal_memory_archive
            WHERE domain_tag = 'anchor'
              AND metadata->>'specialist' = %s
            LIMIT 1
        """, (specialist_id,))
        anchor_row = cur.fetchone()

        if not anchor_row:
            logger.warning(
                f"No anchor memory for {specialist_id} — returning 1.0 (no baseline)"
            )
            return 1.0

        anchor_text = anchor_row[0]

        # Fetch recent memories tagged with this specialist in metadata
        # Look for council_vote type memories where the specialist responded
        cur.execute("""
            SELECT original_content
            FROM thermal_memory_archive
            WHERE created_at > NOW() - INTERVAL '30 days'
              AND (
                  metadata->>'specialist' = %s
                  OR metadata->>'type' = 'council_vote'
              )
              AND domain_tag != 'anchor'
            ORDER BY created_at DESC
            LIMIT 50
        """, (specialist_id,))
        recent_rows = cur.fetchall()

        if not recent_rows:
            logger.info(
                f"No recent memories for {specialist_id} — returning 1.0 (no data)"
            )
            return 1.0

        # Encode anchor and recent texts
        model = _get_embedding_model()
        anchor_embedding = model.encode(anchor_text, normalize_embeddings=True)

        recent_texts = [row[0] for row in recent_rows]
        recent_embeddings = model.encode(
            recent_texts, normalize_embeddings=True, batch_size=32
        )

        # Average cosine similarity across all recent memories
        similarities = [
            _cosine_similarity(anchor_embedding, emb)
            for emb in recent_embeddings
        ]
        avg_coherence = float(np.mean(similarities))

        logger.info(
            f"Coherence for {specialist_id}: {avg_coherence:.4f} "
            f"(from {len(similarities)} memories)"
        )
        return avg_coherence

    except Exception as e:
        logger.error(f"Error measuring coherence for {specialist_id}: {e}")
        return 1.0  # Fail open — assume healthy on error
    finally:
        if conn:
            conn.close()


# =============================================================================
# 2. check_circuit_breaker
# =============================================================================

def check_circuit_breaker(specialist_id: str) -> str:
    """
    Query specialist_health table for last 10 entries for this specialist.

    Returns circuit breaker state:
      - 'OPEN':      concern_count >= 7 out of 10, OR avg_coherence < 0.5
      - 'HALF_OPEN': concern_count >= 4, OR avg_coherence < 0.65
      - 'CLOSED':    otherwise

    Returns 'CLOSED' if no health data exists (fail open for new specialists).
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("""
            SELECT had_concern, coherence_score
            FROM specialist_health
            WHERE specialist_id = %s
            ORDER BY measured_at DESC
            LIMIT 10
        """, (specialist_id,))
        rows = cur.fetchall()

        if not rows:
            return 'CLOSED'

        concern_count = sum(1 for row in rows if row[0] is True)

        # Average coherence from rows that have a score
        coherence_scores = [row[1] for row in rows if row[1] is not None]
        avg_coherence = (
            float(np.mean(coherence_scores)) if coherence_scores else 1.0
        )

        # OPEN threshold
        if concern_count >= 7 or avg_coherence < 0.5:
            return 'OPEN'

        # HALF_OPEN threshold
        if concern_count >= 4 or avg_coherence < 0.65:
            return 'HALF_OPEN'

        return 'CLOSED'

    except Exception as e:
        logger.error(f"Error checking circuit breaker for {specialist_id}: {e}")
        return 'CLOSED'  # Fail open
    finally:
        if conn:
            conn.close()


# =============================================================================
# 3. record_specialist_health
# =============================================================================

def record_specialist_health(
    specialist_id: str,
    vote_id: str,
    had_concern: bool,
    concern_type: Optional[str],
    response_time_ms: int,
    coherence_score: Optional[float] = None
) -> None:
    """
    Insert a row into specialist_health after each council vote.

    Args:
        specialist_id: e.g. 'crawdad', 'gecko', etc.
        vote_id: The audit_hash from CouncilVote (used as vote identifier).
                 Note: specialist_health.vote_id is INTEGER, but audit_hash
                 is a hex string. We store a CRC32 of the audit_hash to
                 fit the integer column while preserving linkage.
        had_concern: Whether this specialist raised a concern flag.
        concern_type: The concern flag text, e.g. 'SECURITY CONCERN'.
        response_time_ms: Time the specialist took to respond.
        coherence_score: Pre-computed coherence (None if not yet measured).
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Convert audit_hash (hex string) to integer for vote_id column
        # Use last 8 hex chars as unsigned int, fits in PostgreSQL INTEGER
        vote_id_int = None
        if vote_id:
            vote_id_int = int(vote_id[:8], 16) % (2**31)

        # Also compute current circuit breaker state for this specialist
        breaker_state = check_circuit_breaker(specialist_id)

        cur.execute("""
            INSERT INTO specialist_health
                (specialist_id, vote_id, had_concern, concern_type,
                 response_time_ms, coherence_score, circuit_breaker_state,
                 measured_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        """, (
            specialist_id,
            vote_id_int,
            had_concern,
            concern_type,
            response_time_ms,
            coherence_score,
            breaker_state
        ))

        conn.commit()
        logger.debug(
            f"Recorded health for {specialist_id}: "
            f"concern={had_concern}, breaker={breaker_state}"
        )

    except Exception as e:
        logger.error(f"Failed to record health for {specialist_id}: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


# =============================================================================
# 4. get_circuit_breaker_states
# =============================================================================

def get_circuit_breaker_states() -> Dict[str, str]:
    """
    Return dict of all 7 specialist circuit breaker states.

    Example return:
        {
            'crawdad': 'CLOSED',
            'gecko': 'CLOSED',
            'turtle': 'HALF_OPEN',
            'eagle_eye': 'CLOSED',
            'spider': 'CLOSED',
            'peace_chief': 'CLOSED',
            'raven': 'OPEN'
        }
    """
    states = {}
    for sid in SPECIALIST_IDS:
        states[sid] = check_circuit_breaker(sid)
    return states


# =============================================================================
# 5. apply_circuit_breaker_to_confidence
# =============================================================================

def apply_circuit_breaker_to_confidence(
    base_concerns: List[str],
    specialist_responses: List[Any],
    breaker_states: Dict[str, str]
) -> float:
    """
    Compute adjusted confidence score based on circuit breaker states.

    Logic:
      - OPEN specialists: their concerns are excluded from the count entirely
      - HALF_OPEN specialists: their concerns are weighted at 0.5x
      - CLOSED specialists: their concerns count normally (1.0x)

    Original formula: max(0.25, 1.0 - (len(concerns) * 0.15))
    Adjusted formula: max(0.25, 1.0 - (weighted_concern_count * 0.15))

    Args:
        base_concerns: List of concern_type strings from all specialists.
        specialist_responses: List of SpecialistResponse objects from vote().
        breaker_states: Dict from get_circuit_breaker_states().

    Returns:
        Adjusted confidence float, range [0.25, 1.0].
    """
    weighted_concern_count = 0.0

    for resp in specialist_responses:
        if not resp.has_concern:
            continue

        sid = resp.specialist_id
        state = breaker_states.get(sid, 'CLOSED')

        if state == 'OPEN':
            # Drifted specialist — exclude their concern
            logger.info(
                f"Circuit breaker OPEN for {sid}: "
                f"excluding concern '{resp.concern_type}'"
            )
            continue
        elif state == 'HALF_OPEN':
            # Partially drifted — half weight
            logger.info(
                f"Circuit breaker HALF_OPEN for {sid}: "
                f"concern '{resp.concern_type}' weighted at 0.5x"
            )
            weighted_concern_count += 0.5
        else:
            # CLOSED — normal weight
            weighted_concern_count += 1.0

    confidence = max(0.25, 1.0 - (weighted_concern_count * 0.15))

    logger.info(
        f"Confidence: {confidence:.2f} "
        f"(weighted concerns: {weighted_concern_count}, "
        f"raw concerns: {len(base_concerns)})"
    )
    return confidence

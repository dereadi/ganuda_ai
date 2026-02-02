# Jr Instruction: Drift Detection Phase 2B — Coherence Circuit Breakers

**Task:** JR-DRIFT-PHASE2B-COHERENCE
**Priority:** P1
**Assigned:** Software Engineer Jr.
**Depends On:** JR-DRIFT-PHASE1A-SQL
**Platform:** Redfin (192.168.132.223) + Bluefin (192.168.132.222)
**Council Vote:** #8367 — APPROVED

## Objective

Create a drift detection module that:
1. Measures each specialist's semantic coherence against their anchor memory
2. Implements circuit breaker logic (CLOSED / HALF_OPEN / OPEN) based on recent health history
3. Adjusts council vote confidence by excluding or down-weighting drifted specialists
4. Records per-specialist health data after every council vote

This module integrates directly into the existing `specialist_council.py` vote pipeline, providing automated governance over specialist quality without blocking production.

## Architecture

```
vote() call
  |
  v
collect specialist responses (existing)
  |
  v
record_specialist_health() for each  <--- NEW (Step 2)
  |
  v
get_circuit_breaker_states()         <--- NEW (Step 2)
  |
  v
apply_circuit_breaker_to_confidence() <--- NEW (replaces raw confidence calc)
  |
  v
synthesize consensus, build CouncilVote (existing)
```

Circuit breaker states are computed from the `specialist_health` table (created in Phase 1A):
- **CLOSED** — specialist is healthy, normal operation
- **HALF_OPEN** — specialist is showing drift, concerns weighted at 0.5x
- **OPEN** — specialist is significantly drifted, excluded from concern count entirely

Coherence scores are NOT computed in real-time during votes (too slow). They are computed separately during sanctuary state or on-demand, and stored in `specialist_health.coherence_score`. The circuit breaker logic reads the stored values.

## Step 1: Create `/ganuda/lib/drift_detection.py`

```bash
cat > /ganuda/lib/drift_detection.py << 'PYEOF'
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
PYEOF
```

### Key design decisions

- **Fail open everywhere**: if the DB is down or embeddings fail, return `CLOSED` / `1.0` / healthy. Production votes must never be blocked by drift detection errors.
- **Embedding model singleton**: `_get_embedding_model()` loads `all-MiniLM-L6-v2` exactly once per process lifetime. This avoids re-loading a ~80MB model on every call.
- **Audit hash to integer**: `specialist_health.vote_id` is INTEGER (from Phase 1A schema). We convert the 16-char hex `audit_hash` to a 31-bit integer via `int(hash[:8], 16) % (2**31)`. This preserves linkability without schema changes.
- **Coherence computed separately**: `measure_specialist_coherence()` is NOT called during `vote()`. It runs during sanctuary-state batch jobs. The `coherence_score` column in `specialist_health` is `NULL` during real-time recording and backfilled later.

## Step 2: Modify `/ganuda/lib/specialist_council.py`

**Applied by TPM.** Circuit breaker integration applied to specialist_council.py vote() method.

### What NOT to modify

- Do NOT change `vote_first()` in this phase. Circuit breakers for `vote_first()` will be a separate ticket.
- Do NOT change `_synthesize_consensus()`, `_log_vote()`, or `_query_specialist()`.
- Do NOT add circuit breaker logic to the trail-integrated vote methods. That is Phase 3 scope.

## Step 3: Validation

Run these in order. All must pass before marking the task complete.

### 3a. Module import test

```bash
cd /ganuda && python3 -c "
from lib.drift_detection import (
    measure_specialist_coherence,
    check_circuit_breaker,
    get_circuit_breaker_states,
    record_specialist_health,
    apply_circuit_breaker_to_confidence
)
print('All drift_detection functions imported successfully')
"
```

Expected: `All drift_detection functions imported successfully`

### 3b. Circuit breaker states (should all be CLOSED with empty table)

```bash
cd /ganuda && python3 -c "
from lib.drift_detection import get_circuit_breaker_states
states = get_circuit_breaker_states()
print(f'Circuit breaker states: {states}')
assert all(v == 'CLOSED' for v in states.values()), 'Expected all CLOSED with no health data'
print('PASS: All specialists CLOSED (no health data yet)')
"
```

### 3c. Coherence measurement (requires Phase 1A anchor memories)

```bash
cd /ganuda && python3 -c "
from lib.drift_detection import measure_specialist_coherence
for sid in ['crawdad', 'gecko', 'turtle']:
    score = measure_specialist_coherence(sid)
    print(f'{sid} coherence: {score:.4f}')
    assert 0.0 <= score <= 1.0, f'Score out of range: {score}'
print('PASS: Coherence measurement working')
"
```

### 3d. Confidence adjustment logic (unit test, no DB needed)

```bash
cd /ganuda && python3 -c "
from dataclasses import dataclass
from typing import Optional

@dataclass
class FakeResponse:
    specialist_id: str
    has_concern: bool
    concern_type: Optional[str] = None

from lib.drift_detection import apply_circuit_breaker_to_confidence

# Test 1: No circuit breakers active, 3 concerns => 1.0 - (3*0.15) = 0.55
responses = [
    FakeResponse('crawdad', True, 'SECURITY CONCERN'),
    FakeResponse('gecko', True, 'PERF CONCERN'),
    FakeResponse('turtle', True, '7GEN CONCERN'),
    FakeResponse('eagle_eye', False),
    FakeResponse('spider', False),
    FakeResponse('peace_chief', False),
    FakeResponse('raven', False),
]
breakers = {sid: 'CLOSED' for sid in ['crawdad','gecko','turtle','eagle_eye','spider','peace_chief','raven']}
c = apply_circuit_breaker_to_confidence(['a','b','c'], responses, breakers)
assert abs(c - 0.55) < 0.01, f'Expected ~0.55, got {c}'
print(f'Test 1 PASS: all CLOSED, 3 concerns => {c:.2f}')

# Test 2: crawdad OPEN (excluded), gecko HALF_OPEN (0.5x) => weighted = 0 + 0.5 + 1.0 = 1.5
breakers['crawdad'] = 'OPEN'
breakers['gecko'] = 'HALF_OPEN'
c = apply_circuit_breaker_to_confidence(['a','b','c'], responses, breakers)
expected = max(0.25, 1.0 - (1.5 * 0.15))  # 1.0 - 0.225 = 0.775
assert abs(c - expected) < 0.01, f'Expected ~{expected:.2f}, got {c}'
print(f'Test 2 PASS: OPEN+HALF_OPEN adjustments => {c:.2f}')

# Test 3: All concerns from OPEN specialists => confidence should be 1.0
breakers = {sid: 'OPEN' for sid in ['crawdad','gecko','turtle','eagle_eye','spider','peace_chief','raven']}
c = apply_circuit_breaker_to_confidence(['a','b','c'], responses, breakers)
assert abs(c - 1.0) < 0.01, f'Expected 1.0, got {c}'
print(f'Test 3 PASS: all OPEN, all concerns excluded => {c:.2f}')

print('ALL CONFIDENCE TESTS PASS')
"
```

### 3e. Specialist council syntax check

```bash
python3 -c "
import py_compile
py_compile.compile('/ganuda/lib/specialist_council.py', doraise=True)
print('specialist_council.py compiles OK')
"
```

### 3f. Record and retrieve health data (integration test)

```bash
cd /ganuda && python3 -c "
from lib.drift_detection import record_specialist_health, check_circuit_breaker

# Record a test entry
record_specialist_health(
    specialist_id='crawdad',
    vote_id='deadbeef12345678',
    had_concern=False,
    concern_type=None,
    response_time_ms=150,
    coherence_score=None
)
print('Recorded test health entry for crawdad')

# Check circuit breaker still CLOSED (only 1 entry, no concerns)
state = check_circuit_breaker('crawdad')
assert state == 'CLOSED', f'Expected CLOSED, got {state}'
print(f'crawdad circuit breaker: {state} (PASS)')
"
```

### 3g. Clean up test data

```bash
psql -h 192.168.132.222 -U claude -d zammad_production -c "
DELETE FROM specialist_health
WHERE specialist_id = 'crawdad'
  AND vote_id = $(python3 -c \"print(int('deadbeef'[:8], 16) % (2**31))\");
"
```

## Failure Modes & Rollback

| Failure | Impact | Rollback |
|---------|--------|----------|
| `sentence-transformers` not installed | `measure_specialist_coherence` raises ImportError | Install: `pip install sentence-transformers` |
| Phase 1A migration not run | `specialist_health` table does not exist | Run Phase 1A first. `record_specialist_health` will log error and skip (fail open) |
| DB connection failure | All functions return safe defaults (CLOSED / 1.0) | No action needed — production unaffected |
| drift_detection import fails in specialist_council | `vote()` falls back to `breaker_states = all CLOSED` via try/except | Remove the SEARCH/REPLACE changes from Step 2 |

## Dependencies

- **Python packages**: `sentence-transformers`, `numpy`, `psycopg2` (all already installed on redfin)
- **Database**: `specialist_health` table from JR-DRIFT-PHASE1A-SQL migration
- **Anchor memories**: 7 specialist anchor rows from JR-DRIFT-PHASE1A-SQL migration
- **Model file**: `all-MiniLM-L6-v2` auto-downloads from HuggingFace on first use (~80MB). If redfin has no internet, pre-download to `~/.cache/torch/sentence_transformers/`

## Files Modified

| File | Action |
|------|--------|
| `/ganuda/lib/drift_detection.py` | **CREATE** — New module (via bash heredoc) |
| `/ganuda/lib/specialist_council.py` | **MODIFY** — Applied by TPM |

## Acceptance Criteria

- [ ] `/ganuda/lib/drift_detection.py` exists and imports cleanly
- [ ] All 5 public functions are callable
- [ ] `get_circuit_breaker_states()` returns all 7 specialists as CLOSED when no health data exists
- [ ] `apply_circuit_breaker_to_confidence()` correctly adjusts for OPEN (exclude) and HALF_OPEN (0.5x)
- [ ] `specialist_council.py` compiles without syntax errors
- [ ] Council `vote()` method records health data and uses circuit breaker confidence
- [ ] All validation tests in Step 3 pass
- [ ] No existing tests or functionality broken

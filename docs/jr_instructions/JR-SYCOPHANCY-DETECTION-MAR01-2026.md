# JR Instruction: Sycophancy Detection — Council Diversity Monitor

**Task ID**: SYCO-001
**Priority**: 3 (Medium)
**Assigned Jr**: Software Engineer Jr.
**Use RLM**: false
**Sacred Fire Priority**: false
**Depends On**: STANCE-001 (Structured Stance Objects — uses stance data for richer analysis)

## Context

Council diversity diagnostic (scripts/council_diversity_diagnostic.py) found 0.9052 average cosine similarity between specialist responses. This means specialists are saying nearly the same thing — the council is converging to groupthink instead of providing genuinely independent perspectives.

Research (CONSENSAGENT, Virginia Tech, ACL 2025 Findings) identifies this as "sycophancy" — agents reinforcing each other instead of critically engaging. Free-MAD (arXiv:2509.11035) introduces anti-conformity mechanisms.

We need an AUTOMATED diversity check after every council vote that:
1. Computes pairwise cosine similarity between specialist responses
2. Flags pairs that exceed 0.85 threshold
3. Logs the diversity score to the council_votes record
4. Writes a thermal alert when diversity drops below acceptable levels

This uses the existing embedding service on greenfin (192.168.132.224:8003, BGE-large-en-v1.5, 1024d).

## What To Create

Create `lib/council_diversity_check.py`

```python
"""
council_diversity_check.py — Automated sycophancy detection for council votes.

After each council vote, computes pairwise cosine similarity between specialist
responses using the greenfin embedding service. Flags convergence above 0.85.

CONSENSAGENT (Virginia Tech, ACL 2025) calls this "sycophancy detection."
We call it making sure the council is actually seven voices, not one voice
echoed seven times.

Usage:
    from lib.council_diversity_check import check_diversity
    diversity = check_diversity(specialist_responses, audit_hash)
"""

import sys
sys.path.insert(0, '/ganuda/lib')

import json
import logging
import math
import requests
from dataclasses import dataclass
from typing import List, Tuple, Optional

logger = logging.getLogger("council_diversity")

EMBEDDING_URL = "http://192.168.132.224:8003/embed"
SIMILARITY_THRESHOLD = 0.85  # pairs above this are flagged as sycophantic
DIVERSITY_FLOOR = 0.60       # overall diversity below this triggers thermal alert


@dataclass
class DiversityReport:
    """Result of a council diversity check."""
    overall_diversity: float             # 1.0 - mean pairwise similarity
    flagged_pairs: List[Tuple[str, str, float]]  # pairs above threshold
    pairwise_scores: dict                # {(a,b): similarity}
    is_healthy: bool                     # True if no pairs flagged


def _cosine_similarity(vec_a: list, vec_b: list) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _get_embeddings(texts: List[str]) -> Optional[List[list]]:
    """Get embeddings from greenfin embedding service."""
    try:
        response = requests.post(
            EMBEDDING_URL,
            json={"texts": texts},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data.get("embeddings", [])
    except Exception as e:
        logger.warning(f"Embedding service unavailable: {e}")
        return None


def check_diversity(responses, audit_hash: str = "") -> Optional[DiversityReport]:
    """
    Check pairwise diversity of specialist responses.

    Args:
        responses: List of SpecialistResponse objects (must have .specialist_id and .response)
        audit_hash: Council vote audit hash for logging

    Returns:
        DiversityReport or None if embedding service unavailable
    """
    if len(responses) < 2:
        return None

    # Get response texts and specialist IDs
    texts = [r.response for r in responses]
    ids = [r.specialist_id for r in responses]

    # Embed all responses
    embeddings = _get_embeddings(texts)
    if embeddings is None or len(embeddings) != len(texts):
        return None

    # Compute all pairwise similarities
    pairwise = {}
    flagged = []
    similarities = []

    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            sim = _cosine_similarity(embeddings[i], embeddings[j])
            pair_key = f"{ids[i]}:{ids[j]}"
            pairwise[pair_key] = round(sim, 4)
            similarities.append(sim)

            if sim > SIMILARITY_THRESHOLD:
                flagged.append((ids[i], ids[j], round(sim, 4)))

    # Overall diversity = 1 - mean similarity
    mean_sim = sum(similarities) / len(similarities) if similarities else 0
    overall_diversity = round(1.0 - mean_sim, 4)

    report = DiversityReport(
        overall_diversity=overall_diversity,
        flagged_pairs=flagged,
        pairwise_scores=pairwise,
        is_healthy=len(flagged) == 0,
    )

    # Log results
    if flagged:
        pair_names = ", ".join(f"{a}+{b} ({s})" for a, b, s in flagged)
        logger.warning(
            f"[DIVERSITY] Vote #{audit_hash}: {len(flagged)} sycophantic pair(s): "
            f"{pair_names}. Overall diversity: {overall_diversity}"
        )
    else:
        logger.info(
            f"[DIVERSITY] Vote #{audit_hash}: Healthy. "
            f"Overall diversity: {overall_diversity}"
        )

    # Thermal alert if diversity is critically low
    if overall_diversity < DIVERSITY_FLOOR:
        try:
            from ganuda_db import safe_thermal_write
            safe_thermal_write(
                content=(
                    f"COUNCIL DIVERSITY ALERT — Vote #{audit_hash}\n"
                    f"Overall diversity: {overall_diversity} (floor: {DIVERSITY_FLOOR})\n"
                    f"Flagged pairs: {len(flagged)}\n"
                    f"The council is speaking with one voice instead of seven. "
                    f"Specialist prompts may need differentiation.\n"
                    f"Pairs: {pair_names if flagged else 'none'}"
                ),
                temperature=80.0,
                source="council_diversity",
                sacred=False,
                metadata={
                    "type": "diversity_alert",
                    "audit_hash": audit_hash,
                    "overall_diversity": overall_diversity,
                    "flagged_count": len(flagged),
                    "pairwise_scores": pairwise,
                }
            )
        except Exception as e:
            logger.warning(f"Diversity thermal alert failed: {e}")

    return report
```

## What To Change

File: `lib/specialist_council.py`

### Step 1: Add diversity check after vote creation (after the CouncilVote construction, around line 1109)

```python
<<<<<<< SEARCH
        # Log to database
=======
        # Run diversity check (non-blocking — failure does not affect vote)
        try:
            from lib.council_diversity_check import check_diversity
            diversity = check_diversity(responses, audit_hash)
            if diversity:
                print(f"[COUNCIL] Diversity: {diversity.overall_diversity:.3f} "
                      f"({'HEALTHY' if diversity.is_healthy else f'{len(diversity.flagged_pairs)} FLAGGED PAIRS'})")
        except Exception as e:
            print(f"[COUNCIL] Diversity check skipped: {e}")

        # Log to database
>>>>>>> REPLACE
```

**NOTE**: If "# Log to database" does not exist verbatim at that location, search for the next code block after the `CouncilVote(...)` construction and the sacred dissent thermal write (from GHIGAU-001). The diversity check goes AFTER the vote object is created but BEFORE database logging.

## What NOT To Change

- Do NOT modify the embedding service on greenfin
- Do NOT block the vote on diversity check failure — this is advisory, non-blocking
- Do NOT modify specialist prompts based on diversity scores (that's a future step)
- Do NOT modify drift_detection.py

## Verification

1. Import check: `python3 -c "from lib.council_diversity_check import check_diversity, DiversityReport; print('OK')"`
2. Test embedding connectivity: `python3 -c "from lib.council_diversity_check import _get_embeddings; r = _get_embeddings(['test one', 'test two']); print(f'{len(r)} embeddings, {len(r[0])}d')"`
3. Run a council vote and check for `[COUNCIL] Diversity:` in the output
4. Check thermal alerts: `SELECT * FROM thermal_memory_archive WHERE metadata->>'type' = 'diversity_alert' ORDER BY id DESC LIMIT 5;`

## Future Work (NOT in this instruction)

- Automated prompt differentiation when diversity stays low across N votes
- Per-specialist diversity trend tracking (is Crawdad consistently echoing Gecko?)
- Integration with drift_detection circuit breakers
- Dashboard in OpenObserve showing diversity over time

## References

- CONSENSAGENT (Virginia Tech, ACL 2025 Findings) — sycophancy detection
- Free-MAD (arXiv:2509.11035) — anti-conformity mechanisms
- Existing diagnostic: /ganuda/scripts/council_diversity_diagnostic.py
- Embedding service: greenfin:8003 (BGE-large-en-v1.5, 1024d)

"""
council_diversity_check.py — Automated sycophancy detection for council votes.

After each council vote, computes pairwise cosine similarity between specialist
responses using the greenfin embedding service. Flags convergence above 0.85.

CONSENSAGENT (Virginia Tech, ACL 2025) calls this "sycophancy detection."
We call it making sure the council is actually seven voices, not one voice
echoed seven times.

Diamond 3: SYCO-001. Council Vote Mar 1 2026.

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

EMBEDDING_URL = "http://192.168.132.224:8003/v1/embeddings"
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


@dataclass
class DCRReport:
    """Disagreement Collapse Rate — behavioral sycophancy metric.

    Tracks whether specialists are losing distinct voices over time.
    arXiv:2509.23055 (Peacemaker or Troublemaker, Sept 2025).
    """
    dcr_score: float                    # 0.0 = healthy disagreement, 1.0 = total collapse
    drifting_pairs: List[Tuple[str, str, float]]  # pairs converging over time
    vote_window: int                    # how many recent votes were analyzed
    is_healthy: bool                    # True if no pairs drifting


def compute_dcr(window: int = 20) -> Optional[DCRReport]:
    """Compute Disagreement Collapse Rate across recent council votes.

    Looks at the last `window` votes where responses were stored.
    For each specialist pair, computes mean cosine similarity across the window.
    If a pair's mean similarity is INCREASING over the window (regression slope > 0)
    AND their latest similarity exceeds the threshold, they are flagged as drifting.

    This is our adaptation of arXiv:2509.23055's DCR for single-round voting.
    """
    import psycopg2
    import os
    import numpy as np

    try:
        conn = psycopg2.connect(
            host=os.environ.get('CHEROKEE_DB_HOST', '10.100.0.2'),
            database='zammad_production',
            user='claude',
            password=os.environ.get('CHEROKEE_DB_PASS', '')
        )
        cur = conn.cursor()

        # Get recent votes that have stored responses
        cur.execute("""
            SELECT audit_hash, responses
            FROM council_votes
            WHERE responses IS NOT NULL
              AND responses != 'null'
              AND jsonb_array_length(responses) > 1
            ORDER BY voted_at DESC
            LIMIT %s
        """, (window,))
        rows = cur.fetchall()
        conn.commit()  # explicit commit before close
        conn.close()

        if len(rows) < 5:
            logger.info("[DCR] Not enough votes with responses for DCR analysis")
            return None

        # Extract per-specialist response texts across votes
        # vote_responses[vote_idx] = {specialist_id: response_text}
        vote_responses = []
        for _hash, responses_json in rows:
            if not responses_json:
                continue
            vote_map = {}
            for r in responses_json:
                sid = r.get('specialist_id', r.get('name', ''))
                text = r.get('response', '')
                if sid and text:
                    vote_map[sid] = text
            if vote_map:
                vote_responses.append(vote_map)

        if len(vote_responses) < 5:
            return None

        # Get all specialist IDs that appear in at least half the votes
        from collections import Counter
        all_sids = Counter()
        for vm in vote_responses:
            for sid in vm:
                all_sids[sid] += 1
        threshold = len(vote_responses) // 2
        active_sids = [sid for sid, count in all_sids.items() if count >= threshold]

        if len(active_sids) < 2:
            return None

        # For each pair, compute similarity per vote and check for upward trend
        drifting = []
        pair_scores = []

        for i, sid_a in enumerate(active_sids):
            for sid_b in active_sids[i+1:]:
                # Collect per-vote similarities for this pair
                pair_sims = []
                for vm in vote_responses:
                    if sid_a in vm and sid_b in vm:
                        # Simple word overlap as a fast proxy (no embedding call needed)
                        words_a = set(vm[sid_a].lower().split())
                        words_b = set(vm[sid_b].lower().split())
                        if words_a and words_b:
                            jaccard = len(words_a & words_b) / len(words_a | words_b)
                            pair_sims.append(jaccard)

                if len(pair_sims) < 5:
                    continue

                mean_sim = sum(pair_sims) / len(pair_sims)
                pair_scores.append(mean_sim)

                # Check for upward trend (linear regression slope)
                n = len(pair_sims)
                x_mean = (n - 1) / 2
                y_mean = mean_sim
                numerator = sum((i - x_mean) * (s - y_mean) for i, s in enumerate(pair_sims))
                denominator = sum((i - x_mean) ** 2 for i in range(n))
                slope = numerator / denominator if denominator > 0 else 0

                # Flag if trending upward AND recent similarity is high
                recent_sim = sum(pair_sims[:3]) / 3  # most recent 3 votes
                if slope > 0.01 and recent_sim > 0.4:
                    drifting.append((sid_a, sid_b, round(recent_sim, 4)))

        # DCR score: proportion of pairs that are drifting
        total_pairs = len(active_sids) * (len(active_sids) - 1) // 2
        dcr_score = len(drifting) / total_pairs if total_pairs > 0 else 0.0

        report = DCRReport(
            dcr_score=round(dcr_score, 4),
            drifting_pairs=drifting,
            vote_window=len(vote_responses),
            is_healthy=len(drifting) == 0,
        )

        if drifting:
            pair_names = ", ".join(f"{a}+{b} ({s})" for a, b, s in drifting)
            logger.warning(
                f"[DCR] {len(drifting)} drifting pair(s) across {len(vote_responses)} votes: "
                f"{pair_names}. DCR score: {dcr_score:.3f}"
            )
        else:
            logger.info(
                f"[DCR] Healthy — no voice drift across {len(vote_responses)} votes. "
                f"DCR score: {dcr_score:.3f}"
            )

        return report

    except Exception as e:
        logger.warning(f"[DCR] Computation failed (non-fatal): {e}")
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
            pair_str = pair_names if flagged else 'none'
            safe_thermal_write(
                content=(
                    f"COUNCIL DIVERSITY ALERT — Vote #{audit_hash}\n"
                    f"Overall diversity: {overall_diversity} (floor: {DIVERSITY_FLOOR})\n"
                    f"Flagged pairs: {len(flagged)}\n"
                    f"The council is speaking with one voice instead of seven. "
                    f"Specialist prompts may need differentiation.\n"
                    f"Pairs: {pair_str}"
                ),
                temperature=80.0,
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

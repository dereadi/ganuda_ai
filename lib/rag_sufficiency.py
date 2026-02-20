"""
RAG Sufficient Context Framework — Cherokee AI Federation

Evaluates whether retrieved context is sufficient to answer a query.
Returns a confidence score and recommendation (SUFFICIENT, PARTIAL, INSUFFICIENT).

Council Vote #33e50dc466de520e — RC-2026-02C.
"""

import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)

# Thresholds (tunable)
HIGH_CONFIDENCE = 0.65    # Best similarity score must exceed this
MIN_RELEVANT = 2          # At least this many results above LOW_CONFIDENCE
LOW_CONFIDENCE = 0.40     # Minimum useful similarity
TEMPERATURE_BONUS = 0.05  # Bonus for hot memories (temp > 70)


def assess_sufficiency(query: str, results: List[Dict],
                       similarity_key: str = "similarity") -> Dict:
    """Assess whether retrieved results provide sufficient context.

    Args:
        query: The user's question
        results: Retrieved memory dicts with similarity scores
        similarity_key: Key name for similarity score in each result

    Returns:
        Dict with:
            - confidence: float 0-1
            - verdict: SUFFICIENT | PARTIAL | INSUFFICIENT
            - reason: explanation string
            - usable_count: number of results above LOW_CONFIDENCE
    """
    if not results:
        return {
            "confidence": 0.0,
            "verdict": "INSUFFICIENT",
            "reason": "No results retrieved",
            "usable_count": 0,
        }

    scores = [r.get(similarity_key, 0) for r in results]
    best_score = max(scores) if scores else 0
    usable = [s for s in scores if s >= LOW_CONFIDENCE]
    usable_count = len(usable)

    # Temperature bonus: hot memories (recently accessed, high importance) boost confidence
    temp_bonus = 0
    for r in results:
        temp = r.get("temperature", r.get("temp", r.get("temperature_score", 0)))
        if temp and float(temp) > 70 and r.get(similarity_key, 0) >= LOW_CONFIDENCE:
            temp_bonus += TEMPERATURE_BONUS

    # Calculate composite confidence
    confidence = min(1.0, best_score + (usable_count * 0.03) + min(temp_bonus, 0.15))

    if best_score >= HIGH_CONFIDENCE and usable_count >= MIN_RELEVANT:
        verdict = "SUFFICIENT"
        reason = f"Strong match ({best_score:.2f}) with {usable_count} supporting results"
    elif best_score >= LOW_CONFIDENCE and usable_count >= 1:
        verdict = "PARTIAL"
        reason = f"Moderate match ({best_score:.2f}), {usable_count} usable results"
    else:
        verdict = "INSUFFICIENT"
        reason = f"Best match only {best_score:.2f}, {usable_count} usable results"

    return {
        "confidence": round(confidence, 3),
        "verdict": verdict,
        "reason": reason,
        "usable_count": usable_count,
    }


def format_sufficiency_warning(assessment: Dict) -> str:
    """Format a warning message for INSUFFICIENT or PARTIAL contexts."""
    if assessment["verdict"] == "INSUFFICIENT":
        return (
            "\n[CONTEXT WARNING: Retrieved memories may not be relevant to this query. "
            f"Confidence: {assessment['confidence']:.0%}. {assessment['reason']}. "
            "Response may be based on general knowledge rather than tribal memory.]\n"
        )
    elif assessment["verdict"] == "PARTIAL":
        return (
            f"\n[CONTEXT NOTE: Partial match ({assessment['confidence']:.0%} confidence). "
            f"{assessment['reason']}. Some information may be incomplete.]\n"
        )
    return ""
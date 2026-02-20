# Jr Instruction: Sufficient Context Framework for RAG

**Task**: Add confidence scoring so the system knows when it has enough context to answer
**Council Vote**: #33e50dc466de520e (RC-2026-02C, 25 pts, 4/7)
**Kanban**: #1705
**Priority**: 4
**Assigned Jr**: Software Engineer Jr.
**Story Points**: 8
**Depends on**: JR-RAG-PHASE2B-CROSS-ENCODER-RERANKING-FEB13-2026.md (reranker provides scores)

## Context

Currently the council always answers, even when retrieved context is irrelevant or sparse. The Sufficient Context Framework adds a confidence gate: if retrieved memories score below a threshold, the system says "I don't have enough context" instead of hallucinating.

This is implemented as a scoring function that evaluates retrieval quality before passing context to the council.

## Step 1: Create sufficient context module

Create `/ganuda/lib/rag_sufficiency.py`

```python
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
```

## Step 2: Wire sufficiency check into council retrieval

File: `/ganuda/lib/specialist_council.py`

Find the section after reranking (Phase 2b) and before context assembly. Add sufficiency check:

<<<<<<< SEARCH
        context_parts = ["RELEVANT THERMAL MEMORIES (semantic retrieval + reranked):"]
        for row in rows:
            mem_id, content, temp, score = row
            context_parts.append(f"\n[Memory #{mem_id} | temp={temp:.0f} | relevance={score:.2f}]")
            context_parts.append(content)

        return "\n".join(context_parts)
=======
        # Phase 2: Sufficient Context assessment
        sufficiency_note = ""
        try:
            from lib.rag_sufficiency import assess_sufficiency, format_sufficiency_warning
            result_dicts = [{"similarity": r[3], "temp": r[2]} for r in rows]
            assessment = assess_sufficiency(question, result_dicts)
            sufficiency_note = format_sufficiency_warning(assessment)
            print(f"[RAG] Sufficiency: {assessment['verdict']} ({assessment['confidence']:.0%})")
        except Exception as e:
            print(f"[RAG] Sufficiency check skipped: {e}")

        context_parts = ["RELEVANT THERMAL MEMORIES (semantic retrieval + reranked):"]
        if sufficiency_note:
            context_parts.append(sufficiency_note)
        for row in rows:
            mem_id, content, temp, score = row
            context_parts.append(f"\n[Memory #{mem_id} | temp={temp:.0f} | relevance={score:.2f}]")
            context_parts.append(content)

        return "\n".join(context_parts)
>>>>>>> REPLACE

## Manual Steps

Verify sufficiency scoring:

```text
cd /ganuda && python3 -c "
from lib.rag_sufficiency import assess_sufficiency

# High confidence case
results = [{'similarity': 0.82}, {'similarity': 0.71}, {'similarity': 0.45}]
print(assess_sufficiency('power outage', results))

# Low confidence case
results = [{'similarity': 0.25}, {'similarity': 0.18}]
print(assess_sufficiency('quantum computing history', results))
"
```

After patching specialist_council.py:

```text
sudo rm -rf /ganuda/lib/__pycache__
sudo systemctl restart llm-gateway.service
```

## Success Criteria

- [ ] `assess_sufficiency()` returns SUFFICIENT/PARTIAL/INSUFFICIENT with confidence score
- [ ] Temperature bonus rewards hot (important) memories
- [ ] Warning injected into council context when confidence < HIGH_CONFIDENCE
- [ ] Council retrieval logs sufficiency verdict
- [ ] No false negatives on well-known tribal topics (power outage, council votes)

---

*For Seven Generations - Cherokee AI Federation*

# JR Instruction: Sufficient Context Framework for RAG

## Date: January 16, 2026
## Priority: P2 (Council HIGH from Gecko & Turtle)
## Council Vote: 6700b2d88464ab8b
## Assigned To: IT Triad
## Target: Q2 2026

---

## Overview

Implement the Sufficient Context Framework to improve RAG (Retrieval-Augmented Generation) quality in the LLM Gateway. This framework determines when retrieved context is sufficient before generating a response, preventing hallucinations and low-quality answers.

**Council Support:**
- Gecko (Technical): HIGH - Improves response quality
- Turtle (7Gen): HIGH - Ensures accurate knowledge transmission

---

## Problem Statement

Current RAG flow:
1. User asks question
2. Retrieve top-N memories from thermal_memory_archive
3. Generate response with retrieved context

**Issues:**
- No verification that retrieved context actually answers the question
- Model may hallucinate if context is insufficient
- No confidence signal to user about answer quality

---

## Sufficient Context Framework

### Core Concept

Before generating a response, assess whether the retrieved context is **sufficient** to answer the question:

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Query     │───▶│  Retrieve Top-N  │───▶│  Sufficiency    │
│             │    │  Memories        │    │  Check          │
└─────────────┘    └──────────────────┘    └────────┬────────┘
                                                    │
                                    ┌───────────────┼───────────────┐
                                    ▼               ▼               ▼
                              ┌──────────┐   ┌──────────┐   ┌──────────┐
                              │SUFFICIENT│   │ PARTIAL  │   │INSUFFIC- │
                              │          │   │          │   │  IENT    │
                              └────┬─────┘   └────┬─────┘   └────┬─────┘
                                   │              │              │
                                   ▼              ▼              ▼
                              Generate       Generate +      Decline or
                              Response       Caveat          Request More
```

### Sufficiency Levels

| Level | Score | Action |
|-------|-------|--------|
| **SUFFICIENT** | 0.8 - 1.0 | Generate confident response |
| **PARTIAL** | 0.5 - 0.79 | Generate with caveat ("Based on available information...") |
| **INSUFFICIENT** | 0.0 - 0.49 | Decline gracefully, suggest alternatives |

---

## Implementation Plan

### Phase 1: Sufficiency Scorer

Create a module that scores context sufficiency:

```python
# /ganuda/lib/sufficient_context.py

from dataclasses import dataclass
from typing import List, Tuple
import re

@dataclass
class SufficiencyResult:
    score: float                    # 0.0 to 1.0
    level: str                      # 'sufficient', 'partial', 'insufficient'
    missing_aspects: List[str]      # What's missing from context
    confidence_factors: List[str]   # Why we're confident (or not)

class SufficientContextChecker:
    """
    Determines if retrieved context is sufficient to answer a query.

    Uses multiple signals:
    1. Query coverage - Are key terms from query present in context?
    2. Semantic relevance - Do context embeddings match query?
    3. Information density - Does context contain substantive info?
    4. Recency - Is the information recent enough?
    """

    def __init__(self, embedding_model=None):
        self.embedding_model = embedding_model

    def check_sufficiency(
        self,
        query: str,
        retrieved_contexts: List[dict],
        min_contexts: int = 1,
        recency_days: int = 365
    ) -> SufficiencyResult:
        """
        Check if retrieved contexts are sufficient to answer the query.

        Args:
            query: The user's question
            retrieved_contexts: List of retrieved memory dicts
            min_contexts: Minimum contexts required
            recency_days: Max age for context to be considered current

        Returns:
            SufficiencyResult with score and recommendations
        """
        if not retrieved_contexts:
            return SufficiencyResult(
                score=0.0,
                level='insufficient',
                missing_aspects=['No relevant context found'],
                confidence_factors=[]
            )

        scores = []
        missing = []
        factors = []

        # 1. Query coverage check
        coverage_score, coverage_missing = self._check_query_coverage(
            query, retrieved_contexts
        )
        scores.append(coverage_score * 0.4)  # 40% weight
        missing.extend(coverage_missing)
        if coverage_score > 0.7:
            factors.append(f"Good keyword coverage ({coverage_score:.0%})")

        # 2. Semantic relevance (if embeddings available)
        if self.embedding_model:
            relevance_score = self._check_semantic_relevance(
                query, retrieved_contexts
            )
            scores.append(relevance_score * 0.3)  # 30% weight
            if relevance_score > 0.7:
                factors.append(f"High semantic relevance ({relevance_score:.0%})")
        else:
            scores.append(0.15)  # Default if no embeddings

        # 3. Information density
        density_score = self._check_information_density(retrieved_contexts)
        scores.append(density_score * 0.2)  # 20% weight
        if density_score < 0.5:
            missing.append("Retrieved context lacks detailed information")

        # 4. Context count
        count_score = min(len(retrieved_contexts) / min_contexts, 1.0)
        scores.append(count_score * 0.1)  # 10% weight
        if count_score < 1.0:
            missing.append(f"Only {len(retrieved_contexts)} context(s), need {min_contexts}")

        # Calculate final score
        final_score = sum(scores)

        # Determine level
        if final_score >= 0.8:
            level = 'sufficient'
        elif final_score >= 0.5:
            level = 'partial'
        else:
            level = 'insufficient'

        return SufficiencyResult(
            score=final_score,
            level=level,
            missing_aspects=missing,
            confidence_factors=factors
        )

    def _check_query_coverage(
        self,
        query: str,
        contexts: List[dict]
    ) -> Tuple[float, List[str]]:
        """Check how many query terms appear in contexts"""
        # Extract key terms (nouns, verbs) - simplified
        query_terms = set(re.findall(r'\b[a-zA-Z]{3,}\b', query.lower()))
        stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all',
                      'can', 'had', 'her', 'was', 'one', 'our', 'out', 'has',
                      'what', 'how', 'why', 'when', 'where', 'which', 'who'}
        query_terms -= stop_words

        if not query_terms:
            return 1.0, []

        # Check coverage in contexts
        context_text = ' '.join(
            c.get('content', '') + ' ' + c.get('summary', '')
            for c in contexts
        ).lower()

        found_terms = sum(1 for term in query_terms if term in context_text)
        missing_terms = [t for t in query_terms if t not in context_text]

        coverage = found_terms / len(query_terms)
        missing_aspects = [f"Query term '{t}' not found in context" for t in missing_terms[:3]]

        return coverage, missing_aspects

    def _check_semantic_relevance(
        self,
        query: str,
        contexts: List[dict]
    ) -> float:
        """Check semantic similarity between query and contexts"""
        import numpy as np

        query_emb = self.embedding_model.encode(query)
        context_embs = [
            self.embedding_model.encode(c.get('content', ''))
            for c in contexts
        ]

        similarities = [
            np.dot(query_emb, ctx_emb) / (
                np.linalg.norm(query_emb) * np.linalg.norm(ctx_emb)
            )
            for ctx_emb in context_embs
        ]

        return max(similarities) if similarities else 0.0

    def _check_information_density(self, contexts: List[dict]) -> float:
        """Check if contexts contain substantive information"""
        total_chars = sum(len(c.get('content', '')) for c in contexts)
        avg_temp = sum(c.get('temperature', 37) for c in contexts) / len(contexts)

        # Score based on content length and temperature
        length_score = min(total_chars / 1000, 1.0)  # 1000 chars = max
        temp_score = min(avg_temp / 50, 1.0)  # 50 degrees = max

        return (length_score + temp_score) / 2
```

### Phase 2: Gateway Integration

Update the LLM Gateway to use sufficiency checking:

```python
# In /ganuda/services/llm_gateway/gateway.py

from lib.sufficient_context import SufficientContextChecker

checker = SufficientContextChecker()

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    # ... existing code to retrieve memories ...

    # NEW: Check context sufficiency
    sufficiency = checker.check_sufficiency(
        query=request.messages[-1]['content'],
        retrieved_contexts=memories,
        min_contexts=2
    )

    # Modify response based on sufficiency
    if sufficiency.level == 'insufficient':
        # Option 1: Decline gracefully
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "I don't have sufficient information to answer this question accurately. "
                               f"Missing: {', '.join(sufficiency.missing_aspects[:2])}. "
                               "Could you provide more context or rephrase?"
                }
            }],
            "sufficiency": {
                "score": sufficiency.score,
                "level": sufficiency.level
            }
        }

    elif sufficiency.level == 'partial':
        # Add caveat to response
        caveat = "\n\n*Note: This response is based on limited available information.*"
        # ... generate response, append caveat ...

    # Include sufficiency in response metadata
    response["sufficiency"] = {
        "score": sufficiency.score,
        "level": sufficiency.level,
        "factors": sufficiency.confidence_factors
    }

    return response
```

### Phase 3: Council Integration

Add sufficiency checking to Council votes:

```python
# In council_vote endpoint

@app.post("/v1/council/vote")
async def council_vote(request: CouncilRequest):
    # Retrieve context for question
    memories = get_relevant_memories(request.question)

    # Check sufficiency
    sufficiency = checker.check_sufficiency(
        query=request.question,
        retrieved_contexts=memories
    )

    # If insufficient, flag for TPM review
    if sufficiency.level == 'insufficient':
        response["recommendation"] = "REVIEW REQUIRED: Insufficient context"
        response["concerns"].append(
            f"Context sufficiency: {sufficiency.score:.0%} - {', '.join(sufficiency.missing_aspects)}"
        )

    # Include in response
    response["context_sufficiency"] = {
        "score": sufficiency.score,
        "level": sufficiency.level,
        "missing": sufficiency.missing_aspects
    }
```

---

## Configuration

Add to gateway config:

```yaml
# /ganuda/config/gateway.yaml

sufficient_context:
  enabled: true
  min_contexts: 2
  thresholds:
    sufficient: 0.8
    partial: 0.5
  require_embeddings: false  # Set true when embedding model available
  decline_insufficient: false  # Set true to refuse low-confidence answers
```

---

## Validation Checklist

- [ ] SufficientContextChecker module created
- [ ] Gateway chat endpoint updated
- [ ] Council vote endpoint updated
- [ ] Config options added
- [ ] Sufficiency scores visible in responses
- [ ] Partial responses include caveats
- [ ] Insufficient responses handled gracefully
- [ ] Metrics added to Grafana

---

## Metrics to Track

| Metric | Description |
|--------|-------------|
| `sufficient_context_score_avg` | Average sufficiency score |
| `sufficient_context_insufficient_count` | Count of insufficient responses |
| `sufficient_context_partial_count` | Count of partial responses |
| `sufficient_context_latency_ms` | Time to compute sufficiency |

---

## Timeline

| Phase | Target | Deliverable |
|-------|--------|-------------|
| Phase 1 | Week 1-2 | Sufficiency checker module |
| Phase 2 | Week 2-3 | Gateway integration |
| Phase 3 | Week 3-4 | Council integration |
| Testing | Week 4-5 | Validation and tuning |

---

## References

- Research: "Sufficient Context Framework for RAG"
- Council Vote: `6700b2d88464ab8b` (January 16, 2026)
- Related: A-MEM integration for better context retrieval

---

*Cherokee AI Federation - For the Seven Generations*
*"Speak only when your words improve upon silence."*

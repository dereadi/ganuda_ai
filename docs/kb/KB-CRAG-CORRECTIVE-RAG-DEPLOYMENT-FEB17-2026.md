# KB: CRAG — Corrective RAG Deployment
**Date**: February 17, 2026
**Kanban**: #1770
**Sprint**: RC-2026-02E
**Council Vote**: PROCEED 0.84

## Summary

Corrective RAG (CRAG) adds a self-evaluation retrieval loop to the RAG pipeline. After retrieving and reranking memories, CRAG checks for contradictions between retrieved results AND searches for sentinel/correction memories that explicitly override false beliefs.

## Architecture

CRAG slots into the RAG pipeline between cross-encoder reranking and sufficiency assessment:

```
HyDE (pre) → pgvector (retrieve) → Reliability Penalty (Phase 2) → Cross-encoder (rerank) → CRAG (correct) → Sufficiency (gate)
```

## Module: `/ganuda/lib/rag_crag.py`

### Two-Tier Sentinel Search
- **Tier 2 (sacred sentinels)**: `sacred_pattern=true` AND `temperature_score >= 90` — highest authority corrections
- **Tier 1 (correction-language)**: `temperature_score >= 80` with correction keywords ("false belief", "not running", "deprecated", "removed", "was never", "incorrect", "corrected")

### Entity Extraction
Uses `extract_facts()` from `memory_consensus_analyzer.py` to extract infrastructure entities (node, service, port, ip) from both queries and results. Only activates when infrastructure entities are detected.

### Verdicts
- **CONSISTENT**: No corrections found, results are trustworthy
- **CORRECTIONS_FOUND**: Sentinel memories found that contradict or augment results. Correction text is injected into the context.

## Integration Point: `specialist_council.py` line 226

```python
# Phase 2e: CRAG — Corrective retrieval for contradiction detection (#1770)
from lib.rag_crag import evaluate_retrieval
crag_result = evaluate_retrieval(question, rows, DB_CONFIG)
if crag_result['correction_text']:
    crag_note = crag_result['correction_text']
```

CRAG injection at line 251 appends correction text to context_parts.

## Test Results (Feb 17 2026)

| Test | Query | Verdict | Details |
|------|-------|---------|---------|
| 1 | "Grafana on bluefin" | CORRECTIONS_FOUND | 5 corrections, 3 contradictions — correctly identifies false belief |
| 2 | "vLLM on redfin" | CORRECTIONS_FOUND | 5 corrections, 2 contradictions — slightly trigger-happy on valid queries |
| 3 | "Seven Generations" (cultural) | CONSISTENT | Clean pass — no false corrections on non-infra queries |

## Known Tuning Opportunities
- Entity matching is broad — "redfin" + "port" in any query triggers correction search even for valid queries
- Non-harmful (corrections are additional context, not filtering) but generates noise
- Future: Add confidence threshold to suppress low-relevance corrections

## Lessons Learned
- CRAG must be non-fatal — wrapped in try/except so RAG pipeline continues if CRAG fails
- Sacred sentinels (sacred_pattern=true) are the gold standard for corrections
- The "Grafana on bluefin" test case is the canonical validation — must always return CORRECTIONS_FOUND

For Seven Generations.

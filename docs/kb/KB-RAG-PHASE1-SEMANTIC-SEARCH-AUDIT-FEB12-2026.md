# KB: RAG Phase 1 — Semantic Search Audit & Upgrade

**Date**: February 12, 2026
**Council Vote**: #d7275d4814969bbf — REVIEW REQUIRED (0.888 confidence)
**Kanban**: #1760 (sacred fire raised 4 → 21)
**Jr Task**: #709 (Software Engineer Jr.)
**Story Points**: 8 | **River Cycle**: RC-2026-02A

## Audit Findings (Corrected)

The initial explore-agent audit incorrectly reported the schema was NOT deployed. **Actual state:**

| Component | Status | Details |
|-----------|--------|---------|
| pgvector extension | DEPLOYED | v0.8.0 |
| embedding column | DEPLOYED | `vector(1024)` on thermal_memory_archive |
| IVFFlat index | DEPLOYED | `idx_thermal_embedding_cosine` (lists=150) + temp composite index |
| Embeddings backfilled | 98.1% | 77,916 of 79,406 — 1,490 remaining |
| Embedding service | HEALTHY | greenfin:8003, BGE-large-en-v1.5, 1024d |
| Semantic search (Council) | WORKING | specialist_council.py:132 `query_thermal_memory_semantic()` |
| Semantic search (Jr executors) | NOT DEPLOYED | Both files still use ILIKE keyword-only |
| Backfill script | BUG | API format mismatch: sends `{"text":...}` but service expects `{"texts":[...]}` |

## Key Learning

**Always verify audit findings against the actual database before acting.** The explore agent read migration files and assumed they hadn't been run. A single `SELECT column_name FROM information_schema.columns` query would have caught this immediately. **Coyote was right to ask: "Does this actually work, or does it just look like it works?"**

## What Phase 1 Fixes

1. Backfill script API format: `{"text": x}` → `{"texts": [x]}`
2. Jr executor semantic search: ILIKE → embedding service `/v1/search` with ILIKE fallback
3. Retrieval window: 300-400 chars → 600-800 chars
4. Finish backfill: 1,490 remaining memories

## What Phase 2 Will Add (Future)

- Chunking strategy for long memories (overlapping semantic chunks)
- Cross-encoder re-ranking (two-stage: retrieve 10, rerank to 3)
- Evaluation framework (nDCG@5, Recall@5, Precision@5)
- BM25 keyword search to replace naive ILIKE
- Graph RAG activation (entangled_with column, entity extraction)
- Metadata filtering (sacred_pattern, type, recency)

## Nate Hagens RAG Video — Gap Analysis

**What we already have:**
- Hybrid search (semantic + keyword fallback)
- Memory lifecycle (temperature decay, sacred patterns)
- Context window management (RLM bootstrap)

**What we need (from Nate's best practices):**
- Overlapping semantic chunks (20% overlap) — we store monolithically
- Cross-encoder re-ranking — we do single-stage only
- Evaluation frameworks (RAGAS metrics) — we have none
- Graph RAG for entity relationships — infrastructure exists but dormant
- Agentic RAG levels — specialists don't reason ABOUT retrieval quality

## IBM OpenRAG Comparison

- Uses Docling (document parsing), OpenSearch (vector store), Langflow (visual workflows)
- Our approach is more sophisticated in: temperature lifecycle, stigmergic relationships, graceful degradation, Council integration
- Docling could help with CFR/VA legal document parsing (future consideration)
- OpenSearch is overkill at our scale (79K memories vs 1M+ target)
- Verdict: Keep our architecture, consider Docling for document ingestion

## Related

- JR-RAG-PHASE1-SEMANTIC-SEARCH-UPGRADE-FEB12-2026.md (Jr instruction)
- KB-SOLIX-3800-MONITORING-API-DISCOVERY-FEB11-2026.md (greenfin services)
- /ganuda/services/embedding_service/embedding_server.py (embedding service)
- /ganuda/lib/specialist_council.py:132 (semantic search function)

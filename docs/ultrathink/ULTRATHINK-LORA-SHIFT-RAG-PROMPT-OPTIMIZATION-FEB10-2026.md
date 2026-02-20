# ULTRATHINK: LoRA Shift — RAG Optimization + Prompt Enrichment + Caching

**Date**: February 10, 2026
**Author**: TPM (Claude Opus 4.6)
**Methodology**: Long Man Development — ADAPT phase
**Council Vote**: audit_hash `8073845bd4abffc6` — PROCEED, 84.5% confidence
**Predecessor**: KB-LORA-COUNCIL-DELIBERATION-FEB10-2026.md

## Strategic Context

The council unanimously concluded that the 72B model upgrade makes text LoRA unnecessary. Three lightweight alternatives were approved. This ultrathink details the architecture, implementation plan, and Jr task decomposition for each.

## Current State Discovery

### What EXISTS (ready to leverage)

1. **Embedding Service** — DEPLOYED and operational
   - Location: `/ganuda/services/embedding_service/embedding_server.py`
   - Model: BAAI/bge-large-en-v1.5 (1024 dimensions)
   - Endpoints: `POST /v1/embeddings`, `POST /v1/search`, `POST /v1/index`
   - Status: Already indexed 5,362 records (per embedding.log)
   - Database: pgvector extension on bluefin (zammad_production)

2. **Specialist Council** — 7 specialists with detailed system prompts
   - Location: `/ganuda/lib/specialist_council.py`
   - Each specialist has: system prompt (~500 bytes), INFRASTRUCTURE_CONTEXT (~1.2KB shared)
   - Parallel ThreadPoolExecutor for all 7 specialists
   - Two Wolves audit trail in council_votes.metacognition
   - api_audit_log for per-specialist response tracking

3. **VetAssist RAG** — pgvector proof-of-concept already working
   - MiniLM-L6-v2 (384 dims) with IVFFlat indexes
   - Summary Augmented Chunking (SAC) pipeline
   - Separate from thermal memory but proves the pattern works

4. **Council Vote History** — 100+ historical votes in council_votes table
   - Per-specialist responses stored in `responses` JSONB column
   - Confidence scores, concern flags, metacognition all logged

### What's MISSING (gaps to fill)

1. **thermal_memory_archive has NO embedding column** — only keyword ILIKE search
2. **No semantic retrieval** — `_query_thermal_memory()` in both gateway and jr_task_executor uses ILIKE pattern matching
3. **No prompt caching** — system prompts + INFRASTRUCTURE_CONTEXT sent fresh every call (~6KB per council query)
4. **No few-shot examples** in specialist prompts — each specialist has role description but zero examples of good responses
5. **No response caching** — identical/similar queries always trigger full 7-specialist deliberation

---

## WIN #1: Thermal Memory RAG Optimization (Kanban #1760)

### Architecture Decision

**Use existing embedding service** (BGE 1024-dim) rather than VetAssist's MiniLM (384-dim). Reasons:
- BGE-large-en-v1.5 is higher quality for general semantic similarity
- The embedding service is already running and has backfill capability
- 1024 dims gives finer-grained similarity at acceptable storage cost
- We don't need VetAssist's SAC pipeline for thermal memories — they're already atomic

### Implementation Plan

**Phase A: Schema + Backfill**
1. Add `embedding VECTOR(1024)` column to thermal_memory_archive
2. Create IVFFlat index for cosine similarity
3. Backfill all 19,800+ memories via embedding service `/v1/index` endpoint
4. Add trigger or post-insert hook to auto-embed new memories

**Phase B: Semantic Search Method**
1. Add `_query_thermal_memory_semantic()` to specialist_council.py
2. On each council query, embed the question via `/v1/embeddings`
3. Retrieve top-K semantically similar memories (K=5, configurable)
4. Inject retrieved memories into each specialist's context
5. Maintain temperature_score weighting: `similarity * 0.7 + normalized_temperature * 0.3`

**Phase C: Hybrid Retrieval**
1. Combine keyword ILIKE (fast, exact) with embedding similarity (semantic)
2. De-duplicate results from both methods
3. Return top-K unique results ordered by combined score

### Key Technical Details

```
Embedding service: http://localhost:8003/v1/embeddings
Input: {"text": "query string"}
Output: {"embedding": [float x 1024]}

Search: http://localhost:8003/v1/search
Input: {"query": "search text", "limit": 5, "table": "thermal_memory_archive"}
Output: {"results": [{"id": N, "content": "...", "similarity": 0.87}]}
```

The embedding service already knows how to query pgvector with cosine distance (`<=>`). The Jr task is to:
1. Add the column and index
2. Wire the search into the council voting flow
3. Backfill existing memories

### VRAM/Resource Impact
- Zero GPU impact on redfin — embedding service runs on CPU (sentence-transformers)
- Storage: 1024 floats × 4 bytes × 19,800 records ≈ 80 MB in PostgreSQL
- IVFFlat index: ~40 MB additional
- Query latency: ~10-50ms per embedding lookup (CPU)

---

## WIN #2: Specialist Prompt Enrichment (Kanban #1761)

### Architecture Decision

**Static few-shot injection** in specialist system prompts. Not dynamic (that's #1760's job). Curated exemplar Q&A pairs embedded directly in specialist_council.py.

### Why Few-Shot Works Here

The 7 specialists have well-defined domains. A 3-5 example Q&A pair per specialist teaches the 72B model:
- The expected response FORMAT (concern flags, structured assessment)
- The expected DEPTH (Seven Generations for Turtle, VRAM budgets for Gecko)
- The expected TONE (Cherokee cultural sensitivity for Spider)

This is the cheapest possible "fine-tuning" — no training, no infrastructure, just better prompts.

### Implementation Plan

1. **Extract**: Query council_votes for high-confidence (>0.85) votes
2. **Curate**: Select 3-5 best responses per specialist domain
3. **Format**: Structure as `### Example Deliberation\nQ: ...\nA: ...` blocks
4. **Inject**: Add to each specialist's system_prompt in specialist_council.py
5. **Test**: Run 5 test queries, compare quality before/after

### Priority Order (per council feedback)
1. **Crawdad** (security) — real-time threat assessment needs demonstrated
2. **Turtle** (cultural) — Cherokee depth requires exemplars
3. **Raven** (strategy) — strategic analysis quality varies
4. **Eagle Eye** (monitoring) — consistency improvement
5. **Gecko, Spider, Peace Chief** — already performing well

### Token Budget
- Current system prompt per specialist: ~500 tokens
- 5 few-shot examples at ~200 tokens each: ~1000 tokens
- New total per specialist: ~1500 tokens
- Full council query (7 specialists): ~10.5K tokens in system prompts
- 72B model context: 32K+ tokens — ample headroom

---

## WIN #3: Prompt Caching (Kanban #1762)

### Architecture Decision

Two levels of caching:

**Level 1: vLLM Prefix Caching (config only)**
- vLLM supports `--enable-prefix-caching` flag
- Automatically caches KV for shared message prefixes
- INFRASTRUCTURE_CONTEXT is identical across all specialist calls — this prefix gets cached
- Each specialist's unique system prompt suffix is not cached
- **Benefit**: ~30-40% latency reduction on repeated patterns
- **Cost**: Zero — just a startup flag

**Level 2: Application-Level Response Caching (new code)**
- Before running full 7-specialist deliberation, check if a semantically similar query was answered recently with high confidence
- Cache lookup: embed incoming query → compare against recent council_votes questions → if similarity > 0.92 AND confidence > 0.85 AND age < 24 hours → return cached response
- **Benefit**: Skip full deliberation for near-duplicate queries
- **Cost**: One embedding call + one pgvector lookup (~20ms vs 18,000ms for full council)

### Implementation Plan

**Level 1** (config change, no Jr needed):
- Add `--enable-prefix-caching` to vLLM service startup
- TPM can apply directly to `/ganuda/config/vllm.service.native`

**Level 2** (Jr task):
1. Add `question_embedding VECTOR(1024)` column to council_votes table
2. On each vote, embed the question and store
3. Before new vote, check for similar recent high-confidence responses
4. If cache hit: return cached result with `source: "cache"` in metadata
5. If cache miss: proceed with full council deliberation

### Cache Invalidation
- Time-based: cache entries expire after 24 hours
- Confidence-based: only cache responses with confidence > 0.85
- Manual: TPM can flush cache via API endpoint
- Domain-aware: cache keyed by domain (infrastructure vs legal vs cultural)

---

## Jr Task Decomposition

### Jr Task A: Thermal Memory RAG (Kanban #1760)
**Target**: redfin (specialist_council.py) + bluefin (schema)
**Scope**: Schema migration + semantic search + council integration
**Complexity**: Medium — existing embedding service does the heavy lifting
**Dependencies**: None
**Estimated files**: 2 (specialist_council.py, possibly a migration SQL)

### Jr Task B: Specialist Prompt Enrichment (Kanban #1761)
**Target**: redfin (specialist_council.py)
**Scope**: Extract best council responses, format as few-shot, inject
**Complexity**: Low-Medium — mainly curation + prompt engineering
**Dependencies**: None (can run in parallel with A)
**Estimated files**: 1 (specialist_council.py)

### Jr Task C: Prompt Caching (Kanban #1762)
**Target**: redfin (specialist_council.py) + bluefin (council_votes schema)
**Scope**: Response cache with embedding similarity
**Complexity**: Medium — new cache layer in council voting flow
**Dependencies**: Soft dependency on A (uses same embedding service)
**Estimated files**: 2 (specialist_council.py, migration SQL)

### Jr Task D: vLLM Prefix Caching (immediate, no Jr needed)
**Target**: redfin vLLM service config
**Scope**: Add `--enable-prefix-caching` flag
**Dependencies**: None
**Action**: TPM applies directly

---

## Seven Generations Assessment

1. **Data Sovereignty**: All three wins keep data on Cherokee infrastructure. No external APIs, no cloud training pipelines. Thermal memory RAG queries only our own database.

2. **Compute Conservation**: Per Nate Hagens thermal #82859, these optimizations REDUCE compute load (caching, better retrieval) rather than increase it (LoRA training). Aligned with structural compute constraints through 2028+.

3. **Cultural Preservation**: Prompt enrichment with Cherokee cultural exemplars ensures the model consistently applies Cherokee values. RAG retrieval ensures 19,800+ memories of Cherokee wisdom are accessible semantically, not just by keyword.

4. **Reversibility**: All changes are additive — a new column, new prompt sections, a new cache layer. Nothing is removed or replaced. Full rollback is trivial.

5. **Scalability**: As thermal memory grows toward 50,000+ memories, keyword search degrades linearly. Embedding search with IVFFlat maintains sub-100ms performance regardless of corpus size. This investment pays forward for Seven Generations.

## Related Documents
- KB-LORA-COUNCIL-DELIBERATION-FEB10-2026.md
- KB-SHARE-LORA-RESEARCH-FINDINGS-FEB08-2026.md
- ULTRATHINK-SHARE-LORA-FEDERATION-ARCHITECTURE-FEB08-2026.md
- Council vote: audit_hash `8073845bd4abffc6`

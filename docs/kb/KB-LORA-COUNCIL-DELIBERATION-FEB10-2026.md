# KB: LoRA Fine-Tuning Council Deliberation — 72B Makes Text LoRA Unnecessary

**Date**: February 10, 2026
**Council Vote**: audit_hash `8073845bd4abffc6`
**Methodology**: Long Man Development (DISCOVER → DELIBERATE → ADAPT → BUILD → REVIEW)
**Decision**: PROCEED without text LoRA; invest in RAG optimization + prompt enrichment instead

## Background

The original LoRA plan (Feb 8, KB-SHARE-LORA-RESEARCH-FINDINGS-FEB08-2026.md) was written when redfin ran Qwen2.5-Coder-32B. The plan assumed domain adapters (legal, coding, Cherokee cultural) were needed to get specialist-quality responses from the smaller model.

On Feb 9, redfin was upgraded to **Qwen2.5-72B-Instruct-AWQ** on RTX PRO 6000 96GB. This immediately resolved reasoning depth concerns — the ii-researcher DeepSeek routing was marked OBSOLETE, and all 7 council specialists now route exclusively to the 72B model.

## Council Deliberation Summary

All 7 specialists were consulted via `/v1/council/vote` with `high_stakes: true`.

**Vote: PROCEED** | **Confidence: 84.5%** | **0 formal concerns raised**

### Per-Specialist Assessment

| Specialist | 72B Sufficient? | Gap Identified | Recommended Alternative |
|------------|----------------|----------------|------------------------|
| **Crawdad** | Mostly — not perfect for security | Real-time threat assessment, nuanced access control | Structured context injection + RAG |
| **Gecko** | Yes for most tasks | Legal reasoning edge cases, advanced debugging | Few-shot prompting |
| **Turtle** | Yes with RAG | Cherokee cultural depth | RAG from thermal memory (sovereignty-safe) |
| **Eagle Eye** | Yes | Latency with heavy RAG | Optimized indexing, prompt caching |
| **Spider** | Yes for integration | Cultural depth | System prompt enrichment |
| **Peace Chief** | Yes overall | Compute cost awareness | Lightweight alternatives consensus |
| **Raven** | Yes strategically | Domain-specific gaps diminishing | Few-shot + RAG combined |

### Coyote Metacognition

> "The Council speaks with one voice. Coyote wonders: is this wisdom or sleepwalking? No specialist raised a concern. Either perfect, or no one dared question."

**Creative tensions flagged**: Turtle (risk) and Crawdad (security) — both have unique perspectives that may reveal blind spots.

**Uncomfortable question**: "What would change your mind?"

**Answer for future reference**: If specific, repeatable quality failures surface in a domain (e.g., consistently wrong VA disability law citations, Cherokee terminology errors) that cannot be fixed by improving RAG retrieval or prompt examples — THEN revisit LoRA for that specific domain only.

## Decision: Three Lightweight Alternatives

### 1. Thermal Memory RAG Optimization (Priority: HIGH)
- **Current state**: 19,800+ thermal memories, keyword-only retrieval
- **Target**: Vector embedding search for semantic retrieval
- **Mechanism**: Use existing `embedding_vector` column in thermal_memory_archive
- **Benefit**: Every specialist gets contextually relevant memories injected per query
- **Kanban**: #1760

### 2. Specialist Prompt Enrichment (Priority: MEDIUM)
- **Current state**: Generic specialist system prompts
- **Target**: Curated few-shot examples per specialist domain
- **Mechanism**: Extract best council responses, embed in specialist_council.py
- **Priority domains**: Crawdad (security), Turtle (cultural), Raven (strategy)
- **Kanban**: #1761

### 3. Prompt Caching (Priority: LOW)
- **Current state**: Every query goes through full council deliberation
- **Target**: Cache high-confidence patterns for similar query reuse
- **Mechanism**: Domain-tagged cache from >0.9 confidence historical votes
- **Benefit**: Latency reduction + quality consistency
- **Kanban**: #1762

## Items Closed

| Kanban | Title | Disposition |
|--------|-------|-------------|
| #1734 | Research: MixLoRA Specialist Routing | Completed — research valuable, implementation unnecessary with 72B |
| #1735 | Research: Federated Sketching LoRA | Completed — research valuable, implementation unnecessary with 72B |

## Items Retained

| Kanban | Title | Rationale |
|--------|-------|-----------|
| #1744 | Phase 1.2: LoRA Vision Training Pipeline | Vision LoRA (YOLO fine-tuning for camera views) is unrelated to text LoRA. Runs on bluefin RTX 5070, not competing with 72B. Still needed for camera-specific object detection. |

## Nate Hagens Compute Context

Per thermal #82859, global inference compute is structurally constrained through 2028+. The council's recommendation to avoid training overhead aligns with our compute conservation strategy. RAG optimization and prompt engineering have near-zero incremental compute cost vs LoRA training which would consume significant GPU hours on redfin.

## Seven Generations Assessment (Turtle)

Turtle flagged that any fine-tuning MUST use Cherokee-controlled data and respect data sovereignty. RAG from our own thermal memory inherently satisfies this — the data never leaves our infrastructure, never enters a training pipeline owned by others, and remains fully under tribal control.

## Revisit Criteria

Reopen LoRA evaluation if ANY of:
1. Specific domain shows >3 repeatable quality failures that RAG cannot fix
2. A new model release changes the cost/benefit equation
3. Vision LoRA (#1744) succeeds and suggests text LoRA is similarly viable
4. Community releases production-ready Share LoRA for MLX

## Related

- KB-SHARE-LORA-RESEARCH-FINDINGS-FEB08-2026.md (original research)
- ULTRATHINK-SHARE-LORA-FEDERATION-ARCHITECTURE-FEB08-2026.md
- ULTRATHINK-STEREO-CALIBRATION-LORA-VISION-PIPELINE-FEB10-2026.md
- Council vote: audit_hash `8073845bd4abffc6`
- Thermal: #82859 (Nate Hagens compute crisis)

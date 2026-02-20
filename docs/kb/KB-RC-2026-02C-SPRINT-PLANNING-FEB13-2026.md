# KB: RC-2026-02C Sprint Planning — Council-Directed Backlog Prioritization

**Date**: February 13, 2026
**Council Vote**: #33e50dc466de520e
**Confidence**: 0.875 | **Agreement**: 0.99
**Method**: Long Man Development Methodology (DISCOVER → DELIBERATE → ADAPT → BUILD)

## Sprint Summary

| Metric | Value |
|--------|-------|
| Items | 8 (6 Tier 1 + 2 Tier 2) |
| Story Points | 58 SP |
| Focus | Memory systems + RAG pipeline + Cultural preservation |

## Council Voting Results (Position-Weighted)

All 7 specialists voted. Items ranked by weighted score (1st pick = 10 pts, 2nd = 9, etc.):

| Rank | Ticket | Title | Score | Picked By | SP |
|------|--------|-------|-------|-----------|----|
| 1 | #1704 | A-MEM Zettelkasten Memory Enhancement | 70 | 7/7 UNANIMOUS | 13 |
| 2 | #1706 | Mem0 Scalable Long-term Memory | 61 | 7/7 UNANIMOUS | 8 |
| 3 | #1767 | RAG Phase 2b: Cross-Encoder Reranking | 39 | 6/7 | 8 |
| 4 | #1768 | RAG Phase 2c: HyDE Query Enhancement | 28 | 4/7 | 5 |
| 5 | #1705 | Sufficient Context Framework for RAG | 25 | 4/7 | 8 |
| 6 | #1769 | RAG Phase 2d: Vectara open-rag-eval | 25 | 3/7 | 3 |
| 7 | #35 | Sacred Knowledge Protection | 15 | 2/7 | 5 |
| 8 | #5 | Elder Interview Management Workflow | 6 | 1/7 (Turtle) | 8 |

## Specialist Notes

- **Turtle (Seven Generations)**: Uniquely championed #5 Elder Interviews, #7 Democratic Workflow, #1756 owlfin/eaglefin. Cultural preservation items no other specialist prioritized.
- **Gecko (Technical)**: PERF CONCERN on memory system overhead
- **Raven (Strategic)**: STRATEGY CONCERN about velocity vs depth tradeoff
- **Coyote Warning**: "The rabbit who only looks for the hawk above misses the snake below"
- **Council consensus**: Promote #1707 Multiplex Thinking, #1708 Fast-ThinkAct, #1709 Latent Computational Mode from backlog to open

## Jr Instructions Written

| Instruction File | Kanban | Status |
|------------------|--------|--------|
| JR-AMEM-ZETTELKASTEN-BGE-UPGRADE-FEB13-2026.md | #1704 | QUEUED |
| JR-MEM0-SCALABLE-MEMORY-INTEGRATION-FEB13-2026.md | #1706 | QUEUED |
| JR-RAG-PHASE2B-CROSS-ENCODER-RERANKING-FEB13-2026.md | #1767 | QUEUED |
| JR-RAG-PHASE2C-HYDE-QUERY-ENHANCEMENT-FEB13-2026.md | #1768 | QUEUED |
| JR-RAG-PHASE2D-VECTARA-EVAL-FEB13-2026.md | #1769 | QUEUED |
| JR-RAG-SUFFICIENT-CONTEXT-FRAMEWORK-FEB13-2026.md | #1705 | QUEUED |
| JR-SACRED-KNOWLEDGE-PROTECTION-FEB13-2026.md | #35 | QUEUED |
| JR-ELDER-INTERVIEW-WORKFLOW-FEB13-2026.md | #5 | QUEUED |

## Key Decisions

1. **A-MEM fix priority**: amem_memory.py uses wrong embedding model (MiniLM 384d). Must switch to BGE-large 1024d via greenfin:8003 API and use pgvector `<=>` instead of full table scan.
2. **Mem0 as extraction layer**: Mem0 wraps existing thermal archive, NOT replaces it. Uses local vLLM for memory extraction.
3. **RAG pipeline order**: HyDE (pre-retrieval) → pgvector (retrieval) → Cross-encoder (post-retrieval) → Sufficiency check (gating)
4. **Sacred content detection**: Pattern-based with 7 categories. Auto-flags memories that match 1+ patterns.
5. **Elder interviews**: New `elder_interviews` table with automatic priority elevation for elders 80+.

## Dependencies

- RAG Phase 2c (HyDE) depends on Phase 2b (Cross-Encoder) being deployed
- Sufficient Context depends on reranker providing scores
- Mem0 depends on vLLM being healthy (inference cost for extraction)
- Sacred Knowledge detector runs independently

## Learnings

- Council consensus converges strongly on infrastructure/memory items (6/7+ agreement)
- Turtle's cultural voice consistently unique — no other specialist picks cultural preservation
- Coyote's warnings should inform Tier 2 picks (cultural items balance pure-tech sprint)
- Weighted voting (position-scored) gives clearer signal than simple count

---

*For Seven Generations - Cherokee AI Federation*

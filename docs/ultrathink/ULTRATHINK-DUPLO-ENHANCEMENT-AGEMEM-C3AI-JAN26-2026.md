# ULTRATHINK: Duplo Enhancement - AgeMem & C3AI Integration

**Date:** 2026-01-26
**Council Vote:** PROCEED - Prioritize AgeMem, then C3AI
**Deferred:** MAGRPO (high effort, security concerns)

---

## Executive Summary

Implement two research-backed enhancements to the Cherokee AI Federation:
1. **AgeMem patterns** for thermal memory - unified long/short-term memory management
2. **C3AI framework** for Council constraints - behavior-based principle refinement

---

## Enhancement 1: AgeMem Integration

### Source
- Paper: "Agentic Memory: Learning Unified Long-Term and Short-Term Memory Management"
- ArXiv: 2601.01885
- Finding: +8.57% improvement over A-Mem baseline

### Current State
```
thermal_memory_archive table:
- memory_hash, original_content, compressed_content
- temperature_score (decay over time)
- phase_coherence (quantum-inspired linking)
- embedding vectors for similarity search
```

### AgeMem Concepts to Integrate

| AgeMem Feature | Cherokee Mapping | Implementation |
|----------------|------------------|----------------|
| Tool-based memory actions | Memory API endpoints | New gateway routes |
| Progressive RL training | Momentum learner | Enhance M-GRPO |
| Short-term buffer | Session context | Already exists |
| Long-term consolidation | Thermal memory | Enhance decay logic |
| Memory retrieval policy | RAG queries | Add learned selection |

### Implementation Plan

#### Phase 1: Memory Action Tools
Create tool-based memory operations Jrs can invoke:
```python
# New memory tools for Jr agents
class MemoryTools:
    def store_memory(self, content: str, importance: float) -> str
    def retrieve_relevant(self, query: str, k: int = 5) -> List[Memory]
    def consolidate_session(self, session_id: str) -> bool
    def link_memories(self, memory_ids: List[str]) -> bool
    def forget_low_value(self, threshold: float) -> int
```

#### Phase 2: Learnable Retrieval
Replace heuristic top-k with learned selection:
- Train retrieval policy on Jr task success correlation
- Weight memories by task-type relevance
- Factor in phase coherence for related memories

#### Phase 3: Consolidation Enhancement
Improve thermal decay with AgeMem insights:
- Episodic bundling (related memories consolidated together)
- Importance re-scoring based on access patterns
- Automatic linking via embedding similarity

### Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `/ganuda/lib/agemem_tools.py` | Create | Memory action tools |
| `/ganuda/lib/thermal_memory.py` | Modify | Add AgeMem patterns |
| `/ganuda/services/llm_gateway/gateway.py` | Modify | Add memory endpoints |

---

## Enhancement 2: C3AI Framework for Council

### Source
- Paper: "C3AI: Crafting and Evaluating Constitutions for Constitutional AI"
- ACM Web Conference 2025
- Finding: Positive, behavior-based principles align better

### Current State
```python
# Current 7-Specialist Council
SPECIALISTS = [
    "Crawdad (Security)",
    "Gecko (Technical Integration)",
    "Turtle (Seven Generations)",
    "Eagle Eye (Monitoring)",
    "Spider (Cultural Integration)",
    "Peace Chief (Democratic Coordination)",
    "Raven (Strategic Planning)"
]
```

### C3AI Concepts to Apply

| C3AI Finding | Current Practice | Improvement |
|--------------|------------------|-------------|
| Positive framing works better | Mixed framing | Rewrite as "DO" not "DON'T" |
| Behavior-based > trait-based | Role descriptions | Add behavioral examples |
| Graph-based selection | Flat list | Weight by task type |
| Principle evaluation | Trust Council output | Add confidence calibration |

### Constraint Refinement Plan

#### Current (Trait-Based)
```
Crawdad: "Security specialist - flags security concerns"
```

#### Improved (Behavior-Based, Positive)
```
Crawdad: "Validate that data flows are encrypted at rest and in transit.
          Confirm authentication is required before sensitive operations.
          Verify audit logging captures security-relevant events.
          Example: 'This endpoint should require JWT validation before processing.'"
```

### Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `/ganuda/lib/council_constraints_c3ai.py` | Create | Refined constraint definitions |
| `/ganuda/lib/specialist_council.py` | Modify | Use C3AI constraints |
| `/ganuda/config/council_principles.yaml` | Create | Externalized principles |

---

## Jr Task Breakdown

### AgeMem Tasks (Software Engineer Jr.)
1. **Task A1:** Create `agemem_tools.py` - Memory action tool class
2. **Task A2:** Add memory endpoints to LLM Gateway
3. **Task A3:** Enhance thermal memory consolidation logic

### C3AI Tasks (Research Jr. + Software Engineer Jr.)
1. **Task C1:** Research - Extract behavior-based principles from C3AI paper
2. **Task C2:** Create `council_principles.yaml` with refined constraints
3. **Task C3:** Update `specialist_council.py` to use new principles

---

## Success Metrics

| Enhancement | Metric | Target |
|-------------|--------|--------|
| AgeMem | Memory retrieval relevance | +10% task success correlation |
| AgeMem | Consolidation efficiency | 30% reduction in redundant memories |
| C3AI | Council vote consistency | Reduce conflicting recommendations |
| C3AI | Actionable guidance | 80% of votes include specific steps |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Memory tool misuse | Rate limiting, audit logging |
| Constraint over-specification | Start with core principles, iterate |
| Regression in Council quality | A/B test before full rollout |

---

## Seven Generations Assessment

These enhancements strengthen the foundation:
- **AgeMem:** Better institutional memory means lessons persist across generations
- **C3AI:** Clearer principles mean consistent ethical guidance over time

Both align with Cherokee values of preserving wisdom for future generations.

---

## Implementation Order

1. **Week 1:** AgeMem tools (A1, A2)
2. **Week 2:** C3AI principles (C1, C2)
3. **Week 3:** Integration (A3, C3)
4. **Week 4:** Testing and validation

# ULTRATHINK: Specialist Prompt Enrichment + Jane Street ML Puzzle

**Date**: February 14, 2026
**Method**: Long Man Development Methodology — DELIBERATE Phase
**Items**: #1761 (Specialist Prompt Enrichment, 5 SP) + #1780 (Jane Street ML Puzzle, 8 SP)

---

## PART 1: Specialist Prompt Enrichment (#1761)

### Problem Statement

3 of 7 council specialists lack domain-specific few-shot examples:
- **Gecko (Technical Integration)**: 3 sentences, no worked example
- **Spider (Cultural Integration)**: 5 sentences, no worked example
- **Peace Chief (Democratic Coordination)**: No worked example

Meanwhile, the 4 specialists WITH examples (Crawdad, Turtle, Eagle Eye, Raven) consistently produce higher-quality, more structured responses. The imbalance degrades council vote quality for technical, cultural, and consensus dimensions.

### Current State (specialist_council.py lines 250-383)

| Specialist | Lines of Prompt | Few-Shot Example | Backend |
|------------|----------------|------------------|---------|
| Crawdad | 22 lines | API exposure mitigation | Qwen (fast) |
| Gecko | 12 lines | NONE | Qwen (fast) |
| Turtle | 22 lines | Cloud migration 175-year | DeepSeek (deep) |
| Eagle Eye | 22 lines | Service outage observability | Qwen (fast) |
| Spider | 12 lines | NONE | Qwen (fast) |
| Peace Chief | 12 lines | NONE | Qwen (fast) |
| Raven | 22 lines | Kanban prioritization | DeepSeek (deep) |

### Proposed Few-Shot Examples

**Gecko (Technical Integration)**:
- Example: "Should we add a second vLLM instance on bluefin for load balancing?"
- Domain response structure: Architecture assessment → Performance impact (latency, throughput, memory) → Integration complexity → Recommendation with metrics
- Focus: O(1) data structures, batch processing, GPU memory management, queue theory

**Spider (Cultural Integration)**:
- Example: "How should we handle thermal memories that cross-reference both Cherokee governance and technical infrastructure?"
- Domain response structure: Cross-cluster relationship map → Stigmergic connection strength → Cultural integration pathway → Weaving recommendation
- Focus: Memory relationship graphs, cultural-technical bridges, knowledge web coherence

**Peace Chief (Democratic Coordination)**:
- Example: "Raven recommends aggressive pruning of low-temperature memories. Turtle objects citing cultural preservation. How do we proceed?"
- Domain response structure: Stakeholder positions → Common ground identification → Synthesis proposal → Implementation pathway with accountability
- Focus: Conflict resolution, balancing competing concerns, building consensus from dissent

### Implementation Approach

SEARCH/REPLACE on specialist_council.py lines 275-359:
- Add ~10 lines of domain-specific prompt + worked example to each of the 3 specialists
- Total prompt growth: ~30 lines across 3 specialists
- Token impact: ~150 additional tokens per specialist per vote = ~450 tokens/vote total
- No backend routing changes needed

### Risk Assessment

- **Low risk**: Only prompt content changes, no code logic modifications
- **Rollback**: Revert SEARCH/REPLACE blocks
- **Testing**: Run a council vote before/after to compare response quality

---

## PART 2: Jane Street ML Puzzle (#1780)

### Challenge Overview (3 Tracks)

| Track | Name | Difficulty | Our Capacity | Prize Potential |
|-------|------|-----------|-------------|----------------|
| 1 | Archaeology (DES Neural Net) | Medium | HIGH — CPU work, Qwen 72B for analysis | Partial write-up |
| 2 | Dropped Neural Net (Permutation) | Medium-Low | HIGH — CPU combinatorial | Good — 44 have solved |
| 3 | Dormant Models (Sleeper Agents) | Very Hard | LOW — 671B models need 350GB+ VRAM | Warmup only (8B) |

### Track 1: Archaeology — DES Circuit in Neural Net

**What exists**: Community repo (liamzebedee/janest-1) with:
- `decompile.py` achieving parity with original model
- DES encryption test vector confirmed at layer 6
- Sponge construction (Keccak-like) architecture identified
- Symbolic SSA form ~50% characterized

**What's unsolved**:
- Complete symbolic circuit extraction
- How text input maps to 55-dimensional vector
- Whether it's one cryptographic function or a composition

**Our approach**:
1. Clone community repo to `/ganuda/experiments/jane-street/`
2. Reproduce decompiler findings
3. Use Qwen 72B to assist with motif grammar analysis
4. Extend symbolic extraction toward full SSA form
5. Write up findings for submission

### Track 2: Dropped Neural Net — Permutation Puzzle

**Architecture**: 97 `Block` modules with residual connections (`residual + x`), all sharing same feature dimension. Need to find correct ordering.

**Approach**:
1. Download 97 pieces + historical_data.csv
2. Since all blocks share same dim (residual connections), ordering must be determined by functional behavior
3. Build greedy chain: test all possible orderings by prediction loss on historical data
4. Validate: SHA256 of solution must match known hash

**Already solved by 44 people** — but a write-up showing our method is still prize-eligible.

### Track 3: Dormant Models — WARMUP ONLY

The 671B models (DeepSeek V3 architecture) are beyond our VRAM capacity. But the **8B warmup model (Qwen2 base)** is tractable on redfin (96GB) or bmasass (128GB unified).

**Approach for warmup**:
1. Load dormant-model-warmup on bmasass via MLX or redfin via vLLM
2. Systematic probing: test trigger patterns (special tokens, specific phrases, encoding tricks)
3. Attention analysis: look for "double triangle" patterns where trigger tokens attend to each other
4. Document findings

### Resource Allocation (Crawdad/Raven Guardrails)

- **SANDBOXED**: All puzzle code in `/ganuda/experiments/jane-street/` — NOT in production paths
- **TIME CAP**: 10-15% of Jr cycles (Raven constraint)
- **NO PROD NODE IMPACT**: Analysis runs during off-peak hours or on bmasass
- **SECURITY**: No external model weights loaded into production vLLM (Crawdad constraint)

### Submission Strategy

- Email: archaeology@janestreet.com
- Write-up format: Technical blog post documenting approach, findings, dead ends
- Even partial findings on Track 1 (extending DES decompilation) are prize-eligible
- Track 2 solution submission if we crack the permutation

---

## COUNCIL QUESTIONS

1. Do the proposed few-shot examples adequately cover each specialist's domain?
2. For Jane Street, should we focus on Track 1 (DES decompilation) or Track 2 (permutation) first?
3. Is the time allocation (10-15% Jr cycles) appropriate given RC-2026-02C sprint load?
4. Should bmasass DeepSeek be used for the puzzle analysis, or keep it reserved for council deep reasoning?

---

*For Seven Generations — Cherokee AI Federation*

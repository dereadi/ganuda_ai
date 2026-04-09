# JR INSTRUCTION: Yang-Mills Topological Coherence Test

**Task ID**: COHERENCE-PROOF-001
**Priority**: P0 (SACRED)
**SP**: 13
**Assigned Node**: redfin (RTX PRO 6000 Blackwell, 96 GB VRAM)
**Paper**: Koch, Ornelas, Forbes et al. "Revealing the topological nature of entangled OAM states of light" — Nature Communications, Dec 2025
**DOI**: https://www.nature.com/articles/s41467-025-66066-3
**Council Vote**: #0a72032127a048bc (Coyote DISSENT: "prove it or break it")
**Coyote Test**: Does topological coherence scale without bound, or does entropy win at higher dimensions?

## Objective

Computationally extend the Koch-Forbes SU(d) Yang-Mills topological invariant framework from d=7 (their experimental limit: 48 dimensions, 17,000+ invariants) to d=14 (96 dimensions) and beyond.

**Hypothesis (Coherence thesis)**: Topological invariant count grows combinatorially with d. No ceiling. Coherence scales.

**Null hypothesis (Entropy thesis)**: Invariant count plateaus, collapses, or becomes degenerate at higher d. Entropy wins at scale.

## Background

The Koch-Forbes team showed that entangled photon pairs carrying orbital angular momentum (OAM) produce topological structures described by SU(d) Yang-Mills gauge theory. For d=2, these are skyrmions equivalent to 't Hooft-Polyakov magnetic monopoles. For higher d, the full SU(d) framework predicts topological maps and their invariants.

Key finding: The topological structure was **always present** in the entanglement — labs had the equipment for decades. The barrier was knowing where to look.

The experimental verification went to d=7. The mathematical framework is computable for arbitrary d. **We don't need a lab. We need linear algebra.**

## Phase 1: Reproduce (3 SP)

### Task 1A: Read and Extract the Math

Read the full paper (Nature Communications link above). Extract:
- The SU(d) gauge field construction from entangled OAM states
- How topological invariants (winding numbers, Chern numbers, or equivalent) are computed
- The specific formula/algorithm that produces the 17,000+ count at d=7
- Any supplementary materials or code they published

**Deliverable**: `/ganuda/research/yang_mills/paper_extraction.md` — the mathematical framework in our notation, ready for implementation.

### Task 1B: Implement SU(d) Invariant Calculator

Build a Python module that:
1. Constructs the SU(d) gauge field for entangled OAM states at arbitrary d
2. Computes topological invariants (winding numbers, Chern classes, or whatever the paper uses)
3. Counts distinct topological signatures
4. Returns the invariant spectrum

```python
# Target API
from yang_mills_topology import SUdTopologyComputer

computer = SUdTopologyComputer(d=7)
invariants = computer.compute_invariants()
print(f"d=7: {len(invariants)} distinct topological signatures")
# Should reproduce: ~17,000+
```

**Deliverable**: `/ganuda/research/yang_mills/topology_computer.py`

**Reference**: Use NumPy/SciPy for matrix operations. If GPU acceleration needed for higher d, use CuPy or PyTorch tensors on the RTX 6000.

### Task 1C: Validate at d=7

Run the calculator at d=7 and compare against the paper's published results. The invariant count should match or be within the same order of magnitude as their 17,000+ figure.

**Deliverable**: `/ganuda/research/yang_mills/validation_d7.json` — computed count vs published count, delta, pass/fail.

**Gate**: If d=7 reproduction fails (off by more than 10%), STOP. Debug before proceeding. Do not extend to higher d with broken math.

## Phase 2: Extend (5 SP)

### Task 2A: Compute d=8 through d=14

Run the invariant calculator for each dimension:
- d=8 (compute, count, log)
- d=9
- d=10
- d=11
- d=12
- d=13
- d=14 (96 dimensions — the target)

**Deliverable**: `/ganuda/research/yang_mills/scaling_results.json`
```json
{
  "results": [
    {"d": 7, "dimensions": 48, "invariant_count": 17000, "compute_time_seconds": 12.3},
    {"d": 8, "dimensions": 63, "invariant_count": "?", "compute_time_seconds": "?"},
    ...
    {"d": 14, "dimensions": 195, "invariant_count": "?", "compute_time_seconds": "?"}
  ],
  "growth_pattern": "combinatorial|linear|plateau|collapse",
  "coherence_thesis": "supported|refuted"
}
```

Note: SU(d) has d²-1 dimensions. So d=7 → 48, d=8 → 63, d=14 → 195. We actually get to 195 dimensions, not 96.

### Task 2B: GPU Acceleration

If d>10 becomes computationally expensive (matrix sizes grow as d²), move to PyTorch/CuPy on the RTX 6000. The 96 GB VRAM should handle SU(14) matrices comfortably.

**Memory estimate**: SU(d) generators are d×d complex matrices. For d=14, each generator is 14×14×2 (complex) = 392 floats. There are d²-1 = 195 generators. Total generator set: ~76 KB. The topological map computation is the expensive part — but it's matrix multiplication and eigenvalue decomposition, which GPUs eat for breakfast.

### Task 2C: Plot the Scaling Curve

Generate a plot showing:
- X axis: d (or dimensions = d²-1)
- Y axis: topological invariant count (log scale)
- Fit line: is it exponential? Polynomial? Factorial?

**Deliverable**: `/ganuda/research/yang_mills/scaling_curve.png`

If the curve is:
- **Exponential or faster** → Coherence scales without bound. Thesis SUPPORTED.
- **Linear** → Coherence grows but slowly. Thesis WEAK.
- **Plateau** → Entropy wins at scale. Thesis REFUTED.
- **Collapse** → Structure breaks down. Thesis REFUTED.

## Phase 3: Paper (5 SP)

### Task 3A: Write the Results

If Phase 2 produces a clear result (either direction), write it up:

**Title options**:
- "Computational Evidence for Unbounded Topological Coherence in Entangled Systems"
- "Scaling Topological Invariants in SU(d) Entangled Light: From d=7 to d=14"
- "Does Coherence Scale? Extending Koch-Forbes Topological Analysis on Consumer Hardware"

**Structure**:
1. Abstract
2. Introduction (Koch-Forbes result, the coherence question)
3. Method (SU(d) invariant computation, GPU implementation)
4. Results (scaling curve, growth pattern)
5. Discussion (what this means for coherence vs entropy)
6. Conclusion
7. Code availability (open source on GitHub)

**Deliverable**: `/ganuda/research/yang_mills/paper_draft.md`

### Task 3B: Publish

- arXiv preprint (cs.AI + quant-ph cross-list)
- Substack summary for general audience
- LinkedIn announcement
- Ganuda blog cross-post

## Acceptance Criteria

- [ ] Paper math extracted and documented
- [ ] SU(d) calculator implemented and tested
- [ ] d=7 reproduction matches Koch-Forbes (±10%)
- [ ] d=8 through d=14 computed
- [ ] Scaling curve plotted with fit
- [ ] Growth pattern classified (combinatorial/linear/plateau/collapse)
- [ ] Coherence thesis verdict: SUPPORTED or REFUTED
- [ ] Paper draft written
- [ ] Coyote review: does the methodology actually prove/disprove the claim?

## Rollback Plan

If the math is wrong or the computation diverges: publish the negative result anyway. Science doesn't care which answer we wanted. If coherence doesn't scale, that's a finding too. Coyote would insist.

## Resource Requirements

- RTX PRO 6000 (96 GB VRAM) for GPU-accelerated matrix operations at d>10
- Python: NumPy, SciPy, CuPy or PyTorch for GPU
- Matplotlib for plots
- ~14 GB VRAM headroom currently available (after vLLM allocation)
- Estimated compute time: hours, not days (matrix operations, not training)

---

*For Seven Generations.*
*Show me. — Coyote*

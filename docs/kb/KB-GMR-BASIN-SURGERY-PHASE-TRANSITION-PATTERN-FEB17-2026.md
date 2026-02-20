# KB: GMR Basin Surgery & Phase Transition Aware Surgery Pattern

**Date**: February 17, 2026
**Council Vote**: #b44e9044e7cc7e9c (PROCEED, 0.86 confidence)
**Thermal Memory**: #101734
**Kanban**: #1811 (Moltbook monitoring)
**Related**: KB-JANE-STREET-TRACK2-PROGRESS-FEB15-2026.md

## Source

Video analysis of **Geometric Manifold Rectification** (Wang, Li, Jia — arXiv 2602.13045, Feb 2026), extended from data-space class imbalance to **loss landscape topology** by the video creator. Three iterative experiments demonstrating basin interference surgery.

## The GMR Paper (What It Actually Is)

GMR addresses class imbalance as a **topological problem** — when a majority class intrudes into the minority class manifold, overlap obscures the decision boundary. Two components:
1. **Geometric confidence estimation**: Inverse-distance weighted kNN voting (replaces uniform voting)
2. **Asymmetric cleaning**: Strict majority removal (confidence < 0.3), conservative minority protection (only remove if majority confidence > 0.7, max 10% minority removal)

Key detail: switches from Euclidean distance to cosine similarity when dimensionality > 100 (concentration of distances in high-dimensional spaces).

## Extension to Loss Landscape (Video Creator's Contribution)

**Thesis**: Multitask basin interference is structurally isomorphic to class imbalance. When Task A (dominant, 2000 samples) and Task B (subordinate, 400 samples) share parameters, Task A's gradient updates push shared parameters in directions that degrade Task B's loss basin.

### Three Experiments

| Version | Method | Result | Diagnosis |
|---------|--------|--------|-----------|
| v1 | Subspace projection — project gradients onto clean subspace | **Catastrophic** — eigenvalue ratio inverted 35.28 → 0.26, Task A basin collapsed entirely | Removed legitimate optimization directions along with intrusive ones. "Removed the entire organ." |
| v2 | PCA intrusion detection → targeted direction removal | **Zero intrusive samples detected** across all threshold configurations (0.3 to 0.7) | Gradient magnitude separation (Task A: 1.4 mean, Task B: 0.48 — 3:1 ratio) makes clouds trivially separable spatially. But interference is **DIRECTIONAL not spatial**. |
| v3 | Spectral eigenvector alignment → project out shared directions only | **SUCCESS** — 45% improvement at threshold 0.05 (15 eigenvector directions) | Used eigenvector alignment matrix to identify Task A directions that share significant alignment with Task B eigenvectors. These shared directions = intrusion subspace. |

### The Phase Transition (Critical Finding)

The relationship between directions removed and performance is **profoundly non-monotonic**:

| Threshold | Directions Removed | Task B Performance |
|-----------|-------------------|-------------------|
| 0.15 | 3 | Minimal improvement |
| 0.10 | 4 | Slightly worse |
| 0.08 | 6 | **+72% degradation** (worse than no surgery) |
| 0.05 | 15 | **-45% improvement** (best result) |

Partial removal breaks the symmetry the optimizer was exploiting **without providing a clean alternative**. There is a critical threshold where enough of the interfering manifold has been removed that the optimizer finds a qualitatively different solution — one where basins layer cleanly. Below that threshold, partial removal creates worse geometry than no removal at all.

Specific eigenvectors matter: directions 11 and 18 (added at threshold 0.08) have low eigenvalues but their removal destabilizes training. The directions added between 0.08 and 0.05 provide the critical mass for the phase transition.

## Isomorphism to Jane Street Puzzle Solve

| GMR Basin Surgery | Jane Street Track 2 |
|-------------------|---------------------|
| 172 solutions basin-trapped at same MSE | 172 solutions at MSE 0.00275, all converged |
| Interference is directional, not spatial (v2 failure) | Pairwise swaps all increase MSE — wrong move vocabulary |
| Partial surgery worse than none (threshold 0.08 → +72%) | Single swaps within a triple all increase MSE |
| Phase transition at 15 directions (threshold 0.05 → -45%) | 3-opt rotations — coordinated 3-element moves crack it |
| Spectral alignment analysis of eigenvectors | Consensus disagreement analysis across top-50 solutions |
| Specific eigenvectors matter enormously | Specific position triples: 32-34, 28-30, 19-21 |
| v1 "removed entire organ" → catastrophic | Jacobian chain conditioning — elegant theory, marginal signal |
| Diagnostic infrastructure built in from start | puzzle_observer.py 3-layer metacognitive monitor |

## Federation Pattern: Phase Transition Aware Surgery

**Principle**: Partial correction can be worse than no correction. You must cross a critical threshold of coordinated change.

### Applications

1. **Optimization** (proven): 3-opt rotations in combinatorial search. K=1 and K=2 moves make things worse when the landscape has lock-step barriers requiring K=3.

2. **Memory Consolidation** (deploying — Jr #1802): When thermal memories disagree, resolving *some* contradictions without resolving the full cluster can leave the knowledge base in a worse state than the original contradiction. The consensus disagreement analyzer must identify full contradiction clusters and resolve them atomically.

3. **Council Deliberation**: When specialists disagree, forcing partial consensus (3 of 7 agree) may be worse than preserving the full disagreement for TPM resolution. Peace Chief synthesis must cross the phase transition — enough specialist perspectives integrated that the result is qualitatively different from any single view.

4. **Service Migration**: Partially migrating a service (e.g., moving only the API but not the database) can create worse reliability than the original monolith. Migration must be atomic enough to reach a stable new configuration.

5. **Governance**: Partial policy changes that break existing symmetry without providing a complete new framework. Constitutional DyTopo (#82856) — topology changes must be complete enough to establish new stable patterns.

## Moltbook Creator → OpenAI

The creator of Moltbook was hired by OpenAI (Feb 17, 2026). Community reaction is positive — "how cool is that?" The real question: what does this say about OpenAI? Are they struggling with competitors, or stretching into new directions?

The hire validates Moltbook's significance in the AI community. Platform likely stable — a Big Tech acquisition of the creator is a stamp of approval, not abandonment. The video speaker notes "300-400 people more advanced" — this is the talent pool our Jane Street solve and Reddit engagement (30K views) puts us in front of.

**Action**: Monitor Moltbook platform stability 30 days (Kanban #1811). Continue posting. Archive our content. Assess alternatives only if instability appears.

## Key Insight (Coyote's Corner)

The council voted PROCEED with 1.0 agreement and zero concerns. Coyote flagged: "The rabbit who only looks for the hawk above misses the snake below." Unanimous agreement on a two-item deliberation with this much surface area suggests the council didn't engage deeply enough with the Moltbook platform risk dimension. The GMR isomorphism was the easy part — the real strategic question (platform sovereignty) got smoothed over.

---

For the Seven Generations.
Cherokee AI Federation

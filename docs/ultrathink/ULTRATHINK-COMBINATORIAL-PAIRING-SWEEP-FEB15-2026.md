# ULTRATHINK: Combinatorial Pairing Sweep — Jane Street Track 2

**Date**: February 15, 2026
**Sprint**: RC-2026-02D
**Kanban**: #1780
**Context**: Pool best MSE 0.004576 (3.2x better than public solver), SHA256 NOT matched

## The Problem

We have 48 (inp, out) pairings. Trace analysis via `trace(W_out @ W_inp)` + Hungarian assignment identifies 38/48 that agree with the pool-best solution. The remaining **10 pairings** are where trace and pool disagree:

```
inp  6: trace→out  8 (-7.51) vs pool→out 18 ( 0.15)   ← trace MUCH stronger
inp 10: trace→out 42 (-7.89) vs pool→out  8 (-0.62)   ← trace MUCH stronger
inp 18: trace→out 20 (-7.78) vs pool→out 28 (-0.06)   ← trace MUCH stronger
inp 20: trace→out 28 (-12.21) vs pool→out 20 (-0.63)  ← trace MUCH stronger
inp 21: trace→out 18 (-8.99) vs pool→out 46 (-0.19)   ← trace MUCH stronger
inp 22: trace→out 41 (-8.41) vs pool→out 39 (-0.51)   ← trace MUCH stronger
inp 24: trace→out  3 (-7.98) vs pool→out 42 (-0.42)   ← trace MUCH stronger
inp 30: trace→out 46 (-9.72) vs pool→out  3 (-0.02)   ← trace MUCH stronger
inp 32: trace→out 39 (-8.85) vs pool→out 16 ( 0.74)   ← trace MUCH stronger (pool is POSITIVE)
inp 39: trace→out 16 (-8.96) vs pool→out 41 (-0.33)   ← trace MUCH stronger
```

**Key observation**: For ALL 10 disagreements, trace pairing has strongly negative traces (-7.5 to -12.2) while pool pairing has near-zero traces (-0.62 to +0.74). The trace signal overwhelmingly favors its own choices. Yet the pool's pairing evolved through billions of SA evaluations.

**The paradox**: If trace is right on all 10, why isn't MSE zero? Because the **ordering** (which block goes in which position) interacts with the pairing. The trace solver's SA found a good ordering for its 38+10 pairing, but maybe a DIFFERENT subset of those 10 needs to be "pool" to enable a better ordering.

## Search Space Analysis

- 10 binary choices (trace vs pool for each disagreement) = 2^10 = **1,024 combinations**
- For each combination, we need ordering SA to evaluate quality
- The pool-best ordering is a good starting point but will need adaptation

### Constraint: Pairings Must Be Valid Permutations

The 10 disagreements involve overlapping out indices. For example:
- Trace: inp 6→out 8, inp 10→out 42
- Pool: inp 6→out 18, inp 10→out 8

If we pick trace for inp 6 (→out 8) and pool for inp 10 (→out 8), we get **two inputs mapped to out 8** — invalid. The choices are NOT independent.

**This is critical.** We can't just flip each of the 10 independently. The 10 disagreements form a **permutation subgroup** — we must swap in consistent subsets that maintain a valid 1:1 mapping.

### Cycle Analysis of the Disagreements

The trace pairing and pool pairing disagree on these mappings:

```
Trace:  6→8,  10→42, 18→20, 20→28, 21→18, 22→41, 24→3,  30→46, 32→39, 39→16
Pool:   6→18, 10→8,  18→28, 20→20, 21→46, 22→39, 24→42, 30→3,  32→16, 39→41
```

The out indices involved: {3, 8, 16, 18, 20, 28, 39, 41, 42, 46}

The composition (trace^-1 * pool) on these out indices forms cycles:
- 8→18→28→20→...  (need to trace through)
- The valid swaps must follow these cycles

**Actually**, a simpler approach: since both trace and pool each define a valid permutation (bijection), any combination that takes ALL of trace's mapping for some inputs and ALL of pool's mapping for the complement WILL be valid IF AND ONLY IF we swap complete cycles.

Let me trace the cycles:
- Start at inp 6: trace says 8, pool says 18
- Find who maps to 18 in trace: inp 21→18. Pool says inp 21→46.
- Find who maps to 46 in trace: inp 30→46. Pool says inp 30→3.
- Find who maps to 3 in trace: inp 24→3. Pool says inp 24→42.
- Find who maps to 42 in trace: inp 10→42. Pool says inp 10→8.
- 8 is where we started → **CYCLE: {6, 21, 30, 24, 10}** mapping outs {8, 18, 46, 3, 42}

Second cycle:
- Start at inp 18: trace says 20, pool says 28
- Find who maps to 28 in trace: inp 20→28. Pool says inp 20→20.
- Find who maps to 20 in trace: inp 18→20 (already visited) → **CYCLE: {18, 20}** mapping outs {20, 28}

Third cycle:
- Start at inp 22: trace says 41, pool says 39
- Find who maps to 39 in trace: inp 32→39. Pool says inp 32→16.
- Find who maps to 16 in trace: inp 39→16. Pool says inp 39→41.
- 41 is where we started → **CYCLE: {22, 32, 39}** mapping outs {41, 39, 16}

**Three independent cycles**: {6,21,30,24,10}, {18,20}, {22,32,39}

For each cycle, we can either use ALL trace pairings or ALL pool pairings. Mixed choices within a cycle create an invalid permutation.

**Valid combinations: 2^3 = 8** (not 1,024!)

This is a MUCH smaller search space. 8 combinations with full SA evaluation is trivial — maybe 2-3 hours total.

## The 8 Valid Pairing Combinations

| ID | Cycle A (5 inp) | Cycle B (2 inp) | Cycle C (3 inp) | Expected |
|----|-----------------|-----------------|-----------------|----------|
| 0 | TRACE | TRACE | TRACE | Pure trace (current solver) |
| 1 | TRACE | TRACE | POOL | |
| 2 | TRACE | POOL | TRACE | |
| 3 | TRACE | POOL | POOL | |
| 4 | POOL | TRACE | TRACE | |
| 5 | POOL | TRACE | POOL | |
| 6 | POOL | POOL | TRACE | |
| 7 | POOL | POOL | POOL | Pool-like (close to old SA fleet) |

Combination 0 = pure trace (MSE 0.004576 currently).
Combination 7 = pool pairings for all 10 (close to old SA fleet's 0.030161).

The answer is one of these 8. We just need to run ordering SA on each.

## Evaluation Strategy

For each of the 8 combinations:
1. Construct the full 48-pair mapping (38 agreed + cycle choices)
2. Seed ordering from pool best (inp_sigma from MSE 0.004576 solution)
3. Run 200K-step ordering-only SA with 2000 data samples (full dataset)
4. Run 5 random restarts to avoid local optima
5. Record best MSE + ordering
6. **Check SHA256 hash** for every solution

Total: 8 combinations × 5 runs × 628s (M4 speed) = ~7 hours on bmasass alone.
With 4 Mac nodes: ~2 hours.

## Hash Verification

```python
SOLUTION_HASH = "093be1cf2d24094db903cbc3e8d33d306ebca49c6accaa264e44b0b675e7d9c4"
perm_str = ",".join(str(p) for p in permutation)  # 97-element list
h = hashlib.sha256(perm_str.encode()).hexdigest()
```

The permutation is the FULL 97-piece ordering: `[inp_indices[inp_sigma[k]] for k in range(48)] + [out_indices[out_sigma[k]] for k in range(48)] + [last_idx]`

## Risk Assessment

**High confidence this works**: The trace signal is overwhelmingly strong on the 10 disagreements (all -7 to -12 vs near-zero). The pure trace combination (0) already achieves 0.004576. The correct combination should achieve near-zero MSE. If NONE of the 8 combinations gives near-zero MSE, it means some of the 38 "agreed" pairings are also wrong — but this is unlikely given the trace strength.

**Fallback**: If the 8-combination sweep doesn't solve it, expand to allow mixed trace/pool within the 5-element cycle (Cycle A). That's 2^5 - 2 = 30 additional sub-combinations for Cycle A, with Cycles B and C fully enumerated. Total: ~120 combinations.

## Implementation Notes

- Script should be self-contained (no imports from lib/)
- Use pool-best solution as ordering seed
- 2000 data samples for full-dataset accuracy
- Check SHA256 hash after EVERY run (not just the best)
- Save ALL results to js_puzzle_pool with worker tag "sweep-{combo_id}"
- Print the combo ID + MSE in a clean summary table at the end

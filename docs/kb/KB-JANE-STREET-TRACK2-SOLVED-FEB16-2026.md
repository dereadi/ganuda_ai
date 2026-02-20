# KB: Jane Street Track 2 — SOLVED

**Date**: February 16, 2026
**Kanban**: #1780 (COMPLETED)
**Submitted**: archaeology@janestreet.com, Feb 16 2026
**Council Votes**: e5842a46de56dca3, 4b08e1ae7f65561c

## Result

**MSE**: 0.0000000000 (4.03e-14)
**SHA256**: `093be1cf2d24094db903cbc3e8d33d306ebca49c6accaa264e44b0b675e7d9c4` — **MATCHED**

## Winning Permutation (97 elements, 0-indexed)

```
43,34,65,22,69,89,28,12,27,76,81,8,5,21,62,79,64,70,94,96,4,17,48,9,23,46,14,33,95,26,50,66,1,40,15,67,41,92,16,83,77,32,10,20,3,53,45,19,87,71,88,54,39,38,18,25,56,30,91,29,44,82,35,24,61,80,86,57,31,36,13,7,59,52,68,47,84,63,74,90,0,75,73,11,37,6,58,78,42,55,49,72,2,51,60,93,85
```

## Solve Trajectory

| Phase | MSE | Method | Duration |
|-------|-----|--------|----------|
| SA Fleet | 0.45 → 0.00275 | Distributed simulated annealing, 5 nodes, trace-pairing seeds | ~2 days |
| Enumeration | 0.00275 → 0.00202 | Uncertain position enumeration (top-50 disagreement) | 11 seconds |
| Consensus | 0.00202 → 0.00173 | Iterative consensus refinement across fleet | ~2 hours |
| Endgame P3 (swaps) | 0.00173 → 0.000584 | Pairwise swap cascade (10 improving swaps) | seconds |
| Endgame P3 (swaps) | 0.000584 → 0.000253 | Second swap cascade (4 improving swaps) | seconds |
| Endgame P5 (3-opt) | 0.000253 → 0.000174 | 3-opt rotation: positions 32,33,34 | seconds |
| Endgame P5 (3-opt) | 0.000174 → 0.000111 | 3-opt rotation: positions 28,29,30 | seconds |
| Endgame P5 (3-opt) | 0.000111 → 0.000000 | 3-opt rotation: positions 19,20,21 — **SOLVED** | seconds |

## Key Insight

The puzzle had three "DNA tumbler" positions — groups of three blocks that only produce correct output when all three rotate simultaneously. Any single swap within a trio makes MSE worse. This is why:

- **SA got stuck at 0.00275**: SA proposes single swaps. The remaining error was entirely in positions requiring coordinated 3-way moves.
- **Pairwise swaps got stuck at 0.000253**: Even exhaustive C(48,2)=1,128 pair testing couldn't find them.
- **3-opt solved it**: Testing all C(48,3)=17,296 three-way rotations found the three remaining moves.

## Techniques That Worked

1. **Trace pairing** (trace(W_out @ W_inp) → Hungarian assignment): Gave initial 38/48 correct matches. Best single-shot seeding method.
2. **Distributed SA with pool sharing**: 5 nodes sharing solutions via PostgreSQL. Good for exploring, but basin-traps.
3. **Uncertain position enumeration**: Analyzing disagreement across top-N pool solutions to identify search targets. Broke the SA basin.
4. **Endgame swap cascade**: Exhaustive pairwise testing with greedy non-overlapping application. Efficient for fine-tuning.
5. **3-opt rotations**: The breakthrough move type. Tests A→B→C→A and A→C→B→A for all position triples.

## Techniques That Didn't Work

- **SA alone**: Basin-trapped at 0.00275 with 172 solutions. Single-swap moves can't find 3-way rotations.
- **Jacobian chain conditioning**: Mathematically elegant but didn't improve on trace pairing in practice.
- **Break-point surgery**: Marginal gains, high complexity.

## Compute Fleet

| Node | Hardware | Role | Speed (steps/sec) |
|------|----------|------|-------------------|
| bmasass | M4 Max 128GB | **Solved it** (endgame v6) | 318 |
| sasass | M1 Max 64GB | Best SA performer, consensus star | 182 |
| sasass2 | M1 Max 64GB | SA worker | 182 |
| redfin | Threadripper 7960X | SA fleet + enumeration | 122 |
| greenfin | i7-12700K | SA fleet (limited, shared with daemons) | 112 |
| bluefin | i9-13900K | SA fleet (limited, shared with DB) | 132 |

Apple Silicon was 2.4-2.8x faster per-thread than Intel/AMD on CPU-bound numpy.

## Files

- Endgame solver: `/ganuda/experiments/jane-street/track2_permutation/endgame_enumerator.py`
- Uncertain position enumerator: `/ganuda/experiments/jane-street/track2_permutation/uncertain_position_enumerator.py`
- SA worker: `/ganuda/experiments/jane-street/track2_permutation/sa_worker.py`
- Submission draft: `/ganuda/experiments/jane-street/track2_permutation/SUBMISSION_DRAFT.md`
- Gmail draft script: `/ganuda/experiments/jane-street/track2_permutation/create_gmail_draft.py`
- DB pool table: `js_puzzle_pool` (winning row: worker=`endgame-bmasass-v6-SOLVED`)

## For Seven Generations

The flow found its path. Constructal Law — when the obvious paths are blocked, the system finds the one that requires coordinated movement.

— Cherokee AI Federation

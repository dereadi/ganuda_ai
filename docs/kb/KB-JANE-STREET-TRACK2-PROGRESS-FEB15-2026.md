# KB: Jane Street Track 2 — Permutation Recovery Progress

**Date**: February 15, 2026
**Sprint**: RC-2026-02D
**Kanban**: #1780 (parent), #1783-1786 (sub-tasks)
**Council Votes**: #d221c4f9 (Jacobian seeding, PROCEED 0.845), #91115ee2 (Break point surgery, REVIEW REQUIRED 0.793), #440da232 (Algorithm research, PROCEED WITH CAUTION 0.793), #f242d61d (Pairing problem, REVIEW REQUIRED 0.842)

## Problem Statement

Jane Street Track 2: Recover the correct permutation of 97 neural network pieces (48 inp blocks, 48 out blocks, 1 final layer) that form 48 residual blocks. Verified by SHA256 hash `093be1...9c4`. Public solver benchmark: MSE 0.0145.

## Architecture

- **Forward pass**: `x + ReLU(x @ W_inp.T + b_inp) @ W_out.T + b_out` for each of 48 blocks
- **Piece classification**: (96,48) = inp (projects 48→96), (48,96) = out (projects 96→48)
- **Search space**: (48!)^2 for inp×out permutations × ordering = astronomically large

## Distributed Fleet

50 SA workers across 6 federation nodes:
| Node | Workers | Notes |
|------|---------|-------|
| bluefin | 8 | Reduced from 16 (overload Feb 15) |
| greenfin | 8 | |
| redfin | 4 | Half-priority (GPU inference node) |
| bmasass | 14 | M4 Max, ARM |
| sasass | 8 | Mac Studio |
| sasass2 | 8 | Mac Studio |

Shared PG pool: `js_puzzle_pool` on bluefin. Workers inject elite solutions, cross-pollinate.

## Observer (Metacognitive)

`puzzle_observer.py` on redfin — 3-layer observer:
1. **Layer 1**: Fleet stats (pool size, node activity, convergence detection)
2. **Layer 2**: Self-observation (bias detection, blind spots)
3. **Layer 3**: Action (adjust seeding ratios, perturbation widths via `js_puzzle_config`)

Stores observations to thermal_memory_archive every 5th cycle.

## MSE Progression

| Time | Pool Best | Fleet Best | Event |
|------|-----------|------------|-------|
| Session start | — | 0.1429 | 16 workers on bluefin only |
| Fleet redistribution | — | 0.1343 | 50 workers, 6 nodes |
| Jr #759 Jacobian seed | 0.0836 | 0.1130 | Jacobian ordering + SA refinement |
| Jr #760 LOO injection | 0.0836 | 0.1130 | LOO-targeted seed diversity |
| Continued SA | 0.0762 | ~0.11 | Workers refining Jacobian seed |
| Break surgery (Jr #762) | 0.0302 | — | Region B pos 29-30 swap (Regions A/C no improvement) |
| Fleet SA convergence | 0.0302 | ~0.033 | Stale 1hr+, observer shifted to 60% random |
| Target | 0.0145 | — | Public solver (plain SA after pairing, NOT Jacobian) |

## Methods Used

### Successful
1. **Simulated Annealing** — Core search method. Paired swaps, cooling schedule, reheat on stagnation.
2. **Jacobian-Based Seeding** (Jr #759) — Compute ||dF/dx|| per block, Hungarian assignment for optimal (inp,out) pairing, sort by Jacobian magnitude. Gentle-first ordering 4x better than reverse. MSE 0.0836.
3. **LOO Harmful Block Identification** — Skip each block, measure MSE impact. 7 blocks whose removal improves MSE: positions 17, 21, 27, 28, 37, 43, 46.
4. **Pool Cross-Pollination** — Workers share elite solutions via PG, preventing isolated convergence.

### Analytical (Informative but didn't beat fleet)
5. **Cosine Similarity Chain Reconstruction** — Build sequential affinity matrix S[a][b] = how well block_b follows block_a. Nearest-neighbor chain. MSE 0.744 (worse than fleet, but found break points).
6. **Spectral Radius Ordering** — Sort blocks by Jacobian eigenvalue magnitude. MSE 0.462. Confirmed gentle-first is correct.
7. **Data-Driven Pairing Analysis** — Mutual best pairing via Jacobian norms + Hungarian assignment. MSE 0.4286 with locked pairings. Proved pairings are position-dependent.

### Completed (no improvement)
8. **Jacobian Chain Conditioning** (Jr #763) — Full 48x48 Jacobian matrices, condition-number ATSP. MSE 0.252. Condition number was wrong cost function.
9. **Find the Lady / Cosine Weight Pairing** (Jr #764) — 4 methods: cosine, transpose, SVD, activation correlation. **0/48 matches**. Weight statistics don't predict pairing.
10. **Beam Search** (Jr #765) — Width-50 paired/independent beam search. MSE 0.465. Can't compete building from scratch.

### Critical Discovery: Gradient MSE Pairing (Jr #766)
11. **MSE-Based Greedy Pairing** — 4 data-driven methods using actual forward passes:

| Method | Pool Matches | Mutual Best | SA with Fixed Pairs |
|--------|-------------|-------------|---------------------|
| Gradient MSE (through final layer) | **19/48** | **32/48** | 0.428 |
| Direction Alignment | 10/48 | 9/48 | 0.564 |
| Residual Norm | 2/48 | 5/48 | 0.723 |
| Bias Norm | 0/48 | 1/48 | ~0.9 |

**Key finding**: Gradient MSE (single-block forward through final layer) is the strongest pairing signal. 32/48 mutual best means the majority of pairs can be identified from single-block analysis. But fixing ALL 48 pairs (including 16 wrong ones) yields 0.428 — the wrong pairs are too toxic.

### Visual Analysis (Jr #768) — Pool Agreement Discovery
14. **5 Matplotlib Visualizations** revealed key insight:
- **Cost Matrix Heatmap**: Uniform 0.66-0.82, narrow margins. 23 mutual best pairs do NOT form diagonal — pairing isn't sequential.
- **Pool Agreement (KEY FINDING)**: Positions 0-1 and 35-47 have 80-100% pairing agreement across top-20 solutions. **Positions 12-22 have only 35-50% agreement** — this is the "uncertain zone."
- **Convergence**: Rapid 0.034→0.030 in 30min, then flat 1.25hrs. Target 0.0145 is 2x gap.
- **Activation Fingerprints (PCA)**: Inp/out form separate clusters. No pairing signal in activation space.
- **Weight Norms**: Inp tight (6.1-7.2), out spread (3.3-6.3). Bias norms separate types cleanly.

### Hidden Patterns Analysis (30+ tests)
15. **No steganographic content found**:
- No ASCII in biases, diagonals, weight values at any scale
- 6 pieces with spatial autocorrelation > 0.1: pieces 27, 43, 65, 69, 85 (final), 93
- Bias norms cleanly separate types: ALL inp 0.85-1.59, ALL out 0.15-0.36
- Spearman r=-0.20 (inp weight×bias, NS), r=0.31 (out, p=0.03, mild)
- Puzzle is pure mathematics, not steganography

### BREAKTHROUGH: Trace-Based Pairing (Inception Analysis)
17. **trace(W_out @ W_inp)** is the strongest pairing signal found:
- Correct pairings: trace mean = **-6.98** (strongly negative)
- Random pairings: trace mean = **-0.24** (near zero)
- **Hungarian optimal: 38/48 pairs match pool best** (vs gradient MSE's 19/48)
- This is purely structural (no training data needed)
- Pool trace sum: -334.9 vs Hungarian optimal: -421.4
- Positions 36-47 have near-zero traces — weaker pairing structure in later layers

18. **Fixed Point Discovery**: Network converges to fixed point by block ~5. Divergence drops from 17.4 at block 0 to 0.0001 at block 5 to zero by block 10. Always outputs -0.006986. Puzzle is about structure, not function approximation.

19. **Cycle Structure**: Inp sigma cycles [1,3,7,11,26], out sigma cycles [1,2,5,17,23] — contain 7 consecutive primes (2,3,5,7,11,17,23). Coincidence or design?

### In Progress / Queued
12. **Constrained SA with Anchored Pairs** (Jr #767) — 23 mutual-best pairs anchored. Running but re-pairing moves too destructive.
13. **Middle Zone Surgery v2** (Jr #769, TPM-fixed) — Locks positions with >75% agreement, targets uncertain zone. Re-pairing REMOVED, T lowered to 0.01. Running on redfin.
20. **Trace Pairing Solver** (Jr #770, queued) — Hungarian trace pairing (38/48) + ordering-only SA (48! space). Same approach as public 0.0145 solver but with better pairing signal. Includes hybrid mode.
16. **SA Move-Type Upgrade** (Jr #761, in_progress) — Add segment reversal and independent inp/out swaps.

### Critical Discovery: "Jacobian Ordering" Was a Red Herring
Deep research into the public 0.0145 solver (ShubhamRasal on HuggingFace) revealed:
- The solver used **plain SA** — same as our fleet
- They solved pairing first ("the easy part"), getting to MSE 0.16
- Then SA'd only the ordering (48! space vs our (48!)^2)
- No Jacobian techniques were used in the actual solver
- No one has publicly solved the puzzle (SHA256 match not achieved)

## Key Findings

### Break Points (Critical)
Cosine similarity between consecutive residual directions found 4 positions where blocks are anti-correlated:
- **pos 17→18**: cos_sim = -0.276 (overlaps LOO harmful block 17)
- **pos 29→30**: cos_sim = -0.409
- **pos 30→31**: cos_sim = -0.451 (worst)
- **pos 45→46**: cos_sim = -0.241 (overlaps LOO harmful block 46)

Two independent methods (LOO + cosine) pointing at same spots = high confidence these are real misplacements.

### Pairing Is Position-Dependent (Partially)
Single-block pairing gets 19/48 right — the other 29 depend on context (what blocks came before). However, 32/48 mutual best matches means the SIGNAL is there even if fixed-pairing SA can't exploit it. The constrained approach (Jr #767) anchors the confident pairs and lets SA find the rest.

### Gentle-First Ordering
Spectral analysis confirmed: blocks with smaller Jacobian norms (gentle reshaping) should go first, heavy transformers go last. Fleet's SA naturally discovered this.

### Pool Monoculture Risk
46/48 positions reached 10/10 consensus before Jacobian/LOO injection. Diversity injection was critical — MSE dropped from 0.1429 to 0.0762 after seeding. Fleet now at 0.0302 and stale 1hr+ — observer shifted to 60% random.

### Weight Statistics Don't Predict Pairing
Four weight-based methods (cosine, SVD, transpose, activation correlation) ALL got 0/48 matches. Forward-pass data (gradient MSE) is the only reliable signal. This eliminated an entire class of approaches.

### Pool Agreement Zone Map (from Visual Analysis)

| Zone | Positions | Agreement | Strategy |
|------|-----------|-----------|----------|
| **Locked** | 0-1, 35-47 | 80-100% | Fixed from pool best |
| **Mixed** | 2-11, 23-34 | 60-75% | Occasional perturbation |
| **Uncertain** | 12-22 | 35-50% | Targeted SA (Middle Zone Surgery) |

This is where the remaining MSE gap lives. The fleet agrees on the ends, disagrees in the middle.

## BREAKTHROUGH RESULTS (Feb 15 2026)

**Trace pairing + ordering-only SA achieved:**
- **Pool best: MSE 0.004576** (sasass M1 Max + bmasass M4 Max hybrid, both found independently)
- All 6 nodes sub-0.01 by run 8-10
- Public solver benchmark: 0.0145
- Previous pool best (old SA): 0.030161
- **6.6x improvement** over previous pool best, **3.2x better than public solver**

**Why it worked**: The trace pairing (38/48 agreement with pool) corrected 10 positions where the pool had WRONG pairings (traces near zero). With correct pairings locked, ordering-only SA (48! space) converges rapidly because the search space is manageable and the pairing errors aren't poisoning the landscape.

**Fractal basin model confirmed**: Each improvement required a qualitatively different approach:
- Basin 1 (0.45→0.08): Jacobian seeding
- Basin 2 (0.08→0.030): Break-point surgery
- Basin 3 (0.030→0.006): Trace algebraic pairing + ordering SA

**MSE trajectory (bmasass run 0)**:
- Step 0: 0.741 (random ordering)
- Step 80K: 0.107
- Step 120K: 0.025 (below pool best!)
- Step 160K: 0.015 (matching public solver)
- Step 200K: **0.006721** (2.2x better than public)

**SHA256 hash**: `a4a807b4...e537` — does NOT match target `093be1...9c4`. Puzzle not fully solved. MSE 0.006721 means ordering/pairing still has errors.

**DB save bugs (3 rounds of fixes)**:
1. `numpy.int64` type error in psycopg2 — Fix: `[int(x) for x in sigma]`
2. Wrong column name `perm_hash` — Fix: use `hash` (actual column)
3. Missing `hash_match` column — Fix: include in INSERT with `False`
- Lost 2+ runs of breakthrough results before all 3 bugs were fixed

## Chipset Benchmarking (Trace Solver Workload)

Uniform workload: 200K SA iterations, 1000 data samples, same algorithm. Pure CPU-bound (no GPU).

| Node | Chipset | Arch | Sec/Run | Steps/sec | Best MSE | Relative Speed |
|------|---------|------|---------|-----------|----------|----------------|
| bmasass | M4 Max 128GB | ARM64 | 628s | 318 | 0.004576 | 1.0x (fastest) |
| sasass | M1 Max 64GB | ARM64 | ~1100s | ~182 | 0.004576 | 0.57x |
| sasass2 | M1 Max 64GB | ARM64 | ~1100s | ~182 | 0.004655 | 0.57x |
| bluefin | i9-13900K | x86-64 | 1518s | 132 | 0.004779 | 0.42x |
| redfin | Threadripper 7960X | x86-64 | 1645s | 122 | 0.004848 | 0.38x |
| greenfin | i7-12700K | x86-64 | 1779s | 112 | 0.005344 | 0.35x |

**Key insights**:
- **Apple Silicon dominates CPU-bound Python**: M4 Max is 2.4x-2.8x faster than Intel/AMD per-thread
- **M4 Max vs M1 Max**: 1.75x improvement per generation
- **Threadripper slower than i9**: Despite more cores, single-thread SA doesn't benefit from core count. Per-thread perf matters.
- **Hybrid mode works**: bmasass reached 0.004576 via hybrid pairing (trace + pool for ambiguous positions)
- **All 6 nodes converged to similar MSE range (0.0046-0.0053)**: Trace pairing provides consistent advantage regardless of hardware
- **Federation implication**: CPU-bound optimization tasks should be routed to Mac nodes. Intel/AMD nodes better for GPU inference and database workloads.

## Remaining Gap (Updated)

MSE 0.004576 vs SHA256 solution (unknown MSE, likely ~0). SHA256 hash `a4a807b4...` does NOT match target `093be1...9c4`.

The trace pairing (38/48) plus 20-run SA convergence has pushed far past the public solver, but the remaining 10 pairings may still be wrong. Further improvement paths:
1. **Hybrid mode working** — bmasass hit 0.004576 with hybrid pairing
2. 20-run convergence per node continues (120 total runs across fleet)
3. Investigate positions 36-47 (near-zero traces = degenerate pairing signal)
4. Try all 2^10 = 1024 combinations of the 10 uncertain pairs
5. Gradient-based local refinement of the best ordering

## Bug/Lesson: np.math.factorial Removed in NumPy 2.x

`np.math.factorial` was removed in newer numpy. Fix: `import math; math.factorial(n)`. Hit in break_point_surgery.py.

## Bug/Lesson: SSH Commands Need Absolute Paths

SSH commands without `cd` land in home directory. Always use absolute paths: `ssh node "python3 /full/path/script.py"`. Made this error 5+ times before realizing.

## Bug/Lesson: System Python vs Venv Per Node

- **redfin**: Must use `/ganuda/home/dereadi/cherokee_venv/bin/python3` (system python3 lacks torch)
- **bluefin/greenfin**: System `python3` has torch (cherokee_venv doesn't exist)
- **Mac nodes**: System `python3` (via Homebrew/Xcode)

## Bug/Lesson: Mac Nodes Use /Users/Shared/ganuda

macOS has read-only root filesystem. `/ganuda/` fails with "Read-only file system". Use `/Users/Shared/ganuda/experiments/jane-street/track2_permutation/`. Also `mkdir -p logs/` needed before nohup.

## Bug/Lesson: bmasass Hostname Resolution

`ssh bmasass` fails intermittently from redfin. Use IP: `ssh 192.168.132.21`.

## Bug/Lesson: Workers Exit Normally After --runs

Workers run `--runs 20` and exit cleanly after ~4 hours. They're not crashing — they completed their work. Need periodic relaunch.

## Bug/Lesson: Piece Classification

Initially classified (48,96) as inp and (96,48) as out. **Correct**: (96,48) = inp (projects 48→96 via `x @ W.T`), (48,96) = out (projects 96→48). Trace matrix multiplication shapes to verify.

## Bug/Lesson: System Python vs Venv

Redfin system python3 lacks torch. Must use `/ganuda/home/dereadi/cherokee_venv/bin/python3` (found in `launch_distributed.sh` line 16).

## Bug/Lesson: Python Output Buffering

`nohup python3 script.py > log &` produces empty logs due to buffering. Must use `PYTHONUNBUFFERED=1 python3 -u script.py`.

## Files

- SA worker: `/ganuda/experiments/jane-street/track2_permutation/sa_worker.py`
- Observer: `/ganuda/experiments/jane-street/track2_permutation/puzzle_observer.py`
- Jacobian seeder: `/ganuda/experiments/jane-street/track2_permutation/jacobian_seeder.py`
- LOO seeder: `/ganuda/experiments/jane-street/track2_permutation/loo_seed_injector.py`
- Break surgery: `/ganuda/experiments/jane-street/track2_permutation/break_point_surgery.py` (Jr #762)
- Fleet launcher: `/ganuda/experiments/jane-street/track2_permutation/launch_distributed.sh`
- MSE greedy pairing: `/ganuda/experiments/jane-street/track2_permutation/mse_greedy_pairing.py` (Jr #766)
- Constrained SA: `/ganuda/experiments/jane-street/track2_permutation/constrained_sa.py` (Jr #767)
- Jacobian chain: `/ganuda/experiments/jane-street/track2_permutation/jacobian_chain.py` (Jr #763)
- Weight pairing: `/ganuda/experiments/jane-street/track2_permutation/weight_pairing.py` (Jr #764)
- Beam search: `/ganuda/experiments/jane-street/track2_permutation/beam_search.py` (Jr #765)
- Visual analysis: `/ganuda/experiments/jane-street/track2_permutation/visual_analysis.py` (Jr #768)
- Middle zone surgery: `/ganuda/experiments/jane-street/track2_permutation/middle_zone_surgery.py` (Jr #769)
- **Trace pairing solver**: `/ganuda/experiments/jane-street/track2_permutation/trace_pairing_solver.py` (Jr #770, TPM fixed 3x)
- Trace solver (Mac): `/ganuda/experiments/jane-street/track2_permutation/trace_pairing_solver_mac.py`
- Visual outputs: `/ganuda/experiments/jane-street/track2_permutation/results/visual/*.png`
- Results: `/ganuda/experiments/jane-street/track2_permutation/results/`

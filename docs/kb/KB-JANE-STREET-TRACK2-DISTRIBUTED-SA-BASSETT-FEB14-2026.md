# KB: Jane Street Track 2 — Distributed SA + Bassett Energy Analysis

**Created**: Feb 14, 2026
**Thermal**: Puzzle competition
**Status**: IN PROGRESS
**Prize**: $50K | **Deadline**: April 1, 2026
**44 people have solved it**

## Problem Statement

Reassemble 97 neural network pieces (48 inp layers 96x48, 48 out layers 48x96, 1 last layer 1x48) into the correct permutation. Model: `Block.forward(x) = x + out(relu(inp(x)))`. Two permutations needed: `inp_sigma[48]` and `out_sigma[48]`. Search space: (48!)^2 ≈ 10^122.

SHA256 target hash: `093be1cf2d24094db903cbc3e8d33d306ebca66143e3c2d4f3bdf0fd53b6ab4a5`

Puzzle pieces: `/ganuda/experiments/jane-street/track2_permutation/pieces/`

## Architecture

### Distributed Fleet (34 CPU workers)
- **redfin** (4 workers): 192.168.132.223
- **bluefin** (8 workers): 192.168.132.222
- **greenfin** (8 workers): 192.168.132.224
- **sasass** (4 workers): 192.168.132.241
- **sasass2** (4 workers): 192.168.132.242
- **bmasass** (6 workers): 192.168.132.21 (M4 Max 128GB, added 21:13 CST)

### PostgreSQL Shared Pool
- Table: `js_puzzle_pool` on bluefin (zammad_production)
- Columns: id, worker, full_mse, inp_sigma, out_sigma, permutation, hash, hash_match, created_at
- Quality-gated writes: only solutions better than current pool best are stored
- Table: `js_puzzle_config` for observer→worker feedback

### SA Worker (sa_worker.py)
Key strategies (Banks):
1. **Bank 1**: Hill climbing endgame (last 10% of iterations)
2. **Bank 2**: Pool seeding (start from perturbed best-known solution)
3. **Bank 3**: Larger moves (3-opt, segment reversal)
4. **Bank 4**: LNS (Large Neighborhood Search) — pick 4-6 positions, try ALL permutations (120-720 evals per move)
5. **Bank 5**: Bassett-biased position selection — 30% of moves target suspicious positions from energy analysis
6. **Bank 6**: Slow cooling (--slow flag: 250K iters, T_start=10, T_end=0.0001)

### Puzzle Observer (puzzle_observer.py)
3-layer metacognitive monitor running on redfin:
1. Observe fleet: track MSE improvements, convergence, per-node activity
2. Observe self: monitor stagnation detection accuracy
3. Take action: adjust seeding ratios, publish suspicious positions to js_puzzle_config

## Bassett Energy Analysis

Inspired by Dani Bassett's network neuroscience work on energy consumption of brain activity patterns. For each block position, compute:
- **Residual ratio**: ||f(x)|| / ||x|| — how much the block amplifies the signal
- **Cosine similarity**: cos(f(x), x) — does the block refine (positive) or transform (negative)?
- **Skip-block MSE delta**: MSE_without - MSE_with — how essential is this block?

### Key Finding: Cosine Transition Zone
Positions 0-8 have **negative cosine** (transformation phase), positions 9+ have **positive** (refinement phase). Blocks at the transition boundary (pos 8-9) were most likely misplaced.

### Round 1 Results (MSE 0.258892 → 0.253351)
- Found swap pos 8↔9 at cosine transition zone
- Hill climbing cascaded: 13 total improvements
- Trajectory: 0.258892 → 0.258119 → 0.256503 → 0.254708 → 0.253351
- **One structural insight produced more improvement than thousands of random SA iterations**

### Round 2 Results (MSE 0.253351)
- Found 9 suspicious positions: [10, 13, 14, 29, 33, 34, 36, 41, 47]
- Pos 47: extreme outlier (ratio=0.666, cos=-0.611, delta=+0.538) — highly essential, likely correctly placed
- Pos 13: neg_cos_late (-0.067), high ratio (0.366) — structural mismatch?
- **0 improvements from targeted swaps** — basin is harder, pairwise swaps insufficient
- Implication: remaining error is from **group misplacements**, not individual blocks

## Lessons Learned

1. **Convergent topology pattern**: Shared-Memory Star with Quality-Gated Writes works for distributed search — same pattern as thermal memory system
2. **Structural analysis > brute force**: One Bassett insight = 13 improvements that random SA would have taken hours to find
3. **SSH via FreeIPA workaround**: `ssh -o 'ProxyCommand=nc -w 10 %h %p'` bypasses sss_ssh_knownhostsproxy timeout (root cause: silverfin IPA only reachable via greenfin bridge)
4. **psycopg2 JSONB returns native Python types**: Don't `json.loads()` on already-parsed JSONB values
5. **Python output buffering with nohup**: Use `PYTHONUNBUFFERED=1` for daemon output visibility
6. **pgrep -acf incompatible on macOS**: Use `ps aux | grep | wc -l` instead

## MSE Trajectory
```
0.321  initial fleet convergence (v2 workers)
0.289  greenfin_w2 breakthrough
0.265  sasass_w3 (LNS/slow cooling)
0.259  sasass2_w1
0.258  bassett_targeted (swap pos 8↔9)
0.253  bassett_hillclimb (13 cascaded improvements)
```

## Bayesian Placement Analysis (Brunton lens, Long Man Cycle 3)

Inspired by Steve Brunton's Bayesian inference lecture. Built a posterior probability distribution
P(block i at position j) from the pool of solutions, weighted by Boltzmann: w(s) = exp(-β × MSE(s)).

### Key Findings
- **38/48 blocks** confidently placed (>50% probability) — pool converged on 79% of puzzle
- **Best solution vs MAP: 85% agreement** — 7 blocks disagree at 3 swap-pair locations
- **Hungarian algorithm MAP** (globally optimal Bayesian assignment): 6 differences from best
- **MAP increases MSE**: +0.004 worse. The best solution is slightly anti-consensus but better.
- **Implication**: the pool has converged to a basin. Improvement requires larger structural moves.

### Bayesian-to-SA Pipeline
1. Build posterior from pool solutions (Boltzmann-weighted)
2. Hungarian algorithm → MAP solution
3. Compare MAP vs best → identify low-confidence positions
4. Store low-confidence positions in js_puzzle_config
5. Workers use biased position selection toward uncertain blocks

## Massive Breakthrough (Long Man Cycle 3 result)

**0.321 → 0.253 (Bassett) → 0.189 (fleet breakthrough)**

The v4 workers with Bassett-biased LNS found a fundamentally different solution:
- 46/48 inp blocks and 45/48 out blocks changed positions vs 0.253
- Peak cascade MSE: 0.88 (was 1.91 at 0.253) — 54% lower peak
- Monotonicity violations: 40% (improving but still high)
- Position 47: inp=21, out=46, correction=-0.403 (still doing heavy lifting)

## Bank 7: Anchor Mode

Added `--anchor` flag to sa_worker.py. Freezes specified positions, only searches moveable ones.
Example: `--anchor 0-10,44-47` freezes bookends, searches middle (33 positions).
Reduces search space from 48! to 33! (10^30 factor reduction).

## Analytical Approaches Tested (Long Man Cycle 4)

### Approaches That FAILED
1. **Pairwise TSP** (MRF model): 2-block compatibility matrix → greedy + 2-opt TSP. MSE=7.96. Fails because pairwise interaction doesn't capture cascading 48-block dynamics.
2. **Greedy Chain Building**: At each position, choose the (inp,out) pair minimizing immediate MSE. MSE=1.99. Too myopic — can't plan for later positions.
3. **Weight Structure Analysis**: Frobenius norms, spectral norms, bias norms, effective rank of weight matrices vs position. **ZERO signal** (all correlations p > 0.23). Static weights don't predict position.
4. **Weight Adjacency Matrix**: Frobenius norm of W_out[i].T @ W_inp[j].T for all pairs. Z-score = 0.01 between best solution path and random. **No discriminative power**.

### Key Insight
The puzzle can ONLY be solved through data-flow evaluation (running forward passes with training data). Static weight analysis has no signal. The fleet's stochastic approach with intelligent seeding IS the right strategy.

### Gumbel-Sinkhorn Gradient Approach (Long Man Cycle 5) — FAILED
- **Approach**: Differentiable relaxation of permutations via Sinkhorn operator. Replace hard permutation matrices with soft doubly-stochastic matrices, run gradient descent (Adam) on MSE.
- **Result from random init**: Hard MSE 11.75 (80x worse than fleet). Soft MSE converges to ~0.17 but hard extraction via Hungarian algorithm fails catastrophically.
- **Result seeded from pool best (0.1476)**: Soft MSE drops to 0.094 (below hard baseline!) but ALL extracted hard permutations are worse. Delta = 0.000000.
- **Root cause**: With 48 cascading residual blocks + ReLU, the soft weighted-average of weights is NOT a good proxy for the hard discrete forward pass. The soft relaxation "cheats" by blending nearby blocks in ways that don't correspond to any valid permutation. Errors compound through the cascade.
- **Conclusion**: First-order gradient methods via Sinkhorn relaxation DO NOT work for this class of puzzle. Zero-order methods (SA) remain the only viable approach.
- **Script**: `/ganuda/experiments/jane-street/track2_permutation/sinkhorn_solver.py`
- **Reference**: Mena et al. "Learning Latent Permutations with Gumbel-Sinkhorn Networks" (2018)

### Reference Papers
- [Gumbel-Sinkhorn Networks](https://arxiv.org/abs/1802.08665) — differentiable permutation relaxation. Works for jigsaw puzzles (independent pieces) but fails for cascading residual networks.
- [Find the Lady: Permutation and Re-Synchronization of DNNs](https://arxiv.org/abs/2312.14182) — neuron-level permutation recovery via cosine similarity. Different problem (within-layer, not cross-layer ordering).
- [Neural Combinatorial Optimization](https://www.sciencedirect.com/science/article/pii/S0305054825001303) — RL-based approach to permutation problems.

## MSE Trajectory (Full)
```
0.321  12:25  greenfin_w0 (initial convergence)
0.289  12:33  greenfin_w2
0.265  12:53  sasass_w3 (LNS breakthrough)
0.259  13:11  sasass2_w1
0.258  13:13  bassett_targeted (swap pos 8↔9)
0.253  13:25  bassett_hillclimb (13 cascaded improvements)
0.245  13:44  sasass2_w2
0.231  13:44  greenfin_w3
0.200  13:50  sasass_w0
0.189  14:01  sasass2_w2 (fundamentally new basin)
0.162  ~15:00  fleet convergence
0.156  15:27  sasass2_w0
0.153  19:06  redfin_w0
0.152  21:37  bmasass_w4 (M4 Max joins fleet)
0.148  21:54  bluefin_w0 (current best, 22:17 CST)
```

## Fleet Watchdog
Auto-relaunch daemon checking every 5 minutes across all 6 nodes.
Script: `/ganuda/experiments/jane-street/track2_permutation/fleet_watchdog.sh`
Log: `/ganuda/experiments/jane-street/track2_permutation/logs/fleet_watchdog.log`

## Files
- Worker: `/ganuda/experiments/jane-street/track2_permutation/sa_worker.py`
- Observer: `/ganuda/experiments/jane-street/track2_permutation/puzzle_observer.py`
- Launcher: `/ganuda/experiments/jane-street/track2_permutation/launch_local.sh`
- Pieces: `/ganuda/experiments/jane-street/track2_permutation/pieces/piece_*.pth`

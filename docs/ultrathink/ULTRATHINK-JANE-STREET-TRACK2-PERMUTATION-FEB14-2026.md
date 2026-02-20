# ULTRATHINK: Jane Street Track 2 — Dropped Neural Net (Permutation Puzzle)

**Date**: February 14, 2026
**Kanban**: #1780 (Track 2)
**Time Cap**: 10-15% (council-approved)
**Sandbox**: /ganuda/experiments/jane-street/track2_permutation/
**Deadline**: April 1, 2026

---

## DISCOVER

### Puzzle Specification

"I dropped an extremely valuable trading model and it fell apart into linear layers!"

- **97 pieces** total: 96 residual `Block` modules + 1 `LastLayer` module
- **Block architecture**: `residual + Linear(in_dim, hidden_dim) → ReLU → Linear(hidden_dim, in_dim)`
- **LastLayer**: `Linear(in_dim, out_dim)` — simple projection, no residual
- **Key constraint**: All Blocks have the **same in_dim** (residual connection forces it). Hidden dims vary.
- **Task**: Find the permutation of piece indices (0-96) that reconstructs the original model
- **Verification**: SHA256 of comma-separated permutation = `093be1cf2d24094db903cbc3e8d33d306ebca49c6accaa264e44b0b675e7d9c4`
- **Data**: `historical_data.csv` (5.58 MB) — input/output pairs from the original model
- **44 solvers** have solved it

### Why Shape Matching Won't Work

All 96 Blocks have identical in_dim/out_dim (residual connection). You can't chain them by
dimension compatibility like you would with non-residual layers. The LastLayer is the only
piece with a different output dimension — it clearly goes last. The challenge is ordering
the 96 blocks.

### What Signal DO We Use?

The key insight: **the historical data provides input→output pairs from the correctly-ordered model**.
If we order the blocks correctly and run the inputs through, the outputs should match.

This is a **combinatorial optimization** problem:
- Search space: 96! ≈ 10^149 (brute force impossible)
- But we can evaluate quality: MSE between model output and historical output
- And we can exploit structure: blocks are residual, so each block makes a small additive correction

### Research: Proven Approaches

1. **Greedy Chain Building** (most practical)
   - Start with random input from historical data
   - For each position, try all remaining blocks
   - Pick the block whose output, when fed through the rest of the chain, minimizes loss
   - O(96² × data_size) — feasible on CPU

2. **Pairwise Activation Correlation** (Git Re-Basin style)
   - For each pair (i, j), measure how well block i's output feeds into block j
   - Build a directed graph of "compatibility scores"
   - Find the Hamiltonian path through the graph
   - O(96² × data_size) — feasible

3. **Loss-Based Local Search** (refinement)
   - Start with greedy solution
   - Repeatedly swap adjacent blocks, keep if loss improves
   - Simulated annealing or hill climbing
   - Good for polishing a near-correct solution

4. **Gradient-Based Ordering** (advanced)
   - Differentiable permutation via Gumbel-Sinkhorn
   - Train a permutation matrix to minimize MSE on historical data
   - Elegant but may get stuck in local optima

### Recommended Strategy

**Phase 1**: Download data + pieces, analyze dimensions
**Phase 2**: Greedy chain building — forward pass each candidate block, pick best by MSE
**Phase 3**: Local search refinement — swap-based optimization
**Phase 4**: Verify with SHA256 hash and submit

---

## DELIBERATE

### Turtle (7GEN)
The puzzle exercises sequence optimization and model reconstruction — skills directly
applicable to our own model assembly and checkpoint management. Educational value is clear.

### Crawdad (Security)
All work sandboxed in `/ganuda/experiments/jane-street/`. No external model weights in
production. No GPU impact (CPU-only, residual blocks are small).

### Gecko (Performance)
96 blocks × 96 candidates × N data points per evaluation step. With batch processing
and torch.no_grad(), this should run in minutes on CPU. No GPU needed.

### Eagle Eye (Visibility)
Results logged to `/ganuda/experiments/jane-street/track2_permutation/results/`.
MSE at each step logged for debugging.

### Raven (Strategy)
44 solvers means it's tractable. The greedy approach is the standard method for these
puzzles. Time cap is the main constraint — we should be efficient.

### Spider (Integration)
Builds on Track 1 experience. Same puzzle ecosystem, same submission email.

### Peace Chief (Consensus)
PROCEED — within time cap, educational value established by Track 1.

---

## ADAPT → BUILD

### Phase 1: Data Download + Piece Analysis (2 SP)

**Goal**: Download all puzzle pieces and historical data, analyze dimensions and structure.

**Steps**:
1. Download `historical_data_and_pieces.zip` from HuggingFace
2. Extract pieces (97 .pt files) and historical_data.csv
3. Load all pieces, classify as Block or LastLayer
4. Analyze: input dim, hidden dims, output dim, weight statistics
5. Save analysis to results/piece_analysis.json

**Output**: Downloaded data + dimension analysis report

### Phase 2: Greedy Chain Builder (5 SP)

**Goal**: Implement greedy ordering algorithm using historical data as ground truth.

**Algorithm**:
1. Load historical_data.csv (input features → target outputs)
2. Identify the LastLayer (only piece with different out_dim) — it goes at position 96
3. For the remaining 96 blocks, greedily build the chain:
   a. Start with the raw input features
   b. For each position (0 to 95):
      - Try each remaining block at this position
      - Forward pass through this block + all remaining blocks (in current best order) + LastLayer
      - Compute MSE against historical targets
      - Pick the block that gives lowest MSE
   c. Record the chosen block and update the chain
4. Save the resulting permutation

**Optimization**: Use batched forward passes with `torch.no_grad()` for speed.

**Fallback**: If full forward pass through remaining chain is too slow, use a
**local greedy** approach: pick the block whose output activations have the smallest
norm change (residual blocks should make small corrections, so the "right next block"
is the one that makes the most coherent small correction for the current activation state).

### Phase 3: Local Search Refinement (3 SP)

**Goal**: Polish the greedy solution using swap-based local search.

**Algorithm**:
1. Start with the greedy permutation from Phase 2
2. Compute baseline MSE on historical data
3. For N iterations (e.g., 10,000):
   a. Pick two random positions (i, j) where i < j
   b. Swap blocks at positions i and j
   c. Forward pass full model, compute MSE
   d. If MSE improved, keep the swap; otherwise revert
4. Optional: simulated annealing (accept worse swaps with decreasing probability)
5. Save best permutation found

**Verification**: After optimization, check SHA256 hash. If it matches, we're done.

### Phase 4: Hash Verification + Submission (1 SP)

**Goal**: Verify the solution and create Gmail draft.

**Steps**:
1. Compute SHA256 of the best permutation string
2. Compare against `093be1cf2d24094db903cbc3e8d33d306ebca49c6accaa264e44b0b675e7d9c4`
3. If match: create Gmail draft to archaeology@janestreet.com
4. If no match: log the best MSE achieved and the permutation for manual analysis

---

## REVIEW

### Validation Checklist

- [ ] All code in `/ganuda/experiments/jane-street/track2_permutation/` (sandboxed)
- [ ] No GPU usage (CPU only, torch.no_grad())
- [ ] Historical data downloaded and parsed correctly
- [ ] Greedy algorithm produces a valid permutation (all 97 indices, each used exactly once)
- [ ] MSE decreasing at each greedy step (logged)
- [ ] Local search improves on greedy solution
- [ ] SHA256 verification attempted
- [ ] Results saved to results/ directory
- [ ] Time investment within 10-15% cap

### Risk Assessment

- **LOW**: CPU-only, sandboxed, no production impact
- **MEDIUM**: May not find correct solution (96! search space)
- **MITIGATION**: Greedy + local search is the standard approach for this puzzle type.
  44 solvers suggests it's tractable with the right algorithm.

### File Inventory

| File | Purpose |
|------|---------|
| `download_data.py` | Phase 1: Download + extract HuggingFace data |
| `analyze_pieces.py` | Phase 1: Dimension analysis + piece classification |
| `greedy_solver.py` | Phase 2: Greedy chain building algorithm |
| `local_search.py` | Phase 3: Swap-based refinement |
| `verify_and_submit.py` | Phase 4: SHA256 check + Gmail draft |

# Jr Instruction: Jane Street Track 2 — Phase 2: Greedy Chain Builder

**Ticket**: #1780 (Track 2)
**Priority**: 3
**Story Points**: 5
**Assigned**: Software Engineer Jr.
**Sandbox**: /ganuda/experiments/jane-street/track2_permutation/
**Depends on**: Phase 1 (data download + analysis)

## Context

97 neural network pieces (96 residual Blocks + 1 LastLayer) need to be reordered.
Historical data provides input→output pairs from the correctly-ordered model.
All Blocks have the same in_dim (residual), so we can't order by shape.
We use the historical data as ground truth — the correct ordering minimizes MSE.

## Step 1: Create greedy solver

Create `/ganuda/experiments/jane-street/track2_permutation/greedy_solver.py`

```python
#!/usr/bin/env python3
"""
Jane Street Track 2: Greedy chain builder for block ordering.

Strategy: Build the permutation greedily from left to right.
At each position, try all remaining blocks and pick the one
whose output, when fed through the rest of the pipeline, gives
lowest MSE against historical targets.

Since full forward pass through all remaining blocks is expensive,
we use a simpler heuristic: pick the block that produces activations
closest to what the next block in a "reference chain" expects.

Fallback: Use activation norm smoothness — the correct chain should
produce smoothly-evolving activations (residual blocks make small
corrections).
"""
import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import json
import hashlib
import time
import sys
from pathlib import Path

EXPERIMENT_DIR = Path(__file__).parent
PIECES_DIR = EXPERIMENT_DIR / "pieces"
RESULTS_DIR = EXPERIMENT_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

SOLUTION_HASH = "093be1cf2d24094db903cbc3e8d33d306ebca49c6accaa264e44b0b675e7d9c4"


class Block(nn.Module):
    def __init__(self, in_dim, hidden_dim):
        super().__init__()
        self.inp = nn.Linear(in_dim, hidden_dim)
        self.activation = nn.ReLU()
        self.out = nn.Linear(hidden_dim, in_dim)

    def forward(self, x):
        residual = x
        x = self.inp(x)
        x = self.activation(x)
        x = self.out(x)
        return residual + x


class LastLayer(nn.Module):
    def __init__(self, in_dim, out_dim):
        super().__init__()
        self.layer = nn.Linear(in_dim, out_dim)

    def forward(self, x):
        return self.layer(x)


def load_pieces():
    """Load all pieces, return blocks dict and last_layer info."""
    blocks = {}
    last_layer_idx = None
    last_layer = None

    for pt_file in sorted(PIECES_DIR.glob("*.pt")):
        idx = int(pt_file.stem.replace("piece_", ""))
        piece = torch.load(str(pt_file), weights_only=False, map_location='cpu')

        if hasattr(piece, 'layer'):
            last_layer_idx = idx
            last_layer = piece
        elif hasattr(piece, 'inp'):
            blocks[idx] = piece

    print(f"Loaded {len(blocks)} blocks, LastLayer = piece {last_layer_idx}")
    return blocks, last_layer_idx, last_layer


def load_historical_data():
    """Load historical data CSV, split into inputs and targets."""
    csv_path = EXPERIMENT_DIR / "historical_data.csv"
    df = pd.read_csv(csv_path)
    print(f"Historical data: {df.shape}")

    # Auto-detect input/output split
    # Convention: input columns are features, last column(s) are targets
    # We'll figure this out from the piece dimensions
    return df


def build_model(block_order, blocks, last_layer):
    """Assemble blocks in given order + last_layer into a sequential model."""
    layers = []
    for idx in block_order:
        layers.append(blocks[idx])
    layers.append(last_layer)
    return nn.Sequential(*layers)


def compute_mse(model, inputs, targets):
    """Forward pass and compute MSE."""
    with torch.no_grad():
        preds = model(inputs)
        mse = ((preds - targets) ** 2).mean().item()
    return mse


def greedy_solve(blocks, last_layer, inputs, targets, method="mse"):
    """
    Greedy chain builder.

    Methods:
    - "mse": At each position, try each remaining block, forward through
      remaining chain + LastLayer, pick lowest MSE. O(n² * data * n/2).
    - "activation_norm": Pick block that produces smallest activation
      change (residual blocks should make small corrections in order).
    - "pairwise": Precompute pairwise compatibility scores, then
      build chain greedily using best-next heuristic.
    """
    block_indices = list(blocks.keys())
    n = len(block_indices)
    remaining = set(block_indices)
    order = []

    print(f"\nGreedy solver ({method}) — {n} blocks to order")
    start_time = time.time()

    if method == "pairwise":
        return greedy_pairwise(blocks, last_layer, inputs, targets)

    # For each position in the chain
    for pos in range(n):
        best_idx = None
        best_score = float('inf')

        # Sample data for speed (use subset if dataset is large)
        sample_size = min(len(inputs), 500)
        sample_idx = torch.randperm(len(inputs))[:sample_size]
        x_sample = inputs[sample_idx]
        y_sample = targets[sample_idx]

        # Current state: forward pass through already-placed blocks
        x_current = x_sample.clone()
        for placed_idx in order:
            x_current = blocks[placed_idx](x_current)

        for candidate_idx in remaining:
            if method == "mse":
                # Forward through candidate + remaining (in arbitrary order) + LastLayer
                x_test = blocks[candidate_idx](x_current)
                # Simple: just candidate + LastLayer (ignore remaining blocks)
                # This approximates the full chain for early positions
                preds = last_layer(x_test)
                score = ((preds - y_sample) ** 2).mean().item()

            elif method == "activation_norm":
                # Pick the block that makes the smallest change to activations
                x_test = blocks[candidate_idx](x_current)
                # Residual blocks: output = input + f(input)
                # The correction f(input) should be small and coherent
                correction = x_test - x_current
                score = correction.norm(dim=1).mean().item()

            if score < best_score:
                best_score = score
                best_idx = candidate_idx

        order.append(best_idx)
        remaining.remove(best_idx)

        if pos % 10 == 0 or pos == n - 1:
            elapsed = time.time() - start_time
            print(f"  Position {pos:3d}/{n}: piece {best_idx:3d} (score={best_score:.6f}) [{elapsed:.1f}s]")

    elapsed = time.time() - start_time
    print(f"\nGreedy ordering complete in {elapsed:.1f}s")
    return order


def greedy_pairwise(blocks, last_layer, inputs, targets):
    """
    Pairwise compatibility approach:
    1. Compute compatibility score for every pair (i→j)
    2. Build chain greedily: start with best first block, always pick best next
    """
    block_indices = list(blocks.keys())
    n = len(block_indices)
    print(f"\nComputing pairwise compatibility matrix ({n}x{n})...")

    # Sample data
    sample_size = min(len(inputs), 200)
    sample_idx = torch.randperm(len(inputs))[:sample_size]
    x_sample = inputs[sample_idx]

    # Compute each block's output on raw input
    block_outputs = {}
    with torch.no_grad():
        for idx in block_indices:
            block_outputs[idx] = blocks[idx](x_sample)

    # Compatibility: how well does block_i's output work as input to block_j?
    # Measure: MSE between block_j(block_i(x)) and block_j(x) is NOT right.
    # Better: measure activation smoothness of the chain.
    # block_i → block_j: compute block_j(block_i(x)) and measure the
    # residual correction norm. Correct chains should have small, smooth corrections.

    compat = np.zeros((n, n))
    idx_to_pos = {idx: i for i, idx in enumerate(block_indices)}

    start = time.time()
    with torch.no_grad():
        for i, idx_i in enumerate(block_indices):
            out_i = block_outputs[idx_i]
            for j, idx_j in enumerate(block_indices):
                if i == j:
                    compat[i, j] = float('inf')
                    continue
                # How well does block_j process the output of block_i?
                out_ij = blocks[idx_j](out_i)
                correction = out_ij - out_i
                compat[i, j] = correction.norm(dim=1).mean().item()

            if i % 20 == 0:
                print(f"  Row {i}/{n} [{time.time() - start:.1f}s]")

    print(f"Pairwise matrix computed in {time.time() - start:.1f}s")

    # Save compatibility matrix
    np.save(str(RESULTS_DIR / "pairwise_compat.npy"), compat)

    # Greedy chain: find best starting block, then always pick best next
    # Try each starting block
    best_order = None
    best_total_score = float('inf')

    for start_idx in range(n):
        remaining = set(range(n))
        remaining.remove(start_idx)
        chain = [start_idx]
        total = 0

        current = start_idx
        for _ in range(n - 1):
            # Pick the neighbor with lowest compatibility score (smoothest transition)
            best_next = min(remaining, key=lambda j: compat[current, j])
            total += compat[current, best_next]
            chain.append(best_next)
            remaining.remove(best_next)
            current = best_next

        if total < best_total_score:
            best_total_score = total
            best_order = chain

    # Convert position indices back to piece indices
    order = [block_indices[pos] for pos in best_order]
    print(f"Best chain score: {best_total_score:.4f}")
    return order


def verify_solution(order, last_layer_idx):
    """Check if permutation matches solution hash."""
    # Full permutation: block order + last layer at end
    full_perm = order + [last_layer_idx]
    perm_str = ",".join(str(p) for p in full_perm)
    hash_val = hashlib.sha256(perm_str.encode()).hexdigest()
    matches = hash_val == SOLUTION_HASH
    print(f"\nPermutation (first 20): {full_perm[:20]}...")
    print(f"SHA256: {hash_val}")
    print(f"Expected: {SOLUTION_HASH}")
    print(f"MATCH: {matches}")
    return matches


def main():
    print("=" * 60)
    print("JANE STREET TRACK 2 — GREEDY SOLVER")
    print("Cherokee AI Federation — Sandboxed")
    print("=" * 60)

    # Load pieces
    blocks, last_layer_idx, last_layer = load_pieces()

    # Load data
    df = load_historical_data()

    # Parse analysis to determine input/output split
    analysis_path = RESULTS_DIR / "piece_analysis.json"
    if analysis_path.exists():
        with open(analysis_path) as f:
            analysis = json.load(f)
        in_dim = analysis["summary"]["block_in_dims"][0]
        out_dim = analysis["summary"]["last_layer_out_dim"]
        print(f"Model: {in_dim} -> [96 blocks] -> {out_dim}")
    else:
        # Infer from pieces
        sample_block = next(iter(blocks.values()))
        in_dim = sample_block.inp.in_features
        out_dim = last_layer.layer.out_features
        print(f"Model (inferred): {in_dim} -> [96 blocks] -> {out_dim}")

    # Split historical data into inputs and targets
    # Input features = first in_dim columns, targets = last out_dim columns
    data_tensor = torch.tensor(df.values, dtype=torch.float32)
    inputs = data_tensor[:, :in_dim]
    targets = data_tensor[:, -out_dim:]
    print(f"Inputs: {inputs.shape}, Targets: {targets.shape}")

    # Try multiple methods
    results = {}

    for method in ["pairwise", "activation_norm", "mse"]:
        print(f"\n{'='*40}")
        print(f"Method: {method}")
        print(f"{'='*40}")

        order = greedy_solve(blocks, last_layer, inputs, targets, method=method)

        # Evaluate full model MSE
        model = build_model(order, blocks, last_layer)
        mse = compute_mse(model, inputs[:1000], targets[:1000])
        print(f"Full model MSE ({method}): {mse:.6f}")

        # Check hash
        matched = verify_solution(order, last_layer_idx)

        results[method] = {
            "order": order,
            "mse": mse,
            "hash_match": matched,
        }

        if matched:
            print(f"\n*** SOLUTION FOUND with method '{method}'! ***")
            break

    # Save results
    # Convert orders for JSON serialization
    save_results = {}
    for method, r in results.items():
        save_results[method] = {
            "order": r["order"],
            "full_permutation": r["order"] + [last_layer_idx],
            "mse": r["mse"],
            "hash_match": r["hash_match"],
        }

    output_path = RESULTS_DIR / "greedy_results.json"
    with open(output_path, 'w') as f:
        json.dump(save_results, f, indent=2)
    print(f"\nResults saved to: {output_path}")

    # Find best
    best_method = min(results, key=lambda m: results[m]["mse"])
    print(f"\nBest method: {best_method} (MSE={results[best_method]['mse']:.6f})")
    print(f"Hash match: {results[best_method]['hash_match']}")


if __name__ == "__main__":
    main()
```

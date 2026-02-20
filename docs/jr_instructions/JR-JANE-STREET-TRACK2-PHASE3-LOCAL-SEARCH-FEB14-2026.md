# Jr Instruction: Jane Street Track 2 — Phase 3: Local Search Refinement

**Ticket**: #1780 (Track 2)
**Priority**: 3
**Story Points**: 3
**Assigned**: Software Engineer Jr.
**Sandbox**: /ganuda/experiments/jane-street/track2_permutation/
**Depends on**: Phase 2 (greedy solver)

## Context

Phase 2 produces a greedy permutation that may not be optimal. This phase refines it
using swap-based local search and simulated annealing. Also handles SHA256 verification
and result reporting.

## Step 1: Create local search refinement script

Create `/ganuda/experiments/jane-street/track2_permutation/local_search.py`

```python
#!/usr/bin/env python3
"""
Jane Street Track 2: Local search refinement.

Takes the best greedy solution and improves it via:
1. Adjacent swap hill climbing
2. Random swap with simulated annealing
3. Window-based reordering (try all permutations within a small window)

Also includes SHA256 verification and final result output.
"""
import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import json
import hashlib
import time
import random
import sys
from pathlib import Path

EXPERIMENT_DIR = Path(__file__).parent
PIECES_DIR = EXPERIMENT_DIR / "pieces"
RESULTS_DIR = EXPERIMENT_DIR / "results"

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
    """Load all pieces."""
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

    return blocks, last_layer_idx, last_layer


def compute_mse(order, blocks, last_layer, inputs, targets):
    """Compute MSE for a given block ordering."""
    with torch.no_grad():
        x = inputs.clone()
        for idx in order:
            x = blocks[idx](x)
        preds = last_layer(x)
        return ((preds - targets) ** 2).mean().item()


def verify_hash(order, last_layer_idx):
    """Check SHA256 hash."""
    full_perm = list(order) + [last_layer_idx]
    perm_str = ",".join(str(p) for p in full_perm)
    return hashlib.sha256(perm_str.encode()).hexdigest() == SOLUTION_HASH


def adjacent_swap_search(order, blocks, last_layer, inputs, targets, max_passes=20):
    """Repeatedly sweep through, swapping adjacent pairs if it improves MSE."""
    order = list(order)
    best_mse = compute_mse(order, blocks, last_layer, inputs, targets)
    print(f"\nAdjacent swap search (max {max_passes} passes)")
    print(f"  Starting MSE: {best_mse:.8f}")

    for pass_num in range(max_passes):
        improved = False
        for i in range(len(order) - 1):
            # Try swapping positions i and i+1
            order[i], order[i + 1] = order[i + 1], order[i]
            mse = compute_mse(order, blocks, last_layer, inputs, targets)

            if mse < best_mse:
                best_mse = mse
                improved = True
            else:
                # Revert
                order[i], order[i + 1] = order[i + 1], order[i]

        print(f"  Pass {pass_num + 1}: MSE={best_mse:.8f} {'(improved)' if improved else '(no change)'}")
        if not improved:
            break

    return order, best_mse


def simulated_annealing(order, blocks, last_layer, inputs, targets,
                        max_iters=50000, temp_start=1.0, temp_end=0.001):
    """Simulated annealing with random swaps."""
    order = list(order)
    n = len(order)
    best_mse = compute_mse(order, blocks, last_layer, inputs, targets)
    best_order = list(order)
    current_mse = best_mse

    print(f"\nSimulated annealing ({max_iters} iterations)")
    print(f"  Starting MSE: {best_mse:.8f}")

    start = time.time()
    accepts = 0

    for iteration in range(max_iters):
        # Temperature schedule (exponential decay)
        t = temp_start * (temp_end / temp_start) ** (iteration / max_iters)

        # Random swap
        i, j = random.sample(range(n), 2)
        order[i], order[j] = order[j], order[i]

        new_mse = compute_mse(order, blocks, last_layer, inputs, targets)
        delta = new_mse - current_mse

        # Accept or reject
        if delta < 0 or random.random() < np.exp(-delta / t):
            current_mse = new_mse
            accepts += 1
            if new_mse < best_mse:
                best_mse = new_mse
                best_order = list(order)
        else:
            # Revert
            order[i], order[j] = order[j], order[i]

        if iteration % 5000 == 0:
            elapsed = time.time() - start
            print(f"  Iter {iteration:6d}: MSE={current_mse:.8f} best={best_mse:.8f} "
                  f"T={t:.6f} accept={accepts}/{iteration + 1} [{elapsed:.1f}s]")

        # Early exit if hash matches
        if iteration % 1000 == 0 and verify_hash(best_order, last_layer_idx_global):
            print(f"  *** HASH MATCH at iteration {iteration}! ***")
            return best_order, best_mse

    elapsed = time.time() - start
    print(f"  Final: MSE={best_mse:.8f} accepts={accepts}/{max_iters} [{elapsed:.1f}s]")
    return best_order, best_mse


def window_reorder(order, blocks, last_layer, inputs, targets, window_size=4):
    """Try all permutations within sliding windows."""
    from itertools import permutations

    order = list(order)
    n = len(order)
    best_mse = compute_mse(order, blocks, last_layer, inputs, targets)
    print(f"\nWindow reorder (window={window_size})")
    print(f"  Starting MSE: {best_mse:.8f}")

    improved_count = 0
    for start in range(n - window_size + 1):
        window = order[start:start + window_size]
        best_window = list(window)

        for perm in permutations(window):
            order[start:start + window_size] = list(perm)
            mse = compute_mse(order, blocks, last_layer, inputs, targets)
            if mse < best_mse:
                best_mse = mse
                best_window = list(perm)

        order[start:start + window_size] = best_window

        if start % 20 == 0:
            print(f"  Window {start}/{n - window_size}: MSE={best_mse:.8f}")

    print(f"  Final: MSE={best_mse:.8f}")
    return order, best_mse


# Global for simulated annealing callback
last_layer_idx_global = None


def main():
    global last_layer_idx_global

    print("=" * 60)
    print("JANE STREET TRACK 2 — LOCAL SEARCH REFINEMENT")
    print("Cherokee AI Federation — Sandboxed")
    print("=" * 60)

    # Load pieces
    blocks, last_layer_idx, last_layer = load_pieces()
    last_layer_idx_global = last_layer_idx

    # Load data
    df = pd.read_csv(EXPERIMENT_DIR / "historical_data.csv")
    data_tensor = torch.tensor(df.values, dtype=torch.float32)

    sample_block = next(iter(blocks.values()))
    in_dim = sample_block.inp.in_features
    out_dim = last_layer.layer.out_features

    inputs = data_tensor[:, :in_dim]
    targets = data_tensor[:, -out_dim:]

    # Use a sample for speed during search
    sample_size = min(len(inputs), 1000)
    sample_idx = torch.randperm(len(inputs))[:sample_size]
    x_sample = inputs[sample_idx]
    y_sample = targets[sample_idx]

    # Load best greedy result
    greedy_path = RESULTS_DIR / "greedy_results.json"
    if not greedy_path.exists():
        print("ERROR: Run greedy_solver.py first!")
        sys.exit(1)

    with open(greedy_path) as f:
        greedy_results = json.load(f)

    # Find best method
    best_method = min(greedy_results, key=lambda m: greedy_results[m]["mse"])
    order = greedy_results[best_method]["order"]
    print(f"\nStarting from {best_method} (MSE={greedy_results[best_method]['mse']:.8f})")

    # Already solved?
    if verify_hash(order, last_layer_idx):
        print("*** ALREADY SOLVED from greedy! ***")
        return

    # Phase 1: Adjacent swap
    order, mse = adjacent_swap_search(order, blocks, last_layer, x_sample, y_sample)
    if verify_hash(order, last_layer_idx):
        print("*** SOLVED after adjacent swap! ***")

    # Phase 2: Window reorder
    order, mse = window_reorder(order, blocks, last_layer, x_sample, y_sample, window_size=4)
    if verify_hash(order, last_layer_idx):
        print("*** SOLVED after window reorder! ***")

    # Phase 3: Simulated annealing
    order, mse = simulated_annealing(order, blocks, last_layer, x_sample, y_sample,
                                      max_iters=50000)

    # Final verification on full dataset
    full_mse = compute_mse(order, blocks, last_layer, inputs[:2000], targets[:2000])
    matched = verify_hash(order, last_layer_idx)

    full_perm = order + [last_layer_idx]

    # Save final results
    final = {
        "permutation": full_perm,
        "permutation_str": ",".join(str(p) for p in full_perm),
        "mse_sample": mse,
        "mse_full": full_mse,
        "hash_match": matched,
        "hash": hashlib.sha256(",".join(str(p) for p in full_perm).encode()).hexdigest(),
    }

    output_path = RESULTS_DIR / "final_solution.json"
    with open(output_path, 'w') as f:
        json.dump(final, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"FINAL RESULT")
    print(f"MSE (sample): {mse:.8f}")
    print(f"MSE (full):   {full_mse:.8f}")
    print(f"Hash match:   {matched}")
    print(f"Saved to:     {output_path}")
    if matched:
        print(f"\n*** PUZZLE SOLVED! Submit permutation to archaeology@janestreet.com ***")
    else:
        print(f"\nNot solved yet. Try adjusting parameters or different initial ordering.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
```

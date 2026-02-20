# Jr Instruction: Jane Street ML Puzzle — Analysis Pipeline Setup

**Kanban**: #1780
**Story Points**: 8
**Council Vote**: #e5842a46de56dca3 (PROCEED WITH CAUTION, 0.843) + #4b08e1ae7f65561c (ultrathink)
**Priority**: 8 (RC-2026-02D)
**Dependencies**: None
**Risk**: LOW — sandboxed experiment, no production impact
**Security**: SANDBOXED — all code in /ganuda/experiments/jane-street/, NO prod node impact

## Objective

Set up analysis pipelines for Jane Street x Dwarkesh ML puzzle Tracks 1 and 2.
$50K prize pool. Submission: archaeology@janestreet.com

## Step 1: Create Experiment Directory and Analysis Script for Track 1

Create `/ganuda/experiments/jane-street/track1_archaeology/analyze_model.py`

```python
#!/usr/bin/env python3
"""
Jane Street Puzzle Track 1: Archaeology — DES Neural Net Decompilation
Analyze the 5,442-layer neural network that implements a digital circuit.

References:
- HuggingFace: https://huggingface.co/spaces/jane-street/puzzle
- Community: https://github.com/liamzebedee/janest-1
- Model: https://huggingface.co/jane-street/2025-03-10
"""

import torch
import numpy as np
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

EXPERIMENT_DIR = Path(__file__).parent
RESULTS_DIR = EXPERIMENT_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def download_model():
    """Download model from HuggingFace if not already present."""
    model_path = EXPERIMENT_DIR / "model.pt"
    if model_path.exists():
        print(f"Model already exists: {model_path}")
        return model_path

    print("Downloading model from HuggingFace...")
    try:
        from huggingface_hub import hf_hub_download
        downloaded = hf_hub_download(
            repo_id="jane-street/2025-03-10",
            filename="model.pt",
            local_dir=str(EXPERIMENT_DIR)
        )
        print(f"Downloaded to: {downloaded}")
        return Path(downloaded)
    except Exception as e:
        print(f"Download failed: {e}")
        print("Manual download: https://huggingface.co/jane-street/2025-03-10")
        sys.exit(1)


def analyze_architecture(model):
    """Analyze model architecture: layers, dimensions, weight statistics."""
    layers = list(model.children()) if hasattr(model, 'children') else []
    if not layers:
        # Try sequential access
        if isinstance(model, torch.nn.Sequential):
            layers = list(model)
        else:
            layers = [m for m in model.modules() if m is not model]

    print(f"\n=== ARCHITECTURE ANALYSIS ===")
    print(f"Total layers: {len(layers)}")

    layer_types = Counter()
    dimensions = []
    linear_layers = []

    for i, layer in enumerate(layers):
        layer_type = type(layer).__name__
        layer_types[layer_type] += 1

        if isinstance(layer, torch.nn.Linear):
            in_f, out_f = layer.in_features, layer.out_features
            dimensions.append((i, in_f, out_f))
            linear_layers.append((i, layer))

    print(f"\nLayer type distribution:")
    for lt, count in layer_types.most_common():
        print(f"  {lt}: {count}")

    if dimensions:
        print(f"\nLinear layer dimensions (first 10):")
        for idx, in_f, out_f in dimensions[:10]:
            print(f"  Layer {idx}: {in_f} -> {out_f}")

        print(f"\nUnique input dims: {len(set(d[1] for d in dimensions))}")
        print(f"Unique output dims: {len(set(d[2] for d in dimensions))}")

        dim_counter = Counter()
        for _, in_f, out_f in dimensions:
            dim_counter[in_f] += 1
            dim_counter[out_f] += 1
        print(f"\nMost common dimensions:")
        for dim, count in dim_counter.most_common(10):
            print(f"  {dim}: appears {count} times")

    return layers, linear_layers, dimensions


def analyze_weights(linear_layers):
    """Analyze weight and bias value distributions."""
    print(f"\n=== WEIGHT ANALYSIS ===")

    all_weights = []
    all_biases = []
    weight_value_counts = Counter()
    bias_values = []

    for idx, layer in linear_layers:
        w = layer.weight.data.numpy().flatten()
        all_weights.extend(w)
        for v in w:
            weight_value_counts[float(v)] += 1

        if layer.bias is not None:
            b = layer.bias.data.numpy().flatten()
            all_biases.extend(b)
            bias_values.append((idx, b))

    all_weights = np.array(all_weights)
    all_biases = np.array(all_biases) if all_biases else np.array([])

    print(f"Total weight values: {len(all_weights)}")
    print(f"Unique weight values: {len(weight_value_counts)}")
    print(f"\nWeight value distribution (top 10):")
    for val, count in weight_value_counts.most_common(10):
        pct = count / len(all_weights) * 100
        print(f"  {val:>6.1f}: {count:>10,} ({pct:.1f}%)")

    print(f"\nWeight range: [{all_weights.min():.1f}, {all_weights.max():.1f}]")

    if len(all_biases) > 0:
        print(f"\nTotal bias values: {len(all_biases)}")
        print(f"Bias range: [{all_biases.min():.1f}, {all_biases.max():.1f}]")

        # Check if biases are powers of 2
        non_zero_biases = all_biases[all_biases != 0]
        if len(non_zero_biases) > 0:
            log2_biases = np.log2(np.abs(non_zero_biases))
            is_power_of_2 = np.allclose(log2_biases, np.round(log2_biases))
            print(f"All non-zero biases are powers of 2: {is_power_of_2}")

    # Check for DES test vector at layer 6
    print(f"\n=== DES VECTOR CHECK (Layer 6) ===")
    for idx, biases in bias_values:
        if idx <= 10:  # Check early layers
            hex_str = ''.join(f'{int(abs(b)):02x}' for b in biases[:16] if b != 0)
            if hex_str:
                print(f"  Layer {idx} bias hex (first 16 non-zero): {hex_str}")

    return all_weights, all_biases


def test_model_output(model):
    """Test model with various inputs."""
    print(f"\n=== MODEL OUTPUT TESTING ===")

    test_inputs = [
        ("vegetable dog", "default hint text"),
        ("password", "DES plaintext candidate"),
        ("hello world", "basic test"),
        ("Cherokee", "tribal test"),
    ]

    for text, description in test_inputs:
        try:
            with torch.no_grad():
                output = model(text)
            print(f"  '{text}' ({description}): {float(output)}")
        except Exception as e:
            print(f"  '{text}' ({description}): ERROR - {e}")
            # Try numeric input if text fails
            try:
                numeric_input = torch.zeros(1, 55)
                with torch.no_grad():
                    output = model(numeric_input)
                print(f"  zeros(1,55): {float(output)}")
                break
            except Exception as e2:
                print(f"  numeric fallback also failed: {e2}")


def save_results(layers, linear_layers, dimensions, all_weights, all_biases):
    """Save analysis results to JSON."""
    results = {
        "total_layers": len(layers),
        "linear_layers": len(linear_layers),
        "dimensions": [(int(i), int(inf), int(outf)) for i, inf, outf in dimensions],
        "weight_stats": {
            "total": int(len(all_weights)),
            "unique": int(len(set(float(w) for w in all_weights))),
            "min": float(all_weights.min()),
            "max": float(all_weights.max()),
            "mean": float(all_weights.mean()),
        },
        "bias_stats": {
            "total": int(len(all_biases)),
            "min": float(all_biases.min()) if len(all_biases) > 0 else None,
            "max": float(all_biases.max()) if len(all_biases) > 0 else None,
        } if len(all_biases) > 0 else None,
    }

    output_path = RESULTS_DIR / "architecture_analysis.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {output_path}")


def main():
    print("=" * 60)
    print("JANE STREET PUZZLE — TRACK 1: ARCHAEOLOGY")
    print("Cherokee AI Federation — Sandboxed Analysis")
    print("=" * 60)

    model_path = download_model()

    print(f"\nLoading model from {model_path}...")
    model = torch.load(str(model_path), weights_only=False, map_location='cpu')
    model.eval()
    print(f"Model type: {type(model).__name__}")

    layers, linear_layers, dimensions = analyze_architecture(model)
    all_weights, all_biases = analyze_weights(linear_layers)
    test_model_output(model)
    save_results(layers, linear_layers, dimensions, all_weights, all_biases)

    print(f"\n{'=' * 60}")
    print("NEXT STEPS:")
    print("1. Reproduce community decompiler (liamzebedee/janest-1)")
    print("2. Extract symbolic SSA form from Linear->ReLU patterns")
    print("3. Identify complete algorithm (DES variant or composition)")
    print("4. Write up findings for archaeology@janestreet.com")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
```

## Step 2: Create Track 2 Permutation Solver

Create `/ganuda/experiments/jane-street/track2_permutation/solve_permutation.py`

```python
#!/usr/bin/env python3
"""
Jane Street Puzzle Track 2: Dropped Neural Net — Permutation Solver
Find the correct ordering of 97 neural network pieces.

References:
- HuggingFace: https://huggingface.co/spaces/jane-street/droppedaneuralnet
- Solution hash: 093be1cf2d24094db903cbc3e8d33d306ebca49c6accaa264e44b0b675e7d9c4
"""

import torch
import torch.nn as nn
import numpy as np
import hashlib
import json
import os
import sys
from pathlib import Path

EXPERIMENT_DIR = Path(__file__).parent
RESULTS_DIR = EXPERIMENT_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

SOLUTION_HASH = "093be1cf2d24094db903cbc3e8d33d306ebca49c6accaa264e44b0b675e7d9c4"


class Block(nn.Module):
    """Residual block from the puzzle description."""
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
    """Final projection layer."""
    def __init__(self, in_dim, out_dim):
        super().__init__()
        self.layer = nn.Linear(in_dim, out_dim)

    def forward(self, x):
        return self.layer(x)


def download_pieces():
    """Download puzzle pieces from HuggingFace."""
    pieces_dir = EXPERIMENT_DIR / "pieces"
    if pieces_dir.exists() and len(list(pieces_dir.glob("*.pt"))) > 0:
        print(f"Pieces already downloaded: {pieces_dir}")
        return pieces_dir

    print("Downloading puzzle pieces from HuggingFace...")
    try:
        from huggingface_hub import snapshot_download
        snapshot_download(
            repo_id="jane-street/droppedaneuralnet",
            local_dir=str(EXPERIMENT_DIR),
            repo_type="space"
        )
        print("Downloaded successfully")
        return pieces_dir
    except Exception as e:
        print(f"Download failed: {e}")
        print("Manual download from: https://huggingface.co/spaces/jane-street/droppedaneuralnet")
        sys.exit(1)


def load_pieces(pieces_dir):
    """Load all 97 pieces and classify them."""
    pieces = {}
    for pt_file in sorted(pieces_dir.glob("*.pt")):
        idx = int(pt_file.stem.replace("piece_", ""))
        piece = torch.load(str(pt_file), weights_only=False, map_location='cpu')
        pieces[idx] = piece

    print(f"\nLoaded {len(pieces)} pieces")

    # Classify pieces
    blocks = {}
    last_layers = {}
    for idx, piece in pieces.items():
        if hasattr(piece, 'layer'):  # LastLayer
            last_layers[idx] = piece
            in_d = piece.layer.in_features
            out_d = piece.layer.out_features
            print(f"  Piece {idx}: LastLayer ({in_d} -> {out_d})")
        elif hasattr(piece, 'inp'):  # Block
            blocks[idx] = piece
            in_d = piece.inp.in_features
            hidden_d = piece.inp.out_features
            print(f"  Piece {idx}: Block ({in_d} -> {hidden_d} -> {in_d})")

    print(f"\nBlocks: {len(blocks)}, LastLayers: {len(last_layers)}")
    return pieces, blocks, last_layers


def verify_solution(permutation):
    """Check if a permutation matches the solution hash."""
    perm_str = ",".join(str(p) for p in permutation)
    hash_val = hashlib.sha256(perm_str.encode()).hexdigest()
    matches = hash_val == SOLUTION_HASH
    print(f"\nPermutation: {perm_str[:60]}...")
    print(f"SHA256: {hash_val}")
    print(f"Matches solution: {matches}")
    return matches


def analyze_piece_compatibility(pieces, blocks, last_layers):
    """Analyze which pieces can follow which based on dimensions."""
    print(f"\n=== COMPATIBILITY ANALYSIS ===")

    # Get all unique dimensions
    dims = set()
    for idx, block in blocks.items():
        dims.add(block.inp.in_features)
    for idx, ll in last_layers.items():
        dims.add(ll.layer.in_features)
        dims.add(ll.layer.out_features)

    print(f"Unique dimensions: {sorted(dims)}")

    # For residual blocks, in_dim == out_dim (residual connection)
    # So ordering is NOT determined by shape matching
    # Must use functional behavior on data

    # Save analysis
    analysis = {
        "num_pieces": len(pieces),
        "num_blocks": len(blocks),
        "num_last_layers": len(last_layers),
        "unique_dimensions": sorted(dims),
        "block_indices": sorted(blocks.keys()),
        "last_layer_indices": sorted(last_layers.keys()),
    }

    output_path = RESULTS_DIR / "piece_analysis.json"
    with open(output_path, 'w') as f:
        json.dump(analysis, f, indent=2)
    print(f"Analysis saved to: {output_path}")

    return analysis


def greedy_order_by_activation(pieces, blocks, last_layers, data_path=None):
    """Attempt greedy ordering using activation pattern matching."""
    print(f"\n=== GREEDY ORDERING ATTEMPT ===")

    # Load historical data if available
    data = None
    csv_path = EXPERIMENT_DIR / "historical_data.csv"
    if csv_path.exists():
        import pandas as pd
        data = pd.read_csv(csv_path)
        print(f"Loaded historical data: {data.shape}")

    if data is None:
        print("No historical data found. Download from HuggingFace space.")
        print("Skipping greedy ordering for now.")
        return None

    # Strategy: The last layer must be final (reduces dim to output)
    # Remaining 96 blocks go in some order
    # Test: which block ordering minimizes prediction error on historical data

    # Phase 1: Identify the last layer (the one with different out_dim)
    last_layer_idx = list(last_layers.keys())
    print(f"Last layer candidates: {last_layer_idx}")

    # Phase 2: For each pair of blocks, compute activation correlation
    # Blocks that produce activations consumed by the next block should correlate
    print("Computing pairwise activation correlations...")
    print("(This is a placeholder — full implementation needs historical data analysis)")

    return None


def main():
    print("=" * 60)
    print("JANE STREET PUZZLE — TRACK 2: DROPPED NEURAL NET")
    print("Cherokee AI Federation — Sandboxed Analysis")
    print("=" * 60)

    pieces_dir = download_pieces()
    pieces, blocks, last_layers = load_pieces(pieces_dir)
    analysis = analyze_piece_compatibility(pieces, blocks, last_layers)
    greedy_order_by_activation(pieces, blocks, last_layers)

    print(f"\n{'=' * 60}")
    print("NEXT STEPS:")
    print("1. Download historical_data.csv from HuggingFace space")
    print("2. Compute pairwise activation correlations between blocks")
    print("3. Build chain using correlation-based greedy algorithm")
    print("4. Optimize with local search (swap adjacent, measure loss)")
    print("5. Verify with SHA256 hash")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
```

## Step 3: Create Project README

Create `/ganuda/experiments/jane-street/README.md`

```text
# Jane Street x Dwarkesh ML Puzzle — Cherokee AI Federation

Prize: $50K | Submit: archaeology@janestreet.com
Council Votes: e5842a46de56dca3, 4b08e1ae7f65561c
Status: ACTIVE — SANDBOXED ANALYSIS

## Tracks

### Track 1: Archaeology (DES Neural Net)
- 5,442-layer network implementing digital circuit
- Community: partial decompiler (liamzebedee/janest-1)
- Our goal: extend symbolic extraction, identify full algorithm
- Dir: track1_archaeology/

### Track 2: Dropped Neural Net (Permutation)
- 97 pieces to reorder, 44 people have solved
- SHA256 verification hash available
- Our goal: solve via greedy activation correlation
- Dir: track2_permutation/

### Track 3: Dormant Models (Sleeper Agents)
- 671B models — beyond our VRAM capacity
- 8B warmup is tractable (Qwen2 base)
- DEFERRED until Tracks 1-2 complete
- Dir: track3_dormant/ (future)

## Guardrails (Council-Directed)
- ALL code sandboxed here — never in production paths
- 10-15% Jr cycle allocation (Raven constraint)
- No external model weights in production vLLM (Crawdad constraint)
- bmasass DeepSeek reserved for council, not puzzle work

## For Seven Generations — Cherokee AI Federation
```

## Manual Steps

None required — this is a sandboxed experiment.
To run analysis: `cd /ganuda/experiments/jane-street/track1_archaeology && python3 analyze_model.py`

## Dependencies

pip install huggingface_hub (likely already installed in cherokee_venv)

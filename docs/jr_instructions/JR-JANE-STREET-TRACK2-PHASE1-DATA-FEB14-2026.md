# Jr Instruction: Jane Street Track 2 — Phase 1: Data Download + Piece Analysis

**Ticket**: #1780 (Track 2)
**Priority**: 3
**Story Points**: 2
**Assigned**: Software Engineer Jr.
**Sandbox**: /ganuda/experiments/jane-street/track2_permutation/

## Context

Jane Street ML puzzle Track 2: "Dropped Neural Net". 97 neural network pieces (96 residual
Blocks + 1 LastLayer) need to be reordered into the correct permutation. Historical data
(input→output pairs) is provided for evaluation. All work sandboxed — no production impact.

## Step 1: Create data download script

Create `/ganuda/experiments/jane-street/track2_permutation/download_data.py`

```python
#!/usr/bin/env python3
"""
Jane Street Track 2: Download puzzle data from HuggingFace.
Downloads pieces (97 .pt files) and historical_data.csv.
"""
import os
import sys
import zipfile
import urllib.request
from pathlib import Path

EXPERIMENT_DIR = Path(__file__).parent
PIECES_DIR = EXPERIMENT_DIR / "pieces"
DATA_URL = "https://huggingface.co/spaces/jane-street/droppedaneuralnet/resolve/main/historical_data_and_pieces.zip"
ZIP_PATH = EXPERIMENT_DIR / "historical_data_and_pieces.zip"


def download():
    """Download and extract puzzle data."""
    # Check if already downloaded
    csv_path = EXPERIMENT_DIR / "historical_data.csv"
    if csv_path.exists() and PIECES_DIR.exists() and len(list(PIECES_DIR.glob("*.pt"))) >= 97:
        print(f"Data already downloaded:")
        print(f"  CSV: {csv_path} ({csv_path.stat().st_size / 1024:.0f} KB)")
        print(f"  Pieces: {len(list(PIECES_DIR.glob('*.pt')))} files")
        return True

    # Download zip
    print(f"Downloading from HuggingFace...")
    print(f"URL: {DATA_URL}")
    try:
        urllib.request.urlretrieve(DATA_URL, str(ZIP_PATH))
        print(f"Downloaded: {ZIP_PATH} ({ZIP_PATH.stat().st_size / 1024 / 1024:.1f} MB)")
    except Exception as e:
        print(f"Download failed: {e}")
        print("Try manually: wget {DATA_URL}")
        return False

    # Extract
    print("Extracting...")
    with zipfile.ZipFile(str(ZIP_PATH), 'r') as zf:
        zf.extractall(str(EXPERIMENT_DIR))
        print(f"Extracted {len(zf.namelist())} files")

    # Verify
    if not csv_path.exists():
        print(f"WARNING: historical_data.csv not found after extraction")
        # Check if it extracted into a subdirectory
        for root, dirs, files in os.walk(str(EXPERIMENT_DIR)):
            for f in files:
                if f == "historical_data.csv":
                    src = Path(root) / f
                    src.rename(csv_path)
                    print(f"Moved {src} -> {csv_path}")

    if not PIECES_DIR.exists():
        # Check for pieces in subdirectory
        for root, dirs, files in os.walk(str(EXPERIMENT_DIR)):
            pt_files = [f for f in files if f.endswith('.pt')]
            if len(pt_files) >= 97 and Path(root) != PIECES_DIR:
                Path(root).rename(PIECES_DIR)
                print(f"Moved {root} -> {PIECES_DIR}")
                break

    # Final check
    n_pieces = len(list(PIECES_DIR.glob("*.pt"))) if PIECES_DIR.exists() else 0
    csv_exists = csv_path.exists()
    print(f"\nVerification:")
    print(f"  historical_data.csv: {'OK' if csv_exists else 'MISSING'}")
    print(f"  Pieces: {n_pieces} .pt files {'OK' if n_pieces >= 97 else 'MISSING'}")

    # Clean up zip
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
        print(f"  Cleaned up zip file")

    return csv_exists and n_pieces >= 97


if __name__ == "__main__":
    success = download()
    sys.exit(0 if success else 1)
```

## Step 2: Create piece analysis script

Create `/ganuda/experiments/jane-street/track2_permutation/analyze_pieces.py`

```python
#!/usr/bin/env python3
"""
Jane Street Track 2: Analyze all 97 pieces.
Classify as Block or LastLayer, extract dimensions, compute weight statistics.
"""
import torch
import torch.nn as nn
import json
import sys
from pathlib import Path

EXPERIMENT_DIR = Path(__file__).parent
PIECES_DIR = EXPERIMENT_DIR / "pieces"
RESULTS_DIR = EXPERIMENT_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)


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


def analyze():
    """Load and analyze all pieces."""
    if not PIECES_DIR.exists():
        print("ERROR: pieces/ directory not found. Run download_data.py first.")
        sys.exit(1)

    pt_files = sorted(PIECES_DIR.glob("*.pt"))
    print(f"Found {len(pt_files)} piece files")

    blocks = {}
    last_layers = {}
    analysis = {
        "num_pieces": len(pt_files),
        "blocks": [],
        "last_layers": [],
    }

    for pt_file in pt_files:
        idx = int(pt_file.stem.replace("piece_", ""))
        piece = torch.load(str(pt_file), weights_only=False, map_location='cpu')

        if hasattr(piece, 'layer'):  # LastLayer
            in_d = piece.layer.in_features
            out_d = piece.layer.out_features
            w_norm = piece.layer.weight.data.norm().item()
            b_norm = piece.layer.bias.data.norm().item() if piece.layer.bias is not None else 0
            last_layers[idx] = piece
            info = {
                "idx": idx,
                "type": "LastLayer",
                "in_dim": in_d,
                "out_dim": out_d,
                "weight_frobenius": round(w_norm, 4),
                "bias_norm": round(b_norm, 4),
            }
            analysis["last_layers"].append(info)
            print(f"  Piece {idx:3d}: LastLayer ({in_d} -> {out_d}) |W|={w_norm:.4f}")

        elif hasattr(piece, 'inp'):  # Block
            in_d = piece.inp.in_features
            hidden_d = piece.inp.out_features
            w1_norm = piece.inp.weight.data.norm().item()
            w2_norm = piece.out.weight.data.norm().item()
            blocks[idx] = piece
            info = {
                "idx": idx,
                "type": "Block",
                "in_dim": in_d,
                "hidden_dim": hidden_d,
                "inp_weight_frobenius": round(w1_norm, 4),
                "out_weight_frobenius": round(w2_norm, 4),
            }
            analysis["blocks"].append(info)
            print(f"  Piece {idx:3d}: Block ({in_d} -> {hidden_d} -> {in_d}) |W1|={w1_norm:.4f} |W2|={w2_norm:.4f}")

        else:
            print(f"  Piece {idx:3d}: UNKNOWN TYPE — {type(piece)}")

    # Summary
    in_dims = set(b["in_dim"] for b in analysis["blocks"])
    hidden_dims = sorted(set(b["hidden_dim"] for b in analysis["blocks"]))

    analysis["summary"] = {
        "num_blocks": len(blocks),
        "num_last_layers": len(last_layers),
        "block_in_dims": sorted(in_dims),
        "block_hidden_dims": hidden_dims,
        "last_layer_in_dim": analysis["last_layers"][0]["in_dim"] if analysis["last_layers"] else None,
        "last_layer_out_dim": analysis["last_layers"][0]["out_dim"] if analysis["last_layers"] else None,
    }

    print(f"\n=== SUMMARY ===")
    print(f"Blocks: {len(blocks)}")
    print(f"LastLayers: {len(last_layers)}")
    print(f"Block in_dim(s): {sorted(in_dims)}")
    print(f"Block hidden_dims: {hidden_dims}")
    if analysis["last_layers"]:
        ll = analysis["last_layers"][0]
        print(f"LastLayer: piece {ll['idx']} ({ll['in_dim']} -> {ll['out_dim']})")

    # Also analyze historical data dimensions
    csv_path = EXPERIMENT_DIR / "historical_data.csv"
    if csv_path.exists():
        import pandas as pd
        df = pd.read_csv(csv_path)
        analysis["historical_data"] = {
            "rows": len(df),
            "columns": list(df.columns),
            "num_columns": len(df.columns),
            "shape": list(df.shape),
        }
        print(f"\nHistorical data: {df.shape}")
        print(f"Columns: {list(df.columns)[:10]}{'...' if len(df.columns) > 10 else ''}")

        # Infer input/output split
        # Typically: input features = all but last column(s), target = last column(s)
        print(f"First 5 column names: {list(df.columns)[:5]}")
        print(f"Last 5 column names: {list(df.columns)[-5:]}")

    # Save
    output_path = RESULTS_DIR / "piece_analysis.json"
    with open(output_path, 'w') as f:
        json.dump(analysis, f, indent=2)
    print(f"\nAnalysis saved to: {output_path}")


if __name__ == "__main__":
    analyze()
```

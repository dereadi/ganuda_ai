# Jr Instruction: Jane Street Track 2 — Visual Analysis Dashboard

**Task**: Create visualization scripts that render the puzzle's structure, pairing signals, and pool convergence as images for human pattern recognition.

**Kanban**: #1790 (Jane Street Track 2)
**Priority**: 2 (HIGH)
**Depends on**: `mse_greedy_pairing.py` (gradient cost matrix), `js_puzzle_pool` table

## Context

We've been analyzing this puzzle numerically for hours. Time to LOOK at it. The gradient MSE cost matrix has a 48x48 structure that may reveal patterns invisible in summary statistics. Pool convergence data across 6 nodes might show clustering. Weight matrix structure might reveal something about the puzzle's design.

## Step 1: Create the visualization script

Create `/ganuda/experiments/jane-street/track2_permutation/visual_analysis.py`

```python
#!/usr/bin/env python3
"""Jane Street Track 2 — Visual Analysis.

Generates matplotlib figures that reveal structure in the puzzle:
1. Gradient MSE cost matrix heatmap (48x48)
2. Pool pairing agreement matrix (consensus per position)
3. Weight norm landscape (inp and out blocks, sorted)
4. Convergence trajectory (pool best over time)
5. Block activation fingerprints (PCA of what each block does to data)

Saves all figures to results/visual/ directory.
"""
import torch, numpy as np, pandas as pd, psycopg2, json, sys
import matplotlib
matplotlib.use('Agg')  # headless
import matplotlib.pyplot as plt
from pathlib import Path

sys.path.insert(0, "/ganuda/lib")

BASE = Path("/ganuda/experiments/jane-street/track2_permutation")
OUT_DIR = BASE / "results" / "visual"
OUT_DIR.mkdir(parents=True, exist_ok=True)

torch.set_num_threads(4)


def get_db_conn():
    try:
        from secrets_loader import get_secret
        password = get_secret("DB_PASSWORD")
    except Exception:
        password = "TYDo5U2NVkXqQ8DHuhIpvRgLUrXf2iZE"
    return psycopg2.connect(
        host="192.168.132.222", dbname="zammad_production",
        user="claude", password=password
    )


def load_puzzle():
    W_inp, b_inp, W_out, b_out = [], [], [], []
    inp_indices, out_indices, last_idx = [], [], None
    for i in range(97):
        d = torch.load(BASE / f"pieces/piece_{i}.pth", map_location='cpu', weights_only=True)
        w = d['weight']
        if w.shape == (96, 48):
            inp_indices.append(i)
            W_inp.append(w)
            b_inp.append(d['bias'])
        elif w.shape == (48, 96):
            out_indices.append(i)
            W_out.append(w)
            b_out.append(d['bias'])
        else:
            last_idx = i
            W_last = w
            b_last = d['bias']
    return {
        'W_inp': W_inp, 'b_inp': b_inp,
        'W_out': W_out, 'b_out': b_out,
        'W_last': W_last, 'b_last': b_last,
    }, inp_indices, out_indices, last_idx


def load_data(n=2000):
    df = pd.read_csv(BASE / "historical_data.csv")
    data = torch.tensor(df.values, dtype=torch.float32)
    return data[:n, :48], data[:n, 48]


# === FIGURE 1: Gradient MSE Cost Matrix Heatmap ===
def fig_cost_matrix(pz, X, Y):
    """48x48 heatmap of single-block gradient MSE.

    Shows which (inp, out) pairs produce low MSE when used alone.
    Diagonal-like patterns = clear pairing structure.
    Uniform = no pairing signal.
    """
    print("Fig 1: Computing gradient MSE cost matrix...")
    n = min(500, X.shape[0])
    X_sub, Y_sub = X[:n], Y[:n]

    cost = np.zeros((48, 48))
    for ii in range(48):
        h = torch.relu(X_sub @ pz['W_inp'][ii].T + pz['b_inp'][ii])
        for oi in range(48):
            residual = h @ pz['W_out'][oi].T + pz['b_out'][oi]
            x_out = X_sub + residual
            pred = x_out @ pz['W_last'].T + pz['b_last']
            cost[ii, oi] = ((pred.squeeze() - Y_sub) ** 2).mean().item()

    # Raw heatmap
    fig, axes = plt.subplots(1, 3, figsize=(24, 7))

    im = axes[0].imshow(cost, cmap='viridis', aspect='auto')
    axes[0].set_title("Gradient MSE Cost Matrix (raw)")
    axes[0].set_xlabel("Out block index")
    axes[0].set_ylabel("Inp block index")
    plt.colorbar(im, ax=axes[0])

    # Row-normalized (each row shows relative preference)
    cost_norm = cost / cost.min(axis=1, keepdims=True)
    im2 = axes[1].imshow(cost_norm, cmap='viridis', aspect='auto', vmax=2.0)
    axes[1].set_title("Row-Normalized (1.0 = best, >1 = worse)")
    axes[1].set_xlabel("Out block index")
    axes[1].set_ylabel("Inp block index")
    plt.colorbar(im2, ax=axes[1])

    # Best pairing highlighted
    # Mark mutual best matches
    best_per_row = np.argmin(cost, axis=1)
    best_per_col = np.argmin(cost, axis=0)
    mutual = np.zeros((48, 48))
    for i in range(48):
        j = best_per_row[i]
        if best_per_col[j] == i:
            mutual[i, j] = 1.0

    axes[2].imshow(cost_norm, cmap='viridis', aspect='auto', vmax=2.0, alpha=0.7)
    # Overlay mutual best as red dots
    for i in range(48):
        for j in range(48):
            if mutual[i, j] > 0:
                axes[2].plot(j, i, 'ro', markersize=8)
    axes[2].set_title(f"Mutual Best Matches ({int(mutual.sum())}/48, red dots)")
    axes[2].set_xlabel("Out block index")
    axes[2].set_ylabel("Inp block index")

    fig.tight_layout()
    fig.savefig(OUT_DIR / "cost_matrix_heatmap.png", dpi=150)
    plt.close(fig)
    print(f"  Saved: cost_matrix_heatmap.png")
    return cost


# === FIGURE 2: Pool Pairing Agreement ===
def fig_pool_agreement():
    """For each position in the top-10 pool solutions, show pairing agreement.

    If all top solutions agree on a pairing at position k, that's a strong signal.
    Disagreement spots are where the search is still uncertain.
    """
    print("Fig 2: Pool pairing agreement...")
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT inp_sigma, out_sigma, full_mse FROM js_puzzle_pool ORDER BY full_mse LIMIT 20")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("  No pool data!")
        return

    n_sol = len(rows)
    # For each position k (0..47), count how many solutions agree on the same (inp, out) pair
    agreement = np.zeros(48)
    for k in range(48):
        pair_counts = {}
        for inp_s, out_s, mse in rows:
            pair = (inp_s[k], out_s[k])
            pair_counts[pair] = pair_counts.get(pair, 0) + 1
        agreement[k] = max(pair_counts.values()) / n_sol

    # Also show inp/out diversity per position
    inp_diversity = np.zeros(48)
    out_diversity = np.zeros(48)
    for k in range(48):
        inp_set = set(r[0][k] for r in rows)
        out_set = set(r[1][k] for r in rows)
        inp_diversity[k] = len(inp_set) / n_sol
        out_diversity[k] = len(out_set) / n_sol

    fig, axes = plt.subplots(2, 1, figsize=(16, 10))

    axes[0].bar(range(48), agreement, color='steelblue', alpha=0.8)
    axes[0].axhline(y=0.5, color='red', linestyle='--', alpha=0.5, label='50% agreement')
    axes[0].set_title(f"Pool Pairing Agreement (top {n_sol} solutions)")
    axes[0].set_xlabel("Block position")
    axes[0].set_ylabel("Max pairing agreement fraction")
    axes[0].legend()

    x = np.arange(48)
    width = 0.35
    axes[1].bar(x - width/2, inp_diversity, width, label='Inp diversity', color='steelblue', alpha=0.7)
    axes[1].bar(x + width/2, out_diversity, width, label='Out diversity', color='coral', alpha=0.7)
    axes[1].set_title("Block Diversity per Position (lower = more consensus)")
    axes[1].set_xlabel("Block position")
    axes[1].set_ylabel("Unique blocks / solutions")
    axes[1].legend()

    fig.tight_layout()
    fig.savefig(OUT_DIR / "pool_agreement.png", dpi=150)
    plt.close(fig)
    print(f"  Saved: pool_agreement.png")


# === FIGURE 3: Weight Norm Landscape ===
def fig_weight_norms(pz):
    """Plot Frobenius norms and spectral norms of all blocks.

    If blocks cluster by norm, that might inform pairing or ordering.
    """
    print("Fig 3: Weight norm landscape...")
    inp_frob = [pz['W_inp'][i].norm().item() for i in range(48)]
    out_frob = [pz['W_out'][i].norm().item() for i in range(48)]
    inp_spec = [torch.linalg.svdvals(pz['W_inp'][i])[0].item() for i in range(48)]
    out_spec = [torch.linalg.svdvals(pz['W_out'][i])[0].item() for i in range(48)]
    inp_bias = [pz['b_inp'][i].norm().item() for i in range(48)]
    out_bias = [pz['b_out'][i].norm().item() for i in range(48)]

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Frobenius norms scatter
    axes[0,0].scatter(inp_frob, out_frob, c=range(48), cmap='tab20', s=60, edgecolors='black', linewidths=0.5)
    for i in range(48):
        axes[0,0].annotate(str(i), (inp_frob[i], out_frob[i]), fontsize=6, ha='center')
    axes[0,0].set_title("Block Frobenius Norms (inp vs out)")
    axes[0,0].set_xlabel("Inp block ||W||_F")
    axes[0,0].set_ylabel("Out block ||W||_F")

    # Spectral norms scatter
    axes[0,1].scatter(inp_spec, out_spec, c=range(48), cmap='tab20', s=60, edgecolors='black', linewidths=0.5)
    for i in range(48):
        axes[0,1].annotate(str(i), (inp_spec[i], out_spec[i]), fontsize=6, ha='center')
    axes[0,1].set_title("Block Spectral Norms (inp vs out)")
    axes[0,1].set_xlabel("Inp block σ_max")
    axes[0,1].set_ylabel("Out block σ_max")

    # Sorted norms (do they cluster?)
    axes[1,0].bar(range(48), sorted(inp_frob), color='steelblue', alpha=0.7, label='Inp')
    axes[1,0].bar(range(48), sorted(out_frob), color='coral', alpha=0.5, label='Out')
    axes[1,0].set_title("Sorted Frobenius Norms")
    axes[1,0].legend()

    # Bias norms
    axes[1,1].scatter(inp_bias, out_bias, c=range(48), cmap='tab20', s=60, edgecolors='black', linewidths=0.5)
    for i in range(48):
        axes[1,1].annotate(str(i), (inp_bias[i], out_bias[i]), fontsize=6, ha='center')
    axes[1,1].set_title("Bias Norms (inp vs out)")
    axes[1,1].set_xlabel("Inp bias ||b||")
    axes[1,1].set_ylabel("Out bias ||b||")

    fig.tight_layout()
    fig.savefig(OUT_DIR / "weight_norms.png", dpi=150)
    plt.close(fig)
    print(f"  Saved: weight_norms.png")


# === FIGURE 4: Block Activation Fingerprints ===
def fig_activation_fingerprints(pz, X):
    """PCA of what each block does to the data.

    For each inp block, compute mean activation pattern. Project all 48 inp
    and 48 out blocks into 2D via PCA. If paired blocks cluster together,
    that's a visual pairing signal.
    """
    print("Fig 4: Activation fingerprints (PCA)...")
    n = min(500, X.shape[0])
    X_sub = X[:n]

    # Inp fingerprints: mean hidden activation h = relu(X @ W_inp.T + b_inp)
    inp_fps = []
    for i in range(48):
        h = torch.relu(X_sub @ pz['W_inp'][i].T + pz['b_inp'][i])  # (n, 96)
        inp_fps.append(h.mean(dim=0).numpy())
    inp_fps = np.array(inp_fps)  # (48, 96)

    # Out fingerprints: mean residual direction
    out_fps = []
    for j in range(48):
        # Use identity-like input through out block
        # Actually, use mean hidden from ALL inp blocks as input
        h_mean = torch.stack([torch.relu(X_sub @ pz['W_inp'][i].T + pz['b_inp'][i])
                              for i in range(48)]).mean(dim=0)
        residual = h_mean @ pz['W_out'][j].T + pz['b_out'][j]
        out_fps.append(residual.mean(dim=0).numpy())
    out_fps = np.array(out_fps)  # (48, 48)

    # PCA of combined fingerprints (pad out_fps to 96-dim)
    out_fps_padded = np.zeros((48, 96))
    out_fps_padded[:, :48] = out_fps

    combined = np.vstack([inp_fps, out_fps_padded])  # (96, 96)
    from sklearn.decomposition import PCA
    pca = PCA(n_components=2)
    coords = pca.fit_transform(combined)

    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    # Inp blocks in blue
    ax.scatter(coords[:48, 0], coords[:48, 1], c='steelblue', s=80, marker='o',
               edgecolors='black', linewidths=0.5, label='Inp blocks', alpha=0.8)
    for i in range(48):
        ax.annotate(f'i{i}', (coords[i, 0], coords[i, 1]), fontsize=6, ha='center', color='navy')

    # Out blocks in red
    ax.scatter(coords[48:, 0], coords[48:, 1], c='coral', s=80, marker='s',
               edgecolors='black', linewidths=0.5, label='Out blocks', alpha=0.8)
    for j in range(48):
        ax.annotate(f'o{j}', (coords[48+j, 0], coords[48+j, 1]), fontsize=6, ha='center', color='darkred')

    ax.set_title(f"Block Activation Fingerprints (PCA, var explained: {pca.explained_variance_ratio_.sum():.2%})")
    ax.legend()

    fig.tight_layout()
    fig.savefig(OUT_DIR / "activation_fingerprints.png", dpi=150)
    plt.close(fig)
    print(f"  Saved: activation_fingerprints.png")


# === FIGURE 5: Convergence History ===
def fig_convergence():
    """Pool MSE over time, colored by contributing node."""
    print("Fig 5: Convergence history...")
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT worker_id, full_mse, created_at FROM js_puzzle_pool ORDER BY created_at")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("  No pool data!")
        return

    times = [(r[2] - rows[0][2]).total_seconds() / 3600 for r in rows]
    mses = [r[1] for r in rows]
    workers = [r[0] for r in rows]

    # Running minimum
    running_min = []
    cur_min = float('inf')
    for m in mses:
        cur_min = min(cur_min, m)
        running_min.append(cur_min)

    # Color by node
    node_colors = {}
    color_map = {'redfin': 'red', 'bluefin': 'blue', 'greenfin': 'green',
                 'sasass': 'orange', 'sasass2': 'purple', 'bmasass': 'brown',
                 'surgery': 'black', 'constrained': 'magenta', 'pairing': 'cyan'}
    colors = []
    for w in workers:
        c = 'gray'
        for node, col in color_map.items():
            if node in w:
                c = col
                break
        colors.append(c)

    fig, axes = plt.subplots(2, 1, figsize=(16, 10))

    axes[0].scatter(times, mses, c=colors, s=10, alpha=0.5)
    axes[0].plot(times, running_min, 'k-', linewidth=2, label='Pool best')
    axes[0].set_title("Pool Convergence (all solutions)")
    axes[0].set_xlabel("Hours since start")
    axes[0].set_ylabel("MSE")
    axes[0].set_yscale('log')
    axes[0].legend()

    # Zoomed to best solutions
    good_mask = [m < 0.1 for m in mses]
    good_times = [t for t, g in zip(times, good_mask) if g]
    good_mses = [m for m, g in zip(mses, good_mask) if g]
    good_colors = [c for c, g in zip(colors, good_mask) if g]
    good_running = [r for r, g in zip(running_min, good_mask) if g]

    if good_times:
        axes[1].scatter(good_times, good_mses, c=good_colors, s=20, alpha=0.7)
        axes[1].plot(good_times, good_running, 'k-', linewidth=2, label='Pool best')
        axes[1].axhline(y=0.0145, color='gold', linestyle='--', label='Target (0.0145)')
        axes[1].set_title("Convergence (MSE < 0.1)")
        axes[1].set_xlabel("Hours since start")
        axes[1].set_ylabel("MSE")
        axes[1].legend()

    fig.tight_layout()
    fig.savefig(OUT_DIR / "convergence.png", dpi=150)
    plt.close(fig)
    print(f"  Saved: convergence.png")


def main():
    print("=" * 60)
    print("Jane Street Track 2 — Visual Analysis")
    print("=" * 60)

    pz, inp_indices, out_indices, last_idx = load_puzzle()
    X, Y = load_data(2000)

    cost = fig_cost_matrix(pz, X, Y)
    fig_pool_agreement()
    fig_weight_norms(pz)
    fig_convergence()

    try:
        fig_activation_fingerprints(pz, X)
    except ImportError:
        print("  sklearn not available, skipping PCA fingerprints")

    print(f"\n=== All figures saved to {OUT_DIR} ===")
    print("View with: scp redfin:/ganuda/experiments/jane-street/track2_permutation/results/visual/*.png .")


if __name__ == "__main__":
    main()
```

## Expected Outcome

5 PNG figures in `results/visual/`:
1. `cost_matrix_heatmap.png` — 48x48 gradient MSE with mutual best overlay
2. `pool_agreement.png` — pairing consensus per position across top-20 solutions
3. `weight_norms.png` — Frobenius/spectral/bias norm scatterplots
4. `activation_fingerprints.png` — PCA of block activation patterns
5. `convergence.png` — pool MSE over time, colored by node

## Testing

```text
cd /ganuda/experiments/jane-street/track2_permutation
/ganuda/home/dereadi/cherokee_venv/bin/python3 visual_analysis.py
```

Then SCP the images to view them:
```text
scp redfin:/ganuda/experiments/jane-street/track2_permutation/results/visual/*.png /tmp/
```

## Notes

- Uses matplotlib Agg backend (headless — no display needed)
- Cost matrix computation takes ~2min (48*48 forward passes)
- Pool agreement reveals WHERE the search is uncertain — those positions need the most work
- Activation fingerprints might reveal clustering that matches pairing structure
- If sklearn not available, the PCA figure is skipped gracefully

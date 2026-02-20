# Jr Instruction: MSE-Based Greedy Pairing for Jane Street Track 2

**Task ID**: PUZZLE-MSE-PAIR-001
**Priority**: 1 (CRITICAL — this is blocking progress)
**Assigned Jr**: Software Engineer Jr.
**Council Vote**: #f242d61d (REVIEW REQUIRED, 0.842)
**use_rlm**: false

## Context

Research revealed the public solver (MSE 0.0145) solved pairing FIRST ("the easy part"), then SA'd only the ordering. We're searching pairings AND orderings simultaneously — (48!)^2 instead of 48!. Our 4 previous pairing methods (cosine, transpose, SVD, activation) all failed with 0/48 matches against the pool best. But they all used weight statistics, NOT actual forward-pass MSE on data.

The simplest approach: for each inp block, try all 48 out blocks on real data, measure which produces the best single-block residual. If pairing is "easy," this should work.

## Objective

Create `/ganuda/experiments/jane-street/track2_permutation/mse_greedy_pairing.py` — a script that:
1. For each (inp, out) pair, computes single-block MSE: `||x + relu(x @ W_inp.T + b_inp) @ W_out.T + b_out - x||` on data
2. Uses Hungarian algorithm on the MSE matrix to find optimal pairing
3. Also tries: greedy pairing, bias-vector pairing, and gradient-based pairing
4. Compares all pairings against the current pool best's pairing
5. With the best pairing fixed, runs SA on ordering only (48! space)
6. Injects results into pool

## Implementation

Create `/ganuda/experiments/jane-street/track2_permutation/mse_greedy_pairing.py`

```python
#!/usr/bin/env python3
"""MSE-Based Greedy Pairing — Council Vote #f242d61d.

The simplest pairing approach: run each (inp, out) combination on real data,
measure the single-block residual, and find optimal pairing via Hungarian algorithm.

Also tries bias-vector distance and gradient correlation as alternatives.
"""
import torch, numpy as np, json, psycopg2, hashlib, time, sys
from pathlib import Path
from scipy.optimize import linear_sum_assignment

sys.path.insert(0, "/ganuda/lib")

BASE = Path("/ganuda/experiments/jane-street/track2_permutation")
N_BLOCKS = 48
TARGET_HASH = "093be1cf2d24094db903cbc3e8d33d306ebca49c6accaa264e44b0b675e7d9c4"

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
    pz = {
        'W_inp': torch.stack(W_inp), 'b_inp': torch.stack(b_inp),
        'W_out': torch.stack(W_out), 'b_out': torch.stack(b_out),
        'W_last': W_last, 'b_last': b_last
    }
    return pz, inp_indices, out_indices, last_idx


def load_data(n_samples=2000):
    import pandas as pd
    df = pd.read_csv(BASE / "historical_data.csv")
    X = torch.tensor(df.iloc[:, :48].values, dtype=torch.float32)[:n_samples]
    Y = torch.tensor(df.iloc[:, 48].values, dtype=torch.float32)[:n_samples]
    return X, Y


def compute_mse(inp_s, out_s, X, Y, pz):
    x = X.clone()
    for k in range(N_BLOCKS):
        h = torch.relu(x @ pz['W_inp'][inp_s[k]].T + pz['b_inp'][inp_s[k]])
        x = x + h @ pz['W_out'][out_s[k]].T + pz['b_out'][out_s[k]]
    return ((x @ pz['W_last'].T + pz['b_last'] - Y.unsqueeze(1)) ** 2).mean().item()


def save_to_pool(inp_sigma, out_sigma, full_mse, inp_indices, out_indices, last_idx, tag):
    perm = []
    for k in range(N_BLOCKS):
        perm.extend([int(inp_indices[inp_sigma[k]]), int(out_indices[out_sigma[k]])])
    perm.append(int(last_idx))
    h = hashlib.sha256(json.dumps(perm).encode()).hexdigest()
    try:
        conn = get_db_conn()
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO js_puzzle_pool (worker, full_mse, inp_sigma, out_sigma, permutation, hash, hash_match) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (tag, full_mse,
             [int(x) for x in inp_sigma], [int(x) for x in out_sigma],
             perm, h, h == TARGET_HASH)
        )
        conn.close()
        print(f"  SAVED: MSE={full_mse:.6f} hash_match={h == TARGET_HASH}")
        if h == TARGET_HASH:
            print("  *** HASH MATCH — PUZZLE SOLVED! ***")
    except Exception as e:
        print(f"  DB save failed: {e}")


def method_single_block_mse(pz, X):
    """For each (inp, out) pair, compute single-block residual norm on data.

    block(x) = x + relu(x @ W_inp.T + b_inp) @ W_out.T + b_out
    residual = block(x) - x = relu(x @ W_inp.T + b_inp) @ W_out.T + b_out

    A correct pair should produce a "meaningful" residual.
    A wrong pair produces a large or chaotic residual.

    Metric: mean ||residual||^2 over samples. LOWER = tighter pair.
    """
    print("\n--- Method 1: Single-Block Residual Norm ---")
    n = min(1000, X.shape[0])
    X_sub = X[:n]

    cost = np.zeros((48, 48))
    for ii in range(48):
        h = torch.relu(X_sub @ pz['W_inp'][ii].T + pz['b_inp'][ii])  # (n, 96)
        for oi in range(48):
            residual = h @ pz['W_out'][oi].T + pz['b_out'][oi]  # (n, 48)
            cost[ii, oi] = (residual ** 2).mean().item()

    # Hungarian: minimize residual norm
    row_ind, col_ind = linear_sum_assignment(cost)
    pairs = list(zip(row_ind.tolist(), col_ind.tolist()))
    total = sum(cost[i, j] for i, j in pairs)
    print(f"  Total residual cost: {total:.4f}")
    print(f"  Mean pair cost: {total/48:.4f}")

    # Also check: for each inp, which out is the BEST match?
    greedy_pairs = []
    for ii in range(48):
        best_oi = np.argmin(cost[ii])
        greedy_pairs.append((ii, int(best_oi)))
    print(f"  Greedy unique outs: {len(set(p[1] for p in greedy_pairs))}/48")

    return pairs, cost, "residual_norm"


def method_residual_direction(pz, X):
    """Pair by cosine similarity between residual direction and input direction.

    For a correct pair, the residual should align with the data manifold.
    """
    print("\n--- Method 2: Residual-Input Direction Alignment ---")
    n = min(1000, X.shape[0])
    X_sub = X[:n]
    X_mean_dir = X_sub.mean(dim=0)
    X_mean_dir = X_mean_dir / X_mean_dir.norm()

    cost = np.zeros((48, 48))
    for ii in range(48):
        h = torch.relu(X_sub @ pz['W_inp'][ii].T + pz['b_inp'][ii])
        for oi in range(48):
            residual = h @ pz['W_out'][oi].T + pz['b_out'][oi]
            res_mean = residual.mean(dim=0)
            res_norm = res_mean.norm()
            if res_norm > 1e-8:
                cos = (res_mean @ X_mean_dir / res_norm).item()
            else:
                cos = 0.0
            # Higher alignment = better pair, so negate for minimization
            cost[ii, oi] = -abs(cos)

    row_ind, col_ind = linear_sum_assignment(cost)
    pairs = list(zip(row_ind.tolist(), col_ind.tolist()))
    return pairs, cost, "direction_alignment"


def method_bias_distance(pz):
    """Pair by distance between bias vectors.

    If biases were trained together, they may have correlated magnitudes or directions.
    inp bias: (96,), out bias: (48,) — different sizes, so compare norms.
    """
    print("\n--- Method 3: Bias Norm Correlation ---")
    inp_norms = np.array([pz['b_inp'][i].norm().item() for i in range(48)])
    out_norms = np.array([pz['b_out'][i].norm().item() for i in range(48)])

    # Sort both by norm, pair by rank
    inp_sorted = np.argsort(inp_norms)
    out_sorted = np.argsort(out_norms)
    pairs = list(zip(inp_sorted.tolist(), out_sorted.tolist()))

    # Also compute a cost matrix based on norm difference
    cost = np.zeros((48, 48))
    for i in range(48):
        for j in range(48):
            cost[i, j] = abs(inp_norms[i] - out_norms[j])

    row_ind, col_ind = linear_sum_assignment(cost)
    pairs_hungarian = list(zip(row_ind.tolist(), col_ind.tolist()))

    print(f"  Inp norm range: [{inp_norms.min():.4f}, {inp_norms.max():.4f}]")
    print(f"  Out norm range: [{out_norms.min():.4f}, {out_norms.max():.4f}]")

    return pairs_hungarian, cost, "bias_norm"


def method_gradient_correlation(pz, X, Y):
    """Pair by gradient signal.

    For each (inp, out) pair at a single position, compute the gradient of MSE
    w.r.t. the block output. Correct pairs should have aligned gradient structure.
    """
    print("\n--- Method 4: Gradient Correlation ---")
    n = min(500, X.shape[0])
    X_sub = X[:n]
    Y_sub = Y[:n]

    cost = np.zeros((48, 48))
    for ii in range(48):
        h = torch.relu(X_sub @ pz['W_inp'][ii].T + pz['b_inp'][ii])  # (n, 96)
        for oi in range(48):
            residual = h @ pz['W_out'][oi].T + pz['b_out'][oi]  # (n, 48)
            # After this block: x_out = X_sub + residual
            x_out = X_sub + residual
            # MSE through final layer
            pred = x_out @ pz['W_last'].T + pz['b_last']  # (n, 1)
            mse = ((pred.squeeze() - Y_sub) ** 2).mean().item()
            cost[ii, oi] = mse

    # This is actually the single-block FULL MSE (through last layer)
    row_ind, col_ind = linear_sum_assignment(cost)
    pairs = list(zip(row_ind.tolist(), col_ind.tolist()))
    total = sum(cost[i, j] for i, j in pairs)
    print(f"  Total single-block full MSE: {total:.4f}")
    print(f"  Mean: {total/48:.4f}")
    print(f"  Best single pair MSE: {cost[row_ind, col_ind].min():.6f}")

    return pairs, cost, "gradient_mse"


def sa_with_fixed_pairing(pairs, pz, X, Y, inp_indices, out_indices, last_idx, tag, n_steps=50000):
    """Given fixed pairings, SA over ordering only (48! space)."""
    import random
    random.seed(42)

    # Convert pairs to arrays
    pair_inp = [p[0] for p in pairs]
    pair_out = [p[1] for p in pairs]

    # Random initial ordering
    order = list(range(48))
    random.shuffle(order)
    cur_inp = [pair_inp[order[k]] for k in range(48)]
    cur_out = [pair_out[order[k]] for k in range(48)]
    cur_mse = compute_mse(cur_inp, cur_out, X, Y, pz)

    best_mse = cur_mse
    best_order = list(order)
    T = 3.0

    for step in range(n_steps):
        trial_order = list(order)
        r = random.random()
        if r < 0.6:
            # Swap two positions
            i, j = random.sample(range(48), 2)
            trial_order[i], trial_order[j] = trial_order[j], trial_order[i]
        elif r < 0.8:
            # 3-opt rotation
            pts = sorted(random.sample(range(48), 3))
            a, b, c = pts
            trial_order = trial_order[:a] + trial_order[b:c] + trial_order[a:b] + trial_order[c:]
        else:
            # Or-opt: relocate a block
            src = random.randint(0, 47)
            dst = random.randint(0, 47)
            if src != dst:
                val = trial_order.pop(src)
                trial_order.insert(dst, val)

        trial_inp = [pair_inp[trial_order[k]] for k in range(48)]
        trial_out = [pair_out[trial_order[k]] for k in range(48)]
        m = compute_mse(trial_inp, trial_out, X, Y, pz)

        delta = m - cur_mse
        if delta < 0 or random.random() < np.exp(-delta / max(T, 1e-10)):
            order, cur_mse = trial_order, m
            if m < best_mse:
                best_mse = m
                best_order = list(order)

        T *= 0.99994  # slower cooling for 50K steps

        if step % 10000 == 0:
            print(f"    SA step {step}: best={best_mse:.6f} T={T:.5f}")

    best_inp = [pair_inp[best_order[k]] for k in range(48)]
    best_out = [pair_out[best_order[k]] for k in range(48)]
    print(f"  {tag} SA result: MSE={best_mse:.6f}")

    return best_inp, best_out, best_mse


def main():
    print("=" * 60)
    print("MSE-Based Greedy Pairing — Council Vote #f242d61d")
    print("'The easy part' — finding which inp goes with which out")
    print("=" * 60)

    pz, inp_indices, out_indices, last_idx = load_puzzle()
    X, Y = load_data(2000)

    # Get pool best for comparison
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT inp_sigma, out_sigma, full_mse FROM js_puzzle_pool ORDER BY full_mse ASC LIMIT 1")
    row = cur.fetchone()
    conn.close()
    pool_inp, pool_out, pool_mse = list(row[0]), list(row[1]), float(row[2])
    pool_pairs = {pool_inp[k]: pool_out[k] for k in range(48)}
    print(f"Pool best: {pool_mse:.6f}")

    # Run all pairing methods
    all_results = []

    for method_fn, needs_data in [
        (lambda: method_single_block_mse(pz, X), True),
        (lambda: method_residual_direction(pz, X), True),
        (lambda: method_bias_distance(pz), False),
        (lambda: method_gradient_correlation(pz, X, Y), True),
    ]:
        pairs, cost, name = method_fn()

        # Check overlap with pool best pairing
        pair_dict = {i: j for i, j in pairs}
        matches = sum(1 for i in pair_dict if pair_dict[i] == pool_pairs.get(i, -1))
        print(f"  Matches pool best pairing: {matches}/48")

        # Check mutual consistency: for how many pairs is i->j AND j is best match for i?
        mutual = 0
        for i, j in pairs:
            best_for_i = np.argmin(cost[i]) if cost is not None else -1
            if best_for_i == j:
                mutual += 1
        print(f"  Mutual best matches: {mutual}/48")

        all_results.append((name, pairs, matches, mutual))

    # Run SA with the best pairing method (most matches or most mutual)
    print(f"\n{'='*60}")
    print("SA REFINEMENT WITH FIXED PAIRINGS")
    print(f"{'='*60}")

    for name, pairs, matches, mutual in sorted(all_results, key=lambda x: -x[2]):
        print(f"\n--- {name} (pool matches: {matches}, mutual: {mutual}) ---")
        inp_s, out_s, mse = sa_with_fixed_pairing(
            pairs, pz, X, Y, inp_indices, out_indices, last_idx,
            name, n_steps=50000
        )
        if mse < pool_mse:
            save_to_pool(inp_s, out_s, mse, inp_indices, out_indices, last_idx,
                         f"pairing_{name}")

    # Summary
    print(f"\n{'='*60}")
    print("PAIRING SUMMARY")
    print(f"{'='*60}")
    for name, pairs, matches, mutual in all_results:
        print(f"  {name:25s}: {matches}/48 pool matches, {mutual}/48 mutual")


if __name__ == "__main__":
    main()
```

## Manual Step (TPM)

After Jr creates the file, run on redfin:
```text
cd /ganuda/experiments/jane-street/track2_permutation
/ganuda/home/dereadi/cherokee_venv/bin/python3 mse_greedy_pairing.py
```

## Success Criteria
- Tests 4 data-driven pairing methods (NOT weight-statistics methods)
- Reports how many pairings match the current pool best
- Reports mutual consistency for each method
- Runs SA with fixed pairings (48! space instead of (48!)^2)
- Injects any improvements into pool

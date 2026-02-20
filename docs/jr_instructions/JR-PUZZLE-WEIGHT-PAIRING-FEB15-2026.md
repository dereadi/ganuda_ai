# Jr Instruction: Cosine Similarity Weight Pairing for Jane Street Track 2

**Task ID**: PUZZLE-WEIGHT-PAIR-001
**Priority**: 2 (HIGH)
**Assigned Jr**: Software Engineer Jr.
**Council Vote**: #440da232 (PROCEED WITH CAUTION, 0.793)
**use_rlm**: false

## Context

Each residual block pairs one inp matrix (96x48) with one out matrix (48x96). During training, these pairs develop structural correlations. The "Find the Lady" paper (AAAI 2024) showed that cosine similarity between flattened weight matrices can recover the correct pairing.

Our SA fleet currently searches both orderings AND pairings — a space of (48!)^2. If we can fix the pairings, we cut the search space to 48!, making SA dramatically more effective.

Fleet is at MSE 0.0341, target 0.0145.

## Objective

Create `/ganuda/experiments/jane-street/track2_permutation/weight_pairing_solver.py` — a script that:
1. Computes cosine similarity between all (inp, out) weight pairs
2. Uses Hungarian algorithm to find optimal pairing
3. Validates pairing against current pool best
4. Injects paired solutions into pool with SA refinement

## Implementation

Create `/ganuda/experiments/jane-street/track2_permutation/weight_pairing_solver.py`

```python
#!/usr/bin/env python3
"""Cosine Similarity Weight Pairing — Council Vote #440da232.

From 'Find the Lady' (AAAI 2024): paired inp/out weight matrices
develop structural correlations during training. Cosine similarity
between flattened weights can recover the correct pairing.

Also tries: Frobenius inner product, singular value correlation,
and output correlation pairing.
"""
import torch, numpy as np, json, psycopg2, hashlib, time, sys
from pathlib import Path
from scipy.optimize import linear_sum_assignment

sys.path.insert(0, "/ganuda/lib")

BASE = Path("/ganuda/experiments/jane-street/track2_permutation")
N_BLOCKS = 48
TARGET_HASH = "093be1cf2d24094db903cbc3e8d33d306ebca49c6accaa264e44b0b675e7d9c4"

torch.set_num_threads(1)


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


def method_cosine_similarity(pz):
    """Cosine similarity between flattened weight matrices."""
    print("\n--- Method 1: Cosine Similarity (Find the Lady) ---")
    sim = np.zeros((48, 48))
    for i in range(48):
        w_inp = pz['W_inp'][i].flatten()  # (96*48,)
        for j in range(48):
            w_out = pz['W_out'][j].flatten()  # (48*96,)
            # Both are 4608 elements — same size since 96*48 == 48*96
            cos = torch.nn.functional.cosine_similarity(
                w_inp.unsqueeze(0), w_out.unsqueeze(0)
            ).item()
            sim[i, j] = cos

    # Hungarian: maximize similarity (negate for minimization)
    row_ind, col_ind = linear_sum_assignment(-sim)
    pairs = list(zip(row_ind.tolist(), col_ind.tolist()))
    total_sim = sum(sim[i, j] for i, j in pairs)
    print(f"  Total similarity: {total_sim:.4f}")
    print(f"  Mean pair similarity: {total_sim/48:.4f}")
    print(f"  Top 5 pairs: {[(i, j, f'{sim[i,j]:.4f}') for i,j in sorted(pairs, key=lambda p: -sim[p[0],p[1]])[:5]]}")
    return pairs, sim


def method_transpose_correlation(pz):
    """Correlation between W_inp and W_out.T — exploiting the transpose relationship."""
    print("\n--- Method 2: Transpose Correlation ---")
    sim = np.zeros((48, 48))
    for i in range(48):
        w_inp = pz['W_inp'][i]  # (96, 48)
        for j in range(48):
            w_out_t = pz['W_out'][j].T  # (96, 48) — same shape as W_inp
            # Frobenius inner product
            sim[i, j] = (w_inp * w_out_t).sum().item()

    row_ind, col_ind = linear_sum_assignment(-sim)
    pairs = list(zip(row_ind.tolist(), col_ind.tolist()))
    total_sim = sum(sim[i, j] for i, j in pairs)
    print(f"  Total Frobenius inner product: {total_sim:.4f}")
    return pairs, sim


def method_svd_correlation(pz):
    """Correlation between singular value spectra of paired matrices."""
    print("\n--- Method 3: SVD Spectrum Correlation ---")
    # Compute SVD spectra
    inp_svs = []
    out_svs = []
    for i in range(48):
        inp_svs.append(torch.linalg.svdvals(pz['W_inp'][i]).numpy())
        out_svs.append(torch.linalg.svdvals(pz['W_out'][i]).numpy())

    sim = np.zeros((48, 48))
    for i in range(48):
        for j in range(48):
            # Correlation of singular value spectra
            sim[i, j] = np.corrcoef(inp_svs[i], out_svs[j])[0, 1]

    row_ind, col_ind = linear_sum_assignment(-sim)
    pairs = list(zip(row_ind.tolist(), col_ind.tolist()))
    total_sim = sum(sim[i, j] for i, j in pairs)
    print(f"  Total SVD correlation: {total_sim:.4f}")
    return pairs, sim


def method_activation_correlation(pz, X):
    """Correlation between inp activation norms and out output norms."""
    print("\n--- Method 4: Activation Correlation ---")
    X_sub = X[:500]

    inp_norms = []
    out_norms = []
    for i in range(48):
        h = torch.relu(X_sub @ pz['W_inp'][i].T + pz['b_inp'][i])
        inp_norms.append(h.norm(dim=1).numpy())
    for j in range(48):
        # Apply out block to identity-like input
        out_norms.append(pz['W_out'][j].norm(dim=1).numpy())

    sim = np.zeros((48, 48))
    for i in range(48):
        for j in range(48):
            # How well does out[j] "match" the activation pattern of inp[i]?
            h = torch.relu(X_sub @ pz['W_inp'][i].T + pz['b_inp'][i])
            result = h @ pz['W_out'][j].T + pz['b_out'][j]
            # A good pair should produce small residual relative to x
            sim[i, j] = -result.norm().item()  # negate: smaller norm = better pair

    row_ind, col_ind = linear_sum_assignment(-sim)  # maximize (smallest norm)
    pairs = list(zip(row_ind.tolist(), col_ind.tolist()))
    return pairs, sim


def validate_and_refine(pairs, pz, X, Y, inp_indices, out_indices, last_idx, method_name):
    """Given fixed pairings, find best ordering via greedy + SA."""
    print(f"\n  Validating {method_name} pairing...")

    # With fixed pairings, we only need to find the ordering of 48 paired blocks
    # Greedy: try each pair at position 0, extend greedily
    pair_dict = {i: j for i, j in pairs}  # inp -> out

    # Get current pool best for comparison
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT inp_sigma, out_sigma, full_mse FROM js_puzzle_pool ORDER BY full_mse ASC LIMIT 1")
    row = cur.fetchone()
    conn.close()
    pool_best_mse = float(row[2])

    # Check how many pairings match the pool best
    pool_inp = list(row[0])
    pool_out = list(row[1])
    pool_pairs = {pool_inp[k]: pool_out[k] for k in range(48)}
    matches = sum(1 for i in pair_dict if pair_dict[i] == pool_pairs.get(i, -1))
    print(f"  Pairing matches pool best: {matches}/48")

    # Simple ordering: use pool best ordering, replace pairings
    test_inp = list(pool_inp)
    test_out = [pair_dict[i] for i in test_inp]
    mse_paired = compute_mse(test_inp, test_out, X, Y, pz)
    print(f"  Pool ordering + new pairing: MSE={mse_paired:.6f} (pool best: {pool_best_mse:.6f})")

    # SA refinement with fixed pairings (only optimize ordering)
    import random
    random.seed(42)
    cur_order = list(range(48))
    random.shuffle(cur_order)
    cur_inp = [pairs[k][0] for k in cur_order]
    cur_out = [pairs[k][1] for k in cur_order]
    cur_mse = compute_mse(cur_inp, cur_out, X, Y, pz)
    best_mse = cur_mse
    best_order = list(cur_order)
    T = 2.0

    for step in range(20000):
        trial_order = list(cur_order)
        i, j = random.sample(range(48), 2)
        trial_order[i], trial_order[j] = trial_order[j], trial_order[i]

        trial_inp = [pairs[k][0] for k in trial_order]
        trial_out = [pairs[k][1] for k in trial_order]
        m = compute_mse(trial_inp, trial_out, X, Y, pz)

        delta = m - cur_mse
        if delta < 0 or random.random() < np.exp(-delta / max(T, 1e-10)):
            cur_order, cur_mse = trial_order, m
            if m < best_mse:
                best_mse = m
                best_order = list(cur_order)

        T *= 0.99985

        if step % 5000 == 0:
            print(f"    SA step {step}: best={best_mse:.6f} T={T:.5f}")

    best_inp = [pairs[k][0] for k in best_order]
    best_out = [pairs[k][1] for k in best_order]
    print(f"  {method_name} SA result: MSE={best_mse:.6f}")

    if best_mse < pool_best_mse:
        save_to_pool(best_inp, best_out, best_mse,
                     inp_indices, out_indices, last_idx,
                     f"weight_pair_{method_name}")
    return best_mse


def main():
    print("=" * 60)
    print("Weight Pairing Solver — Council Vote #440da232")
    print("Find the Lady (AAAI 2024) + variants")
    print("=" * 60)

    pz, inp_indices, out_indices, last_idx = load_puzzle()
    X, Y = load_data(2000)

    # Try all pairing methods
    results = {}

    pairs_cos, sim_cos = method_cosine_similarity(pz)
    results['cosine'] = validate_and_refine(
        pairs_cos, pz, X, Y, inp_indices, out_indices, last_idx, 'cosine')

    pairs_trans, sim_trans = method_transpose_correlation(pz)
    results['transpose'] = validate_and_refine(
        pairs_trans, pz, X, Y, inp_indices, out_indices, last_idx, 'transpose')

    pairs_svd, sim_svd = method_svd_correlation(pz)
    results['svd'] = validate_and_refine(
        pairs_svd, pz, X, Y, inp_indices, out_indices, last_idx, 'svd')

    pairs_act, sim_act = method_activation_correlation(pz, X)
    results['activation'] = validate_and_refine(
        pairs_act, pz, X, Y, inp_indices, out_indices, last_idx, 'activation')

    # Summary
    print(f"\n{'='*60}")
    print("PAIRING METHOD COMPARISON")
    print(f"{'='*60}")
    for method, mse in sorted(results.items(), key=lambda x: x[1]):
        print(f"  {method:15s}: MSE={mse:.6f}")

    # Save similarity matrices for analysis
    np.savez(BASE / "results/weight_pairing_matrices.npz",
             cosine=sim_cos, transpose=sim_trans, svd=sim_svd, activation=sim_act)
    print(f"\nSimilarity matrices saved to results/weight_pairing_matrices.npz")


if __name__ == "__main__":
    main()
```

## Manual Step (TPM)

After Jr creates the file, run on redfin:
```text
cd /ganuda/experiments/jane-street/track2_permutation
/ganuda/home/dereadi/cherokee_venv/bin/python3 weight_pairing_solver.py
```

## Success Criteria
- Tests 4 different weight pairing methods
- Reports how many pairings match the current pool best
- Runs SA with fixed pairings to find best ordering
- Injects any improvements into pool
- Saves similarity matrices for analysis

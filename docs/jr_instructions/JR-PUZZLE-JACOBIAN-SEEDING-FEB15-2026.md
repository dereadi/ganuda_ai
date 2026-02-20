# Jr Instruction: Jacobian-Based Initial Seeding for Jane Street Track 2

**Task ID**: PUZZLE-JACOBIAN-001
**Priority**: 2 (HIGH)
**Assigned Jr**: Software Engineer Jr.
**Council Vote**: #d221c4f9 (PROCEED, 0.845)
**use_rlm**: false

## Context

The SA fleet has converged to a monoculture (46/48 positions locked at 10/10 consensus). A public solver achieved MSE 0.0145 using Jacobian-based gradient ordering. We are at 0.1343 — 10x worse. The Jacobian technique computes ||dF/dx|| for each block to determine how much it transforms the input, giving a principled initial ordering.

## Objective

Create `/ganuda/experiments/jane-street/track2_permutation/jacobian_seeder.py` — a script that:
1. Computes the Jacobian magnitude of each block
2. Builds an initial ordering based on Jacobian analysis
3. Injects the result into the shared PG pool as a seed solution

## Implementation

Create `/ganuda/experiments/jane-street/track2_permutation/jacobian_seeder.py`

```python
#!/usr/bin/env python3
"""Jacobian-based initial seeding for SA fleet.

For each block, compute the Jacobian ||dF/dx|| on sample data.
Blocks with larger Jacobians reshape the representation more.
Use this to build a principled initial ordering.

Council Vote #d221c4f9.
"""
import torch, numpy as np, json, psycopg2, hashlib
from pathlib import Path

BASE = Path("/ganuda/experiments/jane-street/track2_permutation")
N_BLOCKS = 48
TARGET_HASH = "093be1cf2d24094db903cbc3e8d33d306ebca49c6accaa264e44b0b675e7d9c4"

DB_HOST = "192.168.132.222"
DB_NAME = "zammad_production"
DB_USER = "claude"
DB_PASS = "TYDo5U2NVkXqQ8DHuhIpvRgLUrXf2iZE"

torch.set_num_threads(1)


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


def compute_jacobian_norms(pz, X):
    """Compute ||dF/dx|| for each (inp, out) block on sample data.

    For a residual block F(x) = x + out(relu(inp(x))):
      dF/dx = I + W_out @ diag(relu'(inp(x))) @ W_inp

    We approximate ||dF/dx|| by the mean Frobenius norm over samples.
    """
    n_samples = min(200, X.shape[0])
    X_sub = X[:n_samples]

    jacobian_norms = np.zeros((48, 48))

    for ii in range(48):
        W1 = pz['W_inp'][ii]  # (96, 48)
        b1 = pz['b_inp'][ii]  # (96,)

        # Pre-activation for this inp block
        pre_act = X_sub @ W1.T + b1  # (n, 96)
        relu_mask = (pre_act > 0).float()  # (n, 96)

        for oi in range(48):
            W2 = pz['W_out'][oi]  # (48, 96)

            # Jacobian: I + W2 @ diag(mask) @ W1 for each sample
            # Frobenius norm approximation via trace(J^T J)
            # For efficiency, compute the residual Jacobian: W2 @ diag(mask) @ W1
            # Its norm tells us how much this block changes x

            # Batched: (n, 48, 96) @ (n, 96, 48) is expensive
            # Instead: ||W2 @ diag(mask_i) @ W1||_F^2 = sum of (W2 * mask_i @ W1)^2
            # Approximate with mean over samples of ||W2 @ diag(mask) @ W1||_F

            norms = []
            for s in range(0, n_samples, 50):
                batch_mask = relu_mask[s:s+50]  # (batch, 96)
                # J_res = W2 @ diag(mask) @ W1 for each sample
                # = (W2 * mask.unsqueeze(1)) @ W1 ... but that's (batch, 48, 96) @ (96, 48)
                # Simpler: column-scale W1 by mask, then multiply
                masked_W1 = batch_mask.unsqueeze(2) * W1.unsqueeze(0)  # (batch, 96, 48)
                J_res = W2.unsqueeze(0) @ masked_W1  # (batch, 48, 48)
                fnorm = torch.linalg.norm(J_res, dim=(1, 2))  # (batch,)
                norms.append(fnorm.mean().item())

            jacobian_norms[ii, oi] = np.mean(norms)

    return jacobian_norms


def jacobian_ordering(jac_norms, pz, X, Y):
    """Build ordering using Jacobian magnitudes.

    Strategy: blocks with SMALLER Jacobians should go first (gentle reshaping),
    blocks with LARGER Jacobians go later (heavy transformation near the end).
    Try both orderings and pick the one with lower MSE.
    """
    # Hungarian assignment for optimal pairing based on Jacobian
    from scipy.optimize import linear_sum_assignment
    row_ind, col_ind = linear_sum_assignment(-jac_norms)  # maximize
    pairs = list(zip(row_ind.tolist(), col_ind.tolist()))
    pair_jac = [jac_norms[ii, oi] for ii, oi in pairs]

    # Sort by Jacobian magnitude (ascending = gentle first)
    sorted_asc = sorted(range(48), key=lambda i: pair_jac[i])
    inp_asc = [pairs[i][0] for i in sorted_asc]
    out_asc = [pairs[i][1] for i in sorted_asc]

    # Sort descending = heavy first
    sorted_desc = sorted(range(48), key=lambda i: -pair_jac[i])
    inp_desc = [pairs[i][0] for i in sorted_desc]
    out_desc = [pairs[i][1] for i in sorted_desc]

    mse_asc = compute_mse(inp_asc, out_asc, X, Y, pz)
    mse_desc = compute_mse(inp_desc, out_desc, X, Y, pz)

    print(f"Jacobian ascending (gentle first):  MSE={mse_asc:.6f}")
    print(f"Jacobian descending (heavy first):  MSE={mse_desc:.6f}")

    if mse_asc < mse_desc:
        return inp_asc, out_asc, mse_asc, "ascending"
    else:
        return inp_desc, out_desc, mse_desc, "descending"


def save_to_pool(inp_sigma, out_sigma, full_mse, inp_indices, out_indices, last_idx, tag):
    """Save solution to shared PG pool."""
    perm = []
    for k in range(N_BLOCKS):
        perm.extend([int(inp_indices[inp_sigma[k]]), int(out_indices[out_sigma[k]])])
    perm.append(int(last_idx))

    h = hashlib.sha256(json.dumps(perm).encode()).hexdigest()

    try:
        conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
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
        print(f"Saved to pool: MSE={full_mse:.6f} hash_match={h == TARGET_HASH}")
    except Exception as e:
        print(f"DB save failed: {e}")
        # Save locally as fallback
        result = {
            "worker": tag, "full_mse": full_mse,
            "inp_sigma": [int(x) for x in inp_sigma],
            "out_sigma": [int(x) for x in out_sigma],
            "permutation": perm, "hash": h, "hash_match": h == TARGET_HASH
        }
        out_path = BASE / f"results/pool/jacobian_seed_{full_mse:.4f}.json"
        with open(out_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Saved locally: {out_path}")


def main():
    import random, time

    print("=" * 60)
    print("Jacobian-Based Seeder — Council Vote #d221c4f9")
    print("=" * 60)

    pz, inp_indices, out_indices, last_idx = load_puzzle()
    X, Y = load_data(2000)

    print(f"\nComputing Jacobian norms for all 48x48 (inp, out) pairs...")
    t0 = time.time()
    jac_norms = compute_jacobian_norms(pz, X)
    print(f"Done in {time.time()-t0:.1f}s")
    print(f"Jacobian norm range: [{jac_norms.min():.4f}, {jac_norms.max():.4f}]")

    # Build Jacobian-based ordering
    print(f"\nBuilding Jacobian-ordered solution...")
    inp_s, out_s, jac_mse, direction = jacobian_ordering(jac_norms, pz, X, Y)
    print(f"Best Jacobian ordering ({direction}): MSE={jac_mse:.6f}")

    # Refine with quick SA (10K steps)
    print(f"\nRefining with SA (10K steps)...")
    random.seed(42)
    best_inp, best_out, best_mse = list(inp_s), list(out_s), jac_mse
    cur_inp, cur_out, cur_mse = list(inp_s), list(out_s), jac_mse
    T = 2.0

    for step in range(10000):
        # Random move type
        r = random.random()
        if r < 0.4:
            # Swap two positions (paired)
            i, j = random.sample(range(48), 2)
            cur_inp[i], cur_inp[j] = cur_inp[j], cur_inp[i]
            cur_out[i], cur_out[j] = cur_out[j], cur_out[i]
        elif r < 0.7:
            # Swap just inp pairing at two positions
            i, j = random.sample(range(48), 2)
            cur_inp[i], cur_inp[j] = cur_inp[j], cur_inp[i]
        else:
            # Swap just out pairing at two positions
            i, j = random.sample(range(48), 2)
            cur_out[i], cur_out[j] = cur_out[j], cur_out[i]

        m = compute_mse(cur_inp, cur_out, X, Y, pz)
        delta = m - cur_mse
        if delta < 0 or random.random() < np.exp(-delta / T):
            cur_mse = m
            if m < best_mse:
                best_mse = m
                best_inp, best_out = list(cur_inp), list(cur_out)
        else:
            # Revert (simplified — just copy best)
            cur_inp, cur_out, cur_mse = list(best_inp), list(best_out), best_mse

        T *= 0.9997
        if step % 2000 == 0:
            print(f"  step {step}: best={best_mse:.6f} T={T:.4f}")

    print(f"\nFinal MSE after SA refinement: {best_mse:.6f}")

    # Save to pool
    save_to_pool(best_inp, best_out, best_mse, inp_indices, out_indices, last_idx,
                 "jacobian_seeder")

    # Also save Jacobian norms for future analysis
    np.save(BASE / "results/jacobian_norms.npy", jac_norms)
    print(f"Jacobian norms saved to results/jacobian_norms.npy")


if __name__ == "__main__":
    main()
```

## Manual Step (TPM)

After Jr creates the file, run on redfin:
```text
cd /ganuda/experiments/jane-street/track2_permutation
/ganuda/home/dereadi/cherokee_venv/bin/python3 jacobian_seeder.py
```

## Success Criteria
- jacobian_seeder.py runs without errors
- Produces a seed solution and injects it into the PG pool
- Jacobian norms saved for future analysis

# Jr Instruction: LOO-Targeted Seed Injection for Jane Street Track 2

**Task ID**: PUZZLE-LOO-SEED-001
**Priority**: 2 (HIGH)
**Assigned Jr**: Software Engineer Jr.
**Council Vote**: #d221c4f9 (PROCEED, 0.845)
**use_rlm**: false

## Context

Leave-one-out analysis found 7 blocks at positions 17, 21, 27, 28, 37, 43, 46 that are actively harmful — removing them improves MSE. The pool has converged to a monoculture. We need to inject diverse seed solutions that reshuffle these 7 blocks to break the basin.

## Objective

Create `/ganuda/experiments/jane-street/track2_permutation/loo_seed_injector.py` — a script that:
1. Takes the current best solution from the pool
2. Identifies the 7 LOO-harmful blocks
3. Generates N diverse seed solutions by permuting those 7 blocks to different positions
4. Injects them into the shared PG pool

## Implementation

Create `/ganuda/experiments/jane-street/track2_permutation/loo_seed_injector.py`

```python
#!/usr/bin/env python3
"""LOO-targeted seed injection to break pool monoculture.

Takes the current best solution, identifies blocks that hurt when present,
generates diverse seeds by reshuffling those blocks, and injects into pool.

Council Vote #d221c4f9.
"""
import torch, numpy as np, json, psycopg2, hashlib, random, itertools
from pathlib import Path

BASE = Path("/ganuda/experiments/jane-street/track2_permutation")
N_BLOCKS = 48
TARGET_HASH = "093be1cf2d24094db903cbc3e8d33d306ebca49c6accaa264e44b0b675e7d9c4"

DB_HOST = "192.168.132.222"
DB_NAME = "zammad_production"
DB_USER = "claude"
DB_PASS = "TYDo5U2NVkXqQ8DHuhIpvRgLUrXf2iZE"

# LOO-identified harmful positions (removal improves MSE)
LOO_HARMFUL = [17, 21, 27, 28, 37, 43, 46]

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


def get_best_from_pool():
    conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cur = conn.cursor()
    cur.execute("SELECT full_mse, inp_sigma, out_sigma FROM js_puzzle_pool ORDER BY full_mse LIMIT 1")
    row = cur.fetchone()
    conn.close()
    mse = row[0]
    inp_s = json.loads(row[1]) if isinstance(row[1], str) else list(row[1])
    out_s = json.loads(row[2]) if isinstance(row[2], str) else list(row[2])
    return mse, inp_s, out_s


def save_to_pool(inp_sigma, out_sigma, full_mse, inp_indices, out_indices, last_idx, tag):
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
        return True
    except Exception as e:
        print(f"  DB error: {e}")
        return False


def generate_loo_seeds(best_inp, best_out, n_seeds=20):
    """Generate seeds by reshuffling the 7 harmful positions."""
    seeds = []
    harmful_inp_vals = [best_inp[p] for p in LOO_HARMFUL]
    harmful_out_vals = [best_out[p] for p in LOO_HARMFUL]

    for _ in range(n_seeds):
        new_inp = list(best_inp)
        new_out = list(best_out)

        # Randomly permute the harmful positions
        perm_inp = list(harmful_inp_vals)
        perm_out = list(harmful_out_vals)
        random.shuffle(perm_inp)
        random.shuffle(perm_out)

        for i, pos in enumerate(LOO_HARMFUL):
            new_inp[pos] = perm_inp[i]
            new_out[pos] = perm_out[i]

        seeds.append((new_inp, new_out))

    return seeds


def main():
    print("=" * 60)
    print("LOO Seed Injector — Council Vote #d221c4f9")
    print(f"Targeting positions: {LOO_HARMFUL}")
    print("=" * 60)

    pz, inp_indices, out_indices, last_idx = load_puzzle()
    X, Y = load_data(2000)

    pool_mse, best_inp, best_out = get_best_from_pool()
    verified = compute_mse(best_inp, best_out, X, Y, pz)
    print(f"\nPool best MSE: {pool_mse:.6f} (verified: {verified:.6f})")

    # Generate diverse seeds
    random.seed(42)
    n_seeds = 50
    print(f"\nGenerating {n_seeds} LOO-targeted seeds...")
    seeds = generate_loo_seeds(best_inp, best_out, n_seeds)

    # Evaluate and inject best ones
    results = []
    for i, (inp_s, out_s) in enumerate(seeds):
        m = compute_mse(inp_s, out_s, X, Y, pz)
        results.append((m, inp_s, out_s))
        if i % 10 == 0:
            print(f"  Evaluated {i}/{n_seeds}...")

    results.sort(key=lambda x: x[0])

    print(f"\n=== TOP 10 LOO SEEDS ===")
    injected = 0
    for i, (m, inp_s, out_s) in enumerate(results[:10]):
        delta = m - verified
        print(f"  #{i}: MSE={m:.6f} (delta={delta:+.6f})")

        # Inject into pool (even if worse — diversity matters)
        if save_to_pool(inp_s, out_s, m, inp_indices, out_indices, last_idx,
                       f"loo_seed_{i}"):
            injected += 1

    print(f"\nInjected {injected} seeds into pool")
    print(f"Best LOO seed: {results[0][0]:.6f} vs pool best: {verified:.6f}")

    if results[0][0] < verified:
        print("*** LOO seed beat the pool! ***")
    else:
        print(f"Gap to pool: {results[0][0] - verified:.6f}")
        print("Seeds provide diversity for crossover — workers will recombine.")


if __name__ == "__main__":
    main()
```

## Manual Step (TPM)

After Jr creates the file, run on redfin:
```text
cd /ganuda/experiments/jane-street/track2_permutation
/ganuda/home/dereadi/cherokee_venv/bin/python3 loo_seed_injector.py
```

## Success Criteria
- loo_seed_injector.py runs without errors
- Injects 10+ diverse seed solutions into the PG pool
- Pool diversity increases (check via observer log)

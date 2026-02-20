# Jr Instruction: Break Point Surgery for Jane Street Track 2

**Task ID**: PUZZLE-BREAK-001
**Priority**: 2 (HIGH)
**Assigned Jr**: Software Engineer Jr.
**Council Vote**: #91115ee2 (REVIEW REQUIRED, 0.793 — all 7 specialists flagged concerns but consensus supports)
**use_rlm**: false

## Context

The SA fleet has improved to MSE 0.0762 (pool best) from initial 0.1429. Cosine similarity analysis of consecutive residual directions in the current best solution found **4 break points** where adjacent blocks are anti-correlated:

| Break | Positions | Cos Sim | Notes |
|-------|-----------|---------|-------|
| 1 | 17→18 | -0.276 | Overlaps LOO harmful block 17 |
| 2 | 29→30 | -0.409 | Strong conflict |
| 3 | 30→31 | -0.451 | Worst break (anti-correlated) |
| 4 | 45→46 | -0.241 | Overlaps LOO harmful block 46 |

Mean consecutive cosine similarity is 0.259 (std 0.319). These 4 breaks are 1.5+ std below mean. Positions overlap with LOO harmful blocks (17, 21, 27, 28, 37, 43, 46) — two independent methods pointing at the same spots.

The pool best solution (`inp_sigma` and `out_sigma`) must be read from the `js_puzzle_pool` table at runtime.

## Objective

Create `/ganuda/experiments/jane-street/track2_permutation/break_point_surgery.py` — a script that:
1. Reads the current best solution from the PG pool
2. For each of the 3 break regions, tries all local permutations of blocks in that window
3. Injects improved solutions back into the pool

## Implementation

Create `/ganuda/experiments/jane-street/track2_permutation/break_point_surgery.py`

```python
#!/usr/bin/env python3
"""Break Point Surgery — Council Vote #91115ee2.

Reads the best solution from the PG pool. For each break region,
tries all local permutations within a window. Injects improvements
into the pool for SA workers to refine.

Break Regions:
  Region A: positions 16-19 (around break at 17-18)
  Region B: positions 28-32 (around breaks at 29-30 and 30-31)
  Region C: positions 44-47 (around break at 45-46)
"""
import torch, numpy as np, json, psycopg2, hashlib, itertools, time
from pathlib import Path

BASE = Path("/ganuda/experiments/jane-street/track2_permutation")
N_BLOCKS = 48
TARGET_HASH = "093be1cf2d24094db903cbc3e8d33d306ebca49c6accaa264e44b0b675e7d9c4"

torch.set_num_threads(1)

REGIONS = {
    "A_pos16-19": (16, 20),   # 4 positions: 4! * 4! = 576 combos (paired)
    "B_pos28-32": (28, 33),   # 5 positions: 5! * 5! = 14400 combos (paired)
    "C_pos44-47": (44, 48),   # 4 positions: 4! * 4! = 576 combos (paired)
}


def get_db_conn():
    """Get database connection using secrets_loader pattern."""
    import sys
    sys.path.insert(0, "/ganuda/lib")
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


def get_best_solution():
    """Fetch best solution from PG pool."""
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT inp_sigma, out_sigma, full_mse FROM js_puzzle_pool "
        "ORDER BY full_mse ASC LIMIT 1"
    )
    row = cur.fetchone()
    conn.close()
    if row is None:
        raise RuntimeError("No solutions in pool")
    return list(row[0]), list(row[1]), float(row[2])


def save_to_pool(inp_sigma, out_sigma, full_mse, inp_indices, out_indices, last_idx, tag):
    """Save solution to shared PG pool."""
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
        print(f"  SAVED to pool: MSE={full_mse:.6f} hash_match={h == TARGET_HASH}")
        if h == TARGET_HASH:
            print("  *** HASH MATCH — PUZZLE SOLVED! ***")
    except Exception as e:
        print(f"  DB save failed: {e}")


def surgery_region(region_name, start, end, best_inp, best_out, X, Y, pz,
                   inp_indices, out_indices, last_idx):
    """Try all permutations of blocks within [start, end) for one region.

    For tractability, try independent inp and out permutations first,
    then try paired permutations of the best combinations.
    """
    width = end - start
    print(f"\n{'='*60}")
    print(f"REGION {region_name}: positions {start}-{end-1} ({width} blocks)")
    print(f"{'='*60}")

    base_inp = list(best_inp)
    base_out = list(best_out)
    base_mse = compute_mse(base_inp, base_out, X, Y, pz)
    print(f"  Baseline MSE: {base_mse:.6f}")

    # Extract the sub-arrays for this window
    inp_window = base_inp[start:end]
    out_window = base_out[start:end]

    best_found_mse = base_mse
    best_found_inp = list(base_inp)
    best_found_out = list(base_out)
    evals = 0

    # Phase 1: Try all paired permutations (same permutation applied to both inp and out)
    print(f"  Phase 1: Paired permutations ({width}! = {np.math.factorial(width)})")
    for perm in itertools.permutations(range(width)):
        trial_inp = list(base_inp)
        trial_out = list(base_out)
        for i, p in enumerate(perm):
            trial_inp[start + i] = inp_window[p]
            trial_out[start + i] = out_window[p]

        m = compute_mse(trial_inp, trial_out, X, Y, pz)
        evals += 1
        if m < best_found_mse:
            best_found_mse = m
            best_found_inp = list(trial_inp)
            best_found_out = list(trial_out)
            print(f"    NEW BEST at perm {perm}: MSE={m:.6f} (delta={m - base_mse:.6f})")

    print(f"  Phase 1 done: {evals} evals, best={best_found_mse:.6f}")

    # Phase 2: Try independent permutations (different perms for inp and out)
    # Only for small windows (width <= 4) to keep tractable
    if width <= 4:
        print(f"  Phase 2: Independent permutations ({width}!^2 = {np.math.factorial(width)**2})")
        ph2_best = best_found_mse
        for inp_perm in itertools.permutations(range(width)):
            for out_perm in itertools.permutations(range(width)):
                trial_inp = list(best_found_inp)
                trial_out = list(best_found_out)
                # Apply inp perm to the ORIGINAL window values
                for i, p in enumerate(inp_perm):
                    trial_inp[start + i] = inp_window[p]
                for i, p in enumerate(out_perm):
                    trial_out[start + i] = out_window[p]

                m = compute_mse(trial_inp, trial_out, X, Y, pz)
                evals += 1
                if m < best_found_mse:
                    best_found_mse = m
                    best_found_inp = list(trial_inp)
                    best_found_out = list(trial_out)
                    print(f"    NEW BEST at inp={inp_perm} out={out_perm}: MSE={m:.6f}")

        print(f"  Phase 2 done: {evals} total evals, best={best_found_mse:.6f}")
    else:
        # For width=5 (region B), sample 20K random independent permutations
        import random
        random.seed(42)
        n_samples = 20000
        print(f"  Phase 2: Sampled independent permutations ({n_samples})")
        for _ in range(n_samples):
            inp_perm = list(range(width))
            out_perm = list(range(width))
            random.shuffle(inp_perm)
            random.shuffle(out_perm)

            trial_inp = list(best_found_inp)
            trial_out = list(best_found_out)
            for i, p in enumerate(inp_perm):
                trial_inp[start + i] = inp_window[p]
            for i, p in enumerate(out_perm):
                trial_out[start + i] = out_window[p]

            m = compute_mse(trial_inp, trial_out, X, Y, pz)
            evals += 1
            if m < best_found_mse:
                best_found_mse = m
                best_found_inp = list(trial_inp)
                best_found_out = list(trial_out)
                print(f"    NEW BEST at sample: MSE={m:.6f}")

        print(f"  Phase 2 done: {evals} total evals, best={best_found_mse:.6f}")

    improvement = base_mse - best_found_mse
    print(f"\n  Region {region_name} result: {base_mse:.6f} → {best_found_mse:.6f} (delta={improvement:.6f})")

    # Save if improved
    if best_found_mse < base_mse:
        save_to_pool(best_found_inp, best_found_out, best_found_mse,
                     inp_indices, out_indices, last_idx,
                     f"surgery_{region_name}")
        return best_found_inp, best_found_out, best_found_mse
    else:
        print(f"  No improvement in region {region_name}")
        return base_inp, base_out, base_mse


def main():
    print("=" * 60)
    print("Break Point Surgery — Council Vote #91115ee2")
    print("=" * 60)

    pz, inp_indices, out_indices, last_idx = load_puzzle()
    X, Y = load_data(2000)

    # Get current best from pool
    best_inp, best_out, pool_mse = get_best_solution()
    print(f"Pool best MSE: {pool_mse:.6f}")

    # Verify
    verified_mse = compute_mse(best_inp, best_out, X, Y, pz)
    print(f"Verified MSE:  {verified_mse:.6f}")

    # Run surgery on each region, cascading improvements
    current_inp, current_out = best_inp, best_out
    for name, (start, end) in REGIONS.items():
        current_inp, current_out, _ = surgery_region(
            name, start, end, current_inp, current_out, X, Y, pz,
            inp_indices, out_indices, last_idx
        )

    # Final combined result
    final_mse = compute_mse(current_inp, current_out, X, Y, pz)
    print(f"\n{'='*60}")
    print(f"SURGERY COMPLETE")
    print(f"  Before: {pool_mse:.6f}")
    print(f"  After:  {final_mse:.6f}")
    print(f"  Delta:  {pool_mse - final_mse:.6f}")
    print(f"{'='*60}")

    # Save final combined result
    if final_mse < pool_mse:
        save_to_pool(current_inp, current_out, final_mse,
                     inp_indices, out_indices, last_idx,
                     "surgery_combined")


if __name__ == "__main__":
    main()
```

## Manual Step (TPM)

After Jr creates the file, run on redfin:
```text
cd /ganuda/experiments/jane-street/track2_permutation
/ganuda/home/dereadi/cherokee_venv/bin/python3 break_point_surgery.py
```

## Success Criteria
- Script reads best solution from PG pool
- Tries all local permutations at 3 break regions
- Injects any improvements back into the pool
- Reports delta for each region

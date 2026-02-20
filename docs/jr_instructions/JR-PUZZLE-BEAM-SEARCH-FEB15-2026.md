# Jr Instruction: Beam Search Solver for Jane Street Track 2

**Task ID**: PUZZLE-BEAM-001
**Priority**: 3 (MEDIUM)
**Assigned Jr**: Software Engineer Jr.
**Council Vote**: #440da232 (PROCEED WITH CAUTION, 0.793)
**use_rlm**: false

## Context

The current greedy solver uses width-1 search (pure greedy). A beam search with width 100 would explore exponentially more of the space near the beginning of the chain, where errors compound most. Total evals: 48 positions × 100 beams × 48 candidates = ~230K per position, ~11M total — tractable on a single core in minutes.

Fleet is at MSE 0.0341, target 0.0145.

## Objective

Create `/ganuda/experiments/jane-street/track2_permutation/beam_search_solver.py` — a script that:
1. Builds solutions position-by-position using beam search (width K)
2. At each position, evaluates all remaining candidates and keeps top-K partial solutions
3. Evaluates partial solutions by running through placed blocks + final layer
4. Injects best result into the PG pool

## Implementation

Create `/ganuda/experiments/jane-street/track2_permutation/beam_search_solver.py`

```python
#!/usr/bin/env python3
"""Beam Search Solver — Council Vote #440da232.

Position-by-position beam search with configurable width.
Evaluates partial solutions through placed blocks + final layer.
Dramatically better than width-1 greedy.
"""
import torch, numpy as np, json, psycopg2, hashlib, time, sys, heapq
from pathlib import Path

sys.path.insert(0, "/ganuda/lib")

BASE = Path("/ganuda/experiments/jane-street/track2_permutation")
N_BLOCKS = 48
TARGET_HASH = "093be1cf2d24094db903cbc3e8d33d306ebca49c6accaa264e44b0b675e7d9c4"

torch.set_num_threads(1)

BEAM_WIDTH = 100  # Keep top-100 partial solutions at each step


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


def compute_partial_mse(inp_partial, out_partial, X, Y, pz):
    """Compute MSE using only the placed blocks + final layer."""
    x = X.clone()
    for k in range(len(inp_partial)):
        h = torch.relu(x @ pz['W_inp'][inp_partial[k]].T + pz['b_inp'][inp_partial[k]])
        x = x + h @ pz['W_out'][out_partial[k]].T + pz['b_out'][out_partial[k]]
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


def beam_search_paired(pz, X, Y, beam_width=BEAM_WIDTH):
    """Beam search where inp and out are paired (same permutation).

    Each beam state: (mse, inp_placed, out_placed, used_inp, used_out)
    At each step, try all remaining (inp, out) pairs at the next position.
    """
    print(f"\n--- Beam Search (Paired, width={beam_width}) ---")
    n_samples = min(500, X.shape[0])
    X_sub, Y_sub = X[:n_samples], Y[:n_samples]

    # Initial beam: try all 48*48 combinations for position 0
    beam = []  # list of (mse, inp_list, out_list, used_inp_set, used_out_set)
    print("  Position 0: evaluating 2304 candidates...")

    candidates = []
    for ii in range(48):
        for oi in range(48):
            mse = compute_partial_mse([ii], [oi], X_sub, Y_sub, pz)
            candidates.append((mse, [ii], [oi], frozenset([ii]), frozenset([oi])))

    # Keep top beam_width
    candidates.sort(key=lambda x: x[0])
    beam = candidates[:beam_width]
    print(f"  Position 0 best: MSE={beam[0][0]:.6f}")

    # Extend beam position by position
    for pos in range(1, N_BLOCKS):
        new_beam = []
        for mse, inp_placed, out_placed, used_inp, used_out in beam:
            remaining_inp = [i for i in range(48) if i not in used_inp]
            remaining_out = [o for o in range(48) if o not in used_out]

            # Try all remaining (inp, out) pairs — or sample if too many
            pairs_to_try = []
            if len(remaining_inp) * len(remaining_out) <= 200:
                for ii in remaining_inp:
                    for oi in remaining_out:
                        pairs_to_try.append((ii, oi))
            else:
                # Sample to keep tractable
                import random
                for _ in range(200):
                    ii = random.choice(remaining_inp)
                    oi = random.choice(remaining_out)
                    pairs_to_try.append((ii, oi))

            for ii, oi in pairs_to_try:
                new_inp = inp_placed + [ii]
                new_out = out_placed + [oi]
                new_mse = compute_partial_mse(new_inp, new_out, X_sub, Y_sub, pz)
                new_beam.append((
                    new_mse, new_inp, new_out,
                    used_inp | {ii}, used_out | {oi}
                ))

        # Keep top beam_width
        new_beam.sort(key=lambda x: x[0])
        beam = new_beam[:beam_width]

        if (pos + 1) % 8 == 0 or pos == N_BLOCKS - 1:
            print(f"  Position {pos}: best partial MSE={beam[0][0]:.6f} ({len(new_beam)} candidates evaluated)")

    return beam[0][1], beam[0][2], beam[0][0]


def beam_search_independent(pz, X, Y, beam_width=BEAM_WIDTH):
    """Beam search where inp and out are ordered independently.

    First find best inp ordering, then best out ordering given inp.
    """
    print(f"\n--- Beam Search (Independent, width={beam_width}) ---")
    n_samples = min(500, X.shape[0])
    X_sub, Y_sub = X[:n_samples], Y[:n_samples]

    # Get pool best as starting point for the other half
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT inp_sigma, out_sigma FROM js_puzzle_pool ORDER BY full_mse ASC LIMIT 1")
    row = cur.fetchone()
    conn.close()
    pool_inp = list(row[0])
    pool_out = list(row[1])

    # Phase 1: Beam search for inp ordering (fix out to pool best)
    print("  Phase 1: Optimizing inp ordering...")
    beam = []
    for ii in range(48):
        inp_partial = [ii]
        out_partial = [pool_out[0]]  # Use pool's out for position 0
        mse = compute_partial_mse(inp_partial, out_partial, X_sub, Y_sub, pz)
        beam.append((mse, [ii], frozenset([ii])))

    beam.sort(key=lambda x: x[0])
    beam = beam[:beam_width]

    for pos in range(1, N_BLOCKS):
        new_beam = []
        for mse, inp_placed, used_inp in beam:
            remaining = [i for i in range(48) if i not in used_inp]
            for ii in remaining:
                new_inp = inp_placed + [ii]
                new_out = pool_out[:pos+1]
                new_mse = compute_partial_mse(new_inp, new_out, X_sub, Y_sub, pz)
                new_beam.append((new_mse, new_inp, used_inp | {ii}))

        new_beam.sort(key=lambda x: x[0])
        beam = new_beam[:beam_width]

        if (pos + 1) % 16 == 0:
            print(f"    Position {pos}: best={beam[0][0]:.6f}")

    best_inp = beam[0][1]
    print(f"  Best inp ordering partial MSE: {beam[0][0]:.6f}")

    # Phase 2: Beam search for out ordering (fix inp to best found)
    print("  Phase 2: Optimizing out ordering...")
    beam = []
    for oi in range(48):
        mse = compute_partial_mse([best_inp[0]], [oi], X_sub, Y_sub, pz)
        beam.append((mse, [oi], frozenset([oi])))

    beam.sort(key=lambda x: x[0])
    beam = beam[:beam_width]

    for pos in range(1, N_BLOCKS):
        new_beam = []
        for mse, out_placed, used_out in beam:
            remaining = [o for o in range(48) if o not in used_out]
            for oi in remaining:
                new_out = out_placed + [oi]
                new_mse = compute_partial_mse(best_inp[:pos+1], new_out, X_sub, Y_sub, pz)
                new_beam.append((new_mse, new_out, used_out | {oi}))

        new_beam.sort(key=lambda x: x[0])
        beam = new_beam[:beam_width]

        if (pos + 1) % 16 == 0:
            print(f"    Position {pos}: best={beam[0][0]:.6f}")

    best_out = beam[0][1]
    full_mse = compute_mse(best_inp, best_out, X, Y, pz)
    print(f"  Full MSE: {full_mse:.6f}")

    return best_inp, best_out, full_mse


def main():
    print("=" * 60)
    print("Beam Search Solver — Council Vote #440da232")
    print("=" * 60)

    pz, inp_indices, out_indices, last_idx = load_puzzle()
    X, Y = load_data(2000)

    # Get pool best for comparison
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT full_mse FROM js_puzzle_pool ORDER BY full_mse ASC LIMIT 1")
    pool_best = float(cur.fetchone()[0])
    conn.close()
    print(f"Pool best: {pool_best:.6f}")

    # Method 1: Paired beam search
    t0 = time.time()
    inp1, out1, mse1 = beam_search_paired(pz, X, Y, beam_width=50)
    print(f"  Time: {time.time()-t0:.0f}s")

    # Validate with full data
    full_mse1 = compute_mse(inp1, out1, X, Y, pz)
    print(f"  Full-data MSE: {full_mse1:.6f}")
    if full_mse1 < pool_best:
        save_to_pool(inp1, out1, full_mse1, inp_indices, out_indices, last_idx, "beam_paired")

    # Method 2: Independent beam search
    t0 = time.time()
    inp2, out2, mse2 = beam_search_independent(pz, X, Y, beam_width=50)
    print(f"  Time: {time.time()-t0:.0f}s")

    full_mse2 = compute_mse(inp2, out2, X, Y, pz)
    print(f"  Full-data MSE: {full_mse2:.6f}")
    if full_mse2 < pool_best:
        save_to_pool(inp2, out2, full_mse2, inp_indices, out_indices, last_idx, "beam_independent")

    # Summary
    print(f"\n{'='*60}")
    print(f"BEAM SEARCH RESULTS")
    print(f"  Pool best:  {pool_best:.6f}")
    print(f"  Paired:     {full_mse1:.6f}")
    print(f"  Independent: {full_mse2:.6f}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
```

## Manual Step (TPM)

After Jr creates the file, run on redfin:
```text
cd /ganuda/experiments/jane-street/track2_permutation
/ganuda/home/dereadi/cherokee_venv/bin/python3 beam_search_solver.py
```

## Success Criteria
- Beam search completes for both paired and independent modes
- Reports MSE comparison with pool best
- Injects any improvements into pool

# Jr Instruction: Trace-Based Pairing Solver — Hungarian Assignment

**Task**: Use `trace(W_out @ W_inp)` as the pairing cost function to find optimal inp-out pairing via Hungarian algorithm, then run SA on ordering only (48! space instead of (48!)^2).

**Council Vote**: #f242d61d (pairing problem)
**Kanban**: #1790 (Jane Street Track 2)
**Priority**: 1 (CRITICAL)

## Context

Inception analysis discovered that `trace(W_out @ W_inp)` is the strongest pairing signal:
- Correct pairings have trace mean = -6.98 (strongly negative)
- Random pairings have trace mean = -0.24 (near zero)
- Hungarian optimal matching by trace agrees with pool best on **38/48 pairs**
- This is 2x better than gradient MSE (19/48 pool matches)

The 10 disagreeing positions are likely where the pool is WRONG. If trace pairing is more correct, fixing these 10 positions could dramatically improve MSE.

Strategy: Lock trace-based pairings, run SA only on block ordering (48! search space — the "easy" half of the problem, same as the public 0.0145 solver).

## Step 1: Create the trace pairing solver

Create `/ganuda/experiments/jane-street/track2_permutation/trace_pairing_solver.py`

```python
#!/usr/bin/env python3
"""Trace-Based Pairing Solver — Hungarian assignment on trace(W_out @ W_inp).

The trace of W_out @ W_inp captures how well inp/out pieces fit together
algebraically. Correct pairings have strongly negative traces (mean -7),
random pairings are near zero.

Strategy:
1. Compute 48x48 trace matrix
2. Hungarian algorithm to find min-trace pairing (38/48 match pool best)
3. SA on ordering only (48! space) with FIXED pairings
4. Compare with pool best and hybrid solutions
"""
import torch, numpy as np, pandas as pd, json, psycopg2, hashlib, random, sys, argparse, time
from pathlib import Path
from scipy.optimize import linear_sum_assignment

sys.path.insert(0, "/ganuda/lib")

BASE = Path("/ganuda/experiments/jane-street/track2_permutation")
N_BLOCKS = 48

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
    return {
        'W_inp': W_inp, 'b_inp': b_inp,
        'W_out': W_out, 'b_out': b_out,
        'W_last': W_last, 'b_last': b_last,
    }, inp_indices, out_indices, last_idx


def load_data(n=2000):
    df = pd.read_csv(BASE / "historical_data.csv")
    data = torch.tensor(df.values, dtype=torch.float32)
    return data[:n, :48], data[:n, 48]


def compute_mse(inp_sigma, out_sigma, X, Y, pz):
    x = X.clone()
    for k in range(48):
        h = torch.relu(x @ pz['W_inp'][inp_sigma[k]].T + pz['b_inp'][inp_sigma[k]])
        x = x + h @ pz['W_out'][out_sigma[k]].T + pz['b_out'][out_sigma[k]]
    pred = x @ pz['W_last'].T + pz['b_last']
    return ((pred.squeeze() - Y) ** 2).mean().item()


def save_to_pool(inp_sigma, out_sigma, full_mse, inp_indices, out_indices, last_idx, tag):
    perm = [inp_indices[i] for i in inp_sigma] + [out_indices[j] for j in out_sigma] + [last_idx]
    h = hashlib.sha256(json.dumps(perm).encode()).hexdigest()
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO js_puzzle_pool (worker, inp_sigma, out_sigma, full_mse, perm_hash)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (perm_hash) DO NOTHING
        """, (tag, inp_sigma, out_sigma, full_mse, h))
        conn.commit()
        conn.close()
        print(f"  SAVED to pool: {full_mse:.6f} [{tag}]")
    except Exception as e:
        print(f"  DB save failed: {e}")


def compute_trace_matrix(pz):
    """Compute 48x48 trace matrix: trace(W_out_j @ W_inp_i) for all pairs."""
    n = 48
    trace_mat = np.zeros((n, n))
    for i in range(n):
        w_inp = pz['W_inp'][i].numpy()  # (96, 48)
        for j in range(n):
            w_out = pz['W_out'][j].numpy()  # (48, 96)
            trace_mat[i, j] = np.trace(w_out @ w_inp)
    return trace_mat


def hungarian_pairing(trace_mat):
    """Find optimal inp-out pairing by minimizing trace (most negative = best fit)."""
    row_ind, col_ind = linear_sum_assignment(trace_mat)
    pairing = {row_ind[i]: col_ind[i] for i in range(len(row_ind))}
    trace_sum = trace_mat[row_ind, col_ind].sum()
    return pairing, trace_sum


def ordering_sa(pz, X, Y, pairing, n_iters=200000, n_samples=1000,
                worker_id="trace", n_runs=20, inp_indices=None, out_indices=None, last_idx=None):
    """SA that searches ONLY ordering (48!) with FIXED pairings.

    This is the same approach the public 0.0145 solver used.
    Move types:
    - 60%: Adjacent swap
    - 25%: Random swap
    - 15%: 3-opt rotation
    """
    X_sub = X[:n_samples].float()
    Y_sub = Y[:n_samples].float()

    global_best_mse = float('inf')
    global_best_order = None

    for run in range(n_runs):
        run_start = time.time()

        # Generate ordering
        if run == 0:
            # Start with identity ordering
            order = list(range(48))
        elif run == 1:
            # Start with pool best ordering
            try:
                conn = get_db_conn()
                cur = conn.cursor()
                cur.execute("SELECT inp_sigma FROM js_puzzle_pool ORDER BY full_mse LIMIT 1")
                pool_order = list(cur.fetchone()[0])
                conn.close()
                order = pool_order
            except Exception:
                order = list(range(48))
                random.shuffle(order)
        else:
            # Random permutation
            order = list(range(48))
            random.shuffle(order)

        # Build sigma arrays from ordering + pairing
        inp_sigma = [order[k] for k in range(48)]
        out_sigma = [pairing[order[k]] for k in range(48)]

        cur_mse = compute_mse(inp_sigma, out_sigma, X_sub, Y_sub, pz)
        best_mse = cur_mse
        best_order = list(order)

        T = 0.05  # Low start — we expect good pairing
        decay = 0.99998
        accepted = 0

        for step in range(n_iters):
            trial_order = list(order)
            r = random.random()

            if r < 0.60:
                # Adjacent swap
                i = random.randint(0, 46)
                trial_order[i], trial_order[i+1] = trial_order[i+1], trial_order[i]
            elif r < 0.85:
                # Random swap
                i, j = random.sample(range(48), 2)
                trial_order[i], trial_order[j] = trial_order[j], trial_order[i]
            else:
                # 3-opt rotation
                positions = sorted(random.sample(range(48), 3))
                a, b, c = positions
                tmp = trial_order[a]
                trial_order[a] = trial_order[b]
                trial_order[b] = trial_order[c]
                trial_order[c] = tmp

            trial_inp = [trial_order[k] for k in range(48)]
            trial_out = [pairing[trial_order[k]] for k in range(48)]

            m = compute_mse(trial_inp, trial_out, X_sub, Y_sub, pz)
            delta = m - cur_mse

            if delta < 0 or random.random() < np.exp(-delta / max(T, 1e-10)):
                order = trial_order
                cur_mse = m
                accepted += 1

                if m < best_mse:
                    best_mse = m
                    best_order = list(order)

            T *= decay

            if step % 40000 == 0:
                rate = accepted / max(step, 1) * 100
                print(f"    step {step}: best={best_mse:.6f} cur={cur_mse:.6f} T={T:.6f} accept={rate:.1f}%")

        elapsed = time.time() - run_start
        print(f"  Run {run} done: best={best_mse:.6f} ({elapsed:.0f}s)")

        # Build final sigma arrays
        best_inp = [best_order[k] for k in range(48)]
        best_out = [pairing[best_order[k]] for k in range(48)]

        if best_mse < global_best_mse:
            global_best_mse = best_mse
            global_best_order = list(best_order)
            save_to_pool(best_inp, best_out, best_mse, inp_indices, out_indices, last_idx, worker_id)

    return global_best_order, global_best_mse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", default="trace-0")
    parser.add_argument("--iters", type=int, default=200000)
    parser.add_argument("--samples", type=int, default=1000)
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--hybrid", action="store_true",
                        help="Also try hybrid: trace pairing for 38 confident + pool for 10 uncertain")
    args = parser.parse_args()

    print(f"=== Trace Pairing Solver [{args.id}] ===")
    print(f"  iters={args.iters}, samples={args.samples}, runs={args.runs}")

    pz, inp_indices, out_indices, last_idx = load_puzzle()
    X, Y = load_data(2000)

    # Step 1: Compute trace matrix
    print("\nComputing trace matrix...")
    trace_mat = compute_trace_matrix(pz)
    print(f"  Trace stats: mean={trace_mat.mean():.4f}, std={trace_mat.std():.4f}")
    print(f"  Range: [{trace_mat.min():.4f}, {trace_mat.max():.4f}]")

    # Step 2: Hungarian pairing
    pairing, trace_sum = hungarian_pairing(trace_mat)
    print(f"\nHungarian pairing:")
    print(f"  Trace sum: {trace_sum:.4f}")

    # Compare with pool best
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT inp_sigma, out_sigma, full_mse FROM js_puzzle_pool ORDER BY full_mse LIMIT 1")
        row = cur.fetchone()
        conn.close()
        pool_inp, pool_out, pool_mse = list(row[0]), list(row[1]), float(row[2])
        pool_pairing = {pool_inp[k]: pool_out[k] for k in range(48)}

        match_count = sum(1 for k in pairing if pairing[k] == pool_pairing.get(k))
        print(f"  Pool best MSE: {pool_mse:.6f}")
        print(f"  Trace vs pool pairing agreement: {match_count}/48")

        # Show disagreements
        disagreements = [(k, pairing[k], pool_pairing.get(k)) for k in range(48) if pairing[k] != pool_pairing.get(k)]
        if disagreements:
            print(f"\n  Disagreements (inp_idx: trace_out vs pool_out):")
            for inp_k, trace_out, pool_out_k in disagreements:
                t_trace = trace_mat[inp_k, trace_out]
                t_pool = trace_mat[inp_k, pool_out_k] if pool_out_k is not None else 0
                print(f"    inp {inp_k:2d}: trace→out {trace_out:2d} ({t_trace:.2f}) vs pool→out {pool_out_k:2d} ({t_pool:.2f})")
    except Exception as e:
        print(f"  Could not compare with pool: {e}")
        pool_mse = float('inf')

    # Step 3: SA on ordering with trace pairings
    print(f"\n--- Phase 1: SA with PURE trace pairing ---")
    best_order, best_mse = ordering_sa(
        pz, X, Y, pairing,
        n_iters=args.iters, n_samples=args.samples,
        worker_id=f"{args.id}-pure", n_runs=args.runs,
        inp_indices=inp_indices, out_indices=out_indices, last_idx=last_idx
    )
    print(f"\nPure trace result: {best_mse:.6f}")

    # Step 4: Hybrid — use trace for confident pairs, pool for uncertain
    if args.hybrid and pool_mse < float('inf'):
        print(f"\n--- Phase 2: SA with HYBRID pairing (trace confident + pool uncertain) ---")
        hybrid_pairing = dict(pairing)  # Start with trace
        for k in range(48):
            # If pool and trace disagree AND the trace margin is small, use pool
            if pairing[k] != pool_pairing.get(k):
                trace_best = trace_mat[k, pairing[k]]
                trace_pool = trace_mat[k, pool_pairing[k]]
                margin = abs(trace_best - trace_pool) / abs(trace_best) if trace_best != 0 else 1
                if margin < 0.15:  # Less than 15% difference — uncertain
                    hybrid_pairing[k] = pool_pairing[k]

        hybrid_matches = sum(1 for k in hybrid_pairing if hybrid_pairing[k] == pool_pairing.get(k))
        print(f"  Hybrid uses {hybrid_matches}/48 pool pairings (rest from trace)")

        best_order_h, best_mse_h = ordering_sa(
            pz, X, Y, hybrid_pairing,
            n_iters=args.iters, n_samples=args.samples,
            worker_id=f"{args.id}-hybrid", n_runs=args.runs,
            inp_indices=inp_indices, out_indices=out_indices, last_idx=last_idx
        )
        print(f"\nHybrid result: {best_mse_h:.6f}")

    print(f"\n=== FINAL RESULTS ===")
    print(f"  Pool best: {pool_mse:.6f}")
    print(f"  Pure trace + SA: {best_mse:.6f}")
    if args.hybrid:
        print(f"  Hybrid + SA: {best_mse_h:.6f}")


if __name__ == "__main__":
    main()
```

## Expected Outcome

- Computes 48x48 trace matrix (no training data needed — pure weight analysis)
- Hungarian algorithm finds optimal pairing (expected: 38/48 match pool best)
- SA searches only ordering (48! space) — same approach as the public 0.0145 solver
- Hybrid mode: trace for confident pairs, pool for uncertain (where margin < 15%)
- 200K iterations per run, 20 runs = thorough search

## Testing

```text
cd /ganuda/experiments/jane-street/track2_permutation
/ganuda/home/dereadi/cherokee_venv/bin/python3 trace_pairing_solver.py --id trace-test --runs 2 --iters 50000
```

## Key Design Decisions

1. **Trace as cost function**: `trace(W_out @ W_inp)` captures algebraic fit. Correct pairs have trace ~-7, random ~0.
2. **Hungarian assignment**: Polynomial-time optimal matching (vs exponential enumeration).
3. **Ordering-only SA**: With fixed pairings, search space drops from (48!)^2 to 48!. This is what the public solver did.
4. **Lower temperature (T=0.05)**: With good pairings, we expect to start close to optimum.
5. **Adjacent swaps (60%)**: Since ordering is sequential, adjacent swaps are the most relevant local moves.
6. **Hybrid mode**: When trace and pool disagree by small margin, trust the pool (it was found by data-driven SA).

## Notes

- The 10 disagreeing positions between trace and pool could be the key to breaking through 0.030
- If pure trace SA beats pool, it means some of the pool's pairings are wrong
- If pool SA beats pure trace, it means the 10 wrong trace pairings are critical
- The hybrid approach hedges both bets
- Multiple instances can run in parallel with different `--id` values

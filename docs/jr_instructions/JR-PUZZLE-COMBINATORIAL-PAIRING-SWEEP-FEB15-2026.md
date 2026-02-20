# Jr Instruction: Combinatorial Pairing Sweep — Jane Street Track 2

**Task**: Create a script that exhaustively tests all valid pairing combinations for the 10 uncertain positions
**Priority**: 1 (CRITICAL — this may solve the puzzle)
**Kanban**: #1780
**Ultrathink**: ULTRATHINK-COMBINATORIAL-PAIRING-SWEEP-FEB15-2026.md

## Context

The trace pairing solver found 38/48 pairings that agree with the pool. The remaining 10 disagreements form **3 independent cycles**. For each cycle, we must use either ALL trace pairings or ALL pool pairings (mixing within a cycle creates an invalid permutation). This gives us **2^3 = 8 valid combinations**.

### The 3 Cycles

**Cycle A** (5 inputs): inp indices {6, 10, 21, 24, 30}
- Trace: 6→8, 10→42, 21→18, 24→3, 30→46
- Pool:  6→18, 10→8, 21→46, 24→42, 30→3

**Cycle B** (2 inputs): inp indices {18, 20}
- Trace: 18→20, 20→28
- Pool:  18→28, 20→20

**Cycle C** (3 inputs): inp indices {22, 32, 39}
- Trace: 22→41, 32→39, 39→16
- Pool:  22→39, 32→16, 39→41

### Solution Hash
```
SOLUTION_HASH = "093be1cf2d24094db903cbc3e8d33d306ebca49c6accaa264e44b0b675e7d9c4"
```

Hash is computed as: `hashlib.sha256(",".join(str(p) for p in permutation).encode()).hexdigest()`

Where `permutation` is the 97-element list of piece indices in execution order.

## Step 1: Create the sweep script

Create `/ganuda/experiments/jane-street/track2_permutation/pairing_sweep.py`

```python
#!/usr/bin/env python3
"""Combinatorial Pairing Sweep — exhaustively test all 8 valid pairing combinations.

The 10 uncertain pairings form 3 independent cycles. Each cycle must be
swapped atomically (all-trace or all-pool). 2^3 = 8 combinations total.
For each, run ordering-only SA and check SHA256 hash.
"""
import torch, numpy as np, pandas as pd, json, psycopg2, hashlib, random, sys, time, argparse
from pathlib import Path
from itertools import product

sys.path.insert(0, "/ganuda/lib")

BASE = Path("/ganuda/experiments/jane-street/track2_permutation")
N_BLOCKS = 48
SOLUTION_HASH = "093be1cf2d24094db903cbc3e8d33d306ebca49c6accaa264e44b0b675e7d9c4"

torch.set_num_threads(1)

# === The 3 cycles of disagreement ===
# Each entry: (inp_idx, trace_out, pool_out)
CYCLE_A = [(6, 8, 18), (10, 42, 8), (21, 18, 46), (24, 3, 42), (30, 46, 3)]
CYCLE_B = [(18, 20, 28), (20, 28, 20)]
CYCLE_C = [(22, 41, 39), (32, 39, 16), (39, 16, 41)]

# The 38 agreed pairings (trace == pool) — computed at runtime from trace matrix


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


def compute_trace_matrix(pz):
    n = 48
    trace_mat = np.zeros((n, n))
    for i in range(n):
        w_inp = pz['W_inp'][i].numpy()
        for j in range(n):
            w_out = pz['W_out'][j].numpy()
            trace_mat[i, j] = np.trace(w_out @ w_inp)
    return trace_mat


def build_base_pairing(trace_mat):
    """Build the 38 agreed pairings from Hungarian trace assignment."""
    from scipy.optimize import linear_sum_assignment
    row_ind, col_ind = linear_sum_assignment(trace_mat)
    trace_pairing = {int(row_ind[i]): int(col_ind[i]) for i in range(len(row_ind))}
    return trace_pairing


def build_combo_pairing(base_pairing, combo_bits):
    """Build full pairing for a given combination of cycle choices.

    combo_bits: tuple of 3 bools (cycle_a_use_pool, cycle_b_use_pool, cycle_c_use_pool)
    """
    pairing = dict(base_pairing)  # Start with trace (Hungarian) pairing

    cycles = [CYCLE_A, CYCLE_B, CYCLE_C]
    for cycle, use_pool in zip(cycles, combo_bits):
        if use_pool:
            for inp_idx, trace_out, pool_out in cycle:
                pairing[inp_idx] = pool_out
        # else: keep trace pairing (already in base)

    # Verify it's a valid permutation (all outs unique)
    outs = list(pairing.values())
    assert len(set(outs)) == 48, f"Invalid pairing: {len(set(outs))} unique outs"
    return pairing


def compute_mse(inp_sigma, out_sigma, X, Y, pz):
    x = X.clone()
    for k in range(48):
        h = torch.relu(x @ pz['W_inp'][inp_sigma[k]].T + pz['b_inp'][inp_sigma[k]])
        x = x + h @ pz['W_out'][out_sigma[k]].T + pz['b_out'][out_sigma[k]]
    pred = x @ pz['W_last'].T + pz['b_last']
    return ((pred.squeeze() - Y) ** 2).mean().item()


def check_hash(perm):
    perm_str = ",".join(str(int(p)) for p in perm)
    h = hashlib.sha256(perm_str.encode()).hexdigest()
    return h, h == SOLUTION_HASH


def ordering_sa(pz, X, Y, pairing, n_iters=200000, n_samples=2000,
                seed_order=None, n_runs=5):
    """SA on ordering only (48!) with fixed pairings."""
    X_sub = X[:n_samples].float()
    Y_sub = Y[:n_samples].float()

    global_best_mse = float('inf')
    global_best_order = None

    for run in range(n_runs):
        run_start = time.time()

        if run == 0 and seed_order is not None:
            order = list(seed_order)
        else:
            order = list(range(48))
            random.shuffle(order)

        inp_sigma = [order[k] for k in range(48)]
        out_sigma = [pairing[order[k]] for k in range(48)]
        cur_mse = compute_mse(inp_sigma, out_sigma, X_sub, Y_sub, pz)
        best_mse = cur_mse
        best_order = list(order)

        T = 0.05
        decay = 0.99998

        for step in range(n_iters):
            trial_order = list(order)
            r = random.random()

            if r < 0.60:
                i = random.randint(0, 46)
                trial_order[i], trial_order[i+1] = trial_order[i+1], trial_order[i]
            elif r < 0.85:
                i, j = random.sample(range(48), 2)
                trial_order[i], trial_order[j] = trial_order[j], trial_order[i]
            else:
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

                if m < best_mse:
                    best_mse = m
                    best_order = list(order)

            T *= decay

            if step % 50000 == 0:
                print(f"      step {step}: best={best_mse:.6f} cur={cur_mse:.6f} T={T:.6f}")

        elapsed = time.time() - run_start
        print(f"    Run {run}: best={best_mse:.6f} ({elapsed:.0f}s)")

        if best_mse < global_best_mse:
            global_best_mse = best_mse
            global_best_order = list(best_order)

    return global_best_order, global_best_mse


def save_to_pool(inp_sigma, out_sigma, full_mse, inp_indices, out_indices, last_idx, tag, hash_val, hash_match):
    inp_list = [int(x) for x in inp_sigma]
    out_list = [int(x) for x in out_sigma]
    perm = [inp_indices[i] for i in inp_list] + [out_indices[j] for j in out_list] + [last_idx]
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO js_puzzle_pool (worker, full_mse, inp_sigma, out_sigma, permutation, hash, hash_match) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (tag, float(full_mse), inp_list, out_list, perm, hash_val, hash_match)
        )
        conn.commit()
        conn.close()
        marker = " *** HASH MATCH! ***" if hash_match else ""
        print(f"  SAVED to pool: {full_mse:.6f} [{tag}]{marker}")
    except Exception as e:
        print(f"  DB save failed: {e}")


def get_pool_best_ordering():
    """Get the best ordering from pool to use as seed."""
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT inp_sigma FROM js_puzzle_pool ORDER BY full_mse LIMIT 1")
        row = cur.fetchone()
        conn.close()
        if row:
            return [int(x) for x in row[0]]
    except Exception:
        pass
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", default="sweep-0")
    parser.add_argument("--iters", type=int, default=200000)
    parser.add_argument("--samples", type=int, default=2000)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--combos", default="all", help="Which combos: 'all' or '0,1,2' etc")
    args = parser.parse_args()

    print(f"=== Combinatorial Pairing Sweep [{args.id}] ===")
    print(f"  iters={args.iters}, samples={args.samples}, runs={args.runs}")
    print(f"  Target hash: {SOLUTION_HASH[:16]}...")

    pz, inp_indices, out_indices, last_idx = load_puzzle()
    X, Y = load_data(args.samples)

    # Build base pairing from trace
    print("\nComputing trace matrix...")
    trace_mat = compute_trace_matrix(pz)
    base_pairing = build_base_pairing(trace_mat)

    # Get pool-best ordering as seed
    seed_order = get_pool_best_ordering()
    if seed_order:
        print(f"  Seeding from pool best ordering")
    else:
        print(f"  No pool seed available — using random starts")

    # Determine which combos to run
    all_combos = list(product([False, True], repeat=3))  # False=trace, True=pool
    if args.combos == "all":
        combo_indices = list(range(8))
    else:
        combo_indices = [int(x) for x in args.combos.split(",")]

    results = []

    for combo_idx in combo_indices:
        bits = all_combos[combo_idx]
        labels = ["TRACE" if not b else "POOL" for b in bits]
        print(f"\n{'='*60}")
        print(f"  Combo {combo_idx}: CycleA={labels[0]} CycleB={labels[1]} CycleC={labels[2]}")
        print(f"{'='*60}")

        pairing = build_combo_pairing(base_pairing, bits)

        best_order, best_mse = ordering_sa(
            pz, X, Y, pairing,
            n_iters=args.iters, n_samples=args.samples,
            seed_order=seed_order, n_runs=args.runs
        )

        # Build full permutation and check hash
        best_inp = [best_order[k] for k in range(48)]
        best_out = [pairing[best_order[k]] for k in range(48)]
        perm = [inp_indices[best_inp[k]] for k in range(48)] + \
               [out_indices[best_out[k]] for k in range(48)] + [last_idx]

        hash_val, hash_match = check_hash(perm)

        results.append({
            'combo': combo_idx,
            'bits': bits,
            'labels': labels,
            'mse': best_mse,
            'hash': hash_val[:16],
            'match': hash_match,
            'order': best_order,
            'inp_sigma': best_inp,
            'out_sigma': best_out,
        })

        tag = f"{args.id}-combo{combo_idx}"
        save_to_pool(best_inp, best_out, best_mse, inp_indices, out_indices, last_idx,
                     tag, hash_val, hash_match)

        if hash_match:
            print(f"\n{'*'*60}")
            print(f"  *** SHA256 HASH MATCH! PUZZLE SOLVED! ***")
            print(f"  Combo {combo_idx}: {labels}")
            print(f"  MSE: {best_mse:.10f}")
            print(f"  Hash: {hash_val}")
            print(f"{'*'*60}")
            # Save solution to file
            with open(BASE / "SOLUTION.json", "w") as f:
                json.dump({
                    'permutation': [int(p) for p in perm],
                    'hash': hash_val,
                    'mse': best_mse,
                    'combo': combo_idx,
                    'cycle_choices': labels,
                    'inp_sigma': [int(x) for x in best_inp],
                    'out_sigma': [int(x) for x in best_out],
                }, f, indent=2)
            print(f"  Solution saved to {BASE / 'SOLUTION.json'}")

    # Summary table
    print(f"\n{'='*60}")
    print(f"  SWEEP RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"  {'Combo':>5} {'CycA':>5} {'CycB':>5} {'CycC':>5} {'MSE':>12} {'Hash':>18} {'Match':>6}")
    print(f"  {'-'*5:>5} {'-'*5:>5} {'-'*5:>5} {'-'*5:>5} {'-'*12:>12} {'-'*18:>18} {'-'*6:>6}")
    for r in sorted(results, key=lambda x: x['mse']):
        print(f"  {r['combo']:>5} {r['labels'][0]:>5} {r['labels'][1]:>5} {r['labels'][2]:>5} "
              f"{r['mse']:>12.6f} {r['hash']:>18} {'YES!!' if r['match'] else 'no':>6}")

    best = min(results, key=lambda x: x['mse'])
    print(f"\n  Best: Combo {best['combo']} MSE={best['mse']:.6f} "
          f"(CycA={best['labels'][0]} CycB={best['labels'][1]} CycC={best['labels'][2]})")

    if any(r['match'] for r in results):
        print(f"\n  *** PUZZLE SOLVED! See SOLUTION.json ***")
    else:
        print(f"\n  No hash match. Best MSE: {best['mse']:.6f}")
        print(f"  Next step: Try longer SA runs or investigate if agreed pairings are wrong")


if __name__ == "__main__":
    main()
```

## Step 2: Create Mac variant

Create `/ganuda/experiments/jane-street/track2_permutation/pairing_sweep_mac.py`

This is the same script as Step 1, but with all paths changed:
- `/ganuda/experiments/jane-street/track2_permutation` → `/Users/Shared/ganuda/experiments/jane-street/track2_permutation`
- `/ganuda/lib` → `/Users/Shared/ganuda/lib`

## Notes

- The script tests all 8 valid pairing combinations (3 independent cycles × 2 choices each)
- Each combination gets 5 SA runs of 200K steps with 2000 samples
- Pool-best ordering used as seed for run 0 of each combination
- SHA256 hash checked after every run — if it matches, writes SOLUTION.json
- Results saved to js_puzzle_pool with worker tag "sweep-{combo_id}"
- The `--combos` flag allows splitting work: `--combos 0,1,2,3` on one node, `--combos 4,5,6,7` on another
- Use `PYTHONUNBUFFERED=1 python3 -u` for log visibility

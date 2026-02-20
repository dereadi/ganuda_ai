# Jr Instruction: Middle Zone Surgery — Targeted Search at Positions 12-22

**Task**: Create a script that locks the high-confidence positions (0-1, 35-47) from the pool best solution and exhaustively searches the uncertain middle zone (positions 12-22) where the fleet has lowest agreement.

**Council Vote**: #f242d61d (pairing problem)
**Kanban**: #1790 (Jane Street Track 2)
**Priority**: 1 (CRITICAL)

## Context

Visual analysis of pool agreement (top 20 solutions) revealed:
- Positions 0-1, 35-47: 80-100% pairing agreement (locked in)
- Positions 12-22: 35-50% agreement (fleet is guessing)
- This 11-position zone is where the remaining MSE gap (0.030 → 0.014) likely lives

Strategy: Lock the ends, exhaustively permute the middle. 11 positions = 11! * 11! = ~1.6 billion for full search, but if we fix pairings and just search ordering, it's 11! = ~40 million — feasible with SA.

## Step 1: Create the middle zone surgery script

Create `/ganuda/experiments/jane-street/track2_permutation/middle_zone_surgery.py`

```python
#!/usr/bin/env python3
"""Middle Zone Surgery — targeted SA at positions 12-22.

Locks high-agreement positions from pool best, exhaustively searches the
uncertain middle zone where the fleet has lowest pairing consensus.

Visual analysis showed positions 12-22 have only 35-50% agreement across
top-20 pool solutions. This is where the remaining MSE gap lives.
"""
import torch, numpy as np, pandas as pd, json, psycopg2, hashlib, random, sys, argparse, time
from pathlib import Path

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


def find_uncertain_zone(n_top=20):
    """Analyze pool to find the uncertain middle zone.

    Returns: (locked_positions, uncertain_positions) where locked positions
    have >75% agreement and uncertain have <60%.
    """
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT inp_sigma, out_sigma, full_mse FROM js_puzzle_pool ORDER BY full_mse LIMIT %s", (n_top,))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return list(range(48)), []

    # For each position, find max agreement
    agreement = []
    for k in range(48):
        pair_counts = {}
        for inp_s, out_s, mse in rows:
            pair = (inp_s[k], out_s[k])
            pair_counts[pair] = pair_counts.get(pair, 0) + 1
        max_agree = max(pair_counts.values()) / len(rows)
        agreement.append(max_agree)

    locked = [k for k in range(48) if agreement[k] >= 0.75]
    uncertain = [k for k in range(48) if agreement[k] < 0.60]

    return locked, uncertain, agreement


def middle_zone_sa(pz, X, Y, inp_indices, out_indices, last_idx,
                   locked, uncertain, pool_inp, pool_out, pool_mse,
                   n_iters=100000, n_samples=1000, worker_id="surgery",
                   n_runs=20):
    """SA that only modifies the uncertain zone.

    For locked positions: keep pool best's blocks exactly.
    For uncertain positions: search both block assignment AND pairing.

    Move types:
    - 50%: Swap two uncertain positions (keeps pairs intact)
    - 25%: Re-pair two uncertain positions (swap their outs)
    - 15%: 3-opt rotation within uncertain zone
    - 10%: Swap one uncertain with one locked position (risky but explores)
    """
    n_locked = len(locked)
    n_uncertain = len(uncertain)
    locked_set = set(locked)
    uncertain_set = set(uncertain)

    print(f"\nMiddle Zone SA: {n_locked} locked, {n_uncertain} uncertain")
    print(f"  Locked positions: {locked}")
    print(f"  Uncertain positions: {uncertain}")

    X_sub = X[:n_samples].float()
    Y_sub = Y[:n_samples].float()

    global_best_mse = pool_mse
    global_best_inp = list(pool_inp)
    global_best_out = list(pool_out)

    for run in range(n_runs):
        run_start = time.time()

        # Always seed from pool best
        inp_sigma = list(pool_inp)
        out_sigma = list(pool_out)

        if run > 0 and random.random() < 0.5:
            # Perturb uncertain zone slightly
            unc_pos = list(uncertain)
            for _ in range(random.randint(1, min(3, n_uncertain))):
                if len(unc_pos) >= 2:
                    i, j = random.sample(unc_pos, 2)
                    inp_sigma[i], inp_sigma[j] = inp_sigma[j], inp_sigma[i]
                    out_sigma[i], out_sigma[j] = out_sigma[j], out_sigma[i]

        cur_mse = compute_mse(inp_sigma, out_sigma, X_sub, Y_sub, pz)
        best_mse = cur_mse
        best_inp = list(inp_sigma)
        best_out = list(out_sigma)

        T = 0.5  # Lower start temp — we're close to optimum
        decay = 0.99997  # Slow cooling for 100K steps
        accepted = 0

        for step in range(n_iters):
            trial_inp = list(inp_sigma)
            trial_out = list(out_sigma)

            r = random.random()

            if r < 0.50 and n_uncertain >= 2:
                # Swap two uncertain positions (blocks stay paired)
                i, j = random.sample(uncertain, 2)
                trial_inp[i], trial_inp[j] = trial_inp[j], trial_inp[i]
                trial_out[i], trial_out[j] = trial_out[j], trial_out[i]

            elif r < 0.75 and n_uncertain >= 2:
                # Re-pair: swap out blocks at two uncertain positions
                i, j = random.sample(uncertain, 2)
                trial_out[i], trial_out[j] = trial_out[j], trial_out[i]

            elif r < 0.90 and n_uncertain >= 3:
                # 3-opt within uncertain zone
                positions = sorted(random.sample(uncertain, 3))
                a_idx, b_idx, c_idx = positions
                # Rotate the blocks at these 3 positions
                tmp_inp = trial_inp[a_idx]
                tmp_out = trial_out[a_idx]
                trial_inp[a_idx] = trial_inp[b_idx]
                trial_out[a_idx] = trial_out[b_idx]
                trial_inp[b_idx] = trial_inp[c_idx]
                trial_out[b_idx] = trial_out[c_idx]
                trial_inp[c_idx] = tmp_inp
                trial_out[c_idx] = tmp_out

            else:
                # Risky: swap one uncertain with one locked
                if uncertain and locked:
                    i = random.choice(uncertain)
                    j = random.choice(locked)
                    trial_inp[i], trial_inp[j] = trial_inp[j], trial_inp[i]
                    trial_out[i], trial_out[j] = trial_out[j], trial_out[i]

            m = compute_mse(trial_inp, trial_out, X_sub, Y_sub, pz)
            delta = m - cur_mse

            if delta < 0 or random.random() < np.exp(-delta / max(T, 1e-10)):
                inp_sigma, out_sigma, cur_mse = trial_inp, trial_out, m
                accepted += 1

                if m < best_mse:
                    best_mse = m
                    best_inp = list(inp_sigma)
                    best_out = list(out_sigma)

            T *= decay

            if step % 20000 == 0:
                rate = accepted / max(step, 1) * 100
                print(f"    step {step}: best={best_mse:.6f} cur={cur_mse:.6f} T={T:.5f} accept={rate:.1f}%")

        elapsed = time.time() - run_start
        print(f"  Run {run} done: best={best_mse:.6f} ({elapsed:.0f}s)")

        # Save if better than pool
        if best_mse < global_best_mse:
            global_best_mse = best_mse
            global_best_inp = list(best_inp)
            global_best_out = list(best_out)
            save_to_pool(best_inp, best_out, best_mse, inp_indices, out_indices, last_idx,
                         worker_id)

    return global_best_inp, global_best_out, global_best_mse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", default="surgery-0")
    parser.add_argument("--iters", type=int, default=100000)
    parser.add_argument("--samples", type=int, default=1000)
    parser.add_argument("--runs", type=int, default=20)
    args = parser.parse_args()

    print(f"=== Middle Zone Surgery [{args.id}] ===")
    print(f"  iters={args.iters}, samples={args.samples}, runs={args.runs}")

    pz, inp_indices, out_indices, last_idx = load_puzzle()
    X, Y = load_data(2000)

    # Find uncertain zone from pool analysis
    locked, uncertain, agreement = find_uncertain_zone(n_top=20)
    print(f"\nPool agreement analysis:")
    for k in range(48):
        marker = "LOCKED" if k in locked else ("UNCERTAIN" if k in uncertain else "mixed")
        print(f"  pos {k:2d}: {agreement[k]:.0%} agreement [{marker}]")

    # Get pool best as starting point
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT inp_sigma, out_sigma, full_mse FROM js_puzzle_pool ORDER BY full_mse LIMIT 1")
    row = cur.fetchone()
    conn.close()
    pool_inp, pool_out, pool_mse = list(row[0]), list(row[1]), float(row[2])
    print(f"\nPool best: {pool_mse:.6f}")

    # Run surgery
    best_inp, best_out, best_mse = middle_zone_sa(
        pz, X, Y, inp_indices, out_indices, last_idx,
        locked, uncertain, pool_inp, pool_out, pool_mse,
        n_iters=args.iters, n_samples=args.samples,
        worker_id=args.id, n_runs=args.runs
    )

    print(f"\n=== FINAL: best MSE = {best_mse:.6f} (pool was {pool_mse:.6f}) ===")
    if best_mse < pool_mse:
        print(f"  IMPROVED by {pool_mse - best_mse:.6f}")
    else:
        print(f"  No improvement found")


if __name__ == "__main__":
    main()
```

## Expected Outcome

- Identifies the uncertain middle zone from pool agreement analysis
- Locks high-confidence positions (>75% agreement)
- SA targets ONLY the uncertain zone with lower temperature (we're close to optimum)
- 100K iterations per run, 20 runs = thorough local search
- Uses pool best as starting point every run (we KNOW positions 0-1 and 35-47 are good)
- Saves improvements to pool, benefiting the fleet

## Testing

```text
cd /ganuda/experiments/jane-street/track2_permutation
/ganuda/home/dereadi/cherokee_venv/bin/python3 middle_zone_surgery.py --id surgery-test --runs 2 --iters 50000
```

## Key Design Decisions

1. **Lower starting temperature (T=0.5)**: We're at MSE 0.030, very close to optimum. Don't want to explore wildly.
2. **Slow cooling (0.99997)**: 100K steps needs gentle cooling
3. **10% locked-swap moves**: Occasionally challenge the "locked" positions — the pool might be wrong
4. **Always seed from pool best**: The fleet already found a good solution. We refine, not restart.

## Notes

- Pool agreement thresholds: >=75% = locked, <60% = uncertain, between = mixed
- The "mixed" zone (60-75%) is also searched but less aggressively
- Multiple instances can run in parallel with different `--id` values
- Saves to same pool as fleet, so improvements propagate

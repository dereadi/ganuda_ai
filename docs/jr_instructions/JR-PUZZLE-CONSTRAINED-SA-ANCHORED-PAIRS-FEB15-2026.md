# Jr Instruction: Constrained SA with Anchored Pairs

**Task**: Create a new SA variant that anchors the 32 high-confidence inp/out pairs from gradient MSE analysis while letting SA search ordering + the 16 uncertain pairings.

**Council Vote**: #f242d61d (pairing problem deliberation)
**Kanban**: #1790 (Jane Street Track 2)
**Priority**: 2 (HIGH)
**Depends on**: `mse_greedy_pairing.py` gradient cost matrix results

## Context

The MSE-based greedy pairing analysis (Jr #766) found that gradient MSE (single-block forward pass through final layer) produces **32/48 mutual best matches** — pairs where inp_i's best out is out_j AND out_j's best inp is inp_i. However, fixing ALL 48 pairs and SA'ing only ordering gave MSE 0.428 (worse than pool at 0.030). The 16 wrong pairs are too toxic.

**Key insight**: Anchor the 32 high-confidence pairs as soft constraints. Let SA search both ordering AND the 16 uncertain pairings. This reduces effective search from (48!)^2 to approximately 48! * 16! — still huge but orders of magnitude smaller.

## Step 1: Create the constrained SA script

Create `/ganuda/experiments/jane-street/track2_permutation/constrained_sa.py`

```python
#!/usr/bin/env python3
"""Constrained SA with Anchored Pairs.

Uses gradient MSE cost matrix to identify high-confidence (inp, out) pairs.
Anchors those pairs as soft constraints while SA searches ordering + uncertain pairings.

Pool: shares via PostgreSQL js_puzzle_pool (same as fleet).
"""
import torch, numpy as np, json, psycopg2, hashlib, random, sys, argparse, time
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
    data = torch.load(BASE / "data/data.pth", map_location='cpu', weights_only=True)
    X = data['X'][:n].float()
    Y = data['Y'][:n].float()
    return X, Y


def compute_mse(inp_sigma, out_sigma, X, Y, pz):
    x = X.clone()
    for k in range(48):
        h = torch.relu(x @ pz['W_inp'][inp_sigma[k]].T + pz['b_inp'][inp_sigma[k]])
        x = x + h @ pz['W_out'][out_sigma[k]].T + pz['b_out'][out_sigma[k]]
    pred = x @ pz['W_last'].T + pz['b_last']
    return ((pred.squeeze() - Y) ** 2).mean().item()


def compute_gradient_cost_matrix(pz, X, Y):
    """Compute 48x48 gradient MSE cost matrix.

    For each (inp_i, out_j) pair, run single block + final layer → MSE.
    This is the signal that found 32/48 mutual best matches.
    """
    n = min(500, X.shape[0])
    X_sub = X[:n]
    Y_sub = Y[:n]

    cost = np.zeros((48, 48))
    for ii in range(48):
        h = torch.relu(X_sub @ pz['W_inp'][ii].T + pz['b_inp'][ii])
        for oi in range(48):
            residual = h @ pz['W_out'][oi].T + pz['b_out'][oi]
            x_out = X_sub + residual
            pred = x_out @ pz['W_last'].T + pz['b_last']
            mse = ((pred.squeeze() - Y_sub) ** 2).mean().item()
            cost[ii, oi] = mse

    return cost


def find_anchored_pairs(cost, threshold_ratio=1.5):
    """Find mutual best pairs where both sides strongly prefer each other.

    A pair (i, j) is anchored if:
    1. j = argmin(cost[i, :])  (j is best out for inp i)
    2. i = argmin(cost[:, j])  (i is best inp for out j)
    3. The margin is significant: second_best / best > threshold_ratio

    Returns:
        anchored: dict {inp_idx: out_idx} for high-confidence pairs
        uncertain_inp: list of inp indices without confident pairing
        uncertain_out: list of out indices without confident pairing
    """
    anchored = {}

    for i in range(48):
        best_j = np.argmin(cost[i])
        best_i_for_j = np.argmin(cost[:, best_j])

        if best_i_for_j == i:
            # Mutual best match — check margin
            sorted_row = np.sort(cost[i])
            sorted_col = np.sort(cost[:, best_j])

            row_margin = sorted_row[1] / max(sorted_row[0], 1e-10)
            col_margin = sorted_col[1] / max(sorted_col[0], 1e-10)

            # Both directions should have decent margins
            if row_margin > threshold_ratio and col_margin > threshold_ratio:
                anchored[i] = int(best_j)

    anchored_inps = set(anchored.keys())
    anchored_outs = set(anchored.values())
    uncertain_inp = [i for i in range(48) if i not in anchored_inps]
    uncertain_out = [j for j in range(48) if j not in anchored_outs]

    return anchored, uncertain_inp, uncertain_out


def save_to_pool(inp_sigma, out_sigma, full_mse, inp_indices, out_indices, last_idx, tag):
    perm = [inp_indices[i] for i in inp_sigma] + [out_indices[j] for j in out_sigma] + [last_idx]
    h = hashlib.sha256(json.dumps(perm).encode()).hexdigest()
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO js_puzzle_pool (worker_id, inp_sigma, out_sigma, full_mse, perm_hash)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (perm_hash) DO NOTHING
        """, (tag, inp_sigma, out_sigma, full_mse, h))
        conn.commit()
        conn.close()
        print(f"  SAVED to pool: {full_mse:.6f} [{tag}]")
    except Exception as e:
        print(f"  DB save failed: {e}")


def get_pool_best(conn):
    """Get pool best for seeding."""
    cur = conn.cursor()
    cur.execute("SELECT inp_sigma, out_sigma, full_mse FROM js_puzzle_pool ORDER BY full_mse LIMIT 1")
    row = cur.fetchone()
    if row:
        return list(row[0]), list(row[1]), float(row[2])
    return None, None, float('inf')


def constrained_sa(pz, X, Y, inp_indices, out_indices, last_idx,
                   anchored, uncertain_inp, uncertain_out,
                   n_iters=50000, n_samples=1000, worker_id="constrained",
                   n_runs=10, pool_threshold=0.5):
    """SA that respects anchored pairs.

    State: (ordering[48], pairing[48])
    - Anchored pairs stay together always
    - Uncertain pairs can be re-paired
    - All positions can be reordered

    Move types:
    - 60%: Swap two block positions (keeps pairs intact)
    - 20%: Re-pair two uncertain blocks (swap their outs)
    - 15%: 3-opt rotation of consecutive block positions
    - 5%: Relocate a block to a different position
    """
    n_anchored = len(anchored)
    n_uncertain = len(uncertain_inp)
    print(f"\nConstrained SA: {n_anchored} anchored, {n_uncertain} uncertain")
    print(f"  Effective search: 48! * {n_uncertain}! (vs full (48!)^2)")

    X_sub = X[:n_samples].float()
    Y_sub = Y[:n_samples].float()

    for run in range(n_runs):
        run_start = time.time()

        # Seed from pool or random
        conn = get_db_conn()
        pool_inp, pool_out, pool_mse = get_pool_best(conn)
        conn.close()

        if pool_inp and random.random() < 0.4:
            # Start from pool best
            inp_sigma = list(pool_inp)
            out_sigma = list(pool_out)
            print(f"\n  Run {run}: seeded from pool ({pool_mse:.6f})")
        else:
            # Build initial state: anchored pairs first, then random uncertain
            order = list(range(48))
            random.shuffle(order)

            # Build pairing: anchored are fixed, uncertain are random
            uncertain_out_shuffled = list(uncertain_out)
            random.shuffle(uncertain_out_shuffled)
            pairing = dict(anchored)
            for i, j in zip(uncertain_inp, uncertain_out_shuffled):
                pairing[i] = j

            inp_sigma = [order[k] for k in range(48)]
            out_sigma = [pairing[inp_sigma[k]] for k in range(48)]
            print(f"\n  Run {run}: random start (anchored={n_anchored})")

        cur_mse = compute_mse(inp_sigma, out_sigma, X_sub, Y_sub, pz)
        best_mse = cur_mse
        best_inp = list(inp_sigma)
        best_out = list(out_sigma)

        T_start = 3.0
        T = T_start
        decay = 0.99994
        accepted = 0

        for step in range(n_iters):
            trial_inp = list(inp_sigma)
            trial_out = list(out_sigma)

            r = random.random()

            if r < 0.6:
                # Swap two block positions (pairs stay intact)
                i, j = random.sample(range(48), 2)
                trial_inp[i], trial_inp[j] = trial_inp[j], trial_inp[i]
                trial_out[i], trial_out[j] = trial_out[j], trial_out[i]

            elif r < 0.8 and n_uncertain >= 2:
                # Re-pair two uncertain blocks
                # Find positions of uncertain inp blocks
                unc_positions = [k for k in range(48) if trial_inp[k] in uncertain_inp]
                if len(unc_positions) >= 2:
                    pi, pj = random.sample(unc_positions, 2)
                    # Swap their out blocks (re-pair)
                    trial_out[pi], trial_out[pj] = trial_out[pj], trial_out[pi]
                else:
                    # Fallback to swap
                    i, j = random.sample(range(48), 2)
                    trial_inp[i], trial_inp[j] = trial_inp[j], trial_inp[i]
                    trial_out[i], trial_out[j] = trial_out[j], trial_out[i]

            elif r < 0.95:
                # 3-opt rotation
                pts = sorted(random.sample(range(48), 3))
                a, b, c = pts
                trial_inp = trial_inp[:a] + trial_inp[b:c] + trial_inp[a:b] + trial_inp[c:]
                trial_out = trial_out[:a] + trial_out[b:c] + trial_out[a:b] + trial_out[c:]

            else:
                # Relocate block
                src = random.randint(0, 47)
                dst = random.randint(0, 47)
                if src != dst:
                    vi = trial_inp.pop(src)
                    vo = trial_out.pop(src)
                    trial_inp.insert(dst, vi)
                    trial_out.insert(dst, vo)

            m = compute_mse(trial_inp, trial_out, X_sub, Y_sub, pz)
            delta = m - cur_mse

            if delta < 0 or random.random() < np.exp(-delta / max(T, 1e-10)):
                inp_sigma, out_sigma, cur_mse = trial_inp, trial_out, m
                accepted += 1

                if m < best_mse:
                    best_mse = m
                    best_inp = list(inp_sigma)
                    best_out = list(out_sigma)

                    # Save improvements to pool
                    if m < pool_mse * pool_threshold:
                        save_to_pool(best_inp, best_out, m, inp_indices, out_indices, last_idx,
                                     worker_id)

            T *= decay

            if step % 10000 == 0:
                rate = accepted / max(step, 1) * 100
                print(f"    step {step}: best={best_mse:.6f} cur={cur_mse:.6f} T={T:.4f} accept={rate:.1f}%")

        elapsed = time.time() - run_start
        print(f"  Run {run} done: best={best_mse:.6f} ({elapsed:.0f}s)")

        # Always save if better than pool
        if best_mse < pool_mse:
            save_to_pool(best_inp, best_out, best_mse, inp_indices, out_indices, last_idx,
                         worker_id)
            # Refresh pool best
            conn = get_db_conn()
            _, _, pool_mse = get_pool_best(conn)
            conn.close()

    return best_inp, best_out, best_mse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", default="constrained-0")
    parser.add_argument("--iters", type=int, default=50000)
    parser.add_argument("--samples", type=int, default=1000)
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--margin", type=float, default=1.3,
                        help="Threshold ratio for anchor confidence (default 1.3 = 30% margin)")
    parser.add_argument("--pool-threshold", type=float, default=1.0)
    args = parser.parse_args()

    print(f"=== Constrained SA [{args.id}] ===")
    print(f"  margin={args.margin}, iters={args.iters}, samples={args.samples}, runs={args.runs}")

    pz, inp_indices, out_indices, last_idx = load_puzzle()
    X, Y = load_data(2000)

    # Compute gradient cost matrix
    print("\nComputing gradient MSE cost matrix (48x48)...")
    cost = compute_gradient_cost_matrix(pz, X, Y)

    # Find anchored pairs at various thresholds
    for t in [2.0, 1.5, 1.3, 1.1]:
        anch, unc_i, unc_o = find_anchored_pairs(cost, threshold_ratio=t)
        print(f"  threshold={t:.1f}: {len(anch)} anchored, {len(unc_i)} uncertain")

    # Use the requested margin
    anchored, uncertain_inp, uncertain_out = find_anchored_pairs(cost, threshold_ratio=args.margin)
    print(f"\nUsing margin={args.margin}: {len(anchored)} anchored pairs")

    # Show the anchored pairs
    for i, j in sorted(anchored.items()):
        row_best = cost[i].min()
        row_second = np.partition(cost[i], 1)[1]
        print(f"  inp[{i:2d}] → out[{j:2d}]  (margin: {row_second/row_best:.2f}x)")

    # Run constrained SA
    best_inp, best_out, best_mse = constrained_sa(
        pz, X, Y, inp_indices, out_indices, last_idx,
        anchored, uncertain_inp, uncertain_out,
        n_iters=args.iters, n_samples=args.samples,
        worker_id=args.id, n_runs=args.runs,
        pool_threshold=args.pool_threshold
    )

    print(f"\n=== FINAL: best MSE = {best_mse:.6f} ===")


if __name__ == "__main__":
    main()
```

## Expected Outcome

- Script computes 48x48 gradient cost matrix (~2 min)
- Identifies anchored pairs at configurable margin thresholds
- Runs SA with both ordering moves (swap, 3-opt, relocate) AND pairing moves (re-pair uncertain blocks)
- Shares improvements to pool like the regular fleet
- Multiple instances can run in parallel with different `--id` and `--margin` values

## Testing

Run on redfin:
```text
cd /ganuda/experiments/jane-street/track2_permutation
/ganuda/home/dereadi/cherokee_venv/bin/python3 constrained_sa.py --id constrained-test --runs 2 --margin 1.3
```

## Notes

- The gradient cost matrix computation takes ~2min (48*48 = 2304 forward passes)
- At margin 1.3, expect ~25-30 anchored pairs (from the 32 mutual best)
- At margin 1.1, expect all 32 mutual best to be anchored
- The fleet at 0.030 has been stale >1hr — this is the strategic intervention
- Saves to same pool, so regular fleet workers benefit from any improvements

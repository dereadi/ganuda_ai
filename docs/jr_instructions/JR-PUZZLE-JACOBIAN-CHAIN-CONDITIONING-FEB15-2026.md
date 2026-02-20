# Jr Instruction: True Jacobian Chain Conditioning for Jane Street Track 2

**Task ID**: PUZZLE-JACOBIAN-CHAIN-001
**Priority**: 1 (CRITICAL)
**Assigned Jr**: Software Engineer Jr.
**Council Vote**: #440da232 (PROCEED WITH CAUTION, 0.793)
**use_rlm**: false

## Context

The public solver achieved MSE 0.0145 using "Jacobian-based gradient ordering." Our current Jacobian seeder (Jr #759) only computed scalar Frobenius norms — it missed the key insight: **matrix composition is non-commutative**. The order in which Jacobians multiply matters. We need to compute full 48x48 Jacobian matrices and measure how well they compose pairwise.

Fleet is at MSE 0.0341, target 0.0145. This technique is the most likely to close the gap.

## Objective

Create `/ganuda/experiments/jane-street/track2_permutation/jacobian_chain_solver.py` — a script that:
1. Computes the full 48x48 Jacobian matrix for each residual block on sample data
2. Builds a pairwise "transition cost" matrix measuring composition quality
3. Solves the resulting asymmetric TSP to find optimal ordering
4. Injects the result into the PG pool

## Implementation

Create `/ganuda/experiments/jane-street/track2_permutation/jacobian_chain_solver.py`

```python
#!/usr/bin/env python3
"""True Jacobian Chain Conditioning — Council Vote #440da232.

For each residual block F_k(x) = x + W_out_k @ relu(W_inp_k @ x + b_inp_k) + b_out_k,
the Jacobian is J_k = I + W_out_k @ diag(relu'(z_k)) @ W_inp_k.

The correct ordering should produce a well-conditioned chain of Jacobian products.
We compute pairwise transition costs C(i,j) = condition_number(J_j @ J_i)
and solve as asymmetric TSP using nearest-neighbor + 2-opt.
"""
import torch, numpy as np, json, psycopg2, hashlib, time, sys
from pathlib import Path

sys.path.insert(0, "/ganuda/lib")

BASE = Path("/ganuda/experiments/jane-street/track2_permutation")
N_BLOCKS = 48
TARGET_HASH = "093be1cf2d24094db903cbc3e8d33d306ebca49c6accaa264e44b0b675e7d9c4"

torch.set_num_threads(4)  # can use more threads for matrix ops


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


def compute_block_jacobians(pz, X, n_samples=200):
    """Compute mean Jacobian matrix (48x48) for each (inp, out) pair.

    For block with inp=i, out=o:
      J = I + W_out[o] @ diag(relu_mask) @ W_inp[i]
    where relu_mask = (W_inp[i] @ x + b_inp[i] > 0)

    Returns: jacobians[i][o] = mean Jacobian (48x48) over samples
    """
    X_sub = X[:n_samples]
    I = torch.eye(48)

    # For each inp block, precompute relu masks on sample data
    print("  Computing ReLU activation masks...")
    relu_masks = {}  # inp_idx -> (n_samples, 96) float mask
    for ii in range(48):
        pre_act = X_sub @ pz['W_inp'][ii].T + pz['b_inp'][ii]  # (n, 96)
        relu_masks[ii] = (pre_act > 0).float()  # (n, 96)

    # Compute mean Jacobian for each (inp, out) pair
    print("  Computing 48x48 Jacobian matrices for all pairs...")
    jacobians = np.zeros((48, 48, 48, 48))  # [inp][out] -> 48x48 matrix

    for ii in range(48):
        W1 = pz['W_inp'][ii]  # (96, 48)
        mask = relu_masks[ii]  # (n, 96)

        for oi in range(48):
            W2 = pz['W_out'][oi]  # (48, 96)

            # J_res = W2 @ diag(mask) @ W1 for each sample
            # Mean over samples: W2 @ diag(mean_mask) @ W1
            mean_mask = mask.mean(dim=0)  # (96,)
            J_res = W2 @ torch.diag(mean_mask) @ W1  # (48, 48)
            J_full = I + J_res  # (48, 48)
            jacobians[ii, oi] = J_full.numpy()

        if (ii + 1) % 12 == 0:
            print(f"    {ii+1}/48 inp blocks done")

    return jacobians


def compute_pairwise_transition_cost(jacobians):
    """Compute transition cost C(a, b) for block_a followed by block_b.

    For paired blocks (inp_a, out_a) and (inp_b, out_b):
      C(a, b) = condition_number(J_b @ J_a)

    Lower condition number = smoother gradient flow = better ordering.

    Since we don't know pairings yet, we use the best (inp, out) pairing
    from the current pool solution.
    """
    print("  Computing pairwise transition costs...")

    # First, get the current best solution's pairings from the pool
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT inp_sigma, out_sigma FROM js_puzzle_pool ORDER BY full_mse ASC LIMIT 1")
    row = cur.fetchone()
    conn.close()

    if row is None:
        raise RuntimeError("No solutions in pool")

    best_inp = list(row[0])
    best_out = list(row[1])

    # Use the current best solution's pairings
    # paired_jacobians[k] = Jacobian of position k in the current best solution
    paired_jac = np.zeros((48, 48, 48))
    for k in range(48):
        paired_jac[k] = jacobians[best_inp[k], best_out[k]]

    # Pairwise transition cost: condition number of J_b @ J_a
    cost = np.zeros((48, 48))
    for a in range(48):
        J_a = paired_jac[a]
        for b in range(48):
            if a == b:
                cost[a, b] = 1e10  # can't follow self
                continue
            J_b = paired_jac[b]
            J_product = J_b @ J_a
            # Condition number = max_sv / min_sv
            svs = np.linalg.svd(J_product, compute_uv=False)
            cond = svs[0] / max(svs[-1], 1e-10)
            cost[a, b] = cond

    return cost, best_inp, best_out


def solve_atsp_nearest_neighbor(cost):
    """Solve asymmetric TSP using nearest-neighbor heuristic + 2-opt."""
    n = cost.shape[0]

    # Try all starting positions, keep best
    best_tour = None
    best_cost = float('inf')

    for start in range(n):
        visited = {start}
        tour = [start]
        current = start

        while len(tour) < n:
            # Find nearest unvisited
            min_cost = float('inf')
            min_next = -1
            for j in range(n):
                if j not in visited and cost[current, j] < min_cost:
                    min_cost = cost[current, j]
                    min_next = j
            tour.append(min_next)
            visited.add(min_next)
            current = min_next

        total = sum(cost[tour[i], tour[i+1]] for i in range(n-1))
        if total < best_cost:
            best_cost = total
            best_tour = list(tour)

    print(f"  Nearest-neighbor tour cost: {best_cost:.2f}")

    # 2-opt improvement
    improved = True
    iters = 0
    while improved and iters < 1000:
        improved = False
        iters += 1
        for i in range(n - 2):
            for j in range(i + 2, n):
                # Try reversing segment [i+1, j]
                new_tour = best_tour[:i+1] + best_tour[i+1:j+1][::-1] + best_tour[j+1:]
                new_cost = sum(cost[new_tour[k], new_tour[k+1]] for k in range(n-1))
                if new_cost < best_cost:
                    best_tour = new_tour
                    best_cost = new_cost
                    improved = True
                    break
            if improved:
                break

    print(f"  After 2-opt ({iters} iters): cost={best_cost:.2f}")
    return best_tour, best_cost


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
        print(f"  SAVED to pool: MSE={full_mse:.6f} hash_match={h == TARGET_HASH}")
        if h == TARGET_HASH:
            print("  *** HASH MATCH — PUZZLE SOLVED! ***")
    except Exception as e:
        print(f"  DB save failed: {e}")


def main():
    print("=" * 60)
    print("True Jacobian Chain Conditioning — Council Vote #440da232")
    print("=" * 60)

    pz, inp_indices, out_indices, last_idx = load_puzzle()
    X, Y = load_data(2000)

    # Phase 1: Compute full Jacobian matrices
    print("\nPhase 1: Computing block Jacobians...")
    t0 = time.time()
    jacobians = compute_block_jacobians(pz, X)
    print(f"  Done in {time.time()-t0:.1f}s")

    # Phase 2: Pairwise transition costs
    print("\nPhase 2: Computing pairwise transition costs...")
    t0 = time.time()
    cost, best_inp, best_out = compute_pairwise_transition_cost(jacobians)
    print(f"  Done in {time.time()-t0:.1f}s")
    print(f"  Cost range: [{cost[cost < 1e9].min():.2f}, {cost[cost < 1e9].max():.2f}]")
    print(f"  Cost mean: {cost[cost < 1e9].mean():.2f}")

    # Phase 3: Solve as asymmetric TSP
    print("\nPhase 3: Solving asymmetric TSP...")
    tour, tour_cost = solve_atsp_nearest_neighbor(cost)

    # The tour gives us the POSITION ordering: tour[0] should be first, tour[1] second, etc.
    # Reorder the current best solution according to the tour
    new_inp = [best_inp[tour[k]] for k in range(48)]
    new_out = [best_out[tour[k]] for k in range(48)]

    mse_original = compute_mse(best_inp, best_out, X, Y, pz)
    mse_reordered = compute_mse(new_inp, new_out, X, Y, pz)

    print(f"\n  Original best MSE:     {mse_original:.6f}")
    print(f"  Jacobian-reordered MSE: {mse_reordered:.6f}")

    if mse_reordered < mse_original:
        print(f"  IMPROVEMENT: {mse_original - mse_reordered:.6f}")
        save_to_pool(new_inp, new_out, mse_reordered,
                     inp_indices, out_indices, last_idx,
                     "jacobian_chain_conditioning")
    else:
        print(f"  No improvement from pure reordering. Trying SA refinement...")

    # Phase 4: Quick SA refinement from the Jacobian-ordered seed
    import random
    random.seed(42)
    cur_inp, cur_out = list(new_inp), list(new_out)
    cur_mse = mse_reordered
    best_mse = cur_mse
    best_inp_sa, best_out_sa = list(cur_inp), list(cur_out)
    T = 1.0

    print(f"\nPhase 4: SA refinement (20K steps)...")
    for step in range(20000):
        r = random.random()
        trial_inp, trial_out = list(cur_inp), list(cur_out)

        if r < 0.4:
            i, j = random.sample(range(48), 2)
            trial_inp[i], trial_inp[j] = trial_inp[j], trial_inp[i]
            trial_out[i], trial_out[j] = trial_out[j], trial_out[i]
        elif r < 0.6:
            i, j = random.sample(range(48), 2)
            trial_inp[i], trial_inp[j] = trial_inp[j], trial_inp[i]
        elif r < 0.8:
            i, j = random.sample(range(48), 2)
            trial_out[i], trial_out[j] = trial_out[j], trial_out[i]
        else:
            # Or-opt: relocate a block to a different position
            src = random.randint(0, 47)
            dst = random.randint(0, 47)
            if src != dst:
                inp_val = trial_inp.pop(src)
                out_val = trial_out.pop(src)
                trial_inp.insert(dst, inp_val)
                trial_out.insert(dst, out_val)

        m = compute_mse(trial_inp, trial_out, X, Y, pz)
        delta = m - cur_mse
        if delta < 0 or random.random() < np.exp(-delta / max(T, 1e-10)):
            cur_inp, cur_out, cur_mse = trial_inp, trial_out, m
            if m < best_mse:
                best_mse = m
                best_inp_sa, best_out_sa = list(cur_inp), list(cur_out)
        else:
            cur_inp, cur_out = list(best_inp_sa), list(best_out_sa)
            cur_mse = best_mse

        T *= 0.99985
        if step % 5000 == 0:
            print(f"  step {step}: best={best_mse:.6f} T={T:.5f}")

    print(f"\n  Final MSE after SA: {best_mse:.6f}")

    if best_mse < mse_original:
        save_to_pool(best_inp_sa, best_out_sa, best_mse,
                     inp_indices, out_indices, last_idx,
                     "jacobian_chain_sa")

    # Save Jacobian data and cost matrix for analysis
    np.save(BASE / "results/jacobian_chain_cost_matrix.npy", cost)
    print(f"\nCost matrix saved to results/jacobian_chain_cost_matrix.npy")


if __name__ == "__main__":
    main()
```

## Manual Step (TPM)

After Jr creates the file, run on redfin:
```text
cd /ganuda/experiments/jane-street/track2_permutation
/ganuda/home/dereadi/cherokee_venv/bin/python3 jacobian_chain_solver.py
```

## Success Criteria
- Computes full 48x48 Jacobian matrices for all block pairs
- Builds pairwise condition-number cost matrix
- Solves asymmetric TSP via nearest-neighbor + 2-opt
- Injects result into PG pool (with or without SA refinement)
- Saves cost matrix for future analysis

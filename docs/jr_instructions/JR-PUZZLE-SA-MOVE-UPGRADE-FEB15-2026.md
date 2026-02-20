# Jr Instruction: SA Worker Move-Type Upgrade

**Task ID**: PUZZLE-SA-MOVES-001
**Priority**: 3 (MEDIUM)
**Assigned Jr**: Software Engineer Jr.
**Council Vote**: #d221c4f9 (PROCEED, 0.845)
**use_rlm**: false

## Context

The SA workers currently only do pairwise swaps. The pool has converged to a monoculture. We need larger structural moves to escape the local minimum: segment reversals, 3-opt, and independent inp/out swaps.

## Objective

Modify `/ganuda/experiments/jane-street/track2_permutation/sa_worker.py` to add new move types.

## Implementation

File: `/ganuda/experiments/jane-street/track2_permutation/sa_worker.py`

Find the move selection logic in `run_hybrid_sa()` function (around line 396). The current code does pairwise swaps. Add segment reversal and independent inp/out swaps.

<<<<<<< SEARCH
            # === Move selection ===
            r = random.random()
            if r < 0.5:
                # Swap two positions
                i, j = random.sample(MOVEABLE_POSITIONS, 2)
                inp_a[i], inp_a[j] = inp_a[j], inp_a[i]
                out_a[i], out_a[j] = out_a[j], out_a[i]
=======
            # === Move selection (enhanced with segment ops) ===
            r = random.random()
            if r < 0.30:
                # Swap two positions (paired)
                i, j = random.sample(MOVEABLE_POSITIONS, 2)
                inp_a[i], inp_a[j] = inp_a[j], inp_a[i]
                out_a[i], out_a[j] = out_a[j], out_a[i]
            elif r < 0.45:
                # Swap just inp at two positions (re-pair)
                i, j = random.sample(MOVEABLE_POSITIONS, 2)
                inp_a[i], inp_a[j] = inp_a[j], inp_a[i]
            elif r < 0.60:
                # Swap just out at two positions (re-pair)
                i, j = random.sample(MOVEABLE_POSITIONS, 2)
                out_a[i], out_a[j] = out_a[j], out_a[i]
            elif r < 0.80:
                # Segment reversal (reverse a contiguous block of 3-8 positions)
                seg_len = random.randint(3, min(8, len(MOVEABLE_POSITIONS)))
                moveable_sorted = sorted(MOVEABLE_POSITIONS)
                start_idx = random.randint(0, len(moveable_sorted) - seg_len)
                segment = moveable_sorted[start_idx:start_idx + seg_len]
                seg_inp = [inp_a[p] for p in segment]
                seg_out = [out_a[p] for p in segment]
                seg_inp.reverse()
                seg_out.reverse()
                for k, p in enumerate(segment):
                    inp_a[p] = seg_inp[k]
                    out_a[p] = seg_out[k]
>>>>>>> REPLACE

Note: The SEARCH block above is approximate. The Jr should find the actual move selection code in `run_hybrid_sa()` and add the new move types (independent inp/out swaps, segment reversal) while keeping the existing swap logic. The exact line numbers may differ — search for the pattern where `r = random.random()` is used to select move types.

## Important Notes

- Do NOT change the compute_mse function
- Do NOT change the pool interaction code
- Do NOT change command-line argument parsing
- Only modify the move selection within run_hybrid_sa()
- The segment reversal reverses BOTH inp and out together to maintain pairing within the segment
- Independent inp/out swaps allow RE-PAIRING which the current code cannot do

## Manual Step (TPM)

After modification, restart SA workers across all nodes. The workers auto-load from the same script file, so updating the file on redfin and rsync-ing to other nodes will update them on next restart.

```text
# Kill existing workers on all nodes
ssh bluefin 'pkill -f sa_worker.py'
ssh greenfin 'pkill -f sa_worker.py'
ssh 192.168.132.21 'pkill -f sa_worker.py'
ssh sasass 'pkill -f sa_worker.py'
ssh sasass2 'pkill -f sa_worker.py'
pkill -f sa_worker.py  # redfin

# Rsync updated file
for node in bluefin greenfin; do
  rsync -av /ganuda/experiments/jane-street/track2_permutation/sa_worker.py $node:/ganuda/experiments/jane-street/track2_permutation/
done
for node in 192.168.132.21 sasass sasass2; do
  rsync -av /ganuda/experiments/jane-street/track2_permutation/sa_worker.py $node:/Users/Shared/ganuda/experiments/jane-street/track2_permutation/
done

# Relaunch fleet (use launch_distributed.sh on each node)
```

## Success Criteria
- SA workers use 4 move types: paired swap, inp-only swap, out-only swap, segment reversal
- Workers run without errors
- Pool diversity increases after relaunch

# Jr Instruction: Hungarian Matching for Jr-to-Task Assignment

**Kanban**: #1800
**Priority**: 8 (Wave 1)
**Assigned Jr**: Software Engineer Jr.
**use_rlm**: false
**Sprint**: RC-2026-02E

## Context

The Jr bidding system currently uses greedy winner-take-all: highest `composite_score` wins each task independently. When multiple tasks close simultaneously, this produces suboptimal global assignments — a Jr that's best for Task A might get assigned to Task B because it bid slightly higher there, leaving Task A with a worse match.

The Jane Street puzzle proved that `scipy.optimize.linear_sum_assignment` (Hungarian algorithm) produces globally optimal pairings. We port that pattern here.

**Source**: `/ganuda/experiments/jane-street/track2_permutation/trace_pairing_solver.py` (lines 99-116)

## Step 1: Create the Hungarian bidding optimizer module

Create `/ganuda/jr_executor/hungarian_bidding.py`

```python
#!/usr/bin/env python3
"""
Hungarian Matching for Jr-to-Task Assignment

Replaces greedy per-task winner selection with globally optimal assignment
via scipy.optimize.linear_sum_assignment (Hungarian algorithm).

Ported from Jane Street Track 2 puzzle solver (trace_pairing_solver.py).
Council Vote #a4d8a110e3f06fb8

For Seven Generations - Cherokee AI Federation
"""

import numpy as np
from scipy.optimize import linear_sum_assignment
from datetime import datetime


def build_cost_matrix(tasks, bids):
    """Build NxM cost matrix from tasks and bids.

    Args:
        tasks: list of task dicts with 'task_id'
        bids: list of bid dicts with 'task_id', 'agent_id', 'composite_score',
              'capability_score', 'experience_score', 'load_score'

    Returns:
        cost_matrix: numpy array (n_tasks x n_agents), lower = better
        task_ids: list of task_id in row order
        agent_ids: list of unique agent_id in column order
    """
    task_ids = [t['task_id'] for t in tasks]
    agent_ids = sorted(set(b['agent_id'] for b in bids))

    # Build lookup: (task_id, agent_id) -> composite_score
    score_lookup = {}
    for b in bids:
        key = (b['task_id'], b['agent_id'])
        # Keep highest bid if agent bid multiple times
        if key not in score_lookup or b['composite_score'] > score_lookup[key]:
            score_lookup[key] = b['composite_score']

    n_tasks = len(task_ids)
    n_agents = len(agent_ids)

    # Cost = negative score (Hungarian minimizes cost, we want max score)
    # Use large penalty for missing bids (agent didn't bid on task)
    NO_BID_PENALTY = 1000.0
    cost_matrix = np.full((n_tasks, n_agents), NO_BID_PENALTY)

    for i, tid in enumerate(task_ids):
        for j, aid in enumerate(agent_ids):
            score = score_lookup.get((tid, aid))
            if score is not None:
                cost_matrix[i, j] = -score  # Negate: lower cost = higher score

    return cost_matrix, task_ids, agent_ids


def hungarian_assign(tasks, bids):
    """Find globally optimal task-to-Jr assignment.

    Args:
        tasks: list of task dicts with 'task_id'
        bids: list of bid dicts with 'task_id', 'agent_id', 'composite_score'

    Returns:
        assignments: list of (task_id, agent_id, composite_score, margin) tuples
        unassigned_tasks: list of task_ids with no valid bids
    """
    if not tasks or not bids:
        return [], [t['task_id'] for t in tasks]

    cost_matrix, task_ids, agent_ids = build_cost_matrix(tasks, bids)

    # Hungarian algorithm — O(n^3) but n < 100 for our fleet
    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    assignments = []
    unassigned_tasks = []
    NO_BID_PENALTY = 1000.0

    for row, col in zip(row_ind, col_ind):
        tid = task_ids[row]
        aid = agent_ids[col]
        cost = cost_matrix[row, col]

        if cost >= NO_BID_PENALTY:
            # No valid bid — agent didn't bid on this task
            unassigned_tasks.append(tid)
            continue

        score = -cost  # Undo negation

        # Compute margin: gap between best and second-best assignment
        row_costs = sorted(cost_matrix[row, :])
        if len(row_costs) >= 2:
            margin = row_costs[1] - row_costs[0]  # Bigger = more confident
        else:
            margin = 0.0

        assignments.append({
            'task_id': tid,
            'agent_id': aid,
            'composite_score': score,
            'margin': margin
        })

    # Tasks not in row_ind (more tasks than agents)
    assigned_rows = set(row_ind)
    for i, tid in enumerate(task_ids):
        if i not in assigned_rows:
            unassigned_tasks.append(tid)

    return assignments, unassigned_tasks
```

## Step 2: Update close_bidding.py to use Hungarian matching

File: `/ganuda/jr_executor/close_bidding.py`

<<<<<<< SEARCH
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

import sys
sys.path.insert(0, '/ganuda')
from lib.secrets_loader import get_db_config
DB_CONFIG = get_db_config()

BIDDING_WINDOW_MINUTES = 2  # Close bidding after 2 minutes


def main():
    conn = psycopg2.connect(**DB_CONFIG)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Find tasks open for more than BIDDING_WINDOW_MINUTES with bids
        cur.execute("""
            SELECT a.task_id, a.task_content, a.announced_at
            FROM jr_task_announcements a
            WHERE a.status = 'open'
              AND a.announced_at < NOW() - INTERVAL '%s minutes'
              AND EXISTS (
                  SELECT 1 FROM jr_task_bids b WHERE b.task_id = a.task_id
              )
        """, (BIDDING_WINDOW_MINUTES,))

        tasks = cur.fetchall()

        for task in tasks:
            task_id = task['task_id']

            # Get winning bid
            cur.execute("""
                SELECT agent_id, node_name, composite_score
                FROM jr_task_bids
                WHERE task_id = %s
                ORDER BY composite_score DESC
                LIMIT 1
            """, (task_id,))

            winner = cur.fetchone()

            if winner:
                # Assign task to winner
                cur.execute("""
                    UPDATE jr_task_announcements
                    SET status = 'assigned',
                        assigned_to = %s
                    WHERE task_id = %s
                """, (winner['agent_id'], task_id))

                print(f"[{datetime.now()}] Assigned {task_id} to {winner['agent_id']} "
                      f"(score: {winner['composite_score']:.2f})")

    conn.commit()
    conn.close()
=======
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

import sys
sys.path.insert(0, '/ganuda')
sys.path.insert(0, '/ganuda/jr_executor')
from lib.secrets_loader import get_db_config
from hungarian_bidding import hungarian_assign

DB_CONFIG = get_db_config()

BIDDING_WINDOW_MINUTES = 2  # Close bidding after 2 minutes
USE_HUNGARIAN = True  # Feature flag: set False to revert to greedy


def assign_greedy(cur, tasks):
    """Original greedy assignment: highest composite_score per task."""
    for task in tasks:
        task_id = task['task_id']
        cur.execute("""
            SELECT agent_id, node_name, composite_score
            FROM jr_task_bids
            WHERE task_id = %s
            ORDER BY composite_score DESC
            LIMIT 1
        """, (task_id,))
        winner = cur.fetchone()
        if winner:
            cur.execute("""
                UPDATE jr_task_announcements
                SET status = 'assigned',
                    assigned_to = %s
                WHERE task_id = %s
            """, (winner['agent_id'], task_id))
            print(f"[{datetime.now()}] [greedy] Assigned {task_id} to {winner['agent_id']} "
                  f"(score: {winner['composite_score']:.2f})")


def assign_hungarian(cur, tasks):
    """Globally optimal assignment via Hungarian algorithm."""
    if not tasks:
        return

    # Collect all bids for all closing tasks at once
    task_ids = [t['task_id'] for t in tasks]
    cur.execute("""
        SELECT task_id, agent_id, node_name, composite_score,
               capability_score, experience_score, load_score
        FROM jr_task_bids
        WHERE task_id = ANY(%s)
    """, (task_ids,))
    all_bids = cur.fetchall()

    if not all_bids:
        return

    assignments, unassigned = hungarian_assign(tasks, all_bids)

    for a in assignments:
        cur.execute("""
            UPDATE jr_task_announcements
            SET status = 'assigned',
                assigned_to = %s
            WHERE task_id = %s
        """, (a['agent_id'], a['task_id']))
        print(f"[{datetime.now()}] [hungarian] Assigned {a['task_id']} to {a['agent_id']} "
              f"(score: {a['composite_score']:.2f}, margin: {a['margin']:.2f})")

    for tid in unassigned:
        print(f"[{datetime.now()}] [hungarian] No valid bids for {tid}")


def main():
    conn = psycopg2.connect(**DB_CONFIG)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Find tasks open for more than BIDDING_WINDOW_MINUTES with bids
        cur.execute("""
            SELECT a.task_id, a.task_content, a.announced_at
            FROM jr_task_announcements a
            WHERE a.status = 'open'
              AND a.announced_at < NOW() - INTERVAL '%s minutes'
              AND EXISTS (
                  SELECT 1 FROM jr_task_bids b WHERE b.task_id = a.task_id
              )
        """, (BIDDING_WINDOW_MINUTES,))

        tasks = cur.fetchall()

        if USE_HUNGARIAN:
            assign_hungarian(cur, tasks)
        else:
            assign_greedy(cur, tasks)

    conn.commit()
    conn.close()
>>>>>>> REPLACE

## Verification

After deployment, monitor bidding logs for `[hungarian]` prefix. Compare assignment quality by checking:
1. Tasks still complete successfully (no regression)
2. Margin values — low margin means assignment was close, high margin means clear winner
3. When multiple tasks close simultaneously, agents are spread optimally

## Rollback

Set `USE_HUNGARIAN = False` in close_bidding.py to revert to greedy assignment.

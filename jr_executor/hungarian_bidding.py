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
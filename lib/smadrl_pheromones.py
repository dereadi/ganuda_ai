#!/usr/bin/env python3
"""
S-MADRL Pheromone System for Cherokee AI Federation
Based on arXiv:2510.03592 - Stigmergic Multi-Agent Deep RL

Virtual pheromone mechanics for decentralized Jr agent coordination.
"""

import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import math

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

# S-MADRL Parameters (from paper)
DEFAULT_DECAY_RATE = 0.05        # α: pheromone evaporation rate
DEFAULT_REINFORCEMENT = 0.1      # β: pheromone deposit increment
INITIAL_PHEROMONE = 1.0          # ρ₀: initial pheromone value
MIN_PHEROMONE = 0.01             # Minimum before removal
MAX_PHEROMONE = 10.0             # Cap to prevent runaway

# Reward weights (from paper)
REWARD_WEIGHTS = {
    'distance': 0.2,     # w_d: getting closer to goal
    'collision': 0.2,    # w_c: avoiding conflicts
    'pickup': 0.2,       # w_p: claiming task
    'success': 0.4       # w_s: completing task
}

REWARD_VALUES = {
    'closer_to_goal': 2.5,
    'collision_penalty': -2.0,
    'task_claimed': 50.0,
    'task_success': 50.0,
    'task_failed': -25.0
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def deposit_pheromone(memory_key: str, agent_id: str,
                      agent_state: str, task_type: str = None,
                      action: str = None) -> Dict:
    """
    Deposit pheromone trace at memory location.
    Implements: ρ(t+1) = (1-α)ρ(t) + β
    """
    conn = get_connection()

    with conn.cursor() as cur:
        # Check for existing pheromone at this location from this agent
        cur.execute("""
            SELECT pheromone_id, intensity, decay_rate
            FROM stigmergy_pheromones
            WHERE location_id = %s AND deposited_by = %s
            ORDER BY deposited_at DESC
            LIMIT 1
        """, (memory_key, agent_id))

        existing = cur.fetchone()

        if existing:
            # Reinforce existing pheromone
            pid, current_value, decay = existing
            new_value = (1 - decay) * current_value + DEFAULT_REINFORCEMENT
            new_value = min(MAX_PHEROMONE, max(MIN_PHEROMONE, new_value))

            cur.execute("""
                UPDATE stigmergy_pheromones
                SET intensity = %s,
                    pheromone_type = %s,
                    deposited_at = NOW()
                WHERE pheromone_id = %s
            """, (new_value, agent_state, pid))

            result = {'action': 'reinforced', 'old_value': current_value, 'new_value': new_value}
        else:
            # Deposit new pheromone
            cur.execute("""
                INSERT INTO stigmergy_pheromones
                (location_type, location_id, pheromone_type, intensity, deposited_by, decay_rate)
                VALUES ('memory', %s, %s, %s, %s, %s)
                RETURNING pheromone_id
            """, (memory_key, agent_state, INITIAL_PHEROMONE, agent_id, DEFAULT_DECAY_RATE))

            pid = cur.fetchone()[0]
            result = {'action': 'deposited', 'pheromone_id': pid, 'value': INITIAL_PHEROMONE}

        conn.commit()

    conn.close()
    return result


def read_pheromones(memory_key: str, time_window_minutes: int = 60) -> Dict:
    """
    Read pheromone traces at memory location.
    Returns aggregate pheromone information for agent decision-making.
    """
    conn = get_connection()

    with conn.cursor() as cur:
        cur.execute("""
            SELECT deposited_by, intensity, pheromone_type, deposited_at
            FROM stigmergy_pheromones
            WHERE location_id = %s
            AND deposited_at > NOW() - INTERVAL '%s minutes'
            ORDER BY intensity DESC
        """, (memory_key, time_window_minutes))

        traces = cur.fetchall()

    conn.close()

    if not traces:
        return {
            'memory_key': memory_key,
            'total_pheromone': 0,
            'agent_count': 0,
            'traces': [],
            'dominant_state': None,
            'recommendation': 'explore'
        }

    total_pheromone = sum(t[1] for t in traces)
    agent_count = len(set(t[0] for t in traces))

    # Count agent states
    state_counts = {}
    for t in traces:
        state = t[2]
        state_counts[state] = state_counts.get(state, 0) + 1

    dominant_state = max(state_counts, key=state_counts.get) if state_counts else None

    # Generate recommendation based on pheromone patterns
    if dominant_state == 'blocked':
        recommendation = 'avoid'
    elif dominant_state == 'success' and total_pheromone > 5:
        recommendation = 'exploit'
    elif agent_count > 3:
        recommendation = 'disperse'
    else:
        recommendation = 'follow'

    return {
        'memory_key': memory_key,
        'total_pheromone': total_pheromone,
        'agent_count': agent_count,
        'traces': [
            {'agent_id': t[0], 'value': t[1], 'state': t[2]}
            for t in traces[:10]
        ],
        'dominant_state': dominant_state,
        'state_distribution': state_counts,
        'recommendation': recommendation
    }


def calculate_reward(agent_id: str, task_id: str,
                     outcome: str, metrics: Dict = None) -> float:
    """
    Calculate S-MADRL style composite reward.
    outcome: 'claimed', 'success', 'failed', 'collision', 'progress'
    """
    metrics = metrics or {}

    r_d = REWARD_VALUES['closer_to_goal'] if outcome == 'progress' and metrics.get('closer') else 0
    r_c = REWARD_VALUES['collision_penalty'] if outcome == 'collision' or metrics.get('collisions', 0) > 0 else 0
    r_p = REWARD_VALUES['task_claimed'] if outcome == 'claimed' else 0
    
    if outcome == 'success':
        r_s = REWARD_VALUES['task_success']
    elif outcome == 'failed':
        r_s = REWARD_VALUES['task_failed']
    else:
        r_s = 0

    composite = (
        REWARD_WEIGHTS['distance'] * r_d +
        REWARD_WEIGHTS['collision'] * r_c +
        REWARD_WEIGHTS['pickup'] * r_p +
        REWARD_WEIGHTS['success'] * r_s
    )

    # Log reward
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO memory_usage_attribution
            (memory_hash, task_id, usage_type, reward_signal)
            VALUES (%s, %s, %s, %s)
        """, (task_id, task_id, f'smadrl_{outcome}', composite))
        conn.commit()
    conn.close()

    return composite


def decay_all_pheromones() -> Dict:
    """
    Apply decay to all pheromones.
    Run as periodic job (every 5-15 minutes).
    """
    conn = get_connection()

    with conn.cursor() as cur:
        # Apply decay: ρ = (1-α)ρ
        cur.execute("""
            UPDATE stigmergy_pheromones
            SET intensity = (1 - decay_rate) * intensity
            WHERE intensity > %s
        """, (MIN_PHEROMONE,))

        decayed = cur.rowcount

        # Remove very old/weak pheromones
        cur.execute("""
            DELETE FROM stigmergy_pheromones
            WHERE intensity < %s
            OR deposited_at < NOW() - INTERVAL '24 hours'
        """, (MIN_PHEROMONE,))

        removed = cur.rowcount

        conn.commit()

    conn.close()

    return {'decayed': decayed, 'removed': removed}


def get_pheromone_landscape(limit: int = 50) -> List[Dict]:
    """Get overview of current pheromone landscape."""
    conn = get_connection()

    with conn.cursor() as cur:
        cur.execute("""
            SELECT location_id,
                   SUM(intensity) as total_pheromone,
                   COUNT(DISTINCT deposited_by) as agent_count,
                   MAX(deposited_at) as last_activity
            FROM stigmergy_pheromones
            WHERE deposited_at > NOW() - INTERVAL '2 hours'
            GROUP BY location_id
            ORDER BY total_pheromone DESC
            LIMIT %s
        """, (limit,))

        rows = cur.fetchall()

    conn.close()

    return [
        {
            'memory_key': r[0],
            'total_pheromone': float(r[1]),
            'agent_count': r[2],
            'last_activity': r[3].isoformat() if r[3] else None
        }
        for r in rows
    ]


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == 'decay':
            result = decay_all_pheromones()
            print(f"Decay result: {result}")
        elif sys.argv[1] == 'landscape':
            landscape = get_pheromone_landscape()
            for loc in landscape:
                print(f"{loc['memory_key']}: {loc['total_pheromone']:.2f} ({loc['agent_count']} agents)")
        elif sys.argv[1] == 'test':
            # Quick test
            result = deposit_pheromone('test-memory-001', 'test-agent', 'working', action='test')
            print(f"Deposit: {result}")
            info = read_pheromones('test-memory-001')
            print(f"Read: {info}")
    else:
        print("S-MADRL Pheromone System")
        print("Usage:")
        print("  python smadrl_pheromones.py decay     - Run pheromone decay")
        print("  python smadrl_pheromones.py landscape - View pheromone landscape")
        print("  python smadrl_pheromones.py test      - Run quick test")

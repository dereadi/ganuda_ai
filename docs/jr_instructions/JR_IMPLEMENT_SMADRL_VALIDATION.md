# Jr Task: Implement S-MADRL Pheromone Validation for Stigmergy

**Task ID:** task-impl-smadrl-001
**Priority:** P1 (Phase 3.1 - Parallel Track B)
**Created:** December 22, 2025
**TPM:** Cherokee AI Federation
**Based On:** arXiv:2510.03592 - S-MADRL: Stigmergic Multi-Agent Deep RL

---

## Overview

Validate and enhance our existing stigmergy_coordination.py with pheromone mechanics from S-MADRL research. This adds virtual pheromone deposition, decay dynamics, and RL-based reward structures to improve Jr agent coordination.

**Current State:** We have density-aware stigmergic coordination with 0.230 threshold. This task adds pheromone dynamics and RL integration.

---

## Research Paper Summary

S-MADRL uses virtual pheromones for decentralized emergent coordination:
- Pheromone formula: `ρ(t+1) = (1-α)ρ(t) + β` (decay rate α, reinforcement β)
- Agents encode state information in pheromones
- Four-component reward: distance (+2.5), collision (-2.0), pickup (+50), delivery (+50)
- DQN-based learning with pheromone-augmented observations
- No explicit inter-agent communication required

---

## Implementation Tasks

### Task 1: Add Pheromone Mechanics to Database

```sql
-- Create pheromone trace table
CREATE TABLE IF NOT EXISTS stigmergy_pheromones (
    pheromone_id SERIAL PRIMARY KEY,
    memory_key VARCHAR(128) NOT NULL,
    agent_id VARCHAR(64) NOT NULL,
    pheromone_value FLOAT DEFAULT 1.0,
    agent_state VARCHAR(32),  -- 'working', 'idle', 'blocked', 'success', 'failed'
    task_type VARCHAR(32),
    action_taken VARCHAR(64),
    deposited_at TIMESTAMP DEFAULT NOW(),
    last_reinforced TIMESTAMP DEFAULT NOW(),
    decay_rate FLOAT DEFAULT 0.05,  -- α in paper
    reinforcement_rate FLOAT DEFAULT 0.1  -- β in paper
);

CREATE INDEX IF NOT EXISTS idx_pheromone_key ON stigmergy_pheromones(memory_key);
CREATE INDEX IF NOT EXISTS idx_pheromone_agent ON stigmergy_pheromones(agent_id);
CREATE INDEX IF NOT EXISTS idx_pheromone_time ON stigmergy_pheromones(deposited_at);

-- Add pheromone tracking to memory_access_log
ALTER TABLE memory_access_log
ADD COLUMN IF NOT EXISTS pheromone_deposited BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS agent_state VARCHAR(32);
```

### Task 2: Implement Pheromone Dynamics

**File:** `/ganuda/lib/smadrl_pheromones.py`

```python
#!/usr/bin/env python3
"""
S-MADRL Pheromone System for Cherokee AI Federation
Based on arXiv:2510.03592 - Stigmergic Multi-Agent Deep RL

Virtual pheromone mechanics for decentralized Jr agent coordination.
"""

import psycopg2
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
            SELECT pheromone_id, pheromone_value, decay_rate, reinforcement_rate
            FROM stigmergy_pheromones
            WHERE memory_key = %s AND agent_id = %s
            ORDER BY deposited_at DESC
            LIMIT 1
        """, (memory_key, agent_id))

        existing = cur.fetchone()

        if existing:
            # Reinforce existing pheromone
            pid, current_value, decay, reinforce = existing
            # Apply decay then add reinforcement
            new_value = (1 - decay) * current_value + reinforce
            new_value = min(MAX_PHEROMONE, max(MIN_PHEROMONE, new_value))

            cur.execute("""
                UPDATE stigmergy_pheromones
                SET pheromone_value = %s,
                    agent_state = %s,
                    action_taken = %s,
                    last_reinforced = NOW()
                WHERE pheromone_id = %s
            """, (new_value, agent_state, action, pid))

            result = {'action': 'reinforced', 'old_value': current_value, 'new_value': new_value}
        else:
            # Deposit new pheromone
            cur.execute("""
                INSERT INTO stigmergy_pheromones
                (memory_key, agent_id, pheromone_value, agent_state, task_type, action_taken)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING pheromone_id
            """, (memory_key, agent_id, INITIAL_PHEROMONE, agent_state, task_type, action))

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
            SELECT agent_id, pheromone_value, agent_state, task_type, action_taken,
                   deposited_at, last_reinforced
            FROM stigmergy_pheromones
            WHERE memory_key = %s
            AND last_reinforced > NOW() - INTERVAL '%s minutes'
            ORDER BY pheromone_value DESC
        """, (memory_key, time_window_minutes))

        traces = cur.fetchall()

        # Aggregate statistics
        if not traces:
            return {
                'memory_key': memory_key,
                'total_pheromone': 0,
                'agent_count': 0,
                'traces': [],
                'dominant_state': None,
                'recommendation': 'explore'  # No pheromones = explore
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
            recommendation = 'exploit'  # Strong success trail
        elif agent_count > 3:
            recommendation = 'disperse'  # Too crowded
        else:
            recommendation = 'follow'  # Follow the trail

    conn.close()

    return {
        'memory_key': memory_key,
        'total_pheromone': total_pheromone,
        'agent_count': agent_count,
        'traces': [
            {
                'agent_id': t[0],
                'value': t[1],
                'state': t[2],
                'task_type': t[3],
                'action': t[4]
            }
            for t in traces[:10]  # Top 10 traces
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
    metrics: Optional dict with 'distance_delta', 'collisions', etc.
    """
    metrics = metrics or {}

    # Component rewards
    r_d = 0  # Distance reward
    r_c = 0  # Collision penalty
    r_p = 0  # Pickup/claim reward
    r_s = 0  # Success/delivery reward

    if outcome == 'progress':
        if metrics.get('closer', False):
            r_d = REWARD_VALUES['closer_to_goal']

    if outcome == 'collision' or metrics.get('collisions', 0) > 0:
        r_c = REWARD_VALUES['collision_penalty']

    if outcome == 'claimed':
        r_p = REWARD_VALUES['task_claimed']

    if outcome == 'success':
        r_s = REWARD_VALUES['task_success']
    elif outcome == 'failed':
        r_s = REWARD_VALUES['task_failed']

    # Weighted composite
    composite = (
        REWARD_WEIGHTS['distance'] * r_d +
        REWARD_WEIGHTS['collision'] * r_c +
        REWARD_WEIGHTS['pickup'] * r_p +
        REWARD_WEIGHTS['success'] * r_s
    )

    # Log reward for RL integration
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO memory_usage_attribution
            (memory_hash, agent_id, usage_type, outcome, reward_value, penalty_value, context)
            VALUES (%s, %s, 'smadrl_reward', %s, %s, %s, %s)
        """, (
            task_id, agent_id, outcome,
            max(0, composite), abs(min(0, composite)),
            psycopg2.extras.Json({
                'r_d': r_d, 'r_c': r_c, 'r_p': r_p, 'r_s': r_s,
                'metrics': metrics
            })
        ))
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
            SET pheromone_value = (1 - decay_rate) * pheromone_value
            WHERE pheromone_value > %s
        """, (MIN_PHEROMONE,))

        decayed = cur.rowcount

        # Remove very old/weak pheromones
        cur.execute("""
            DELETE FROM stigmergy_pheromones
            WHERE pheromone_value < %s
            OR last_reinforced < NOW() - INTERVAL '24 hours'
        """, (MIN_PHEROMONE,))

        removed = cur.rowcount

        conn.commit()

    conn.close()

    return {'decayed': decayed, 'removed': removed}


def get_pheromone_landscape(limit: int = 50) -> List[Dict]:
    """
    Get overview of current pheromone landscape.

    Useful for monitoring and visualization.
    """
    conn = get_connection()

    with conn.cursor() as cur:
        cur.execute("""
            SELECT memory_key,
                   SUM(pheromone_value) as total_pheromone,
                   COUNT(DISTINCT agent_id) as agent_count,
                   MODE() WITHIN GROUP (ORDER BY agent_state) as dominant_state,
                   MAX(last_reinforced) as last_activity
            FROM stigmergy_pheromones
            WHERE last_reinforced > NOW() - INTERVAL '2 hours'
            GROUP BY memory_key
            ORDER BY total_pheromone DESC
            LIMIT %s
        """, (limit,))

        rows = cur.fetchall()

    conn.close()

    return [
        {
            'memory_key': r[0],
            'total_pheromone': r[1],
            'agent_count': r[2],
            'dominant_state': r[3],
            'last_activity': r[4].isoformat() if r[4] else None
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
    else:
        print("S-MADRL Pheromone System")
        print("Usage:")
        print("  python smadrl_pheromones.py decay     - Run pheromone decay")
        print("  python smadrl_pheromones.py landscape - View pheromone landscape")
```

### Task 3: Integrate with Existing Stigmergy

Update `/ganuda/lib/stigmergy_coordination.py`:

```python
# Add imports
from lib.smadrl_pheromones import deposit_pheromone, read_pheromones, calculate_reward

def adaptive_memory_recall(memory_key: str, agent_id: str) -> dict:
    """
    Enhanced adaptive recall with pheromone reading.
    """
    # Read pheromones first
    pheromone_info = read_pheromones(memory_key)

    # Adjust strategy based on pheromone recommendation
    recommendation = pheromone_info.get('recommendation', 'explore')

    density = calculate_agent_density(memory_key)

    conn = get_connection()
    with conn.cursor() as cur:
        if recommendation == 'avoid':
            # Blocked trail - find alternative
            cur.execute("""
                SELECT memory_hash, original_content, temperature_score
                FROM thermal_memory_archive
                WHERE original_content NOT ILIKE %s
                ORDER BY temperature_score DESC
                LIMIT 5
            """, (f'%{memory_key}%',))
            strategy = 'pheromone_avoid'

        elif recommendation == 'exploit' or density >= DENSITY_THRESHOLD:
            # Strong success trail or high density - exploit
            cur.execute("""
                SELECT memory_hash, original_content, temperature_score
                FROM thermal_memory_archive
                WHERE original_content ILIKE %s
                ORDER BY temperature_score DESC, created_at DESC
                LIMIT 5
            """, (f'%{memory_key}%',))
            strategy = 'pheromone_exploit'

        else:
            # Explore or follow
            cur.execute("""
                SELECT memory_hash, original_content, temperature_score
                FROM thermal_memory_archive
                WHERE original_content ILIKE %s
                ORDER BY RANDOM()
                LIMIT 5
            """, (f'%{memory_key}%',))
            strategy = 'pheromone_explore'

        memories = cur.fetchall()

        # Deposit our own pheromone
        deposit_pheromone(memory_key, agent_id, 'working', action='memory_recall')

        # Log access
        cur.execute("""
            INSERT INTO memory_access_log
            (agent_id, memory_key, access_type, pheromone_deposited, agent_state)
            VALUES (%s, %s, 'read', TRUE, 'working')
        """, (agent_id, memory_key))

        conn.commit()

    conn.close()

    return {
        'strategy': strategy,
        'density': density,
        'pheromone_info': pheromone_info,
        'memories': [
            {'hash': h, 'content': c[:200], 'temp': t}
            for h, c, t in memories
        ]
    }
```

### Task 4: Add Pheromone Decay Cron Job

```bash
# Add to crontab on greenfin
*/15 * * * * /home/dereadi/cherokee_venv/bin/python3 /ganuda/lib/smadrl_pheromones.py decay >> /var/log/ganuda/pheromone_decay.log 2>&1
```

---

## Deployment Steps

1. Run SQL schema changes on bluefin
2. Create `/ganuda/lib/smadrl_pheromones.py`
3. Update stigmergy_coordination.py with pheromone integration
4. Set up cron job for pheromone decay
5. Deploy to all Jr executor nodes
6. Monitor pheromone landscape via thermal memory

---

## Success Criteria

- [ ] stigmergy_pheromones table created and receiving deposits
- [ ] deposit_pheromone() creates traces on memory access
- [ ] read_pheromones() returns recommendations (avoid/exploit/explore)
- [ ] calculate_reward() logs S-MADRL style rewards
- [ ] Pheromone decay runs every 15 minutes
- [ ] Jr agents use pheromone recommendations for strategy selection

---

## Validation Tests

1. **Pheromone Deposit Test:**
   - Agent accesses memory → pheromone deposited
   - Same agent accesses again → pheromone reinforced (value increases)

2. **Decay Test:**
   - Run decay → all values decrease by decay_rate
   - Values below MIN_PHEROMONE → removed

3. **Recommendation Test:**
   - Multiple 'blocked' states → recommendation = 'avoid'
   - High 'success' pheromone → recommendation = 'exploit'
   - No pheromones → recommendation = 'explore'

---

*For Seven Generations - Cherokee AI Federation*

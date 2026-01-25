# Jr Task: Implement RL Reward Signals for Thermal Memory

**Task ID:** task-impl-rl-001
**Priority:** P2 (Infrastructure Enhancement)
**Created:** December 22, 2025
**TPM:** Cherokee AI Federation
**Based On:** task-rl-rewards-001_impl_plan.md

---

## Overview

Implement reinforcement learning reward signals for thermal memory based on arXiv research. This creates a feedback loop where memory usage patterns influence temperature and future recall priority.

---

## Implementation Tasks

### Task 1: Create memory_usage_attribution Table

```sql
CREATE TABLE memory_usage_attribution (
    attribution_id SERIAL PRIMARY KEY,
    memory_hash VARCHAR(64) NOT NULL,
    agent_id VARCHAR(64) NOT NULL,
    usage_time TIMESTAMP DEFAULT NOW(),
    usage_type VARCHAR(32),  -- 'recall', 'update', 'create', 'reference'
    outcome VARCHAR(32),      -- 'helpful', 'neutral', 'unhelpful'
    reward_value FLOAT DEFAULT 0,
    penalty_value FLOAT DEFAULT 0,
    attribution_weight FLOAT DEFAULT 1.0,
    context JSONB DEFAULT '{}'
);

CREATE INDEX idx_usage_memory ON memory_usage_attribution(memory_hash);
CREATE INDEX idx_usage_agent ON memory_usage_attribution(agent_id);
CREATE INDEX idx_usage_time ON memory_usage_attribution(usage_time);
```

### Task 2: Configure thermal_rl_config

**File:** `/ganuda/config/thermal_rl_config.yaml`

```yaml
# Thermal Memory RL Configuration
# Based on arXiv:2509.20095

learning_rate: 0.05
reward_decay: 0.95
penalty_decay: 0.90

# Temperature adjustments
temperature_rewards:
  helpful_recall: 5.0      # Memory was helpful in task completion
  successful_task: 3.0     # Memory contributed to task success
  frequent_access: 1.0     # Memory accessed frequently (useful)

temperature_penalties:
  unhelpful_recall: -3.0   # Memory was not helpful
  failed_task: -2.0        # Memory may have misled agent
  stale_access: -0.5       # Old memory not accessed in 7 days

# Threshold triggers
thresholds:
  hot_memory: 90           # Alert threshold
  warm_memory: 70          # Active memory
  cold_memory: 30          # Consider for archival
  freeze_memory: 10        # Archive candidate

# Attribution settings
attribution:
  lookback_window_hours: 24
  min_confidence: 0.5
  max_attribution_per_memory: 10.0
```

### Task 3: Implement Reward/Penalty Functions

**File:** `/ganuda/lib/thermal_rl.py`

```python
import psycopg2
import yaml
from datetime import datetime, timedelta
from typing import Dict, Tuple

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

# Load config
with open('/ganuda/config/thermal_rl_config.yaml') as f:
    RL_CONFIG = yaml.safe_load(f)

def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def calculate_reward(memory_hash: str, outcome: str,
                     agent_id: str, context: dict = None) -> float:
    """
    Calculate reward for memory usage outcome.

    outcome: 'helpful', 'neutral', 'unhelpful'
    Returns reward value (positive) or penalty (negative)
    """
    rewards = RL_CONFIG['temperature_rewards']
    penalties = RL_CONFIG['temperature_penalties']

    if outcome == 'helpful':
        reward = rewards['helpful_recall']
    elif outcome == 'successful_task':
        reward = rewards['successful_task']
    elif outcome == 'unhelpful':
        reward = penalties['unhelpful_recall']
    elif outcome == 'failed_task':
        reward = penalties['failed_task']
    else:
        reward = 0.0

    # Log attribution
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO memory_usage_attribution
            (memory_hash, agent_id, usage_type, outcome,
             reward_value, penalty_value, context)
            VALUES (%s, %s, 'evaluation', %s, %s, %s, %s)
        """, (
            memory_hash, agent_id, outcome,
            max(0, reward), min(0, abs(reward)),
            psycopg2.extras.Json(context or {})
        ))
        conn.commit()
    conn.close()

    return reward


def apply_temperature_adjustment(memory_hash: str,
                                  adjustment: float) -> float:
    """
    Apply temperature adjustment to memory.

    Clamps to 0-100 range.
    Returns new temperature.
    """
    conn = get_connection()
    with conn.cursor() as cur:
        # Get current temperature
        cur.execute("""
            SELECT temperature_score FROM thermal_memory_archive
            WHERE memory_hash = %s
        """, (memory_hash,))

        result = cur.fetchone()
        if not result:
            conn.close()
            return 50.0  # Default temperature

        current_temp = result[0]
        new_temp = max(0, min(100, current_temp + adjustment))

        # Update temperature
        cur.execute("""
            UPDATE thermal_memory_archive
            SET temperature_score = %s
            WHERE memory_hash = %s
        """, (new_temp, memory_hash))
        conn.commit()

    conn.close()
    return new_temp


def reward_memory_for_task_success(task_id: str, agent_id: str,
                                    memories_used: list):
    """
    Reward memories that contributed to successful task.

    memories_used: list of memory_hash values
    """
    reward = RL_CONFIG['temperature_rewards']['successful_task']

    for memory_hash in memories_used:
        # Calculate with decay based on position
        position_weight = 1.0 / (memories_used.index(memory_hash) + 1)
        adjusted_reward = reward * position_weight

        calculate_reward(memory_hash, 'successful_task',
                        agent_id, {'task_id': task_id})
        apply_temperature_adjustment(memory_hash, adjusted_reward)


def penalize_memory_for_task_failure(task_id: str, agent_id: str,
                                      memories_used: list):
    """
    Penalize memories associated with failed task.

    Uses lighter penalties to avoid over-correction.
    """
    penalty = RL_CONFIG['temperature_penalties']['failed_task']

    for memory_hash in memories_used:
        # Lighter penalty for memories used later
        position_weight = 0.5 / (memories_used.index(memory_hash) + 1)
        adjusted_penalty = penalty * position_weight

        calculate_reward(memory_hash, 'failed_task',
                        agent_id, {'task_id': task_id})
        apply_temperature_adjustment(memory_hash, adjusted_penalty)


def decay_stale_memories():
    """
    Apply decay penalty to memories not accessed recently.

    Run as periodic job (daily).
    """
    conn = get_connection()
    penalty = RL_CONFIG['temperature_penalties']['stale_access']

    with conn.cursor() as cur:
        # Find memories not accessed in 7 days
        cur.execute("""
            SELECT m.memory_hash
            FROM thermal_memory_archive m
            LEFT JOIN memory_usage_attribution a ON m.memory_hash = a.memory_hash
            WHERE m.temperature_score > 30
            GROUP BY m.memory_hash
            HAVING MAX(a.usage_time) < NOW() - INTERVAL '7 days'
               OR MAX(a.usage_time) IS NULL
        """)

        stale = cur.fetchall()

        for (memory_hash,) in stale:
            cur.execute("""
                UPDATE thermal_memory_archive
                SET temperature_score = GREATEST(10, temperature_score + %s)
                WHERE memory_hash = %s
            """, (penalty, memory_hash))

        conn.commit()
    conn.close()

    return len(stale)
```

### Task 4: Integrate with Task Executor

Update `jr_task_executor.py`:

```python
from lib.thermal_rl import (
    reward_memory_for_task_success,
    penalize_memory_for_task_failure
)

def execute_task(self, task: dict) -> Tuple[bool, str]:
    """Execute task with RL feedback."""

    # Track memories used during execution
    self.memories_used = []

    success, result = self._do_execute(task)

    # Apply RL rewards/penalties
    if self.memories_used:
        if success:
            reward_memory_for_task_success(
                task['task_id'],
                self.agent_id,
                self.memories_used
            )
        else:
            penalize_memory_for_task_failure(
                task['task_id'],
                self.agent_id,
                self.memories_used
            )

    return success, result

def _query_thermal_memory(self, query: str, limit: int = 5) -> str:
    """Query and track memories used."""
    # ... existing query logic ...

    # Track which memories were used
    for memory_hash in retrieved_hashes:
        self.memories_used.append(memory_hash)

    return context
```

---

## Deployment Steps

1. Create memory_usage_attribution table on bluefin
2. Create `/ganuda/config/thermal_rl_config.yaml`
3. Create `/ganuda/lib/thermal_rl.py`
4. Update jr_task_executor.py with RL integration
5. Deploy to all Jr executor nodes
6. Set up daily cron for decay_stale_memories()
7. Monitor temperature changes via thermal browser

---

## Success Criteria

- [ ] memory_usage_attribution table captures all usages
- [ ] Successful tasks increase memory temperatures
- [ ] Failed tasks decrease memory temperatures
- [ ] Stale memories decay over time
- [ ] Hot memory alerts trigger for temp > 90

---

*For Seven Generations - Cherokee AI Federation*

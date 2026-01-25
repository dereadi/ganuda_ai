# Jr Instruction: SwarmSys Pheromone Integration

**Created**: December 24, 2025
**Paper**: arXiv:2510.10047 - SwarmSys: Decentralized Swarm-Inspired Agents
**Priority**: HIGH (Council approved)
**Effort**: LOW (validates existing infrastructure)

---

## CRITICAL: FILESYSTEM ARCHITECTURE

**ganuda is NOT a shared filesystem!** Each node has its own local copy.

| Node Type | Ganuda Path | Nodes |
|-----------|-------------|-------|
| Linux (fin) | `/ganuda` | redfin, greenfin, bluefin |
| macOS (sasass) | `/Users/Shared/ganuda` | sasass, sasass2, bmasass |

**Database (bluefin PostgreSQL) is the ONLY shared state.**

When writing code that references ganuda paths, use:
```python
import platform
GANUDA_PATH = "/Users/Shared/ganuda" if platform.system() == "Darwin" else "/ganuda"
```

---

## EXECUTIVE SUMMARY

SwarmSys describes a pheromone-based coordination system for multi-agent AI.
We ALREADY have the database infrastructure (stigmergy_pheromones table).
We ALREADY have the S-MADRL library (`{GANUDA_PATH}/lib/smadrl_pheromones.py`).

**THE GAP**: Jr agents don't actually USE pheromones in bidding or execution.

This instruction bridges that gap with minimal code changes.

---

## SWARMSYS KEY CONCEPTS

### 1. Pheromone Types (from paper)
| Type | Meaning | Our Mapping |
|------|---------|-------------|
| exploration_success | Found new solution path | task_type discovery |
| task_claimed | Agent claimed task | bid_accepted |
| task_completed | Successful completion | execution_success |
| validation_pass | Output verified | quality_check_pass |
| collision_warning | Multiple agents same task | bid_conflict |

### 2. Pheromone Dynamics
- **Deposit**: Intensity = 1.0 on success, 0.5 on partial, 0.0 on failure
- **Decay**: intensity = intensity * (1 - decay_rate) per hour
- **Reinforcement**: Re-deposit on same location adds, doesn't replace
- **Reading**: Sum all pheromones at location, weight by recency

### 3. Agent Behavior
- **Explore** when pheromone intensity < 0.3 (try new task types)
- **Exploit** when pheromone intensity > 0.7 (stick to proven paths)
- **Balance** in middle range (probabilistic choice)

---

## GAP ANALYSIS

### What We Have ✅
```sql
-- stigmergy_pheromones table (EXISTS)
pheromone_id, location_type, location_id, pheromone_type,
intensity, deposited_by, deposited_at, decay_rate

-- smadrl_pheromones.py functions (EXIST)
deposit_pheromone(location_type, location_id, pheromone_type, intensity, agent_id)
read_pheromones(location_type, location_id)
```

### What's Missing ❌
1. **Jr Executor doesn't deposit pheromones after task completion**
2. **Jr Bidding doesn't read pheromones when calculating scores**
3. **No pheromone decay job running**
4. **No exploration vs exploitation tracking**

---

## IMPLEMENTATION TASKS

### TASK 1: Pheromone Deposit in Jr Executor
**File**: /ganuda/services/jr_executor/jr_task_executor.py

After task completion (success or failure), add:

```python
from lib.smadrl_pheromones import deposit_pheromone

def on_task_complete(task_id, task_type, success, agent_id):
    """Deposit pheromone after task execution."""
    # Location is the task_type (e.g., 'implementation', 'deployment', 'code')
    pheromone_type = 'task_completed' if success else 'task_failed'
    intensity = 1.0 if success else 0.2

    deposit_pheromone(
        location_type='task_type',
        location_id=task_type,
        pheromone_type=pheromone_type,
        intensity=intensity,
        agent_id=agent_id
    )

    # Also deposit at specific task for future similar tasks
    deposit_pheromone(
        location_type='task',
        location_id=task_id,
        pheromone_type=pheromone_type,
        intensity=intensity,
        agent_id=agent_id
    )
```

**Integration Point**: Call `on_task_complete()` in the task execution finally block.

---

### TASK 2: Pheromone Reading in Jr Bidding
**File**: /ganuda/services/jr_bidding/jr_bidding_daemon.py

When calculating composite_score, factor in pheromone data:

```python
from lib.smadrl_pheromones import read_pheromones, get_agent_pheromone_affinity

def calculate_bid_score(task, agent_id, agent_capabilities):
    """Enhanced bid scoring with pheromone awareness."""
    base_score = calculate_capability_match(task, agent_capabilities)

    # Read pheromones at this task type location
    pheromones = read_pheromones('task_type', task['task_type'])

    # Calculate pheromone boost
    total_intensity = sum(p['intensity'] for p in pheromones if p['pheromone_type'] == 'task_completed')
    failure_intensity = sum(p['intensity'] for p in pheromones if p['pheromone_type'] == 'task_failed')

    # Boost score if task type has success history
    pheromone_boost = min(total_intensity * 0.1, 0.3)  # Max 30% boost

    # Penalty if task type has failure history
    failure_penalty = min(failure_intensity * 0.05, 0.15)  # Max 15% penalty

    # Check if THIS agent has affinity for this task type
    agent_affinity = get_agent_pheromone_affinity(agent_id, task['task_type'])
    affinity_boost = agent_affinity * 0.2  # Up to 20% boost for agent's own success

    final_score = base_score + pheromone_boost - failure_penalty + affinity_boost
    return min(max(final_score, 0), 1.0)  # Clamp to [0, 1]
```

---

### TASK 3: Pheromone Decay Daemon
**File**: /ganuda/services/pheromone_decay/decay_daemon.py (NEW)

Create a simple daemon that runs hourly:

```python
#!/usr/bin/env python3
"""Pheromone Decay Daemon - Run every hour via cron or systemd timer."""

import psycopg2
import time

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

def decay_all_pheromones():
    """Apply decay to all pheromones. Remove those below threshold."""
    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor() as cur:
        # Apply decay: intensity = intensity * (1 - decay_rate)
        cur.execute("""
            UPDATE stigmergy_pheromones
            SET intensity = intensity * (1 - decay_rate)
            WHERE intensity > 0.01
        """)

        # Remove pheromones that have decayed below threshold
        cur.execute("""
            DELETE FROM stigmergy_pheromones
            WHERE intensity < 0.01
        """)

        deleted = cur.rowcount
        conn.commit()

    conn.close()
    print(f"[DECAY] Decayed pheromones, removed {deleted} below threshold")

if __name__ == '__main__':
    decay_all_pheromones()
```

**Systemd Timer**: Create pheromone-decay.timer to run this hourly.

---

### TASK 4: Agent Affinity Tracking
**File**: /ganuda/lib/smadrl_pheromones.py (EXTEND)

Add function to track agent's success history:

```python
def get_agent_pheromone_affinity(agent_id: str, task_type: str) -> float:
    """Get agent's affinity for a task type based on their pheromone deposits."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                SUM(CASE WHEN pheromone_type = 'task_completed' THEN intensity ELSE 0 END) as success,
                SUM(CASE WHEN pheromone_type = 'task_failed' THEN intensity ELSE 0 END) as failure
            FROM stigmergy_pheromones
            WHERE deposited_by = %s
              AND location_type = 'task_type'
              AND location_id = %s
        """, (agent_id, task_type))
        row = cur.fetchone()

        if not row or (row[0] is None and row[1] is None):
            return 0.5  # Neutral - no history

        success = row[0] or 0
        failure = row[1] or 0
        total = success + failure

        if total == 0:
            return 0.5

        return success / total  # 0 = all failures, 1 = all successes
    conn.close()


def should_explore(agent_id: str, task_type: str) -> bool:
    """Decide if agent should explore (try new) or exploit (stick to known)."""
    affinity = get_agent_pheromone_affinity(agent_id, task_type)
    pheromones = read_pheromones('task_type', task_type)
    total_intensity = sum(p['intensity'] for p in pheromones)

    # Low pheromone intensity = unexplored territory = explore
    if total_intensity < 0.3:
        return True
    # High intensity with good affinity = exploit
    elif total_intensity > 0.7 and affinity > 0.6:
        return False
    # Middle ground = probabilistic
    else:
        import random
        return random.random() < (1 - affinity)
```

---

## VALIDATION CHECKLIST

After implementation, verify:

- [ ] Task completion deposits pheromone to stigmergy_pheromones
- [ ] Successful tasks deposit intensity=1.0, failures deposit 0.2
- [ ] Jr bidding reads pheromones when calculating scores
- [ ] Agents with history on task type get affinity boost
- [ ] Decay daemon runs hourly
- [ ] Pheromones below 0.01 are removed
- [ ] 10+ tasks show pheromone deposits in database

---

## SEVEN GENERATIONS CONSIDERATION

Pheromone-based coordination embodies:
- **Emergent Intelligence**: No central controller, wisdom emerges from collective traces
- **Sustainable Patterns**: Successful paths strengthen, failures fade
- **Intergenerational Memory**: Future agents learn from past agent experiences

"The paths we walk leave trails for those who follow."

---

## DATABASE VERIFICATION QUERIES

```sql
-- Check pheromone deposits by task type
SELECT location_id as task_type,
       COUNT(*) as deposits,
       SUM(intensity) as total_intensity,
       COUNT(DISTINCT deposited_by) as unique_agents
FROM stigmergy_pheromones
WHERE location_type = 'task_type'
GROUP BY location_id
ORDER BY total_intensity DESC;

-- Check agent affinities
SELECT deposited_by as agent,
       location_id as task_type,
       SUM(CASE WHEN pheromone_type = 'task_completed' THEN intensity ELSE 0 END) as success,
       SUM(CASE WHEN pheromone_type = 'task_failed' THEN intensity ELSE 0 END) as failure
FROM stigmergy_pheromones
WHERE location_type = 'task_type'
GROUP BY deposited_by, location_id
ORDER BY success DESC;
```

---

*For Seven Generations - the paths we walk leave trails for those who follow.*

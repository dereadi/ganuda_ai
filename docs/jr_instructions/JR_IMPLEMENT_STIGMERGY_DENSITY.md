# Jr Task: Implement Density-Aware Stigmergic Coordination

**Task ID:** task-impl-stigmergy-001
**Priority:** P2 (Infrastructure Enhancement)
**Created:** December 22, 2025
**TPM:** Cherokee AI Federation
**Based On:** task-stigmergy-density-001_impl_plan.md

---

## Overview

Implement density-aware stigmergic coordination based on arXiv research. This enables agents to coordinate via environmental signals (pheromones/memories) with density-based strategy switching.

---

## Implementation Tasks

### Task 1: Create memory_access_log Table

```sql
CREATE TABLE memory_access_log (
    log_id SERIAL PRIMARY KEY,
    agent_id VARCHAR(64) NOT NULL,
    memory_key VARCHAR(128) NOT NULL,
    access_type VARCHAR(16) CHECK (access_type IN ('read', 'write', 'update')),
    access_time TIMESTAMP DEFAULT NOW(),
    spatial_x FLOAT DEFAULT 0,
    spatial_y FLOAT DEFAULT 0,
    node_name VARCHAR(32)
);

CREATE INDEX idx_mem_access_agent ON memory_access_log(agent_id);
CREATE INDEX idx_mem_access_key ON memory_access_log(memory_key);
CREATE INDEX idx_mem_access_time ON memory_access_log(access_time);
```

### Task 2: Implement calculate_agent_density()

**File:** `/ganuda/lib/stigmergy_coordination.py`

```python
import psycopg2
from datetime import datetime, timedelta

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

DENSITY_THRESHOLD = 0.230

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def calculate_agent_density(memory_key: str, time_window_minutes: int = 60) -> float:
    """
    Calculate agent density around a memory key.

    Returns density as: unique_agents / max_expected_agents
    Based on arXiv paper density coordination.
    """
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(DISTINCT agent_id) as unique_agents
            FROM memory_access_log
            WHERE memory_key = %s
            AND access_time > NOW() - INTERVAL '%s minutes'
        """, (memory_key, time_window_minutes))

        unique_agents = cur.fetchone()[0]

        # Get total active agents for normalization
        cur.execute("""
            SELECT COUNT(DISTINCT agent_id)
            FROM jr_agent_state
            WHERE last_active > NOW() - INTERVAL '5 minutes'
        """)
        total_agents = max(1, cur.fetchone()[0])

    conn.close()

    # Density = proportion of agents accessing this memory
    density = unique_agents / total_agents
    return round(density, 4)


def calculate_spatial_density(x: float, y: float, radius: float = 1.0) -> float:
    """
    Calculate agent density in spatial region.

    Uses spatial coordinates from memory_access_log.
    """
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(DISTINCT agent_id)
            FROM memory_access_log
            WHERE access_time > NOW() - INTERVAL '30 minutes'
            AND SQRT(POWER(spatial_x - %s, 2) + POWER(spatial_y - %s, 2)) <= %s
        """, (x, y, radius))

        agents_in_area = cur.fetchone()[0]

        # Normalize by area
        area = 3.14159 * radius * radius
        density = agents_in_area / max(1.0, area)

    conn.close()
    return round(density, 4)
```

### Task 3: Implement adaptive_memory_recall()

```python
def adaptive_memory_recall(memory_key: str, agent_id: str) -> list:
    """
    Adaptive memory recall based on density.

    Strategy switch at density threshold 0.230:
    - Below threshold: Global recall (explore)
    - Above threshold: Local recall (exploit)
    """
    density = calculate_agent_density(memory_key)

    conn = get_connection()
    with conn.cursor() as cur:
        if density < DENSITY_THRESHOLD:
            # LOW DENSITY: Global exploration strategy
            # Return diverse memories from different contexts
            cur.execute("""
                SELECT memory_hash, original_content, temperature_score
                FROM thermal_memory_archive
                WHERE original_content ILIKE %s
                ORDER BY RANDOM()
                LIMIT 5
            """, (f'%{memory_key}%',))
            strategy = 'global_explore'
        else:
            # HIGH DENSITY: Local exploitation strategy
            # Return most relevant/hot memories
            cur.execute("""
                SELECT memory_hash, original_content, temperature_score
                FROM thermal_memory_archive
                WHERE original_content ILIKE %s
                ORDER BY temperature_score DESC, created_at DESC
                LIMIT 5
            """, (f'%{memory_key}%',))
            strategy = 'local_exploit'

        memories = cur.fetchall()

        # Log the access for density tracking
        cur.execute("""
            INSERT INTO memory_access_log (agent_id, memory_key, access_type)
            VALUES (%s, %s, 'read')
        """, (agent_id, memory_key))
        conn.commit()

    conn.close()

    return {
        'strategy': strategy,
        'density': density,
        'threshold': DENSITY_THRESHOLD,
        'memories': [
            {'hash': h, 'content': c[:200], 'temp': t}
            for h, c, t in memories
        ]
    }


def log_memory_access(agent_id: str, memory_key: str,
                      access_type: str, x: float = 0, y: float = 0):
    """Log memory access for density tracking."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO memory_access_log
            (agent_id, memory_key, access_type, spatial_x, spatial_y)
            VALUES (%s, %s, %s, %s, %s)
        """, (agent_id, memory_key, access_type, x, y))
        conn.commit()
    conn.close()
```

---

## Integration Points

### Update Jr Task Executor

Modify `jr_task_executor.py` to use adaptive recall:

```python
from lib.stigmergy_coordination import adaptive_memory_recall

def _query_thermal_memory(self, query: str, limit: int = 5) -> str:
    """Use adaptive recall with density awareness."""
    result = adaptive_memory_recall(query[:50], self.agent_id)

    if result['memories']:
        context = f"[Strategy: {result['strategy']}, Density: {result['density']:.3f}]\n"
        for mem in result['memories']:
            context += f"[{mem['temp']:.0f}C] {mem['content']}\n\n"
        return context
    return "No relevant memories found."
```

---

## Deployment Steps

1. Create memory_access_log table on bluefin
2. Create `/ganuda/lib/stigmergy_coordination.py`
3. Update jr_task_executor.py to use adaptive recall
4. Deploy to all Jr executor nodes
5. Monitor density metrics via thermal memory
6. Tune DENSITY_THRESHOLD based on observed behavior

---

## Success Criteria

- [ ] memory_access_log table exists and captures accesses
- [ ] calculate_agent_density() returns values 0.0-1.0
- [ ] adaptive_memory_recall() switches strategies at 0.230
- [ ] Memory accesses are logged automatically
- [ ] Jr executors use density-aware recall

---

*For Seven Generations - Cherokee AI Federation*

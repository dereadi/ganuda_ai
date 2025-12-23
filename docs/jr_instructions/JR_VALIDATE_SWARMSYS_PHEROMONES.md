# JR_VALIDATE_SWARMSYS_PHEROMONES.md
## Cherokee AI Federation - Research Paper Implementation

**Paper**: SwarmSys: Decentralized Swarm-Inspired Agents for Scalable and Adaptive Reasoning
**arXiv**: 2510.10047
**Authors**: Ruohao Li, Hongjun Liu, et al.
**Priority**: 1 (LOW effort - validates existing implementation)
**Council Vote**: PROCEED WITH CAUTION (79.3% confidence)

---

## ULTRATHINK ANALYSIS

### What This Paper Teaches Us

SwarmSys introduces a **closed-loop framework** for distributed multi-agent reasoning that achieves coordination through three specialized roles:

1. **Explorers** - Scout solution space, generate hypotheses
2. **Workers** - Execute on promising paths, implement solutions
3. **Validators** - Verify results, provide quality assurance

The key insight is that coordination emerges through:
- **Adaptive agent profiles** - Agents evolve specializations
- **Embedding-based probabilistic matching** - Tasks matched to agents via embeddings
- **Pheromone-inspired reinforcement** - Success leaves traces that guide future agents

### How This Maps to Cherokee AI Federation

| SwarmSys Concept | Our Implementation | Gap Analysis |
|-----------------|-------------------|--------------|
| Explorers | Jr agents with `strategy` spec | ✅ Similar role |
| Workers | Jr agents with `general` spec | ✅ Similar role |
| Validators | Council voting system | ✅ Similar role |
| Pheromone deposits | `stigmergy_pheromones` table | ⚠️ Partial - needs event types |
| Pheromone decay | `decay_rate` column + cron | ✅ Implemented |
| Embedding matching | A-MEM embeddings | ⚠️ Not connected to task allocation |
| Agent profiles | `jr_agent_state` table | ⚠️ Missing adaptive evolution |

### Critical Validation Tasks

**VALIDATION 1: Pheromone Event Types**

SwarmSys defines specific pheromone types for different events:
- `exploration_success` - Explorer found promising path
- `task_claimed` - Worker claimed task
- `task_completed` - Worker finished successfully
- `validation_pass` - Validator approved result
- `collision_warning` - Multiple agents on same task

Current implementation has generic `pheromone_type` but needs these specific types.

**VALIDATION 2: Probabilistic Task Matching**

SwarmSys uses embedding similarity for task-agent matching:
```
P(agent_i | task_t) ∝ exp(sim(embed(agent_i), embed(task_t)) / τ)
```

We have embeddings in A-MEM but don't use them for task allocation. This is the biggest gap.

**VALIDATION 3: Agent Profile Evolution**

SwarmSys agents maintain evolving profiles based on:
- Success rate per task type
- Average completion time
- Specialization emergence

Our `jr_agent_state` has static `specialization` field - needs history tracking.

---

## IMPLEMENTATION TASKS

### Task 1: Extend Pheromone Types
**Effort**: Low
**Node**: bluefin (database)

Add SwarmSys-aligned pheromone event types:

```sql
-- Add event type enum constraint
ALTER TABLE stigmergy_pheromones 
DROP CONSTRAINT IF EXISTS valid_pheromone_type;

ALTER TABLE stigmergy_pheromones
ADD CONSTRAINT valid_pheromone_type CHECK (
    pheromone_type IN (
        'exploration_success',
        'task_claimed',
        'task_completed',
        'task_failed',
        'validation_pass',
        'validation_fail',
        'collision_warning',
        'success',  -- legacy
        'general'   -- legacy
    )
);

-- Add task context to pheromones
ALTER TABLE stigmergy_pheromones
ADD COLUMN IF NOT EXISTS task_id VARCHAR(64),
ADD COLUMN IF NOT EXISTS task_type VARCHAR(32),
ADD COLUMN IF NOT EXISTS outcome_value FLOAT DEFAULT 0.0;
```

### Task 2: Implement Embedding-Based Task Matching
**Effort**: Medium
**Node**: redfin (Python library)

Create `/ganuda/lib/swarmsys_matching.py`:

```python
#!/usr/bin/env python3
"""
SwarmSys-inspired Task-Agent Matching
Based on arXiv:2510.10047

Uses embedding similarity for probabilistic task allocation.
"""

import numpy as np
from typing import List, Dict, Tuple
import psycopg2
import psycopg2.extras

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

# Temperature parameter for softmax (lower = more deterministic)
TEMPERATURE = 0.5

def get_agent_embedding(agent_id: str) -> np.ndarray:
    """
    Get agent's profile embedding based on recent task history.
    Computed from: specialization keywords + successful task types
    """
    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        # Get agent's recent successful task contexts
        cur.execute("""
            SELECT t.task_content, t.task_type
            FROM jr_task_announcements t
            JOIN jr_task_bids b ON t.task_id = b.task_id
            WHERE b.agent_id = %s AND t.status = 'completed'
            ORDER BY t.completed_at DESC
            LIMIT 10
        """, (agent_id,))
        
        tasks = cur.fetchall()
        
        if not tasks:
            # Return random embedding for new agents
            return np.random.randn(384)
        
        # Combine task contents for embedding
        combined_text = ' '.join([t['task_content'] for t in tasks])
        
        # Use A-MEM's embedding function
        from amem_memory import get_embedding_model
        model = get_embedding_model()
        return model.encode(combined_text)
    
    conn.close()

def get_task_embedding(task_content: str) -> np.ndarray:
    """Get embedding for task description."""
    from amem_memory import get_embedding_model
    model = get_embedding_model()
    return model.encode(task_content)

def probabilistic_match(task_id: str, task_content: str, 
                        candidate_agents: List[str]) -> List[Tuple[str, float]]:
    """
    SwarmSys probabilistic matching.
    
    Returns agents ranked by probability:
    P(agent_i | task_t) ∝ exp(sim(embed(agent_i), embed(task_t)) / τ)
    """
    task_embed = get_task_embedding(task_content)
    
    scores = []
    for agent_id in candidate_agents:
        agent_embed = get_agent_embedding(agent_id)
        
        # Cosine similarity
        similarity = np.dot(task_embed, agent_embed) / (
            np.linalg.norm(task_embed) * np.linalg.norm(agent_embed)
        )
        scores.append((agent_id, similarity))
    
    # Softmax with temperature
    similarities = np.array([s[1] for s in scores])
    exp_scores = np.exp(similarities / TEMPERATURE)
    probabilities = exp_scores / exp_scores.sum()
    
    return sorted(
        [(scores[i][0], probabilities[i]) for i in range(len(scores))],
        key=lambda x: x[1],
        reverse=True
    )

def read_pheromone_landscape(location_id: str) -> Dict[str, float]:
    """
    Read all pheromone traces at a location.
    Used to inform agent decisions.
    """
    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT pheromone_type, SUM(intensity) as total_intensity
            FROM stigmergy_pheromones
            WHERE location_id = %s
            GROUP BY pheromone_type
        """, (location_id,))
        
        landscape = {row['pheromone_type']: row['total_intensity'] 
                     for row in cur.fetchall()}
    
    conn.close()
    return landscape

def should_explore(location_id: str) -> bool:
    """
    SwarmSys exploration vs exploitation decision.
    Explore if:
    - Low total pheromone (unexplored territory)
    - High failure pheromone (needs new approach)
    """
    landscape = read_pheromone_landscape(location_id)
    
    total_intensity = sum(landscape.values())
    failure_ratio = landscape.get('task_failed', 0) / max(total_intensity, 0.1)
    
    # Explore if low activity or high failure
    return total_intensity < 2.0 or failure_ratio > 0.5
```

### Task 3: Add Agent Profile Evolution
**Effort**: Low
**Node**: bluefin (database) + redfin (Python)

```sql
-- Create agent performance history table
CREATE TABLE IF NOT EXISTS jr_agent_performance (
    perf_id SERIAL PRIMARY KEY,
    agent_id VARCHAR(64) NOT NULL,
    task_type VARCHAR(32),
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    avg_completion_time_ms FLOAT DEFAULT 0,
    specialization_score FLOAT DEFAULT 0.0,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(agent_id, task_type)
);

CREATE INDEX IF NOT EXISTS idx_agent_perf_agent ON jr_agent_performance(agent_id);

-- Function to update agent profile after task completion
CREATE OR REPLACE FUNCTION update_agent_profile()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' THEN
        INSERT INTO jr_agent_performance (agent_id, task_type, success_count, updated_at)
        VALUES (NEW.assigned_to, NEW.task_type, 1, NOW())
        ON CONFLICT (agent_id, task_type) DO UPDATE SET
            success_count = jr_agent_performance.success_count + 1,
            specialization_score = (jr_agent_performance.success_count + 1)::float / 
                GREATEST(jr_agent_performance.success_count + jr_agent_performance.failure_count + 1, 1),
            updated_at = NOW();
    ELSIF NEW.status = 'failed' THEN
        INSERT INTO jr_agent_performance (agent_id, task_type, failure_count, updated_at)
        VALUES (NEW.assigned_to, NEW.task_type, 1, NOW())
        ON CONFLICT (agent_id, task_type) DO UPDATE SET
            failure_count = jr_agent_performance.failure_count + 1,
            specialization_score = jr_agent_performance.success_count::float / 
                GREATEST(jr_agent_performance.success_count + jr_agent_performance.failure_count + 1, 1),
            updated_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger
DROP TRIGGER IF EXISTS trg_update_agent_profile ON jr_task_announcements;
CREATE TRIGGER trg_update_agent_profile
    AFTER UPDATE OF status ON jr_task_announcements
    FOR EACH ROW
    WHEN (NEW.status IN ('completed', 'failed'))
    EXECUTE FUNCTION update_agent_profile();
```

### Task 4: Integrate with Jr Bidding Daemon
**Effort**: Medium
**Node**: redfin

Modify `/ganuda/services/jr_bidding_daemon.py` to use SwarmSys matching:

```python
# In calculate_bid_score(), add embedding similarity:

from swarmsys_matching import probabilistic_match, should_explore

def enhanced_bid_score(agent_id: str, task: dict, base_score: float) -> float:
    """
    Enhance bid score with SwarmSys factors:
    1. Embedding similarity (probabilistic matching)
    2. Pheromone landscape guidance
    3. Exploration vs exploitation balance
    """
    # Get probabilistic match score
    matches = probabilistic_match(task['task_id'], task['task_content'], [agent_id])
    embed_score = matches[0][1] if matches else 0.5
    
    # Check pheromone landscape
    if should_explore(task['task_id']):
        # Boost exploration-oriented agents (strategy specialists)
        exploration_bonus = 0.2 if 'strategy' in (task.get('specialization') or '') else 0
    else:
        exploration_bonus = 0
    
    # Combined score
    return base_score * 0.5 + embed_score * 0.3 + exploration_bonus + 0.2
```

---

## VALIDATION CHECKLIST

After implementation, validate against SwarmSys metrics:

- [ ] Pheromone deposits increase after successful task completion
- [ ] Pheromone decay reduces stale traces over time
- [ ] Embedding similarity correlates with task success rate
- [ ] Agent specialization emerges (visible in jr_agent_performance)
- [ ] Collision warnings appear when multiple agents bid on same task
- [ ] Exploration mode activates for low-pheromone territories

---

## SUCCESS METRICS

| Metric | SwarmSys Baseline | Cherokee Target |
|--------|-------------------|-----------------|
| Task completion rate | 85% | >80% |
| Agent specialization emergence | Yes | Observable in data |
| Pheromone-guided decisions | 70% | >50% |
| Collision avoidance | 95% | >90% |

---

## SEVEN GENERATIONS CONSIDERATION

This enhancement validates our existing direction while adding:
- **Self-organizing behavior** - Less manual intervention needed
- **Emergent specialization** - Agents find their strengths naturally
- **Resilience** - Decentralized coordination survives node failures

For Seven Generations - knowledge that guides without commanding.

---

*Created: December 23, 2025*
*Council Vote Audit Hash: aae46bac2393cb44*

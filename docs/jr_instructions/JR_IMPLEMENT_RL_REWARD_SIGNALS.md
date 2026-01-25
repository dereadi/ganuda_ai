# Jr Task: Implement Reinforcement Learning Reward Signals in Thermal Memory

**Task ID:** task-rl-rewards-001
**Priority:** P3 (Council Voted)
**Node:** bluefin (database), redfin (gateway)
**Created:** December 22, 2025
**Research Basis:** arXiv:2509.20095 - From Pheromones to Policies: Reinforcement Learning for Engineered Biological Swarms
**Council Vote:** f0d882b6d8ed0162 (79.5% confidence)

---

## Executive Summary

The paper arXiv:2509.20095 proves a **mathematical equivalence between pheromone-mediated aggregation and reinforcement learning**:

> "Stigmergic signals function as distributed reward mechanisms... environmental signals act as external memory for collective credit assignment."

Our thermal memory system currently has:
- ✅ **Decay** (pheromone evaporation): Nightly 5% temperature reduction
- ❌ **Reward** (reinforcement): Missing - no positive feedback when memories help
- ❌ **Penalty** (negative reinforcement): Missing - no negative feedback when memories mislead

This task transforms thermal memory into a **true distributed RL system** by adding reward and penalty signals.

---

## Theoretical Foundation

### Current System (Decay Only)

```
Temperature(t+1) = Temperature(t) × 0.95  (nightly decay)
```

This means all memories slowly cool down, regardless of usefulness. Hot memories stay hot only because they were created with high temperature.

### RL-Enhanced System (Decay + Reward + Penalty)

```
Temperature(t+1) = Temperature(t) × decay_rate + reward - penalty

Where:
- decay_rate = 0.95 (unchanged)
- reward = +R if memory contributed to successful outcome
- penalty = -P if memory contributed to failed outcome
```

### Biological Analogy

| Ant Colony | Thermal Memory |
|------------|----------------|
| Ant finds food via trail | Jr uses memory to complete task |
| Ant reinforces trail with pheromone | Memory temperature increases |
| Trail not used, pheromone evaporates | Memory temperature decays nightly |
| Trail leads to dead end | Memory temperature decreases |

---

## Implementation Plan

### Phase 1: Track Memory Usage in Tasks

#### 1.1 Add Memory Attribution Table

```sql
-- On bluefin (zammad_production)

CREATE TABLE IF NOT EXISTS memory_usage_attribution (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(128) NOT NULL,
    memory_hash VARCHAR(128) NOT NULL,
    agent_id VARCHAR(64),

    -- Usage context
    usage_type VARCHAR(32),         -- 'recalled', 'cited', 'applied'
    usage_weight FLOAT DEFAULT 1.0, -- How central was this memory (0-1)
    usage_time TIMESTAMP DEFAULT NOW(),

    -- Outcome attribution (filled after task completes)
    task_outcome VARCHAR(32),       -- 'success', 'partial', 'failure'
    outcome_contribution FLOAT,     -- This memory's contribution to outcome (-1 to +1)
    reward_applied FLOAT,           -- Actual reward/penalty applied

    FOREIGN KEY (memory_hash) REFERENCES thermal_memory_archive(memory_hash)
        ON DELETE CASCADE
);

CREATE INDEX idx_memory_usage_task ON memory_usage_attribution(task_id);
CREATE INDEX idx_memory_usage_hash ON memory_usage_attribution(memory_hash);
CREATE INDEX idx_memory_usage_outcome ON memory_usage_attribution(task_outcome);
```

#### 1.2 Function to Record Memory Usage

```sql
CREATE OR REPLACE FUNCTION record_memory_usage(
    p_task_id VARCHAR(128),
    p_memory_hash VARCHAR(128),
    p_agent_id VARCHAR(64),
    p_usage_type VARCHAR(32) DEFAULT 'recalled',
    p_usage_weight FLOAT DEFAULT 1.0
) RETURNS VOID AS $$
BEGIN
    INSERT INTO memory_usage_attribution
        (task_id, memory_hash, agent_id, usage_type, usage_weight)
    VALUES
        (p_task_id, p_memory_hash, p_agent_id, p_usage_type, p_usage_weight);
END;
$$ LANGUAGE plpgsql;
```

---

### Phase 2: Define Reward/Penalty Constants

#### 2.1 RL Configuration Table

```sql
CREATE TABLE IF NOT EXISTS thermal_rl_config (
    config_key VARCHAR(64) PRIMARY KEY,
    config_value FLOAT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Insert default values based on RL best practices
INSERT INTO thermal_rl_config (config_key, config_value, description) VALUES
    ('reward_success', 5.0, 'Temperature boost for memories that helped successful task'),
    ('reward_partial', 2.0, 'Temperature boost for memories in partially successful task'),
    ('penalty_failure', -2.0, 'Temperature reduction for memories in failed task'),
    ('penalty_misleading', -5.0, 'Temperature reduction for explicitly misleading memories'),
    ('max_temperature', 100.0, 'Maximum temperature cap'),
    ('min_temperature', 1.0, 'Minimum temperature floor (never fully forget)'),
    ('decay_rate', 0.95, 'Nightly decay multiplier'),
    ('attribution_decay', 0.8, 'Weight decay for indirect contributions')
ON CONFLICT (config_key) DO NOTHING;
```

#### 2.2 Get Config Function

```sql
CREATE OR REPLACE FUNCTION get_rl_config(p_key VARCHAR(64))
RETURNS FLOAT AS $$
DECLARE
    v_value FLOAT;
BEGIN
    SELECT config_value INTO v_value FROM thermal_rl_config WHERE config_key = p_key;
    RETURN COALESCE(v_value, 0.0);
END;
$$ LANGUAGE plpgsql;
```

---

### Phase 3: Implement Reward/Penalty Application

#### 3.1 Apply Task Outcome Rewards

```sql
CREATE OR REPLACE FUNCTION apply_task_outcome_rewards(
    p_task_id VARCHAR(128),
    p_outcome VARCHAR(32),  -- 'success', 'partial', 'failure'
    p_misleading_memories VARCHAR(128)[] DEFAULT NULL  -- Explicitly bad memories
) RETURNS TABLE (
    memory_hash VARCHAR(128),
    old_temperature FLOAT,
    new_temperature FLOAT,
    reward_applied FLOAT
) AS $$
DECLARE
    v_reward FLOAT;
    v_max_temp FLOAT;
    v_min_temp FLOAT;
BEGIN
    -- Get configuration
    v_max_temp := get_rl_config('max_temperature');
    v_min_temp := get_rl_config('min_temperature');

    -- Determine base reward based on outcome
    CASE p_outcome
        WHEN 'success' THEN v_reward := get_rl_config('reward_success');
        WHEN 'partial' THEN v_reward := get_rl_config('reward_partial');
        WHEN 'failure' THEN v_reward := get_rl_config('penalty_failure');
        ELSE v_reward := 0.0;
    END CASE;

    -- Update memory_usage_attribution with outcome
    UPDATE memory_usage_attribution
    SET task_outcome = p_outcome,
        outcome_contribution = CASE
            WHEN memory_hash = ANY(COALESCE(p_misleading_memories, ARRAY[]::VARCHAR(128)[]))
            THEN -1.0
            ELSE usage_weight
        END
    WHERE memory_usage_attribution.task_id = p_task_id;

    -- Apply rewards to each memory used
    RETURN QUERY
    WITH updated AS (
        UPDATE thermal_memory_archive t
        SET temperature_score = GREATEST(
            v_min_temp,
            LEAST(
                v_max_temp,
                t.temperature_score + (
                    v_reward * COALESCE(u.usage_weight, 1.0) *
                    CASE
                        WHEN t.memory_hash = ANY(COALESCE(p_misleading_memories, ARRAY[]::VARCHAR(128)[]))
                        THEN get_rl_config('penalty_misleading') / v_reward  -- Override with harsh penalty
                        ELSE 1.0
                    END
                )
            )
        )
        FROM memory_usage_attribution u
        WHERE u.task_id = p_task_id
          AND u.memory_hash = t.memory_hash
        RETURNING t.memory_hash,
                  t.temperature_score - (v_reward * COALESCE(u.usage_weight, 1.0)) as old_temp,
                  t.temperature_score as new_temp,
                  v_reward * COALESCE(u.usage_weight, 1.0) as applied_reward
    )
    SELECT * FROM updated;

    -- Record rewards applied
    UPDATE memory_usage_attribution u
    SET reward_applied = (
        SELECT new_temp - old_temp
        FROM thermal_memory_archive t
        WHERE t.memory_hash = u.memory_hash
    )
    WHERE u.task_id = p_task_id;

END;
$$ LANGUAGE plpgsql;
```

---

### Phase 4: Integrate with Task Completion

#### 4.1 Update Jr Executor for RL Feedback

In `/ganuda/jr_executor/jr_executor.py`:

```python
class JrExecutor:

    def __init__(self):
        self.memories_used = []  # Track memories used during task

    def recall_memory(self, query: str, task_id: str) -> list:
        """
        Recall memories and track usage for RL attribution
        """
        memories = self.db_recall(query)

        # Record each memory usage for later reward attribution
        for memory in memories:
            self.memories_used.append(memory['memory_hash'])
            self.db_execute("""
                SELECT record_memory_usage(%s, %s, %s, 'recalled', %s)
            """, (
                task_id,
                memory['memory_hash'],
                self.agent_id,
                memory.get('relevance_score', 1.0)  # Weight by relevance
            ))

        return memories

    def complete_task(self, task_id: str, outcome: str,
                      misleading_memories: list = None):
        """
        Complete task and apply RL rewards to used memories
        Based on arXiv:2509.20095
        """
        # Apply rewards/penalties
        results = self.db_query("""
            SELECT * FROM apply_task_outcome_rewards(%s, %s, %s)
        """, (task_id, outcome, misleading_memories))

        # Log the RL feedback
        for row in results:
            self.log(f"RL Feedback: {row['memory_hash'][:16]}... "
                    f"{row['old_temperature']:.1f}° → {row['new_temperature']:.1f}° "
                    f"({row['reward_applied']:+.1f})")

        # Clear tracking
        self.memories_used = []

        # Record to thermal memory as meta-learning
        if len(results) > 0:
            self.record_rl_event(task_id, outcome, results)

    def record_rl_event(self, task_id: str, outcome: str, results: list):
        """Record RL feedback event to thermal memory itself"""
        total_reward = sum(r['reward_applied'] for r in results)
        self.db_execute("""
            INSERT INTO thermal_memory_archive (memory_hash, original_content, temperature_score, metadata)
            VALUES (%s, %s, 50.0, %s)
        """, (
            f"rl-event-{task_id[:16]}",
            f"RL EVENT: Task {task_id} outcome={outcome}. "
            f"Applied {total_reward:+.1f}° total across {len(results)} memories.",
            json.dumps({'type': 'rl_feedback', 'outcome': outcome})
        ))
```

---

### Phase 5: Explicit Feedback API

#### 5.1 Add Gateway Endpoints for Manual Feedback

In `/ganuda/services/llm_gateway/gateway.py`:

```python
@app.route('/v1/memory/reward', methods=['POST'])
def reward_memory():
    """
    POST /v1/memory/reward
    {
        "memory_hash": "abc123...",
        "reward": 5.0,        // Positive for helpful, negative for misleading
        "reason": "Helped solve the authentication bug",
        "agent_id": "jr-redfin-gecko"
    }

    Manually apply reward/penalty to a memory (arXiv:2509.20095)
    """
    data = request.json
    memory_hash = data.get('memory_hash')
    reward = data.get('reward', 0.0)
    reason = data.get('reason', '')
    agent_id = data.get('agent_id', 'manual')

    if not memory_hash:
        return jsonify({'error': 'memory_hash required'}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    # Apply reward with bounds
    cur.execute("""
        UPDATE thermal_memory_archive
        SET temperature_score = GREATEST(
            (SELECT config_value FROM thermal_rl_config WHERE config_key = 'min_temperature'),
            LEAST(
                (SELECT config_value FROM thermal_rl_config WHERE config_key = 'max_temperature'),
                temperature_score + %s
            )
        )
        WHERE memory_hash = %s
        RETURNING temperature_score
    """, (reward, memory_hash))

    result = cur.fetchone()

    # Log the feedback
    cur.execute("""
        INSERT INTO memory_usage_attribution
            (task_id, memory_hash, agent_id, usage_type, reward_applied)
        VALUES
            (%s, %s, %s, 'manual_feedback', %s)
    """, (f"manual-{datetime.now().isoformat()}", memory_hash, agent_id, reward))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        'memory_hash': memory_hash,
        'reward_applied': reward,
        'new_temperature': result[0] if result else None,
        'reason': reason
    })


@app.route('/v1/memory/feedback', methods=['POST'])
def task_feedback():
    """
    POST /v1/memory/feedback
    {
        "task_id": "task-123",
        "outcome": "success",           // 'success', 'partial', 'failure'
        "misleading_memories": ["hash1", "hash2"]  // Optional
    }

    Apply RL feedback for all memories used in a task
    """
    data = request.json
    task_id = data.get('task_id')
    outcome = data.get('outcome')
    misleading = data.get('misleading_memories', [])

    if not task_id or not outcome:
        return jsonify({'error': 'task_id and outcome required'}), 400

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT * FROM apply_task_outcome_rewards(%s, %s, %s)
    """, (task_id, outcome, misleading))

    results = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        'task_id': task_id,
        'outcome': outcome,
        'memories_updated': len(results),
        'updates': [
            {
                'memory_hash': r['memory_hash'],
                'old_temp': r['old_temperature'],
                'new_temp': r['new_temperature'],
                'reward': r['reward_applied']
            }
            for r in results
        ]
    })
```

---

### Phase 6: RL Metrics Dashboard

#### 6.1 Create RL Metrics View

```sql
CREATE OR REPLACE VIEW rl_metrics AS
SELECT
    DATE(usage_time) as date,
    task_outcome,
    COUNT(*) as memory_uses,
    SUM(reward_applied) as total_reward,
    AVG(reward_applied) as avg_reward,
    COUNT(DISTINCT memory_hash) as unique_memories,
    COUNT(DISTINCT agent_id) as unique_agents
FROM memory_usage_attribution
WHERE task_outcome IS NOT NULL
GROUP BY DATE(usage_time), task_outcome
ORDER BY date DESC, task_outcome;
```

#### 6.2 Grafana Queries

```sql
-- Panel 1: Daily Reward Distribution
SELECT
    date,
    SUM(CASE WHEN task_outcome = 'success' THEN total_reward ELSE 0 END) as success_rewards,
    SUM(CASE WHEN task_outcome = 'partial' THEN total_reward ELSE 0 END) as partial_rewards,
    SUM(CASE WHEN task_outcome = 'failure' THEN total_reward ELSE 0 END) as failure_penalties
FROM rl_metrics
WHERE date > CURRENT_DATE - INTERVAL '30 days'
GROUP BY date
ORDER BY date;

-- Panel 2: Memory Temperature Distribution Over Time
SELECT
    DATE(created_at) as date,
    AVG(temperature_score) as avg_temp,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY temperature_score) as median_temp,
    MAX(temperature_score) as max_temp,
    MIN(temperature_score) as min_temp
FROM thermal_memory_archive
GROUP BY DATE(created_at)
ORDER BY date DESC
LIMIT 30;

-- Panel 3: Top Rewarded Memories (Most Helpful)
SELECT
    memory_hash,
    LEFT(original_content, 100) as content_preview,
    temperature_score,
    (SELECT SUM(reward_applied) FROM memory_usage_attribution
     WHERE memory_usage_attribution.memory_hash = thermal_memory_archive.memory_hash) as lifetime_reward
FROM thermal_memory_archive
ORDER BY lifetime_reward DESC NULLS LAST
LIMIT 10;
```

---

### Phase 7: Update Nightly Decay Script

Update `/ganuda/scripts/pheromone_decay.sh` on bluefin:

```bash
#!/bin/bash
# Pheromone Decay with RL Integration
# Based on arXiv:2509.20095
# Runs nightly at 3:33 AM

LOG_FILE="/var/log/ganuda/pheromone_decay.log"

echo "[$(date)] Starting pheromone decay + RL maintenance" >> $LOG_FILE

PGPASSWORD='jawaseatlasers2' psql -h 127.0.0.1 -U claude -d zammad_production << EOF >> $LOG_FILE 2>&1

-- Get current stats before decay
\echo 'Pre-decay statistics:'
SELECT
    COUNT(*) as total_memories,
    AVG(temperature_score) as avg_temp,
    SUM(CASE WHEN temperature_score >= 90 THEN 1 ELSE 0 END) as hot_count,
    SUM(CASE WHEN temperature_score < 10 THEN 1 ELSE 0 END) as cold_count
FROM thermal_memory_archive;

-- Apply decay (respecting min temperature from RL config)
UPDATE thermal_memory_archive
SET temperature_score = GREATEST(
    (SELECT config_value FROM thermal_rl_config WHERE config_key = 'min_temperature'),
    temperature_score * (SELECT config_value FROM thermal_rl_config WHERE config_key = 'decay_rate')
)
WHERE temperature_score > (SELECT config_value FROM thermal_rl_config WHERE config_key = 'min_temperature');

\echo 'Post-decay statistics:'
SELECT
    COUNT(*) as total_memories,
    AVG(temperature_score) as avg_temp,
    SUM(CASE WHEN temperature_score >= 90 THEN 1 ELSE 0 END) as hot_count,
    SUM(CASE WHEN temperature_score < 10 THEN 1 ELSE 0 END) as cold_count
FROM thermal_memory_archive;

-- Calculate daily RL impact
\echo 'RL impact (last 24 hours):'
SELECT
    task_outcome,
    COUNT(*) as events,
    SUM(reward_applied) as total_temp_change
FROM memory_usage_attribution
WHERE usage_time > NOW() - INTERVAL '24 hours'
  AND reward_applied IS NOT NULL
GROUP BY task_outcome;

-- Archive RL metrics to thermal memory
INSERT INTO thermal_memory_archive (memory_hash, original_content, temperature_score, metadata)
SELECT
    'rl-daily-' || TO_CHAR(NOW(), 'YYYYMMDD'),
    'RL DAILY STATS: ' ||
    'success_rewards=' || COALESCE(SUM(CASE WHEN task_outcome='success' THEN reward_applied END), 0) ||
    ', partial_rewards=' || COALESCE(SUM(CASE WHEN task_outcome='partial' THEN reward_applied END), 0) ||
    ', failure_penalties=' || COALESCE(SUM(CASE WHEN task_outcome='failure' THEN reward_applied END), 0) ||
    ', memories_affected=' || COUNT(DISTINCT memory_hash),
    50.0,
    '{"type": "rl_daily_stats"}'::jsonb
FROM memory_usage_attribution
WHERE usage_time > NOW() - INTERVAL '24 hours'
  AND reward_applied IS NOT NULL
ON CONFLICT (memory_hash) DO UPDATE
SET original_content = EXCLUDED.original_content,
    temperature_score = 50.0;

-- Cleanup old attribution logs (keep 90 days)
DELETE FROM memory_usage_attribution
WHERE usage_time < NOW() - INTERVAL '90 days';

VACUUM ANALYZE memory_usage_attribution;
VACUUM ANALYZE thermal_memory_archive;

EOF

echo "[$(date)] Pheromone decay + RL maintenance complete" >> $LOG_FILE
```

---

## Testing

### Test 1: Record Memory Usage

```bash
# Simulate a task using memories
PGPASSWORD='jawaseatlasers2' psql -h 127.0.0.1 -U claude -d zammad_production -c "
SELECT record_memory_usage('test-task-001', 'phase2-services-20251221', 'jr-test', 'recalled', 0.8);
SELECT record_memory_usage('test-task-001', 'council-sag-django-8ce23768', 'jr-test', 'applied', 1.0);
"
```

### Test 2: Apply Successful Outcome

```bash
PGPASSWORD='jawaseatlasers2' psql -h 127.0.0.1 -U claude -d zammad_production -c "
SELECT * FROM apply_task_outcome_rewards('test-task-001', 'success', NULL);
"
```

### Test 3: Apply Failure with Misleading Memory

```bash
PGPASSWORD='jawaseatlasers2' psql -h 127.0.0.1 -U claude -d zammad_production -c "
SELECT * FROM apply_task_outcome_rewards(
    'test-task-002',
    'failure',
    ARRAY['some-misleading-memory-hash']
);
"
```

### Test 4: API Feedback Endpoint

```bash
curl -X POST "http://192.168.132.223:8080/v1/memory/feedback" \
  -H "Content-Type: application/json" \
  -d '{"task_id": "test-task-001", "outcome": "success"}'
```

---

## Success Criteria

1. ✅ memory_usage_attribution table tracks memory-task associations
2. ✅ thermal_rl_config stores tunable RL parameters
3. ✅ apply_task_outcome_rewards() correctly updates temperatures
4. ✅ Gateway endpoints allow manual and automatic feedback
5. ✅ Nightly decay respects RL configuration
6. ✅ Grafana dashboard shows RL metrics
7. ✅ Hot memories that help stay hot; misleading memories cool faster

---

## Expected Behavior

### Before RL (Current)

```
Memory A: Created at 80° → decays to 76° → 72.2° → 68.6° (regardless of usefulness)
Memory B: Created at 80° → decays to 76° → 72.2° → 68.6° (regardless of usefulness)
```

### After RL (This Implementation)

```
Memory A (helpful): 80° → used in success (+5) = 85° → decay = 80.75° → used (+5) = 85.75°
Memory B (misleading): 80° → used in failure (-5) = 75° → decay = 71.25° → misleading (-5) = 66.25°
```

Over time, helpful memories stabilize at high temperatures while misleading memories fade.

---

## References

- arXiv:2509.20095 - From Pheromones to Policies: Reinforcement Learning for Engineered Biological Swarms
- Council Vote: f0d882b6d8ed0162 (79.5% confidence)
- Cherokee AI thermal_memory_archive: 6,700+ memories
- Nightly cron: /ganuda/scripts/pheromone_decay.sh

---

*For Seven Generations - Cherokee AI Federation*

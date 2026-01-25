# Jr Task: Implement Density-Aware Stigmergic Coordination

**Task ID:** task-stigmergy-density-001
**Priority:** P1 (Council Voted)
**Node:** bluefin (database), redfin (gateway)
**Created:** December 22, 2025
**Research Basis:** arXiv:2512.10166 - Emergent Collective Memory in Decentralized Multi-Agent AI Systems
**Council Vote:** f0d882b6d8ed0162 (79.5% confidence)

---

## Executive Summary

The December 2025 paper arXiv:2512.10166 proves that multi-agent systems perform optimally when they **switch coordination strategies based on agent density**:

- **Below ρc = 0.230**: Individual memory outperforms (68.7% improvement over baseline)
- **Above ρc = 0.230**: Stigmergic coordination outperforms by 36-41%

Our thermal memory system currently uses a fixed strategy. This task implements **adaptive coordination** that automatically switches based on measured agent density.

---

## Theoretical Foundation

### What is Agent Density (ρ)?

Agent density measures how many agents are actively accessing shared memory within a time window:

```
ρ = (active_agents) / (total_memory_capacity)
```

In our context:
- **active_agents** = unique Jr agents + API clients accessing thermal memory in last N minutes
- **total_memory_capacity** = normalized by total memory count

### Why ρc = 0.230?

At low density, agents benefit more from their own reasoning (individual memory). At high density, the "wisdom of the crowd" in thermal memory (stigmergic traces) becomes more valuable because many agents have reinforced useful paths.

### Current Cherokee AI Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    THERMAL MEMORY                        │
│              (thermal_memory_archive)                    │
│                                                          │
│   Memory 1 [temp: 95°]  ←── accessed by many agents     │
│   Memory 2 [temp: 72°]  ←── moderate access              │
│   Memory 3 [temp: 23°]  ←── rarely accessed              │
│                                                          │
│   Current: Fixed decay (5% nightly)                      │
│   Missing: Density-aware retrieval strategy              │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Add Access Tracking

#### 1.1 Create Memory Access Log Table

```sql
-- On bluefin (zammad_production)

CREATE TABLE IF NOT EXISTS memory_access_log (
    id SERIAL PRIMARY KEY,
    memory_hash VARCHAR(128) NOT NULL,
    agent_id VARCHAR(64),           -- Jr agent or API client identifier
    access_type VARCHAR(32),        -- 'query', 'recall', 'reinforce'
    access_time TIMESTAMP DEFAULT NOW(),
    context_hash VARCHAR(64),       -- Hash of the query/task context
    outcome VARCHAR(32) DEFAULT 'pending'  -- 'success', 'failure', 'pending'
);

CREATE INDEX idx_memory_access_time ON memory_access_log(access_time);
CREATE INDEX idx_memory_access_agent ON memory_access_log(agent_id);
CREATE INDEX idx_memory_access_hash ON memory_access_log(memory_hash);

-- Partition by time for performance (optional)
-- Keep 30 days of access logs
```

#### 1.2 Create Density Calculation Function

```sql
CREATE OR REPLACE FUNCTION calculate_agent_density(
    window_minutes INTEGER DEFAULT 15
) RETURNS FLOAT AS $$
DECLARE
    active_agents INTEGER;
    total_memories INTEGER;
    density FLOAT;
BEGIN
    -- Count unique agents in time window
    SELECT COUNT(DISTINCT agent_id) INTO active_agents
    FROM memory_access_log
    WHERE access_time > NOW() - (window_minutes || ' minutes')::INTERVAL;

    -- Get total memory count (normalized)
    SELECT COUNT(*) INTO total_memories
    FROM thermal_memory_archive
    WHERE temperature_score > 10;  -- Only count "alive" memories

    -- Calculate density (normalized to 0-1 range)
    -- Assuming max 50 concurrent agents as baseline
    density := active_agents::FLOAT / GREATEST(50.0, total_memories / 100.0);

    RETURN LEAST(density, 1.0);  -- Cap at 1.0
END;
$$ LANGUAGE plpgsql;
```

#### 1.3 Create Density Metrics View

```sql
CREATE OR REPLACE VIEW density_metrics AS
SELECT
    calculate_agent_density(5) as density_5min,
    calculate_agent_density(15) as density_15min,
    calculate_agent_density(60) as density_1hour,
    (SELECT COUNT(DISTINCT agent_id)
     FROM memory_access_log
     WHERE access_time > NOW() - INTERVAL '15 minutes') as active_agents,
    0.230 as critical_threshold,
    CASE
        WHEN calculate_agent_density(15) > 0.230 THEN 'stigmergic'
        ELSE 'individual'
    END as recommended_strategy;
```

---

### Phase 2: Modify Memory Recall Strategy

#### 2.1 Create Adaptive Recall Function

```sql
CREATE OR REPLACE FUNCTION adaptive_memory_recall(
    search_query TEXT,
    agent_id VARCHAR(64),
    max_results INTEGER DEFAULT 10
) RETURNS TABLE (
    memory_hash VARCHAR(128),
    content TEXT,
    temperature FLOAT,
    relevance_score FLOAT,
    strategy_used VARCHAR(32)
) AS $$
DECLARE
    current_density FLOAT;
    strategy VARCHAR(32);
BEGIN
    -- Get current density
    current_density := calculate_agent_density(15);

    -- Determine strategy
    IF current_density > 0.230 THEN
        strategy := 'stigmergic';
    ELSE
        strategy := 'individual';
    END IF;

    -- Log this access
    INSERT INTO memory_access_log (memory_hash, agent_id, access_type, context_hash)
    VALUES ('QUERY', agent_id, 'query', MD5(search_query));

    IF strategy = 'stigmergic' THEN
        -- HIGH DENSITY: Favor hot memories (collective wisdom)
        -- Weight temperature more heavily
        RETURN QUERY
        SELECT
            t.memory_hash,
            t.original_content,
            t.temperature_score,
            (t.temperature_score / 100.0 * 0.7 +
             ts_rank(to_tsvector('english', t.original_content),
                     plainto_tsquery('english', search_query)) * 0.3
            ) as relevance,
            'stigmergic'::VARCHAR(32)
        FROM thermal_memory_archive t
        WHERE t.original_content ILIKE '%' || search_query || '%'
           OR to_tsvector('english', t.original_content) @@ plainto_tsquery('english', search_query)
        ORDER BY relevance DESC
        LIMIT max_results;
    ELSE
        -- LOW DENSITY: Favor relevance over temperature (individual reasoning)
        -- Weight content match more heavily
        RETURN QUERY
        SELECT
            t.memory_hash,
            t.original_content,
            t.temperature_score,
            (t.temperature_score / 100.0 * 0.3 +
             ts_rank(to_tsvector('english', t.original_content),
                     plainto_tsquery('english', search_query)) * 0.7
            ) as relevance,
            'individual'::VARCHAR(32)
        FROM thermal_memory_archive t
        WHERE t.original_content ILIKE '%' || search_query || '%'
           OR to_tsvector('english', t.original_content) @@ plainto_tsquery('english', search_query)
        ORDER BY relevance DESC
        LIMIT max_results;
    END IF;
END;
$$ LANGUAGE plpgsql;
```

---

### Phase 3: Integrate with LLM Gateway

#### 3.1 Update Gateway Memory Recall

In `/ganuda/services/llm_gateway/gateway.py`, modify the memory recall function:

```python
# Add to gateway.py

import psycopg2
from psycopg2.extras import RealDictCursor

def get_density_strategy():
    """Get current density and recommended strategy"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM density_metrics")
    metrics = cur.fetchone()
    cur.close()
    conn.close()
    return metrics

def adaptive_memory_recall(query: str, agent_id: str = "gateway", limit: int = 10):
    """
    Recall memories using density-aware strategy
    Based on arXiv:2512.10166
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "SELECT * FROM adaptive_memory_recall(%s, %s, %s)",
        (query, agent_id, limit)
    )

    memories = cur.fetchall()
    strategy_used = memories[0]['strategy_used'] if memories else 'none'

    cur.close()
    conn.close()

    return {
        'memories': memories,
        'strategy': strategy_used,
        'density': get_density_strategy()
    }


# Add new endpoint
@app.route('/v1/memory/adaptive', methods=['POST'])
def adaptive_memory_endpoint():
    """
    POST /v1/memory/adaptive
    {
        "query": "search terms",
        "agent_id": "jr-redfin-gecko",
        "limit": 10
    }

    Returns memories using density-aware strategy (arXiv:2512.10166)
    """
    data = request.json
    result = adaptive_memory_recall(
        query=data.get('query', ''),
        agent_id=data.get('agent_id', 'anonymous'),
        limit=data.get('limit', 10)
    )
    return jsonify(result)


@app.route('/v1/memory/density', methods=['GET'])
def density_status():
    """Get current density metrics"""
    return jsonify(get_density_strategy())
```

---

### Phase 4: Add Monitoring Dashboard

#### 4.1 Grafana Query for Density

```sql
-- For Grafana dashboard on bluefin:3000

-- Panel 1: Current Density Gauge
SELECT
    calculate_agent_density(15) as "Current Density",
    0.230 as "Critical Threshold"
FROM (SELECT 1) as dummy;

-- Panel 2: Density Over Time
SELECT
    date_trunc('minute', access_time) as time,
    COUNT(DISTINCT agent_id)::float / 50.0 as density
FROM memory_access_log
WHERE access_time > NOW() - INTERVAL '24 hours'
GROUP BY 1
ORDER BY 1;

-- Panel 3: Strategy Distribution
SELECT
    CASE WHEN calculate_agent_density(15) > 0.230
         THEN 'Stigmergic' ELSE 'Individual' END as strategy,
    COUNT(*) as queries
FROM memory_access_log
WHERE access_time > NOW() - INTERVAL '1 hour'
GROUP BY 1;
```

---

### Phase 5: Cleanup and Maintenance

#### 5.1 Add to Nightly Cron

Update `/ganuda/scripts/pheromone_decay.sh` on bluefin:

```bash
#!/bin/bash
# Pheromone Decay + Density Maintenance
# Runs nightly at 3:33 AM

PGPASSWORD='jawaseatlasers2' psql -h 127.0.0.1 -U claude -d zammad_production << EOF

-- Standard pheromone decay (existing)
UPDATE thermal_memory_archive
SET temperature_score = temperature_score * 0.95
WHERE temperature_score > 5;

-- Clean old access logs (keep 30 days)
DELETE FROM memory_access_log
WHERE access_time < NOW() - INTERVAL '30 days';

-- Log nightly density stats to thermal memory
INSERT INTO thermal_memory_archive (memory_hash, original_content, temperature_score, metadata)
SELECT
    'density-stats-' || TO_CHAR(NOW(), 'YYYYMMDD'),
    'DENSITY STATS ' || TO_CHAR(NOW(), 'YYYY-MM-DD') ||
    ': avg_density=' || ROUND(AVG(density_15min)::numeric, 3) ||
    ', strategy_switches=' || COUNT(DISTINCT
        CASE WHEN density_15min > 0.230 THEN 1 ELSE 0 END
    ),
    50.0,
    '{}'::jsonb
FROM density_metrics;

VACUUM ANALYZE memory_access_log;

EOF

echo "[$(date)] Pheromone decay + density maintenance complete"
```

---

## Testing

### Test 1: Verify Density Calculation

```bash
# On bluefin
PGPASSWORD='jawaseatlasers2' psql -h 127.0.0.1 -U claude -d zammad_production -c "
SELECT * FROM density_metrics;
"
```

### Test 2: Simulate Low Density Query

```bash
curl -X POST http://192.168.132.223:8080/v1/memory/adaptive \
  -H "Content-Type: application/json" \
  -d '{"query": "thermal memory", "agent_id": "test-jr"}'
```

### Test 3: Verify Strategy Switching

```bash
# Insert fake access logs to simulate high density
PGPASSWORD='jawaseatlasers2' psql -h 127.0.0.1 -U claude -d zammad_production -c "
INSERT INTO memory_access_log (memory_hash, agent_id, access_type)
SELECT 'test', 'agent-' || i, 'query'
FROM generate_series(1, 20) i;

SELECT * FROM density_metrics;
"
# Should show density > 0.230 and strategy = 'stigmergic'
```

---

## Success Criteria

1. ✅ memory_access_log table created and tracking accesses
2. ✅ calculate_agent_density() returns correct values
3. ✅ adaptive_memory_recall() switches strategies at ρ = 0.230
4. ✅ Gateway endpoint /v1/memory/adaptive works
5. ✅ Grafana dashboard shows density metrics
6. ✅ Nightly cron cleans old logs

---

## Architecture Diagram

```
                         ┌─────────────────┐
                         │   Jr Agents     │
                         │  (sasass, etc)  │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │  LLM Gateway    │
                         │  (redfin:8080)  │
                         └────────┬────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
              ▼                   ▼                   ▼
     ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
     │ memory_access   │ │ density_metrics │ │ thermal_memory  │
     │ _log            │ │ (view)          │ │ _archive        │
     └────────┬────────┘ └────────┬────────┘ └────────┬────────┘
              │                   │                   │
              └───────────────────┴───────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │ adaptive_memory_recall()│
                    │                         │
                    │  if ρ > 0.230:          │
                    │    → stigmergic (70%T)  │
                    │  else:                  │
                    │    → individual (70%R)  │
                    └─────────────────────────┘
```

---

## References

- arXiv:2512.10166 - Emergent Collective Memory in Decentralized Multi-Agent AI Systems
- Council Vote: f0d882b6d8ed0162 (79.5% confidence)
- Cherokee AI thermal_memory_archive: 6,700+ memories

---

*For Seven Generations - Cherokee AI Federation*

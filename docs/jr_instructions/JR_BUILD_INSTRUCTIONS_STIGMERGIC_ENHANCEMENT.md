# JR BUILD INSTRUCTIONS: Stigmergic Enhancement

**Target**: Cherokee AI Federation
**Date**: December 13, 2025
**Priority**: P2 - Enhancement
**Research Basis**: arXiv:2512.10166 "Emergent Collective Memory in Decentralized Multi-Agent AI Systems"
**Council Vote**: 3de4ffe4b0ca0425 (PROCEED, 100% confidence)

## Overview

This enhancement implements findings from arXiv:2512.10166 which validates our pheromone trail approach:

- **At density >= 0.20**: Stigmergic trails outperform memory by 36-41%
- **At density < 0.20**: Individual memory dominates (our current state with 6 nodes)
- **Hybrid approach**: Build both systems for long-term scalability

## Council Input Summary

| Specialist | Recommendation |
|------------|----------------|
| Crawdad | Security trails should decay slowest |
| Turtle | Hybrid approach serves Seven Generations |
| Gecko | Cache consensus counts to maintain O(1) |
| Raven | Optimize memory now, build stigmergy for future |
| Spider | Map trail categories to specialist types |
| Eagle Eye | Track decay rates and trail health in Grafana |

---

## PART 1: Category-Specific Decay Rates

### 1.1 Schema Update

**Deploy to**: bluefin (192.168.132.222)

```sql
-- /ganuda/sql/trail_categories.sql

-- Add trail_category to breadcrumb_trails
ALTER TABLE breadcrumb_trails
ADD COLUMN IF NOT EXISTS trail_category VARCHAR(20) DEFAULT 'general';

-- Add index for category-based queries
CREATE INDEX IF NOT EXISTS idx_breadcrumb_category
ON breadcrumb_trails(trail_category);

-- Update existing trails to 'general' category
UPDATE breadcrumb_trails
SET trail_category = 'general'
WHERE trail_category IS NULL;

-- Category decay rates reference table
CREATE TABLE IF NOT EXISTS trail_decay_rates (
    category VARCHAR(20) PRIMARY KEY,
    decay_rate NUMERIC(6,4) NOT NULL,  -- Per-day retention (0.998 = 0.2% decay)
    description TEXT,
    specialist_owner VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert decay rates from arXiv:2512.10166
INSERT INTO trail_decay_rates (category, decay_rate, description, specialist_owner) VALUES
    ('danger', 0.998, 'Security alerts - persist longest', 'crawdad'),
    ('technical', 0.985, 'Performance and technical issues', 'gecko'),
    ('wisdom', 0.970, 'Seven Generations patterns', 'turtle'),
    ('discovery', 0.970, 'Exploration and research', 'eagle_eye'),
    ('integration', 0.960, 'Cross-system connections', 'spider'),
    ('coordination', 0.950, 'Social coordination signals', 'peace_chief'),
    ('strategy', 0.980, 'Strategic planning trails', 'raven'),
    ('general', 0.950, 'Default category', NULL)
ON CONFLICT (category) DO UPDATE
SET decay_rate = EXCLUDED.decay_rate,
    description = EXCLUDED.description;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON trail_decay_rates TO claude;
```

### 1.2 Updated Decay Function

**Deploy to**: bluefin (192.168.132.222)

```sql
-- /ganuda/sql/decay_pheromones_v2.sql

-- Drop old function
DROP FUNCTION IF EXISTS decay_pheromones();

-- New category-aware decay function
CREATE OR REPLACE FUNCTION decay_pheromones_v2() RETURNS TABLE(
    category VARCHAR,
    trails_decayed INTEGER,
    avg_strength_after NUMERIC
) AS $$
DECLARE
    cat RECORD;
    v_decayed INTEGER;
    v_avg NUMERIC;
BEGIN
    -- Loop through each category with its specific decay rate
    FOR cat IN SELECT * FROM trail_decay_rates LOOP
        -- Apply category-specific decay
        UPDATE breadcrumb_trails bt
        SET pheromone_strength = pheromone_strength * cat.decay_rate,
            updated_at = NOW()
        WHERE bt.trail_category = cat.category
          AND bt.pheromone_strength > 1.0
          AND bt.last_reinforced < NOW() - INTERVAL '1 day';

        GET DIAGNOSTICS v_decayed = ROW_COUNT;

        -- Get average strength after decay
        SELECT COALESCE(AVG(pheromone_strength), 0) INTO v_avg
        FROM breadcrumb_trails
        WHERE trail_category = cat.category;

        -- Return row for this category
        category := cat.category;
        trails_decayed := v_decayed;
        avg_strength_after := v_avg;
        RETURN NEXT;
    END LOOP;

    -- Also decay pheromone_deposits with general rate
    UPDATE pheromone_deposits
    SET strength = strength * 0.97
    WHERE strength > 0.1
      AND last_decay < NOW() - INTERVAL '1 day';

    -- Cool thermal memories (unchanged from v1)
    UPDATE thermal_memory_archive
    SET temperature_score = temperature_score * 0.99
    WHERE created_at < NOW() - INTERVAL '30 days'
      AND temperature_score > 5.0
      AND sacred_pattern = false;
END;
$$ LANGUAGE plpgsql;

-- Convenience wrapper with old name for backwards compatibility
CREATE OR REPLACE FUNCTION decay_pheromones() RETURNS TABLE(
    trails_decayed INTEGER,
    deposits_cleaned INTEGER,
    thermal_cooled INTEGER
) AS $$
DECLARE
    v_trails INTEGER := 0;
    v_deposits INTEGER;
    v_thermal INTEGER;
    cat_result RECORD;
BEGIN
    -- Call new function and sum results
    FOR cat_result IN SELECT * FROM decay_pheromones_v2() LOOP
        v_trails := v_trails + cat_result.trails_decayed;
    END LOOP;

    -- Count cleaned deposits
    SELECT COUNT(*) INTO v_deposits FROM pheromone_deposits WHERE strength < 0.1;
    DELETE FROM pheromone_deposits WHERE strength < 0.1;

    -- Count cooled thermal memories
    SELECT COUNT(*) INTO v_thermal
    FROM thermal_memory_archive
    WHERE created_at < NOW() - INTERVAL '30 days'
      AND temperature_score > 5.0
      AND sacred_pattern = false;

    RETURN QUERY SELECT v_trails, v_deposits, v_thermal;
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION decay_pheromones_v2() TO claude;
GRANT EXECUTE ON FUNCTION decay_pheromones() TO claude;
```

### 1.3 Updated Decay Script

**Deploy to**: bluefin (192.168.132.222)

```bash
#!/bin/bash
# /ganuda/scripts/pheromone_decay_v2.sh
# Runs nightly at 3:33 AM via cron
# Implements category-specific decay from arXiv:2512.10166

DB_HOST="localhost"
DB_USER="claude"
DB_NAME="zammad_production"
export PGPASSWORD="jawaseatlasers2"

LOG_FILE="/var/log/ganuda/pheromone_decay.log"
mkdir -p /var/log/ganuda

echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting category-specific pheromone decay..." >> "$LOG_FILE"

# Run new decay function with category breakdown
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "
SELECT category, trails_decayed, ROUND(avg_strength_after::numeric, 2) as avg_strength
FROM decay_pheromones_v2()
ORDER BY trails_decayed DESC;
" >> "$LOG_FILE" 2>&1

# Log summary
TOTAL_TRAILS=$(psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM breadcrumb_trails WHERE pheromone_strength > 1;")
AVG_STRENGTH=$(psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT ROUND(AVG(pheromone_strength)::numeric, 2) FROM breadcrumb_trails;")
THERMAL_COUNT=$(psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM thermal_memory_archive;")
THERMAL_AVG=$(psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT ROUND(AVG(temperature_score)::numeric, 2) FROM thermal_memory_archive;")

echo "$(date '+%Y-%m-%d %H:%M:%S') - Decay complete." >> "$LOG_FILE"
echo "  Trails: $TOTAL_TRAILS (avg strength: $AVG_STRENGTH)" >> "$LOG_FILE"
echo "  Thermal: $THERMAL_COUNT memories (avg temp: $THERMAL_AVG)" >> "$LOG_FILE"
```

---

## PART 2: Consensus Amplification

### 2.1 Schema Update

**Deploy to**: bluefin (192.168.132.222)

```sql
-- /ganuda/sql/consensus_tracking.sql

-- Add consensus tracking to breadcrumb_trails
ALTER TABLE breadcrumb_trails
ADD COLUMN IF NOT EXISTS deposit_count INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS consensus_strength NUMERIC(5,2) DEFAULT 1.0;

-- Update reinforce_trail function with consensus amplification
CREATE OR REPLACE FUNCTION reinforce_trail_v2(
    p_trail_id INTEGER,
    p_depositor VARCHAR DEFAULT NULL,
    p_boost NUMERIC DEFAULT 5.0
) RETURNS TABLE(
    new_strength NUMERIC,
    new_consensus NUMERIC,
    deposit_count INTEGER
) AS $$
DECLARE
    v_strength NUMERIC;
    v_consensus NUMERIC;
    v_count INTEGER;
    v_alpha NUMERIC := 0.3;  -- Consensus amplification factor from paper
BEGIN
    -- Increment deposit count
    UPDATE breadcrumb_trails
    SET deposit_count = COALESCE(deposit_count, 1) + 1
    WHERE trail_id = p_trail_id
    RETURNING breadcrumb_trails.deposit_count INTO v_count;

    -- Calculate consensus strength: min(2.0, 1.0 + alpha*(N-1))
    v_consensus := LEAST(2.0, 1.0 + v_alpha * (v_count - 1));

    -- Apply boost with consensus multiplier
    UPDATE breadcrumb_trails
    SET pheromone_strength = LEAST(100.0, pheromone_strength + (p_boost * v_consensus)),
        consensus_strength = v_consensus,
        last_reinforced = NOW(),
        updated_at = NOW()
    WHERE trail_id = p_trail_id
    RETURNING pheromone_strength INTO v_strength;

    -- Log the deposit if depositor provided
    IF p_depositor IS NOT NULL THEN
        INSERT INTO pheromone_deposits (trail_id, deposited_by, strength)
        VALUES (p_trail_id, p_depositor, v_consensus)
        ON CONFLICT DO NOTHING;
    END IF;

    RETURN QUERY SELECT v_strength, v_consensus, v_count;
END;
$$ LANGUAGE plpgsql;

-- Backwards compatible wrapper
CREATE OR REPLACE FUNCTION reinforce_trail(p_trail_id INTEGER, p_boost NUMERIC DEFAULT 5.0)
RETURNS NUMERIC AS $$
DECLARE
    result RECORD;
BEGIN
    SELECT * INTO result FROM reinforce_trail_v2(p_trail_id, NULL, p_boost);
    RETURN result.new_strength;
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION reinforce_trail_v2(INTEGER, VARCHAR, NUMERIC) TO claude;
```

### 2.2 Python Helper

**Deploy to**: redfin (192.168.132.223)

```python
# Add to /ganuda/lib/specialist_council.py or create /ganuda/lib/trail_utils.py

def reinforce_with_consensus(trail_id: int, depositor: str, boost: float = 5.0) -> dict:
    """
    Reinforce a trail with consensus amplification.
    Implements arXiv:2512.10166 formula: min(2.0, 1.0 + 0.3*(N-1))

    Returns:
        dict with new_strength, consensus_strength, deposit_count
    """
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        SELECT new_strength, new_consensus, deposit_count
        FROM reinforce_trail_v2(%s, %s, %s)
    """, (trail_id, depositor, boost))

    row = cur.fetchone()
    conn.commit()
    conn.close()

    if row:
        return {
            "trail_id": trail_id,
            "new_strength": float(row[0]),
            "consensus_strength": float(row[1]),
            "deposit_count": row[2],
            "depositor": depositor
        }
    return None
```

---

## PART 3: Specialist-Trail Mapping

### 3.1 Updated Leave Trail Function

**Deploy to**: bluefin (192.168.132.222)

```sql
-- /ganuda/sql/specialist_trail_mapping.sql

-- Specialist to category mapping
CREATE TABLE IF NOT EXISTS specialist_trail_mapping (
    specialist VARCHAR(50) PRIMARY KEY,
    default_category VARCHAR(20) REFERENCES trail_decay_rates(category),
    description TEXT
);

INSERT INTO specialist_trail_mapping (specialist, default_category, description) VALUES
    ('crawdad', 'danger', 'Security specialist - danger category for alerts'),
    ('gecko', 'technical', 'Technical integration - technical issues'),
    ('turtle', 'wisdom', 'Seven Generations - wisdom patterns'),
    ('eagle_eye', 'discovery', 'Monitoring - discovery and patterns'),
    ('spider', 'integration', 'Cultural integration - cross-system'),
    ('peace_chief', 'coordination', 'Democratic coordination - social signals'),
    ('raven', 'strategy', 'Strategic planning - strategy trails'),
    ('tpm', 'strategy', 'TPM - strategic decisions'),
    ('system', 'technical', 'System-generated trails'),
    ('observer', 'general', 'Observer trails')
ON CONFLICT (specialist) DO UPDATE
SET default_category = EXCLUDED.default_category;

-- Function to leave categorized trail
CREATE OR REPLACE FUNCTION leave_categorized_trail(
    p_specialist VARCHAR,
    p_content TEXT,
    p_target VARCHAR DEFAULT NULL,
    p_category VARCHAR DEFAULT NULL  -- Override default category
) RETURNS TABLE(
    trail_id INTEGER,
    category VARCHAR,
    initial_strength NUMERIC
) AS $$
DECLARE
    v_trail_id INTEGER;
    v_category VARCHAR;
    v_session VARCHAR;
BEGIN
    -- Determine category from mapping or override
    IF p_category IS NOT NULL THEN
        v_category := p_category;
    ELSE
        SELECT default_category INTO v_category
        FROM specialist_trail_mapping
        WHERE specialist = p_specialist;

        IF v_category IS NULL THEN
            v_category := 'general';
        END IF;
    END IF;

    v_session := 'council-' || to_char(NOW(), 'YYYYMMDDHH24MISS');

    -- Create trail with category
    INSERT INTO breadcrumb_trails
    (session_id, trail_type, trail_name, trail_category, pheromone_strength, deposit_count, consensus_strength)
    VALUES (v_session, 'specialist_communication',
            p_specialist || '_to_' || COALESCE(p_target, 'all'),
            v_category, 85.0, 1, 1.0)
    RETURNING breadcrumb_trails.trail_id INTO v_trail_id;

    -- Leave pheromone deposit
    INSERT INTO pheromone_deposits (trail_id, deposited_by, memory_hash, strength)
    VALUES (v_trail_id, p_specialist, LEFT(p_content, 64), 1.0);

    RETURN QUERY SELECT v_trail_id, v_category, 85.0::NUMERIC;
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION leave_categorized_trail(VARCHAR, TEXT, VARCHAR, VARCHAR) TO claude;
GRANT SELECT ON specialist_trail_mapping TO claude;
```

### 3.2 Update Gateway Endpoint

**Modify**: `/ganuda/services/llm_gateway/gateway.py`

```python
# Update the leave_trail_endpoint to use categories

@app.post("/v1/trails/leave")
async def leave_trail_endpoint(
    specialist: str,
    content: str,
    target: str = None,
    category: str = None,  # NEW: optional category override
    api_key: APIKeyInfo = Depends(validate_api_key)
):
    """Leave a categorized breadcrumb trail"""
    valid_specialists = list(SPECIALISTS.keys()) + ["tpm", "system", "observer"]
    if specialist not in valid_specialists:
        raise HTTPException(status_code=400, detail=f"Invalid specialist")

    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT trail_id, category, initial_strength
                FROM leave_categorized_trail(%s, %s, %s, %s)
            """, (specialist, content[:500], target, category))

            row = cur.fetchone()
            conn.commit()

            return {
                "trail_id": row[0],
                "specialist": specialist,
                "category": row[1],
                "target": target,
                "status": "deposited",
                "initial_strength": float(row[2])
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## PART 4: Monitoring Dashboard

### 4.1 Prometheus Metrics

**Deploy to**: redfin (192.168.132.223)

```python
# /ganuda/services/trail_metrics_exporter.py
"""
Trail and Pheromone Metrics Exporter for Prometheus
Implements monitoring recommendations from Council (Eagle Eye)
"""

from prometheus_client import Gauge, Counter, start_http_server
import psycopg2
import time

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "user": "claude",
    "password": "jawaseatlasers2",
    "database": "zammad_production"
}

# Gauges
trail_count = Gauge('cherokee_trail_count', 'Number of trails', ['category'])
trail_avg_strength = Gauge('cherokee_trail_avg_strength', 'Average trail strength', ['category'])
trail_consensus_avg = Gauge('cherokee_trail_consensus_avg', 'Average consensus strength', ['category'])
thermal_count = Gauge('cherokee_thermal_count', 'Total thermal memories')
thermal_avg_temp = Gauge('cherokee_thermal_avg_temp', 'Average thermal temperature')
thermal_hot_count = Gauge('cherokee_thermal_hot', 'Memories with temp >= 90')

# Counters
trail_deposits = Counter('cherokee_trail_deposits', 'Trail deposits', ['specialist'])
trail_reinforcements = Counter('cherokee_trail_reinforcements', 'Trail reinforcements')

def collect_metrics():
    """Collect all trail and thermal metrics"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Trail metrics by category
    cur.execute("""
        SELECT trail_category,
               COUNT(*),
               AVG(pheromone_strength),
               AVG(consensus_strength)
        FROM breadcrumb_trails
        WHERE pheromone_strength > 0
        GROUP BY trail_category
    """)
    for row in cur.fetchall():
        cat = row[0] or 'unknown'
        trail_count.labels(category=cat).set(row[1])
        trail_avg_strength.labels(category=cat).set(float(row[2] or 0))
        trail_consensus_avg.labels(category=cat).set(float(row[3] or 1))

    # Thermal metrics
    cur.execute("""
        SELECT COUNT(*),
               AVG(temperature_score),
               COUNT(*) FILTER (WHERE temperature_score >= 90)
        FROM thermal_memory_archive
    """)
    row = cur.fetchone()
    thermal_count.set(row[0] or 0)
    thermal_avg_temp.set(float(row[1] or 0))
    thermal_hot_count.set(row[2] or 0)

    conn.close()

def run_exporter(port=9091):
    """Run metrics exporter on specified port"""
    start_http_server(port)
    print(f"Trail metrics exporter running on port {port}")

    while True:
        collect_metrics()
        time.sleep(60)

if __name__ == "__main__":
    run_exporter()
```

### 4.2 Grafana Dashboard

**Deploy to**: bluefin Grafana (192.168.132.222:3000)

```json
{
  "title": "Cherokee AI Stigmergic Health",
  "uid": "cherokee-stigmergy",
  "tags": ["cherokee", "trails", "pheromone"],
  "panels": [
    {
      "title": "Trail Count by Category",
      "type": "bargauge",
      "gridPos": {"h": 6, "w": 12, "x": 0, "y": 0},
      "targets": [{"expr": "cherokee_trail_count", "legendFormat": "{{category}}"}],
      "fieldConfig": {"defaults": {"color": {"mode": "palette-classic"}}}
    },
    {
      "title": "Avg Pheromone Strength by Category",
      "type": "gauge",
      "gridPos": {"h": 6, "w": 12, "x": 12, "y": 0},
      "targets": [{"expr": "cherokee_trail_avg_strength", "legendFormat": "{{category}}"}],
      "fieldConfig": {"defaults": {"min": 0, "max": 100, "thresholds": {"steps": [
        {"color": "red", "value": 0},
        {"color": "yellow", "value": 30},
        {"color": "green", "value": 60}
      ]}}}
    },
    {
      "title": "Thermal Memory vs Trail Comparison",
      "type": "stat",
      "gridPos": {"h": 4, "w": 8, "x": 0, "y": 6},
      "targets": [
        {"expr": "cherokee_thermal_count", "legendFormat": "Thermal Memories"},
        {"expr": "sum(cherokee_trail_count)", "legendFormat": "Total Trails"}
      ]
    },
    {
      "title": "Consensus Strength Distribution",
      "type": "timeseries",
      "gridPos": {"h": 6, "w": 16, "x": 8, "y": 6},
      "targets": [{"expr": "cherokee_trail_consensus_avg", "legendFormat": "{{category}}"}],
      "fieldConfig": {"defaults": {"unit": "none", "min": 1, "max": 2}}
    },
    {
      "title": "Decay Rate Effectiveness",
      "type": "table",
      "gridPos": {"h": 6, "w": 24, "x": 0, "y": 12},
      "targets": [{
        "rawSql": "SELECT category, decay_rate, description, specialist_owner FROM trail_decay_rates ORDER BY decay_rate DESC",
        "format": "table"
      }]
    }
  ]
}
```

### 4.3 SQL View for Dashboard

**Deploy to**: bluefin (192.168.132.222)

```sql
-- /ganuda/sql/trail_dashboard_views.sql

-- Summary view for Grafana
CREATE OR REPLACE VIEW trail_health_summary AS
SELECT
    bt.trail_category,
    tdr.decay_rate,
    tdr.specialist_owner,
    COUNT(*) as trail_count,
    ROUND(AVG(bt.pheromone_strength)::numeric, 2) as avg_strength,
    ROUND(AVG(bt.consensus_strength)::numeric, 2) as avg_consensus,
    SUM(bt.deposit_count) as total_deposits,
    MAX(bt.last_reinforced) as last_activity
FROM breadcrumb_trails bt
LEFT JOIN trail_decay_rates tdr ON bt.trail_category = tdr.category
WHERE bt.pheromone_strength > 0
GROUP BY bt.trail_category, tdr.decay_rate, tdr.specialist_owner;

-- Comparison view: memory vs trails
CREATE OR REPLACE VIEW memory_vs_trails AS
SELECT
    'thermal_memory' as system_type,
    COUNT(*) as entry_count,
    ROUND(AVG(temperature_score)::numeric, 2) as avg_strength,
    COUNT(*) FILTER (WHERE temperature_score >= 90) as hot_entries,
    MAX(last_access) as last_activity
FROM thermal_memory_archive
UNION ALL
SELECT
    'breadcrumb_trails' as system_type,
    COUNT(*) as entry_count,
    ROUND(AVG(pheromone_strength)::numeric, 2) as avg_strength,
    COUNT(*) FILTER (WHERE pheromone_strength >= 70) as hot_entries,
    MAX(last_reinforced) as last_activity
FROM breadcrumb_trails
WHERE pheromone_strength > 0;

GRANT SELECT ON trail_health_summary TO claude;
GRANT SELECT ON memory_vs_trails TO claude;
```

---

## Deployment Checklist

### On bluefin (192.168.132.222):

```bash
# 1. Deploy schema updates
PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production -f /ganuda/sql/trail_categories.sql
PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production -f /ganuda/sql/decay_pheromones_v2.sql
PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production -f /ganuda/sql/consensus_tracking.sql
PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production -f /ganuda/sql/specialist_trail_mapping.sql
PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production -f /ganuda/sql/trail_dashboard_views.sql

# 2. Update decay script
cp /ganuda/scripts/pheromone_decay.sh /ganuda/scripts/pheromone_decay.sh.bak
cp /ganuda/scripts/pheromone_decay_v2.sh /ganuda/scripts/pheromone_decay.sh
chmod +x /ganuda/scripts/pheromone_decay.sh

# 3. Test decay function
PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production -c "SELECT * FROM decay_pheromones_v2();"

# 4. Test categorized trail
PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production -c "SELECT * FROM leave_categorized_trail('crawdad', 'Test security alert', NULL, NULL);"
```

### On redfin (192.168.132.223):

```bash
# 1. Deploy metrics exporter
cp /ganuda/services/trail_metrics_exporter.py /ganuda/services/
chmod +x /ganuda/services/trail_metrics_exporter.py

# 2. Start metrics exporter (or add to systemd)
nohup /home/dereadi/cherokee_venv/bin/python /ganuda/services/trail_metrics_exporter.py &

# 3. Restart gateway to pick up endpoint changes
pkill -f 'uvicorn.*gateway'
cd /ganuda/services/llm_gateway && nohup /home/dereadi/cherokee_venv/bin/python -m uvicorn gateway:app --host 0.0.0.0 --port 8080 &
```

### Verification:

```bash
# Test categorized trail via API
curl -X POST "http://192.168.132.223:8080/v1/trails/leave?specialist=crawdad&content=Security+test&category=danger" \
  -H "Authorization: Bearer ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"

# Check trail health summary
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT * FROM trail_health_summary;"

# Check memory vs trails comparison
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT * FROM memory_vs_trails;"

# Check metrics endpoint
curl http://192.168.132.223:9091/metrics | grep cherokee
```

---

## Success Criteria

| Component | Metric | Target |
|-----------|--------|--------|
| Category Decay | Different rates per category | 8 categories configured |
| Consensus Amplification | Deposits increase strength | Formula: min(2.0, 1.0+0.3*(N-1)) |
| Specialist Mapping | Auto-categorization | 10 specialists mapped |
| Dashboard | All metrics visible | Grafana panel operational |
| Decay Script | Category breakdown in logs | All categories reported |

---

## Research Reference

**Paper**: arXiv:2512.10166 "Emergent Collective Memory in Decentralized Multi-Agent AI Systems"
**Author**: Khushiyant
**Date**: December 10, 2025

**Key Findings Applied**:
1. Category-specific decay rates (danger=0.998, social=0.95)
2. Consensus amplification formula: min(2.0, 1.0 + α(N-1)) where α=0.3
3. Memory weight Wmem=15 prioritized over task weight
4. At density >= 0.20, stigmergic coordination dominates

**Council Vote**: 3de4ffe4b0ca0425 (PROCEED, 100% confidence)

---

**FOR SEVEN GENERATIONS**

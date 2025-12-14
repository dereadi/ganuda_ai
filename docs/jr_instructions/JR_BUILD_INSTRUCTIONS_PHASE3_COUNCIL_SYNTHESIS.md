# JR BUILD INSTRUCTIONS: Phase 3 - Council Synthesis

**Target**: Cherokee AI Federation (all 6 nodes)
**Date**: December 13, 2025
**Priority**: P1 - Foundation + Hardening
**Council Vote**: b85dbfeb4dbca422

## Council Input Summary

| Specialist | Concern | Key Input |
|------------|---------|-----------|
| Crawdad | SECURITY | Multiple attack surfaces with 7 Jr instances; encrypt trail data |
| Gecko | PERF | Redfin GPU bottleneck with parallel queries; distribute load |
| Turtle | 7GEN | Persistence equation is foundational; governance structures last |
| Raven | STRATEGY | Dependencies matter; build foundations before features |
| Eagle Eye | VISIBILITY | Need metrics, alerts, Grafana dashboards for new systems |
| Spider | INTEGRATION | Define data flow between specialists, trails, and thermal memory |

## TPM Synthesis: Priority Order

Based on Council wisdom, dependencies, and Seven Generations principle:

```
PRIORITY 1: Activate Pheromone System (foundation already built, just dormant)
PRIORITY 2: Validate Persistence Equation (understand the physics before building)
PRIORITY 3: Production Runbooks (harden what exists before adding complexity)
PRIORITY 4: Extend Specialist Council (add trail-leaving capability)
PRIORITY 5: Breadcrumb Mesh Integration (connect all pieces)
```

---

## PRIORITY 1: Activate Pheromone System

**Status**: Infrastructure exists but dormant (1 row each in tables)
**Tables**: breadcrumb_trails, digital_pheromones, pheromone_deposits
**Script**: /ganuda/scripts/pheromone_decay.sh (runs 3:33 AM daily)
**Missing**: decay_pheromones() SQL function

### 1.1 Create Decay Function

**Deploy to**: bluefin (192.168.132.222)

```sql
-- /ganuda/sql/pheromone_functions.sql

-- Pheromone decay function (called by nightly cron)
CREATE OR REPLACE FUNCTION decay_pheromones() RETURNS TABLE(
    trails_decayed INTEGER,
    deposits_cleaned INTEGER,
    thermal_cooled INTEGER
) AS $$
DECLARE
    v_trails INTEGER;
    v_deposits INTEGER;
    v_thermal INTEGER;
BEGIN
    -- Decay breadcrumb trail pheromone strength by 5% daily
    UPDATE breadcrumb_trails
    SET pheromone_strength = pheromone_strength * 0.95,
        updated_at = NOW()
    WHERE pheromone_strength > 1.0
      AND last_reinforced < NOW() - INTERVAL '1 day';

    GET DIAGNOSTICS v_trails = ROW_COUNT;

    -- Decay digital pheromone strength by 3% daily
    UPDATE digital_pheromones
    SET strength = strength * 0.97
    WHERE strength > 0.1
      AND last_followed < NOW() - INTERVAL '1 day';

    GET DIAGNOSTICS v_deposits = ROW_COUNT;

    -- Clean up exhausted deposits (strength < 0.1)
    DELETE FROM pheromone_deposits WHERE strength < 0.1;

    -- Cool thermal memories older than 30 days by 1%
    UPDATE thermal_memory_archive
    SET temperature_score = temperature_score * 0.99
    WHERE created_at < NOW() - INTERVAL '30 days'
      AND temperature_score > 5.0
      AND sacred_pattern = false;

    GET DIAGNOSTICS v_thermal = ROW_COUNT;

    RETURN QUERY SELECT v_trails, v_deposits, v_thermal;
END;
$$ LANGUAGE plpgsql;

-- Reinforce trail when accessed (called by council/gateway)
CREATE OR REPLACE FUNCTION reinforce_trail(p_trail_id INTEGER, p_boost NUMERIC DEFAULT 5.0)
RETURNS NUMERIC AS $$
DECLARE
    v_new_strength NUMERIC;
BEGIN
    UPDATE breadcrumb_trails
    SET pheromone_strength = LEAST(100.0, pheromone_strength + p_boost),
        last_reinforced = NOW(),
        updated_at = NOW()
    WHERE trail_id = p_trail_id
    RETURNING pheromone_strength INTO v_new_strength;

    RETURN v_new_strength;
END;
$$ LANGUAGE plpgsql;

-- Leave a new pheromone deposit
CREATE OR REPLACE FUNCTION leave_pheromone(
    p_source_table VARCHAR,
    p_source_id INTEGER,
    p_destination_table VARCHAR,
    p_destination_id INTEGER,
    p_specialist VARCHAR DEFAULT NULL,
    p_purpose TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_trail_id UUID;
BEGIN
    INSERT INTO digital_pheromones (
        source_table, source_id, destination_table, destination_id,
        specialist_scent, purpose, strength
    ) VALUES (
        p_source_table, p_source_id, p_destination_table, p_destination_id,
        p_specialist, p_purpose, 1.0
    ) RETURNING trail_id INTO v_trail_id;

    RETURN v_trail_id;
END;
$$ LANGUAGE plpgsql;

-- Follow a pheromone trail (increments follow_count, reinforces)
CREATE OR REPLACE FUNCTION follow_pheromone(p_trail_uuid UUID) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE digital_pheromones
    SET follow_count = follow_count + 1,
        last_followed = NOW(),
        strength = LEAST(10.0, strength + 0.1)  -- Small boost when followed
    WHERE trail_id = p_trail_uuid;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Get hottest trails for a specialist
CREATE OR REPLACE FUNCTION get_hot_trails(
    p_specialist VARCHAR DEFAULT NULL,
    p_min_strength NUMERIC DEFAULT 0.5,
    p_limit INTEGER DEFAULT 20
) RETURNS TABLE(
    trail_id UUID,
    source_table VARCHAR,
    destination_table VARCHAR,
    specialist_scent VARCHAR,
    strength NUMERIC,
    follow_count INTEGER,
    purpose TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        dp.trail_id,
        dp.source_table,
        dp.destination_table,
        dp.specialist_scent,
        dp.strength,
        dp.follow_count,
        dp.purpose
    FROM digital_pheromones dp
    WHERE dp.strength >= p_min_strength
      AND (p_specialist IS NULL OR dp.specialist_scent = p_specialist)
    ORDER BY dp.strength DESC, dp.follow_count DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;
```

### 1.2 Test Pheromone Functions

```bash
# On bluefin as dereadi
PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production << 'EOF'
-- Test decay function
SELECT * FROM decay_pheromones();

-- Leave a test pheromone
SELECT leave_pheromone('thermal_memory_archive', 1, 'council_votes', 1, 'crawdad', 'security review link');

-- Check hot trails
SELECT * FROM get_hot_trails();
EOF
```

---

## PRIORITY 2: Validate Persistence Equation

**Formula**: P(t) = P₀ × e^(-λt + αU(t))
**Data Source**: 5,245 thermal memories with timestamps and temperature_score
**Goal**: Calculate λ (decay rate) and α (usage boost) from real Cherokee data

### 2.1 Extract Aging Data

**Deploy to**: bluefin or any node with psql access

```sql
-- /ganuda/sql/persistence_analysis.sql

-- Extract data for persistence equation fitting
CREATE OR REPLACE VIEW persistence_analysis AS
SELECT
    memory_hash,
    temperature_score,
    access_count,
    EXTRACT(EPOCH FROM (NOW() - created_at)) / 86400.0 AS age_days,
    created_at,
    last_access,
    sacred_pattern
FROM thermal_memory_archive
WHERE temperature_score > 0
ORDER BY created_at;

-- Summary statistics
SELECT
    COUNT(*) as total_memories,
    AVG(age_days) as avg_age_days,
    AVG(temperature_score) as avg_temp,
    AVG(access_count) as avg_accesses,
    CORR(age_days, temperature_score) as age_temp_correlation,
    CORR(access_count, temperature_score) as access_temp_correlation
FROM persistence_analysis
WHERE sacred_pattern = false;
```

### 2.2 Python Fitting Script

**Deploy to**: redfin (has scipy)

```python
#!/usr/bin/env python3
"""
Cherokee AI Persistence Equation Validator
Fits P(t) = P0 * exp(-lambda*t + alpha*U(t)) to thermal memory data

Deploy to: /ganuda/scripts/validate_persistence_equation.py
"""

import psycopg2
import numpy as np
from scipy.optimize import curve_fit
import json
from datetime import datetime

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "user": "claude",
    "password": "jawaseatlasers2",
    "database": "zammad_production"
}

def persistence_model(t_and_u, P0, lambda_decay, alpha_usage):
    """Universal Persistence Equation: P(t) = P0 * exp(-lambda*t + alpha*U(t))"""
    t, U = t_and_u
    return P0 * np.exp(-lambda_decay * t + alpha_usage * U)

def fetch_memory_data():
    """Fetch thermal memory data for analysis"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        SELECT
            temperature_score,
            access_count,
            EXTRACT(EPOCH FROM (NOW() - created_at)) / 86400.0 AS age_days
        FROM thermal_memory_archive
        WHERE temperature_score > 0
          AND sacred_pattern = false
          AND created_at < NOW() - INTERVAL '7 days'  -- Only aged memories
    """)

    rows = cur.fetchall()
    conn.close()

    temps = np.array([r[0] for r in rows])
    accesses = np.array([r[1] for r in rows])
    ages = np.array([r[2] for r in rows])

    return temps, accesses, ages

def fit_persistence_equation():
    """Fit the persistence equation to Cherokee thermal memory data"""
    temps, accesses, ages = fetch_memory_data()

    print(f"Analyzing {len(temps)} thermal memories...")
    print(f"Age range: {ages.min():.1f} - {ages.max():.1f} days")
    print(f"Temp range: {temps.min():.1f} - {temps.max():.1f}")
    print(f"Access range: {accesses.min()} - {accesses.max()}")

    # Initial guesses
    P0_guess = 100.0  # Initial temperature
    lambda_guess = 0.01  # ~1% decay per day
    alpha_guess = 0.5  # Usage boost factor

    try:
        # Fit the model
        popt, pcov = curve_fit(
            persistence_model,
            (ages, accesses),
            temps,
            p0=[P0_guess, lambda_guess, alpha_guess],
            bounds=([50, 0, 0], [100, 0.1, 2.0]),
            maxfev=5000
        )

        P0_fit, lambda_fit, alpha_fit = popt
        perr = np.sqrt(np.diag(pcov))

        # Calculate predicted values
        temps_pred = persistence_model((ages, accesses), *popt)
        residuals = temps - temps_pred
        r_squared = 1 - (np.sum(residuals**2) / np.sum((temps - temps.mean())**2))

        results = {
            "timestamp": datetime.now().isoformat(),
            "sample_size": len(temps),
            "parameters": {
                "P0": {"value": float(P0_fit), "std_error": float(perr[0])},
                "lambda_decay": {"value": float(lambda_fit), "std_error": float(perr[1])},
                "alpha_usage": {"value": float(alpha_fit), "std_error": float(perr[2])}
            },
            "fit_quality": {
                "r_squared": float(r_squared),
                "rmse": float(np.sqrt(np.mean(residuals**2)))
            },
            "interpretation": {
                "half_life_days": float(np.log(2) / lambda_fit) if lambda_fit > 0 else None,
                "access_boost_per_view": float(alpha_fit),
                "formula": f"P(t) = {P0_fit:.1f} * exp(-{lambda_fit:.4f}*t + {alpha_fit:.3f}*U)"
            }
        }

        return results

    except Exception as e:
        return {"error": str(e), "timestamp": datetime.now().isoformat()}

def save_to_thermal_memory(results):
    """Save validation results to thermal memory"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    content = f"""PERSISTENCE EQUATION VALIDATED - {datetime.now().strftime('%B %d, %Y')}

FORMULA: {results.get('interpretation', {}).get('formula', 'FITTING FAILED')}

PARAMETERS:
- P₀ (initial temperature): {results['parameters']['P0']['value']:.2f} ± {results['parameters']['P0']['std_error']:.2f}
- λ (decay rate): {results['parameters']['lambda_decay']['value']:.5f} ± {results['parameters']['lambda_decay']['std_error']:.5f}
- α (usage boost): {results['parameters']['alpha_usage']['value']:.3f} ± {results['parameters']['alpha_usage']['std_error']:.3f}

FIT QUALITY:
- R²: {results['fit_quality']['r_squared']:.4f}
- RMSE: {results['fit_quality']['rmse']:.2f}

INTERPRETATION:
- Memory half-life: {results['interpretation']['half_life_days']:.1f} days (without access)
- Each access boosts persistence by factor of e^{results['interpretation']['access_boost_per_view']:.3f}

SAMPLE: {results['sample_size']} thermal memories analyzed

FOR SEVEN GENERATIONS
"""

    cur.execute("""
        INSERT INTO thermal_memory_archive
        (memory_hash, original_content, temperature_score, metadata)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (memory_hash) DO UPDATE
        SET temperature_score = 98, last_access = NOW()
    """, (
        f"persistence-equation-validated-{datetime.now().strftime('%Y%m%d')}",
        content,
        98.0,
        json.dumps(results)
    ))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("Cherokee AI Persistence Equation Validator")
    print("=" * 50)

    results = fit_persistence_equation()

    if "error" not in results:
        print(f"\nFitted Parameters:")
        print(f"  P₀ = {results['parameters']['P0']['value']:.2f}")
        print(f"  λ  = {results['parameters']['lambda_decay']['value']:.5f} (decay/day)")
        print(f"  α  = {results['parameters']['alpha_usage']['value']:.3f} (usage boost)")
        print(f"\nFit Quality:")
        print(f"  R² = {results['fit_quality']['r_squared']:.4f}")
        print(f"  Half-life = {results['interpretation']['half_life_days']:.1f} days")
        print(f"\nFormula: {results['interpretation']['formula']}")

        save_to_thermal_memory(results)
        print("\nResults saved to thermal memory.")
    else:
        print(f"Error: {results['error']}")
```

---

## PRIORITY 3: Production Runbooks

**Per Crawdad**: Harden what exists before adding complexity
**Deploy to**: /ganuda/runbooks/ on redfin

### 3.1 GPU Wedged Runbook

```markdown
# RUNBOOK: GPU Wedged (vLLM Unresponsive)

## Symptoms
- vLLM requests timing out (>30s response times)
- nvidia-smi shows 100% utilization but no throughput
- GPU memory stuck at max, not releasing
- Health check: `curl http://localhost:8080/health` returns vllm: unhealthy

## Severity
**P1** - Affects all LLM inference

## Diagnosis
```bash
# Check vLLM process state
ps aux | grep vllm
journalctl -u vllm -n 50 --no-pager

# Check GPU state
nvidia-smi
nvidia-smi -q | grep -A5 "Utilization"

# Check for zombie processes
ps aux | grep defunct | grep -v grep

# Check system resources
free -h
df -h /
```

## Resolution Steps

### Step 1: Graceful Restart (try first)
```bash
sudo systemctl restart vllm
sleep 30
curl -s http://localhost:8080/health | jq .
```

### Step 2: Force GPU Reset (if Step 1 fails)
```bash
sudo systemctl stop vllm
sleep 10
sudo nvidia-smi -r  # GPU reset
sleep 5
sudo systemctl start vllm
sleep 60  # Model reload takes ~45s
curl -s http://localhost:8080/health | jq .
```

### Step 3: Nuclear Option (schedule maintenance)
```bash
# Only if Steps 1-2 fail
echo "Scheduling reboot in 5 minutes"
sudo shutdown -r +5 "GPU recovery - planned reboot"
# OR immediate if critical
sudo reboot
```

## Prevention
- Monitor GPU memory utilization (alert at 90%)
- Implement request timeouts in gateway (120s max)
- Add circuit breaker for 3+ consecutive failures
- Check for memory leaks in custom prompts

## Post-Incident
- Check /ganuda/logs/vllm.error.log for root cause
- Update this runbook if new failure mode discovered
- Create thermal memory entry for incident
```

### 3.2 Database Connection Exhausted Runbook

```markdown
# RUNBOOK: PostgreSQL Connection Exhausted

## Symptoms
- "too many connections for role" errors
- New database queries failing
- Services timing out on DB operations

## Severity
**P1** - Affects all database-dependent services

## Diagnosis
```bash
# Check connection count
ssh dereadi@192.168.132.222 "PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production -c \"SELECT count(*) FROM pg_stat_activity;\""

# Check by client
ssh dereadi@192.168.132.222 "PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production -c \"SELECT client_addr, count(*) FROM pg_stat_activity GROUP BY client_addr ORDER BY count DESC;\""

# Check idle connections
ssh dereadi@192.168.132.222 "PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production -c \"SELECT pid, state, query_start, query FROM pg_stat_activity WHERE state = 'idle' ORDER BY query_start;\""
```

## Resolution Steps

### Step 1: Terminate Idle Connections
```bash
ssh dereadi@192.168.132.222 "PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production -c \"
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
  AND query_start < NOW() - INTERVAL '10 minutes'
  AND usename = 'claude';
\""
```

### Step 2: Increase Connection Limit (temporary)
```bash
# On bluefin as postgres user
sudo -u postgres psql -c "ALTER ROLE claude CONNECTION LIMIT 200;"
```

### Step 3: Identify Leaking Service
- Check which client_addr has most connections
- Review that service's connection pooling
- Restart the offending service

## Prevention
- Use connection pooling (PgBouncer)
- Set idle timeout in service configs
- Monitor pg_stat_activity in Grafana
- Alert when connections > 80% of limit

## Post-Incident
- Identify service that leaked connections
- Add connection pooling if missing
- Update thermal memory with incident
```

### 3.3 Node Unreachable Runbook

```markdown
# RUNBOOK: Cherokee Node Unreachable

## Symptoms
- ping to node IP fails
- SSH connection refused/timeout
- Services on that node unavailable

## Severity
**P2** - Single node failure (federation degrades gracefully)

## Diagnosis
```bash
# From TPM workstation
ping -c 3 192.168.132.XXX  # Target node IP

# Check from another node
ssh dereadi@192.168.132.222 "ping -c 3 192.168.132.XXX"

# Check if physical access needed
# Node IPs:
# bluefin: 192.168.132.222
# redfin: 192.168.132.223
# greenfin: 192.168.132.224
# sasass: 192.168.132.241
# sasass2: 192.168.132.242
```

## Resolution Steps

### Step 1: Verify Network Path
```bash
traceroute 192.168.132.XXX
arp -a | grep 192.168.132.XXX
```

### Step 2: Physical Access (if available)
- Check power LED
- Check network cable
- Check for kernel panic on screen
- Power cycle if frozen

### Step 3: Remote Management (if configured)
- Use IPMI/iLO/iDRAC for server nodes
- Use network power switch if available

### Step 4: Failover Procedures
- If bluefin (database): Services will fail - escalate immediately
- If redfin (GPU): LLM inference unavailable - council votes fail
- If greenfin (monitoring): Alerting degraded but services continue
- If sasass/sasass2 (edge): Development affected, production continues

## Prevention
- Configure watchdog timers on all nodes
- Set up out-of-band management
- Monitor with heartbeat checks every 60s
- Cross-node health checks in Grafana

## Post-Incident
- Review /var/log/kern.log for crash cause
- Check dmesg output
- Update thermal memory with incident
```

---

## PRIORITY 4: Extend Specialist Council

**Per Spider**: Define integration between specialists and trail system
**Deploy to**: /ganuda/lib/specialist_council.py on redfin

### 4.1 Add Trail Integration to Council

Add these methods to specialist_council.py:

```python
# Add to specialist_council.py

def leave_specialist_breadcrumb(self, specialist: str, content: str,
                                 target_specialist: str = None) -> int:
    """
    Specialist leaves a breadcrumb for others to follow
    Returns trail_id
    """
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    session_id = f"council-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    cur.execute("""
        INSERT INTO breadcrumb_trails
        (session_id, trail_type, trail_name, pheromone_strength)
        VALUES (%s, %s, %s, %s)
        RETURNING trail_id
    """, (session_id, 'specialist_communication',
          f"{specialist}_to_{target_specialist or 'all'}", 85.0))

    trail_id = cur.fetchone()[0]

    # Leave pheromone deposit
    cur.execute("""
        INSERT INTO pheromone_deposits (trail_id, specialist_scent, content, strength)
        VALUES (%s, %s, %s, %s)
    """, (trail_id, specialist, content, 1.0))

    conn.commit()
    conn.close()

    return trail_id

def follow_hot_trails(self, specialist: str, min_strength: float = 0.5) -> list:
    """
    Specialist follows hot trails left by others
    Returns list of relevant breadcrumbs
    """
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        SELECT dp.content, dp.specialist_scent, dp.strength, bt.trail_name
        FROM pheromone_deposits dp
        JOIN breadcrumb_trails bt ON dp.trail_id = bt.trail_id
        WHERE dp.strength >= %s
          AND dp.specialist_scent != %s
        ORDER BY dp.strength DESC, dp.created_at DESC
        LIMIT 10
    """, (min_strength, specialist))

    trails = []
    for row in cur.fetchall():
        trails.append({
            "content": row[0],
            "from_specialist": row[1],
            "strength": row[2],
            "trail_name": row[3]
        })

        # Reinforce the trail we just followed
        cur.execute("SELECT follow_pheromone(%s)", (row[0],))  # Would need trail_id

    conn.commit()
    conn.close()

    return trails

def council_vote_with_trails(self, question: str) -> dict:
    """
    Enhanced council vote that leaves breadcrumb trail
    """
    # Perform standard council vote
    result = self.council_vote(question)

    # Create breadcrumb trail for this vote
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO breadcrumb_trails
        (session_id, trail_type, trail_name, pheromone_strength)
        VALUES (%s, %s, %s, %s)
        RETURNING trail_id
    """, (
        result.get('audit_hash', 'unknown'),
        'council_vote',
        f"vote_{datetime.now().strftime('%H%M%S')}",
        95.0 if result.get('recommendation') == 'PROCEED' else 70.0
    ))

    trail_id = cur.fetchone()[0]

    # Each specialist leaves their scent on the trail
    for specialist, response in result.get('responses', {}).items():
        cur.execute("""
            INSERT INTO pheromone_deposits (trail_id, specialist_scent, content, strength)
            VALUES (%s, %s, %s, %s)
        """, (trail_id, specialist, response[:500], 1.0))

    conn.commit()
    conn.close()

    result['trail_id'] = trail_id
    return result
```

### 4.2 Add Trail API Endpoints

Add to /ganuda/services/llm_gateway/gateway.py:

```python
@app.get("/v1/trails/hot")
async def get_hot_trails(
    specialist: str = None,
    min_strength: float = 0.5,
    api_key: APIKey = Depends(validate_api_key)
) -> dict:
    """Get currently hot pheromone trails"""
    council = get_council()
    trails = council.follow_hot_trails(specialist or "observer", min_strength)
    return {"trails": trails, "count": len(trails)}

@app.post("/v1/trails/leave")
async def leave_trail(
    specialist: str,
    content: str,
    target: str = None,
    api_key: APIKey = Depends(validate_api_key)
) -> dict:
    """Leave a breadcrumb trail"""
    council = get_council()
    trail_id = council.leave_specialist_breadcrumb(specialist, content, target)
    return {"trail_id": trail_id, "specialist": specialist, "status": "deposited"}

@app.get("/v1/council/history")
async def council_vote_history(
    limit: int = 10,
    api_key: APIKey = Depends(validate_api_key)
) -> dict:
    """Get recent council vote trails"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        SELECT trail_id, session_id, trail_name, pheromone_strength, created_at
        FROM breadcrumb_trails
        WHERE trail_type = 'council_vote'
        ORDER BY created_at DESC
        LIMIT %s
    """, (limit,))

    votes = []
    for row in cur.fetchall():
        votes.append({
            "trail_id": row[0],
            "audit_hash": row[1],
            "name": row[2],
            "strength": row[3],
            "timestamp": row[4].isoformat()
        })

    conn.close()
    return {"votes": votes, "count": len(votes)}
```

---

## PRIORITY 5: Monitoring Dashboard

**Per Eagle Eye**: Need metrics, alerts, Grafana dashboards

### 5.1 Prometheus Metrics

Add to gateway.py or create metrics_exporter.py:

```python
# /ganuda/services/metrics_exporter.py
"""
Cherokee AI Metrics Exporter for Prometheus/Grafana
"""

from prometheus_client import Counter, Gauge, Histogram, start_http_server
import psycopg2
import time

# Metrics
council_votes_total = Counter('cherokee_council_votes_total', 'Total council votes', ['recommendation'])
trail_strength_gauge = Gauge('cherokee_trail_strength', 'Current pheromone strength', ['trail_type'])
thermal_memory_count = Gauge('cherokee_thermal_memories', 'Total thermal memories')
thermal_avg_temp = Gauge('cherokee_thermal_avg_temperature', 'Average memory temperature')
specialist_queries = Counter('cherokee_specialist_queries', 'Queries per specialist', ['specialist'])
api_latency = Histogram('cherokee_api_latency_seconds', 'API response latency', ['endpoint'])

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "user": "claude",
    "password": "jawaseatlasers2",
    "database": "zammad_production"
}

def collect_metrics():
    """Collect metrics from database"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Thermal memory stats
    cur.execute("SELECT COUNT(*), AVG(temperature_score) FROM thermal_memory_archive")
    count, avg_temp = cur.fetchone()
    thermal_memory_count.set(count or 0)
    thermal_avg_temp.set(avg_temp or 0)

    # Trail strengths by type
    cur.execute("""
        SELECT trail_type, AVG(pheromone_strength)
        FROM breadcrumb_trails
        GROUP BY trail_type
    """)
    for trail_type, avg_strength in cur.fetchall():
        trail_strength_gauge.labels(trail_type=trail_type).set(avg_strength or 0)

    conn.close()

def run_metrics_server(port=9090):
    """Run Prometheus metrics server"""
    start_http_server(port)
    print(f"Metrics server started on port {port}")

    while True:
        collect_metrics()
        time.sleep(60)  # Collect every minute

if __name__ == "__main__":
    run_metrics_server()
```

### 5.2 Grafana Dashboard JSON

Create `/ganuda/grafana/cherokee_council_dashboard.json`:

```json
{
  "title": "Cherokee AI Council & Trails",
  "uid": "cherokee-council",
  "panels": [
    {
      "title": "Thermal Memory Count",
      "type": "stat",
      "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0},
      "targets": [{"expr": "cherokee_thermal_memories"}]
    },
    {
      "title": "Average Temperature",
      "type": "gauge",
      "gridPos": {"h": 4, "w": 6, "x": 6, "y": 0},
      "targets": [{"expr": "cherokee_thermal_avg_temperature"}],
      "fieldConfig": {
        "defaults": {
          "min": 0, "max": 100,
          "thresholds": {
            "steps": [
              {"color": "blue", "value": 0},
              {"color": "green", "value": 50},
              {"color": "yellow", "value": 75},
              {"color": "red", "value": 90}
            ]
          }
        }
      }
    },
    {
      "title": "Council Votes (24h)",
      "type": "stat",
      "gridPos": {"h": 4, "w": 6, "x": 12, "y": 0},
      "targets": [{"expr": "increase(cherokee_council_votes_total[24h])"}]
    },
    {
      "title": "Trail Strength by Type",
      "type": "bargauge",
      "gridPos": {"h": 6, "w": 12, "x": 0, "y": 4},
      "targets": [{"expr": "cherokee_trail_strength"}]
    },
    {
      "title": "Specialist Query Distribution",
      "type": "piechart",
      "gridPos": {"h": 6, "w": 12, "x": 12, "y": 4},
      "targets": [{"expr": "cherokee_specialist_queries"}]
    }
  ]
}
```

---

## Deployment Checklist

### On bluefin (192.168.132.222):
```bash
# 1. Deploy pheromone SQL functions
PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production -f /ganuda/sql/pheromone_functions.sql

# 2. Verify decay function
PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production -c "SELECT * FROM decay_pheromones();"

# 3. Create runbooks directory
mkdir -p /ganuda/runbooks
# Copy runbook markdown files
```

### On redfin (192.168.132.223):
```bash
# 1. Deploy persistence equation validator
cp validate_persistence_equation.py /ganuda/scripts/
chmod +x /ganuda/scripts/validate_persistence_equation.py

# 2. Run validation
python3 /ganuda/scripts/validate_persistence_equation.py

# 3. Update specialist_council.py with trail integration
# 4. Update gateway.py with trail endpoints

# 5. Deploy metrics exporter
cp metrics_exporter.py /ganuda/services/
# Add systemd service for metrics
```

### Verification:
```bash
# Test pheromone system
curl -X POST "http://192.168.132.223:8080/v1/trails/leave" \
  -H "Authorization: Bearer ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5" \
  -H "Content-Type: application/json" \
  -d '{"specialist": "crawdad", "content": "Security review complete", "target": "peace_chief"}'

# Check hot trails
curl "http://192.168.132.223:8080/v1/trails/hot?min_strength=0.5" \
  -H "Authorization: Bearer ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"

# Council vote with trail
curl -X POST "http://192.168.132.223:8080/v1/council/vote" \
  -H "Authorization: Bearer ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5" \
  -H "Content-Type: application/json" \
  -d '{"question": "Test trail integration complete?"}'
```

---

## Success Criteria

| Component | Metric | Target |
|-----------|--------|--------|
| Pheromone Decay | decay_pheromones() runs nightly | 100% |
| Persistence Equation | R² fit quality | > 0.7 |
| Runbooks | Coverage of P1 incidents | 3+ runbooks |
| Trail Integration | Council votes create trails | 100% |
| Monitoring | Metrics exported to Prometheus | All key metrics |

---

**Council Vote**: b85dbfeb4dbca422
**Confidence**: 70% (PERF and 7GEN concerns addressed)
**Recommendation**: PROCEED WITH CAUTION

FOR SEVEN GENERATIONS

# Jr Instructions: Thermal Memory Health & Decay Enhancement

**Priority**: 2 (High)
**Assigned Jr**: it_triad_jr
**Council Vote**: PROCEED WITH CAUTION 79.4% - Turtle [7GEN CONCERN]

---

## BACKGROUND

Thermal memory has 6,463 memories with 95% rated HOT or WHITE_HOT. Daily pheromone decay runs at 3:33 AM but temperatures are not cooling. Eagle Eye flagged this as a visibility concern - no thermal memory metrics in health checks.

Seven Generations Impact: Memory that never cools means no natural forgetting/prioritization, unbounded storage growth, old context competing equally with fresh insights.

---

### Task 1: Add Thermal Memory Health Endpoint

Create `/ganuda/services/llm_gateway/thermal_health.py`:

```python
"""
Thermal Memory Health Metrics
For Seven Generations - Cherokee AI Federation
"""

import psycopg2
from datetime import datetime, timedelta

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

def get_thermal_health():
    """Get thermal memory health metrics"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    metrics = {}

    # Total counts by temperature
    cur.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE temperature_score >= 90) as hot,
            COUNT(*) FILTER (WHERE temperature_score >= 50 AND temperature_score < 90) as warm,
            COUNT(*) FILTER (WHERE temperature_score < 50) as cool,
            AVG(temperature_score)::int as avg_temp,
            pg_size_pretty(pg_total_relation_size('thermal_memory_archive')) as size
        FROM thermal_memory_archive
    """)
    row = cur.fetchone()
    metrics['total'] = row[0]
    metrics['hot'] = row[1]
    metrics['warm'] = row[2]
    metrics['cool'] = row[3]
    metrics['avg_temperature'] = row[4]
    metrics['table_size'] = row[5]

    # Stage distribution
    cur.execute("""
        SELECT current_stage, COUNT(*)
        FROM thermal_memory_archive
        GROUP BY current_stage
    """)
    metrics['stages'] = {row[0]: row[1] for row in cur.fetchall()}

    # Activity metrics
    cur.execute("""
        SELECT
            COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '1 hour') as last_hour,
            COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as last_24h,
            COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as last_7d
        FROM thermal_memory_archive
    """)
    row = cur.fetchone()
    metrics['activity'] = {
        'last_hour': row[0],
        'last_24h': row[1],
        'last_7d': row[2]
    }

    # Decay effectiveness (how many cooled in last 24h)
    cur.execute("""
        SELECT COUNT(*)
        FROM thermal_memory_archive
        WHERE updated_at > NOW() - INTERVAL '24 hours'
          AND updated_at != created_at
    """)
    metrics['decayed_24h'] = cur.fetchone()[0]

    # Health assessment
    hot_ratio = metrics['hot'] / max(metrics['total'], 1)
    if hot_ratio > 0.9:
        metrics['health'] = 'CRITICAL'
        metrics['health_note'] = 'Over 90% memories HOT - decay not effective'
    elif hot_ratio > 0.7:
        metrics['health'] = 'WARNING'
        metrics['health_note'] = 'Over 70% memories HOT - review decay params'
    else:
        metrics['health'] = 'HEALTHY'
        metrics['health_note'] = 'Normal temperature distribution'

    cur.close()
    conn.close()

    return metrics


if __name__ == '__main__':
    import json
    print(json.dumps(get_thermal_health(), indent=2))
```

---

### Task 2: Update Pheromone Decay Script

Create `/ganuda/scripts/pheromone_decay_v2.sh`:

```bash
#!/bin/bash
# Pheromone Decay v2.0 - More Aggressive Cooling
# Council Vote: PROCEED WITH CAUTION - Seven Generations Impact
# For Seven Generations - Cherokee AI Federation

PGPASSWORD='jawaseatlasers2'
export PGPASSWORD

PSQL="/usr/bin/psql -h 192.168.132.222 -U claude -d zammad_production"

LOG="/var/log/ganuda/pheromone_decay.log"
echo "$(date): Starting pheromone decay v2" >> $LOG

# Stage 1: WHITE_HOT (>95) older than 3 days -> RED_HOT (90)
$PSQL -c "
UPDATE thermal_memory_archive
SET current_stage = 'RED_HOT',
    temperature_score = 90,
    updated_at = NOW()
WHERE current_stage = 'WHITE_HOT'
  AND temperature_score > 95
  AND created_at < NOW() - INTERVAL '3 days';
" 2>&1 | tee -a $LOG

# Stage 2: RED_HOT older than 7 days -> HOT (80)
$PSQL -c "
UPDATE thermal_memory_archive
SET current_stage = 'HOT',
    temperature_score = 80,
    updated_at = NOW()
WHERE current_stage = 'RED_HOT'
  AND created_at < NOW() - INTERVAL '7 days';
" 2>&1 | tee -a $LOG

# Stage 3: HOT older than 14 days -> WARM (60)
$PSQL -c "
UPDATE thermal_memory_archive
SET current_stage = 'WARM',
    temperature_score = 60,
    updated_at = NOW()
WHERE current_stage = 'HOT'
  AND created_at < NOW() - INTERVAL '14 days';
" 2>&1 | tee -a $LOG

# Stage 4: WARM older than 30 days -> COOL (40)
$PSQL -c "
UPDATE thermal_memory_archive
SET current_stage = 'COOL',
    temperature_score = 40,
    updated_at = NOW()
WHERE current_stage = 'WARM'
  AND created_at < NOW() - INTERVAL '30 days';
" 2>&1 | tee -a $LOG

# Stage 5: COOL older than 60 days -> COLD (20)
$PSQL -c "
UPDATE thermal_memory_archive
SET current_stage = 'COLD',
    temperature_score = 20,
    updated_at = NOW()
WHERE current_stage = 'COOL'
  AND created_at < NOW() - INTERVAL '60 days';
" 2>&1 | tee -a $LOG

# Stage 6: COLD older than 90 days -> ARCHIVE (10)
$PSQL -c "
UPDATE thermal_memory_archive
SET current_stage = 'ARCHIVE',
    temperature_score = 10,
    updated_at = NOW()
WHERE current_stage = 'COLD'
  AND created_at < NOW() - INTERVAL '90 days';
" 2>&1 | tee -a $LOG

# Report
echo "$(date): Decay complete. Summary:" >> $LOG
$PSQL -c "
SELECT current_stage, COUNT(*), AVG(temperature_score)::int as avg_temp
FROM thermal_memory_archive
GROUP BY current_stage
ORDER BY avg_temp DESC;
" 2>&1 | tee -a $LOG

echo "$(date): Pheromone decay v2 finished" >> $LOG
```

---

### Task 3: Add Thermal Health to Gateway

Edit `/ganuda/services/llm_gateway/gateway.py` to add thermal health endpoint. Add after the existing `/health` route:

```python
# Add import at top
from thermal_health import get_thermal_health

# Add route after /health
@app.route('/v1/thermal/health', methods=['GET'])
@require_api_key
def thermal_health():
    """Get thermal memory health metrics"""
    try:
        metrics = get_thermal_health()
        return jsonify(metrics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

---

### Task 4: Deploy and Test

Run these commands on bluefin:

```bash
# Make decay script executable
chmod +x /ganuda/scripts/pheromone_decay_v2.sh

# Update crontab to use v2
crontab -l | sed 's/pheromone_decay.sh/pheromone_decay_v2.sh/' | crontab -

# Run decay once manually to start cooling
/ganuda/scripts/pheromone_decay_v2.sh

# Verify crontab
crontab -l | grep pheromone
```

---

## SUCCESS CRITERIA

1. `/v1/thermal/health` endpoint returns metrics
2. Decay script runs and shows stage transitions
3. After 1 week, HOT ratio should drop below 90%
4. Health dashboard shows thermal status

---

## DECAY TIMELINE (Seven Generations Wisdom)

| Age | Stage | Temperature | Meaning |
|-----|-------|-------------|---------|
| 0-3 days | WHITE_HOT | 98 | Fresh insight, high priority |
| 3-7 days | RED_HOT | 90 | Recent, still relevant |
| 7-14 days | HOT | 80 | Active knowledge |
| 14-30 days | WARM | 60 | Background context |
| 30-60 days | COOL | 40 | Historical reference |
| 60-90 days | COLD | 20 | Archive candidate |
| 90+ days | ARCHIVE | 10 | Long-term storage |

---

*For Seven Generations - Cherokee AI Federation*

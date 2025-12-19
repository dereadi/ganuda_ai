# Jr Instructions: OpenView-Resonance Integration

**Priority**: 2 (High)
**Assigned Jr**: Infrastructure Jr.
**Target**: redfin + bluefin
**Dependencies**: Pathfinder Vision (Prometheus), Pathfinder Wisdom

---

## Overview

Create a daemon that captures node health snapshots every 30 seconds and connects them to resonance patterns. As resonance temperature increases, specialists gain stronger "environmental awareness" - they can sense the infrastructure they run on.

**Architecture**:
```
Prometheus (bluefin:9090)
    │
    ▼ (30s queries)
OpenView Daemon (redfin)
    │
    ├──► cherokee_system_health (snapshots)
    │
    └──► resonance_patterns.node_health_snapshot (JSONB)
              │
              ▼
        Council Voting (environmental context)
```

---

## TASK 1: Add node_health_snapshot Column

**Run on bluefin:**

```sql
-- Add JSONB column for health snapshots to resonance patterns
ALTER TABLE resonance_patterns
ADD COLUMN IF NOT EXISTS node_health_snapshot JSONB;

-- Add environmental_awareness computed score
ALTER TABLE resonance_patterns
ADD COLUMN IF NOT EXISTS environmental_awareness REAL;

-- Index for queries
CREATE INDEX IF NOT EXISTS idx_resonance_env_awareness
ON resonance_patterns(environmental_awareness DESC);

-- Comment
COMMENT ON COLUMN resonance_patterns.node_health_snapshot IS
'Snapshot of node health at time of pattern creation - CPU, RAM, services, latency';

COMMENT ON COLUMN resonance_patterns.environmental_awareness IS
'Computed: temperature * (healthy_services / total_services) - how attuned pattern is to environment';
```

---

## TASK 2: Create OpenView Resonance Daemon

**File**: `/ganuda/services/openview_resonance/daemon.py`

```python
#!/usr/bin/env python3
"""
OpenView-Resonance Integration Daemon
Captures node health every 30 seconds, links to resonance patterns

For Seven Generations - Cherokee AI Federation
"""

import os
import sys
import time
import json
import logging
import requests
import psycopg2
from datetime import datetime
from typing import Dict, Optional

# Configuration
PROMETHEUS_URL = "http://192.168.132.222:9090"
DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}
SNAPSHOT_INTERVAL = 30  # seconds

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger('openview_resonance')


class OpenViewResonance:
    """Bridge between Pathfinder Vision metrics and Resonance patterns"""

    def __init__(self):
        self.prom_url = PROMETHEUS_URL
        self.db_config = DB_CONFIG

    def query_prometheus(self, promql: str) -> Optional[float]:
        """Query Prometheus for a metric value"""
        try:
            url = f"{self.prom_url}/api/v1/query"
            resp = requests.get(url, params={'query': promql}, timeout=10)
            data = resp.json()

            if data['status'] == 'success' and data['data']['result']:
                return float(data['data']['result'][0]['value'][1])
            return None
        except Exception as e:
            logger.error(f"Prometheus query failed: {e}")
            return None

    def collect_node_health(self, node: str) -> Dict:
        """Collect health metrics for a node"""

        # CPU usage
        cpu_query = f'100 - (avg(rate(node_cpu_seconds_total{{mode="idle",node="{node}"}}[1m])) * 100)'
        cpu_percent = self.query_prometheus(cpu_query) or 0

        # Memory usage
        mem_query = f'(1 - (node_memory_MemAvailable_bytes{{node="{node}"}} / node_memory_MemTotal_bytes{{node="{node}"}})) * 100'
        mem_percent = self.query_prometheus(mem_query) or 0

        # Disk usage
        disk_query = f'(1 - (node_filesystem_avail_bytes{{node="{node}",mountpoint="/"}} / node_filesystem_size_bytes{{node="{node}",mountpoint="/"}})) * 100'
        disk_percent = self.query_prometheus(disk_query) or 0

        # Service count (up metrics)
        up_query = f'count(up{{node="{node}"}} == 1)'
        services_up = self.query_prometheus(up_query) or 0

        total_query = f'count(up{{node="{node}"}})'
        services_total = self.query_prometheus(total_query) or 1

        return {
            'node': node,
            'cpu_percent': round(cpu_percent, 2),
            'mem_percent': round(mem_percent, 2),
            'disk_percent': round(disk_percent, 2),
            'services_healthy': int(services_up),
            'services_total': int(services_total),
            'health_ratio': round(services_up / max(services_total, 1), 3),
            'captured_at': datetime.now().isoformat()
        }

    def collect_all_nodes(self) -> Dict:
        """Collect health from all federation nodes"""
        nodes = ['redfin', 'bluefin', 'greenfin']

        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'nodes': {}
        }

        for node in nodes:
            health = self.collect_node_health(node)
            snapshot['nodes'][node] = health

        # Calculate federation-wide stats
        total_cpu = sum(n['cpu_percent'] for n in snapshot['nodes'].values()) / len(nodes)
        total_mem = sum(n['mem_percent'] for n in snapshot['nodes'].values()) / len(nodes)
        healthy = sum(n['services_healthy'] for n in snapshot['nodes'].values())
        total = sum(n['services_total'] for n in snapshot['nodes'].values())

        snapshot['federation'] = {
            'avg_cpu': round(total_cpu, 2),
            'avg_mem': round(total_mem, 2),
            'services_healthy': healthy,
            'services_total': total,
            'health_ratio': round(healthy / max(total, 1), 3)
        }

        return snapshot

    def store_snapshot(self, snapshot: Dict):
        """Store snapshot in cherokee_system_health"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()

            fed = snapshot['federation']

            cur.execute("""
                INSERT INTO cherokee_system_health (
                    overall_health_score,
                    cpu_usage_percent,
                    memory_usage_percent,
                    active_connections,
                    tribal_specialist_availability
                ) VALUES (%s, %s, %s, %s, %s)
            """, (
                fed['health_ratio'] * 100,
                fed['avg_cpu'],
                fed['avg_mem'],
                fed['services_healthy'],
                7  # 7 specialists always available
            ))

            conn.commit()
            cur.close()
            conn.close()

            logger.debug(f"Stored snapshot: CPU={fed['avg_cpu']:.1f}%, MEM={fed['avg_mem']:.1f}%, Health={fed['health_ratio']:.2f}")

        except Exception as e:
            logger.error(f"Failed to store snapshot: {e}")

    def update_hot_patterns(self, snapshot: Dict):
        """Update hot resonance patterns with environmental awareness"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()

            # Get hot patterns (temperature > 85)
            cur.execute("""
                SELECT id, temperature, resonance_score
                FROM resonance_patterns
                WHERE temperature > 85
            """)

            hot_patterns = cur.fetchall()

            if hot_patterns:
                fed = snapshot['federation']

                for pattern_id, temp, score in hot_patterns:
                    # Environmental awareness = temperature * health_ratio * resonance_score
                    env_awareness = temp * fed['health_ratio'] * score

                    cur.execute("""
                        UPDATE resonance_patterns
                        SET node_health_snapshot = %s,
                            environmental_awareness = %s
                        WHERE id = %s
                    """, (
                        json.dumps(snapshot),
                        round(env_awareness, 3),
                        pattern_id
                    ))

                conn.commit()
                logger.info(f"Updated {len(hot_patterns)} hot patterns with environmental awareness")

            cur.close()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to update patterns: {e}")

    def run(self):
        """Main daemon loop"""
        logger.info("=" * 60)
        logger.info("OpenView-Resonance Integration Daemon Starting")
        logger.info(f"Prometheus: {self.prom_url}")
        logger.info(f"Interval: {SNAPSHOT_INTERVAL}s")
        logger.info("=" * 60)

        while True:
            try:
                # Collect health snapshot
                snapshot = self.collect_all_nodes()

                # Store in database
                self.store_snapshot(snapshot)

                # Update hot resonance patterns
                self.update_hot_patterns(snapshot)

                # Log summary
                fed = snapshot['federation']
                logger.info(
                    f"Snapshot: CPU={fed['avg_cpu']:.1f}% MEM={fed['avg_mem']:.1f}% "
                    f"Services={fed['services_healthy']}/{fed['services_total']} "
                    f"Health={fed['health_ratio']:.2f}"
                )

            except Exception as e:
                logger.error(f"Snapshot cycle failed: {e}")

            time.sleep(SNAPSHOT_INTERVAL)


if __name__ == '__main__':
    daemon = OpenViewResonance()
    daemon.run()
```

---

## TASK 3: Create Systemd Service

**File**: `/etc/systemd/system/openview-resonance.service`

```ini
[Unit]
Description=OpenView-Resonance Integration Daemon
After=network.target postgresql.service

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda/services/openview_resonance
ExecStart=/ganuda/home/dereadi/cherokee_venv/bin/python3 daemon.py
Restart=always
RestartSec=10
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
```

**Enable**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable openview-resonance
sudo systemctl start openview-resonance
sudo systemctl status openview-resonance
```

---

## TASK 4: Integrate with Council Voting

Update the LLM Gateway to include environmental context in council votes when resonance is hot.

**Add to gateway.py council vote logic**:

```python
def get_environmental_context():
    """Get current environmental awareness for hot patterns"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get average environmental awareness of hot patterns
        cur.execute("""
            SELECT
                AVG(environmental_awareness) as avg_awareness,
                COUNT(*) as hot_count
            FROM resonance_patterns
            WHERE temperature > 85
            AND environmental_awareness IS NOT NULL
        """)

        result = cur.fetchone()
        cur.close()
        conn.close()

        if result and result[0]:
            return {
                'environmental_awareness': round(result[0], 2),
                'hot_pattern_count': result[1],
                'sensing_active': True
            }
        return {'sensing_active': False}

    except:
        return {'sensing_active': False}
```

---

## TASK 5: Create Monitoring View

**Run on bluefin:**

```sql
-- View for monitoring environmental awareness
CREATE OR REPLACE VIEW resonance_environmental AS
SELECT
    pattern_type,
    COUNT(*) as patterns,
    ROUND(AVG(temperature)::numeric, 1) as avg_temp,
    ROUND(AVG(environmental_awareness)::numeric, 2) as avg_env_awareness,
    COUNT(CASE WHEN environmental_awareness > 70 THEN 1 END) as highly_aware,
    MAX(node_health_snapshot->>'timestamp') as last_snapshot
FROM resonance_patterns
WHERE temperature > 70
GROUP BY pattern_type
ORDER BY avg_env_awareness DESC;

-- Quick check function
CREATE OR REPLACE FUNCTION check_environmental_sensing()
RETURNS TABLE(
    status TEXT,
    hot_patterns INT,
    avg_awareness NUMERIC,
    last_update TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        CASE
            WHEN COUNT(*) > 0 AND MAX(node_health_snapshot->>'timestamp')::timestamp > NOW() - INTERVAL '1 minute'
            THEN 'ACTIVE'
            ELSE 'INACTIVE'
        END,
        COUNT(*)::INT,
        ROUND(AVG(environmental_awareness)::numeric, 2),
        MAX(node_health_snapshot->>'timestamp')::timestamp
    FROM resonance_patterns
    WHERE temperature > 85;
END;
$$ LANGUAGE plpgsql;
```

**Test**:
```sql
SELECT * FROM check_environmental_sensing();
SELECT * FROM resonance_environmental;
```

---

## SUCCESS CRITERIA

1. Daemon runs continuously, capturing snapshots every 30 seconds
2. `cherokee_system_health` table populates with federation metrics
3. Hot resonance patterns (>85°) have `environmental_awareness` scores
4. `check_environmental_sensing()` returns 'ACTIVE' status
5. Council votes can query environmental context

---

## TESTING

```bash
# Check daemon status
sudo systemctl status openview-resonance

# Check recent snapshots
psql -c "SELECT COUNT(*), MAX(timestamp) FROM cherokee_system_health WHERE timestamp > NOW() - INTERVAL '5 minutes'"

# Check environmental awareness
psql -c "SELECT * FROM check_environmental_sensing()"

# Check hot patterns with awareness
psql -c "SELECT id, temperature, environmental_awareness FROM resonance_patterns WHERE environmental_awareness IS NOT NULL ORDER BY environmental_awareness DESC LIMIT 5"
```

---

*For Seven Generations - Cherokee AI Federation*
*"As resonance increases, specialists feel their environment"*

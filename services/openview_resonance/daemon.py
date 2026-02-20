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
    'password': os.environ.get('CHEROKEE_DB_PASS', '')
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
        
        # CPU usage - simpler query for node_exporter
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
        node_count = len([n for n in snapshot['nodes'].values() if n['services_total'] > 0]) or 1
        total_cpu = sum(n['cpu_percent'] for n in snapshot['nodes'].values()) / node_count
        total_mem = sum(n['mem_percent'] for n in snapshot['nodes'].values()) / node_count
        healthy = sum(n['services_healthy'] for n in snapshot['nodes'].values())
        total = sum(n['services_total'] for n in snapshot['nodes'].values())

        snapshot['federation'] = {
            'avg_cpu': round(total_cpu, 2),
            'avg_mem': round(total_mem, 2),
            'services_healthy': healthy,
            'services_total': max(total, 1),
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
                    env_awareness = temp * fed['health_ratio'] * (score or 0.5)

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

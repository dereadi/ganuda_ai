#!/usr/bin/env python3
"""
Spatial Discovery Daemon
Scans network for device presence and updates online_status/last_seen
Council approved - requires nmap installed on host

Run from redfin: python3 /ganuda/services/spatial_discovery/discovery.py
"""

import subprocess
import json
import time
import psycopg2
from datetime import datetime
import re
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': os.environ.get('CHEROKEE_DB_PASS', '')
}

NETWORK_RANGE = '192.168.132.0/24'
SCAN_INTERVAL = 300  # 5 minutes

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def scan_network():
    """Run nmap ping scan to find online hosts"""
    try:
        result = subprocess.run(
            ['nmap', '-sn', NETWORK_RANGE, '-oG', '-'],
            capture_output=True, text=True, timeout=60
        )

        online_ips = []
        for line in result.stdout.split('\n'):
            if 'Up' in line:
                match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if match:
                    online_ips.append(match.group(1))

        return online_ips
    except Exception as e:
        logger.error(f"Network scan failed: {e}")
        return []

def update_device_status(online_ips):
    """Update device online status in database"""
    conn = get_db_connection()
    cur = conn.cursor()
    now = datetime.now()

    try:
        # Update hardware inventory
        cur.execute("""
            UPDATE hardware_inventory
            SET online_status = (ip_address = ANY(%s)),
                last_seen = CASE WHEN ip_address = ANY(%s) THEN %s ELSE last_seen END
        """, (online_ips, online_ips, now))

        # Update IoT devices
        cur.execute("""
            UPDATE iot_devices
            SET online_status = (ip_address = ANY(%s)),
                last_seen = CASE WHEN ip_address = ANY(%s) THEN %s ELSE last_seen END
            WHERE ip_address IS NOT NULL
        """, (online_ips, online_ips, now))

        conn.commit()

        # Get counts for logging
        cur.execute("SELECT COUNT(*) FROM hardware_inventory WHERE online_status = true")
        hw_online = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM iot_devices WHERE online_status = true")
        iot_online = cur.fetchone()[0]

        logger.info(f"Discovery complete: {len(online_ips)} IPs found, {hw_online} nodes online, {iot_online} IoT online")

    except Exception as e:
        logger.error(f"Database update failed: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def run_daemon():
    """Main daemon loop"""
    logger.info("Spatial Discovery Daemon starting...")
    logger.info(f"Scanning {NETWORK_RANGE} every {SCAN_INTERVAL} seconds")

    while True:
        try:
            online_ips = scan_network()
            if online_ips:
                update_device_status(online_ips)
        except Exception as e:
            logger.error(f"Daemon error: {e}")

        time.sleep(SCAN_INTERVAL)

if __name__ == '__main__':
    run_daemon()
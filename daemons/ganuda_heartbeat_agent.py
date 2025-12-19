#!/usr/bin/env python3
"""Ganuda View Heartbeat Agent - Linux version for redfin"""

import psutil
import socket
import time
import psycopg2
from datetime import datetime

DB_CONFIG = {
    "host": "192.168.132.222",
    "database": "triad_federation",
    "user": "claude",
    "password": "jawaseatlasers2"
}

AGENT_VERSION = "1.0"

def get_node_id(conn, hostname):
    """Get node_id for this hostname from ganuda_view_nodes"""
    cursor = conn.cursor()
    cursor.execute("SELECT node_id FROM ganuda_view_nodes WHERE hostname = %s", (hostname,))
    row = cursor.fetchone()
    cursor.close()
    return row[0] if row else None

def get_hostname():
    """Get hostname"""
    return socket.gethostname()

def send_heartbeat():
    """Collect metrics and send to bluefin database"""
    hostname = get_hostname()

    # Collect metrics via psutil
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    load = list(psutil.getloadavg())
    net = psutil.net_io_counters()
    uptime = int(time.time() - psutil.boot_time())
    procs = len(psutil.pids())

    conn = psycopg2.connect(**DB_CONFIG)
    node_id = get_node_id(conn, hostname)

    if node_id:
        cursor = conn.cursor()

        # Insert heartbeat
        cursor.execute("""
            INSERT INTO ganuda_view_heartbeats
            (node_id, cpu_percent, memory_percent, disk_percent, load_avg,
             network_bytes_sent, network_bytes_recv, process_count, uptime_seconds, agent_version)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (node_id, cpu, mem, disk, load, net.bytes_sent, net.bytes_recv, procs, uptime, AGENT_VERSION))

        # Update node status
        cursor.execute("""
            UPDATE ganuda_view_nodes
            SET status = 'online', last_heartbeat = NOW()
            WHERE node_id = %s
        """, (node_id,))

        conn.commit()
        cursor.close()
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Heartbeat sent from {hostname}: CPU={cpu}%, MEM={mem}%, DISK={disk}%")
    else:
        print(f"WARNING: No node_id found for hostname '{hostname}' - check ganuda_view_nodes table")

    conn.close()

if __name__ == '__main__':
    hostname = get_hostname()
    print(f"Starting Ganuda View Heartbeat Agent v{AGENT_VERSION} on {hostname}")
    print(f"Target: {DB_CONFIG['host']}{DB_CONFIG['database']}")
    print(f"Heartbeat interval: 60 seconds")
    print("-" * 60)

    while True:
        try:
            send_heartbeat()
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error: {e}")
        time.sleep(60)

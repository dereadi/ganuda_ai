#!/usr/bin/env python3
"""
Health Monitor - Periodic health checks with Telegram alerts.
Cherokee AI Federation - For Seven Generations
"""

import os
import sys
import time
import logging
import requests
import psycopg2

sys.path.insert(0, '/ganuda/lib')
from alert_manager import alert_service_down, alert_high_latency, alert_medium

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [HealthMonitor] %(message)s'
)

# Services to monitor: (name, url, latency_threshold_ms)
SERVICES = [
    ('vLLM', 'http://localhost:8000/health', 5000),
    ('Gateway', 'http://localhost:8080/health', 2000),
    ('ii-researcher', 'http://localhost:8090/health', 3000),
]

DB_CONFIG = {
    'host': os.environ.get('CHEROKEE_DB_HOST', '192.168.132.222'),
    'database': 'zammad_production',
    'user': 'claude',
    'password': os.environ.get('CHEROKEE_DB_PASS', '')
}

CHECK_INTERVAL = 60  # seconds
QUEUE_DEPTH_THRESHOLD = 10


def check_service(name: str, url: str, latency_threshold_ms: int) -> bool:
    """Check if a service is healthy."""
    try:
        start = time.time()
        response = requests.get(url, timeout=10)
        latency_ms = int((time.time() - start) * 1000)

        if response.status_code != 200:
            alert_service_down(name, f"HTTP {response.status_code}")
            return False

        if latency_ms > latency_threshold_ms:
            alert_high_latency(name, latency_ms, latency_threshold_ms)

        logging.debug(f"{name}: OK ({latency_ms}ms)")
        return True

    except requests.exceptions.Timeout:
        alert_service_down(name, "Request timeout")
        return False
    except requests.exceptions.ConnectionError:
        alert_service_down(name, "Connection refused")
        return False
    except Exception as e:
        alert_service_down(name, str(e))
        return False


def check_database() -> bool:
    """Check database connectivity and latency."""
    try:
        start = time.time()
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        conn.close()
        latency_ms = int((time.time() - start) * 1000)

        if latency_ms > 1000:
            alert_high_latency('PostgreSQL', latency_ms, 1000)

        logging.debug(f"PostgreSQL: OK ({latency_ms}ms)")
        return True

    except Exception as e:
        alert_service_down('PostgreSQL', str(e))
        return False


def check_research_queue_depth() -> bool:
    """Check for research job queue backup."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM research_jobs WHERE status = 'pending'")
        pending = cur.fetchone()[0]
        cur.close()
        conn.close()

        if pending > QUEUE_DEPTH_THRESHOLD:
            alert_medium(
                "Research Queue Backup",
                f"{pending} research jobs pending (threshold: {QUEUE_DEPTH_THRESHOLD})",
                source='eagle-eye',
                context={'pending_jobs': pending, 'threshold': QUEUE_DEPTH_THRESHOLD}
            )
            return False

        logging.debug(f"Research queue: {pending} pending")
        return True

    except Exception as e:
        logging.error(f"Queue check failed: {e}")
        return True  # Don't alert on check failure itself


def check_jr_queue_depth() -> bool:
    """Check for Jr work queue backup."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM jr_work_queue WHERE status = 'pending'")
        pending = cur.fetchone()[0]
        cur.close()
        conn.close()

        if pending > 20:
            alert_medium(
                "Jr Work Queue Backup",
                f"{pending} Jr tasks pending",
                source='eagle-eye',
                context={'pending_tasks': pending}
            )
            return False

        logging.debug(f"Jr queue: {pending} pending")
        return True

    except Exception as e:
        logging.error(f"Jr queue check failed: {e}")
        return True


def run_health_checks():
    """Run all health checks."""
    results = []

    # Check services
    for name, url, threshold in SERVICES:
        results.append(check_service(name, url, threshold))

    # Check database
    results.append(check_database())

    # Check queue depths
    results.append(check_research_queue_depth())
    results.append(check_jr_queue_depth())

    healthy = sum(results)
    total = len(results)
    logging.info(f"Health check: {healthy}/{total} healthy")

    return all(results)


def main():
    logging.info("=" * 50)
    logging.info("Health Monitor - Cherokee AI Federation")
    logging.info("=" * 50)
    logging.info(f"Check interval: {CHECK_INTERVAL}s")
    logging.info(f"Monitoring: {', '.join(s[0] for s in SERVICES)}")
    logging.info("=" * 50)

    while True:
        try:
            run_health_checks()
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            logging.info("Shutting down...")
            break
        except Exception as e:
            logging.error(f"Health monitor error: {e}")
            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""SLA Baseline Metrics — Cherokee AI Federation

Measures current performance baselines for SLA definition.
Task #1206 / #1257. Run from redfin.

Usage:
    python3 /ganuda/scripts/sla_baseline_metrics.py
    python3 /ganuda/scripts/sla_baseline_metrics.py --write-report
"""

import os
import sys
import time
import statistics
from datetime import datetime, timedelta

import psycopg2
import psycopg2.extras
import requests


def load_secrets():
    secrets = {}
    secrets_path = '/ganuda/config/secrets.env'
    if os.path.exists(secrets_path):
        with open(secrets_path) as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    secrets[k.strip()] = v.strip()
    return secrets


secrets = load_secrets()

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "dbname": "zammad_production",
    "user": "claude",
    "password": secrets.get("CHEROKEE_DB_PASS", ""),
}

GATEWAY_URL = "http://192.168.132.223:8080"
REPORT_PATH = "/ganuda/docs/business/SLA-BASELINE-METRICS-MAR12-2026.md"


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def measure_council_vote_time(cur):
    """Measure council vote cadence — interval between successive votes (last 30 days)."""
    cur.execute("""
        SELECT
            EXTRACT(EPOCH FROM (voted_at - LAG(voted_at) OVER (ORDER BY voted_at))) as interval_seconds
        FROM council_votes
        WHERE voted_at > NOW() - INTERVAL '30 days'
          AND voted_at IS NOT NULL
        ORDER BY voted_at DESC
        LIMIT 100
    """)
    rows = cur.fetchall()
    if not rows:
        return {"count": 0, "avg_seconds": None, "p50_seconds": None, "p95_seconds": None}
    times = [r[0] for r in rows if r[0] is not None and r[0] > 0]
    if not times:
        return {"count": 0, "avg_seconds": None, "p50_seconds": None, "p95_seconds": None}
    times.sort()
    p50_idx = int(len(times) * 0.50)
    p95_idx = min(int(len(times) * 0.95), len(times) - 1)
    return {
        "count": len(times),
        "avg_seconds": statistics.mean(times),
        "p50_seconds": times[p50_idx],
        "p95_seconds": times[p95_idx],
    }


def measure_jr_task_completion(cur):
    """Measure Jr task lifecycle time (pending -> completed) over last 30 days."""
    cur.execute("""
        SELECT
            EXTRACT(EPOCH FROM (updated_at - created_at)) as completion_seconds,
            status
        FROM jr_work_queue
        WHERE created_at > NOW() - INTERVAL '30 days'
          AND status IN ('completed', 'failed')
          AND updated_at IS NOT NULL
        ORDER BY created_at DESC
        LIMIT 200
    """)
    rows = cur.fetchall()
    completed = [r[0] for r in rows if r[1] == 'completed' and r[0] is not None and r[0] > 0]
    failed = [r for r in rows if r[1] == 'failed']
    if not completed:
        return {"completed_count": 0, "failed_count": len(failed),
                "avg_seconds": None, "p50_seconds": None, "p95_seconds": None}
    completed.sort()
    p50_idx = int(len(completed) * 0.50)
    p95_idx = min(int(len(completed) * 0.95), len(completed) - 1)
    return {
        "completed_count": len(completed),
        "failed_count": len(failed),
        "avg_seconds": statistics.mean(completed),
        "p50_seconds": completed[p50_idx],
        "p95_seconds": completed[p95_idx],
    }


def measure_thermal_write_latency(cur):
    """Measure thermal memory write frequency (proxy for write latency)."""
    cur.execute("""
        SELECT
            COUNT(*) as total_writes,
            MIN(created_at) as earliest,
            MAX(created_at) as latest
        FROM thermal_memory_archive
        WHERE created_at > NOW() - INTERVAL '24 hours'
    """)
    row = cur.fetchone()
    total = row[0] if row else 0
    if total > 1 and row[1] and row[2]:
        span_seconds = (row[2] - row[1]).total_seconds()
        avg_interval = span_seconds / (total - 1) if total > 1 else None
    else:
        avg_interval = None
    return {
        "writes_24h": total,
        "avg_interval_seconds": avg_interval,
    }


def measure_gateway_response(url=GATEWAY_URL):
    """Measure gateway /health response time (5 samples)."""
    times_ms = []
    errors = 0
    for _ in range(5):
        try:
            start = time.monotonic()
            resp = requests.get(f"{url}/health", timeout=10)
            elapsed_ms = (time.monotonic() - start) * 1000
            if resp.status_code == 200:
                times_ms.append(elapsed_ms)
            else:
                errors += 1
        except Exception:
            errors += 1
        time.sleep(0.5)
    if not times_ms:
        return {"samples": 0, "errors": errors, "avg_ms": None, "p50_ms": None, "p95_ms": None}
    times_ms.sort()
    p50_idx = int(len(times_ms) * 0.50)
    p95_idx = min(int(len(times_ms) * 0.95), len(times_ms) - 1)
    return {
        "samples": len(times_ms),
        "errors": errors,
        "avg_ms": statistics.mean(times_ms),
        "p50_ms": times_ms[p50_idx],
        "p95_ms": times_ms[p95_idx],
    }


def measure_dawn_mist_generation(cur):
    """Measure dawn mist cadence — interval between successive dawn mist thermals."""
    cur.execute("""
        SELECT
            EXTRACT(EPOCH FROM (created_at - LAG(created_at) OVER (ORDER BY created_at))) as interval_seconds
        FROM thermal_memory_archive
        WHERE original_content ILIKE '%%dawn mist%%'
          AND created_at > NOW() - INTERVAL '30 days'
        ORDER BY created_at DESC
        LIMIT 30
    """)
    rows = cur.fetchall()
    times = [r[0] for r in rows if r[0] is not None and r[0] > 0]
    if not times:
        return {"count": 0, "avg_seconds": None}
    return {
        "count": len(times),
        "avg_seconds": statistics.mean(times),
    }


def fmt(val, unit="s", precision=2):
    """Format a numeric value with unit, or 'N/A' if None."""
    if val is None:
        return "N/A"
    return f"{val:.{precision}f}{unit}"


def print_report(metrics):
    """Print formatted baseline metrics report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cv = metrics["council_vote"]
    jr = metrics["jr_task"]
    tw = metrics["thermal_write"]
    gw = metrics["gateway"]
    dm = metrics["dawn_mist"]

    report = f"""
================================================================================
  CHEROKEE AI FEDERATION — SLA BASELINE METRICS
  Measured: {now}
================================================================================

  1. COUNCIL VOTE RESPONSE TIME (last 30 days)
     Samples:    {cv['count']}
     Average:    {fmt(cv['avg_seconds'])}
     P50:        {fmt(cv['p50_seconds'])}
     P95:        {fmt(cv['p95_seconds'])}

  2. JR TASK COMPLETION TIME (last 30 days)
     Completed:  {jr['completed_count']}
     Failed:     {jr['failed_count']}
     Average:    {fmt(jr['avg_seconds'])}
     P50:        {fmt(jr['p50_seconds'])}
     P95:        {fmt(jr['p95_seconds'])}

  3. THERMAL MEMORY WRITE RATE (last 24 hours)
     Writes:     {tw['writes_24h']}
     Avg interval: {fmt(tw['avg_interval_seconds'])}

  4. GATEWAY RESPONSE TIME (redfin:8080/health)
     Samples:    {gw['samples']}
     Errors:     {gw['errors']}
     Average:    {fmt(gw['avg_ms'], 'ms')}
     P50:        {fmt(gw['p50_ms'], 'ms')}
     P95:        {fmt(gw['p95_ms'], 'ms')}

  5. DAWN MIST GENERATION TIME (last 30 days)
     Samples:    {dm['count']}
     Average:    {fmt(dm['avg_seconds'])}

================================================================================
"""
    print(report)
    return report


def write_report(report_text):
    """Write report to markdown file."""
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = "# SLA Baseline Metrics\n\n"
    header += f"**Generated:** {now}\n"
    header += "**Task:** #1206 / #1257\n"
    header += "**Purpose:** Baseline measurements for SLA Framework (Task #1207)\n\n"
    md = header + report_text + "\n"
    with open(REPORT_PATH, "w") as f:
        f.write(md)
    print(f"Report written to {REPORT_PATH}")


def collect_all_metrics():
    """Collect all SLA baseline measurements."""
    load_secrets()
    conn = get_connection()
    cur = conn.cursor()
    metrics = {
        "council_vote": measure_council_vote_time(cur),
        "jr_task": measure_jr_task_completion(cur),
        "thermal_write": measure_thermal_write_latency(cur),
        "gateway": measure_gateway_response(),
        "dawn_mist": measure_dawn_mist_generation(cur),
    }
    cur.close()
    conn.commit()  # explicit commit before close
    conn.close()
    return metrics


if __name__ == "__main__":
    metrics = collect_all_metrics()
    report = print_report(metrics)
    write_report(report)
# Jr Instruction: SLA Baseline Metrics — Governance Response Time (FIXED)

**Task**: #1257 / #1206 (retry)
**Date**: 2026-03-12
**Priority**: 2
**TPM**: Claude Opus

## Context

Previous attempts (#1257, #1206) failed due to wrong table/column names in the SQL queries. This instruction fixes:
- Table `longhouse_votes` → `council_votes` (correct table name)
- Column `content` → `original_content` (correct column on thermal_memory_archive)
- Column `updated_at` → `voted_at` on council_votes (correct timestamp column)

The script measures federation governance performance baselines: council vote latency, Jr task throughput, thermal write rate, gateway response time, and dawn mist generation time.

## Constraints

- Read-only DB queries. Do NOT write to the database.
- Credentials from `/ganuda/config/secrets.env` — never hardcode passwords.
- No imports from federation libraries — standalone script.
- Gateway health check timeout: 10 seconds per request.

---

### Step 1: Create the SLA baseline metrics script

**File:** `/ganuda/scripts/sla_baseline_metrics.py`

```python
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
    """Measure time between vote creation and resolution (last 30 days)."""
    cur.execute("""
        SELECT
            EXTRACT(EPOCH FROM (voted_at - created_at)) as resolution_seconds
        FROM council_votes
        WHERE created_at > NOW() - INTERVAL '30 days'
          AND voted_at IS NOT NULL
          AND voted_at > created_at
        ORDER BY created_at DESC
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
    """Measure dawn mist generation time from thermal records."""
    cur.execute("""
        SELECT
            EXTRACT(EPOCH FROM (updated_at - created_at)) as gen_seconds
        FROM thermal_memory_archive
        WHERE original_content ILIKE '%%dawn mist%%'
          AND created_at > NOW() - INTERVAL '30 days'
          AND updated_at IS NOT NULL
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
    md = f"""# SLA Baseline Metrics

**Generated:** {now}
**Task:** #1206 / #1257
**Purpose:** Baseline measurements for SLA Framework (Task #1207)

```
{report_text.strip()}
```

## Notes

- Council vote time measures creation-to-voted_at (includes async specialist deliberation)
- Jr task time measures creation-to-completion (includes queue wait + execution)
- Gateway response is measured from redfin localhost — external latency will be higher
- Dawn mist generation includes full council session + thermal write
- These baselines should be re-measured monthly to track drift
"""
    with open(REPORT_PATH, 'w') as f:
        f.write(md)
    print(f"Report written to {REPORT_PATH}")


def main():
    write_flag = '--write-report' in sys.argv

    conn = get_connection()
    cur = conn.cursor()

    try:
        metrics = {
            "council_vote": measure_council_vote_time(cur),
            "jr_task": measure_jr_task_completion(cur),
            "thermal_write": measure_thermal_write_latency(cur),
            "gateway": measure_gateway_response(),
            "dawn_mist": measure_dawn_mist_generation(cur),
        }
    finally:
        cur.close()
        conn.close()

    report_text = print_report(metrics)

    if write_flag:
        write_report(report_text)


if __name__ == "__main__":
    main()
```

### Step 2: Make the script executable

```bash
chmod +x /ganuda/scripts/sla_baseline_metrics.py
```

### Step 3: Run the script to verify output

```bash
python3 /ganuda/scripts/sla_baseline_metrics.py
```

Verify all 5 metric sections produce output (N/A is acceptable for sections with no data).

### Step 4: Generate the report file

```bash
mkdir -p /ganuda/docs/business && python3 /ganuda/scripts/sla_baseline_metrics.py --write-report
```

## Acceptance Criteria

- Script exists at `/ganuda/scripts/sla_baseline_metrics.py` and is executable
- Script measures all 5 metrics: council vote time, Jr task completion, thermal write rate, gateway response, dawn mist generation
- Script outputs a formatted table to stdout
- `--write-report` flag writes markdown summary to `/ganuda/docs/business/SLA-BASELINE-METRICS-MAR12-2026.md`
- Script handles missing data gracefully (N/A, not crash)
- Script uses credentials from `/ganuda/config/secrets.env` (never hardcoded)
- Script completes in under 30 seconds

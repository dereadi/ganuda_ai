# Jr Instruction: DC-16 Body Report Digest Timer

**Task #:** TBD (will be assigned)
**Title:** DC-16: 6-Hour Body Report Digest Timer
**Date:** March 10, 2026
**Priority:** 2 (DC-16 Fail Loud — Phase 1, observability)

## Context

The federation handles many events automatically — Fire Guard restarts services, the Jr
executor recovers from DB connection failures, circuit breakers trip and reset. These events
are logged individually but nobody sees the aggregate picture unless they dig through
thermals and journal logs.

DC-16 Fail Loud requires that silently-handled events be reported in aggregate. A "body
report" — like the body reporting to the brain: "handled a cramp in the left leg, digestion
is fine, heart rate elevated for 20 minutes but recovered." Not individual alerts. A digest
with trends.

This script runs every 6 hours, queries the last 6 hours of federation activity, formats
a concise digest, posts it to Slack #dawn-mist, and thermalizes it for the record.

## Task

Create `/ganuda/scripts/body_report.py` plus systemd service and timer unit files.

## Steps

### Step 1: Create the body report script

Create new file: `/ganuda/scripts/body_report.py`

```python
#!/usr/bin/env python3
"""
DC-16 Body Report — 6-hour federation health digest.

Queries thermal memory, Jr task queue, specialist health, and journal logs
to produce a concise digest of automatically-handled events. Posts to
Slack #dawn-mist and thermalizes the report.

Runs every 6 hours via systemd timer (00:15, 06:15, 12:15, 18:15 CT).

For Seven Generations.
"""

import hashlib
import json
import logging
import os
import subprocess
import sys
from datetime import datetime

import psycopg2

sys.path.insert(0, '/ganuda/lib')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("body_report")

# --- Configuration ---

DB_HOST = os.environ.get("CHEROKEE_DB_HOST", "192.168.132.222")
DB_NAME = os.environ.get("CHEROKEE_DB_NAME", "zammad_production")
DB_USER = os.environ.get("CHEROKEE_DB_USER", "claude")
DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")

REPORT_WINDOW_HOURS = 6


def get_db_conn():
    return psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS
    )


def query_fire_guard_alerts(cur):
    """Count fire guard alerts in the last 6 hours from thermal_memory_archive."""
    cur.execute("""
        SELECT COUNT(*),
               COUNT(CASE WHEN temperature_score >= 80 THEN 1 END) as critical_count
        FROM thermal_memory_archive
        WHERE original_content ILIKE '%%FIRE GUARD%%'
          AND created_at > NOW() - INTERVAL '%s hours'
    """, (REPORT_WINDOW_HOURS,))
    row = cur.fetchone()
    return {'total': row[0] or 0, 'critical': row[1] or 0}


def query_jr_activity(cur):
    """Count Jr task completions, failures, and DLQ entries in last 6 hours."""
    # Completed tasks
    cur.execute("""
        SELECT COUNT(*)
        FROM jr_work_queue
        WHERE status = 'completed'
          AND updated_at > NOW() - INTERVAL '%s hours'
    """, (REPORT_WINDOW_HOURS,))
    completed = cur.fetchone()[0] or 0

    # Failed tasks
    cur.execute("""
        SELECT COUNT(*)
        FROM jr_work_queue
        WHERE status = 'failed'
          AND updated_at > NOW() - INTERVAL '%s hours'
    """, (REPORT_WINDOW_HOURS,))
    failed = cur.fetchone()[0] or 0

    # DLQ entries
    cur.execute("""
        SELECT COUNT(*)
        FROM jr_failed_tasks_dlq
        WHERE created_at > NOW() - INTERVAL '%s hours'
    """, (REPORT_WINDOW_HOURS,))
    dlq = cur.fetchone()[0] or 0

    return {'completed': completed, 'failed': failed, 'dlq': dlq}


def query_circuit_breakers(cur):
    """Check specialist health / circuit breaker states."""
    cur.execute("""
        SELECT specialist_id,
               COUNT(CASE WHEN had_concern THEN 1 END) as concern_count,
               COUNT(*) as total_checks
        FROM specialist_health
        WHERE measured_at > NOW() - INTERVAL '%s hours'
        GROUP BY specialist_id
        ORDER BY concern_count DESC
    """, (REPORT_WINDOW_HOURS,))
    rows = cur.fetchall()
    return [
        {'specialist': row[0], 'concerns': row[1], 'checks': row[2]}
        for row in rows
    ]


def query_connection_recoveries():
    """Count DB connection retry events from jr-se journal logs."""
    try:
        result = subprocess.run(
            ['journalctl', '-u', 'jr-se.service', '--since', f'-{REPORT_WINDOW_HOURS}h',
             '--no-pager', '-q'],
            capture_output=True, text=True, timeout=15
        )
        lines = result.stdout.splitlines()
        retry_count = sum(1 for line in lines if 'Retry' in line or 'retry' in line)
        reconnect_count = sum(1 for line in lines if 'reconnect' in line.lower())
        return {'retries': retry_count, 'reconnects': reconnect_count}
    except Exception as e:
        log.warning("Journal query failed: %s", e)
        return {'retries': -1, 'reconnects': -1}


def query_previous_window(cur):
    """Get previous window's stats for trend comparison."""
    cur.execute("""
        SELECT COUNT(*)
        FROM thermal_memory_archive
        WHERE original_content ILIKE '%%FIRE GUARD%%'
          AND created_at > NOW() - INTERVAL '%s hours'
          AND created_at <= NOW() - INTERVAL '%s hours'
    """, (REPORT_WINDOW_HOURS * 2, REPORT_WINDOW_HOURS))
    prev_fire_guard = cur.fetchone()[0] or 0

    cur.execute("""
        SELECT COUNT(*)
        FROM jr_failed_tasks_dlq
        WHERE created_at > NOW() - INTERVAL '%s hours'
          AND created_at <= NOW() - INTERVAL '%s hours'
    """, (REPORT_WINDOW_HOURS * 2, REPORT_WINDOW_HOURS))
    prev_dlq = cur.fetchone()[0] or 0

    return {'fire_guard_alerts': prev_fire_guard, 'dlq': prev_dlq}


def trend_label(current, previous):
    """Generate a trend indicator: up/down/flat."""
    if previous == 0 and current == 0:
        return "flat"
    if previous == 0:
        return f"new ({current})"
    if current > previous:
        return f"up from {previous}"
    if current < previous:
        return f"down from {previous}"
    return "flat"


def format_digest(fire_guard, jr_activity, breakers, conn_recovery, prev_window):
    """Format the body report digest as concise text."""
    now = datetime.now().strftime('%Y-%m-%d %H:%M CT')
    lines = [
        f"*BODY REPORT* — {now} (last {REPORT_WINDOW_HOURS}h)",
        "",
    ]

    # Fire Guard
    fg_trend = trend_label(fire_guard['total'], prev_window['fire_guard_alerts'])
    lines.append(f"*Fire Guard:* {fire_guard['total']} alerts "
                 f"({fire_guard['critical']} critical) — {fg_trend}")

    # Jr Tasks
    lines.append(f"*Jr Tasks:* {jr_activity['completed']} completed, "
                 f"{jr_activity['failed']} failed, "
                 f"{jr_activity['dlq']} DLQ ({trend_label(jr_activity['dlq'], prev_window['dlq'])})")

    # Circuit Breakers
    tripped = [b for b in breakers if b['concerns'] > 0]
    if tripped:
        breaker_parts = [f"{b['specialist']}({b['concerns']}/{b['checks']})" for b in tripped]
        lines.append(f"*Circuit Breakers:* {len(tripped)} tripped — " + ", ".join(breaker_parts))
    else:
        total_checks = sum(b['checks'] for b in breakers)
        lines.append(f"*Circuit Breakers:* all clear ({total_checks} checks)")

    # Connection Recovery
    if conn_recovery['retries'] >= 0:
        lines.append(f"*Connection Recovery:* {conn_recovery['retries']} retries, "
                     f"{conn_recovery['reconnects']} reconnects")
    else:
        lines.append("*Connection Recovery:* journal query unavailable")

    return "\n".join(lines)


def post_to_slack(digest):
    """Post digest to Slack #dawn-mist."""
    try:
        from slack_federation import send as slack_send
        return slack_send("dawn-mist", digest)
    except Exception as e:
        log.error("Slack post failed: %s", e)
        return False


def thermalize_digest(conn, digest):
    """Store digest in thermal_memory_archive."""
    memory_hash = hashlib.sha256(
        f"body-report-{datetime.now().isoformat()}".encode()
    ).hexdigest()[:16]

    metadata = json.dumps({
        "type": "body_report",
        "window_hours": REPORT_WINDOW_HOURS,
        "generated_at": datetime.now().isoformat(),
    })

    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO thermal_memory_archive
            (memory_hash, original_content, temperature_score, metadata,
             source_node, memory_type, domain_tag, tags, created_at)
            VALUES (%s, %s, %s, %s::jsonb, 'redfin', 'episodic',
                    'body_report', %s, NOW())
        """, (memory_hash, digest, 55, metadata,
              ['body_report', 'health', 'digest']))
        conn.commit()
        log.info("Thermalized body report (hash=%s, temp=55)", memory_hash)
    except Exception as e:
        log.error("Thermalization failed: %s", e)
        conn.rollback()


def main():
    log.info("Generating body report (window=%dh)", REPORT_WINDOW_HOURS)

    try:
        conn = get_db_conn()
    except Exception as e:
        log.error("DB connection failed: %s", e)
        # Even a failed connection is worth reporting
        try:
            from slack_federation import send as slack_send
            slack_send("dawn-mist",
                       f"*BODY REPORT FAILED* — Cannot connect to DB: {e}")
        except Exception:
            pass
        sys.exit(1)

    try:
        cur = conn.cursor()

        fire_guard = query_fire_guard_alerts(cur)
        jr_activity = query_jr_activity(cur)
        breakers = query_circuit_breakers(cur)
        conn_recovery = query_connection_recoveries()
        prev_window = query_previous_window(cur)

        digest = format_digest(fire_guard, jr_activity, breakers,
                               conn_recovery, prev_window)

        log.info("Digest:\n%s", digest)

        # Post to Slack
        if post_to_slack(digest):
            log.info("Posted to Slack #dawn-mist")
        else:
            log.warning("Slack post failed or unavailable")

        # Thermalize
        thermalize_digest(conn, digest)

    except Exception as e:
        log.error("Body report generation failed: %s", e)
        sys.exit(1)
    finally:
        conn.close()

    log.info("Body report complete")


if __name__ == "__main__":
    main()
```

### Step 2: Create systemd service unit

Create new file: `/ganuda/scripts/body-report.service`

```ini
[Unit]
Description=DC-16 Body Report — 6-hour federation health digest
After=network.target

[Service]
Type=oneshot
EnvironmentFile=/ganuda/config/secrets.env
ExecStart=/usr/bin/python3 /ganuda/scripts/body_report.py
WorkingDirectory=/ganuda
User=dereadi
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Step 3: Create systemd timer unit

Create new file: `/ganuda/scripts/body-report.timer`

```ini
[Unit]
Description=DC-16 Body Report Timer — every 6 hours

[Timer]
OnCalendar=*-*-* 00,06,12,18:15:00
Persistent=true

[Install]
WantedBy=timers.target
```

### Step 4: Deploy and enable (run on redfin)

```bash
sudo cp /ganuda/scripts/body-report.service /etc/systemd/system/
sudo cp /ganuda/scripts/body-report.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now body-report.timer
```

### Step 5: Verify timer is scheduled

```bash
systemctl list-timers body-report.timer
# Should show next firing at :15 past the next 6-hour mark
```

## Acceptance Criteria

1. `body_report.py` runs without error and produces a digest to stdout.
2. The digest includes: fire guard alert count, Jr task stats, circuit breaker states,
   connection recovery counts — each with trend comparison to previous window.
3. Digest is posted to Slack #dawn-mist via `slack_federation.send()`.
4. Digest is stored in `thermal_memory_archive` with `domain_tag='body_report'`,
   `temperature_score=55`.
5. Timer fires at 00:15, 06:15, 12:15, 18:15 CT daily.
6. If DB connection fails, the script still attempts to notify Slack and exits non-zero.
7. Schema references are correct: `original_content` (not `content`),
   `temperature_score` (not `temperature`), `jr_work_queue` (not `jr_tasks`),
   `jr_failed_tasks_dlq` with `created_at`.

## Constraints

- DB connection: host=192.168.132.222, port=5432, dbname=zammad_production, user=claude,
  password from `CHEROKEE_DB_PASS` in `/ganuda/config/secrets.env`.
- No new pip dependencies. Uses only: psycopg2, requests (already installed), stdlib.
- The report must be CONCISE — no more than 8 lines. Show trends, not raw data dumps.
- Slack is best-effort. A failed Slack post must not crash the script.
- Temperature score 55 (room temp, informational — not hot enough to trigger attention,
  warm enough to survive thermal purge).
- Timer uses `Persistent=true` so missed runs (e.g., reboot) fire on next boot.
- Journal query for connection recoveries may fail (no sudo) — handle gracefully.

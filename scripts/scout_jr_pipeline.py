#!/usr/bin/env python3
"""Scout Daemon — Unetlanvhi's eyes on the Jr pipeline. Leaders Meeting #1, Mar 10 2026."""

import argparse
import sys
import datetime

sys.path.insert(0, "/ganuda/lib")
sys.path.insert(0, "/ganuda")

import psycopg2
from lib.secrets_loader import get_db_config
from lib import slack_federation


STUCK_THRESHOLD_HOURS = 2
DRY_THRESHOLD_HOURS = 4
FAIL_THRESHOLD_HOURS = 6
FAIL_COUNT_LIMIT = 3

QUERIES = {
    "stuck": """
        SELECT id, task_title, started_at
        FROM jr_work_queue
        WHERE status = 'in_progress'
          AND started_at < NOW() - INTERVAL '2 hours'
    """,
    "dry": """
        SELECT completed_at
        FROM jr_work_queue
        WHERE status = 'completed'
        ORDER BY completed_at DESC
        LIMIT 1
    """,
    "failing": """
        SELECT COUNT(*)
        FROM jr_work_queue
        WHERE status = 'failed'
          AND updated_at > NOW() - INTERVAL '6 hours'
    """,
}


def check_pipeline():
    """Run all three health checks. Returns list of alert strings."""
    alerts = []
    db_conf = get_db_config()
    conn = psycopg2.connect(
        host=db_conf["host"],
        dbname=db_conf["dbname"],
        user=db_conf["user"],
        password=db_conf["password"],
        port=db_conf.get("port", 5432),
    )
    try:
        cur = conn.cursor()

        # 1. Stuck tasks
        cur.execute(QUERIES["stuck"])
        stuck = cur.fetchall()
        if stuck:
            ids = ", ".join(f"#{r[0]}" for r in stuck)
            alerts.append(
                f"STUCK: {len(stuck)} task(s) in_progress > {STUCK_THRESHOLD_HOURS}h — {ids}"
            )

        # 2. Queue dry
        cur.execute(QUERIES["dry"])
        row = cur.fetchone()
        if row is None:
            alerts.append("DRY: No completed tasks found at all — pipeline may be dead.")
        elif row[0] is not None:
            age = datetime.datetime.now(datetime.timezone.utc) - row[0].astimezone(
                datetime.timezone.utc
            )
            if age > datetime.timedelta(hours=DRY_THRESHOLD_HOURS):
                alerts.append(
                    f"DRY: No completions in {age.total_seconds() / 3600:.1f}h (threshold {DRY_THRESHOLD_HOURS}h)."
                )

        # 3. Failure spike
        cur.execute(QUERIES["failing"])
        fail_count = cur.fetchone()[0]
        if fail_count > FAIL_COUNT_LIMIT:
            alerts.append(
                f"FAILING: {fail_count} failed tasks in last {FAIL_THRESHOLD_HOURS}h (limit {FAIL_COUNT_LIMIT})."
            )
    finally:
        conn.close()

    return alerts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print alerts instead of sending to Slack")
    args = parser.parse_args()

    alerts = check_pipeline()
    if not alerts:
        print("Scout: Jr pipeline healthy. No alerts.")
        return

    header = "🔥 *Scout Jr Pipeline Alert*"
    message = header + "\n" + "\n".join(f"• {a}" for a in alerts)

    if args.dry_run:
        print(message)
    else:
        slack_federation.send("fire-guard", message, urgent=True)
        print(f"Scout: Sent {len(alerts)} alert(s) to #fire-guard.")


if __name__ == "__main__":
    main()

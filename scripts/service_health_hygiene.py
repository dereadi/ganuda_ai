#!/usr/bin/env python3
"""service_health hygiene — auto-suppress stale + chronically-failing entries.

Closes Council vote 782198bac4be42dd (May 4 2026, Peace Chief synthesis):
auto-prune stale service_health rows to a 'suppressed' state with manual
override, addressing Eagle Eye's alarm-fatigue concern (16,792 consecutive
failures since Feb on Grafana drowning new signal) and Crawdad's audit-trail
concern (don't delete — mute and keep).

Behavior:
  - Marks rows suppressed=TRUE if:
      * consecutive_failures > FAILURE_THRESHOLD (default 1000), OR
      * last_check older than STALE_DAYS (default 30 days)
  - Records suppression timestamp + reason for audit
  - Re-checks daily (idempotent — won't re-suppress already-suppressed rows
    unless their state changed)
  - --report-only mode for review without writes
  - --unsuppress=<service_name>:<node_name> for manual override
  - --list-suppressed to inspect current suppressed set

Run via cron daily ~05:55 UTC (just before Dawn Mist 06:15) or ad-hoc.
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timedelta

sys.path.insert(0, "/ganuda")
sys.path.insert(0, "/ganuda/lib")

from ganuda_db import get_connection, get_dict_cursor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s service_health_hygiene: %(message)s",
)
logger = logging.getLogger("service_health_hygiene")

FAILURE_THRESHOLD = 1000
STALE_DAYS = 30


def find_candidates(cur, failure_threshold: int, stale_days: int):
    """Find service_health rows that should be suppressed."""
    cur.execute(f"""
        SELECT health_id, node_name, service_name, status,
               consecutive_failures, last_check, suppressed
        FROM service_health
        WHERE suppressed = FALSE
          AND (
              consecutive_failures > %s
              OR last_check < NOW() - INTERVAL '{int(stale_days)} days'
          )
        ORDER BY consecutive_failures DESC, last_check ASC
    """, (failure_threshold,))
    return cur.fetchall()


def suppress_row(cur, row, reason: str) -> None:
    cur.execute("""
        UPDATE service_health
        SET suppressed = TRUE,
            suppressed_at = NOW(),
            suppressed_reason = %s
        WHERE health_id = %s
    """, (reason[:200], row['health_id']))


def list_suppressed(cur) -> None:
    cur.execute("""
        SELECT node_name, service_name, status, consecutive_failures,
               last_check, suppressed_at, suppressed_reason
        FROM service_health
        WHERE suppressed = TRUE
        ORDER BY suppressed_at DESC NULLS LAST
    """)
    rows = cur.fetchall()
    if not rows:
        print("No suppressed service_health entries.")
        return
    print(f"{len(rows)} suppressed service_health entries:")
    for r in rows:
        print(
            f"  {r['service_name']:30s} on {r['node_name']:10s} "
            f"({r['status']:10s} cf={r['consecutive_failures']:>6d}) — "
            f"{r['suppressed_reason']}"
        )


def unsuppress(cur, target: str) -> int:
    """Manual override — unsuppress a service:node entry."""
    if ':' not in target:
        raise ValueError(f"--unsuppress format: service_name:node_name (got {target!r})")
    service_name, node_name = target.split(':', 1)
    cur.execute("""
        UPDATE service_health
        SET suppressed = FALSE,
            suppressed_at = NULL,
            suppressed_reason = NULL
        WHERE service_name = %s AND node_name = %s
    """, (service_name, node_name))
    return cur.rowcount


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--report-only", action="store_true",
                    help="Print candidates without writing")
    ap.add_argument("--list-suppressed", action="store_true",
                    help="List currently-suppressed entries and exit")
    ap.add_argument("--unsuppress", metavar="SERVICE:NODE",
                    help="Unsuppress a specific service_name:node_name pair")
    ap.add_argument("--failure-threshold", type=int, default=FAILURE_THRESHOLD,
                    help=f"consecutive_failures threshold (default {FAILURE_THRESHOLD})")
    ap.add_argument("--stale-days", type=int, default=STALE_DAYS,
                    help=f"last_check staleness threshold (default {STALE_DAYS})")
    args = ap.parse_args()

    conn = get_connection()
    try:
        cur = get_dict_cursor(conn)

        if args.list_suppressed:
            list_suppressed(cur)
            return

        if args.unsuppress:
            n = unsuppress(cur, args.unsuppress)
            conn.commit()
            print(f"Unsuppressed {n} row(s) matching {args.unsuppress!r}")
            return

        candidates = find_candidates(cur, args.failure_threshold, args.stale_days)
        if not candidates:
            logger.info("No stale or chronically-failing service_health rows. Clean.")
            return

        logger.info(
            "Found %d service_health row(s) to suppress "
            "(threshold cf>%d OR last_check>%dd ago)",
            len(candidates), args.failure_threshold, args.stale_days,
        )

        for row in candidates:
            stale_age = datetime.now() - row['last_check'] if row['last_check'] else None
            reasons = []
            if row['consecutive_failures'] > args.failure_threshold:
                reasons.append(f"cf={row['consecutive_failures']}>{args.failure_threshold}")
            if stale_age and stale_age.days > args.stale_days:
                reasons.append(f"stale={stale_age.days}d")
            reason = "; ".join(reasons)

            logger.info(
                "  %s on %s (status=%s cf=%d last_check=%s) — %s",
                row['service_name'], row['node_name'], row['status'],
                row['consecutive_failures'], row['last_check'], reason,
            )

            if not args.report_only:
                suppress_row(cur, row, reason)

        if args.report_only:
            logger.info("--report-only mode: no writes. Re-run without --report-only to apply.")
        else:
            conn.commit()
            logger.info("Suppressed %d row(s). Use --unsuppress to undo individual entries.", len(candidates))
    finally:
        conn.close()


if __name__ == "__main__":
    main()

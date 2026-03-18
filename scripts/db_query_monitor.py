"""Long-Running Query Monitor — Remedy Heritage Pattern.

Polls pg_stat_activity every 30 seconds for queries running longer than thresholds.
Logs offenders. Produces weekly top-offender reports.

Internal SLAs:
- Log any query > 500ms (the floor — don't tune below this)
- Alert (Slack) any query > 90s (approaching 2-min timeout)
- Statement timeout stays at 2min (guardrail, not a bug)

Usage:
  python3 scripts/db_query_monitor.py              # Run continuous monitor
  python3 scripts/db_query_monitor.py --report      # Weekly top-offender report
  python3 scripts/db_query_monitor.py --snapshot     # Single snapshot
"""

import csv
import io
import os
import sys
import time
import json
import logging
import signal
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

import psycopg2
import psycopg2.extras

# ---------------------------------------------------------------------------
# Resolve GANUDA_ROOT and wire up lib imports
# ---------------------------------------------------------------------------
if sys.platform == "darwin":
    _GANUDA_ROOT = "/Users/Shared/ganuda"
else:
    _GANUDA_ROOT = "/ganuda"

sys.path.insert(0, _GANUDA_ROOT)

from lib.secrets_loader import get_db_config  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_DIR = os.path.join(_GANUDA_ROOT, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(LOG_DIR, "db_query_monitor.log")),
    ],
)
logger = logging.getLogger("ganuda.db_query_monitor")

# ---------------------------------------------------------------------------
# Thresholds (Internal SLAs)
# ---------------------------------------------------------------------------
POLL_INTERVAL_SECONDS = 30
LOG_THRESHOLD_MS = 500       # Log any query over 500ms
ALERT_THRESHOLD_MS = 90_000  # Alert any query over 90s
QUERY_FLOOR_MS = 500         # Don't tune below this — diminishing returns

# ---------------------------------------------------------------------------
# CSV offender log
# ---------------------------------------------------------------------------
OFFENDER_CSV = os.path.join(LOG_DIR, "db_query_offenders.csv")
CSV_HEADER = ["timestamp", "pid", "user", "client", "duration_ms", "query_snippet"]

# ---------------------------------------------------------------------------
# Graceful shutdown
# ---------------------------------------------------------------------------
_running = True


def _handle_signal(signum, frame):
    global _running
    logger.info("Received signal %d, shutting down gracefully...", signum)
    _running = False


signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)


# ---------------------------------------------------------------------------
# Slack alerting (best-effort)
# ---------------------------------------------------------------------------
def _try_slack_alert(message: str) -> bool:
    """Send alert to fire-guard channel. Returns False on any failure."""
    try:
        from lib.slack_federation import send
        return send("fire-guard", message, urgent=True)
    except Exception as exc:
        logger.warning("Slack alert failed (non-fatal): %s", exc)
        return False


# ---------------------------------------------------------------------------
# Database connection with reconnection logic
# ---------------------------------------------------------------------------
def get_db_connection():
    """Connect using secrets_loader three-tier resolution."""
    db_cfg = get_db_config(prefix="CHEROKEE")
    conn = psycopg2.connect(
        host=db_cfg["host"],
        port=db_cfg["port"],
        dbname=db_cfg["dbname"],
        user=db_cfg["user"],
        password=db_cfg["password"],
        connect_timeout=10,
        options="-c statement_timeout=10000",  # 10s timeout for our own monitoring queries
    )
    conn.set_session(autocommit=True)
    logger.info(
        "Connected to %s@%s:%s/%s",
        db_cfg["user"], db_cfg["host"], db_cfg["port"], db_cfg["dbname"],
    )
    return conn


def _ensure_connection(conn):
    """Test connection, reconnect if stale. Returns a live connection."""
    if conn is None:
        return get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        return conn
    except Exception:
        logger.warning("DB connection stale, reconnecting...")
        try:
            conn.commit()  # explicit commit before close
            conn.close()
        except Exception:
            pass
        return get_db_connection()


# ---------------------------------------------------------------------------
# Core polling
# ---------------------------------------------------------------------------
_POLL_SQL = """
SELECT pid,
       usename,
       client_addr,
       state,
       EXTRACT(EPOCH FROM (now() - query_start)) * 1000 AS duration_ms,
       LEFT(query, 200) AS query_snippet,
       wait_event_type,
       wait_event
  FROM pg_stat_activity
 WHERE state = 'active'
   AND query NOT LIKE '%%pg_stat_activity%%'
   AND query_start < now() - interval '%s milliseconds'
 ORDER BY duration_ms DESC
"""


def poll_active_queries(conn):
    """Query pg_stat_activity for active queries over threshold.

    Returns a list of dicts with query details.
    """
    rows = []
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(_POLL_SQL, (QUERY_FLOOR_MS,))
        for row in cur.fetchall():
            rows.append({
                "pid": row["pid"],
                "usename": row["usename"] or "unknown",
                "client_addr": str(row["client_addr"] or "local"),
                "state": row["state"],
                "duration_ms": round(float(row["duration_ms"]), 1),
                "query_snippet": row["query_snippet"] or "",
                "wait_event_type": row["wait_event_type"] or "",
                "wait_event": row["wait_event"] or "",
            })
    return rows


# ---------------------------------------------------------------------------
# Offender logging
# ---------------------------------------------------------------------------
def _ensure_csv_header():
    """Write CSV header if file doesn't exist or is empty."""
    if not os.path.exists(OFFENDER_CSV) or os.path.getsize(OFFENDER_CSV) == 0:
        with open(OFFENDER_CSV, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADER)


def log_offender(pid, usename, client_addr, duration_ms, query_snippet):
    """Append a long-running query to the CSV offender log."""
    _ensure_csv_header()
    # Sanitize query_snippet — remove newlines for CSV safety
    snippet = query_snippet.replace("\n", " ").replace("\r", "")[:200]
    with open(OFFENDER_CSV, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.utcnow().isoformat(),
            pid,
            usename,
            client_addr,
            round(duration_ms, 1),
            snippet,
        ])


def should_alert(duration_ms):
    """Check if query exceeds alert threshold (90s)."""
    return duration_ms >= ALERT_THRESHOLD_MS


def send_alert(pid, usename, duration_ms, query_snippet):
    """Send Slack alert for queries approaching timeout."""
    duration_s = round(duration_ms / 1000, 1)
    snippet = query_snippet[:100].replace("\n", " ")
    msg = (
        f":warning: *Long-Running Query Alert*\n"
        f"PID `{pid}` | User `{usename}` | Duration `{duration_s}s`\n"
        f"```{snippet}```\n"
        f"_Approaching 2-min statement timeout. Investigate or add an index._"
    )
    logger.warning(
        "ALERT: pid=%s user=%s duration=%.1fs query=%s",
        pid, usename, duration_s, snippet,
    )
    _try_slack_alert(msg)


# ---------------------------------------------------------------------------
# De-duplication: don't spam alerts for the same PID within a poll cycle
# ---------------------------------------------------------------------------
_alerted_pids = {}  # pid -> last alert timestamp
_ALERT_COOLDOWN_S = 300  # 5 minutes between alerts for the same PID


def _should_send_alert(pid):
    """Rate-limit alerts: one per PID per cooldown window."""
    now = time.time()
    last = _alerted_pids.get(pid, 0)
    if now - last >= _ALERT_COOLDOWN_S:
        _alerted_pids[pid] = now
        return True
    return False


# ---------------------------------------------------------------------------
# Weekly report
# ---------------------------------------------------------------------------
def _query_pg_stat_statements(conn):
    """Query pg_stat_statements for top offenders by total time and calls.

    Returns markdown string. Gracefully returns empty string if the
    extension is not installed.
    """
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Check if pg_stat_statements is available
            cur.execute(
                "SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'"
            )
            if not cur.fetchone():
                return ""

            cur.execute("""
                SELECT LEFT(query, 120) AS query_snippet,
                       calls,
                       ROUND(total_exec_time::numeric, 1) AS total_ms,
                       ROUND((mean_exec_time)::numeric, 1) AS avg_ms,
                       ROUND(max_exec_time::numeric, 1) AS max_ms,
                       rows
                  FROM pg_stat_statements
                 WHERE userid != 10  -- skip postgres superuser internals
                 ORDER BY total_exec_time DESC
                 LIMIT 15
            """)
            rows = cur.fetchall()

        if not rows:
            return ""

        lines = [
            "## pg_stat_statements — Top 15 by Total Time",
            "",
            "| # | Calls | Avg(ms) | Max(ms) | Total(ms) | Rows | Query |",
            "|---|-------|---------|---------|-----------|------|-------|",
        ]
        for i, r in enumerate(rows, 1):
            snippet = r["query_snippet"].replace("\n", " ").replace("|", "/")[:80]
            lines.append(
                f"| {i} | {r['calls']} | {r['avg_ms']} | {r['max_ms']} "
                f"| {r['total_ms']} | {r['rows']} | `{snippet}` |"
            )
        lines.append("")
        return "\n".join(lines)

    except Exception as exc:
        logger.warning("pg_stat_statements query failed (non-fatal): %s", exc)
        return ""


def _query_pg_stat_database(conn):
    """Query pg_stat_database for rollback rate and basic health stats.

    Returns markdown string.
    """
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT datname,
                       xact_commit,
                       xact_rollback,
                       CASE WHEN (xact_commit + xact_rollback) > 0
                            THEN ROUND(100.0 * xact_rollback / (xact_commit + xact_rollback), 2)
                            ELSE 0 END AS rollback_pct,
                       blks_hit,
                       blks_read,
                       CASE WHEN (blks_hit + blks_read) > 0
                            THEN ROUND(100.0 * blks_hit / (blks_hit + blks_read), 2)
                            ELSE 0 END AS cache_hit_pct,
                       deadlocks,
                       temp_files,
                       ROUND(temp_bytes / 1048576.0, 1) AS temp_mb
                  FROM pg_stat_database
                 WHERE datname NOT LIKE 'template%%'
                   AND datname IS NOT NULL
                 ORDER BY (xact_commit + xact_rollback) DESC
            """)
            rows = cur.fetchall()

        if not rows:
            return ""

        lines = [
            "## pg_stat_database — Health Summary",
            "",
            "| Database | Commits | Rollbacks | Rollback% | Cache Hit% | Deadlocks | Temp Files | Temp MB |",
            "|----------|---------|-----------|-----------|------------|-----------|------------|---------|",
        ]
        for r in rows:
            lines.append(
                f"| {r['datname']} | {r['xact_commit']} | {r['xact_rollback']} "
                f"| {r['rollback_pct']}% | {r['cache_hit_pct']}% "
                f"| {r['deadlocks']} | {r['temp_files']} | {r['temp_mb']} |"
            )
        lines.append("")
        return "\n".join(lines)

    except Exception as exc:
        logger.warning("pg_stat_database query failed (non-fatal): %s", exc)
        return ""


def _query_pg_stat_user_tables(conn):
    """Query pg_stat_user_tables for tables needing attention.

    Returns markdown string highlighting tables with high seq scans
    relative to index scans (potential missing indexes).
    """
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT schemaname || '.' || relname AS table_name,
                       seq_scan,
                       idx_scan,
                       COALESCE(n_live_tup, 0) AS live_rows,
                       COALESCE(n_dead_tup, 0) AS dead_rows,
                       CASE WHEN (seq_scan + COALESCE(idx_scan, 0)) > 0
                            THEN ROUND(100.0 * seq_scan / (seq_scan + COALESCE(idx_scan, 0)), 1)
                            ELSE 0 END AS seq_pct
                  FROM pg_stat_user_tables
                 WHERE seq_scan > 100
                 ORDER BY seq_scan DESC
                 LIMIT 15
            """)
            rows = cur.fetchall()

        if not rows:
            return ""

        lines = [
            "## pg_stat_user_tables — Seq Scan Heavy (potential missing indexes)",
            "",
            "| Table | Seq Scans | Idx Scans | Seq% | Live Rows | Dead Rows |",
            "|-------|-----------|-----------|------|-----------|-----------|",
        ]
        for r in rows:
            lines.append(
                f"| {r['table_name']} | {r['seq_scan']} | {r['idx_scan'] or 0} "
                f"| {r['seq_pct']}% | {r['live_rows']} | {r['dead_rows']} |"
            )
        lines.append("")
        return "\n".join(lines)

    except Exception as exc:
        logger.warning("pg_stat_user_tables query failed (non-fatal): %s", exc)
        return ""


def generate_weekly_report():
    """Parse offender log + live DB stats, produce top-offender report.

    Groups by: query pattern (first 100 chars), user
    Sorts by: total duration, count
    Outputs: top 20 offenders with avg/max/count

    Queries pg_stat_statements, pg_stat_database, pg_stat_user_tables
    for live health data.  Posts full markdown report to Slack #fire-guard.

    This is the Remedy pattern — weekly reports showing biggest
    offenders. Some have legit reasons — build indexes for those.
    Others need query rewrites.
    """
    report_date = datetime.utcnow().strftime("%Y-%m-%d")
    cutoff = datetime.utcnow() - timedelta(days=7)
    md_lines = [
        f"# DB Query Offender Report — {report_date}",
        f"_Last 7 days (since {cutoff.date()})_",
        "",
    ]

    # ------------------------------------------------------------------
    # Section 1: CSV offender log analysis
    # ------------------------------------------------------------------
    offenders = defaultdict(lambda: {"count": 0, "total_ms": 0.0, "max_ms": 0.0, "users": set()})

    if os.path.exists(OFFENDER_CSV):
        with open(OFFENDER_CSV, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    ts = datetime.fromisoformat(row["timestamp"])
                    if ts < cutoff:
                        continue
                    duration = float(row["duration_ms"])
                    pattern = row["query_snippet"][:100].strip()
                    entry = offenders[pattern]
                    entry["count"] += 1
                    entry["total_ms"] += duration
                    entry["max_ms"] = max(entry["max_ms"], duration)
                    entry["users"].add(row["user"])
                except (ValueError, KeyError) as exc:
                    logger.debug("Skipping malformed row: %s", exc)
                    continue

    if offenders:
        ranked = sorted(offenders.items(), key=lambda x: x[1]["total_ms"], reverse=True)
        md_lines.append("## CSV Offender Log — Top 20 by Total Duration")
        md_lines.append("")
        md_lines.append("| # | Count | Avg(ms) | Max(ms) | Total(ms) | Users | Query Pattern |")
        md_lines.append("|---|-------|---------|---------|-----------|-------|---------------|")

        for rank, (pattern, stats) in enumerate(ranked[:20], 1):
            avg_ms = stats["total_ms"] / stats["count"] if stats["count"] else 0
            users = ",".join(sorted(stats["users"]))
            snippet = pattern[:60].replace("|", "/")
            md_lines.append(
                f"| {rank} | {stats['count']} | {avg_ms:.1f} | {stats['max_ms']:.1f} "
                f"| {stats['total_ms']:.1f} | {users} | `{snippet}` |"
            )

        total_count = sum(s["count"] for s in offenders.values())
        total_duration = sum(s["total_ms"] for s in offenders.values())
        md_lines.append("")
        md_lines.append(
            f"**Totals:** {total_count} offending queries, "
            f"{total_duration / 1000:.1f}s cumulative, "
            f"{len(offenders)} unique patterns"
        )
        md_lines.append("")
    else:
        md_lines.append("## CSV Offender Log")
        md_lines.append("_No offenders recorded in the last 7 days._")
        md_lines.append("")

    # ------------------------------------------------------------------
    # Section 2+: Live DB stats (pg_stat_statements, database, tables)
    # ------------------------------------------------------------------
    conn = None
    try:
        conn = get_db_connection()

        stat_stmts = _query_pg_stat_statements(conn)
        if stat_stmts:
            md_lines.append(stat_stmts)

        stat_db = _query_pg_stat_database(conn)
        if stat_db:
            md_lines.append(stat_db)

        stat_tables = _query_pg_stat_user_tables(conn)
        if stat_tables:
            md_lines.append(stat_tables)

    except Exception as exc:
        logger.error("Failed to query live DB stats: %s", exc)
        md_lines.append("## Live DB Stats")
        md_lines.append(f"_Query failed: {exc}_")
        md_lines.append("")
    finally:
        if conn:
            try:
                conn.commit()
                conn.close()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Assemble final report
    # ------------------------------------------------------------------
    md_lines.append("---")
    md_lines.append(f"_Generated by db_query_monitor.py --report | {report_date}_")

    full_report = "\n".join(md_lines)

    # Print to stdout (captured by journald)
    print(full_report)

    # Post to Slack #fire-guard
    _try_slack_alert(full_report)

    # Write to file for owl-debt-reckoning consumption
    report_path = os.path.join(LOG_DIR, "db_query_offender_report.md")
    try:
        with open(report_path, "w") as f:
            f.write(full_report)
        logger.info("Report written to %s", report_path)
    except Exception as exc:
        logger.warning("Failed to write report file: %s", exc)


# ---------------------------------------------------------------------------
# Continuous monitor
# ---------------------------------------------------------------------------
def run_continuous():
    """Main loop — poll every 30 seconds."""
    logger.info(
        "Starting continuous monitor (poll=%ds, log_threshold=%dms, alert_threshold=%dms)",
        POLL_INTERVAL_SECONDS, LOG_THRESHOLD_MS, ALERT_THRESHOLD_MS,
    )

    conn = None
    consecutive_errors = 0
    max_consecutive_errors = 10

    while _running:
        try:
            conn = _ensure_connection(conn)
            rows = poll_active_queries(conn)
            consecutive_errors = 0  # reset on success

            if rows:
                logger.info("Found %d active queries over %dms threshold", len(rows), QUERY_FLOOR_MS)

            for row in rows:
                duration = row["duration_ms"]
                pid = row["pid"]

                # Always log offenders over threshold
                if duration >= LOG_THRESHOLD_MS:
                    log_offender(
                        pid, row["usename"], row["client_addr"],
                        duration, row["query_snippet"],
                    )
                    logger.info(
                        "Offender: pid=%s user=%s client=%s duration=%.1fms wait=%s/%s query=%.80s",
                        pid, row["usename"], row["client_addr"],
                        duration, row["wait_event_type"], row["wait_event"],
                        row["query_snippet"].replace("\n", " "),
                    )

                # Alert if approaching timeout
                if should_alert(duration) and _should_send_alert(pid):
                    send_alert(pid, row["usename"], duration, row["query_snippet"])

        except psycopg2.OperationalError as exc:
            consecutive_errors += 1
            logger.error(
                "DB connection error (%d/%d): %s",
                consecutive_errors, max_consecutive_errors, exc,
            )
            conn = None  # force reconnect on next iteration
            if consecutive_errors >= max_consecutive_errors:
                msg = f"DB Query Monitor: {max_consecutive_errors} consecutive connection failures. Exiting."
                logger.critical(msg)
                _try_slack_alert(f":rotating_light: {msg}")
                break
        except Exception as exc:
            consecutive_errors += 1
            logger.error("Unexpected error (%d/%d): %s", consecutive_errors, max_consecutive_errors, exc)
            if consecutive_errors >= max_consecutive_errors:
                break

        # Sleep in 1-second ticks for responsive shutdown
        for _ in range(POLL_INTERVAL_SECONDS):
            if not _running:
                break
            time.sleep(1)

    logger.info("Monitor stopped.")
    if conn:
        try:
            conn.commit()  # explicit commit before close
            conn.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Snapshot (single poll)
# ---------------------------------------------------------------------------
def snapshot():
    """Single poll — print current active queries."""
    conn = None
    try:
        conn = get_db_connection()
        rows = poll_active_queries(conn)

        if not rows:
            print("No active queries over %dms threshold." % QUERY_FLOOR_MS)
            return

        print(f"\n{'PID':>8}  {'User':<16}  {'Client':<18}  {'Duration(ms)':>12}  {'Wait':>20}  Query")
        print("-" * 110)
        for row in rows:
            wait = f"{row['wait_event_type']}/{row['wait_event']}" if row["wait_event_type"] else "-"
            snippet = row["query_snippet"].replace("\n", " ")[:60]
            print(
                f"{row['pid']:>8}  {row['usename']:<16}  {row['client_addr']:<18}"
                f"  {row['duration_ms']:>12.1f}  {wait:>20}  {snippet}"
            )
        print(f"\nTotal: {len(rows)} active queries over {QUERY_FLOOR_MS}ms")

    finally:
        if conn:
            try:
                conn.commit()  # explicit commit before close
                conn.close()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if "--report" in sys.argv:
        generate_weekly_report()
    elif "--snapshot" in sys.argv:
        snapshot()
    else:
        run_continuous()

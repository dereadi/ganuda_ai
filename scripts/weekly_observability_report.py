#!/usr/bin/env python3
"""
Weekly Actionable Observability Report — BSM Leg 3
Cherokee AI Federation

Aggregates ALL observability data into a single weekly markdown report.
Partner's BSM principle: "Reports that drove decisions."

Sections:
  1. Event Summary (uptime, incidents, fire-guard alerts)
  2. Performance Summary (p50/p95/p99 latency from api_audit_log)
  3. DB Health (rollback rate, top offenders, connection utilization)
  4. Memory Health (RSS per service, growth trends)
  5. Consultation Ring (exposure log stats)
  6. Recommendations (auto-generated from thresholds)

Data sources:
  - zammad_production.api_audit_log (timing_breakdown JSONB)
  - triad_federation.consultation_exposure_log
  - pg_stat_database, pg_stat_activity
  - /ganuda/state/rss_history.csv
  - /ganuda/logs/db_query_offenders.csv
  - systemd journal (fire-guard alerts)

Usage:
  python3 weekly_observability_report.py              # This week's report
  python3 weekly_observability_report.py --weeks 4    # Last 4 weeks trend

Output:
  - stdout (journald capture)
  - /ganuda/logs/weekly_observability_report.md
  - Slack #saturday-morning (or #fire-guard fallback)

Timer: Wed 04:50 (after db-query-report at 04:45, before owl at 05:00)
"""

import argparse
import csv
import json
import logging
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve GANUDA_ROOT and wire up lib imports
# ---------------------------------------------------------------------------
if sys.platform == "darwin":
    _GANUDA_ROOT = "/Users/Shared/ganuda"
else:
    _GANUDA_ROOT = "/ganuda"

sys.path.insert(0, _GANUDA_ROOT)

import psycopg2
import psycopg2.extras
from lib.secrets_loader import get_db_config, get_secret

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
        logging.FileHandler(os.path.join(LOG_DIR, "weekly_observability_report.log")),
    ],
)
logger = logging.getLogger("ganuda.weekly_observability_report")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
RSS_HISTORY_CSV = os.path.join(_GANUDA_ROOT, "state", "rss_history.csv")
OFFENDER_CSV = os.path.join(LOG_DIR, "db_query_offenders.csv")
REPORT_OUTPUT = os.path.join(LOG_DIR, "weekly_observability_report.md")

# ---------------------------------------------------------------------------
# Thresholds (auto-recommendation triggers)
# ---------------------------------------------------------------------------
ROLLBACK_RATE_THRESHOLD_PCT = 5.0
P95_DEGRADATION_THRESHOLD_PCT = 15.0
RSS_GROWTH_THRESHOLD_PCT = 20.0
UPTIME_THRESHOLD_PCT = 99.0


# ---------------------------------------------------------------------------
# Slack (best-effort)
# ---------------------------------------------------------------------------
def _try_slack(message: str) -> bool:
    """Post to Slack. Try #saturday-morning first, fall back to #fire-guard."""
    try:
        from lib.slack_federation import send
        if send("saturday-morning", message):
            return True
        return send("fire-guard", message)
    except Exception as exc:
        logger.warning("Slack post failed (non-fatal): %s", exc)
        return False


# ---------------------------------------------------------------------------
# DB connections
# ---------------------------------------------------------------------------
def _get_zammad_conn():
    """Connect to zammad_production (api_audit_log lives here)."""
    db_cfg = get_db_config(prefix="CHEROKEE")
    conn = psycopg2.connect(
        host=db_cfg["host"],
        port=db_cfg["port"],
        dbname=db_cfg["dbname"],
        user=db_cfg["user"],
        password=db_cfg["password"],
        connect_timeout=10,
        options="-c statement_timeout=30000",
    )
    return conn


def _get_triad_conn():
    """Connect to triad_federation (consultation_exposure_log lives here)."""
    db_cfg = get_db_config(prefix="CHEROKEE")
    conn = psycopg2.connect(
        host=db_cfg["host"],
        port=db_cfg["port"],
        dbname="triad_federation",
        user=db_cfg["user"],
        password=db_cfg["password"],
        connect_timeout=10,
        options="-c statement_timeout=30000",
    )
    return conn


def _safe_close(conn):
    """conn.commit() before conn.close() — CRITICAL."""
    if conn:
        try:
            conn.commit()
            conn.close()
        except Exception:
            pass


# ===================================================================
# SECTION 1: Event Summary
# ===================================================================
def _section_event_summary(cutoff: datetime, now: datetime) -> tuple:
    """
    Returns (markdown_lines: list[str], recommendations: list[str]).

    Sources:
      - systemd journal for fire-guard alert count
      - Service uptime from systemd (best-effort)
    """
    lines = ["## 1. Event Summary", ""]
    recs = []

    # --- Fire-guard alert count from journald ---
    alert_count = 0
    try:
        cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")
        result = subprocess.run(
            [
                "journalctl", "-u", "fire-guard.service",
                "--since", cutoff_str,
                "--no-pager", "-q", "--output", "cat",
            ],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if "ALERT" in line or "DOWN" in line or "FAIL" in line:
                    alert_count += 1
    except Exception as exc:
        logger.warning("journalctl query failed: %s", exc)

    lines.append(f"- **Fire-guard alerts this period**: {alert_count}")

    # --- Service uptime from systemd ---
    services = [
        "llm-gateway.service",
        "fire-guard.timer",
        "consultation-ring.service",
        "db-query-monitor.service",
        "ganudabot.service",
    ]
    lines.append("")
    lines.append("### Service Status")
    lines.append("")
    lines.append("| Service | Active | Since |")
    lines.append("|---------|--------|-------|")

    for svc in services:
        try:
            result = subprocess.run(
                ["systemctl", "show", svc, "--property=ActiveState,StateChangeTimestamp"],
                capture_output=True, text=True, timeout=5,
            )
            props = {}
            for prop_line in result.stdout.strip().splitlines():
                if "=" in prop_line:
                    k, _, v = prop_line.partition("=")
                    props[k.strip()] = v.strip()

            active = props.get("ActiveState", "unknown")
            since = props.get("StateChangeTimestamp", "unknown")
            status_icon = "OK" if active in ("active", "activating") else "DOWN"
            lines.append(f"| {svc} | {status_icon} ({active}) | {since} |")

            if active not in ("active", "activating", "waiting"):
                recs.append(f"Service `{svc}` is {active} — review fire-guard alerts for root cause")
        except Exception:
            lines.append(f"| {svc} | ? | query failed |")

    lines.append("")
    return lines, recs


# ===================================================================
# SECTION 2: Performance Summary
# ===================================================================
def _section_performance(cutoff: datetime, prev_cutoff: datetime, now: datetime) -> tuple:
    """
    Query api_audit_log for latency percentiles and top slowest requests.

    Returns (markdown_lines, recommendations).
    """
    lines = ["## 2. Performance Summary", ""]
    recs = []
    conn = None

    try:
        conn = _get_zammad_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # --- Percentiles this week ---
        cur.execute("""
            SELECT
                COUNT(*) AS total_requests,
                PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY response_time_ms) AS p50,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) AS p95,
                PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY response_time_ms) AS p99,
                AVG(response_time_ms) AS avg_ms,
                MAX(response_time_ms) AS max_ms
            FROM api_audit_log
            WHERE created_at >= %s AND created_at < %s
        """, (cutoff, now))
        this_week = cur.fetchone()

        # --- Percentiles previous week (for trend) ---
        cur.execute("""
            SELECT
                COUNT(*) AS total_requests,
                PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY response_time_ms) AS p50,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) AS p95,
                PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY response_time_ms) AS p99
            FROM api_audit_log
            WHERE created_at >= %s AND created_at < %s
        """, (prev_cutoff, cutoff))
        last_week = cur.fetchone()

        if this_week and this_week["total_requests"] and this_week["total_requests"] > 0:
            lines.append("### Latency Percentiles")
            lines.append("")
            lines.append("| Metric | This Week | Last Week | Trend |")
            lines.append("|--------|-----------|-----------|-------|")

            for metric in ["p50", "p95", "p99"]:
                tw_val = round(float(this_week[metric] or 0), 1)
                lw_val = round(float(last_week[metric] or 0), 1) if last_week and last_week["total_requests"] else 0

                if lw_val > 0:
                    change_pct = ((tw_val - lw_val) / lw_val) * 100
                    if change_pct > 5:
                        trend = f"DEGRADED (+{change_pct:.1f}%)"
                    elif change_pct < -5:
                        trend = f"IMPROVED ({change_pct:.1f}%)"
                    else:
                        trend = "STABLE"
                else:
                    trend = "N/A (no prior data)"
                    change_pct = 0

                lines.append(f"| {metric.upper()} | {tw_val}ms | {lw_val}ms | {trend} |")

                if metric == "p95" and change_pct > P95_DEGRADATION_THRESHOLD_PCT:
                    recs.append(
                        f"p95 latency degraded {change_pct:.1f}% week-over-week "
                        f"({lw_val}ms -> {tw_val}ms) — check model loading or inference bottleneck"
                    )

            lines.append("")
            lines.append(
                f"**Total requests**: {this_week['total_requests']} | "
                f"**Avg**: {round(float(this_week['avg_ms'] or 0), 1)}ms | "
                f"**Max**: {round(float(this_week['max_ms'] or 0), 1)}ms"
            )
            lines.append("")
        else:
            lines.append("_No API requests recorded this period._")
            lines.append("")

        # --- Top 10 slowest requests ---
        cur.execute("""
            SELECT
                created_at,
                endpoint,
                method,
                status_code,
                response_time_ms,
                key_id,
                timing_breakdown
            FROM api_audit_log
            WHERE created_at >= %s AND created_at < %s
            ORDER BY response_time_ms DESC
            LIMIT 10
        """, (cutoff, now))
        slowest = cur.fetchall()

        if slowest:
            lines.append("### Top 10 Slowest Requests")
            lines.append("")
            lines.append("| # | Timestamp | Endpoint | Status | Latency(ms) | Key | Breakdown |")
            lines.append("|---|-----------|----------|--------|-------------|-----|-----------|")

            for i, row in enumerate(slowest, 1):
                ts = row["created_at"].strftime("%m-%d %H:%M") if row["created_at"] else "?"
                breakdown = ""
                if row["timing_breakdown"]:
                    tb = row["timing_breakdown"]
                    if isinstance(tb, str):
                        try:
                            tb = json.loads(tb)
                        except (json.JSONDecodeError, TypeError):
                            tb = {}
                    parts = []
                    for k, v in (tb or {}).items():
                        if isinstance(v, (int, float)):
                            parts.append(f"{k}={v:.0f}ms")
                    breakdown = ", ".join(parts[:3])  # top 3 breakdown fields

                lines.append(
                    f"| {i} | {ts} | {row['endpoint'] or '?'} | {row['status_code']} "
                    f"| {row['response_time_ms']} | {(row['key_id'] or '?')[:8]}... | {breakdown} |"
                )

            lines.append("")

        cur.close()
    except Exception as exc:
        logger.error("Performance section failed: %s", exc)
        lines.append(f"_Query failed: {exc}_")
        lines.append("")
    finally:
        _safe_close(conn)

    return lines, recs


# ===================================================================
# SECTION 3: DB Health
# ===================================================================
def _section_db_health() -> tuple:
    """
    Rollback rate, top query offenders, connection utilization.

    Returns (markdown_lines, recommendations).
    """
    lines = ["## 3. DB Health", ""]
    recs = []
    conn = None

    try:
        conn = _get_zammad_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # --- pg_stat_database rollback rate ---
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
                   deadlocks
              FROM pg_stat_database
             WHERE datname NOT LIKE 'template%%'
               AND datname IS NOT NULL
             ORDER BY (xact_commit + xact_rollback) DESC
        """)
        db_rows = cur.fetchall()

        if db_rows:
            lines.append("### Rollback Rate & Cache Health")
            lines.append("")
            lines.append("| Database | Commits | Rollbacks | Rollback% | Cache Hit% | Deadlocks |")
            lines.append("|----------|---------|-----------|-----------|------------|-----------|")

            for r in db_rows:
                lines.append(
                    f"| {r['datname']} | {r['xact_commit']} | {r['xact_rollback']} "
                    f"| {r['rollback_pct']}% | {r['cache_hit_pct']}% | {r['deadlocks']} |"
                )
                if float(r["rollback_pct"]) > ROLLBACK_RATE_THRESHOLD_PCT:
                    recs.append(
                        f"Rollback rate for `{r['datname']}` is {r['rollback_pct']}% "
                        f"(>{ROLLBACK_RATE_THRESHOLD_PCT}%) — investigate remaining psycopg2 patterns"
                    )
            lines.append("")

        # --- Connection utilization ---
        cur.execute("""
            SELECT
                COUNT(*) AS total_connections,
                COUNT(*) FILTER (WHERE state = 'active') AS active,
                COUNT(*) FILTER (WHERE state = 'idle') AS idle,
                COUNT(*) FILTER (WHERE state = 'idle in transaction') AS idle_in_txn,
                (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') AS max_conn
            FROM pg_stat_activity
        """)
        conn_row = cur.fetchone()

        if conn_row:
            total = conn_row["total_connections"]
            max_c = conn_row["max_conn"] or 100
            util_pct = round(100.0 * total / max_c, 1)

            lines.append("### Connection Utilization")
            lines.append("")
            lines.append(f"| Total | Active | Idle | Idle-in-Txn | Max | Utilization |")
            lines.append(f"|-------|--------|------|-------------|-----|-------------|")
            lines.append(
                f"| {total} | {conn_row['active']} | {conn_row['idle']} "
                f"| {conn_row['idle_in_txn']} | {max_c} | {util_pct}% |"
            )
            lines.append("")

        # --- Top query offenders from CSV (reuse db_query_monitor data) ---
        if os.path.exists(OFFENDER_CSV):
            cutoff = datetime.utcnow() - timedelta(days=7)
            offenders = defaultdict(lambda: {"count": 0, "total_ms": 0.0, "max_ms": 0.0})

            try:
                with open(OFFENDER_CSV, "r", newline="") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            ts = datetime.fromisoformat(row["timestamp"])
                            if ts < cutoff:
                                continue
                            duration = float(row["duration_ms"])
                            pattern = row["query_snippet"][:80].strip()
                            entry = offenders[pattern]
                            entry["count"] += 1
                            entry["total_ms"] += duration
                            entry["max_ms"] = max(entry["max_ms"], duration)
                        except (ValueError, KeyError):
                            continue

                if offenders:
                    ranked = sorted(offenders.items(), key=lambda x: x[1]["total_ms"], reverse=True)[:10]
                    lines.append("### Top Query Offenders (last 7 days)")
                    lines.append("")
                    lines.append("| # | Count | Avg(ms) | Max(ms) | Query Pattern |")
                    lines.append("|---|-------|---------|---------|---------------|")
                    for i, (pattern, stats) in enumerate(ranked, 1):
                        avg = stats["total_ms"] / stats["count"]
                        snippet = pattern[:60].replace("|", "/")
                        lines.append(f"| {i} | {stats['count']} | {avg:.0f} | {stats['max_ms']:.0f} | `{snippet}` |")
                    lines.append("")
            except Exception as exc:
                logger.warning("CSV offender parse failed: %s", exc)

        cur.close()
    except Exception as exc:
        logger.error("DB Health section failed: %s", exc)
        lines.append(f"_Query failed: {exc}_")
        lines.append("")
    finally:
        _safe_close(conn)

    return lines, recs


# ===================================================================
# SECTION 4: Memory Health
# ===================================================================
def _section_memory_health(cutoff: datetime) -> tuple:
    """
    RSS per service from rss_history.csv, growth trends.

    Returns (markdown_lines, recommendations).
    """
    lines = ["## 4. Memory Health (RSS)", ""]
    recs = []

    if not os.path.exists(RSS_HISTORY_CSV):
        lines.append("_No RSS history data yet (first run)._")
        lines.append("")
        return lines, recs

    # Parse CSV: timestamp,service_name,pid,rss_kb
    service_data = defaultdict(list)  # service -> [(timestamp, rss_kb)]

    try:
        with open(RSS_HISTORY_CSV, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    ts = datetime.fromisoformat(row["timestamp"])
                    if ts < cutoff:
                        continue
                    rss = int(row["rss_kb"])
                    svc = row["service_name"]
                    service_data[svc].append((ts, rss))
                except (ValueError, KeyError):
                    continue
    except Exception as exc:
        logger.warning("RSS CSV parse failed: %s", exc)
        lines.append(f"_CSV parse error: {exc}_")
        lines.append("")
        return lines, recs

    if not service_data:
        lines.append("_No RSS data for this period._")
        lines.append("")
        return lines, recs

    lines.append("| Service | Current RSS (MB) | Min RSS (MB) | Max RSS (MB) | Growth% | Samples |")
    lines.append("|---------|-----------------|--------------|--------------|---------|---------|")

    for svc in sorted(service_data.keys()):
        points = sorted(service_data[svc], key=lambda x: x[0])
        if not points:
            continue

        rss_values = [p[1] for p in points]
        current_mb = round(rss_values[-1] / 1024, 1)
        min_mb = round(min(rss_values) / 1024, 1)
        max_mb = round(max(rss_values) / 1024, 1)

        # Growth: compare first 10% of samples to last 10%
        n = len(rss_values)
        if n >= 4:
            early_window = max(1, n // 10)
            early_avg = sum(rss_values[:early_window]) / early_window
            late_avg = sum(rss_values[-early_window:]) / early_window
            if early_avg > 0:
                growth_pct = round(((late_avg - early_avg) / early_avg) * 100, 1)
            else:
                growth_pct = 0.0
        else:
            growth_pct = 0.0

        growth_flag = f" **!**" if abs(growth_pct) >= RSS_GROWTH_THRESHOLD_PCT else ""
        lines.append(
            f"| {svc} | {current_mb} | {min_mb} | {max_mb} "
            f"| {growth_pct}%{growth_flag} | {n} |"
        )

        if growth_pct >= RSS_GROWTH_THRESHOLD_PCT:
            recs.append(
                f"RSS growth for `{svc}` is {growth_pct}% — memory leak investigation needed"
            )

    lines.append("")
    return lines, recs


# ===================================================================
# SECTION 5: Consultation Ring
# ===================================================================
def _section_consultation_ring(cutoff: datetime, now: datetime) -> tuple:
    """
    Consultation stats from triad_federation.consultation_exposure_log.

    Returns (markdown_lines, recommendations).
    """
    lines = ["## 5. Consultation Ring", ""]
    recs = []
    conn = None

    try:
        conn = _get_triad_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Check if the table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'consultation_exposure_log'
            )
        """)
        exists = cur.fetchone()["exists"]

        if not exists:
            lines.append("_consultation_exposure_log table not found — ring not yet deployed._")
            lines.append("")
            cur.close()
            return lines, recs

        # --- Total consultations this period ---
        cur.execute("""
            SELECT
                COUNT(*) AS total_claims,
                COUNT(DISTINCT consultation_id) AS total_consultations,
                COUNT(DISTINCT provider) AS provider_count
            FROM consultation_exposure_log
            WHERE timestamp >= %s AND timestamp < %s
        """, (cutoff, now))
        summary = cur.fetchone()

        if summary and summary["total_consultations"] and summary["total_consultations"] > 0:
            lines.append(
                f"- **Consultations this period**: {summary['total_consultations']}\n"
                f"- **Total claims exposed**: {summary['total_claims']}\n"
                f"- **Providers consulted**: {summary['provider_count']}"
            )
            lines.append("")

            # --- Provider distribution ---
            cur.execute("""
                SELECT
                    provider,
                    COUNT(*) AS claim_count,
                    COUNT(DISTINCT consultation_id) AS consultations,
                    ROUND(AVG(sensitivity_score)::numeric, 2) AS avg_sensitivity
                FROM consultation_exposure_log
                WHERE timestamp >= %s AND timestamp < %s
                GROUP BY provider
                ORDER BY claim_count DESC
            """, (cutoff, now))
            providers = cur.fetchall()

            if providers:
                lines.append("### Provider Distribution")
                lines.append("")
                lines.append("| Provider | Consultations | Claims | Avg Sensitivity |")
                lines.append("|----------|---------------|--------|-----------------|")
                for p in providers:
                    lines.append(
                        f"| {p['provider']} | {p['consultations']} "
                        f"| {p['claim_count']} | {p['avg_sensitivity']} |"
                    )
                lines.append("")

            # --- Valence gate reject count (ip_classification = 'BLOCKED') ---
            cur.execute("""
                SELECT COUNT(*) AS blocked
                FROM consultation_exposure_log
                WHERE timestamp >= %s AND timestamp < %s
                  AND ip_classification = 'BLOCKED'
            """, (cutoff, now))
            blocked = cur.fetchone()
            if blocked and blocked["blocked"] > 0:
                lines.append(f"- **Valence gate rejects**: {blocked['blocked']}")
                lines.append("")
        else:
            lines.append("_No consultations recorded this period._")
            lines.append("")

        cur.close()
    except Exception as exc:
        logger.warning("Consultation ring section failed (non-fatal): %s", exc)
        lines.append(f"_Query failed: {exc}_")
        lines.append("")
    finally:
        _safe_close(conn)

    return lines, recs


# ===================================================================
# SECTION 6: Recommendations
# ===================================================================
def _section_recommendations(all_recs: list) -> list:
    """Format auto-generated recommendations."""
    lines = ["## 6. Recommendations", ""]

    if not all_recs:
        lines.append("No actionable recommendations this period. All metrics within thresholds.")
    else:
        for i, rec in enumerate(all_recs, 1):
            lines.append(f"{i}. {rec}")

    lines.append("")
    return lines


# ===================================================================
# Main report generator
# ===================================================================
def generate_report(weeks: int = 1):
    """
    Generate the full weekly observability report.

    Args:
        weeks: Number of weeks to cover (1 = this week only, 4 = last 4 weeks).
    """
    now = datetime.utcnow()
    cutoff = now - timedelta(weeks=weeks)
    prev_cutoff = cutoff - timedelta(weeks=weeks)  # previous equivalent period for trend

    report_date = now.strftime("%Y-%m-%d %H:%M UTC")
    period_label = f"{cutoff.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}"

    md_lines = [
        f"# Weekly Observability Report",
        f"_Generated: {report_date}_",
        f"_Period: {period_label} ({weeks} week{'s' if weeks > 1 else ''})_",
        "",
        "---",
        "",
    ]

    all_recs = []

    # Section 1: Event Summary
    logger.info("Generating Section 1: Event Summary...")
    s1_lines, s1_recs = _section_event_summary(cutoff, now)
    md_lines.extend(s1_lines)
    all_recs.extend(s1_recs)

    # Section 2: Performance Summary
    logger.info("Generating Section 2: Performance Summary...")
    s2_lines, s2_recs = _section_performance(cutoff, prev_cutoff, now)
    md_lines.extend(s2_lines)
    all_recs.extend(s2_recs)

    # Section 3: DB Health
    logger.info("Generating Section 3: DB Health...")
    s3_lines, s3_recs = _section_db_health()
    md_lines.extend(s3_lines)
    all_recs.extend(s3_recs)

    # Section 4: Memory Health
    logger.info("Generating Section 4: Memory Health...")
    s4_lines, s4_recs = _section_memory_health(cutoff)
    md_lines.extend(s4_lines)
    all_recs.extend(s4_recs)

    # Section 5: Consultation Ring
    logger.info("Generating Section 5: Consultation Ring...")
    s5_lines, s5_recs = _section_consultation_ring(cutoff, now)
    md_lines.extend(s5_lines)
    all_recs.extend(s5_recs)

    # Section 6: Recommendations
    logger.info("Generating Section 6: Recommendations...")
    md_lines.extend(_section_recommendations(all_recs))

    # Footer
    md_lines.append("---")
    md_lines.append(
        f"_Generated by weekly_observability_report.py | "
        f"Cherokee AI Federation | {report_date}_"
    )

    full_report = "\n".join(md_lines)

    # --- Output ---

    # 1. stdout (journald capture)
    print(full_report)

    # 2. Write to file
    try:
        with open(REPORT_OUTPUT, "w") as f:
            f.write(full_report)
        logger.info("Report written to %s", REPORT_OUTPUT)
    except Exception as exc:
        logger.warning("Failed to write report file: %s", exc)

    # 3. Post to Slack
    _try_slack(full_report)

    logger.info("Weekly observability report complete.")


# ===================================================================
# Entry point
# ===================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Weekly Observability Report — BSM Leg 3"
    )
    parser.add_argument(
        "--weeks", type=int, default=1,
        help="Number of weeks to cover (default: 1)"
    )
    args = parser.parse_args()

    generate_report(weeks=args.weeks)

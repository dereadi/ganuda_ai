"""
Security Monitoring Daemon - AI Blue Team Phase 5

Runs on a 5-minute interval checking for security events:
- Blocked executions in audit log
- Failed login attempts
- Suspicious thermal memories
- Unknown queue entry sources
- PostgreSQL connection count anomalies

Sends alerts to Telegram via alert_manager.

Created: 2026-02-02
"""

import sys
import time
import signal
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

# Add lib to path for alert_manager
sys.path.insert(0, "/ganuda/lib")
sys.path.insert(0, "/ganuda/security/blue_team")

LOG_DIR = Path("/ganuda/logs/security")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "monitor.log"),
    ],
)
logger = logging.getLogger("security_monitor")

CHECK_INTERVAL_SECONDS = 300  # 5 minutes
PG_CONNECTION_ALERT_THRESHOLD = 50
FAILED_LOGIN_THRESHOLD = 5
FAILED_LOGIN_WINDOW_MINUTES = 10

# Graceful shutdown
_running = True


def _signal_handler(signum, frame):
    global _running
    logger.info("Received signal %d, shutting down...", signum)
    _running = False


signal.signal(signal.SIGTERM, _signal_handler)
signal.signal(signal.SIGINT, _signal_handler)


def _get_db_connection():
    """Get PostgreSQL connection."""
    import psycopg2
    return psycopg2.connect(
        dbname="cherokee",
        user="claude",
        host="localhost",
        port=5432,
    )


def _send_alert(message: str, severity: str = "warning"):
    """Send alert via Telegram alert_manager."""
    try:
        from alert_manager import send_alert
        prefix = {
            "critical": "[CRITICAL SECURITY]",
            "warning": "[SECURITY WARNING]",
            "info": "[SECURITY INFO]",
        }.get(severity, "[SECURITY]")
        send_alert(f"{prefix} {message}")
        logger.info("Alert sent: %s %s", prefix, message[:100])
    except ImportError:
        logger.warning("alert_manager not available, logging only: %s", message)
    except Exception as e:
        logger.error("Failed to send alert: %s | message: %s", e, message[:100])


def check_blocked_executions():
    """Check for new blocked entries in execution_audit_log."""
    try:
        conn = _get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT task_id, title, blocked_reason, created_at
            FROM execution_audit_log
            WHERE blocked = true
            AND created_at > NOW() - INTERVAL '6 minutes'
            ORDER BY created_at DESC
            LIMIT 10
        """)
        rows = cur.fetchall()
        conn.close()

        for row in rows:
            task_id, title, reason, created_at = row
            msg = (
                f"Execution BLOCKED\n"
                f"Task: {title[:80]}\n"
                f"Reason: {reason[:100]}\n"
                f"Time: {created_at}"
            )
            _send_alert(msg, "warning")
            logger.warning("Blocked execution: task=%s reason=%s", task_id, reason[:80])

        return len(rows)
    except Exception as e:
        logger.debug("Could not check blocked executions: %s", e)
        return 0


def check_failed_logins():
    """Check for excessive failed login attempts."""
    try:
        conn = _get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT username, COUNT(*) as fail_count, MAX(attempted_at) as last_attempt
            FROM user_sessions
            WHERE success = false
            AND attempted_at > NOW() - INTERVAL '%s minutes'
            GROUP BY username
            HAVING COUNT(*) >= %s
            ORDER BY fail_count DESC
        """, (FAILED_LOGIN_WINDOW_MINUTES, FAILED_LOGIN_THRESHOLD))
        rows = cur.fetchall()
        conn.close()

        for row in rows:
            username, fail_count, last_attempt = row
            msg = (
                f"Brute force suspected\n"
                f"User: {username}\n"
                f"Failed attempts: {fail_count} in {FAILED_LOGIN_WINDOW_MINUTES} min\n"
                f"Last attempt: {last_attempt}"
            )
            _send_alert(msg, "critical")
            logger.warning("Brute force: user=%s count=%d", username, fail_count)

        return len(rows)
    except Exception as e:
        logger.debug("Could not check failed logins: %s", e)
        return 0


def check_suspicious_thermal_memories():
    """Check for thermal memories containing injection patterns."""
    try:
        from prompt_injection_detector import detect_injection

        conn = _get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, content, source, created_at
            FROM thermal_memories
            WHERE created_at > NOW() - INTERVAL '6 minutes'
            ORDER BY created_at DESC
            LIMIT 50
        """)
        rows = cur.fetchall()
        conn.close()

        flagged = 0
        for row in rows:
            mem_id, content, source, created_at = row
            is_injection, confidence, reason = detect_injection(content)
            if is_injection:
                flagged += 1
                msg = (
                    f"Suspicious thermal memory\n"
                    f"ID: {mem_id}\n"
                    f"Source: {source}\n"
                    f"Confidence: {confidence}\n"
                    f"Reason: {reason}\n"
                    f"Preview: {content[:80]}..."
                )
                _send_alert(msg, "warning")
                logger.warning("Suspicious memory: id=%s reason=%s", mem_id, reason)

        return flagged
    except Exception as e:
        logger.debug("Could not check thermal memories: %s", e)
        return 0


def check_unknown_queue_sources():
    """Check for queue entries from unknown sources."""
    try:
        from queue_validator import KNOWN_SOURCES

        conn = _get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, title, source, created_at
            FROM jr_task_queue
            WHERE created_at > NOW() - INTERVAL '6 minutes'
            AND source IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 20
        """)
        rows = cur.fetchall()
        conn.close()

        flagged = 0
        for row in rows:
            task_id, title, source, created_at = row
            if source not in KNOWN_SOURCES:
                flagged += 1
                msg = (
                    f"Unknown queue source\n"
                    f"Task: {title[:80]}\n"
                    f"Source: {source}\n"
                    f"Time: {created_at}"
                )
                _send_alert(msg, "warning")
                logger.warning("Unknown source: task=%s source=%s", task_id, source)

        return flagged
    except Exception as e:
        logger.debug("Could not check queue sources: %s", e)
        return 0


def check_pg_connections():
    """Check PostgreSQL connection count for potential DoS."""
    try:
        conn = _get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM pg_stat_activity;")
        count = cur.fetchone()[0]
        conn.close()

        if count > PG_CONNECTION_ALERT_THRESHOLD:
            msg = (
                f"High PostgreSQL connections\n"
                f"Count: {count} (threshold: {PG_CONNECTION_ALERT_THRESHOLD})\n"
                f"Possible connection leak or DoS"
            )
            _send_alert(msg, "critical" if count > PG_CONNECTION_ALERT_THRESHOLD * 2 else "warning")
            logger.warning("High PG connections: count=%d", count)

        return count
    except Exception as e:
        logger.debug("Could not check PG connections: %s", e)
        return -1


def run_all_checks():
    """Run all security checks and return summary."""
    logger.info("Starting security check cycle")
    start = time.time()

    results = {
        "blocked_executions": check_blocked_executions(),
        "brute_force_alerts": check_failed_logins(),
        "suspicious_memories": check_suspicious_thermal_memories(),
        "unknown_sources": check_unknown_queue_sources(),
        "pg_connections": check_pg_connections(),
    }

    elapsed = time.time() - start
    logger.info(
        "Security check complete in %.2fs | blocked=%d brute=%d memories=%d sources=%d pg=%d",
        elapsed,
        results["blocked_executions"],
        results["brute_force_alerts"],
        results["suspicious_memories"],
        results["unknown_sources"],
        results["pg_connections"],
    )
    return results


def main():
    """Main daemon loop."""
    logger.info("Security Monitor Daemon starting (interval=%ds)", CHECK_INTERVAL_SECONDS)
    _send_alert("Security Monitor Daemon started", "info")

    while _running:
        try:
            run_all_checks()
        except Exception as e:
            logger.error("Error in check cycle: %s", e, exc_info=True)

        # Sleep in 1-second increments for responsive shutdown
        for _ in range(CHECK_INTERVAL_SECONDS):
            if not _running:
                break
            time.sleep(1)

    logger.info("Security Monitor Daemon stopped")
    _send_alert("Security Monitor Daemon stopped", "info")


if __name__ == "__main__":
    main()

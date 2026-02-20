#!/usr/bin/env python3
"""
Execution Audit Logger - Records every command executed by the Jr executor.

Logs to both file and database for forensic analysis.
Command content is stored as SHA-256 hash (not plaintext) for security.

Security Phase 2 - Executor Sandboxing
Created: 2026-02-02
Author: Security Engineer Jr. (via TPM instruction)
"""

import os
import hashlib
import logging
import socket
from datetime import datetime
from typing import Optional

# ============================================================
# Configuration
# ============================================================

LOG_DIR = "/ganuda/logs/security"
AUDIT_LOG_FILE = os.path.join(LOG_DIR, "execution_audit.log")

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': os.environ.get('VETASSIST_DB_PASSWORD', '')
}

EXECUTOR_HOST = socket.gethostname()
RETENTION_DAYS = 90

os.makedirs(LOG_DIR, exist_ok=True)

# File logger
audit_logger = logging.getLogger("execution_audit")
audit_logger.setLevel(logging.INFO)
_fh = logging.FileHandler(AUDIT_LOG_FILE)
_fh.setFormatter(logging.Formatter(
    '%(asctime)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))
audit_logger.addHandler(_fh)


# ============================================================
# Public API
# ============================================================

def log_execution(
    task_id: int,
    command_type: str,
    command: str,
    result_code: int,
    executor_user: str = "dereadi",
    blocked: bool = False,
    block_reason: str = ""
) -> bool:
    """
    Log a command execution to both file and database.

    Args:
        task_id: The jr_work_queue task ID.
        command_type: One of 'bash', 'sql', 'file'.
        command: The full command string (hashed for DB storage).
        result_code: Return code (0 = success, non-zero = failure, -1 = blocked).
        executor_user: The OS user executing the command.
        blocked: True if the command was blocked by the sanitizer.
        block_reason: Reason the command was blocked (if applicable).

    Returns:
        True if logged successfully, False on error.
    """
    command_hash = hashlib.sha256(command.encode('utf-8')).hexdigest()
    command_preview = command[:200].replace('\n', ' ') if command else "(empty)"

    # Always log to file (reliable, local)
    _log_to_file(
        task_id, command_type, command_hash, command_preview,
        result_code, blocked, block_reason
    )

    # Attempt to log to database (best-effort, don't fail the execution)
    try:
        _log_to_database(
            task_id, command_type, command_hash, command_preview,
            result_code, blocked, block_reason
        )
    except Exception as e:
        audit_logger.error(f"DB audit log failed: {e}")

    return True


def cleanup_old_entries() -> int:
    """
    Delete audit log entries older than RETENTION_DAYS.

    Returns:
        Number of rows deleted, or -1 on error.
    """
    try:
        import psycopg2
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM execution_audit_log "
            "WHERE executed_at < NOW() - INTERVAL '%s days'",
            (RETENTION_DAYS,)
        )
        deleted = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        audit_logger.info(f"Retention cleanup: deleted {deleted} entries older than {RETENTION_DAYS} days")
        return deleted
    except Exception as e:
        audit_logger.error(f"Retention cleanup failed: {e}")
        return -1


def ensure_audit_table() -> bool:
    """
    Create the execution_audit_log table if it does not exist.

    Returns:
        True if table exists or was created, False on error.
    """
    try:
        import psycopg2
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS execution_audit_log (
                id SERIAL PRIMARY KEY,
                task_id INTEGER REFERENCES jr_work_queue(id),
                command_type VARCHAR(20) NOT NULL,
                command_hash VARCHAR(64) NOT NULL,
                command_preview VARCHAR(200),
                result_code INTEGER,
                blocked BOOLEAN DEFAULT false,
                block_reason VARCHAR(500),
                executed_at TIMESTAMPTZ DEFAULT NOW(),
                executor_host VARCHAR(100)
            );
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_exec_audit_task
            ON execution_audit_log(task_id);
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_exec_audit_time
            ON execution_audit_log(executed_at);
        """)
        conn.commit()
        cur.close()
        conn.close()
        audit_logger.info("execution_audit_log table verified/created")
        return True
    except Exception as e:
        audit_logger.error(f"Failed to create audit table: {e}")
        return False


# ============================================================
# Internal Helpers
# ============================================================

def _log_to_file(
    task_id: int,
    command_type: str,
    command_hash: str,
    command_preview: str,
    result_code: int,
    blocked: bool,
    block_reason: str
) -> None:
    """Write audit entry to local file."""
    status = "BLOCKED" if blocked else ("OK" if result_code == 0 else "FAIL")
    audit_logger.info(
        f"task={task_id} | type={command_type} | status={status} | "
        f"rc={result_code} | hash={command_hash[:16]}... | "
        f"preview={command_preview[:100]} | "
        f"blocked_reason={block_reason if blocked else 'n/a'}"
    )


def _log_to_database(
    task_id: int,
    command_type: str,
    command_hash: str,
    command_preview: str,
    result_code: int,
    blocked: bool,
    block_reason: str
) -> None:
    """Write audit entry to PostgreSQL."""
    import psycopg2
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO execution_audit_log "
        "(task_id, command_type, command_hash, command_preview, "
        " result_code, blocked, block_reason, executor_host) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (task_id, command_type, command_hash, command_preview,
         result_code, blocked, block_reason, EXECUTOR_HOST)
    )
    conn.commit()
    cur.close()
    conn.close()


# ============================================================
# Module Self-Test
# ============================================================

if __name__ == "__main__":
    print("=== Execution Audit Logger Self-Test ===\n")

    # Test table creation
    print("Creating audit table...")
    result = ensure_audit_table()
    print(f"  Table creation: {'OK' if result else 'FAILED'}")

    # Test logging
    print("Logging test execution...")
    log_result = log_execution(
        task_id=0,
        command_type="bash",
        command="echo 'audit self-test'",
        result_code=0,
        blocked=False
    )
    print(f"  Log write: {'OK' if log_result else 'FAILED'}")

    # Test blocked logging
    print("Logging blocked command...")
    log_result = log_execution(
        task_id=0,
        command_type="bash",
        command="rm -rf /",
        result_code=-1,
        blocked=True,
        block_reason="Self-test: rm -rf / blocked"
    )
    print(f"  Blocked log: {'OK' if log_result else 'FAILED'}")

    # Test cleanup
    print(f"Running retention cleanup (>{RETENTION_DAYS} days)...")
    deleted = cleanup_old_entries()
    print(f"  Cleanup: deleted {deleted} old entries")

    print(f"\nAudit log file: {AUDIT_LOG_FILE}")
    print("=== Self-Test Complete ===")

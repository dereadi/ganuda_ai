"""DC-16 database connection helpers — three metabolic databases.

During migration: new helpers point to cherokee_identity/ops/telemetry.
Legacy get_db() still points to zammad_production.
Both work simultaneously. No daemon breaks.

Council Vote: cf4ac0aeddc7eb75 (DC-16 Longhouse, 0.858)
"""
import os
import re
import psycopg2


def _load_secrets():
    """Load secrets.env if env vars not already set."""
    if os.environ.get("CHEROKEE_DB_PASS"):
        return
    try:
        with open("/ganuda/config/secrets.env") as f:
            for line in f:
                m = re.match(r"^(\w+)=(.+)$", line.strip())
                if m:
                    os.environ.setdefault(m.group(1), m.group(2))
    except FileNotFoundError:
        pass


def _connect(db_name_env, db_name_default, host_env=None, host_default="10.100.0.2"):
    """Internal: create a connection to a specific database.
    Default host uses WireGuard IP (10.100.0.2) — more reliable than LAN.
    """
    _load_secrets()
    host = os.environ.get(host_env, host_default) if host_env else host_default
    return psycopg2.connect(
        host=host,
        port=5432,
        dbname=os.environ.get(db_name_env, db_name_default),
        user=os.environ.get("CHEROKEE_DB_USER", "claude"),
        password=os.environ.get("CHEROKEE_DB_PASS", ""),
        connect_timeout=10,
    )


def get_identity_db():
    """Connect to cherokee_identity — thermals, council, sacred patterns."""
    return _connect("CHEROKEE_IDENTITY_DB", "cherokee_identity",
                     "CHEROKEE_IDENTITY_HOST")


def get_ops_db():
    """Connect to cherokee_ops — jr_work_queue, heartbeats, task pipeline."""
    return _connect("CHEROKEE_OPS_DB", "cherokee_ops",
                     "CHEROKEE_OPS_HOST")


def get_telemetry_db():
    """Connect to cherokee_telemetry — timeline, fedattn, health checks, IoT."""
    return _connect("CHEROKEE_TELEMETRY_DB", "cherokee_telemetry",
                     "CHEROKEE_TELEMETRY_HOST")


def get_db():
    """Legacy: connect to zammad_production. Use specific helpers for new code."""
    return _connect("CHEROKEE_DB_NAME", "zammad_production",
                     "CHEROKEE_DB_HOST")

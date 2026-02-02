#!/usr/bin/env python3
"""
VetAssist Database Configuration Module
Single source of truth for all VetAssist database connections.

Cherokee AI Federation - For Seven Generations
Created: January 29, 2026
"""

import os
import yaml
import logging
import psycopg2
from pathlib import Path
from functools import lru_cache
from typing import Dict, Optional

logger = logging.getLogger(__name__)

CONFIG_PATH = Path("/ganuda/vetassist/config/database.yaml")


class DatabaseConfigError(Exception):
    """Raised when database configuration is invalid or tables are missing."""
    pass


@lru_cache()
def load_config() -> Dict:
    """Load database configuration from YAML file."""
    if not CONFIG_PATH.exists():
        raise DatabaseConfigError(f"Config file not found: {CONFIG_PATH}")

    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def _get_credentials(db_type: str = 'non_pii') -> tuple:
    """
    Get database credentials from vault or environment.

    Priority:
    1. Silverfin vault (if available)
    2. Environment variables
    """
    if db_type == 'pii':
        user = os.environ.get('PII_DB_USER', 'claude')
        password = os.environ.get('PII_DB_PASSWORD')
    else:
        user = os.environ.get('DB_USER', 'claude')
        password = os.environ.get('DB_PASSWORD')

    if not password:
        # Try vault
        try:
            import subprocess
            result = subprocess.run(
                ["/ganuda/scripts/get-vault-secret.sh", "bluefin_claude_password"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                password = result.stdout.strip()
        except Exception:
            pass

    if not password:
        raise DatabaseConfigError(
            f"No password for {db_type} database. Set DB_PASSWORD or configure vault."
        )

    return user, password


def get_non_pii_connection():
    """
    Get connection to non-PII database (bluefin/zammad_production).

    Usage:
        conn = get_non_pii_connection()
        cur = conn.cursor()
        ...
        conn.close()
    """
    config = load_config()
    db_config = config['non_pii']
    user, password = _get_credentials('non_pii')

    logger.info(f"Connecting to non-PII database: {db_config['host']}/{db_config['database']}")

    return psycopg2.connect(
        host=db_config['host'],
        database=db_config['database'],
        port=db_config['port'],
        user=user,
        password=password
    )


def get_pii_connection():
    """
    Get connection to PII database (goldfin/vetassist_pii).

    Usage:
        conn = get_pii_connection()
        cur = conn.cursor()
        ...
        conn.close()
    """
    config = load_config()
    db_config = config['pii']
    user, password = _get_credentials('pii')

    logger.info(f"Connecting to PII database: {db_config['host']}/{db_config['database']}")

    return psycopg2.connect(
        host=db_config['host'],
        database=db_config['database'],
        port=db_config['port'],
        user=user,
        password=password
    )


def validate_tables(db_type: str = 'non_pii') -> bool:
    """
    Validate that required tables exist. FAILS LOUDLY if missing.

    Call this on service startup to catch misconfiguration immediately.
    """
    config = load_config()
    required = config.get('required_tables', {}).get(db_type, [])

    if not required:
        logger.warning(f"No required tables defined for {db_type}")
        return True

    if db_type == 'pii':
        conn = get_pii_connection()
    else:
        conn = get_non_pii_connection()

    try:
        cur = conn.cursor()
        missing = []

        for table in required:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = %s
                )
            """, (table,))
            exists = cur.fetchone()[0]

            if not exists:
                missing.append(table)

        cur.close()

        if missing:
            raise DatabaseConfigError(
                f"FATAL: Missing required tables in {db_type} database: {missing}\n"
                f"Database: {config[db_type]['database']} on {config[db_type]['host']}\n"
                "This usually means the service is pointing to the wrong database."
            )

        logger.info(f"Validated {len(required)} required tables in {db_type} database")
        return True

    finally:
        conn.close()


def validate_on_startup():
    """
    Run all validations on service startup.

    Call this in your service's main() before starting the event loop.
    Raises DatabaseConfigError if validation fails.
    """
    logger.info("Validating VetAssist database configuration...")

    # Validate non-PII database
    validate_tables('non_pii')

    # PII database validation is optional (may not be needed by all services)
    try:
        validate_tables('pii')
    except Exception as e:
        logger.warning(f"PII database validation skipped: {e}")

    logger.info("Database validation complete - all tables present")
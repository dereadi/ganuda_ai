"""
ganuda_db: Core Database Library
Cherokee AI Federation - For the Seven Generations

Consolidated database utilities for the federation.
All services should import from here instead of duplicating connection logic.

Usage:
    from ganuda_db import get_connection, execute_query, DB_CONFIG
    from ganuda_db import get_db_config, get_dict_cursor
"""

import os
import logging
import psycopg2
import psycopg2.extras

__version__ = "1.3.0"

logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host": "192.168.132.222",
    "dbname": "zammad_production",
    "user": "claude",
}


def get_db_config() -> dict:
    """
    Return database connection config with password via secrets_loader.

    Uses the three-tier resolution chain:
      1. /ganuda/config/secrets.env (file)
      2. CHEROKEE_DB_PASS environment variable
      3. FreeIPA vault

    Returns a dict suitable for passing to psycopg2.connect(**config).

    Raises:
        RuntimeError: If password cannot be resolved from any source.
    """
    try:
        from secrets_loader import get_secret
        password = get_secret("CHEROKEE_DB_PASS")
    except ImportError:
        # Fallback: secrets_loader not on path (e.g., standalone scripts)
        password = os.environ.get("CHEROKEE_DB_PASS")
        if password:
            logger.debug("ganuda_db: CHEROKEE_DB_PASS from env (secrets_loader not available)")
    if not password:
        raise ValueError(
            "CHEROKEE_DB_PASS not resolved. Check /ganuda/config/secrets.env, "
            "environment variables, or vault configuration."
        )
    config = dict(DB_CONFIG)
    config["password"] = password
    return config


def link_thermal_entity(thermal_id: int, entity_type: str, entity_id: str,
                        link_type: str = "references", created_by: str = "system") -> bool:
    """
    Create a cross-domain link between a thermal memory and another entity.
    Idempotent — skips if link already exists.
    Returns True if link was created, False if it already existed.

    Entity types: council_vote, jr_task, kanban_ticket, specification, code_commit, thermal, observation
    Link types: references, caused_by, produced, resolved, blocked_by, supersedes, validates
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO thermal_entity_links (thermal_id, entity_type, entity_id, link_type, created_by)
            SELECT %s, %s, %s, %s, %s
            WHERE NOT EXISTS (
                SELECT 1 FROM thermal_entity_links
                WHERE thermal_id = %s AND entity_type = %s AND entity_id = %s
            )
        """, (thermal_id, entity_type, entity_id, link_type, created_by,
              thermal_id, entity_type, entity_id))
        created = cur.rowcount > 0
        conn.commit()
        conn.close()
        return created
    except Exception as e:
        logger.error(f"link_thermal_entity failed: {e}")
        return False


def get_connection(retries: int = 3):
    """
    Create and return a new psycopg2 connection using get_db_config().

    Retries on transient failures (SSL drops, connection resets).
    Caller is responsible for closing the connection.

    Args:
        retries: Number of connection attempts (default 3).

    Returns:
        psycopg2.extensions.connection
    """
    import time
    config = get_db_config()
    last_err = None
    for attempt in range(retries):
        try:
            return psycopg2.connect(**config)
        except psycopg2.OperationalError as e:
            last_err = e
            if attempt < retries - 1:
                wait = 0.5 * (2 ** attempt)
                logger.warning("ganuda_db: connection attempt %d failed (%s), retrying in %.1fs", attempt + 1, e, wait)
                time.sleep(wait)
    raise last_err


def get_dict_cursor(conn):
    """
    Return a RealDictCursor for the given connection.

    Args:
        conn: A psycopg2 connection object.

    Returns:
        psycopg2.extras.RealDictCursor
    """
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


def _gate_thermal_temp(content: str, temperature: float, source: str = "unknown") -> float:
    """
    Gate thermal temperature to prevent inflation.
    Council Vote #aacfbf5a17920766 — "When you highlight the whole book, nothing is sacred."

    Sacred-level temps (90+) only allowed from constitutional sources.
    Sycophantic content gets capped. Casual content gets capped.
    """
    content_lower = content.lower()

    # Constitutional sources can write at any temperature
    constitutional_sources = {"council", "tpm_vote", "constitutional_change",
                              "design_constraint", "longhouse", "ghigau"}
    if source in constitutional_sources:
        return temperature

    # Inflation detection: sycophantic language shouldn't be sacred
    inflation_markers = ["brilliant", "sacred", "profound", "perfect", "beautiful",
                         "extraordinary", "magnificent", "incredible", "amazing"]
    inflation_count = sum(1 for m in inflation_markers if m in content_lower)
    if inflation_count >= 2:
        return min(temperature, 50.0)

    # Casual/conversational content: cap at 50
    casual_markers = ["hello", "hi there", "good morning", "how are you", "thanks",
                      "thank you", "sounds good", "got it", "ok", "cool", "nice"]
    if any(content_lower.startswith(m) for m in casual_markers):
        return min(temperature, 50.0)

    # Non-constitutional sources capped at 85
    return min(temperature, 85.0)


def safe_thermal_write(content: str, temperature: float = 60.0,
                       source: str = "unknown", sacred: bool = False,
                       metadata: dict = None) -> bool:
    """
    Resilient thermal memory write with 3x retry + disk fallback.
    Legion adoption (QW-4, kanban #1909).
    Temperature gating added (Council Vote #aacfbf5a17920766).

    Returns True if written to DB, False if fell back to disk.
    """
    import hashlib
    import json
    import time
    from datetime import datetime

    # Apply temperature gating before write
    temperature = _gate_thermal_temp(content, temperature, source)

    memory_hash = hashlib.sha256(content.encode()).hexdigest()
    meta = metadata or {}
    meta.update({"source": source, "timestamp": datetime.now().isoformat()})

    for attempt in range(3):
        try:
            conn = get_connection()
            try:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO thermal_memory_archive
                    (original_content, temperature_score, memory_hash,
                     sacred_pattern, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (memory_hash) DO NOTHING
                """, (content, temperature, memory_hash, sacred,
                      json.dumps(meta)))
                conn.commit()
                return True
            finally:
                conn.close()
        except Exception:
            if attempt < 2:
                time.sleep(0.5 * (2 ** attempt))

    # All retries failed — disk fallback
    try:
        import os
        fallback_dir = "/ganuda/logs"
        os.makedirs(fallback_dir, exist_ok=True)
        fallback_path = os.path.join(fallback_dir, "thermal_fallback.jsonl")
        with open(fallback_path, "a") as f:
            f.write(json.dumps({
                "content": content[:2000],
                "temperature": temperature,
                "memory_hash": memory_hash,
                "sacred": sacred,
                "metadata": meta,
            }) + "\n")
    except Exception:
        pass
    return False


def execute_query(sql: str, params=None) -> list:
    """
    Convenience function: connect, execute a query, fetchall, close.

    Opens a connection, runs the query with optional params,
    fetches all results as a list of dicts, then closes the connection.

    Args:
        sql: SQL query string. Use %s placeholders for params.
        params: Optional tuple or dict of query parameters.

    Returns:
        list[dict]: Query results as a list of RealDictRow dicts.
    """
    conn = None
    try:
        conn = get_connection()
        cur = get_dict_cursor(conn)
        cur.execute(sql, params)
        results = cur.fetchall()
        cur.close()
        return results
    finally:
        if conn is not None:
            conn.commit()  # Commit read txn to avoid implicit ROLLBACK (psycopg2 autocommit=False)
            conn.close()
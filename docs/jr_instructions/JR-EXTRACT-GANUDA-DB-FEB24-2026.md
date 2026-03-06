# Jr Instruction: Extract ganuda_db Package — Consolidated Database Utilities

**Task ID:** EXTRACT-DB
**Kanban:** #1717
**Priority:** 2
**Sacred Fire Priority:** 35
**Story Points:** 5
**Assigned Jr:** Software Engineer Jr.
**use_rlm:** false

---

## Overview

The `ganuda_db` package at `/ganuda/lib/ganuda_db/__init__.py` currently contains only a placeholder docstring and a TODO comment. This task populates it with consolidated database utilities that the entire federation can import instead of duplicating connection logic across services.

The module must export:
- `DB_CONFIG` — dict with connection parameters
- `get_db_config()` — reads password from env, returns full config dict
- `get_connection()` — returns a psycopg2 connection
- `get_dict_cursor(conn)` — returns a RealDictCursor for a given connection
- `execute_query(sql, params)` — convenience function: connect, execute, fetchall, close

Uses `psycopg2` and `psycopg2.extras` only. No SQLAlchemy.

---

## Step 1: Populate ganuda_db __init__.py

Create `/ganuda/lib/ganuda_db/__init__.py`

```python
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
import psycopg2
import psycopg2.extras

__version__ = "1.1.0"

DB_CONFIG = {
    "host": "192.168.132.222",
    "dbname": "zammad_production",
    "user": "claude",
}


def get_db_config() -> dict:
    """
    Return database connection config with password from environment.

    Reads CHEROKEE_DB_PASS env var for the password.
    Returns a dict suitable for passing to psycopg2.connect(**config).

    Raises:
        ValueError: If CHEROKEE_DB_PASS is not set.
    """
    password = os.environ.get("CHEROKEE_DB_PASS")
    if not password:
        raise ValueError(
            "CHEROKEE_DB_PASS environment variable is not set. "
            "Cannot connect to database without credentials."
        )
    config = dict(DB_CONFIG)
    config["password"] = password
    return config


def get_connection():
    """
    Create and return a new psycopg2 connection using get_db_config().

    Caller is responsible for closing the connection.

    Returns:
        psycopg2.extensions.connection
    """
    config = get_db_config()
    return psycopg2.connect(**config)


def get_dict_cursor(conn):
    """
    Return a RealDictCursor for the given connection.

    Args:
        conn: A psycopg2 connection object.

    Returns:
        psycopg2.extras.RealDictCursor
    """
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


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
            conn.close()
```

---

## Verification

```text
cd /ganuda && python3 -c "
from lib.ganuda_db import DB_CONFIG, get_db_config, get_connection, get_dict_cursor, execute_query
print('DB_CONFIG:', DB_CONFIG)
print('All exports OK')
"
```

Expected output should show DB_CONFIG dict with host, dbname, user keys and print "All exports OK". The `get_db_config()` call will raise ValueError if CHEROKEE_DB_PASS is not set, which is expected.

---

## What NOT to Change

- Do NOT add SQLAlchemy or any ORM dependencies
- Do NOT hardcode the database password anywhere in the file
- Do NOT add connection pooling in this step (future task)
- Do NOT modify any other files in this task

# JR INSTRUCTION: Ephemeral Per-Task Test Harness

**Task**: Build a disposable test environment pattern that spins up per Jr task and tears down after — no persistent shared test environment
**Priority**: P1 — executor integrity, quality gate
**Date**: 2026-03-11
**TPM**: Claude Opus
**Council Vote**: #69aa084f9634eab4 (test environment spec)
**Story Points**: 8

## Problem Statement

The federation has no test environment. Production is the test. This has caused:
- Fire Guard false alerts (20 in 6 hours during a power outage)
- Jr shallow completions (3 of 5 tasks marked done without deliverables)
- Standing dissent bug shipped without test coverage
- idle-in-transaction leaks discovered only in production

A persistent shared test environment (traditional dev/test/prod) doesn't work either. Chief's direct experience: when multiple developers work on interacting systems, shared test environments accumulate stale code from other projects, drift from production, and produce test results that don't reflect reality. The sync-test-roll cycle breaks down.

**Solution**: Ephemeral, per-task test environments. No shared state. No drift. Spin up clean, test, tear down. The test environment lives exactly as long as the test run.

## What You're Building

### Component 1: Test Database Bootstrap Script

A script that creates a fresh test database, mirrors production schema, and seeds baseline data.

**File**: `/ganuda/scripts/test_harness_setup.py`

```python
#!/usr/bin/env python3
"""Ephemeral test database setup — create, seed, and return connection info."""

import psycopg2
import os
import uuid
import sys
from datetime import datetime

# Production DB (read schema only)
PROD_HOST = os.environ.get('CHEROKEE_DB_HOST', '192.168.132.222')
PROD_PORT = int(os.environ.get('CHEROKEE_DB_PORT', 5432))
PROD_DB = os.environ.get('CHEROKEE_DB_NAME', 'zammad_production')
PROD_USER = os.environ.get('CHEROKEE_DB_USER', 'claude')
PROD_PASS = os.environ.get('CHEROKEE_DB_PASS', '')

def create_test_db():
    """Create a uniquely-named test database with production schema."""
    test_db_name = f"ganuda_test_{uuid.uuid4().hex[:8]}"

    # Connect to postgres (default DB) to create test DB
    conn = psycopg2.connect(
        host=PROD_HOST, port=PROD_PORT, dbname='postgres',
        user=PROD_USER, password=PROD_PASS
    )
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f'CREATE DATABASE {test_db_name}')
    cur.close()
    conn.close()

    # Dump production schema (no data) and load into test DB
    # Uses pg_dump --schema-only to get structure without production data
    import subprocess
    env = os.environ.copy()
    env['PGPASSWORD'] = PROD_PASS

    dump = subprocess.run(
        ['pg_dump', '--schema-only', '--no-owner', '--no-privileges',
         '-h', PROD_HOST, '-p', str(PROD_PORT), '-U', PROD_USER, PROD_DB],
        capture_output=True, text=True, env=env, timeout=30
    )

    if dump.returncode != 0:
        raise RuntimeError(f"Schema dump failed: {dump.stderr}")

    load = subprocess.run(
        ['psql', '-h', PROD_HOST, '-p', str(PROD_PORT), '-U', PROD_USER, test_db_name],
        input=dump.stdout, capture_output=True, text=True, env=env, timeout=30
    )

    return test_db_name

def seed_baseline(test_db_name):
    """Seed minimal baseline data for testing."""
    conn = psycopg2.connect(
        host=PROD_HOST, port=PROD_PORT, dbname=test_db_name,
        user=PROD_USER, password=PROD_PASS
    )
    cur = conn.cursor()

    # Seed Jr status entries (required for FK constraints)
    jr_names = [
        'Software Engineer Jr.', 'Infrastructure Jr.', 'Research Jr.',
        'Synthesis Jr.', 'Document Jr.'
    ]
    for jr in jr_names:
        cur.execute(
            "INSERT INTO jr_status (jr_name, status, current_task_id) VALUES (%s, 'idle', NULL) ON CONFLICT DO NOTHING",
            (jr,)
        )

    # Seed a few baseline thermals so queries don't return empty
    cur.execute("""
        INSERT INTO thermal_memory_archive (memory_hash, original_content, memory_type, temperature_score, sacred_pattern, created_at)
        VALUES ('test_baseline_01', 'Test baseline thermal', 'test', 50, false, NOW())
    """)

    conn.commit()
    cur.close()
    conn.close()

def teardown_test_db(test_db_name):
    """Drop the test database. No lingering state."""
    if not test_db_name.startswith('ganuda_test_'):
        raise ValueError(f"Refusing to drop non-test database: {test_db_name}")

    conn = psycopg2.connect(
        host=PROD_HOST, port=PROD_PORT, dbname='postgres',
        user=PROD_USER, password=PROD_PASS
    )
    conn.autocommit = True
    cur = conn.cursor()
    # Terminate any remaining connections
    cur.execute(f"""
        SELECT pg_terminate_backend(pid) FROM pg_stat_activity
        WHERE datname = '{test_db_name}' AND pid <> pg_backend_pid()
    """)
    cur.execute(f'DROP DATABASE IF EXISTS {test_db_name}')
    cur.close()
    conn.close()
```

**Safety**: `teardown_test_db()` refuses to drop anything that doesn't start with `ganuda_test_`. Production cannot be accidentally destroyed.

### Component 2: Test Runner Wrapper

A wrapper that any Jr task (or pytest) can use to get an ephemeral test environment.

**File**: `/ganuda/lib/test_harness.py`

```python
#!/usr/bin/env python3
"""Context manager for ephemeral test environments."""

import os
from contextlib import contextmanager

# Import from scripts
import sys
sys.path.insert(0, '/ganuda/scripts')
from test_harness_setup import create_test_db, seed_baseline, teardown_test_db

@contextmanager
def ephemeral_db():
    """Context manager that provides a clean test database.

    Usage:
        with ephemeral_db() as test_db_name:
            # All code in this block uses the test DB
            os.environ['CHEROKEE_DB_NAME'] = test_db_name
            # ... run tests ...
        # DB is automatically torn down here
    """
    test_db_name = create_test_db()
    seed_baseline(test_db_name)
    try:
        yield test_db_name
    finally:
        teardown_test_db(test_db_name)

@contextmanager
def ephemeral_test_env():
    """Full ephemeral environment — DB + env vars.

    Saves and restores original env vars so production state is never polluted.
    """
    original_db = os.environ.get('CHEROKEE_DB_NAME')
    test_db_name = create_test_db()
    seed_baseline(test_db_name)
    os.environ['CHEROKEE_DB_NAME'] = test_db_name
    os.environ['GANUDA_TEST_MODE'] = '1'
    try:
        yield test_db_name
    finally:
        teardown_test_db(test_db_name)
        # Restore original env
        if original_db:
            os.environ['CHEROKEE_DB_NAME'] = original_db
        else:
            os.environ.pop('CHEROKEE_DB_NAME', None)
        os.environ.pop('GANUDA_TEST_MODE', None)
```

### Component 3: Pytest Fixture

So existing and new tests can use the harness with one decorator.

**File**: `/ganuda/tests/conftest.py`

```python
import pytest
import os
import sys
sys.path.insert(0, '/ganuda/lib')
from test_harness import ephemeral_db, ephemeral_test_env

@pytest.fixture
def test_db():
    """Pytest fixture providing an ephemeral test database."""
    with ephemeral_db() as db_name:
        yield db_name

@pytest.fixture
def test_env():
    """Pytest fixture providing full ephemeral test environment."""
    with ephemeral_test_env() as db_name:
        yield db_name
```

Usage in any test file:
```python
def test_standing_dissent_with_consent_true(test_env):
    """Now this test runs against an ephemeral DB, not production."""
    from specialist_council import SpecialistCouncil
    # ... test code that writes to DB without touching production ...
```

### Component 4: Stale Test DB Cleanup

A safety script that finds and drops any `ganuda_test_*` databases older than 1 hour. Catches cases where teardown failed (crash, timeout, etc.).

**File**: `/ganuda/scripts/cleanup_test_dbs.py`

```python
#!/usr/bin/env python3
"""Clean up orphaned test databases older than 1 hour."""
import psycopg2
import os

def cleanup():
    conn = psycopg2.connect(
        host=os.environ.get('CHEROKEE_DB_HOST', '192.168.132.222'),
        port=5432, dbname='postgres',
        user=os.environ.get('CHEROKEE_DB_USER', 'claude'),
        password=os.environ.get('CHEROKEE_DB_PASS', '')
    )
    conn.autocommit = True
    cur = conn.cursor()

    # Find test databases
    cur.execute("""
        SELECT datname FROM pg_database
        WHERE datname LIKE 'ganuda_test_%'
    """)
    test_dbs = [r[0] for r in cur.fetchall()]

    for db in test_dbs:
        # Check age via stats
        cur.execute(f"""
            SELECT (NOW() - stats_reset) > INTERVAL '1 hour'
            FROM pg_stat_database WHERE datname = '{db}'
        """)
        row = cur.fetchone()
        if row and row[0]:
            print(f"Dropping orphaned test DB: {db}")
            cur.execute(f"""
                SELECT pg_terminate_backend(pid) FROM pg_stat_activity
                WHERE datname = '{db}' AND pid <> pg_backend_pid()
            """)
            cur.execute(f'DROP DATABASE IF EXISTS {db}')

    cur.close()
    conn.close()

if __name__ == '__main__':
    cleanup()
```

Wire this into the credential-scanner timer (Sat 2 AM) or add its own weekly timer.

## Target Files

- `/ganuda/scripts/test_harness_setup.py` — DB create/seed/teardown (CREATE)
- `/ganuda/lib/test_harness.py` — context manager wrapper (CREATE)
- `/ganuda/tests/conftest.py` — pytest fixtures (CREATE)
- `/ganuda/scripts/cleanup_test_dbs.py` — orphaned test DB cleanup (CREATE)

## How This Changes the Jr Executor Flow

Currently:
```
Jr picks up task → executes steps → marks complete (against production)
```

Future (once wired into executor):
```
Jr picks up task → spin up ephemeral DB → execute steps → verify artifacts → tear down → if pass: apply to production → mark complete
```

This wiring into the executor is a SEPARATE Jr task. This instruction only builds the harness itself.

## Constraints

- Test databases MUST be named `ganuda_test_*` — teardown refuses to drop anything else
- NEVER copy production DATA into test — schema only, then seed baseline
- Crawdad binding condition: no credentials in test seed data
- DC-9: test DBs are ephemeral, not permanent. No lingering compute cost
- Test harness must work with existing pytest tests (backward compatible)
- `GANUDA_TEST_MODE=1` env var must be set during test runs so production code can check it

## Acceptance Criteria

- `python3 scripts/test_harness_setup.py` creates a `ganuda_test_*` database, seeds it, and tears it down
- `pytest tests/test_standing_dissent.py` runs against an ephemeral DB (not production)
- No `ganuda_test_*` databases remain after test completion
- `cleanup_test_dbs.py` finds and drops orphaned test DBs older than 1 hour
- `teardown_test_db()` raises ValueError if asked to drop a non-test database
- Production `zammad_production` is never modified by test runs
- `python3 -c "import py_compile; py_compile.compile('scripts/test_harness_setup.py', doraise=True)"` passes
- `python3 -c "import py_compile; py_compile.compile('lib/test_harness.py', doraise=True)"` passes

## DO NOT

- Copy production data into test databases
- Create a persistent test database that lingers
- Modify any production tables or schemas
- Include credentials in seed data
- Make the test harness dependent on GPU services (embedding, LLM) — mock those
- Wire this into the executor yet — that's a separate task

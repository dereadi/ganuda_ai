# Jr Instruction: TPM Autonomic Daemon — Connection Pooling Fix + Basin History Table

**Task ID:** TPM-AUTONOMIC-FIX
**Kanban:** #1819 (Phase 1), #1820 (Phase 2)
**Priority:** 3
**Assigned:** Software Engineer Jr.

---

## Overview

The TPM autonomic daemon v2 (`/ganuda/daemons/tpm_autonomic_v2.py`, 615 lines) is feature-complete but has a connection leak: every DB operation creates a new psycopg2 connection without pooling. Fix the connection pattern and add a `basin_signal_history` table for trend analysis.

---

## Step 1: Add connection pooling to TPM autonomic daemon

File: `/ganuda/daemons/tpm_autonomic_v2.py`

<<<<<<< SEARCH
import psycopg2
from psycopg2.extras import RealDictCursor
=======
import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor
>>>>>>> REPLACE

---

## Step 2: Replace get_db with pooled connection

File: `/ganuda/daemons/tpm_autonomic_v2.py`

<<<<<<< SEARCH
def get_db():
    """Get a database connection."""
    return psycopg2.connect(**DB_PARAMS, cursor_factory=RealDictCursor)
=======
# Connection pool (initialized once, reused across cycles)
_db_pool = None

def init_db_pool():
    """Initialize the connection pool. Call once at daemon startup."""
    global _db_pool
    _db_pool = psycopg2.pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=5,
        cursor_factory=RealDictCursor,
        **DB_PARAMS
    )

def get_db():
    """Get a pooled database connection. Must call put_db() when done."""
    if _db_pool is None:
        init_db_pool()
    return _db_pool.getconn()

def put_db(conn):
    """Return a connection to the pool."""
    if _db_pool and conn:
        _db_pool.putconn(conn)
>>>>>>> REPLACE

---

## Step 3: Update fetch_pending_tasks to return connections to pool

File: `/ganuda/daemons/tpm_autonomic_v2.py`

<<<<<<< SEARCH
def fetch_pending_tasks(limit=5):
    """Fetch pending tasks from jr_work_queue, oldest first by priority."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, task_id, title, instruction_file, assigned_jr, priority,
               sacred_fire_priority, use_rlm, parameters, created_at
        FROM jr_work_queue
        WHERE status = 'pending'
        ORDER BY priority ASC, created_at ASC
        LIMIT %s
    """, (limit,))
    tasks = cur.fetchall()
=======
def fetch_pending_tasks(limit=5):
    """Fetch pending tasks from jr_work_queue, oldest first by priority."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, task_id, title, instruction_file, assigned_jr, priority,
                   sacred_fire_priority, use_rlm, parameters, created_at
            FROM jr_work_queue
            WHERE status = 'pending'
            ORDER BY priority ASC, created_at ASC
            LIMIT %s
        """, (limit,))
        tasks = cur.fetchall()
>>>>>>> REPLACE

Find the corresponding close at the end of this function and replace:

<<<<<<< SEARCH
    cur.close()
    conn.close()
=======
        cur.close()
        return tasks
    finally:
        put_db(conn)
>>>>>>> REPLACE

---

## Step 4: Update log_thermal_memory to use pool

File: `/ganuda/daemons/tpm_autonomic_v2.py`

<<<<<<< SEARCH
def log_thermal_memory(content, temperature=75.0, sacred=False):
    """Store a thermal memory record."""
    conn = get_db()
    cur = conn.cursor()
    memory_hash = hashlib.sha256(content.encode()).hexdigest()
    cur.execute("""
        INSERT INTO thermal_memory_archive
        (original_content, temperature_score, sacred_pattern, memory_hash,
         metadata, created_at)
        VALUES (%s, %s, %s, %s, %s, NOW())
        ON CONFLICT (memory_hash) DO NOTHING
    """, (
        content[:10000],
        temperature,
        sacred,
        memory_hash,
        json.dumps({"source": "tpm_autonomic_v2", "timestamp": datetime.utcnow().isoformat()})
    ))
    conn.commit()
    cur.close()
    conn.close()
=======
def log_thermal_memory(content, temperature=75.0, sacred=False):
    """Store a thermal memory record."""
    conn = get_db()
    try:
        cur = conn.cursor()
        memory_hash = hashlib.sha256(content.encode()).hexdigest()
        cur.execute("""
            INSERT INTO thermal_memory_archive
            (original_content, temperature_score, sacred_pattern, memory_hash,
             metadata, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            ON CONFLICT (memory_hash) DO NOTHING
        """, (
            content[:10000],
            temperature,
            sacred,
            memory_hash,
            json.dumps({"source": "tpm_autonomic_v2", "timestamp": datetime.utcnow().isoformat()})
        ))
        conn.commit()
        cur.close()
    finally:
        put_db(conn)
>>>>>>> REPLACE

---

## Step 5: Update check_basin_signals to use pool

File: `/ganuda/daemons/tpm_autonomic_v2.py`

<<<<<<< SEARCH
def check_basin_signals():
    """Check all 6 basin signals. Returns list of active signals."""
    signals = []
    conn = get_db()
    cur = conn.cursor()
=======
def check_basin_signals():
    """Check all 6 basin signals. Returns list of active signals."""
    signals = []
    conn = get_db()
    try:
        cur = conn.cursor()
>>>>>>> REPLACE

And at the end of check_basin_signals:

<<<<<<< SEARCH
    cur.close()
    conn.close()
    return signals
=======
        cur.close()
        return signals
    finally:
        put_db(conn)
>>>>>>> REPLACE

---

## Step 6: Create basin_signal_history table

Create `/ganuda/scripts/migrations/basin_signal_history.py`

```python
#!/usr/bin/env python3
"""Basin Signal History table for trend analysis. Kanban #1820."""

import os
import psycopg2

SECRETS_FILE = "/ganuda/config/secrets.env"

def load_secrets():
    secrets = {}
    if os.path.exists(SECRETS_FILE):
        with open(SECRETS_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    secrets[key] = val
    return secrets

def run():
    secrets = load_secrets()
    conn = psycopg2.connect(
        host=secrets.get("CHEROKEE_DB_HOST", "192.168.132.222"),
        dbname=secrets.get("CHEROKEE_DB_NAME", "zammad_production"),
        user=secrets.get("CHEROKEE_DB_USER", "claude"),
        password=secrets.get("CHEROKEE_DB_PASS", ""),
        port=int(secrets.get("CHEROKEE_DB_PORT", "5432"))
    )
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS basin_signal_history (
            id SERIAL PRIMARY KEY,
            signal_type VARCHAR(50) NOT NULL,
            signal_value FLOAT NOT NULL,
            threshold FLOAT NOT NULL,
            detail TEXT,
            escalated BOOLEAN DEFAULT FALSE,
            detected_at TIMESTAMP DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_basin_signal_type
            ON basin_signal_history (signal_type, detected_at DESC);
        CREATE INDEX IF NOT EXISTS idx_basin_escalated
            ON basin_signal_history (escalated) WHERE escalated = true;
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("[MIGRATION] basin_signal_history table created")

if __name__ == "__main__":
    run()
```

---

## Verification

1. Run the migration:
```text
cd /ganuda/scripts/migrations && python3 basin_signal_history.py
```

2. Test the daemon starts without connection errors:
```text
cd /ganuda/daemons && python3 -c "from tpm_autonomic_v2 import init_db_pool, get_db, put_db, check_basin_signals; init_db_pool(); s = check_basin_signals(); print(f'Basin signals: {len(s)}')"
```

---

## Notes

- Systemd service deployment is TPM-direct (requires sudo)
- Claude Agent SDK dependency (`claude-agent-sdk`) must be installed separately
- Connection pool maxconn=5 is sufficient — daemon runs single-threaded with periodic async tasks

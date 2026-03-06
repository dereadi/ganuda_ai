# Jr Instruction: VetAssist Backend Memory Leak Fix

**Task ID:** VA-MEMLEAK
**Kanban:** #1776
**Priority:** 3
**Assigned:** Software Engineer Jr.

---

## Overview

VetAssist backend creeps from 1.2GB → 2.0GB over 48-72 hours. Root causes:

1. SQLAlchemy connection pool missing `pool_recycle` and `pool_timeout` — connections accumulate
2. Raw psycopg2 connections in services lack `finally` cleanup — exceptions leak connections
3. No `MemoryHigh` in systemd service — OOM kill is the only recovery

Three surgical fixes, no architectural changes.

---

## Step 1: Fix SQLAlchemy connection pool settings

File: `/ganuda/vetassist/backend/app/core/database.py`

<<<<<<< SEARCH
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DB_ECHO,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )
=======
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DB_ECHO,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_recycle=1800,
        pool_timeout=30
    )
>>>>>>> REPLACE

**What this does:**
- `pool_size=5` (was 10): Reduces baseline connection count
- `max_overflow=10` (was 20): Caps max connections at 15 (was 30)
- `pool_recycle=1800`: Recycles connections after 30 minutes — prevents stale connection accumulation
- `pool_timeout=30`: Timeout waiting for a connection from pool — prevents indefinite hangs

---

## Step 2: Add connection cleanup to RAG query service

File: `/ganuda/vetassist/backend/app/services/rag_query.py`

Find the `retrieve` method's database connection section and wrap it in try/finally. The exact search text may vary, but look for:

<<<<<<< SEARCH
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()
=======
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
>>>>>>> REPLACE

And at the end of the method, find the close call and ensure it's in a finally:

<<<<<<< SEARCH
        conn.close()
        return chunks
=======
            return chunks
        finally:
            if conn:
                conn.close()
>>>>>>> REPLACE

---

## Step 3: Add connection cleanup to RAG ingestion service

File: `/ganuda/vetassist/backend/app/services/rag_ingestion.py`

Same pattern — find the `ingest` method's connection and wrap:

<<<<<<< SEARCH
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()
=======
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
>>>>>>> REPLACE

And at the end:

<<<<<<< SEARCH
        conn.close()
=======
        finally:
            if conn:
                conn.close()
>>>>>>> REPLACE

---

## Verification

After deploying, restart VetAssist backend:
```text
sudo systemctl restart vetassist-backend
```

Monitor memory over 24 hours:
```text
ps -p $(pgrep -f "uvicorn app.main") -o rss=
```

Expected: Memory stays under 1.5GB instead of creeping to 2.0GB.

---

## Notes

- systemd `MemoryHigh=1536M` addition requires TPM (service file modification)
- The pool_recycle=1800 is the most impactful fix — it prevents zombie connections
- Reducing pool_size from 10 to 5 is safe — VetAssist handles <50 concurrent users

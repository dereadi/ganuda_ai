# Jr Instruction: Council Orchestrator Daemon

**Task ID:** COUNCIL-ORCH
**Kanban:** #1835
**Priority:** 3
**Assigned:** Software Engineer Jr.

---

## Overview

Create a daemon that auto-triages council votes. Auto-approves high-confidence votes and flags low-confidence ones for Chief review.

---

## Step 1: Create the orchestrator daemon

Create `/ganuda/daemons/council_orchestrator.py`

```python
#!/usr/bin/env python3
"""Council Orchestrator Daemon.
Polls council_votes for pending TPM decisions.
Auto-approves high-confidence, flags low-confidence for review."""

import signal
import sys
import time
from datetime import datetime

import psycopg2
import psycopg2.pool

DB_CONFIG = {
    "host": "192.168.132.222",
    "user": "claude",
    "dbname": "zammad_production"
}

POLL_INTERVAL = 60
AUTO_APPROVE_THRESHOLD = 0.85
MAX_CONCERNS_AUTO = 1
FLAG_THRESHOLD = 0.6

pool = None
running = True

def init_pool():
    global pool
    pool = psycopg2.pool.SimpleConnectionPool(1, 3, **DB_CONFIG)

def shutdown(signum, frame):
    global running
    print(f"Received signal {signum}, shutting down...")
    running = False

def get_pending_votes(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT vote_id, audit_hash, confidence, concern_count,
                   recommendation, vote_window_expires
            FROM council_votes
            WHERE tpm_vote = 'pending'
              AND vote_window_expires < NOW()
            ORDER BY vote_window_expires ASC
        """)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

def auto_decide(conn, vote):
    conf = vote["confidence"] or 0
    concerns = vote["concern_count"] or 0
    if conf >= AUTO_APPROVE_THRESHOLD and concerns <= MAX_CONCERNS_AUTO:
        decision = "approve"
        comment = f"AUTO-APPROVED by orchestrator (confidence={conf:.3f}, concerns={concerns})"
    elif conf < FLAG_THRESHOLD:
        decision = "needs_review"
        comment = f"FLAGGED for Chief review (confidence={conf:.3f} below {FLAG_THRESHOLD})"
    else:
        return False
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE council_votes
            SET tpm_vote = %s, tpm_vote_at = NOW(), tpm_comment = %s
            WHERE vote_id = %s AND tpm_vote = 'pending'
        """, (decision, comment, vote["vote_id"]))
        cur.execute("""
            INSERT INTO thermal_memory_archive (original_content, temperature_score, sacred_pattern, memory_hash)
            VALUES (%s, %s, false, encode(sha256((%s || now()::text)::bytea), 'hex'))
        """, (
            f"COUNCIL ORCHESTRATOR: {decision.upper()} vote #{vote['audit_hash']} "
            f"(confidence={conf:.3f}, concerns={concerns}). {comment}",
            70 if decision == "approve" else 85,
            f"orchestrator-{vote['audit_hash']}-"
        ))
    conn.commit()
    print(f"[{datetime.now().isoformat()}] {decision.upper()}: #{vote['audit_hash']} (conf={conf:.3f})")
    return True

def poll_loop():
    while running:
        conn = pool.getconn()
        try:
            votes = get_pending_votes(conn)
            for vote in votes:
                auto_decide(conn, vote)
            if votes:
                print(f"[{datetime.now().isoformat()}] Processed {len(votes)} votes")
        except Exception as e:
            print(f"Error: {e}")
            conn.rollback()
        finally:
            pool.putconn(conn)
        for _ in range(POLL_INTERVAL):
            if not running:
                break
            time.sleep(1)

def main():
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    print(f"Council Orchestrator starting (poll={POLL_INTERVAL}s, auto_approve>={AUTO_APPROVE_THRESHOLD})")
    init_pool()
    try:
        poll_loop()
    finally:
        if pool:
            pool.closeall()
    print("Orchestrator shutdown complete")

if __name__ == "__main__":
    main()
```

---

## Verification

```text
python3 /ganuda/daemons/council_orchestrator.py &
sleep 5 && kill %1
```

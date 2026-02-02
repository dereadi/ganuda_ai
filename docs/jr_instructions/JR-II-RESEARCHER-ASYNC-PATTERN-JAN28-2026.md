# JR Instruction: ii-researcher Async Job Pattern

**JR ID:** JR-II-RESEARCHER-ASYNC-PATTERN-JAN28-2026
**Priority:** P1
**Assigned To:** Software Engineer Jr.
**Council Vote:** 166956a7959c2232
**Related:** JR-II-RESEARCHER-STEP-LIMIT-FIX-JAN28-2026

---

## Objective

Implement async job pattern for ii-researcher. Research takes 3-5 minutes - too long for synchronous requests. Run research in background, write results to file, notify user when complete.

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ User Request    │────▶│ Research Queue   │────▶│ ii-researcher   │
│ (Telegram/API)  │     │ (PostgreSQL)     │     │ (background)    │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Notify User     │◀────│ Watcher Daemon   │◀────│ Output File     │
│ (Telegram/etc)  │     │ (polls for done) │     │ .json           │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

---

## Files to Create

### 1. Research Job Queue Table

```sql
-- Run on bluefin (192.168.132.222) in zammad_production

CREATE TABLE IF NOT EXISTS research_jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(64) UNIQUE NOT NULL,
    query TEXT NOT NULL,
    max_steps INT DEFAULT 5,
    requester_type VARCHAR(50),  -- 'telegram', 'vetassist', 'council', 'jr'
    requester_id VARCHAR(100),   -- telegram user_id, session_id, etc.
    callback_type VARCHAR(50),   -- 'telegram', 'webhook', 'file'
    callback_target TEXT,        -- chat_id, webhook_url, or file path
    status VARCHAR(20) DEFAULT 'pending',  -- pending, running, completed, failed
    output_file TEXT,
    result_summary TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_research_jobs_status ON research_jobs(status);
CREATE INDEX idx_research_jobs_requester ON research_jobs(requester_type, requester_id);
```

### 2. Research Job Dispatcher

Create `/ganuda/lib/research_dispatcher.py`:

```python
#!/usr/bin/env python3
"""
Research Job Dispatcher - Queue and dispatch research jobs.

For Seven Generations - Cherokee AI Federation
"""

import os
import uuid
import json
import psycopg2
from datetime import datetime
from typing import Optional, Dict, Any

DB_CONFIG = {
    'host': os.environ.get('CHEROKEE_DB_HOST', '192.168.132.222'),
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

RESEARCH_OUTPUT_DIR = "/ganuda/research/completed"


class ResearchDispatcher:
    """Dispatch research jobs to background processing."""

    def __init__(self):
        os.makedirs(RESEARCH_OUTPUT_DIR, exist_ok=True)

    def _get_conn(self):
        return psycopg2.connect(**DB_CONFIG)

    def queue_research(
        self,
        query: str,
        requester_type: str,
        requester_id: str,
        callback_type: str = "file",
        callback_target: str = None,
        max_steps: int = 5
    ) -> str:
        """
        Queue a research job.

        Returns:
            job_id for tracking
        """
        job_id = f"research-{uuid.uuid4().hex[:12]}"
        output_file = f"{RESEARCH_OUTPUT_DIR}/{job_id}.json"

        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO research_jobs
            (job_id, query, max_steps, requester_type, requester_id,
             callback_type, callback_target, output_file, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')
            RETURNING id
        """, (job_id, query, max_steps, requester_type, requester_id,
              callback_type, callback_target or output_file, output_file))
        conn.commit()
        cur.close()
        conn.close()

        return job_id

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get status of a research job."""
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT job_id, query, status, result_summary, error_message,
                   output_file, created_at, completed_at
            FROM research_jobs WHERE job_id = %s
        """, (job_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if not row:
            return None

        return {
            "job_id": row[0],
            "query": row[1],
            "status": row[2],
            "result_summary": row[3],
            "error": row[4],
            "output_file": row[5],
            "created_at": row[6].isoformat() if row[6] else None,
            "completed_at": row[7].isoformat() if row[7] else None
        }

    def get_pending_jobs(self, limit: int = 10) -> list:
        """Get pending research jobs."""
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT job_id, query, max_steps, requester_type, output_file
            FROM research_jobs
            WHERE status = 'pending'
            ORDER BY created_at ASC
            LIMIT %s
        """, (limit,))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        return [{"job_id": r[0], "query": r[1], "max_steps": r[2],
                 "requester_type": r[3], "output_file": r[4]} for r in rows]


# Convenience function
def queue_research(query: str, requester: str = "api") -> str:
    """Quick way to queue a research job."""
    dispatcher = ResearchDispatcher()
    return dispatcher.queue_research(
        query=query,
        requester_type=requester,
        requester_id="anonymous",
        max_steps=5
    )
```

### 3. Research Worker Daemon

Create `/ganuda/services/research_worker.py`:

```python
#!/usr/bin/env python3
"""
Research Worker - Processes research jobs from queue.

Runs as systemd service, polls for pending jobs, executes ii-researcher,
writes results to files, updates job status.

For Seven Generations - Cherokee AI Federation
"""

import os
import sys
import json
import time
import logging
import psycopg2
import subprocess
from datetime import datetime

sys.path.insert(0, '/ganuda/lib')
from research_client import ResearchClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [ResearchWorker] %(message)s'
)

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

POLL_INTERVAL = 10  # seconds


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def claim_job():
    """Claim a pending job for processing."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE research_jobs
        SET status = 'running', started_at = NOW()
        WHERE id = (
            SELECT id FROM research_jobs
            WHERE status = 'pending'
            ORDER BY created_at ASC
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        )
        RETURNING job_id, query, max_steps, output_file, callback_type, callback_target
    """)
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return row


def complete_job(job_id: str, output_file: str, summary: str):
    """Mark job as completed."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE research_jobs
        SET status = 'completed', completed_at = NOW(),
            result_summary = %s, output_file = %s
        WHERE job_id = %s
    """, (summary[:500], output_file, job_id))
    conn.commit()
    cur.close()
    conn.close()


def fail_job(job_id: str, error: str):
    """Mark job as failed."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE research_jobs
        SET status = 'failed', completed_at = NOW(), error_message = %s
        WHERE job_id = %s
    """, (error[:500], job_id))
    conn.commit()
    cur.close()
    conn.close()


def process_job(job_id, query, max_steps, output_file, callback_type, callback_target):
    """Process a research job."""
    logging.info(f"Processing job {job_id}: {query[:50]}...")

    try:
        client = ResearchClient(timeout=300.0)  # 5 min timeout
        result = client.search(query, max_steps=max_steps)

        if result.error:
            fail_job(job_id, result.error)
            logging.error(f"Job {job_id} failed: {result.error}")
            return

        # Write result to file
        output = {
            "job_id": job_id,
            "query": query,
            "answer": result.answer,
            "sources": result.sources,
            "confidence": result.confidence,
            "search_time_ms": result.search_time_ms,
            "completed_at": datetime.now().isoformat()
        }

        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)

        # Generate summary (first 200 chars of answer)
        summary = result.answer[:200] + "..." if len(result.answer) > 200 else result.answer

        complete_job(job_id, output_file, summary)
        logging.info(f"Job {job_id} completed -> {output_file}")

        # Handle callbacks
        if callback_type == "telegram":
            notify_telegram(callback_target, job_id, summary)

    except Exception as e:
        fail_job(job_id, str(e))
        logging.error(f"Job {job_id} exception: {e}")


def notify_telegram(chat_id: str, job_id: str, summary: str):
    """Send Telegram notification when research is done."""
    # TODO: Implement telegram notification
    logging.info(f"Would notify Telegram {chat_id}: Research {job_id} complete")


def main():
    logging.info("Research Worker starting...")
    logging.info(f"Poll interval: {POLL_INTERVAL}s")

    while True:
        try:
            job = claim_job()
            if job:
                job_id, query, max_steps, output_file, cb_type, cb_target = job
                process_job(job_id, query, max_steps, output_file, cb_type, cb_target)
            else:
                time.sleep(POLL_INTERVAL)
        except Exception as e:
            logging.error(f"Worker error: {e}")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
```

### 4. Systemd Service

Create `/ganuda/scripts/systemd/research-worker.service`:

```ini
[Unit]
Description=Cherokee Research Worker
After=network.target ii-researcher.service
Wants=ii-researcher.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/services
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
ExecStart=/home/dereadi/cherokee_venv/bin/python /ganuda/services/research_worker.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=research-worker

[Install]
WantedBy=multi-user.target
```

### 5. Update LLM Gateway Endpoint

Add async research endpoint to `/ganuda/services/llm_gateway/gateway.py`:

```python
@app.post("/v1/research/async")
async def queue_research(request: ResearchQuery, api_key: APIKeyInfo = Depends(validate_api_key)):
    """
    Queue a research job for background processing.
    Returns job_id immediately. Poll /v1/research/status/{job_id} for results.
    """
    sys.path.insert(0, '/ganuda/lib')
    from research_dispatcher import ResearchDispatcher

    dispatcher = ResearchDispatcher()
    job_id = dispatcher.queue_research(
        query=request.query,
        requester_type="api",
        requester_id=api_key.user_id,
        max_steps=request.max_steps
    )

    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Research queued. Poll /v1/research/status/{job_id} for results.",
        "estimated_time": "3-5 minutes"
    }

@app.get("/v1/research/status/{job_id}")
async def research_status(job_id: str, api_key: APIKeyInfo = Depends(validate_api_key)):
    """Get status of a research job."""
    sys.path.insert(0, '/ganuda/lib')
    from research_dispatcher import ResearchDispatcher

    dispatcher = ResearchDispatcher()
    status = dispatcher.get_job_status(job_id)

    if not status:
        raise HTTPException(status_code=404, detail="Job not found")

    return status
```

---

## Deployment

```bash
# Create output directory
mkdir -p /ganuda/research/completed

# Create database table
psql -h 192.168.132.222 -U claude -d zammad_production -f create_research_jobs.sql

# Deploy files
# (files created above)

# Enable and start worker
sudo ln -sf /ganuda/scripts/systemd/research-worker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable research-worker
sudo systemctl start research-worker

# Restart gateway
sudo systemctl restart llm-gateway
```

---

## Usage

### Queue Research (API)
```bash
curl -X POST http://localhost:8080/v1/research/async \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -d '{"query": "VA tinnitus rating", "max_steps": 5}'

# Response:
# {"job_id": "research-abc123", "status": "queued", "estimated_time": "3-5 minutes"}
```

### Check Status
```bash
curl http://localhost:8080/v1/research/status/research-abc123 \
  -H "X-API-Key: YOUR_KEY"

# Response when complete:
# {"job_id": "research-abc123", "status": "completed", "result_summary": "...", "output_file": "..."}
```

### Telegram Integration
User: `/research VA sleep apnea secondary to PTSD`
Bot: "🔍 Research queued. I'll notify you when complete (3-5 min)."
... 4 minutes later ...
Bot: "📊 Research complete! [summary] Full report: [link]"

---

## Notes

- Research runs completely in background
- User gets immediate acknowledgment
- Notification when complete (Telegram, webhook, or file watcher)
- Results stored in JSON files for easy access
- Job history in database for tracking/analytics

---

FOR SEVEN GENERATIONS

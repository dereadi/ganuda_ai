# JR Instruction: VetAssist File-Watcher Daemon

**JR ID:** JR-VETASSIST-FILE-WATCHER-DAEMON-JAN28-2026
**Priority:** P1
**Assigned To:** Software Engineer Jr.
**Related:** JR-II-RESEARCHER-ASYNC-PATTERN-JAN28-2026

---

## Objective

Create file-based async research for VetAssist:
1. VetAssist drops request file
2. Watcher daemon picks up and queues to ii-researcher
3. When output file is 1 minute old (complete), post results to dashboard

---

## Architecture

```
VetAssist                    File Watcher                 ii-researcher
    │                            │                             │
    ├─► /ganuda/research/requests/{veteran_id}-{uuid}.json     │
    │                            │                             │
    │                    detect new file                       │
    │                            │                             │
    │                            ├─────► queue research ───────►
    │                            │                             │
    │                            │       ◄─── output file ─────┤
    │                            │                             │
    │               wait until file 1 min old                  │
    │                            │                             │
    │   ◄──── POST to dashboard ─┤                             │
```

---

## Files to Create

### 1. Request/Response Directories

```bash
mkdir -p /ganuda/research/requests
mkdir -p /ganuda/research/completed
```

### 2. File Watcher Daemon

Create `/ganuda/services/research_file_watcher.py`:

```python
#!/usr/bin/env python3
"""
Research File Watcher - Monitors for request files, triggers research,
posts results back to VetAssist dashboard when complete.

File is considered complete when modified date is >= 60 seconds old.

For Seven Generations - Cherokee AI Federation
"""

import os
import sys
import json
import time
import logging
import requests
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/ganuda/lib')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [FileWatcher] %(message)s'
)

REQUEST_DIR = Path("/ganuda/research/requests")
COMPLETED_DIR = Path("/ganuda/research/completed")
PROCESSED_DIR = Path("/ganuda/research/requests/processed")
GATEWAY_URL = "http://localhost:8080"
VETASSIST_API = "http://localhost:8000/api/v1"  # VetAssist backend
API_KEY = "ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"

POLL_INTERVAL = 5  # seconds
COMPLETION_AGE = 60  # seconds - file must be this old to be considered complete


def get_file_age(filepath: Path) -> float:
    """Get file age in seconds."""
    mtime = filepath.stat().st_mtime
    return time.time() - mtime


def process_request_file(request_file: Path):
    """Process a research request file."""
    try:
        with open(request_file) as f:
            request = json.load(f)

        veteran_id = request.get("veteran_id")
        session_id = request.get("session_id")
        question = request.get("question")
        condition = request.get("condition", "")

        if not all([veteran_id, question]):
            logging.error(f"Invalid request file: {request_file}")
            return

        logging.info(f"Processing request for veteran {veteran_id}: {question[:50]}...")

        # Queue research via gateway
        response = requests.post(
            f"{GATEWAY_URL}/v1/research/async",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": API_KEY
            },
            json={
                "query": f"{question} {condition}".strip(),
                "max_steps": 5
            },
            timeout=10
        )

        if response.status_code != 200:
            logging.error(f"Failed to queue research: {response.text}")
            return

        data = response.json()
        job_id = data.get("job_id")

        # Update request file with job_id
        request["job_id"] = job_id
        request["queued_at"] = datetime.now().isoformat()

        with open(request_file, 'w') as f:
            json.dump(request, f, indent=2)

        logging.info(f"Queued job {job_id} for veteran {veteran_id}")

        # Move to processed directory
        PROCESSED_DIR.mkdir(exist_ok=True)
        processed_file = PROCESSED_DIR / request_file.name
        request_file.rename(processed_file)

        # Start monitoring for completion
        monitor_job_completion(job_id, veteran_id, session_id, question)

    except Exception as e:
        logging.error(f"Error processing {request_file}: {e}")


def monitor_job_completion(job_id: str, veteran_id: str, session_id: str, question: str):
    """Monitor for job completion and post to dashboard."""
    output_file = COMPLETED_DIR / f"{job_id}.json"
    max_wait = 600  # 10 minutes max
    waited = 0

    while waited < max_wait:
        if output_file.exists():
            age = get_file_age(output_file)
            if age >= COMPLETION_AGE:
                logging.info(f"Job {job_id} complete (file age: {age:.0f}s)")
                post_to_dashboard(job_id, veteran_id, session_id, question, output_file)
                return
            else:
                logging.debug(f"File exists but only {age:.0f}s old, waiting...")

        time.sleep(10)
        waited += 10

    logging.error(f"Job {job_id} timed out after {max_wait}s")


def post_to_dashboard(job_id: str, veteran_id: str, session_id: str, question: str, output_file: Path):
    """Post research results to VetAssist dashboard."""
    try:
        with open(output_file) as f:
            result = json.load(f)

        answer = result.get("answer", "")
        sources = result.get("sources", [])

        # Post to VetAssist research results endpoint
        response = requests.post(
            f"{VETASSIST_API}/research/complete",
            json={
                "veteran_id": veteran_id,
                "session_id": session_id,
                "job_id": job_id,
                "question": question,
                "answer": answer,
                "sources": sources,
                "completed_at": datetime.now().isoformat()
            },
            timeout=10
        )

        if response.status_code == 200:
            logging.info(f"Posted results for {job_id} to dashboard")
        else:
            logging.error(f"Failed to post to dashboard: {response.text}")

    except Exception as e:
        logging.error(f"Error posting to dashboard: {e}")


def scan_for_requests():
    """Scan for new request files."""
    REQUEST_DIR.mkdir(exist_ok=True)

    for request_file in REQUEST_DIR.glob("*.json"):
        if request_file.is_file():
            age = get_file_age(request_file)
            # Only process files that are at least 5 seconds old (fully written)
            if age >= 5:
                process_request_file(request_file)


def main():
    logging.info("Research File Watcher starting...")
    logging.info(f"Request dir: {REQUEST_DIR}")
    logging.info(f"Completed dir: {COMPLETED_DIR}")
    logging.info(f"Completion age threshold: {COMPLETION_AGE}s")

    REQUEST_DIR.mkdir(exist_ok=True)
    COMPLETED_DIR.mkdir(exist_ok=True)

    while True:
        try:
            scan_for_requests()
            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            logging.info("Watcher shutting down...")
            break
        except Exception as e:
            logging.error(f"Watcher error: {e}")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
```

### 3. Systemd Service

Create `/ganuda/scripts/systemd/research-file-watcher.service`:

```ini
[Unit]
Description=Cherokee Research File Watcher
After=network.target research-worker.service
Wants=research-worker.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/services
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
Environment=PYTHONPATH=/ganuda/lib
ExecStart=/home/dereadi/cherokee_venv/bin/python -u /ganuda/services/research_file_watcher.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=research-file-watcher

[Install]
WantedBy=multi-user.target
```

### 4. VetAssist Backend Endpoint

Add to `/ganuda/vetassist/backend/app/api/v1/endpoints/research.py`:

```python
@router.post("/request")
def create_research_request(request: ResearchRequest):
    """
    Drop a research request file for async processing.
    File watcher will pick it up and post results when complete.
    """
    import uuid
    from pathlib import Path

    request_id = str(uuid.uuid4())[:8]
    request_dir = Path("/ganuda/research/requests")
    request_dir.mkdir(exist_ok=True)

    request_file = request_dir / f"{request.veteran_id}-{request_id}.json"

    with open(request_file, 'w') as f:
        json.dump({
            "veteran_id": request.veteran_id,
            "session_id": request.session_id,
            "question": request.question,
            "condition": request.condition,
            "created_at": datetime.now().isoformat()
        }, f, indent=2)

    return {
        "status": "request_filed",
        "request_id": request_id,
        "message": "Research request filed. Results will appear on your dashboard in 3-5 minutes."
    }


@router.post("/complete")
def receive_research_complete(data: dict):
    """
    Receive completed research from file watcher.
    Store in database for dashboard display.
    """
    conn = get_db_conn()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO vetassist_research_results
            (veteran_id, session_id, job_id, question, answer, sources, completed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            data["veteran_id"],
            data["session_id"],
            data["job_id"],
            data["question"],
            data["answer"],
            json.dumps(data.get("sources", [])),
            data["completed_at"]
        ))
        conn.commit()
    conn.close()

    return {"status": "stored"}
```

### 5. Database Table

```sql
-- Run on bluefin
CREATE TABLE IF NOT EXISTS vetassist_research_results (
    id SERIAL PRIMARY KEY,
    veteran_id VARCHAR(100) NOT NULL,
    session_id VARCHAR(100),
    job_id VARCHAR(64),
    question TEXT,
    answer TEXT,
    sources JSONB DEFAULT '[]',
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_research_results_veteran ON vetassist_research_results(veteran_id);
```

---

## Data Flow

1. **VetAssist Chat** → POST `/api/v1/research/request`
2. **Backend** → Writes `/ganuda/research/requests/{veteran_id}-{uuid}.json`
3. **File Watcher** → Detects new file (5s old)
4. **File Watcher** → POST to `/v1/research/async`
5. **research-worker** → Runs ii-researcher
6. **research-worker** → Writes `/ganuda/research/completed/{job_id}.json`
7. **File Watcher** → Detects output file (60s old = complete)
8. **File Watcher** → POST to `/api/v1/research/complete`
9. **Backend** → Stores in `vetassist_research_results`
10. **Dashboard** → Queries and displays results

---

## Deployment

```bash
# Create directories
mkdir -p /ganuda/research/requests
mkdir -p /ganuda/research/completed
mkdir -p /ganuda/research/requests/processed

# Create database table
psql -h 192.168.132.222 -U claude -d zammad_production -f create_research_results.sql

# Deploy file watcher service
sudo ln -sf /ganuda/scripts/systemd/research-file-watcher.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable research-file-watcher
sudo systemctl start research-file-watcher
```

---

## Testing

```bash
# Drop a test request file
cat > /ganuda/research/requests/test-veteran-001.json << 'EOF'
{
  "veteran_id": "test-veteran",
  "session_id": "test-session",
  "question": "What is the VA rating for PTSD?",
  "condition": "PTSD"
}
EOF

# Watch the logs
journalctl -u research-file-watcher -f

# Check dashboard after 5 minutes
curl http://localhost:8000/api/v1/dashboard/test-veteran
```

---

FOR SEVEN GENERATIONS

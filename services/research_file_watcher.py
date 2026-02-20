#!/usr/bin/env python3
"""
Research File Watcher - Production async research integration.

Monitors for request files, triggers ii-researcher, waits for completion
(file 60s old), then posts results to VetAssist dashboard.

For Seven Generations - Cherokee AI Federation
"""

import os
import sys
import json
import time
import logging
import threading
import psycopg2
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

sys.path.insert(0, '/ganuda/lib')
from research_personas import build_research_query

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [FileWatcher] %(message)s'
)

# Configuration
REQUEST_DIR = Path("/ganuda/research/requests")
COMPLETED_DIR = Path("/ganuda/research/completed")
PROCESSED_DIR = Path("/ganuda/research/requests/processed")
GATEWAY_URL = os.environ.get("LLM_GATEWAY_URL", "http://localhost:8080")
API_KEY = os.environ.get("LLM_API_KEY", "ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5")

DB_CONFIG = {
    'host': os.environ.get('CHEROKEE_DB_HOST', '192.168.132.222'),
    'database': 'zammad_production',  # Fixed Jan 29, 2026 - was triad_federation, breaking VetAssist dashboard
    'user': 'claude',
    'password': os.environ.get('CHEROKEE_DB_PASS', '')
}

POLL_INTERVAL = 5  # seconds between scans
REQUEST_MIN_AGE = 5  # seconds - request file must be this old before processing
COMPLETION_AGE = 60  # seconds - output file must be this old to be considered complete
MAX_WAIT_TIME = 600  # seconds - maximum time to wait for completion

# Track jobs being monitored
active_monitors: Dict[str, threading.Thread] = {}


def get_db_conn():
    """Get database connection."""
    return psycopg2.connect(**DB_CONFIG)


def get_file_age(filepath: Path) -> float:
    """Get file age in seconds."""
    try:
        mtime = filepath.stat().st_mtime
        return time.time() - mtime
    except:
        return 0


def queue_research(query: str, max_steps: int = 5) -> Optional[str]:
    """Queue research job via LLM Gateway."""
    try:
        import requests
        response = requests.post(
            f"{GATEWAY_URL}/v1/research/async",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": API_KEY
            },
            json={
                "query": query,
                "max_steps": max_steps
            },
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("job_id")
        else:
            logging.error(f"Failed to queue research: {response.status_code} {response.text}")
            return None

    except Exception as e:
        logging.error(f"Queue research error: {e}")
        return None


def store_result(veteran_id: str, session_id: str, job_id: str,
                 question: str, answer: str, sources: list):
    """Store completed research in database for dashboard."""
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO vetassist_research_results
            (veteran_id, session_id, job_id, question, answer, sources, completed_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (job_id) DO UPDATE SET
                answer = EXCLUDED.answer,
                sources = EXCLUDED.sources,
                completed_at = NOW()
        """, (
            veteran_id,
            session_id,
            job_id,
            question,
            answer,
            json.dumps(sources) if sources else '[]'
        ))
        conn.commit()
        cur.close()
        conn.close()
        logging.info(f"Stored result for {job_id} -> veteran {veteran_id}")
        return True
    except Exception as e:
        logging.error(f"Store result error: {e}")
        return False


def monitor_completion(job_id: str, veteran_id: str, session_id: str, question: str):
    """Monitor for job completion in background thread."""
    output_file = COMPLETED_DIR / f"{job_id}.json"
    waited = 0

    logging.info(f"Monitoring {job_id} for completion...")

    while waited < MAX_WAIT_TIME:
        if output_file.exists():
            age = get_file_age(output_file)
            if age >= COMPLETION_AGE:
                logging.info(f"Job {job_id} complete (file age: {age:.0f}s)")

                try:
                    with open(output_file) as f:
                        result = json.load(f)

                    answer = result.get("answer", "")
                    sources = result.get("sources", [])

                    if answer and answer != "No answer generated. Try a more specific query.":
                        store_result(veteran_id, session_id, job_id, question, answer, sources)
                    else:
                        logging.warning(f"Job {job_id} returned empty answer")
                        store_result(veteran_id, session_id, job_id, question,
                                     "Research completed but no definitive answer found. Please try rephrasing your question.",
                                     sources)

                except Exception as e:
                    logging.error(f"Error reading result for {job_id}: {e}")

                # Cleanup
                if job_id in active_monitors:
                    del active_monitors[job_id]
                return

        time.sleep(10)
        waited += 10

        if waited % 60 == 0:
            logging.info(f"Still waiting for {job_id}... ({waited}s)")

    logging.error(f"Job {job_id} timed out after {MAX_WAIT_TIME}s")
    store_result(veteran_id, session_id, job_id, question,
                 "Research timed out. Please try again.", [])

    if job_id in active_monitors:
        del active_monitors[job_id]


def process_request_file(request_file: Path):
    """Process a research request file."""
    try:
        with open(request_file) as f:
            request = json.load(f)

        veteran_id = request.get("veteran_id", "unknown")
        session_id = request.get("session_id", "")
        question = request.get("question", "")
        condition = request.get("condition") or ""
        persona = request.get("persona", "default")
        max_steps = request.get("max_steps", 5)

        if not question:
            logging.error(f"Empty question in {request_file}")
            return

        # Build query with persona context
        base_question = f"{question} {condition}".strip() if condition else question
        query = build_research_query(base_question, persona)

        logging.info(f"Processing request [{persona}]: {question[:50]}... (veteran: {veteran_id})")

        # Queue research
        job_id = queue_research(query, max_steps)

        if not job_id:
            logging.error(f"Failed to queue research for {request_file}")
            return

        logging.info(f"Queued job {job_id}")

        # Move request file to processed
        PROCESSED_DIR.mkdir(exist_ok=True)
        processed_file = PROCESSED_DIR / f"{job_id}-{request_file.name}"
        request_file.rename(processed_file)

        # Start monitoring thread
        monitor_thread = threading.Thread(
            target=monitor_completion,
            args=(job_id, veteran_id, session_id, question),
            daemon=True
        )
        active_monitors[job_id] = monitor_thread
        monitor_thread.start()

    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in {request_file}: {e}")
    except Exception as e:
        logging.error(f"Error processing {request_file}: {e}")


def scan_requests():
    """Scan for new request files."""
    REQUEST_DIR.mkdir(exist_ok=True)

    for request_file in REQUEST_DIR.glob("*.json"):
        if request_file.is_file():
            age = get_file_age(request_file)
            if age >= REQUEST_MIN_AGE:
                process_request_file(request_file)


def main():
    logging.info("=" * 60)
    logging.info("Research File Watcher - Production")
    logging.info("=" * 60)
    logging.info(f"Request dir: {REQUEST_DIR}")
    logging.info(f"Completed dir: {COMPLETED_DIR}")
    logging.info(f"Gateway: {GATEWAY_URL}")
    logging.info(f"Poll interval: {POLL_INTERVAL}s")
    logging.info(f"Completion age threshold: {COMPLETION_AGE}s")
    logging.info("=" * 60)

    REQUEST_DIR.mkdir(exist_ok=True)
    COMPLETED_DIR.mkdir(exist_ok=True)
    PROCESSED_DIR.mkdir(exist_ok=True)

    while True:
        try:
            scan_requests()
            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            logging.info("Shutting down...")
            break
        except Exception as e:
            logging.error(f"Main loop error: {e}")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()

# Use centralized config (Jan 29, 2026)
import sys
sys.path.insert(0, '/ganuda/lib')
from vetassist_db_config import get_non_pii_connection, validate_on_startup

def get_db_conn():
    """Get database connection from centralized config."""
    return get_non_pii_connection()

# In main(), add validation:
def main():
    validate_on_startup()  # FAIL if tables missing
    # ... rest of main ...


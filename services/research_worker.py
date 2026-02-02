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
from datetime import datetime

# Add lib to path
sys.path.insert(0, '/ganuda/lib')

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
RESEARCH_TIMEOUT = 300.0  # 5 minutes


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
        RETURNING job_id, query, max_steps, output_file, callback_type, callback_target, requester_type, requester_id
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
    """, (summary[:500] if summary else "No summary", output_file, job_id))
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
    """, (error[:500] if error else "Unknown error", job_id))
    conn.commit()
    cur.close()
    conn.close()


def store_in_thermal_memory(job_id: str, query: str, answer: str, sources: list):
    """
    Store research result in thermal memory for future Council context.
    Research results start warm (70°) and decay over time.
    """
    try:
        import hashlib
        conn = get_conn()
        cur = conn.cursor()

        # Extract core question (strip persona prompt)
        core_question = query
        if '---' in query and 'Research Question:' in query:
            core_question = query.split('Research Question:')[-1].strip()

        # Create memory content (truncated for storage)
        source_urls = ', '.join(
            s.get('url', str(s)) if isinstance(s, dict) else str(s)
            for s in (sources or [])[:5]
        )
        memory_content = f"""RESEARCH: {core_question[:200]}

FINDINGS: {answer[:3000]}

SOURCES: {source_urls}"""

        # Generate memory hash
        memory_hash = hashlib.sha256(f"{job_id}-research".encode()).hexdigest()[:16]

        # Check if already stored (idempotent)
        cur.execute(
            "SELECT 1 FROM thermal_memory_archive WHERE memory_hash = %s",
            (memory_hash,)
        )
        if cur.fetchone():
            logging.info(f"Research {job_id} already in thermal memory")
            cur.close()
            conn.close()
            return

        # Compute integrity checksum
        content_checksum = hashlib.sha256(memory_content.encode('utf-8', errors='replace')).hexdigest()

        # Insert into thermal memory with checksum
        cur.execute("""
            INSERT INTO thermal_memory_archive
            (memory_hash, original_content, memory_type, temperature_score,
             context_tags, source_type, content_checksum, domain_tag, created_at)
            VALUES (%s, %s, 'research_result', 70.0, %s, 'ii-researcher', %s, 'research', NOW())
        """, (
            memory_hash,
            memory_content,
            json.dumps({
                'job_id': job_id,
                'question': core_question[:200],
                'source_count': len(sources) if sources else 0,
                'answer_length': len(answer) if answer else 0
            }),
            content_checksum
        ))

        conn.commit()
        cur.close()
        conn.close()

        logging.info(f"Stored research {job_id} in thermal memory (hash: {memory_hash})")

    except Exception as e:
        logging.error(f"Failed to store research in thermal memory: {e}")


def process_job(job_id, query, max_steps, output_file, callback_type, callback_target, requester_type=None, requester_id=None):
    """Process a research job."""
    logging.info(f"Processing job {job_id}: {query[:50]}...")

    try:
        from research_client import ResearchClient

        client = ResearchClient(timeout=RESEARCH_TIMEOUT)
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

        # Store in thermal memory for future Council context
        store_in_thermal_memory(job_id, query, result.answer, result.sources)

        # Handle callbacks
        if callback_type == "telegram" and callback_target:
            notify_telegram(callback_target, job_id, summary, output_file)

        # VetAssist sync - populate dashboard table
        if requester_type == "vetassist" and requester_id:
            notify_vetassist(job_id, query, result.answer, result.sources, requester_id)

    except Exception as e:
        fail_job(job_id, str(e))
        logging.error(f"Job {job_id} exception: {e}")


def notify_telegram(chat_id: str, job_id: str, summary: str, output_file: str):
    """Send Telegram notification when research is done."""
    try:
        import requests

        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            logging.warning("TELEGRAM_BOT_TOKEN not set, skipping notification")
            return

        # Try to load full answer from output file
        full_answer = summary
        try:
            with open(output_file) as f:
                data = json.load(f)
                full_answer = data.get("answer", summary)
        except:
            pass

        # Telegram message limit is 4096 chars
        MAX_LEN = 4000  # Leave room for header/footer

        # Send header
        header = f"📊 *Research Complete* (Job: {job_id})\n\n"
        requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": header, "parse_mode": "Markdown"},
            timeout=10
        )

        # Split answer into chunks and send
        chunks = [full_answer[i:i+MAX_LEN] for i in range(0, len(full_answer), MAX_LEN)]
        for i, chunk in enumerate(chunks[:10]):  # Max 10 messages (~40KB)
            requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={"chat_id": chat_id, "text": chunk},
                timeout=10
            )
            time.sleep(0.5)  # Rate limit protection

        if len(chunks) > 10:
            requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={"chat_id": chat_id, "text": f"_(Result truncated. Full output: {output_file})_", "parse_mode": "Markdown"},
                timeout=10
            )

        logging.info(f"Telegram notification sent to {chat_id} ({len(chunks)} chunks)")

    except Exception as e:
        logging.error(f"Telegram notification failed: {e}")


def notify_vetassist(job_id: str, query: str, answer: str, sources: list, requester_id: str):
    """Populate vetassist_research_results table for dashboard."""
    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO vetassist_research_results
                (veteran_id, job_id, question, answer, sources, completed_at, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            ON CONFLICT (job_id) DO UPDATE SET
                answer = EXCLUDED.answer,
                sources = EXCLUDED.sources,
                completed_at = NOW()
        """, (
            requester_id,
            job_id,
            query,
            answer,
            json.dumps(sources) if sources else '[]'
        ))

        conn.commit()
        cur.close()
        conn.close()

        logging.info(f"Synced research {job_id} to vetassist_research_results for veteran {requester_id}")

    except Exception as e:
        logging.error(f"Failed to sync to vetassist_research_results: {e}")


def main():
    logging.info("Research Worker starting...")
    logging.info(f"Poll interval: {POLL_INTERVAL}s")
    logging.info(f"Research timeout: {RESEARCH_TIMEOUT}s")

    # Ensure output directory exists
    os.makedirs("/ganuda/research/completed", exist_ok=True)

    while True:
        try:
            job = claim_job()
            if job:
                job_id, query, max_steps, output_file, cb_type, cb_target, req_type, req_id = job
                process_job(job_id, query, max_steps, output_file, cb_type, cb_target, req_type, req_id)
            else:
                time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            logging.info("Worker shutting down...")
            break
        except Exception as e:
            logging.error(f"Worker error: {e}")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()



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
from typing import Optional, Dict, Any, List

from lib.secrets_loader import get_db_config
DB_CONFIG = get_db_config()

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

        Args:
            query: Research question
            requester_type: 'telegram', 'vetassist', 'council', 'jr', 'api'
            requester_id: User/session identifier
            callback_type: 'telegram', 'webhook', 'file'
            callback_target: chat_id, webhook_url, or file path
            max_steps: Maximum research steps (default 5)

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

    def get_pending_jobs(self, limit: int = 10) -> List[Dict]:
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

    def get_completed_jobs(self, requester_type: str = None, limit: int = 10) -> List[Dict]:
        """Get recently completed jobs."""
        conn = self._get_conn()
        cur = conn.cursor()

        if requester_type:
            cur.execute("""
                SELECT job_id, query, status, result_summary, output_file, completed_at
                FROM research_jobs
                WHERE status = 'completed' AND requester_type = %s
                ORDER BY completed_at DESC
                LIMIT %s
            """, (requester_type, limit))
        else:
            cur.execute("""
                SELECT job_id, query, status, result_summary, output_file, completed_at
                FROM research_jobs
                WHERE status = 'completed'
                ORDER BY completed_at DESC
                LIMIT %s
            """, (limit,))

        rows = cur.fetchall()
        cur.close()
        conn.close()

        return [{"job_id": r[0], "query": r[1], "status": r[2],
                 "result_summary": r[3], "output_file": r[4],
                 "completed_at": r[5].isoformat() if r[5] else None} for r in rows]


# Convenience function for simple usage
def queue_research(query: str, requester: str = "api", requester_id: str = "anonymous") -> str:
    """Quick way to queue a research job."""
    dispatcher = ResearchDispatcher()
    return dispatcher.queue_research(
        query=query,
        requester_type=requester,
        requester_id=requester_id,
        max_steps=5
    )


def get_status(job_id: str) -> Optional[Dict]:
    """Quick way to get job status."""
    dispatcher = ResearchDispatcher()
    return dispatcher.get_job_status(job_id)


if __name__ == "__main__":
    # Self-test
    print("Research Dispatcher Self-Test")
    print("=" * 50)

    dispatcher = ResearchDispatcher()

    # Queue a test job
    job_id = dispatcher.queue_research(
        query="Test query",
        requester_type="test",
        requester_id="self-test"
    )
    print(f"Queued job: {job_id}")

    # Check status
    status = dispatcher.get_job_status(job_id)
    print(f"Status: {status}")

    # List pending
    pending = dispatcher.get_pending_jobs()
    print(f"Pending jobs: {len(pending)}")

    print("=" * 50)
    print("FOR SEVEN GENERATIONS")

#!/usr/bin/env python3
"""
Jr Queue Client - Interface for Jrs to interact with the work queue.

Provides:
- Claim tasks assigned to a specific Jr
- Update task status and progress
- Report results and artifacts
- Heartbeat updates

For Seven Generations - Cherokee AI Federation
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Optional, List, Dict, Any

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('CHEROKEE_DB_HOST', '192.168.132.222'),
    'database': os.environ.get('CHEROKEE_DB_NAME', 'zammad_production'),
    'user': os.environ.get('CHEROKEE_DB_USER', 'claude'),
    'password': os.environ.get('CHEROKEE_DB_PASS', 'jawaseatlasers2')
}


class JrQueueClient:
    """Client for Jr agents to interact with the work queue."""

    def __init__(self, jr_name: str):
        """
        Initialize the queue client for a specific Jr.

        Args:
            jr_name: The Jr's registered name (must exist in jr_status table)
        """
        self.jr_name = jr_name
        self._conn = None

    def _get_connection(self):
        """Get or create database connection."""
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(**DB_CONFIG)
        return self._conn

    def _execute(self, query: str, params: tuple = None, fetch: bool = True) -> Any:
        """Execute a query and optionally fetch results."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                if fetch:
                    result = cur.fetchall()
                    conn.commit()  # P0 FIX: Commit after SELECT to close transaction (Jan 27, 2026)
                    return result
                conn.commit()
                return cur.rowcount
        except Exception as e:
            conn.rollback()  # Rollback on error to release locks
            raise

    def heartbeat(self) -> bool:
        """
        Update Jr's last_seen timestamp.
        Should be called periodically while Jr is active.

        Returns:
            True if heartbeat was recorded
        """
        try:
            self._execute(
                "UPDATE jr_status SET last_seen = NOW(), is_online = TRUE WHERE jr_name = %s",
                (self.jr_name,),
                fetch=False
            )
            return True
        except Exception as e:
            print(f"[JrQueue] Heartbeat failed: {e}")
            return False

    def get_pending_tasks(self, limit: int = 10) -> List[Dict]:
        """
        Get pending tasks assigned to this Jr.

        Args:
            limit: Maximum number of tasks to return

        Returns:
            List of task dictionaries
        """
        return self._execute("""
            SELECT id, task_id, title, description, priority, sacred_fire_priority,
                   instruction_file, instruction_content, parameters,
                   seven_gen_impact, tags, created_at, use_rlm
            FROM jr_work_queue
            WHERE assigned_jr = %s
              AND status IN ('pending', 'assigned')
            ORDER BY sacred_fire_priority DESC, priority ASC, created_at ASC
            LIMIT %s
        """, (self.jr_name, limit))

    def claim_task(self, task_id: int) -> bool:
        """
        Claim a task and mark it as in_progress.

        Args:
            task_id: The task's database ID

        Returns:
            True if task was successfully claimed
        """
        try:
            rows = self._execute("""
                UPDATE jr_work_queue
                SET status = 'in_progress',
                    started_at = NOW(),
                    status_message = 'Task claimed by Jr'
                WHERE id = %s
                  AND assigned_jr = %s
                  AND status IN ('pending', 'assigned')
                RETURNING id
            """, (task_id, self.jr_name), fetch=True)
            return len(rows) > 0
        except Exception as e:
            print(f"[JrQueue] Failed to claim task {task_id}: {e}")
            return False

    def update_progress(self, task_id: int, percent: int, message: str = None) -> bool:
        """
        Update task progress.

        Args:
            task_id: The task's database ID
            percent: Progress percentage (0-100)
            message: Optional status message

        Returns:
            True if update succeeded
        """
        try:
            query = """
                UPDATE jr_work_queue
                SET progress_percent = %s
            """
            params = [percent]

            if message:
                query += ", status_message = %s"
                params.append(message)

            query += " WHERE id = %s AND assigned_jr = %s"
            params.extend([task_id, self.jr_name])

            self._execute(query, tuple(params), fetch=False)
            return True
        except Exception as e:
            print(f"[JrQueue] Failed to update progress: {e}")
            return False

    def complete_task(self, task_id: int, result: Dict = None, artifacts: List[str] = None) -> bool:
        """
        Mark a task as completed with results.

        Args:
            task_id: The task's database ID
            result: Optional result dictionary (will be stored as JSONB)
            artifacts: Optional list of file paths created

        Returns:
            True if task was marked complete
        """
        try:
            # Handle artifacts - extract paths if dicts, otherwise use as-is
            processed_artifacts = None
            if artifacts:
                processed_artifacts = []
                for a in artifacts:
                    if isinstance(a, dict):
                        # Extract path from dict artifact
                        processed_artifacts.append(a.get('path', str(a)))
                    else:
                        processed_artifacts.append(str(a))

            self._execute("""
                UPDATE jr_work_queue
                SET status = 'completed',
                    progress_percent = 100,
                    completed_at = NOW(),
                    result = %s,
                    artifacts = %s,
                    status_message = 'Task completed successfully'
                WHERE id = %s AND assigned_jr = %s
            """, (
                json.dumps(result) if result else None,
                processed_artifacts,
                task_id,
                self.jr_name
            ), fetch=False)
            return True
        except Exception as e:
            print(f"[JrQueue] Failed to complete task: {e}")
            return False

    def fail_task(self, task_id: int, error_message: str, result: Dict = None) -> bool:
        """
        Mark a task as failed with error details.

        Args:
            task_id: The task's database ID
            error_message: Description of what went wrong
            result: Optional partial result dictionary

        Returns:
            True if task was marked failed
        """
        try:
            self._execute("""
                UPDATE jr_work_queue
                SET status = 'failed',
                    completed_at = NOW(),
                    error_message = %s,
                    result = %s,
                    status_message = 'Task failed'
                WHERE id = %s AND assigned_jr = %s
            """, (
                error_message,
                json.dumps(result) if result else None,
                task_id,
                self.jr_name
            ), fetch=False)
            return True
        except Exception as e:
            print(f"[JrQueue] Failed to mark task failed: {e}")
            return False

    def block_task(self, task_id: int, reason: str) -> bool:
        """
        Mark a task as blocked (needs intervention).

        Args:
            task_id: The task's database ID
            reason: Why the task is blocked

        Returns:
            True if task was marked blocked
        """
        try:
            self._execute("""
                UPDATE jr_work_queue
                SET status = 'blocked',
                    status_message = %s
                WHERE id = %s AND assigned_jr = %s
            """, (f"BLOCKED: {reason}", task_id, self.jr_name), fetch=False)
            return True
        except Exception as e:
            print(f"[JrQueue] Failed to block task: {e}")
            return False

    def get_my_workload(self) -> Dict:
        """
        Get this Jr's current workload summary.

        Returns:
            Dictionary with task counts by status
        """
        result = self._execute("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'in_progress') as active,
                COUNT(*) FILTER (WHERE status IN ('pending', 'assigned')) as queued,
                COUNT(*) FILTER (WHERE status = 'completed' AND completed_at > NOW() - INTERVAL '24 hours') as completed_24h,
                COUNT(*) FILTER (WHERE status = 'blocked') as blocked
            FROM jr_work_queue
            WHERE assigned_jr = %s
        """, (self.jr_name,))
        return dict(result[0]) if result else {}

    def close(self):
        """Close database connection."""
        if self._conn and not self._conn.closed:
            self._conn.close()


# Convenience functions for simple scripts
def get_client(jr_name: str) -> JrQueueClient:
    """Create a new queue client for a Jr."""
    return JrQueueClient(jr_name)


if __name__ == "__main__":
    # Self-test
    print("Jr Queue Client Self-Test")
    print("=" * 50)

    client = JrQueueClient("Software Engineer Jr.")

    # Test heartbeat
    print(f"Heartbeat: {client.heartbeat()}")

    # Test get workload
    workload = client.get_my_workload()
    print(f"Workload: {workload}")

    # Test get pending tasks
    tasks = client.get_pending_tasks()
    print(f"Pending tasks: {len(tasks)}")

    client.close()
    print("=" * 50)
    print("Self-test complete - For Seven Generations")
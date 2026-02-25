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

# Database configuration - loaded from secrets
import sys
sys.path.insert(0, '/ganuda')
from lib.secrets_loader import get_db_config
DB_CONFIG = get_db_config()


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

    def reap_stale_tasks(self, timeout_minutes: int = 10) -> int:
        """
        Reset tasks stuck in_progress for longer than timeout.
        Called before get_pending_tasks to recover from executor crashes.
        Returns number of tasks reset.
        """
        try:
            rows = self._execute(f"""
                UPDATE jr_work_queue
                SET status = 'pending',
                    started_at = NULL,
                    status_message = 'Reset by reaper (stale in_progress > {timeout_minutes} min)'
                WHERE assigned_jr = %s
                  AND status = 'in_progress'
                  AND started_at < NOW() - INTERVAL '{timeout_minutes} minutes'
                RETURNING id, title
            """, (self.jr_name,))
            if rows:
                for r in rows:
                    print(f"[Reaper] Reset stale task #{r['id']}: {r['title']}")
            return len(rows) if rows else 0
        except Exception as e:
            print(f"[Reaper] Error: {e}")
            return 0

    def get_pending_tasks(self, limit: int = 10) -> List[Dict]:
        """
        Atomically claim pending tasks assigned to this Jr.

        Uses FOR UPDATE SKIP LOCKED to prevent race conditions when
        multiple workers poll simultaneously. Tasks are moved to
        'in_progress' status in the same transaction as the SELECT.

        TPM-deployed: Feb 3, 2026 (Ultrathink: 95% Solution Phase A)

        Args:
            limit: Maximum number of tasks to return

        Returns:
            List of claimed task dictionaries (already in_progress)
        """
        return self._execute("""
            UPDATE jr_work_queue
            SET status = 'in_progress',
                started_at = COALESCE(started_at, NOW()),
                status_message = 'Claimed by worker'
            WHERE id IN (
                SELECT id
                FROM jr_work_queue
                WHERE assigned_jr = %s
                  AND status IN ('pending', 'assigned')
                ORDER BY sacred_fire_priority DESC, priority ASC, created_at ASC
                LIMIT %s
                FOR UPDATE SKIP LOCKED
            )
            RETURNING id, task_id, title, description, priority, sacred_fire_priority,
                      instruction_file, instruction_content, parameters,
                      seven_gen_impact, tags, created_at, use_rlm, assigned_jr
        """, (self.jr_name, limit))

    def claim_task(self, task_id: int) -> bool:
        """
        Verify a task is claimed and in_progress for this Jr.

        Note: As of Feb 2026, get_pending_tasks() atomically claims tasks
        via FOR UPDATE SKIP LOCKED. This method serves as verification
        and backward-compatibility for direct claim requests.

        Args:
            task_id: The task's database ID

        Returns:
            True if task is in_progress and assigned to this Jr
        """
        try:
            rows = self._execute("""
                UPDATE jr_work_queue
                SET status = 'in_progress',
                    started_at = COALESCE(started_at, NOW()),
                    status_message = 'Task claimed by Jr'
                WHERE id = %s
                  AND assigned_jr = %s
                  AND status IN ('pending', 'assigned', 'in_progress')
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

            # Record completion analytics
            try:
                self._execute("""
                    INSERT INTO jr_task_completions
                        (task_id, agent_id, actual_duration, success)
                    SELECT
                        id::text,
                        assigned_jr,
                        NOW() - started_at,
                        true
                    FROM jr_work_queue
                    WHERE id = %s AND assigned_jr = %s
                """, (task_id, self.jr_name), fetch=False)
            except Exception:
                pass  # completion tracking is non-critical

            # TEG child completion hook: unblock dependents + check parent
            # Council Vote #ec088d89 — OpenSage Diamond 1
            try:
                self._teg_child_hook(task_id)
            except Exception:
                pass  # TEG tracking is non-critical

            return True
        except Exception as e:
            print(f"[JrQueue] Failed to complete task: {e}")
            return False

    def _teg_child_hook(self, task_id: int):
        """When a TEG child completes, unblock dependents and check parent."""
        # Get this task's TEG metadata
        rows = self._execute("""
            SELECT parent_task_id, parameters FROM jr_work_queue WHERE id = %s
        """, (task_id,))
        if not rows:
            return
        row = rows[0]
        parent_id = row['parent_task_id']
        params = row['parameters']
        if not parent_id:
            return
        params = json.loads(params) if isinstance(params, str) else (params or {})
        my_node_id = params.get('teg_node_id')
        if not my_node_id:
            return  # Not a TEG child

        print(f"[TEG] Child hook fired for node {my_node_id} (task {task_id})")

        # Unblock siblings whose deps include my node_id
        siblings = self._execute("""
            SELECT id, parameters FROM jr_work_queue
            WHERE parent_task_id = %s AND status = 'blocked'
        """, (parent_id,))

        for sib in (siblings or []):
            sib_id = sib['id']
            sib_params = sib['parameters']
            sp = json.loads(sib_params) if isinstance(sib_params, str) else (sib_params or {})
            deps = sp.get('teg_deps', [])
            if my_node_id not in deps:
                continue
            # Check if ALL deps for this sibling are now completed
            all_done = True
            for dep_node_id in deps:
                dep_rows = self._execute("""
                    SELECT status FROM jr_work_queue
                    WHERE parent_task_id = %s
                      AND parameters->>'teg_node_id' = %s
                """, (parent_id, dep_node_id))
                if not dep_rows or dep_rows[0]['status'] != 'completed':
                    all_done = False
                    break
            if all_done:
                self._execute("""
                    UPDATE jr_work_queue SET status = 'pending',
                        status_message = 'TEG: dependencies resolved, unblocked'
                    WHERE id = %s
                """, (sib_id,), fetch=False)
                print(f"[TEG] Unblocked node {sib_id} (all deps resolved)")

        # Check if ALL children of parent are complete
        remaining = self._execute("""
            SELECT COUNT(*) as cnt FROM jr_work_queue
            WHERE parent_task_id = %s AND status NOT IN ('completed', 'cancelled')
        """, (parent_id,))
        if remaining and remaining[0]['cnt'] == 0:
            # All children done — auto-complete the parent
            self._execute("""
                UPDATE jr_work_queue SET status = 'completed',
                    progress_percent = 100,
                    completed_at = NOW(),
                    status_message = 'TEG: all child nodes completed'
                WHERE id = %s
            """, (parent_id,), fetch=False)
            print(f"[TEG] Parent task {parent_id} auto-completed (all children done)")

    def _teg_child_fail_hook(self, task_id: int):
        """When a TEG child fails, cancel downstream dependents and fail parent."""
        rows = self._execute("""
            SELECT parent_task_id, parameters FROM jr_work_queue WHERE id = %s
        """, (task_id,))
        if not rows:
            return
        row = rows[0]
        parent_id = row['parent_task_id']
        params = row['parameters']
        if not parent_id:
            return
        params = json.loads(params) if isinstance(params, str) else (params or {})
        my_node_id = params.get('teg_node_id')
        if not my_node_id:
            return

        # Cancel any blocked siblings that depend on me
        siblings = self._execute("""
            SELECT id, parameters FROM jr_work_queue
            WHERE parent_task_id = %s AND status = 'blocked'
        """, (parent_id,))

        cancelled = []
        for sib in (siblings or []):
            sib_id = sib['id']
            sib_params = sib['parameters']
            sp = json.loads(sib_params) if isinstance(sib_params, str) else (sib_params or {})
            deps = sp.get('teg_deps', [])
            if my_node_id in deps:
                self._execute("""
                    UPDATE jr_work_queue SET status = 'cancelled',
                        status_message = %s
                    WHERE id = %s
                """, (
                    f'TEG: cancelled — dependency {my_node_id} failed',
                    sib_id
                ), fetch=False)
                cancelled.append(sib_id)
                print(f"[TEG] Cancelled node {sib_id} (dependency {my_node_id} failed)")

        # Check remaining active children
        remaining = self._execute("""
            SELECT COUNT(*) as cnt FROM jr_work_queue
            WHERE parent_task_id = %s AND status NOT IN ('completed', 'cancelled', 'failed')
        """, (parent_id,))

        if remaining and remaining[0]['cnt'] == 0:
            # No more active children — fail the parent with summary
            completed = self._execute("""
                SELECT COUNT(*) as cnt FROM jr_work_queue
                WHERE parent_task_id = %s AND status = 'completed'
            """, (parent_id,))
            total = self._execute("""
                SELECT COUNT(*) as cnt FROM jr_work_queue
                WHERE parent_task_id = %s
            """, (parent_id,))

            c_count = completed[0]['cnt'] if completed else 0
            t_count = total[0]['cnt'] if total else 0

            self._execute("""
                UPDATE jr_work_queue SET status = 'failed',
                    completed_at = NOW(),
                    error_message = %s,
                    status_message = 'TEG: partial failure'
                WHERE id = %s
            """, (
                f'TEG partial failure: {c_count}/{t_count} nodes completed. '
                f'Failed node: {my_node_id}. Cancelled: {cancelled}',
                parent_id
            ), fetch=False)
            print(f"[TEG] Parent {parent_id} failed ({c_count}/{t_count} nodes completed)")

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

            # TEG child failure hook: cancel dependents + check parent
            try:
                self._teg_child_fail_hook(task_id)
            except Exception:
                pass  # TEG tracking is non-critical

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

    def get_dlq_summary(self) -> Dict:
        """Get Dead Letter Queue summary for monitoring."""
        result = self._execute("""
            SELECT
                COUNT(*) FILTER (WHERE d.resolution_status = 'unresolved') as unresolved,
                COUNT(*) FILTER (WHERE d.resolution_status = 'retrying') as retrying,
                COUNT(*) FILTER (WHERE d.escalation_level = 2) as escalated_tpm,
                COUNT(*) FILTER (WHERE d.escalation_level = 3) as escalated_council,
                COUNT(*) FILTER (WHERE d.resolution_status = 'resolved') as resolved
            FROM jr_failed_tasks_dlq d
        """)
        return dict(result[0]) if result else {}

    def requeue_from_dlq(self, task_id: int) -> bool:
        """Re-queue a failed task by resetting its status to pending."""
        try:
            self._execute("""
                UPDATE jr_work_queue
                SET status = 'pending',
                    error_message = NULL,
                    started_at = NULL,
                    completed_at = NULL,
                    progress_percent = 0,
                    status_message = 'Re-queued from DLQ'
                WHERE id = %s
            """, (task_id,), fetch=False)
            return True
        except Exception as e:
            print(f"[JrQueue] Failed to requeue task {task_id} from DLQ: {e}")
            return False

    def save_checkpoint(self, task_id: int, last_completed_step: int,
                        total_steps: int = None, checkpoint_data: Dict = None) -> bool:
        """Save a checkpoint for a task so it can resume on retry."""
        try:
            self._execute("""
                INSERT INTO jr_task_checkpoints
                    (task_id, last_completed_step, total_steps, checkpoint_data)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (task_id) DO UPDATE SET
                    last_completed_step = EXCLUDED.last_completed_step,
                    total_steps = COALESCE(EXCLUDED.total_steps, jr_task_checkpoints.total_steps),
                    checkpoint_data = EXCLUDED.checkpoint_data,
                    updated_at = NOW()
            """, (
                task_id,
                last_completed_step,
                total_steps,
                json.dumps(checkpoint_data) if checkpoint_data else None,
            ), fetch=False)
            return True
        except Exception as e:
            print(f"[JrQueue] Failed to save checkpoint for task {task_id}: {e}")
            return False

    def get_last_checkpoint(self, task_id: int) -> Optional[Dict]:
        """Get the last checkpoint for a task (for resume-from-failure)."""
        try:
            rows = self._execute("""
                SELECT last_completed_step, total_steps, checkpoint_data
                FROM jr_task_checkpoints
                WHERE task_id = %s
            """, (task_id,))
            if rows:
                return dict(rows[0])
            return None
        except Exception as e:
            print(f"[JrQueue] Failed to get checkpoint for task {task_id}: {e}")
            return None

    def cleanup_checkpoints(self, task_id: int) -> bool:
        """Remove checkpoints after a task completes successfully."""
        try:
            self._execute("""
                DELETE FROM jr_task_checkpoints WHERE task_id = %s
            """, (task_id,), fetch=False)
            return True
        except Exception as e:
            print(f"[JrQueue] Failed to cleanup checkpoints for task {task_id}: {e}")
            return False

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
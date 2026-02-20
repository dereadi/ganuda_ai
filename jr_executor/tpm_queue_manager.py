#!/usr/bin/env python3
"""
TPM Queue Manager - Tools for the TPM to manage the Jr work queue.

Provides:
- Add new tasks to the queue
- Reassign tasks between Jrs
- View queue status
- Cancel tasks

For Seven Generations - Cherokee AI Federation
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, List, Dict, Any

DB_CONFIG = {
    'host': os.environ.get('CHEROKEE_DB_HOST', '192.168.132.222'),
    'database': os.environ.get('CHEROKEE_DB_NAME', 'zammad_production'),
    'user': os.environ.get('CHEROKEE_DB_USER', 'claude'),
    'password': os.environ.get('CHEROKEE_DB_PASS', '')
}


class TPMQueueManager:
    """Manager for TPM to control the Jr work queue."""

    def __init__(self):
        self._conn = None

    def _get_connection(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(**DB_CONFIG)
        return self._conn

    def _execute(self, query: str, params: tuple = None, fetch: bool = True) -> Any:
        conn = self._get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if fetch:
                return cur.fetchall()
            conn.commit()
            return cur.rowcount

    def add_task(
        self,
        title: str,
        assigned_jr: str,
        description: str = None,
        priority: int = 5,
        sacred_fire: bool = False,
        instruction_file: str = None,
        instruction_content: str = None,
        parameters: Dict = None,
        seven_gen_impact: str = None,
        tags: List[str] = None,
        assigned_mountain: str = None,
        requires_council: bool = False,
        parent_task_id: int = None
    ) -> int:
        """
        Add a new task to the queue.

        Args:
            title: Short task title
            assigned_jr: Jr name to assign task to
            description: Detailed description
            priority: 1-10 (lower = higher priority)
            sacred_fire: True if urgent/constitutional priority
            instruction_file: Path to instruction markdown file
            instruction_content: Inline instructions (if no file)
            parameters: Task-specific parameters dict
            seven_gen_impact: How this serves seven generations
            tags: List of tags for categorization
            assigned_mountain: Mountain the Jr is on
            requires_council: Whether council approval needed
            parent_task_id: ID of parent task (for subtasks)

        Returns:
            ID of created task
        """
        result = self._execute("""
            INSERT INTO jr_work_queue (
                title, description, assigned_jr, assigned_mountain,
                priority, sacred_fire_priority,
                instruction_file, instruction_content, parameters,
                seven_gen_impact, tags,
                requires_council_approval, parent_task_id
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING id
        """, (
            title, description, assigned_jr, assigned_mountain,
            priority, sacred_fire,
            instruction_file, instruction_content,
            json.dumps(parameters) if parameters else None,
            seven_gen_impact, tags,
            requires_council, parent_task_id
        ))
        return result[0]['id'] if result else None

    def get_queue_status(self) -> List[Dict]:
        """Get full queue status summary."""
        return self._execute("""
            SELECT * FROM jr_work_queue_pending
        """)

    def get_jr_workloads(self) -> List[Dict]:
        """Get workload for all Jrs."""
        return self._execute("""
            SELECT * FROM jr_workload
        """)

    def reassign_task(self, task_id: int, new_jr: str, new_mountain: str = None) -> bool:
        """Reassign a task to a different Jr."""
        try:
            self._execute("""
                UPDATE jr_work_queue
                SET assigned_jr = %s,
                    assigned_mountain = COALESCE(%s, assigned_mountain),
                    status = 'pending',
                    assigned_at = NULL,
                    started_at = NULL,
                    status_message = 'Task reassigned by TPM'
                WHERE id = %s
            """, (new_jr, new_mountain, task_id), fetch=False)
            return True
        except Exception as e:
            print(f"[TPMQueue] Reassign failed: {e}")
            return False

    def cancel_task(self, task_id: int, reason: str = None) -> bool:
        """Cancel a task."""
        try:
            self._execute("""
                UPDATE jr_work_queue
                SET status = 'cancelled',
                    completed_at = NOW(),
                    status_message = %s
                WHERE id = %s
            """, (f"Cancelled: {reason}" if reason else "Cancelled by TPM", task_id), fetch=False)
            return True
        except Exception as e:
            print(f"[TPMQueue] Cancel failed: {e}")
            return False

    def get_blocked_tasks(self) -> List[Dict]:
        """Get all blocked tasks that need attention."""
        return self._execute("""
            SELECT id, task_id, title, assigned_jr, status_message, created_at
            FROM jr_work_queue
            WHERE status = 'blocked'
            ORDER BY created_at ASC
        """)

    def unblock_task(self, task_id: int, message: str = None) -> bool:
        """Unblock a task and set it back to pending."""
        try:
            self._execute("""
                UPDATE jr_work_queue
                SET status = 'pending',
                    status_message = %s
                WHERE id = %s AND status = 'blocked'
            """, (message or "Unblocked by TPM", task_id), fetch=False)
            return True
        except Exception as e:
            print(f"[TPMQueue] Unblock failed: {e}")
            return False

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()


if __name__ == "__main__":
    print("TPM Queue Manager Self-Test")
    print("=" * 50)

    mgr = TPMQueueManager()

    print("\nQueue Status:")
    for task in mgr.get_queue_status():
        print(f"  [{task['priority_label']}] {task['title']} -> {task['assigned_jr']}")

    print("\nJr Workloads:")
    for jr in mgr.get_jr_workloads():
        if jr['queued_tasks'] > 0 or jr['active_tasks'] > 0:
            print(f"  {jr['jr_name']}: {jr['active_tasks']} active, {jr['queued_tasks']} queued")

    print("\nBlocked Tasks:")
    blocked = mgr.get_blocked_tasks()
    if blocked:
        for task in blocked:
            print(f"  [{task['id']}] {task['title']} - {task['status_message']}")
    else:
        print("  None")

    mgr.close()
    print("=" * 50)
    print("Self-test complete - For Seven Generations")
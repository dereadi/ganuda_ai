#!/usr/bin/env python3
"""
Thermal Memory Queue Poller for Jr Executor
Enables Jr to receive tasks written to jr_task_history by Telegram/Chief
"""

import psycopg2
import uuid
from datetime import datetime
from typing import List, Dict, Optional
import os

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'triad_federation',
    'user': 'claude',
    'password': os.environ.get('CHEROKEE_DB_PASS', '')
}


class ThermalQueuePoller:
    """Polls jr_task_history for pending tasks assigned via thermal memory"""

    def __init__(self, jr_name: str = 'it_triad_jr'):
        self.jr_name = jr_name
        self.db_config = DB_CONFIG

    def _get_connection(self):
        return psycopg2.connect(**self.db_config)

    def get_pending_tasks(self, limit: int = 5) -> List[Dict]:
        """Get tasks assigned to this Jr that haven't been started"""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute('''
                SELECT
                    id::text, task_id, task_type, task_description,
                    task_complexity, assigned_by, thermal_memory_id::text
                FROM jr_task_history
                WHERE jr_name = %s
                  AND outcome IS NULL
                  AND started_at IS NULL
                ORDER BY task_complexity DESC, assigned_at ASC
                LIMIT %s
            ''', (self.jr_name, limit))
            rows = cur.fetchall()
            cur.close()
            conn.close()

            return [{
                'id': row[0],
                'task_id': row[1],
                'task_type': row[2],
                'description': row[3],
                'complexity': row[4],
                'assigned_by': row[5],
                'thermal_memory_id': row[6]
            } for row in rows]
        except Exception as e:
            print(f"Error getting pending tasks: {e}")
            return []

    def claim_task(self, task_id: str) -> bool:
        """Mark task as started by this Jr"""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute('''
                UPDATE jr_task_history
                SET started_at = NOW()
                WHERE id = %s::uuid AND started_at IS NULL
                RETURNING id
            ''', (task_id,))
            result = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()
            return result is not None
        except Exception as e:
            print(f"Error claiming task: {e}")
            return False

    def complete_task(self, task_id: str, outcome: str, description: str = None) -> bool:
        """Mark task as completed with outcome"""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute('''
                UPDATE jr_task_history
                SET completed_at = NOW(),
                    outcome = %s,
                    outcome_description = %s,
                    duration_seconds = EXTRACT(EPOCH FROM (NOW() - started_at))::int
                WHERE id = %s::uuid
                RETURNING id
            ''', (outcome, description, task_id))
            result = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()
            return result is not None
        except Exception as e:
            print(f"Error completing task: {e}")
            return False

    def get_thermal_mission_content(self, thermal_id: str) -> Optional[str]:
        """Get mission content from thermal memory"""
        if not thermal_id:
            return None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute('''
                SELECT content FROM triad_shared_memories
                WHERE id = %s::uuid
            ''', (thermal_id,))
            row = cur.fetchone()
            cur.close()
            conn.close()
            return row[0] if row else None
        except Exception as e:
            print(f"Error getting thermal content: {e}")
            return None

    def write_status_update(self, task_id: str, status: str, details: str = None):
        """Write status update to thermal memory for Telegram notification"""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            content = f"JR_STATUS_UPDATE|task_id:{task_id}|status:{status}"
            if details:
                content += f"|details:{details[:500]}"
            cur.execute('''
                INSERT INTO triad_shared_memories
                (content, temperature, source_triad, tags, created_at)
                VALUES (%s, %s, %s, %s, NOW())
            ''', (
                content,
                75,  # Medium-high temperature for notifications
                self.jr_name,
                ['jr_status', 'telegram_notify', task_id]
            ))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Error writing status: {e}")


def poll_and_process(jr_name: str = 'it_triad_jr'):
    """Main polling loop - call from Jr executor"""
    poller = ThermalQueuePoller(jr_name)
    tasks = poller.get_pending_tasks(limit=3)

    print(f"[ThermalQueue] Found {len(tasks)} pending tasks")

    for task in tasks:
        print(f"  - {task['task_id']}: {task['task_type']} (complexity: {task['complexity']})")

        # If task has thermal memory link, get the content
        if task.get('thermal_memory_id'):
            content = poller.get_thermal_mission_content(task['thermal_memory_id'])
            if content:
                print(f"    Thermal content: {content[:100]}...")

    return tasks


if __name__ == '__main__':
    tasks = poll_and_process()
    if tasks:
        print(f"\nReady to process {len(tasks)} tasks from thermal queue")
    else:
        print("\nNo pending tasks in thermal queue")
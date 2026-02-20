#!/usr/bin/env python3
"""
Task Assigner for Telegram Chief
Enables Telegram bot (LLM) to assign tasks to Jr via jr_task_history table
"""

import psycopg2
import uuid
import json
from datetime import datetime
from typing import Dict, Optional, List
import os

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'triad_federation',
    'user': 'claude',
    'password': os.environ.get('CHEROKEE_DB_PASS', '')
}

# Task types that can be auto-assigned without human confirmation
AUTO_ASSIGN_TYPES = [
    'file_creation',      # Creating new files
    'monitoring_script',  # Creating monitoring scripts
    'data_analysis',      # Running analysis queries
    'status_check',       # System status checks
    'report_generation',  # Generating reports
]

# Task types requiring human confirmation
CONFIRM_REQUIRED_TYPES = [
    'file_modification',  # Changing existing files
    'service_restart',    # Restarting services
    'config_change',      # Configuration changes
    'deployment',         # Any deployment action
]

# Never auto-assign these
FORBIDDEN_TYPES = [
    'delete_file',
    'drop_table',
    'credential_change',
    'production_deploy',
]


class TaskAssigner:
    """Assigns tasks from Telegram to Jr via jr_task_history"""

    def __init__(self):
        self.db_config = DB_CONFIG

    def _get_connection(self):
        return psycopg2.connect(**self.db_config)

    def classify_task(self, description: str) -> Dict:
        """Classify task type from description"""
        desc_lower = description.lower()

        # Check for forbidden patterns
        for forbidden in FORBIDDEN_TYPES:
            if forbidden.replace('_', ' ') in desc_lower:
                return {
                    'task_type': forbidden,
                    'can_auto_assign': False,
                    'forbidden': True,
                    'reason': f'Task type "{forbidden}" requires human execution'
                }

        # Check for confirmation required
        for confirm_type in CONFIRM_REQUIRED_TYPES:
            if confirm_type.replace('_', ' ') in desc_lower:
                return {
                    'task_type': confirm_type,
                    'can_auto_assign': False,
                    'forbidden': False,
                    'reason': f'Task type "{confirm_type}" requires human confirmation'
                }

        # Check for auto-assignable patterns
        if any(word in desc_lower for word in ['create', 'write', 'generate', 'new']):
            if 'script' in desc_lower or 'monitor' in desc_lower:
                return {'task_type': 'monitoring_script', 'can_auto_assign': True}
            elif 'file' in desc_lower or '.py' in desc_lower:
                return {'task_type': 'file_creation', 'can_auto_assign': True}
            elif 'report' in desc_lower:
                return {'task_type': 'report_generation', 'can_auto_assign': True}

        if any(word in desc_lower for word in ['check', 'status', 'health', 'verify']):
            return {'task_type': 'status_check', 'can_auto_assign': True}

        if any(word in desc_lower for word in ['analyze', 'query', 'count', 'summarize']):
            return {'task_type': 'data_analysis', 'can_auto_assign': True}

        # Default: general task, can auto-assign with low complexity
        return {'task_type': 'general', 'can_auto_assign': True}

    def calculate_complexity(self, description: str, task_type: str) -> float:
        """Calculate task complexity (0.0 to 1.0)"""
        complexity = 0.3  # Base complexity

        # Length adds complexity
        if len(description) > 200:
            complexity += 0.1
        if len(description) > 500:
            complexity += 0.1

        # Certain keywords increase complexity
        high_complexity_words = ['multiple', 'several', 'all', 'batch', 'recursive']
        for word in high_complexity_words:
            if word in description.lower():
                complexity += 0.1

        # Task type affects complexity
        if task_type in ['monitoring_script', 'report_generation']:
            complexity += 0.2
        elif task_type in ['data_analysis']:
            complexity += 0.15

        return min(1.0, complexity)

    def assign_task(
        self,
        description: str,
        jr_name: str = 'it_triad_jr',
        requester: str = 'telegram_chief',
        thermal_memory_id: str = None
    ) -> Dict:
        """
        Assign a task to Jr

        Returns dict with:
        - success: bool
        - task_id: str (if successful)
        - reason: str (if failed)
        - requires_confirmation: bool
        """
        # Classify the task
        classification = self.classify_task(description)

        if classification.get('forbidden'):
            return {
                'success': False,
                'reason': classification['reason'],
                'forbidden': True
            }

        if not classification.get('can_auto_assign'):
            return {
                'success': False,
                'requires_confirmation': True,
                'reason': classification['reason'],
                'task_type': classification['task_type']
            }

        # Calculate complexity
        complexity = self.calculate_complexity(description, classification['task_type'])

        # Generate task ID
        task_id = f"TG-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"

        try:
            conn = self._get_connection()
            cur = conn.cursor()

            cur.execute('''
                INSERT INTO jr_task_history (
                    id, task_id, jr_name, task_type, task_description,
                    task_complexity, assigned_by, assigned_at,
                    thermal_memory_id, created_at
                ) VALUES (
                    gen_random_uuid(), %s, %s, %s, %s,
                    %s, %s, NOW(),
                    %s, NOW()
                )
                RETURNING id::text
            ''', (
                task_id,
                jr_name,
                classification['task_type'],
                description,
                complexity,
                requester,
                thermal_memory_id
            ))

            result_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()

            # Also write to thermal memory for audit trail
            self._log_assignment(task_id, description, jr_name, requester)

            return {
                'success': True,
                'task_id': task_id,
                'db_id': result_id,
                'task_type': classification['task_type'],
                'complexity': complexity,
                'jr_name': jr_name
            }

        except Exception as e:
            return {
                'success': False,
                'reason': f'Database error: {str(e)}'
            }

    def _log_assignment(self, task_id: str, description: str, jr_name: str, requester: str):
        """Log task assignment to thermal memory"""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO triad_shared_memories
                (content, temperature, source_triad, tags, created_at)
                VALUES (%s, %s, %s, %s, NOW())
            ''', (
                f"Task assigned: {task_id}\\nJr: {jr_name}\\nDescription: {description[:200]}",
                70,
                requester,
                ['task_assignment', 'telegram_tpm', jr_name, task_id]
            ))
            conn.commit()
            cur.close()
            conn.close()
        except Exception:
            pass  # Don't fail assignment if logging fails

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get status of an assigned task"""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute('''
                SELECT task_id, task_type, jr_name, outcome, outcome_description,
                       assigned_at, started_at, completed_at, duration_seconds
                FROM jr_task_history
                WHERE task_id = %s
            ''', (task_id,))
            row = cur.fetchone()
            cur.close()
            conn.close()

            if not row:
                return None

            status = 'pending'
            if row[6]:  # started_at
                status = 'in_progress'
            if row[7]:  # completed_at
                status = 'completed'

            return {
                'task_id': row[0],
                'task_type': row[1],
                'jr_name': row[2],
                'outcome': row[3],
                'outcome_description': row[4],
                'assigned_at': row[5].isoformat() if row[5] else None,
                'started_at': row[6].isoformat() if row[6] else None,
                'completed_at': row[7].isoformat() if row[7] else None,
                'duration_seconds': row[8],
                'status': status
            }
        except Exception as e:
            return {'error': str(e)}

    def get_pending_assignments(self, limit: int = 10) -> List[Dict]:
        """Get list of pending task assignments"""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute('''
                SELECT task_id, task_type, jr_name, task_description, assigned_at
                FROM jr_task_history
                WHERE outcome IS NULL
                ORDER BY assigned_at DESC
                LIMIT %s
            ''', (limit,))
            rows = cur.fetchall()
            cur.close()
            conn.close()

            return [{
                'task_id': row[0],
                'task_type': row[1],
                'jr_name': row[2],
                'description': row[3][:100] + '...' if len(row[3]) > 100 else row[3],
                'assigned_at': row[4].isoformat() if row[4] else None
            } for row in rows]
        except Exception as e:
            return []


# Convenience function for Telegram bot
def assign_to_jr(description: str, requester: str = 'telegram_chief') -> Dict:
    """Simple interface for Telegram bot to assign tasks"""
    assigner = TaskAssigner()
    return assigner.assign_task(description, requester=requester)


if __name__ == '__main__':
    # Test the assigner
    assigner = TaskAssigner()

    test_tasks = [
        "Create a monitoring script to check disk space on all servers",
        "Delete all log files older than 30 days",
        "Generate a report of email statistics for December",
        "Restart the web server",
        "Check the status of all running services"
    ]

    print("Task Classification Test:")
    print("=" * 60)
    for task in test_tasks:
        result = assigner.classify_task(task)
        print(f"Task: {task[:50]}...")
        print(f"  Type: {result.get('task_type')}")
        print(f"  Auto-assign: {result.get('can_auto_assign')}")
        if result.get('forbidden'):
            print(f"  FORBIDDEN: {result.get('reason')}")
        print()
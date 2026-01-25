
#!/usr/bin/env python3
"""
Jr Learning Store - Records and applies learnings from task executions.

For Seven Generations - Cherokee AI Federation
"""

import hashlib
import json
import psycopg2
from typing import Dict, List, Optional

class JrLearningStore:
    """Store and apply Jr learning from past executions."""

    def __init__(self, jr_name: str):
        self.jr_name = jr_name
        self.db_config = {
            'host': '192.168.132.222',
            'database': 'zammad_production',
            'user': 'claude',
            'password': 'jawaseatlasers2'
        }

    def _get_connection(self):
        return psycopg2.connect(**self.db_config)

    def _classify_task_type(self, task: Dict) -> str:
        """Classify task into a type for learning matching."""
        title = task.get('title', '').lower()
        if 'fix' in title or 'bug' in title:
            return 'bugfix'
        elif 'test' in title:
            return 'testing'
        elif 'deploy' in title or 'systemd' in title:
            return 'deployment'
        elif 'create' in title or 'implement' in title or 'add' in title:
            return 'feature'
        elif 'refactor' in title or 'cleanup' in title:
            return 'refactor'
        else:
            return 'general'

    def _extract_error_pattern(self, error: str) -> Optional[str]:
        """Extract reusable error pattern from error message."""
        if not error:
            return None
        # Normalize paths and specific values
        import re
        pattern = re.sub(r'/[^\s]+', '<PATH>', error)
        pattern = re.sub(r'\d+', '<NUM>', pattern)
        return pattern[:200] if len(pattern) > 200 else pattern

    def record_execution(self, task: Dict, result: Dict, reflection: Dict = None):
        """Record execution outcome for learning."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO jr_execution_learning (
                        jr_name, task_type, instruction_hash,
                        success, steps_count, error_pattern,
                        reflection_analysis, improvements_suggested
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    self.jr_name,
                    self._classify_task_type(task),
                    hashlib.md5(task.get('instruction_content', '').encode()).hexdigest()[:16],
                    result.get('success', False),
                    len(result.get('steps_executed', [])),
                    self._extract_error_pattern(result.get('error', '')),
                    reflection.get('analysis') if reflection else None,
                    json.dumps(reflection.get('improvements', [])) if reflection else '[]'
                ))
            conn.commit()
        finally:
            conn.close()

    def get_similar_task_learnings(self, task: Dict, limit: int = 3) -> List[Dict]:
        """Retrieve learnings from similar past tasks."""
        task_type = self._classify_task_type(task)
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT reflection_analysis, improvements_suggested,
                           success, error_pattern
                    FROM jr_execution_learning
                    WHERE task_type = %s
                      AND reflection_analysis IS NOT NULL
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (task_type, limit))
                rows = cur.fetchall()
                return [
                    {
                        'analysis': row[0],
                        'improvements': json.loads(row[1]) if row[1] else [],
                        'success': row[2],
                        'error_pattern': row[3]
                    }
                    for row in rows
                ]
        finally:
            conn.close()

    def apply_learnings_to_prompt(self, task: Dict, base_prompt: str) -> str:
        """Enhance prompt with past learnings."""
        learnings = self.get_similar_task_learnings(task)

        if not learnings:
            return base_prompt

        learning_context = "\n\n## LEARNINGS FROM SIMILAR TASKS:\n"
        for l in learnings:
            if l['analysis']:
                learning_context += f"- {l['analysis']}\n"
                for imp in l.get('improvements', [])[:2]:
                    learning_context += f"  → {imp}\n"

        return base_prompt + learning_context


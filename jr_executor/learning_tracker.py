#!/usr/bin/env python3
"""
Cherokee Jr Learning Tracker Module
Tracks task history and learning metrics for Jr agents

Created: 2025-12-10
Author: TPM
Task: JR-LEARNING-001

For Seven Generations
"""

import os
import sys
from datetime import datetime

# Database connection - reuse from thermal_poller
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False


def get_db_connection():
    """Get database connection using environment or defaults"""
    if not HAS_PSYCOPG2:
        return None
    
    return psycopg2.connect(
        host=os.environ.get('CHEROKEE_SPOKE_HOST', '192.168.132.222'),
        database=os.environ.get('CHEROKEE_SPOKE_DB', 'triad_federation'),
        user=os.environ.get('CHEROKEE_SPOKE_USER', 'claude'),
        password=os.environ.get('CHEROKEE_SPOKE_PASSWORD', 'jawaseatlasers2')
    )


def detect_task_type(title: str, tasks: list) -> str:
    """Detect task type from mission content for categorization"""
    content_lower = (title + ' '.join(tasks or [])).lower()
    
    if any(k in content_lower for k in ['css', 'style', 'theme', 'color']):
        return 'css_styling'
    elif any(k in content_lower for k in ['database', 'sql', 'table', 'grant', 'index', 'query']):
        return 'database_admin'
    elif any(k in content_lower for k in ['monitor', 'alert', 'metric', 'check', 'health']):
        return 'monitoring'
    elif any(k in content_lower for k in ['security', 'encrypt', 'auth', 'permission', 'secret']):
        return 'security'
    elif any(k in content_lower for k in ['file', 'create', 'write', 'deploy', 'copy']):
        return 'file_operations'
    elif any(k in content_lower for k in ['api', 'endpoint', 'http', 'request', 'fetch']):
        return 'api_integration'
    elif any(k in content_lower for k in ['test', 'verify', 'validate', 'diagnostic']):
        return 'testing'
    elif any(k in content_lower for k in ['consult', 'vote', 'review', 'response']):
        return 'consultation'
    else:
        return 'general'


def record_task_start(mission_id: str, jr_name: str, task_type: str, 
                      description: str, source_memory_id: str = None) -> str:
    """Record task assignment in jr_task_history, return history_id"""
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return None
            
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO jr_task_history
            (task_id, jr_name, task_type, task_description, assigned_by, assigned_at, thermal_memory_id)
            VALUES (%s, %s, %s, %s, %s, NOW(), %s)
            RETURNING id;
        """, (
            str(mission_id)[:255],
            jr_name,
            task_type,
            description[:500] if description else '',
            'Chiefs',
            source_memory_id
        ))
        result = cur.fetchone()
        conn.commit()
        cur.close()
        return str(result[0]) if result else None
    except Exception as e:
        print(f"[LEARNING] Error recording task start: {e}")
        return None
    finally:
        if conn:
            conn.close()


def record_task_completion(history_id: str, outcome: str,
                          duration_seconds: int, validation_score: float = None):
    """Record task completion in jr_task_history"""
    if not history_id:
        return
        
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return
            
        cur = conn.cursor()
        cur.execute("""
            UPDATE jr_task_history
            SET completed_at = NOW(),
                started_at = COALESCE(started_at, assigned_at),
                duration_seconds = %s,
                outcome = %s,
                validation_score = %s,
                learned_from_task = %s
            WHERE id = %s::uuid;
        """, (duration_seconds, outcome, validation_score, outcome == 'success', history_id))
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"[LEARNING] Error recording task completion: {e}")
    finally:
        if conn:
            conn.close()


def update_learning_metrics(jr_name: str, task_type: str, success: bool,
                           duration_seconds: int, validation_score: float = None):
    """Update aggregated learning metrics for a Jr"""
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return
            
        cur = conn.cursor()
        
        # Get current metrics for this Jr + skill
        cur.execute("""
            SELECT id, task_count, success_count, avg_completion_time_seconds,
                   avg_validation_score, proficiency_score
            FROM jr_learning_metrics
            WHERE jr_name = %s AND skill_category = %s
            ORDER BY measured_at DESC LIMIT 1;
        """, (jr_name, task_type))
        
        existing = cur.fetchone()
        
        if existing:
            old_id, old_count, old_success, old_avg_time, old_avg_val, old_prof = existing
            new_count = old_count + 1
            new_success = old_success + (1 if success else 0)
            new_avg_time = ((old_avg_time or 0) * old_count + duration_seconds) / new_count
            val_score = validation_score if validation_score is not None else 0.5
            new_avg_val = ((old_avg_val or 0.5) * old_count + val_score) / new_count
            
            # Proficiency: success_rate * 0.7 + normalized_validation * 0.3
            success_rate = new_success / new_count
            new_proficiency = success_rate * 0.7 + new_avg_val * 0.3
            improvement_rate = new_proficiency - (old_prof or 0.5)
            plateau_detected = abs(improvement_rate) < 0.01 and new_count > 5
            
            cur.execute("""
                INSERT INTO jr_learning_metrics
                (jr_name, skill_category, proficiency_score, task_count, success_count,
                 avg_completion_time_seconds, avg_validation_score, improvement_rate, plateau_detected)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (jr_name, task_type, new_proficiency, new_count, new_success,
                  int(new_avg_time), new_avg_val, improvement_rate, plateau_detected))
        else:
            # First task of this type
            proficiency = 0.6 if success else 0.3
            val_score = validation_score if validation_score is not None else 0.5
            cur.execute("""
                INSERT INTO jr_learning_metrics
                (jr_name, skill_category, proficiency_score, task_count, success_count,
                 avg_completion_time_seconds, avg_validation_score, improvement_rate, plateau_detected)
                VALUES (%s, %s, %s, 1, %s, %s, %s, 0, false);
            """, (jr_name, task_type, proficiency, 1 if success else 0,
                  duration_seconds, val_score))
        
        conn.commit()
        cur.close()
        print(f"[LEARNING] Updated metrics: {jr_name}/{task_type} success={success} prof={new_proficiency if existing else proficiency:.2f}")
        
    except Exception as e:
        print(f"[LEARNING] Error updating learning metrics: {e}")
    finally:
        if conn:
            conn.close()


class LearningTracker:
    """Wrapper class for tracking learning in Jr executor"""
    
    def __init__(self, jr_name: str):
        self.jr_name = jr_name
        self.current_history_id = None
        self.current_task_type = None
        self.start_time = None
    
    def start_mission(self, mission_id: str, title: str, tasks: list, source_memory_id: str = None):
        """Call at start of mission processing"""
        self.start_time = datetime.now()
        self.current_task_type = detect_task_type(title, tasks)
        description = f"{title}: {' '.join(tasks or [])[:400]}"
        self.current_history_id = record_task_start(
            mission_id, self.jr_name, self.current_task_type, 
            description, source_memory_id
        )
        return self.current_history_id
    
    def complete_mission(self, success: bool, results: list = None):
        """Call at end of mission processing"""
        if not self.start_time:
            return
            
        duration_seconds = int((datetime.now() - self.start_time).total_seconds())
        
        # Calculate validation score from results
        if results:
            successes = sum(1 for r in results if r.get('success'))
            validation_score = successes / len(results)
        else:
            validation_score = 1.0 if success else 0.0
        
        outcome = 'success' if success else 'failed'
        
        # Record to both tables
        record_task_completion(self.current_history_id, outcome, duration_seconds, validation_score)
        update_learning_metrics(self.jr_name, self.current_task_type, success, duration_seconds, validation_score)
        
        # Reset state
        self.current_history_id = None
        self.current_task_type = None
        self.start_time = None


if __name__ == '__main__':
    # Test the module
    print("Testing Learning Tracker Module...")
    
    tracker = LearningTracker('test_jr')
    
    # Test task type detection
    print(f"Task type for 'Create CSS theme': {detect_task_type('Create CSS theme', [])}")
    print(f"Task type for 'Run SQL query': {detect_task_type('Run SQL query', ['SELECT * FROM test'])}")
    print(f"Task type for 'Monitor alerts': {detect_task_type('Monitor alerts', [])}")
    
    # Test tracking flow
    print("\nTesting tracking flow...")
    history_id = tracker.start_mission('test-001', 'Test Mission', ['Task 1', 'Task 2'])
    print(f"Started mission, history_id: {history_id}")
    
    tracker.complete_mission(True, [{'success': True}, {'success': True}])
    print("Mission completed")
    
    print("\nDone. Check jr_task_history and jr_learning_metrics tables.")

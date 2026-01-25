import json
import uuid
import psycopg2
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class StepStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"

@dataclass
class ExecutionStep:
    step_id: str
    name: str
    status: StepStatus
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    output: Optional[str] = None
    error: Optional[str] = None

class SessionTracker:
    """
    Manages execution sessions by creating, updating, and querying sessions in a PostgreSQL database.
    """
    def __init__(self, db_config: dict):
        """
        Initializes the SessionTracker with database configuration.

        :param db_config: Dictionary containing database connection parameters.
        """
        self.db_config = db_config

    def create_session(self, task_id: str, jr_name: str, steps: List[str]) -> str:
        """
        Creates a new execution session in the database.

        :param task_id: Unique identifier for the task.
        :param jr_name: Name of the Junior responsible for the task.
        :param steps: List of step names to be included in the session.
        :return: Unique identifier for the created session.
        """
        session_id = str(uuid.uuid4())
        step_list = [
            asdict(
                ExecutionStep(
                    step_id=str(uuid.uuid4()),
                    name=f"Step {i+1}",
                    status=StepStatus.PENDING
                )
            ) for i, _ in enumerate(steps)
        ]
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO jr_execution_sessions (session_id, task_id, jr_name, status, steps, created_at, updated_at) 
               VALUES (%s, %s, %s, %s, %s, NOW(), NOW())""",
            (session_id, task_id, jr_name, "pending", json.dumps(step_list, default=str))
        )
        conn.commit()
        cur.close()
        conn.close()
        return session_id

    def update_step_status(self, session_id: str, step_id: str, status: StepStatus, output: Optional[str] = None, error: Optional[str] = None) -> None:
        """
        Updates the status of a specific step within a session.

        :param session_id: Unique identifier for the session.
        :param step_id: Unique identifier for the step.
        :param status: New status for the step.
        :param output: Output from the step execution.
        :param error: Error message if the step failed.
        """
        timestamp = datetime.now().isoformat()
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()
        cur.execute(
            """UPDATE jr_execution_sessions 
               SET steps = jsonb_set(steps::jsonb, '{%s,status}', %s::jsonb),
                   steps = jsonb_set(steps::jsonb, '{%s,started_at}', %s::jsonb),
                   steps = jsonb_set(steps::jsonb, '{%s,completed_at}', %s::jsonb),
                   steps = jsonb_set(steps::jsonb, '{%s,output}', %s::jsonb),
                   steps = jsonb_set(steps::jsonb, '{%s,error}', %s::jsonb),
                   updated_at = NOW()
               WHERE session_id = %s AND steps @> '[{"step_id": "%s"}]'""",
            (
                step_id, json.dumps(status.value),
                step_id, json.dumps(timestamp) if status == StepStatus.IN_PROGRESS else 'null',
                step_id, json.dumps(timestamp) if status in [StepStatus.PASSED, StepStatus.FAILED] else 'null',
                step_id, json.dumps(output) if output else 'null',
                step_id, json.dumps(error) if error else 'null',
                session_id, step_id
            )
        )
        conn.commit()
        cur.close()
        conn.close()

    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Retrieves a session by its unique identifier.

        :param session_id: Unique identifier for the session.
        :return: Dictionary containing session details or None if not found.
        """
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()
        cur.execute("SELECT * FROM jr_execution_sessions WHERE session_id = %s", (session_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return {
                "session_id": row[0],
                "task_id": row[1],
                "jr_name": row[2],
                "status": row[3],
                "steps": json.loads(row[4]),
                "created_at": row[5].isoformat(),
                "updated_at": row[6].isoformat()
            }
        return None
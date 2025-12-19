# JR INSTRUCTIONS: Work Queue Integration
## JR_BUILD_INSTRUCTIONS_WORK_QUEUE_INTEGRATION
## December 17, 2025

### OBJECTIVE
Enable Jrs to claim tasks from the `jr_work_queue` table, execute them, and report results back to the database.

---

## BACKGROUND

The `jr_work_queue` table provides database-backed task assignment for all Cherokee AI Federation Jrs. This replaces the file-only instruction system with a queryable, trackable queue.

**Database:** `zammad_production` on bluefin (192.168.132.222)
**User:** `claude` / **Password:** `jawaseatlasers2`

---

## TASK 1: Create Jr Queue Client Library

Create `/ganuda/jr_executor/jr_queue_client.py`:

```python
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
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if fetch:
                return cur.fetchall()
            conn.commit()
            return cur.rowcount

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
                   seven_gen_impact, tags, created_at
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
                artifacts,
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
```

---

## TASK 2: Create TPM Queue Manager

Create `/ganuda/jr_executor/tpm_queue_manager.py`:

```python
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
    'password': os.environ.get('CHEROKEE_DB_PASS', 'jawaseatlasers2')
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
```

---

## TASK 3: Integrate with Jr Executor

Update `/ganuda/jr_executor/task_executor.py` to use the queue client.

Add this import at the top:
```python
from jr_queue_client import JrQueueClient
```

Add this method to the TaskExecutor class:
```python
def process_queue_task(self, task: dict) -> dict:
    """
    Process a task from the work queue.

    Args:
        task: Task dictionary from jr_work_queue

    Returns:
        Result dictionary with status and outputs
    """
    task_id = task['id']
    client = JrQueueClient(self.jr_name)

    try:
        # Claim the task
        if not client.claim_task(task_id):
            return {'success': False, 'error': 'Failed to claim task'}

        # Get instructions from file or inline content
        instructions = None
        if task.get('instruction_file'):
            with open(task['instruction_file'], 'r') as f:
                instructions = f.read()
        elif task.get('instruction_content'):
            instructions = task['instruction_content']

        if not instructions:
            client.fail_task(task_id, "No instructions provided")
            return {'success': False, 'error': 'No instructions'}

        # Parse and execute instructions
        from instruction_parser import parse_instructions
        steps = parse_instructions(instructions)

        total_steps = len(steps)
        artifacts = []

        for i, step in enumerate(steps):
            # Update progress
            progress = int((i / total_steps) * 100)
            client.update_progress(task_id, progress, f"Step {i+1}/{total_steps}")

            # Execute step
            result = self.execute_step(step)

            if step.get('type') == 'file' and result.get('success'):
                artifacts.append(step.get('args', {}).get('path'))

            if not result.get('success') and step.get('critical', True):
                client.fail_task(task_id, f"Step {i+1} failed: {result.get('error')}")
                return {'success': False, 'error': result.get('error')}

        # Mark complete
        client.complete_task(task_id, {'steps_completed': total_steps}, artifacts)
        return {'success': True, 'steps': total_steps, 'artifacts': artifacts}

    except Exception as e:
        client.fail_task(task_id, str(e))
        return {'success': False, 'error': str(e)}
    finally:
        client.close()
```

---

## TASK 4: Create Queue Worker Daemon

Create `/ganuda/jr_executor/jr_queue_worker.py`:

```python
#!/usr/bin/env python3
"""
Jr Queue Worker - Daemon that polls for and executes assigned tasks.

Run as: python3 jr_queue_worker.py "Software Engineer Jr."

For Seven Generations - Cherokee AI Federation
"""

import sys
import time
import signal
from datetime import datetime

from jr_queue_client import JrQueueClient
from task_executor import TaskExecutor

# Configuration
POLL_INTERVAL = 30  # seconds between queue checks
HEARTBEAT_INTERVAL = 60  # seconds between heartbeats


class JrQueueWorker:
    """Worker daemon that processes queue tasks for a Jr."""

    def __init__(self, jr_name: str):
        self.jr_name = jr_name
        self.client = JrQueueClient(jr_name)
        self.executor = TaskExecutor(jr_name)
        self.running = True
        self.last_heartbeat = 0

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def _shutdown(self, signum, frame):
        print(f"\n[{self.jr_name}] Shutting down...")
        self.running = False

    def _heartbeat(self):
        """Send heartbeat if interval elapsed."""
        now = time.time()
        if now - self.last_heartbeat >= HEARTBEAT_INTERVAL:
            self.client.heartbeat()
            self.last_heartbeat = now

    def run(self):
        """Main worker loop."""
        print(f"[{self.jr_name}] Queue worker starting...")
        print(f"[{self.jr_name}] Poll interval: {POLL_INTERVAL}s")
        print(f"[{self.jr_name}] Heartbeat interval: {HEARTBEAT_INTERVAL}s")

        self.client.heartbeat()
        self.last_heartbeat = time.time()

        while self.running:
            try:
                self._heartbeat()

                # Check for pending tasks
                tasks = self.client.get_pending_tasks(limit=1)

                if tasks:
                    task = tasks[0]
                    print(f"[{self.jr_name}] Processing task: {task['title']}")

                    result = self.executor.process_queue_task(task)

                    if result.get('success'):
                        print(f"[{self.jr_name}] Task completed successfully")
                    else:
                        print(f"[{self.jr_name}] Task failed: {result.get('error')}")

                # Sleep before next poll
                time.sleep(POLL_INTERVAL)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[{self.jr_name}] Worker error: {e}")
                time.sleep(POLL_INTERVAL)

        self.client.close()
        print(f"[{self.jr_name}] Worker stopped.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 jr_queue_worker.py 'Jr Name'")
        print("Example: python3 jr_queue_worker.py 'Software Engineer Jr.'")
        sys.exit(1)

    jr_name = sys.argv[1]
    worker = JrQueueWorker(jr_name)
    worker.run()
```

---

## Verification

```bash
cd /ganuda/jr_executor && /home/dereadi/cherokee_venv/bin/python3 -c "
from jr_queue_client import JrQueueClient
from tpm_queue_manager import TPMQueueManager

# Test client
client = JrQueueClient('Software Engineer Jr.')
print('Client heartbeat:', client.heartbeat())
print('Client workload:', client.get_my_workload())
client.close()

# Test manager
mgr = TPMQueueManager()
print('Queue status:', len(mgr.get_queue_status()), 'pending tasks')
mgr.close()

print('All tests passed!')
"
```

---

## SUCCESS CRITERIA

1. Jr Queue Client can connect and query tasks
2. TPM Queue Manager can add and manage tasks
3. Worker daemon can poll and process tasks
4. Progress updates flow through the database
5. Task status transitions work correctly

---

## DATABASE TABLES CREATED

- `jr_work_queue` - Main task queue table
- `jr_work_queue_pending` - View of pending tasks
- `jr_workload` - View of Jr workloads

---

*Jr Instructions issued: December 17, 2025*
*For Seven Generations - Cherokee AI Federation*

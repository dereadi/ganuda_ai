#!/usr/bin/env python3
"""
Jr Queue Worker - Daemon that polls for and executes assigned tasks.

Run as: python3 jr_queue_worker.py "Software Engineer Jr."

For Seven Generations - Cherokee AI Federation

FIXED: Dec 25, 2025 - Proper error handling, no false completions
"""

import sys
import time
import signal
import traceback
from datetime import datetime

from jr_queue_client import JrQueueClient
from task_executor import TaskExecutor

# Configuration
POLL_INTERVAL = 30  # seconds between queue checks
HEARTBEAT_INTERVAL = 60  # seconds between heartbeats
MAX_TASKS_PER_WORKER = 50  # Restart after N tasks for code freshness (TPM Feb 3, 2026)


class JrQueueWorker:
    """Worker daemon that processes queue tasks for a Jr."""

    def __init__(self, jr_name: str):
        self.jr_name = jr_name
        self.client = JrQueueClient(jr_name)
        self.executor = TaskExecutor()
        self.running = True
        self.last_heartbeat = 0
        self.current_task = None
        self.tasks_processed = 0  # Counter for max-tasks-per-child (TPM Feb 3, 2026)

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
            try:
                self.client.heartbeat()
                self.last_heartbeat = now
            except Exception as e:
                print(f"[{self.jr_name}] Heartbeat failed: {e}")

    def _generate_summary(self, task: dict, result: dict) -> str:
        """Generate meaningful task summary based on actual work done."""
        steps = result.get('steps_executed', [])

        if not steps:
            return f"Task '{task['title']}': No steps executed"

        successful = sum(1 for s in steps if s.get('success'))
        failed = len(steps) - successful

        # Collect file artifacts
        files_created = [
            s.get('args', {}).get('path', s.get('file_path', 'unknown'))
            for s in steps
            if s.get('type') == 'file' and s.get('success')
        ]

        summary = f"Task '{task['title']}': {successful}/{len(steps)} steps succeeded"

        if files_created:
            file_list = ', '.join(files_created[:3])
            if len(files_created) > 3:
                file_list += f" (+{len(files_created) - 3} more)"
            summary += f". Files: {file_list}"

        if failed:
            summary += f". {failed} step(s) failed."

        return summary

    def run(self):
        """Main worker loop."""
        print(f"[{self.jr_name}] Queue worker starting...")
        print(f"[{self.jr_name}] Poll interval: {POLL_INTERVAL}s")
        print(f"[{self.jr_name}] Heartbeat interval: {HEARTBEAT_INTERVAL}s")

        try:
            self.client.heartbeat()
        except Exception as e:
            print(f"[{self.jr_name}] Initial heartbeat failed: {e}")
        self.last_heartbeat = time.time()

        while self.running:
            self.current_task = None
            try:
                # Check sanctuary pause flag
                import os as _os
                if _os.path.exists('/tmp/jr_executor_paused'):
                    print(f"[{self.jr_name}] Paused for sanctuary state")
                    time.sleep(30)
                    continue

                self._heartbeat()

                # Check for pending tasks
                tasks = self.client.get_pending_tasks(limit=1)

                if tasks:
                    self.current_task = tasks[0]
                    task = self.current_task
                    print(f"[{self.jr_name}] Processing task: {task['title']}")

                    try:
                        result = self.executor.process_queue_task(task)

                        # P0 FIX Jan 27, 2026: Defense in depth - validate work was done
                        # Don't trust success flag alone if no actual work evidence
                        # UPGRADED Feb 3, 2026: Staged files are NOT completion evidence
                        steps = result.get('steps_executed', [])
                        artifacts = result.get('artifacts', [])
                        files_created = result.get('files_created', 0)
                        files_staged = result.get('files_staged', 0)

                        # Count real vs staged artifacts
                        real_artifacts = [a for a in artifacts if isinstance(a, dict) and a.get('type') == 'file_created']
                        staged_artifacts = [a for a in artifacts if isinstance(a, dict) and a.get('type') == 'file_staged']

                        if result.get('success'):
                            # Secondary validation: require evidence of REAL work
                            # Staged files mean protected paths - needs TPM review, not completion
                            real_file_count = len(real_artifacts) if real_artifacts else (files_created - files_staged)
                            if not steps and not real_artifacts and real_file_count <= 0:
                                print(f"[{self.jr_name}] WARNING: success=True but no real work evidence")
                                if staged_artifacts:
                                    print(f"[{self.jr_name}] INFO: {len(staged_artifacts)} files were STAGED (protected paths) - needs TPM merge")
                                    result['success'] = False
                                    result['error'] = f'All {len(staged_artifacts)} files staged to protected paths - requires TPM merge via /staging'
                                else:
                                    result['success'] = False
                                    result['error'] = 'No work performed (0 steps, 0 artifacts, 0 real files)'

                        if result.get('success'):
                            print(f"[{self.jr_name}] Task completed successfully")
                            # Mark as completed with meaningful summary
                            summary = self._generate_summary(task, result)
                            self.client.complete_task(
                                task['id'],  # Use integer id, not varchar task_id
                                result={
                                    'summary': summary,
                                    'steps_executed': result.get('steps_executed', []),
                                    'completed_at': datetime.now().isoformat(),
                                    # Full result metadata (Jan 28, 2026)
                                    'execution_mode': result.get('execution_mode', 'unknown'),
                                    'files_created': result.get('files_created', 0),
                                    'success': result.get('success', True),
                                    'subtasks_completed': result.get('subtasks_completed', 0),
                                    'plan': result.get('plan'),
                                    'task_id': result.get('task_id'),
                                    'title': result.get('title')
                                },
                                artifacts=result.get('artifacts', [])
                            )
                        else:
                            error_msg = result.get('error', 'Unknown error')
                            print(f"[{self.jr_name}] Task failed: {error_msg}")
                            # DLQ integration: route failures for retry + escalation
                            try:
                                sys.path.insert(0, '/ganuda')
                                from jr_executor.dlq_manager import send_to_dlq
                                dlq_id = send_to_dlq(
                                    task_id=task['id'],
                                    failure_reason=error_msg,
                                    failure_traceback=result.get('traceback'),
                                )
                                print(f"[{self.jr_name}] Task {task['id']} routed to DLQ (entry {dlq_id})")
                            except Exception as dlq_err:
                                print(f"[{self.jr_name}] DLQ routing failed ({dlq_err}), falling back to fail_task")
                                self.client.fail_task(task['id'], error_msg, result)
                    except Exception as task_error:
                        # Task execution error - route through DLQ for retry
                        error_msg = f"Task execution error: {task_error}"
                        print(f"[{self.jr_name}] {error_msg}")
                        traceback.print_exc()
                        try:
                            sys.path.insert(0, '/ganuda')
                            from jr_executor.dlq_manager import send_to_dlq
                            send_to_dlq(
                                task_id=task['id'],
                                failure_reason=error_msg,
                                failure_traceback=traceback.format_exc(),
                            )
                        except Exception as dlq_err:
                            print(f"[{self.jr_name}] DLQ routing failed ({dlq_err}), falling back to fail_task")
                            try:
                                self.client.fail_task(task['id'], error_msg)
                            except Exception as mark_error:
                                print(f"[{self.jr_name}] Could not mark task as failed: {mark_error}")

                # Max-tasks-per-child: restart for code freshness (TPM Feb 3, 2026)
                if tasks:
                    self.tasks_processed += 1
                    if self.tasks_processed >= MAX_TASKS_PER_WORKER:
                        print(f"[{self.jr_name}] Processed {self.tasks_processed} tasks, exiting for code freshness (systemd will restart)")
                        break

                # Sleep before next poll
                time.sleep(POLL_INTERVAL)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[{self.jr_name}] Worker error: {e}")
                traceback.print_exc()
                # If we have a current task, try to mark it failed
                if self.current_task:
                    try:
                        self.client.fail_task(
                            self.current_task['id'],  # Use integer id
                            f"Worker error during processing: {e}"
                        )
                    except:
                        pass
                time.sleep(POLL_INTERVAL)

        self.client.close()
        print(f"[{self.jr_name}] Worker stopped.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 jr_queue_worker.py 'Jr Name'")
        sys.exit(1)
    
    jr_name = sys.argv[1]
    worker = JrQueueWorker(jr_name)
    worker.run()

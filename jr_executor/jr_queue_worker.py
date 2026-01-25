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


class JrQueueWorker:
    """Worker daemon that processes queue tasks for a Jr."""

    def __init__(self, jr_name: str):
        self.jr_name = jr_name
        self.client = JrQueueClient(jr_name)
        self.executor = TaskExecutor()
        self.running = True
        self.last_heartbeat = 0
        self.current_task = None

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
                self._heartbeat()

                # Check for pending tasks
                tasks = self.client.get_pending_tasks(limit=1)

                if tasks:
                    self.current_task = tasks[0]
                    task = self.current_task
                    print(f"[{self.jr_name}] Processing task: {task['title']}")

                    try:
                        result = self.executor.process_queue_task(task)

                        if result.get('success'):
                            print(f"[{self.jr_name}] Task completed successfully")
                            # Mark as completed with meaningful summary
                            summary = self._generate_summary(task, result)
                            self.client.complete_task(
                                task['id'],  # Use integer id, not varchar task_id
                                result={
                                    'summary': summary,
                                    'steps_executed': result.get('steps_executed', []),
                                    'completed_at': datetime.now().isoformat()
                                },
                                artifacts=result.get('artifacts', [])
                            )
                        else:
                            error_msg = result.get('error', 'Unknown error')
                            print(f"[{self.jr_name}] Task failed: {error_msg}")
                            # Mark as failed explicitly
                            self.client.fail_task(task['id'], error_msg, result)  # Use integer id
                    except Exception as task_error:
                        # Task execution error - mark as FAILED, not skip
                        error_msg = f"Task execution error: {task_error}"
                        print(f"[{self.jr_name}] {error_msg}")
                        traceback.print_exc()
                        try:
                            self.client.fail_task(task['id'], error_msg)  # Use integer id
                        except Exception as mark_error:
                            print(f"[{self.jr_name}] Could not mark task as failed: {mark_error}")

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

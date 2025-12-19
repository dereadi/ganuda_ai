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
# JR Instruction: Jr Orchestrator with Graduated Priority Queue

**Task ID:** ORCHESTRATOR-001
**Priority:** P0
**Type:** infrastructure
**Assigned:** Software Engineer Jr.
**Council Approval:** PROCEED WITH CAUTION (70% confidence, 2026-01-25)

---

## Objective

Create a Jr Orchestrator daemon that manages all Jr worker processes with graduated priority resource allocation (50%, 25%, 12.5%...).

---

## Context

Currently Jr workers are started manually and die when sessions end. We need a single systemd-managed daemon that:
1. Spawns and monitors all Jr worker types
2. Allocates LLM inference capacity based on graduated priority
3. Promotes lower-priority tasks when higher ones complete

---

## Deliverables

### 1. Token Bucket Implementation

Create `/ganuda/lib/graduated_token_bucket.py`:

```python
"""
Graduated Token Bucket for Jr Priority Queue.
Council Approved: 2026-01-25 (70% confidence)

Allocates LLM inference capacity:
- Position 1: 50% (100 tokens/min)
- Position 2: 25% (50 tokens/min)
- Position 3: 12.5% (25 tokens/min)
- ...halving pattern continues
"""

import time
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class TokenBucket:
    """Token bucket for rate limiting a single task."""
    task_id: int
    worker_name: str
    position: int
    tokens: float = 0.0
    max_tokens: float = 0.0
    refill_rate: float = 0.0  # tokens per second
    last_refill: float = field(default_factory=time.time)

    BASE_RATE = 100.0  # tokens per minute for position 1

    def __post_init__(self):
        self._update_rates()

    def _update_rates(self):
        """Calculate rates based on position."""
        # 50%, 25%, 12.5%, 6.25%... of base rate
        minute_rate = self.BASE_RATE * (0.5 ** (self.position - 1))
        self.refill_rate = minute_rate / 60.0  # per second
        self.max_tokens = minute_rate * 2  # 2 minute burst capacity

    def refill(self):
        """Add tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.max_tokens, self.tokens + (elapsed * self.refill_rate))
        self.last_refill = now

    def try_consume(self, amount: float = 1.0) -> bool:
        """Try to consume tokens. Returns True if successful."""
        self.refill()
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False

    def wait_time(self, amount: float = 1.0) -> float:
        """Calculate seconds to wait for tokens."""
        self.refill()
        if self.tokens >= amount:
            return 0.0
        needed = amount - self.tokens
        return needed / self.refill_rate

    def promote(self, new_position: int):
        """Promote to higher priority (lower position number)."""
        self.position = new_position
        self._update_rates()

    def demote(self, new_position: int):
        """Demote to lower priority (higher position number)."""
        self.position = new_position
        self._update_rates()


class GraduatedPriorityManager:
    """
    Manages graduated priority queue with automatic promotion.

    When a task completes, all lower-priority tasks promote upward.
    """

    def __init__(self):
        self.buckets: Dict[int, TokenBucket] = {}  # task_id -> bucket
        self.position_order: List[int] = []  # task_ids in position order
        self._lock = threading.Lock()

    def add_task(self, task_id: int, worker_name: str) -> TokenBucket:
        """Add a new task at the lowest priority position."""
        with self._lock:
            position = len(self.position_order) + 1
            bucket = TokenBucket(
                task_id=task_id,
                worker_name=worker_name,
                position=position
            )
            self.buckets[task_id] = bucket
            self.position_order.append(task_id)
            return bucket

    def add_urgent_task(self, task_id: int, worker_name: str) -> TokenBucket:
        """Add urgent task at position 1, demote all others."""
        with self._lock:
            # Demote all existing tasks
            for existing_id in self.position_order:
                self.buckets[existing_id].demote(
                    self.buckets[existing_id].position + 1
                )

            # Insert at position 1
            bucket = TokenBucket(
                task_id=task_id,
                worker_name=worker_name,
                position=1
            )
            self.buckets[task_id] = bucket
            self.position_order.insert(0, task_id)
            return bucket

    def complete_task(self, task_id: int) -> List[int]:
        """
        Remove completed task and promote all below it.

        Returns list of task_ids that were promoted.
        """
        with self._lock:
            if task_id not in self.buckets:
                return []

            # Find position of completed task
            try:
                completed_idx = self.position_order.index(task_id)
            except ValueError:
                return []

            # Remove completed task
            del self.buckets[task_id]
            self.position_order.pop(completed_idx)

            # Promote everyone below
            promoted = []
            for i in range(completed_idx, len(self.position_order)):
                promoting_id = self.position_order[i]
                new_position = i + 1  # 1-indexed
                self.buckets[promoting_id].promote(new_position)
                promoted.append(promoting_id)

            return promoted

    def get_bucket(self, task_id: int) -> Optional[TokenBucket]:
        """Get bucket for a task."""
        return self.buckets.get(task_id)

    def get_status(self) -> List[dict]:
        """Get current queue status for monitoring."""
        with self._lock:
            return [
                {
                    'task_id': tid,
                    'worker': self.buckets[tid].worker_name,
                    'position': self.buckets[tid].position,
                    'tokens': round(self.buckets[tid].tokens, 1),
                    'rate': round(self.buckets[tid].refill_rate * 60, 1),  # per minute
                    'capacity_pct': round(100 * (0.5 ** (self.buckets[tid].position - 1)), 1)
                }
                for tid in self.position_order
            ]
```

### 2. Jr Orchestrator Daemon

Create `/ganuda/jr_executor/jr_orchestrator.py`:

```python
#!/usr/bin/env python3
"""
Jr Orchestrator - Manages all Jr workers with graduated priority.
Council Approved: 2026-01-25 (70% confidence)

Spawns worker processes for each Jr type and manages their resource allocation
using graduated token buckets (50%, 25%, 12.5%...).
"""

import os
import sys
import time
import signal
import subprocess
import threading
import logging
from datetime import datetime
from typing import Dict, Optional, List
from dataclasses import dataclass

# Add lib to path
sys.path.insert(0, '/ganuda/lib')
from graduated_token_bucket import GraduatedPriorityManager

import psycopg2
from psycopg2.extras import RealDictCursor

# Configuration
JR_TYPES = [
    'Software Engineer Jr.',
    'Research Jr.',
    'Infrastructure Jr.',
    'it_triad_jr'
]

DB_CONFIG = {
    'host': os.environ.get('CHEROKEE_DB_HOST', '192.168.132.222'),
    'database': os.environ.get('CHEROKEE_DB_NAME', 'zammad_production'),
    'user': os.environ.get('CHEROKEE_DB_USER', 'claude'),
    'password': os.environ.get('CHEROKEE_DB_PASS', 'jawaseatlasers2')
}

POLL_INTERVAL = 30  # seconds
HEARTBEAT_TIMEOUT = 120  # seconds before considering worker dead

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('jr_orchestrator')


@dataclass
class WorkerProcess:
    """Tracks a worker subprocess."""
    jr_name: str
    process: subprocess.Popen
    started_at: datetime
    restart_count: int = 0
    last_heartbeat: datetime = None


class JrOrchestrator:
    """
    Main orchestrator that manages Jr worker processes.

    Responsibilities:
    1. Spawn worker processes for each Jr type
    2. Monitor worker health via heartbeats
    3. Restart failed workers with exponential backoff
    4. Coordinate priority queue for active tasks
    """

    def __init__(self):
        self.workers: Dict[str, WorkerProcess] = {}
        self.priority_manager = GraduatedPriorityManager()
        self.running = True
        self._conn = None

        # Signal handlers
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def _shutdown(self, signum, frame):
        logger.info("Shutdown signal received")
        self.running = False

    def _get_connection(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(**DB_CONFIG)
        return self._conn

    def _spawn_worker(self, jr_name: str) -> WorkerProcess:
        """Spawn a worker subprocess for a Jr type."""
        logger.info(f"Spawning worker for: {jr_name}")

        log_file = f"/ganuda/logs/jr_{jr_name.lower().replace(' ', '_').replace('.', '')}.log"

        # Open log file
        log_handle = open(log_file, 'a')

        process = subprocess.Popen(
            [
                '/home/dereadi/cherokee_venv/bin/python',
                '-u',
                'jr_queue_worker.py',
                jr_name
            ],
            cwd='/ganuda/jr_executor',
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            env={
                **os.environ,
                'PYTHONPATH': '/ganuda/lib',
                'JR_ORCHESTRATED': '1',  # Flag so worker knows it's managed
            }
        )

        return WorkerProcess(
            jr_name=jr_name,
            process=process,
            started_at=datetime.now(),
            last_heartbeat=datetime.now()
        )

    def _check_worker_health(self, worker: WorkerProcess) -> bool:
        """Check if worker is still alive."""
        # Check process status
        if worker.process.poll() is not None:
            logger.warning(f"Worker {worker.jr_name} process died (exit: {worker.process.returncode})")
            return False

        # Check heartbeat from database
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT last_seen FROM jr_status
                    WHERE jr_name = %s
                """, (worker.jr_name,))
                row = cur.fetchone()

                if row and row['last_seen']:
                    elapsed = (datetime.now() - row['last_seen']).total_seconds()
                    if elapsed > HEARTBEAT_TIMEOUT:
                        logger.warning(f"Worker {worker.jr_name} heartbeat stale ({elapsed:.0f}s)")
                        return False
                    worker.last_heartbeat = row['last_seen']

        except Exception as e:
            logger.error(f"Health check DB error: {e}")

        return True

    def _restart_worker(self, jr_name: str):
        """Restart a failed worker with exponential backoff."""
        old_worker = self.workers.get(jr_name)
        restart_count = old_worker.restart_count + 1 if old_worker else 0

        # Exponential backoff: 5s, 10s, 20s, 40s, max 300s
        backoff = min(300, 5 * (2 ** restart_count))
        logger.info(f"Restarting {jr_name} in {backoff}s (attempt {restart_count + 1})")
        time.sleep(backoff)

        # Kill old process if still running
        if old_worker and old_worker.process.poll() is None:
            logger.info(f"Killing stale process for {jr_name}")
            old_worker.process.kill()
            old_worker.process.wait()

        # Spawn new worker
        new_worker = self._spawn_worker(jr_name)
        new_worker.restart_count = restart_count
        self.workers[jr_name] = new_worker

    def _sync_priority_queue(self):
        """Sync priority queue state with database."""
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get currently in-progress tasks
                cur.execute("""
                    SELECT id, assigned_jr, sacred_fire_priority
                    FROM jr_work_queue
                    WHERE status = 'in_progress'
                    ORDER BY started_at ASC
                """)
                active_tasks = cur.fetchall()

                # Update priority manager
                current_task_ids = set(self.priority_manager.buckets.keys())
                db_task_ids = set(t['id'] for t in active_tasks)

                # Remove completed tasks
                for task_id in current_task_ids - db_task_ids:
                    promoted = self.priority_manager.complete_task(task_id)
                    if promoted:
                        logger.info(f"Task {task_id} completed. Promoted: {promoted}")

                # Add new tasks
                for task in active_tasks:
                    if task['id'] not in current_task_ids:
                        if task['sacred_fire_priority'] and task['sacred_fire_priority'] > 8:
                            bucket = self.priority_manager.add_urgent_task(
                                task['id'], task['assigned_jr']
                            )
                            logger.info(f"Urgent task {task['id']} added at position 1")
                        else:
                            bucket = self.priority_manager.add_task(
                                task['id'], task['assigned_jr']
                            )
                            logger.info(f"Task {task['id']} added at position {bucket.position}")

        except Exception as e:
            logger.error(f"Priority sync error: {e}")

    def _log_status(self):
        """Log current orchestrator status."""
        status = self.priority_manager.get_status()
        if status:
            logger.info("Priority Queue Status:")
            for s in status:
                logger.info(f"  #{s['task_id']} ({s['worker']}): "
                          f"pos={s['position']}, {s['capacity_pct']}% capacity, "
                          f"{s['tokens']}/{s['rate']} tokens")

    def run(self):
        """Main orchestrator loop."""
        logger.info("Jr Orchestrator starting...")
        logger.info(f"Managing Jr types: {JR_TYPES}")

        # Spawn initial workers
        for jr_name in JR_TYPES:
            try:
                self.workers[jr_name] = self._spawn_worker(jr_name)
            except Exception as e:
                logger.error(f"Failed to spawn {jr_name}: {e}")

        logger.info(f"Spawned {len(self.workers)} workers")

        # Main loop
        while self.running:
            try:
                # Check worker health
                for jr_name, worker in list(self.workers.items()):
                    if not self._check_worker_health(worker):
                        self._restart_worker(jr_name)

                # Sync priority queue
                self._sync_priority_queue()

                # Log status periodically
                self._log_status()

                # Wait for next poll
                time.sleep(POLL_INTERVAL)

            except Exception as e:
                logger.error(f"Main loop error: {e}")
                time.sleep(5)

        # Shutdown
        logger.info("Shutting down workers...")
        for jr_name, worker in self.workers.items():
            if worker.process.poll() is None:
                logger.info(f"Terminating {jr_name}")
                worker.process.terminate()
                worker.process.wait(timeout=10)

        logger.info("Jr Orchestrator stopped")


if __name__ == '__main__':
    orchestrator = JrOrchestrator()
    orchestrator.run()
```

### 3. Systemd Service

Create `/ganuda/scripts/systemd/jr-orchestrator.service`:

```ini
[Unit]
Description=Cherokee AI Jr Orchestrator - Graduated Priority Queue
After=network.target postgresql.service vllm-cherokee.service
Wants=vllm-cherokee.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/jr_executor
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
Environment=PYTHONPATH=/ganuda/lib
ExecStart=/home/dereadi/cherokee_venv/bin/python jr_orchestrator.py
Restart=always
RestartSec=30
StandardOutput=append:/ganuda/logs/jr_orchestrator.log
StandardError=append:/ganuda/logs/jr_orchestrator.log
SyslogIdentifier=jr-orchestrator

[Install]
WantedBy=multi-user.target
```

---

## Deployment Steps

After files are created:

```bash
# 1. Stop existing Jr workers
pkill -f "jr_queue_worker.py"
systemctl stop jr-queue-worker

# 2. Install new service
sudo ln -sf /ganuda/scripts/systemd/jr-orchestrator.service /etc/systemd/system/
sudo systemctl daemon-reload

# 3. Disable old service
sudo systemctl disable jr-queue-worker

# 4. Enable and start orchestrator
sudo systemctl enable jr-orchestrator
sudo systemctl start jr-orchestrator

# 5. Verify
systemctl status jr-orchestrator
tail -f /ganuda/logs/jr_orchestrator.log
```

---

## Success Criteria

- [ ] `graduated_token_bucket.py` created with tests
- [ ] `jr_orchestrator.py` spawns all Jr types
- [ ] Workers restart automatically on failure
- [ ] Priority queue promotes on task completion
- [ ] Systemd service manages orchestrator
- [ ] Logs to `/ganuda/logs/jr_orchestrator.log`

---

## For Seven Generations

A well-organized workforce serves continuously without manual intervention. Each worker contributes, each task completes, and the flow never stops.

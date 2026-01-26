import os
import signal
import time
import logging
import subprocess
from dataclasses import dataclass
from typing import Dict, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

# Define supported job types
JR_TYPES = [
    "Software Engineer Jr.",
    "Research Jr.",
    "Infrastructure Jr.",
    "it_triad_jr"
]

# Database configuration for PostgreSQL
DB_CONFIG = {
    "host": "192.168.132.222",
    "database": "zammad_production",
    "user": "claude",
    "password": "jawaseatlasers2"
}

@dataclass
class WorkerProcess:
    process: subprocess.Popen
    last_heartbeat: float
    restart_count: int = 0

class JrOrchestrator:
    """
    Orchestrates the execution of worker processes for different job types.
    Manages spawning, health checking, and restarting of workers.
    """
    def __init__(self):
        self.workers: Dict[str, WorkerProcess] = {}
        self.shutdown_flag = False
        self.logger = logging.getLogger(__name__)

    def _spawn_worker(self, job_type: str) -> None:
        """
        Spawns a new worker process for the specified job type.
        """
        if job_type not in JR_TYPES:
            raise ValueError(f"Unsupported job type: {job_type}")

        log_file_path = f"/ganuda/logs/{job_type.lower().replace(' ', '_')}_worker.log"
        with open(log_file_path, 'a') as log_handle:
            process = subprocess.Popen(
                ["/home/dereadi/cherokee_venv/bin/python", "-u", "jr_queue_worker.py", job_type],
                cwd="/ganuda/jr_executor",
                stdout=log_handle,
                stderr=subprocess.STDOUT
            )

        self.workers[job_type] = WorkerProcess(process=process, last_heartbeat=time.time(), restart_count=0)
        self.logger.info(f"Spawned worker for {job_type}")

    def _get_db_connection(self):
        """Get database connection for health checks."""
        try:
            return psycopg2.connect(**DB_CONFIG)
        except Exception as e:
            self.logger.error(f"DB connection failed: {e}")
            return None

    def _check_worker_health(self) -> None:
        """Check worker health via jr_status table heartbeats."""
        timeout = 120  # seconds
        conn = self._get_db_connection()
        if not conn:
            return
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                for job_type, worker in list(self.workers.items()):
                    # Check if process is alive
                    if worker.process.poll() is not None:
                        self.logger.warning(f"Worker {job_type} process died")
                        self._restart_worker(job_type)
                        continue
                    
                    # Check database heartbeat
                    cur.execute("""
                        SELECT last_seen FROM jr_status 
                        WHERE jr_name = %s
                    """, (job_type,))
                    row = cur.fetchone()
                    
                    if row and row["last_seen"]:
                        from datetime import datetime
                        elapsed = (datetime.now() - row["last_seen"]).total_seconds()
                        if elapsed > timeout:
                            self.logger.warning(f"Worker {job_type} heartbeat stale ({elapsed:.0f}s)")
                            self._restart_worker(job_type)
                        else:
                            worker.last_heartbeat = row["last_seen"]
        except Exception as e:
            self.logger.error(f"Health check error: {e}")
        finally:
            conn.close()

    def _restart_worker(self, job_type: str) -> None:
        """
        Restarts the worker process for the specified job type with exponential backoff.
        """
        if job_type in self.workers:
            worker = self.workers[job_type]
            worker.restart_count += 1
            old_worker = self.workers.pop(job_type)
            old_worker.process.terminate()
            old_worker.process.wait()
            self.logger.info(f"Terminated worker for {job_type}")

            # Exponential backoff: wait 2^restart_count seconds before restarting
            backoff_time = 2 ** worker.restart_count
            self.logger.info(f"Restarting worker for {job_type} in {backoff_time} seconds due to {worker.restart_count} failures")
            time.sleep(backoff_time)

        self._spawn_worker(job_type)

    def run(self) -> None:
        """
        Main loop of the orchestrator.
        Spawns initial workers, checks their health, and handles shutdown.
        """
        for job_type in JR_TYPES:
            self._spawn_worker(job_type)

        try:
            while not self.shutdown_flag:
                self._check_worker_health()
                time.sleep(1)
        except KeyboardInterrupt:
            self.shutdown_flag = True
            self.logger.info("Shutting down orchestrator...")
            for worker in list(self.workers.values()):
                worker.process.terminate()
                worker.process.wait()
            self.logger.info("All workers terminated")

def signal_handler(signum: int, frame) -> None:
    """
    Signal handler for SIGINT and SIGTERM.
    """
    orchestrator.shutdown_flag = True
    orchestrator.logger.info(f"Received signal {signum}, shutting down...")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(filename='/ganuda/logs/jr_orchestrator.log', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    orchestrator = JrOrchestrator()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    orchestrator.run()
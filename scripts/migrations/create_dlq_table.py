#!/usr/bin/env python3
"""Create the jr_failed_tasks_dlq table for Dead Letter Queue.

Kanban #1750 — Executor DLQ Wiring
Run once: python3 /ganuda/scripts/migrations/create_dlq_table.py

For Seven Generations
"""

import sys
sys.path.insert(0, '/ganuda')
from lib.secrets_loader import get_db_config
import psycopg2

def create_table():
    """Create the DLQ table if it doesn't exist."""
    db = get_db_config()
    conn = psycopg2.connect(**db)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS jr_failed_tasks_dlq (
            id SERIAL PRIMARY KEY,
            original_task_id INTEGER NOT NULL REFERENCES jr_work_queue(id),
            failure_reason TEXT NOT NULL,
            failure_traceback TEXT,
            step_number INTEGER,
            retry_count INTEGER DEFAULT 0,
            max_retries INTEGER DEFAULT 3,
            escalation_level INTEGER DEFAULT 0,
            assigned_escalation_target VARCHAR(100),
            resolution_status VARCHAR(50) DEFAULT 'unresolved',
            resolution_notes TEXT,
            next_retry_timestamp TIMESTAMP,
            last_retry_timestamp TIMESTAMP,
            resolved_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_dlq_resolution_status
            ON jr_failed_tasks_dlq(resolution_status);

        CREATE INDEX IF NOT EXISTS idx_dlq_next_retry
            ON jr_failed_tasks_dlq(next_retry_timestamp)
            WHERE resolution_status = 'retrying';

        CREATE INDEX IF NOT EXISTS idx_dlq_original_task
            ON jr_failed_tasks_dlq(original_task_id);

        CREATE INDEX IF NOT EXISTS idx_dlq_escalation
            ON jr_failed_tasks_dlq(escalation_level)
            WHERE escalation_level >= 2;
    """)

    conn.commit()
    print("[DLQ Migration] jr_failed_tasks_dlq table created successfully")

    # Verify
    cur.execute("SELECT COUNT(*) FROM jr_failed_tasks_dlq")
    count = cur.fetchone()[0]
    print(f"[DLQ Migration] Table has {count} existing entries")

    cur.close()
    conn.close()

if __name__ == '__main__':
    create_table()
    print("[DLQ Migration] Done — For Seven Generations")
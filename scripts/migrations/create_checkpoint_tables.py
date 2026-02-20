#!/usr/bin/env python3
"""Create step tracking and checkpoint tables for executor resume capability.

Kanban #1751 — Executor Checkpointing
Run once: python3 /ganuda/scripts/migrations/create_checkpoint_tables.py

For Seven Generations
"""

import sys
sys.path.insert(0, '/ganuda')
from lib.secrets_loader import get_db_config
import psycopg2

def create_tables():
    """Create step rewards and checkpoint tables."""
    db = get_db_config()
    conn = psycopg2.connect(**db)
    cur = conn.cursor()

    # Table 1: Step-level execution rewards (referenced by _record_step_result)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jr_step_rewards (
            id SERIAL PRIMARY KEY,
            task_id INTEGER NOT NULL,
            step_number INTEGER NOT NULL,
            step_type VARCHAR(50),
            target_file TEXT,
            step_content_hash VARCHAR(64),
            execution_result VARCHAR(20) NOT NULL DEFAULT 'pending',
            execution_time_ms INTEGER,
            error_detail TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(task_id, step_number)
        );

        CREATE INDEX IF NOT EXISTS idx_step_rewards_task
            ON jr_step_rewards(task_id);

        CREATE INDEX IF NOT EXISTS idx_step_rewards_result
            ON jr_step_rewards(execution_result);
    """)

    # Table 2: Task-level checkpoints (for resume-from-failure)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jr_task_checkpoints (
            id SERIAL PRIMARY KEY,
            task_id INTEGER NOT NULL,
            last_completed_step INTEGER NOT NULL DEFAULT 0,
            total_steps INTEGER,
            checkpoint_data JSONB,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(task_id)
        );

        CREATE INDEX IF NOT EXISTS idx_checkpoints_task
            ON jr_task_checkpoints(task_id);
    """)

    conn.commit()
    print("[Checkpoint Migration] Tables created: jr_step_rewards, jr_task_checkpoints")

    # Verify
    for table in ['jr_step_rewards', 'jr_task_checkpoints']:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"[Checkpoint Migration] {table}: {count} rows")

    cur.close()
    conn.close()

if __name__ == '__main__':
    create_tables()
    print("[Checkpoint Migration] Done — For Seven Generations")
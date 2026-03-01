#!/usr/bin/env python3
"""
Queue Living Cell Architecture Jr tasks into jr_work_queue.
Run on redfin with cherokee_venv: python3 /ganuda/scripts/queue_living_cell_tasks.py

Phase 1: Duplo Enzyme System (registry, composer, profiles, pipeline)
Phase 2: ATP Accounting (token counter)
Phase 3: Epigenetics (environmental modifiers)

Prerequisite: Run duplo_schema.sql on bluefin FIRST:
  psql -U claude -d zammad_production -f /ganuda/scripts/migrations/duplo_schema.sql
"""

import os
import sys
import hashlib
from datetime import datetime

sys.path.insert(0, "/ganuda")
from lib.ganuda_db import get_connection

TASKS = [
    # Phase 1: Foundation
    {
        "title": "Duplo Tool Registry (Enzyme Amino Acids)",
        "instruction_file": "/ganuda/docs/jr_instructions/JR-DUPLO-REGISTRY-MAR01-2026.md",
        "priority": 2,
        "assigned_jr": "Software Engineer Jr.",
        "source": "living-cell-architecture",
        "created_by": "TPM",
    },
    {
        "title": "Duplo Context Profiles (Enzyme Active Sites)",
        "instruction_file": "/ganuda/docs/jr_instructions/JR-DUPLO-CONTEXT-PROFILES-MAR01-2026.md",
        "priority": 3,
        "assigned_jr": "Software Engineer Jr.",
        "source": "living-cell-architecture",
        "created_by": "TPM",
    },
    {
        "title": "Duplo Composer (Enzyme Assembly)",
        "instruction_file": "/ganuda/docs/jr_instructions/JR-DUPLO-COMPOSER-MAR01-2026.md",
        "priority": 2,
        "assigned_jr": "Software Engineer Jr.",
        "source": "living-cell-architecture",
        "created_by": "TPM",
    },
    {
        "title": "Duplo Pipeline (Multi-Enzyme Complexes)",
        "instruction_file": "/ganuda/docs/jr_instructions/JR-DUPLO-PIPELINE-MAR01-2026.md",
        "priority": 3,
        "assigned_jr": "Software Engineer Jr.",
        "source": "living-cell-architecture",
        "created_by": "TPM",
    },
    # Phase 2: ATP Accounting
    {
        "title": "ATP Counter (Token Economics)",
        "instruction_file": "/ganuda/docs/jr_instructions/JR-ATP-COUNTER-MAR01-2026.md",
        "priority": 2,
        "assigned_jr": "Software Engineer Jr.",
        "source": "living-cell-architecture",
        "created_by": "TPM",
    },
    # Phase 3: Epigenetics
    {
        "title": "Epigenetic Modifiers (Environmental Gene Expression)",
        "instruction_file": "/ganuda/docs/jr_instructions/JR-EPIGENETIC-MODIFIERS-MAR01-2026.md",
        "priority": 3,
        "assigned_jr": "Software Engineer Jr.",
        "source": "living-cell-architecture",
        "created_by": "TPM",
    },
]


def queue_tasks():
    conn = get_connection()
    try:
        cur = conn.cursor()
        queued = 0
        for task in TASKS:
            task_id = hashlib.md5(
                f"living-cell-{task['title']}-{datetime.now().date()}".encode()
            ).hexdigest()

            cur.execute("""
                INSERT INTO jr_work_queue
                (task_id, title, instruction_file, priority, status,
                 assigned_jr, source, created_by, use_rlm,
                 sacred_fire_priority, parameters)
                VALUES (%s, %s, %s, %s, 'pending', %s, %s, %s, FALSE, FALSE,
                        '{"teg_plan": true}')
                ON CONFLICT (task_id) DO NOTHING
            """, (
                task_id, task["title"], task["instruction_file"],
                task["priority"], task["assigned_jr"],
                task["source"], task["created_by"],
            ))
            if cur.rowcount > 0:
                queued += 1
                print(f"  Queued: {task['title']} [{task_id[:8]}]")
            else:
                print(f"  Exists: {task['title']} [{task_id[:8]}]")

        conn.commit()
        print(f"\n{queued} tasks queued for Living Cell architecture")
    finally:
        conn.close()


if __name__ == "__main__":
    print("Living Cell Architecture — Queuing Jr Tasks")
    print("=" * 50)
    queue_tasks()

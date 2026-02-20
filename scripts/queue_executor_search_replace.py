#!/usr/bin/env python3
"""
Queue Jr tasks for the Executor Search-Replace Architecture.

Council Vote: ULTRATHINK-EXECUTOR-SEARCH-REPLACE-ARCHITECTURE-JAN31-2026 (7/7 APPROVE)

Batch 1 (independent): Module creation + integration test creation
Batch 2 (depends on Batch 1): Wire into executor
Batch 3 (depends on Batch 2): LLM prompt update + run integration tests

Usage: python3 /ganuda/scripts/queue_executor_search_replace.py [batch_number]
       No argument = queue Batch 1 only
"""

import sys
import os
import psycopg2
from datetime import datetime

DB_CONFIG = {
    'host': '192.168.132.222',
    'dbname': 'zammad_production',
    'user': 'claude',
    'password': os.environ.get('CHEROKEE_DB_PASS', '')
}

TASKS = {
    1: [
        {
            'task_id': 'EXECUTOR-SR-MODULE-001',
            'title': 'Create SearchReplaceEditor module (new file)',
            'instruction_file': '/ganuda/docs/jr_instructions/JR-EXECUTOR-SEARCH-REPLACE-MODULE-JAN31-2026.md',
            'priority': 1,
            'tags': ['executor', 'search-replace', 'phase1', 'new-file'],
        },
        {
            'task_id': 'EXECUTOR-SR-TEST-001',
            'title': 'Create search-replace integration test suite (new file)',
            'instruction_file': '/ganuda/docs/jr_instructions/JR-EXECUTOR-SR-INTEGRATION-TEST-JAN31-2026.md',
            'priority': 2,
            'tags': ['executor', 'search-replace', 'testing', 'new-file'],
        },
    ],
    2: [
        {
            'task_id': 'EXECUTOR-SR-WIRE-001',
            'title': 'Wire search-replace into task_executor.py (bash only)',
            'instruction_file': '/ganuda/docs/jr_instructions/JR-EXECUTOR-WIRE-SEARCH-REPLACE-JAN31-2026.md',
            'priority': 1,
            'tags': ['executor', 'search-replace', 'phase1', 'bash-only'],
        },
    ],
    3: [
        {
            'task_id': 'EXECUTOR-SR-PROMPT-001',
            'title': 'Update LLM prompts for search-replace format (bash only)',
            'instruction_file': '/ganuda/docs/jr_instructions/JR-EXECUTOR-LLM-PROMPT-SEARCH-REPLACE-JAN31-2026.md',
            'priority': 2,
            'tags': ['executor', 'search-replace', 'phase2', 'bash-only'],
        },
    ],
}


def read_instruction(filepath):
    """Read instruction file content."""
    with open(filepath, 'r') as f:
        return f.read()


def queue_batch(batch_num):
    """Queue all tasks in a batch."""
    if batch_num not in TASKS:
        print(f"ERROR: No batch {batch_num}. Available: {list(TASKS.keys())}")
        return

    tasks = TASKS[batch_num]
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    print(f"\n{'='*60}")
    print(f"QUEUING BATCH {batch_num} — {len(tasks)} task(s)")
    print(f"{'='*60}")

    for task in tasks:
        instruction_content = read_instruction(task['instruction_file'])

        cur.execute("""
            INSERT INTO jr_work_queue
            (task_id, title, description, instruction_file, instruction_content,
             priority, status, tags, created_by, source)
            VALUES (%s, %s, %s, %s, %s, %s, 'pending', %s, %s, %s)
            RETURNING id
        """, (
            task['task_id'],
            task['title'],
            f"Search-replace architecture — {task['title']}",
            task['instruction_file'],
            instruction_content,
            task['priority'],
            task['tags'],
            'tpm-claude-opus',
            'council-vote-sr-architecture'
        ))

        db_id = cur.fetchone()[0]
        print(f"  [{task['priority']}] #{db_id}: {task['title']}")
        print(f"       Task ID: {task['task_id']}")
        print(f"       Tags: {task['tags']}")

    conn.commit()

    # Show queue status
    cur.execute("""
        SELECT status, COUNT(*) FROM jr_work_queue
        WHERE tags && ARRAY['search-replace']
        GROUP BY status ORDER BY status
    """)
    print(f"\nSearch-replace task status:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}")

    cur.close()
    conn.close()

    print(f"\nBatch {batch_num} queued successfully.")
    if batch_num < max(TASKS.keys()):
        print(f"Run batch {batch_num + 1} after this batch completes:")
        print(f"  python3 /ganuda/scripts/queue_executor_search_replace.py {batch_num + 1}")


if __name__ == '__main__':
    batch = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    queue_batch(batch)

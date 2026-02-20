#!/usr/bin/env python3
"""
Queue VetAssist P0 Sprint + VA Linking + Executor Enhancements
Council Vote: 7/7 APPROVE (ULTRATHINK-VETASSIST-P0-SPRINT-AND-VA-LINKING-JAN30-2026)

Batch 1: 6 independent tasks (queue immediately)
Batch 2: 3 tasks (queue after Batch 1 dependencies complete)
Batch 3: 1 task (queue after Batch 2)
Batch 4: 1 task (queue after Batch 3)

Usage:
    python3 /ganuda/scripts/queue_vetassist_p0_sprint.py [--batch 1|2|3|4|all]

For Seven Generations — Cherokee AI Federation
"""

import psycopg2
import json
import sys
import os
from datetime import datetime

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': os.environ.get('CLAUDE_DB_PASSWORD', '')
}

ASSIGNED_JR = 'it_triad_jr'
INSTRUCTION_BASE = '/ganuda/docs/jr_instructions'

# ============================================================================
# BATCH DEFINITIONS
# ============================================================================

BATCH_1 = [
    {
        'task_id': 'VETASSIST-COMP-TABLE-001',
        'title': 'Create va_compensation_rates table',
        'description': (
            'Create and seed the va_compensation_rates table with 2025 VA compensation rates. '
            'The calculator computes combined ratings but cannot return dollar amounts without this table. '
            'Turtle caveat: mark rates as estimated until verified against VA.gov.'
        ),
        'instruction_file': f'{INSTRUCTION_BASE}/JR-VETASSIST-CALCULATOR-COMPENSATION-TABLE-JAN31-2026.md',
        'priority': 1,
        'tags': ['vetassist', 'database', 'calculator', 'p0'],
    },
    {
        'task_id': 'VETASSIST-EVIDENCE-MOUNT-001',
        'title': 'Mount evidence checklist router + fix wizard routing',
        'description': (
            'Mount evidence_checklist.py in the FastAPI router (currently 96 lines of unused code). '
            'Fix wizard forms routing conflict: literal /forms must register before wildcard /{session_id}. '
            'Gecko addendum: run import pre-check before mounting.'
        ),
        'instruction_file': f'{INSTRUCTION_BASE}/JR-VETASSIST-MOUNT-EVIDENCE-CHECKLIST-JAN31-2026.md',
        'priority': 1,
        'tags': ['vetassist', 'routing', 'backend', 'p0'],
    },
    {
        'task_id': 'VETASSIST-TYPE-FIX-001',
        'title': 'Fix claim_id integer to string type mismatch (IDOR remediation)',
        'description': (
            'Change claim_id: int to claim_id: str in 4 files (19 functions). '
            'Integer claim IDs are sequentially guessable (IDOR risk per Crawdad). '
            'Files: evidence_analysis.py, export.py, workbench.py, routers.py.'
        ),
        'instruction_file': f'{INSTRUCTION_BASE}/JR-VETASSIST-FIX-CLAIM-ID-TYPES-JAN30-2026.md',
        'priority': 1,
        'tags': ['vetassist', 'security', 'backend', 'p0', 'crawdad'],
    },
    {
        'task_id': 'EXECUTOR-VERIFY-001',
        'title': 'Phase 17: Verification Executor',
        'description': (
            'Add post-execution verification to Jr task executor. '
            'SQL INSERT → SELECT COUNT to confirm rows. CREATE TABLE → check information_schema. '
            'File write → check exists + non-empty. Catches silent failures. '
            'Eagle Eye priority: deploy before Phase 11 so self-healing has verification data.'
        ),
        'instruction_file': f'{INSTRUCTION_BASE}/JR-EXECUTOR-VERIFICATION-JAN30-2026.md',
        'priority': 2,
        'tags': ['executor', 'verification', 'phase17', 'p1'],
    },
    {
        'task_id': 'VALINK-MIGRATION-001',
        'title': 'VA Account Linking: Database migration (va_icn, va_linked_at)',
        'description': (
            'Add va_icn VARCHAR(50) UNIQUE and va_linked_at TIMESTAMPTZ columns to users table. '
            'Additive-only migration, safe on live database. '
            'Blocks all subsequent VA linking phases.'
        ),
        'instruction_file': f'{INSTRUCTION_BASE}/JR-VETASSIST-VA-LINK-MIGRATION-JAN30-2026.md',
        'priority': 2,
        'tags': ['vetassist', 'database', 'va-linking', 'phase1'],
    },
    {
        'task_id': 'VALINK-LOGIN-CLARITY-001',
        'title': 'Login page: Add "no VA account needed" callout',
        'description': (
            'Add green callout box below VA.gov login button on login page. '
            'Message: "New to VetAssist? You don\'t need a VA.gov account to get started." '
            'Independent of all other phases, pure frontend copy change.'
        ),
        'instruction_file': f'{INSTRUCTION_BASE}/JR-VETASSIST-LOGIN-CLARITY-JAN30-2026.md',
        'priority': 3,
        'tags': ['vetassist', 'frontend', 'ux', 'va-linking', 'phase5'],
    },
]

BATCH_2 = [
    {
        'task_id': 'EXECUTOR-SELFHEAL-001',
        'title': 'Phase 11: Self-Healing Retry Loop',
        'description': (
            'Add Reflexion-based retry to Jr executor. On failure: reflect → modify approach → retry (max 2). '
            'Eagle Eye addendum: snapshot current failure rate before deploying as baseline.'
        ),
        'instruction_file': f'{INSTRUCTION_BASE}/JR-EXECUTOR-SELF-HEALING-RETRY-JAN30-2026.md',
        'priority': 2,
        'tags': ['executor', 'self-healing', 'phase11', 'p1'],
    },
    {
        'task_id': 'EXECUTOR-RESEARCH-SEED-001',
        'title': 'Phase 10: Research-to-Seed Pipeline',
        'description': (
            'Chain web fetch → LLM schema extraction → SQL INSERT → verification. '
            'Unblocks autonomous database population from web sources. '
            'Crawdad addendum: ensure parameterized queries, not string interpolation for SQL.'
        ),
        'instruction_file': f'{INSTRUCTION_BASE}/JR-EXECUTOR-RESEARCH-TO-SEED-JAN30-2026.md',
        'priority': 2,
        'tags': ['executor', 'research', 'phase10', 'p1'],
    },
    {
        'task_id': 'VALINK-ENDPOINT-001',
        'title': 'VA Account Linking: POST /auth/link-va endpoint',
        'description': (
            'Add link-va endpoint to auth.py. Decodes VA JWT, extracts ICN, links to users row. '
            'Rate limit 2/min. 409 on ICN conflicts. Never exposes va_icn in responses. '
            'Also updates User model and UserResponse schema with va_linked fields.'
        ),
        'instruction_file': f'{INSTRUCTION_BASE}/JR-VETASSIST-VA-LINK-ENDPOINT-JAN30-2026.md',
        'priority': 2,
        'tags': ['vetassist', 'backend', 'va-linking', 'phase2'],
    },
]

BATCH_3 = [
    {
        'task_id': 'VALINK-CALLBACK-001',
        'title': 'VA Account Linking: OAuth callback linking + linked-login modes',
        'description': (
            'Modify va_callback() to support 3 modes: linking (session_id present), '
            'linked-login (ICN found in users table), and default (existing behavior). '
            'The bridge between the two auth systems.'
        ),
        'instruction_file': f'{INSTRUCTION_BASE}/JR-VETASSIST-VA-CALLBACK-LINKING-JAN30-2026.md',
        'priority': 2,
        'tags': ['vetassist', 'backend', 'va-linking', 'phase3'],
    },
]

BATCH_4 = [
    {
        'task_id': 'VALINK-FRONTEND-001',
        'title': 'VA Account Linking: Frontend settings page + VA success updates',
        'description': (
            'Create /settings page with VA linking button. Update va-success page for 3 modes. '
            'Add linkVAAccount() to API client. Add va_linked to User type. Add Settings to nav.'
        ),
        'instruction_file': f'{INSTRUCTION_BASE}/JR-VETASSIST-VA-LINK-FRONTEND-JAN30-2026.md',
        'priority': 2,
        'tags': ['vetassist', 'frontend', 'va-linking', 'phase4'],
    },
]

ALL_BATCHES = {
    1: BATCH_1,
    2: BATCH_2,
    3: BATCH_3,
    4: BATCH_4,
}


def get_baseline_snapshot(conn):
    """Eagle Eye requirement: snapshot current task status before queueing."""
    cur = conn.cursor()
    cur.execute("""
        SELECT status, COUNT(*)
        FROM jr_work_queue
        GROUP BY status
        ORDER BY status
    """)
    rows = cur.fetchall()
    cur.close()

    print("\n=== BASELINE SNAPSHOT (Eagle Eye) ===")
    for status, count in rows:
        print(f"  {status}: {count}")
    print(f"  Timestamp: {datetime.now().isoformat()}")
    print("=" * 40)
    return dict(rows)


def queue_batch(conn, batch_num, tasks):
    """Queue a batch of tasks to the Jr work queue."""
    cur = conn.cursor()
    queued = []

    print(f"\n--- Queuing Batch {batch_num} ({len(tasks)} tasks) ---")

    for task in tasks:
        # Verify instruction file exists
        instruction_file = task.get('instruction_file')
        if instruction_file and not os.path.exists(instruction_file):
            print(f"  WARNING: Instruction file not found: {instruction_file}")
            print(f"  Skipping task: {task['task_id']}")
            continue

        try:
            cur.execute("""
                INSERT INTO jr_work_queue (
                    task_id, title, description, priority,
                    assigned_jr, instruction_file, status,
                    progress_percent, created_at, use_rlm,
                    tags
                )
                VALUES (%s, %s, %s, %s, %s, %s, 'pending', 0, NOW(), false, %s)
                RETURNING id, task_id
            """, (
                task['task_id'],
                task['title'],
                task['description'],
                task['priority'],
                ASSIGNED_JR,
                task.get('instruction_file'),
                task.get('tags', []),
            ))

            db_id, returned_id = cur.fetchone()
            queued.append((db_id, returned_id))
            print(f"  Queued: {returned_id} (DB #{db_id}, P{task['priority']})")

        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            print(f"  SKIP (already queued): {task['task_id']}")
        except Exception as e:
            conn.rollback()
            print(f"  ERROR queuing {task['task_id']}: {e}")

    conn.commit()
    cur.close()

    print(f"\n  Batch {batch_num}: {len(queued)}/{len(tasks)} tasks queued")
    return queued


def main():
    batch_arg = 'all'
    if len(sys.argv) > 1:
        if sys.argv[1] == '--batch' and len(sys.argv) > 2:
            batch_arg = sys.argv[2]
        else:
            batch_arg = sys.argv[1]

    print("=" * 60)
    print("VetAssist P0 Sprint — Council-Approved Task Queue")
    print("Vote: 7/7 APPROVE (confidence 0.89)")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)

    conn = psycopg2.connect(**DB_CONFIG)

    try:
        # Eagle Eye baseline
        get_baseline_snapshot(conn)

        if batch_arg == 'all':
            for batch_num in sorted(ALL_BATCHES.keys()):
                queue_batch(conn, batch_num, ALL_BATCHES[batch_num])
            print("\n*** All 4 batches queued. ***")
            print("NOTE: Batches 2-4 have dependencies. Monitor Batch 1 completion")
            print("before Batch 2 tasks execute. The Jr worker processes sequentially,")
            print("so priority ordering handles this naturally.")
        elif batch_arg.isdigit():
            batch_num = int(batch_arg)
            if batch_num in ALL_BATCHES:
                queue_batch(conn, batch_num, ALL_BATCHES[batch_num])
            else:
                print(f"ERROR: Batch {batch_num} not found. Valid: 1, 2, 3, 4")
                sys.exit(1)
        else:
            print(f"Usage: {sys.argv[0]} [--batch 1|2|3|4|all]")
            sys.exit(1)

        # Post-queue status
        cur = conn.cursor()
        cur.execute("""
            SELECT status, COUNT(*)
            FROM jr_work_queue
            WHERE created_at > NOW() - INTERVAL '5 minutes'
            GROUP BY status
        """)
        rows = cur.fetchall()
        cur.close()

        print("\n=== QUEUE STATUS (last 5 min) ===")
        for status, count in rows:
            print(f"  {status}: {count}")

    finally:
        conn.close()

    print("\nFor Seven Generations")


if __name__ == '__main__':
    main()

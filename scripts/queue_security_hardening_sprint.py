#!/usr/bin/env python3
"""
Queue Security Hardening Sprint — 7-Phase Waterfall
Council Vote: Security Audit findings → 2 CRITICAL, 5 HIGH
Ultrathink: ULTRATHINK-SECURITY-HARDENING-AI-RED-BLUE-TEAM-FEB02-2026

Phase 1-2: P0 (credential rotation + executor sandboxing) — no dependencies
Phase 3-6: P1 (network, AI red/blue team, incident response) — after Phase 2
Phase 7:   P2 (supply chain continuous) — after Phase 3

Assigned across active workers:
  - it_triad_jr:          Phase 1 (credentials), Phase 6 (incident response), Phase 7 (supply chain)
  - Software Engineer Jr: Phase 2 (sandboxing), Phase 4 (red team), Phase 5 (blue team)
  - Infrastructure Jr:    Phase 3 (network/host hardening)

Usage:
    python3 /ganuda/scripts/queue_security_hardening_sprint.py [--batch 1|2|3|all]

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
    'password': os.environ.get('CLAUDE_DB_PASSWORD', 'jawaseatlasers2')
}

INSTRUCTION_BASE = '/ganuda/docs/jr_instructions'

# ============================================================================
# BATCH DEFINITIONS
# ============================================================================

# Batch 1: P0 — Independent, queue immediately
BATCH_1 = [
    {
        'task_id': 'SECURITY-CRED-ROTATE-001',
        'title': 'Phase 1: Credential Rotation — secrets.env + secrets_loader.py',
        'description': (
            'CRITICAL: Hardcoded password jawaseatlasers2 found in 1,874 files. '
            'Create /ganuda/config/secrets.env (chmod 600) with all credentials. '
            'Create /ganuda/lib/secrets_loader.py with three-tier resolution (file/env/vault). '
            'Add .gitignore entries for secrets. Install gitleaks pre-commit hook. '
            'Create KB migration guide. Does NOT modify existing files — creates the infrastructure.'
        ),
        'assigned_jr': 'it_triad_jr',
        'instruction_file': f'{INSTRUCTION_BASE}/JR-SECURITY-PHASE1-CREDENTIAL-ROTATION-FEB02-2026.md',
        'priority': 1,
        'tags': ['security', 'credentials', 'p0', 'phase1'],
    },
    {
        'task_id': 'SECURITY-SANDBOX-001',
        'title': 'Phase 2: Executor Sandboxing — command_sanitizer.py + execution_audit.py',
        'description': (
            'CRITICAL: Jr executor runs arbitrary code via shell=True with no validation. '
            'Create /ganuda/jr_executor/command_sanitizer.py — blocks rm -rf, dd, curl|bash, eval, '
            'fork bombs; blocks DROP/TRUNCATE/DELETE-without-WHERE in SQL. '
            'Create /ganuda/jr_executor/execution_audit.py — logs to file + PostgreSQL. '
            'Create execution_audit_log table. Create KB integration guide. '
            'Does NOT modify task_executor.py — TPM wires it in after validation.'
        ),
        'assigned_jr': 'Software Engineer Jr.',
        'instruction_file': f'{INSTRUCTION_BASE}/JR-SECURITY-PHASE2-EXECUTOR-SANDBOXING-FEB02-2026.md',
        'priority': 1,
        'tags': ['security', 'executor', 'sandboxing', 'p0', 'phase2'],
    },
]

# Batch 2: P1 — Depends on Phase 2 (sandboxing) being complete
BATCH_2 = [
    {
        'task_id': 'SECURITY-NETWORK-001',
        'title': 'Phase 3: Network & Host Hardening — nftables + fail2ban + Caddy + PostgreSQL SSL',
        'description': (
            'Deploy nftables firewall rules for redfin (public-facing) and bluefin (DB). '
            'Configure fail2ban with Caddy auth filter, PostgreSQL filter, Telegram alerts. '
            'Add Caddy security headers (HSTS, CSP, X-Frame-Options). '
            'Enable PostgreSQL SSL + pgAudit. Create deployment script with --dry-run.'
        ),
        'assigned_jr': 'Infrastructure Jr.',
        'instruction_file': f'{INSTRUCTION_BASE}/JR-SECURITY-PHASE3-NETWORK-HOST-HARDENING-FEB02-2026.md',
        'priority': 3,
        'tags': ['security', 'network', 'firewall', 'p1', 'phase3'],
    },
    {
        'task_id': 'SECURITY-RED-TEAM-001',
        'title': 'Phase 4: AI Red Team Test Suite — 28 tests across 5 attack vectors',
        'description': (
            'Create /ganuda/security/ai_red_team/ with test runner + 5 modules: '
            'prompt injection (8 tests), council manipulation (5), PII extraction (5), '
            'memory poisoning (5), crisis evasion (5). All test data prefixed REDTEAM_ for cleanup. '
            'PASS = attack blocked. FAIL = vulnerability found. JSON + markdown reports.'
        ),
        'assigned_jr': 'Software Engineer Jr.',
        'instruction_file': f'{INSTRUCTION_BASE}/JR-SECURITY-PHASE4-AI-RED-TEAM-FEB02-2026.md',
        'priority': 3,
        'tags': ['security', 'ai-red-team', 'testing', 'p1', 'phase4'],
    },
    {
        'task_id': 'SECURITY-BLUE-TEAM-001',
        'title': 'Phase 5: AI Blue Team Monitoring — 5 detectors + security monitor daemon',
        'description': (
            'Create /ganuda/security/ai_blue_team/ with 5 modules: '
            'prompt injection detector (15+ signatures), output PII scanner (7 patterns + Luhn), '
            'queue validator, council anomaly detector, security monitor daemon. '
            'Deploy as systemd service. 5-minute monitoring interval.'
        ),
        'assigned_jr': 'Software Engineer Jr.',
        'instruction_file': f'{INSTRUCTION_BASE}/JR-SECURITY-PHASE5-AI-BLUE-TEAM-MONITORING-FEB02-2026.md',
        'priority': 4,
        'tags': ['security', 'ai-blue-team', 'monitoring', 'p1', 'phase5'],
    },
    {
        'task_id': 'SECURITY-INCIDENT-001',
        'title': 'Phase 6: Incident Response Playbook + Break Glass Scripts',
        'description': (
            'Create incident response playbook (SEV1-SEV4, escalation tree, containment for 7 attack types). '
            'Create collect_incident_evidence.sh (system/network/logs/DB state + SHA-256 manifest). '
            'Create break_glass.sh (8 emergency actions: isolate-network, stop-database, etc). '
            'All scripts require YES confirmation or --force flag.'
        ),
        'assigned_jr': 'it_triad_jr',
        'instruction_file': f'{INSTRUCTION_BASE}/JR-SECURITY-PHASE6-INCIDENT-RESPONSE-PLAYBOOK-FEB02-2026.md',
        'priority': 4,
        'tags': ['security', 'incident-response', 'playbook', 'p1', 'phase6'],
    },
]

# Batch 3: P2 — Depends on Phase 3 (network hardening) being complete
BATCH_3 = [
    {
        'task_id': 'SECURITY-SUPPLY-CHAIN-001',
        'title': 'Phase 7: Supply Chain & Continuous Security — model checksums + dependency scanning',
        'description': (
            'Create model checksum baselines (SHA-256 for all LLM/ML models). '
            'Generate dependency locks + CycloneDX SBOM + pip-audit scanning. '
            'Create unified weekly security_check.sh (7 checks). '
            'Create dependency_checker.py daemon. Deploy as systemd weekly timer (Sunday 03:00).'
        ),
        'assigned_jr': 'it_triad_jr',
        'instruction_file': f'{INSTRUCTION_BASE}/JR-SECURITY-PHASE7-SUPPLY-CHAIN-CONTINUOUS-FEB02-2026.md',
        'priority': 5,
        'tags': ['security', 'supply-chain', 'continuous', 'p2', 'phase7'],
    },
]

ALL_BATCHES = {
    1: BATCH_1,
    2: BATCH_2,
    3: BATCH_3,
}


def get_baseline_snapshot(conn):
    """Snapshot current queue status before queueing."""
    cur = conn.cursor()
    cur.execute("""
        SELECT status, COUNT(*)
        FROM jr_work_queue
        GROUP BY status
        ORDER BY status
    """)
    rows = cur.fetchall()
    cur.close()

    print("\n=== BASELINE SNAPSHOT ===")
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
                task['assigned_jr'],
                task.get('instruction_file'),
                task.get('tags', []),
            ))

            db_id, returned_id = cur.fetchone()
            queued.append((db_id, returned_id))
            print(f"  Queued: {returned_id} (DB #{db_id}, P{task['priority']}, Jr: {task['assigned_jr']})")

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
    print("Security Hardening Sprint — 7-Phase Waterfall")
    print("Audit: 2 CRITICAL + 5 HIGH findings")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)

    conn = psycopg2.connect(**DB_CONFIG)

    try:
        get_baseline_snapshot(conn)

        if batch_arg == 'all':
            for batch_num in sorted(ALL_BATCHES.keys()):
                queue_batch(conn, batch_num, ALL_BATCHES[batch_num])
            print("\n*** All 3 batches queued (7 phases). ***")
            print("Execution order enforced by priority:")
            print("  P1: Phase 1 (credentials) + Phase 2 (sandboxing) — run first")
            print("  P3: Phase 3 (network) + Phase 4 (red team) — after P0 complete")
            print("  P4: Phase 5 (blue team) + Phase 6 (incident) — after red team")
            print("  P5: Phase 7 (supply chain) — final")
        elif batch_arg.isdigit():
            batch_num = int(batch_arg)
            if batch_num in ALL_BATCHES:
                queue_batch(conn, batch_num, ALL_BATCHES[batch_num])
            else:
                print(f"ERROR: Batch {batch_num} not found. Valid: 1, 2, 3")
                sys.exit(1)
        else:
            print(f"Usage: {sys.argv[0]} [--batch 1|2|3|all]")
            sys.exit(1)

        # Post-queue status
        cur = conn.cursor()
        cur.execute("""
            SELECT task_id, title, priority, assigned_jr, status
            FROM jr_work_queue
            WHERE task_id LIKE 'SECURITY-%%'
            ORDER BY priority ASC, created_at ASC
        """)
        rows = cur.fetchall()
        cur.close()

        print("\n=== SECURITY SPRINT QUEUE STATUS ===")
        for task_id, title, priority, assigned_jr, status in rows:
            print(f"  P{priority} [{status:10s}] {task_id} → {assigned_jr}")

    finally:
        conn.close()

    print("\nFor Seven Generations")


if __name__ == '__main__':
    main()

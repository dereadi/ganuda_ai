#!/usr/bin/env python3
"""Credential Migration Helper — Phase 1 to Phase 2 bridge.

Kanban #1754 — Security: Migrate Password Files to secrets_loader
Scans Python files for known hardcoded credential patterns and reports
which files still need migration. Optionally applies fixes.

Usage:
    python3 /ganuda/scripts/security/credential_migration.py --scan
    python3 /ganuda/scripts/security/credential_migration.py --apply --file PATH

For Seven Generations
"""

import os
import re
import sys
import argparse
from datetime import datetime

GANUDA_ROOT = '/ganuda'

# Patterns that indicate hardcoded credentials
PATTERNS = [
    {
        'name': 'DB_CONFIG dict with password',
        'regex': re.compile(
            r"DB_CONFIG\s*=\s*\{[^}]*'password'\s*:\s*'[^']{8,}'",
            re.DOTALL
        ),
        'severity': 'CRITICAL',
    },
    {
        'name': 'psycopg2.connect with password kwarg',
        'regex': re.compile(
            r"psycopg2\.connect\([^)]*password\s*=\s*['\"][^'\"]{8,}['\"]",
            re.DOTALL
        ),
        'severity': 'HIGH',
    },
    {
        'name': 'os.environ.get DB_PASSWORD with fallback',
        'regex': re.compile(
            r"os\.environ\.get\(\s*['\"]DB_PASSWORD['\"],\s*'[^']{8,}'"
        ),
        'severity': 'HIGH',
    },
]

# Directories to skip
SKIP_DIRS = {
    '__pycache__', '.git', 'venv', '.venv', 'node_modules',
    'site-packages', 'amem_venv', 'cherokee_training_env',
    'icl_research_env', 'venv-django', 'week1_integration_env',
}

# Files already migrated (use secrets_loader)
ALREADY_MIGRATED = {
    'jr_executor/jr_queue_client.py',
    'jr_executor/jr_task_executor.py',
}


def scan_files():
    """Scan all Python files for hardcoded credential patterns."""
    findings = []

    for root, dirs, files in os.walk(GANUDA_ROOT):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for fname in files:
            if not fname.endswith('.py'):
                continue

            filepath = os.path.join(root, fname)
            rel_path = os.path.relpath(filepath, GANUDA_ROOT)

            if rel_path in ALREADY_MIGRATED:
                continue

            try:
                with open(filepath, 'r', errors='ignore') as f:
                    content = f.read()
            except (IOError, OSError):
                continue

            # Check if already uses secrets_loader
            uses_loader = 'secrets_loader' in content or 'get_db_config' in content

            for pattern in PATTERNS:
                matches = pattern['regex'].findall(content)
                if matches:
                    findings.append({
                        'file': rel_path,
                        'pattern': pattern['name'],
                        'severity': pattern['severity'],
                        'uses_loader': uses_loader,
                        'match_count': len(matches),
                    })

    return findings


def print_report(findings):
    """Print a formatted scan report."""
    print("=" * 70)
    print(f"CREDENTIAL MIGRATION SCAN — {datetime.now().isoformat()}")
    print(f"Cherokee AI Federation — Kanban #1754")
    print("=" * 70)

    if not findings:
        print("\nNo hardcoded credentials found. All clear.")
        return

    # Group by severity
    by_severity = {}
    for f in findings:
        by_severity.setdefault(f['severity'], []).append(f)

    for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
        items = by_severity.get(severity, [])
        if not items:
            continue

        print(f"\n{severity} ({len(items)} findings):")
        for item in sorted(items, key=lambda x: x['file']):
            loader_status = " [PARTIAL — already imports secrets_loader]" if item['uses_loader'] else ""
            print(f"  [{item['severity']}] {item['file']}")
            print(f"         Pattern: {item['pattern']}{loader_status}")

    # Summary
    total = len(findings)
    critical = len(by_severity.get('CRITICAL', []))
    high = len(by_severity.get('HIGH', []))
    already_partial = sum(1 for f in findings if f['uses_loader'])

    print(f"\nSUMMARY: {total} findings ({critical} CRITICAL, {high} HIGH)")
    print(f"  Already partially migrated: {already_partial}")
    print(f"  Need full migration: {total - already_partial}")
    print(f"\nRecommendation: Fix CRITICAL files first, then sweep HIGH.")
    print(f"Pattern: Replace DB_CONFIG dict with `from lib.secrets_loader import get_db_config`")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Credential Migration Helper')
    parser.add_argument('--scan', action='store_true', help='Scan for hardcoded credentials')
    args = parser.parse_args()

    if args.scan or len(sys.argv) == 1:
        findings = scan_files()
        print_report(findings)
    else:
        parser.print_help()
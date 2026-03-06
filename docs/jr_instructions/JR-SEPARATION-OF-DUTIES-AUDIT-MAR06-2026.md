# Jr Instruction: Separation of Duties Audit Script

**Task**: Create an audit script that checks for separation of duties violations in the federation
**Priority**: 4
**Story Points**: 3
**Epic**: #1974

## Context

Security principle: no single agent/process should both write data AND validate that same data. We need a script that scans for potential violations: same DB user writing and reading audit data, same process creating and approving tasks, etc.

## Steps

### Step 1: Create the audit script

Create `/ganuda/scripts/security/separation_of_duties_audit.py`

```python
#!/usr/bin/env python3
"""Separation of Duties Audit — scan for single-entity write+validate patterns."""

import os
import re
import psycopg2
from datetime import datetime


DB_HOST = os.environ.get("CHEROKEE_DB_HOST", "192.168.132.222")
DB_NAME = os.environ.get("CHEROKEE_DB_NAME", "zammad_production")
DB_USER = os.environ.get("CHEROKEE_DB_USER", "claude")
DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")


def load_secrets():
    global DB_PASS
    if not DB_PASS:
        try:
            with open("/ganuda/config/secrets.env") as f:
                for line in f:
                    m = re.match(r"^(\w+)=(.+)$", line.strip())
                    if m:
                        os.environ[m.group(1)] = m.group(2)
            DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")
        except FileNotFoundError:
            pass


def audit_db_roles(cur):
    """Check if the same DB role has both write and superuser privileges."""
    findings = []
    cur.execute("SELECT rolname, rolsuper, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolcanlogin = true")
    for row in cur.fetchall():
        name, superuser, createdb, createrole = row
        if superuser:
            findings.append(f"CRITICAL: DB role '{name}' has SUPERUSER — can bypass all checks")
        if createdb and createrole:
            findings.append(f"WARNING: DB role '{name}' can create both databases and roles")
    return findings


def audit_task_self_approval(cur):
    """Check for tasks where creator == completer (self-approval)."""
    findings = []
    cur.execute("""
        SELECT id, title, created_by, assigned_jr
        FROM jr_work_queue
        WHERE status = 'completed'
        AND created_by = assigned_jr
        AND created_by IS NOT NULL
        LIMIT 10
    """)
    rows = cur.fetchall()
    if rows:
        findings.append(f"INFO: {len(rows)} tasks where creator == assigned Jr (self-assignment, not self-approval per se)")
    return findings


def audit_council_vote_diversity(cur):
    """Check for council votes with insufficient voter diversity."""
    findings = []
    cur.execute("""
        SELECT vote_hash, COUNT(DISTINCT voter) as voters
        FROM council_votes
        WHERE voted_at > NOW() - INTERVAL '7 days'
        GROUP BY vote_hash
        HAVING COUNT(DISTINCT voter) < 3
    """)
    rows = cur.fetchall()
    if rows:
        findings.append(f"WARNING: {len(rows)} council votes in last 7 days had fewer than 3 distinct voters")
    return findings


def audit_single_db_user(cur):
    """Flag if all operations use the same DB user."""
    findings = []
    cur.execute("SELECT DISTINCT usename FROM pg_stat_activity WHERE datname = %s", (DB_NAME,))
    users = [r[0] for r in cur.fetchall()]
    if len(users) == 1:
        findings.append(f"WARNING: Only one DB user active ('{users[0]}') — no role separation")
    else:
        findings.append(f"INFO: {len(users)} distinct DB users active: {', '.join(users)}")
    return findings


def main():
    load_secrets()
    conn = psycopg2.connect(host=DB_HOST, port=5432, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cur = conn.cursor()

    print(f"=== Separation of Duties Audit ===")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Database: {DB_NAME}@{DB_HOST}")
    print()

    all_findings = []
    checks = [
        ("DB Role Privileges", audit_db_roles),
        ("Task Self-Approval", audit_task_self_approval),
        ("Council Vote Diversity", audit_council_vote_diversity),
        ("Single DB User", audit_single_db_user),
    ]

    for name, check_fn in checks:
        print(f"--- {name} ---")
        findings = check_fn(cur)
        for f in findings:
            print(f"  {f}")
        if not findings:
            print("  PASS: No issues found")
        all_findings.extend(findings)
        print()

    critical = sum(1 for f in all_findings if f.startswith("CRITICAL"))
    warnings = sum(1 for f in all_findings if f.startswith("WARNING"))
    print(f"Summary: {critical} critical, {warnings} warnings, {len(all_findings)} total findings")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
```

## Verification

1. Run: `cd /ganuda && python3 scripts/security/separation_of_duties_audit.py`
2. Should produce audit report with findings categorized by severity

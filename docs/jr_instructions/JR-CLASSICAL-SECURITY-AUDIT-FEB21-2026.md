# JR Instruction: Classical Security Audit

**Task**: SEC-AUDIT-001
**Priority**: P0
**Kanban**: #1871 (3 SP)
**use_rlm**: false
**assigned_jr**: Software Engineer Jr.
**Council Vote**: PROCEED WITH CAUTION (0.846 confidence, 1.0 agreement)
**Long Man Phase**: BUILD — Quantum/PQC Hardening Sprint

## Context

Council deliberation on Google's quantum error correction breakthrough identified that classical security hardening gaps are MORE urgent than post-quantum migration. Raven (contrarian specialist): "Fix the screen door before adding the titanium lock." Before we pursue PQC upgrades, we must verify baselines are solid.

This script audits all reachable federation nodes for classical security posture and produces a report.

The script must run on redfin using `/ganuda/home/dereadi/cherokee_venv/bin/python3`.

## Changes

### Change 1: Create the classical security audit script

Create `/ganuda/scripts/security_audit_classical.py`

```python
<<<<<<< SEARCH
=======
#!/usr/bin/env python3
"""Classical Security Audit — Federation-Wide.

Checks fail2ban, nftables, SSH config, PostgreSQL TLS enforcement,
and plaintext credential exposure across all reachable nodes.
Produces report at /ganuda/reports/security_audit_classical_feb2026.md

Council mandate: Quantum/PQC Sprint, Raven P0.
"""

import subprocess
import os
import re
import sys
from datetime import datetime

NODES = {
    "redfin": {"host": "localhost", "ssh": False},
    "greenfin": {"host": "greenfin", "ssh": True},
    "bluefin": {"host": "bluefin", "ssh": True},
}

REPORT_PATH = "/ganuda/reports/security_audit_classical_feb2026.md"
SCAN_DIRS = ["/ganuda/scripts", "/ganuda/config", "/ganuda/services", "/ganuda/telegram_bot"]

# Patterns that look like credentials (conservative)
CREDENTIAL_PATTERNS = [
    r'(?i)password\s*[=:]\s*["\']?[A-Za-z0-9!@#$%^&*]{8,}',
    r'(?i)api_key\s*[=:]\s*["\']?[A-Za-z0-9_-]{16,}',
    r'(?i)secret\s*[=:]\s*["\']?[A-Za-z0-9_-]{16,}',
    r'(?i)token\s*[=:]\s*["\']?[A-Za-z0-9_-]{20,}',
    r'PGPASSWORD\s*=\s*["\']?[A-Za-z0-9!@#$%^&*]{8,}',
]

# Files that SHOULD contain credentials (skip these)
CREDENTIAL_ALLOWLIST = [
    ".env",
    "token.pickle",
    ".pyc",
    "__pycache__",
    "node_modules",
    "venv",
    "cherokee_venv",
    ".git",
]


def run_local(cmd):
    """Run command locally, return stdout."""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return r.stdout.strip()
    except Exception as e:
        return f"[ERROR: {e}]"


def run_ssh(host, cmd):
    """Run command via SSH, return stdout."""
    try:
        r = subprocess.run(
            f"ssh -o ConnectTimeout=10 {host} '{cmd}'",
            shell=True, capture_output=True, text=True, timeout=30
        )
        return r.stdout.strip()
    except Exception as e:
        return f"[ERROR: {e}]"


def run_on(node_name, node_info, cmd):
    """Run command on a node (local or SSH)."""
    if node_info["ssh"]:
        return run_ssh(node_info["host"], cmd)
    return run_local(cmd)


def check_fail2ban(node_name, node_info):
    """Check fail2ban status on a node."""
    status = run_on(node_name, node_info, "systemctl is-active fail2ban 2>/dev/null || echo INACTIVE")
    jails = run_on(node_name, node_info, "sudo fail2ban-client status 2>/dev/null | head -5 || echo 'NO_ACCESS'")
    return {"status": status, "jails": jails}


def check_nftables(node_name, node_info):
    """Check nftables ruleset on a node."""
    policy = run_on(node_name, node_info, "sudo nft list chain inet filter input 2>/dev/null | grep policy || echo 'NO_NFT'")
    rule_count = run_on(node_name, node_info, "sudo nft list ruleset 2>/dev/null | wc -l || echo 0")
    return {"input_policy": policy, "rule_count": rule_count}


def check_ssh_config(node_name, node_info):
    """Check SSH server configuration."""
    config_items = {}
    for key in ["PermitRootLogin", "PasswordAuthentication", "PubkeyAuthentication",
                 "X11Forwarding", "MaxAuthTries", "PermitEmptyPasswords"]:
        val = run_on(node_name, node_info,
                     f"sshd -T 2>/dev/null | grep -i '^{key.lower()}' || grep -i '^{key}' /etc/ssh/sshd_config 2>/dev/null || echo 'NOT_SET'")
        config_items[key] = val
    # Check host key types served
    host_keys = run_on(node_name, node_info,
                       "sshd -T 2>/dev/null | grep -i hostkeyalgorithms || echo 'DEFAULT'")
    config_items["HostKeyAlgorithms"] = host_keys
    # Check KEX algorithms
    kex = run_on(node_name, node_info, "ssh -Q kex 2>/dev/null | grep sntrup || echo 'NO_SNTRUP'")
    config_items["sntrup761_available"] = "YES" if "sntrup" in kex else "NO"
    return config_items


def check_pg_tls():
    """Check PostgreSQL TLS enforcement."""
    try:
        r = subprocess.run(
            "PGPASSWORD='${CHEROKEE_DB_PASS}' psql -h 192.168.132.222 -U claude -d zammad_production -t -c \"SHOW ssl;\"",
            shell=True, capture_output=True, text=True, timeout=15
        )
        ssl_status = r.stdout.strip()
        # Check if our connection is using SSL
        r2 = subprocess.run(
            "PGPASSWORD='${CHEROKEE_DB_PASS}' psql -h 192.168.132.222 -U claude -d zammad_production -t -c \"SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid();\"",
            shell=True, capture_output=True, text=True, timeout=15
        )
        conn_ssl = r2.stdout.strip()
        return {"server_ssl": ssl_status, "connection_ssl": conn_ssl}
    except Exception as e:
        return {"error": str(e)}


def scan_credentials():
    """Scan for plaintext credentials in code directories."""
    findings = []
    for scan_dir in SCAN_DIRS:
        if not os.path.isdir(scan_dir):
            continue
        for root, dirs, files in os.walk(scan_dir):
            # Skip allowlisted directories
            dirs[:] = [d for d in dirs if d not in CREDENTIAL_ALLOWLIST]
            for fname in files:
                # Skip binary and allowlisted files
                if any(skip in fname for skip in CREDENTIAL_ALLOWLIST):
                    continue
                if fname.endswith(('.pyc', '.so', '.o', '.png', '.jpg', '.gif', '.pdf')):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, 'r', errors='ignore') as f:
                        for lineno, line in enumerate(f, 1):
                            for pattern in CREDENTIAL_PATTERNS:
                                if re.search(pattern, line):
                                    # Redact the actual value
                                    redacted = re.sub(
                                        r'([=:]\s*["\']?)[A-Za-z0-9!@#$%^&*_-]{8,}',
                                        r'\1[REDACTED]',
                                        line.strip()
                                    )
                                    findings.append({
                                        "file": fpath,
                                        "line": lineno,
                                        "match": redacted[:120],
                                    })
                                    break  # One finding per line
                except (PermissionError, IsADirectoryError):
                    continue
    return findings


def main():
    report = []
    report.append("# Classical Security Audit — Cherokee AI Federation")
    report.append(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"**Auditor**: security_audit_classical.py")
    report.append(f"**Council Mandate**: Quantum/PQC Sprint, Raven P0")
    report.append("")
    report.append("---")
    report.append("")

    # Per-node checks
    for node_name, node_info in NODES.items():
        report.append(f"## {node_name}")
        report.append("")

        # fail2ban
        f2b = check_fail2ban(node_name, node_info)
        report.append(f"### fail2ban")
        report.append(f"- Status: `{f2b['status']}`")
        report.append(f"- Jails: `{f2b['jails'][:200]}`")
        report.append("")

        # nftables
        nft = check_nftables(node_name, node_info)
        report.append(f"### nftables")
        report.append(f"- Input policy: `{nft['input_policy']}`")
        report.append(f"- Rule count: `{nft['rule_count']}` lines")
        report.append("")

        # SSH config
        ssh = check_ssh_config(node_name, node_info)
        report.append(f"### SSH Configuration")
        for k, v in ssh.items():
            report.append(f"- {k}: `{v[:100]}`")
        report.append("")

    # PostgreSQL TLS
    report.append("## PostgreSQL TLS (192.168.132.222)")
    report.append("")
    pg = check_pg_tls()
    for k, v in pg.items():
        report.append(f"- {k}: `{v}`")
    report.append("")

    # Credential scan
    report.append("## Plaintext Credential Scan")
    report.append("")
    creds = scan_credentials()
    if creds:
        report.append(f"**Found {len(creds)} potential credential exposures:**")
        report.append("")
        for c in creds[:50]:  # Cap at 50
            report.append(f"- `{c['file']}:{c['line']}` — `{c['match']}`")
    else:
        report.append("No plaintext credentials found in scanned directories.")
    report.append("")

    report.append("---")
    report.append("")
    report.append("*Generated by security_audit_classical.py — Council mandate Raven P0*")

    # Write report
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, 'w') as f:
        f.write('\n'.join(report))

    print(f"Report written to {REPORT_PATH}")
    print(f"Nodes audited: {len(NODES)}")
    print(f"Credential findings: {len(creds)}")


if __name__ == "__main__":
    main()
>>>>>>> REPLACE
```

## Verification

Run on redfin:

```text
/ganuda/home/dereadi/cherokee_venv/bin/python3 /ganuda/scripts/security_audit_classical.py
cat /ganuda/reports/security_audit_classical_feb2026.md
```

Expected: Report with fail2ban status, nftables policy, SSH config, PostgreSQL TLS status, and credential scan results for all reachable nodes.

## Notes

- Some checks require sudo — the script captures what it can without sudo and notes gaps.
- DMZ nodes (owlfin/eaglefin) are excluded until SSSD/Kerberos auth is restored.
- Credential scan is conservative — false positives expected. Manual review of flagged items required.
- The .service file for systemd is not needed — this is a one-shot audit script.

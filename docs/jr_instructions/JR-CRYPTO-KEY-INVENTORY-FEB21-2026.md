# JR Instruction: Cryptographic Key Inventory

**Task**: PQC-INVENTORY-001
**Priority**: P1
**Kanban**: #1875 (3 SP)
**use_rlm**: false
**assigned_jr**: Software Engineer Jr.
**Council Vote**: PROCEED WITH CAUTION (0.846 confidence, 1.0 agreement)
**Long Man Phase**: BUILD — Quantum/PQC Hardening Sprint

## Context

Council deliberation on quantum error correction identified the need for a complete cryptographic key inventory before PQC migration can proceed. Bear (Security): "Cannot migrate what you have not inventoried." This script inventories all SSH host keys, user keys, TLS certificates, and Kerberos keytabs across all reachable nodes.

The script must run on redfin using `/ganuda/home/dereadi/cherokee_venv/bin/python3`.

## Changes

### Change 1: Create the cryptographic key inventory script

Create `/ganuda/scripts/crypto_key_inventory.py`

```python
<<<<<<< SEARCH
=======
#!/usr/bin/env python3
"""Cryptographic Key Inventory — Federation-Wide.

Inventories all SSH host keys, user keys, TLS certificates,
and KEX algorithm support across all reachable federation nodes.
Produces report at /ganuda/reports/crypto_inventory_feb2026.md

Council mandate: Quantum/PQC Sprint, Bear P1.
"""

import subprocess
import os
from datetime import datetime

NODES = {
    "redfin": {"host": "localhost", "ssh": False},
    "greenfin": {"host": "greenfin", "ssh": True},
    "bluefin": {"host": "bluefin", "ssh": True},
}

REPORT_PATH = "/ganuda/reports/crypto_inventory_feb2026.md"


def run_local(cmd):
    """Run command locally."""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return r.stdout.strip()
    except Exception as e:
        return f"[ERROR: {e}]"


def run_ssh(host, cmd):
    """Run command via SSH."""
    try:
        r = subprocess.run(
            f"ssh -o ConnectTimeout=10 {host} '{cmd}'",
            shell=True, capture_output=True, text=True, timeout=30
        )
        return r.stdout.strip()
    except Exception as e:
        return f"[ERROR: {e}]"


def run_on(node_name, node_info, cmd):
    """Run command on a node."""
    if node_info["ssh"]:
        return run_ssh(node_info["host"], cmd)
    return run_local(cmd)


def inventory_ssh_host_keys(node_name, node_info):
    """List SSH host keys on a node."""
    keys = []
    key_types = ["rsa", "ecdsa", "ed25519"]
    for kt in key_types:
        path = f"/etc/ssh/ssh_host_{kt}_key.pub"
        result = run_on(node_name, node_info,
                        f"test -f {path} && ssh-keygen -lf {path} 2>/dev/null || echo MISSING")
        keys.append({"type": kt, "path": path, "info": result})
    return keys


def inventory_user_keys(node_name, node_info):
    """List user SSH keys."""
    result = run_on(node_name, node_info,
                    "for f in ~/.ssh/id_*.pub; do test -f $f && ssh-keygen -lf $f 2>/dev/null; done || echo NONE")
    return result


def inventory_kex_algorithms(node_name, node_info):
    """List available KEX algorithms."""
    result = run_on(node_name, node_info, "ssh -Q kex 2>/dev/null")
    return result


def inventory_ssh_version(node_name, node_info):
    """Get SSH version."""
    return run_on(node_name, node_info, "ssh -V 2>&1")


def inventory_openssl_version(node_name, node_info):
    """Get OpenSSL version."""
    return run_on(node_name, node_info, "openssl version 2>&1")


def inventory_tls_certs():
    """Check Caddy TLS certificates on redfin."""
    caddy_certs = run_local(
        "find /home/dereadi/.local/share/caddy -name '*.crt' -o -name '*.pem' 2>/dev/null | head -20"
    )
    # Check Let's Encrypt cert details if accessible
    cert_info = run_local(
        "echo | openssl s_client -connect localhost:443 -servername vetassist.ganuda.us 2>/dev/null | "
        "openssl x509 -noout -subject -issuer -dates -fingerprint -text 2>/dev/null | "
        "grep -E '(Subject:|Issuer:|Not Before|Not After|Public Key Algorithm|RSA Public-Key|ASN1 OID)'"
    )
    return {"cert_files": caddy_certs, "cert_info": cert_info}


def inventory_kerberos(node_name, node_info):
    """Check Kerberos keytab info."""
    keytab = run_on(node_name, node_info,
                    "klist -ket /etc/krb5.keytab 2>/dev/null | head -20 || echo 'NO_KEYTAB'")
    tickets = run_on(node_name, node_info, "klist 2>/dev/null | head -10 || echo 'NO_TICKETS'")
    return {"keytab": keytab, "tickets": tickets}


def main():
    report = []
    report.append("# Cryptographic Key Inventory — Cherokee AI Federation")
    report.append(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"**Auditor**: crypto_key_inventory.py")
    report.append(f"**Council Mandate**: Quantum/PQC Sprint, Bear P1")
    report.append("")
    report.append("---")
    report.append("")

    for node_name, node_info in NODES.items():
        report.append(f"## {node_name}")
        report.append("")

        # Versions
        ssh_ver = inventory_ssh_version(node_name, node_info)
        ssl_ver = inventory_openssl_version(node_name, node_info)
        report.append(f"- SSH: `{ssh_ver}`")
        report.append(f"- OpenSSL: `{ssl_ver}`")
        report.append("")

        # Host keys
        report.append("### SSH Host Keys")
        report.append("")
        host_keys = inventory_ssh_host_keys(node_name, node_info)
        for k in host_keys:
            status = "MISSING" if "MISSING" in k["info"] else k["info"]
            report.append(f"- **{k['type']}**: `{status}`")
        report.append("")

        # User keys
        report.append("### User SSH Keys")
        report.append("")
        user_keys = inventory_user_keys(node_name, node_info)
        report.append(f"```\n{user_keys}\n```")
        report.append("")

        # PQC KEX support
        report.append("### PQC KEX Support")
        report.append("")
        kex = inventory_kex_algorithms(node_name, node_info)
        pqc_kex = [line for line in kex.split('\n') if 'sntrup' in line or 'mlkem' in line.lower()]
        if pqc_kex:
            for k in pqc_kex:
                report.append(f"- `{k}` (POST-QUANTUM)")
        else:
            report.append("- NO PQC KEX algorithms available")
        report.append("")

        # Kerberos
        report.append("### Kerberos")
        report.append("")
        krb = inventory_kerberos(node_name, node_info)
        report.append(f"Keytab:\n```\n{krb['keytab'][:500]}\n```")
        report.append(f"Tickets:\n```\n{krb['tickets'][:500]}\n```")
        report.append("")

    # TLS Certificates
    report.append("## TLS Certificates (Caddy on redfin)")
    report.append("")
    tls = inventory_tls_certs()
    report.append(f"### Certificate Files")
    report.append(f"```\n{tls['cert_files'] or 'None found'}\n```")
    report.append("")
    report.append(f"### Active Certificate Details")
    report.append(f"```\n{tls['cert_info'] or 'Could not connect'}\n```")
    report.append("")

    # Summary
    report.append("---")
    report.append("")
    report.append("## PQC Migration Readiness Summary")
    report.append("")
    report.append("| Node | SSH Version | sntrup761 | OpenSSL | PQC Ready |")
    report.append("|------|------------|-----------|---------|-----------|")
    for node_name, node_info in NODES.items():
        ssh_ver = inventory_ssh_version(node_name, node_info)
        kex = inventory_kex_algorithms(node_name, node_info)
        has_sntrup = "YES" if "sntrup" in kex else "NO"
        ssl_ver = inventory_openssl_version(node_name, node_info)
        pqc_ready = "YES" if "sntrup" in kex else "NO"
        report.append(f"| {node_name} | {ssh_ver[:30]} | {has_sntrup} | {ssl_ver[:20]} | {pqc_ready} |")
    report.append("")
    report.append("---")
    report.append("")
    report.append("*Generated by crypto_key_inventory.py — Council mandate Bear P1*")

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, 'w') as f:
        f.write('\n'.join(report))

    print(f"Report written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
>>>>>>> REPLACE
```

## Verification

```text
/ganuda/home/dereadi/cherokee_venv/bin/python3 /ganuda/scripts/crypto_key_inventory.py
cat /ganuda/reports/crypto_inventory_feb2026.md
```

Expected: Inventory of all SSH host keys (type, size, fingerprint), user keys, PQC KEX support, Kerberos keytabs, and TLS certificates across all reachable nodes.

## Notes

- DMZ nodes (owlfin/eaglefin) excluded until SSSD auth restored.
- bmasass (macOS) requires separate inventory approach.
- Credential values are NOT logged — only key metadata (type, size, fingerprint).
- Run BEFORE and AFTER SSH PQC hardening playbook (#1874) to verify changes took effect.

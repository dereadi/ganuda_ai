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
        report.append(f"
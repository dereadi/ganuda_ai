#!/usr/bin/env python3
"""Config Checker — audits SSH, firewall, sudo, encryption, and system security settings."""

import subprocess
import os
from pathlib import Path
from typing import List, Dict


def check_ssh_config() -> List[Dict]:
    """Check SSH server configuration for security issues."""
    findings = []
    sshd_config = Path("/etc/ssh/sshd_config")

    if not sshd_config.exists():
        findings.append({"check": "ssh_config", "severity": "info", "description": "No SSH server config found (sshd not installed or not standard path)"})
        return findings

    try:
        content = sshd_config.read_text(errors='ignore')
        lines = {l.strip().split()[0].lower(): l.strip() for l in content.split('\n')
                 if l.strip() and not l.strip().startswith('#') and ' ' in l.strip()}

        # PermitRootLogin
        if 'permitrootlogin' in lines:
            val = lines['permitrootlogin'].split()[-1].lower()
            if val in ('yes', 'without-password'):
                findings.append({"check": "ssh_root_login", "severity": "critical",
                    "description": f"SSH root login is {val}",
                    "fix": "Set PermitRootLogin no in /etc/ssh/sshd_config"})
            else:
                findings.append({"check": "ssh_root_login", "severity": "info", "description": "SSH root login disabled"})

        # PasswordAuthentication
        if 'passwordauthentication' in lines:
            val = lines['passwordauthentication'].split()[-1].lower()
            if val == 'yes':
                findings.append({"check": "ssh_password_auth", "severity": "warning",
                    "description": "SSH password authentication enabled (prefer key-only)",
                    "fix": "Set PasswordAuthentication no in /etc/ssh/sshd_config"})
        else:
            findings.append({"check": "ssh_password_auth", "severity": "warning",
                "description": "SSH PasswordAuthentication not explicitly set (defaults may vary)"})

    except PermissionError:
        findings.append({"check": "ssh_config", "severity": "warning", "description": "Cannot read sshd_config (need sudo)"})

    return findings


def check_firewall() -> List[Dict]:
    """Check firewall status."""
    findings = []

    # Try ufw first (Ubuntu/Debian)
    try:
        result = subprocess.run(["ufw", "status"], capture_output=True, text=True, timeout=5)
        if "inactive" in result.stdout.lower():
            findings.append({"check": "firewall", "severity": "critical",
                "description": "UFW firewall is INACTIVE",
                "fix": "sudo ufw enable"})
        elif "active" in result.stdout.lower():
            rule_count = result.stdout.count('\n') - 4  # rough count
            findings.append({"check": "firewall", "severity": "info",
                "description": f"UFW firewall active (~{max(0,rule_count)} rules)"})
        return findings
    except FileNotFoundError:
        pass

    # Try iptables
    try:
        result = subprocess.run(["iptables", "-L", "-n", "--line-numbers"],
                              capture_output=True, text=True, timeout=5)
        rule_count = len([l for l in result.stdout.split('\n') if l.strip() and not l.startswith('Chain') and not l.startswith('num')])
        if rule_count == 0:
            findings.append({"check": "firewall", "severity": "warning",
                "description": "iptables has no rules (no firewall filtering)"})
        else:
            findings.append({"check": "firewall", "severity": "info",
                "description": f"iptables has {rule_count} rules"})
    except (FileNotFoundError, PermissionError):
        findings.append({"check": "firewall", "severity": "warning",
            "description": "Cannot check firewall status (try with sudo)"})

    return findings


def check_sudo_config() -> List[Dict]:
    """Check for NOPASSWD sudo entries."""
    findings = []
    try:
        result = subprocess.run(["sudo", "-l"], capture_output=True, text=True, timeout=5)
        nopasswd_count = result.stdout.lower().count('nopasswd')
        if nopasswd_count > 0:
            findings.append({"check": "sudo_nopasswd", "severity": "warning",
                "description": f"{nopasswd_count} NOPASSWD sudo rules found",
                "fix": "Review: sudo -l — ensure only necessary commands have NOPASSWD"})
        else:
            findings.append({"check": "sudo_nopasswd", "severity": "info",
                "description": "No NOPASSWD sudo rules detected"})
    except Exception:
        findings.append({"check": "sudo", "severity": "info",
            "description": "Cannot enumerate sudo rules without password"})

    return findings


def check_disk_encryption() -> List[Dict]:
    """Check if disk encryption is enabled."""
    findings = []

    # Linux LUKS
    try:
        result = subprocess.run(["lsblk", "-o", "NAME,TYPE,FSTYPE,MOUNTPOINT"],
                              capture_output=True, text=True, timeout=5)
        if 'crypt' in result.stdout.lower() or 'luks' in result.stdout.lower():
            findings.append({"check": "disk_encryption", "severity": "info",
                "description": "Disk encryption (LUKS) detected"})
        else:
            findings.append({"check": "disk_encryption", "severity": "warning",
                "description": "No disk encryption detected",
                "fix": "Consider enabling LUKS full-disk encryption"})
    except FileNotFoundError:
        # macOS
        try:
            result = subprocess.run(["fdesetup", "status"],
                                  capture_output=True, text=True, timeout=5)
            if "On" in result.stdout:
                findings.append({"check": "disk_encryption", "severity": "info",
                    "description": "FileVault encryption enabled"})
            else:
                findings.append({"check": "disk_encryption", "severity": "warning",
                    "description": "FileVault encryption not enabled",
                    "fix": "Enable FileVault in System Preferences > Security & Privacy"})
        except FileNotFoundError:
            findings.append({"check": "disk_encryption", "severity": "info",
                "description": "Cannot determine encryption status"})

    return findings


def check_auto_updates() -> List[Dict]:
    """Check if automatic security updates are enabled."""
    findings = []

    # Ubuntu/Debian
    apt_conf = Path("/etc/apt/apt.conf.d/20auto-upgrades")
    if apt_conf.exists():
        try:
            content = apt_conf.read_text()
            if 'Unattended-Upgrade "1"' in content:
                findings.append({"check": "auto_updates", "severity": "info",
                    "description": "Unattended security upgrades enabled"})
            else:
                findings.append({"check": "auto_updates", "severity": "warning",
                    "description": "Unattended upgrades not enabled",
                    "fix": "sudo apt install unattended-upgrades && sudo dpkg-reconfigure -plow unattended-upgrades"})
        except Exception:
            pass
    else:
        findings.append({"check": "auto_updates", "severity": "warning",
            "description": "Auto-updates config not found — may not be configured"})

    return findings


def run_config_check() -> List[Dict]:
    """Run all config security checks."""
    all_findings = []
    all_findings.extend(check_ssh_config())
    all_findings.extend(check_firewall())
    all_findings.extend(check_sudo_config())
    all_findings.extend(check_disk_encryption())
    all_findings.extend(check_auto_updates())

    return sorted(all_findings, key=lambda x: (
        {"critical": 0, "warning": 1, "info": 2}.get(x.get("severity", "info"), 3)
    ))


if __name__ == '__main__':
    results = run_config_check()
    print(f"Config check: {len(results)} findings\n")
    for r in results:
        icon = {"critical": "🔴", "warning": "🟡", "info": "🟢"}.get(r.get("severity"), "⚪")
        print(f"  {icon} {r['severity']:8} | {r['check']:20} | {r['description']}")
        if r.get('fix'):
            print(f"    Fix: {r['fix']}")

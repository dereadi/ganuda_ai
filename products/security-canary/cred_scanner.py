#!/usr/bin/env python3
"""Credential Scanner — finds exposed secrets in common locations. NEVER logs actual credentials."""

import os
import re
from pathlib import Path
from typing import List, Dict

# Patterns that indicate exposed credentials
CREDENTIAL_PATTERNS = {
    'aws_access_key': (r'AKIA[0-9A-Z]{16}', "critical", "AWS Access Key ID"),
    'aws_secret_key': (r'(?i)(aws_secret|secret_access_key)\s*[=:]\s*\S{20,}', "critical", "AWS Secret Key"),
    'generic_password': (r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']?\S{4,}', "warning", "Hardcoded password"),
    'generic_token': (r'(?i)(token|api_key|apikey|secret)\s*[=:]\s*["\']?\S{8,}', "warning", "API token or key"),
    'bearer_token': (r'Bearer\s+[A-Za-z0-9\-_.~+/]+=*', "warning", "Bearer token"),
    'private_key_header': (r'-----BEGIN\s+(RSA|OPENSSH|EC|DSA)\s+PRIVATE\s+KEY-----', "critical", "Private key in file"),
    'github_token': (r'gh[ps]_[A-Za-z0-9_]{36,}', "critical", "GitHub personal access token"),
    'slack_token': (r'xox[baprs]-[A-Za-z0-9-]+', "critical", "Slack token"),
    'jwt_token': (r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}', "warning", "JWT token"),
    'connection_string': (r'(?i)(postgres|mysql|mongodb|redis)://\S+:\S+@', "critical", "Database connection string with credentials"),
}

# Locations to scan
SCAN_LOCATIONS = [
    ("~/.env", "Environment file"),
    ("~/.bashrc", "Bash config"),
    ("~/.bash_history", "Bash history"),
    ("~/.zshrc", "Zsh config"),
    ("~/.zsh_history", "Zsh history"),
    ("~/.gitconfig", "Git config"),
    ("~/.netrc", "Netrc credentials"),
    ("~/.pgpass", "PostgreSQL passwords"),
    ("~/.my.cnf", "MySQL config"),
    ("~/.aws/credentials", "AWS credentials"),
    ("~/.aws/config", "AWS config"),
    ("~/.ssh/config", "SSH config"),
    ("~/.docker/config.json", "Docker config"),
    ("~/.kube/config", "Kubernetes config"),
    ("~/.npmrc", "NPM config"),
]


def check_ssh_keys() -> List[Dict]:
    """Check for SSH private keys without passphrases."""
    findings = []
    ssh_dir = Path.home() / ".ssh"
    if not ssh_dir.exists():
        return findings

    for key_file in ssh_dir.glob("*"):
        if key_file.suffix == '.pub' or key_file.name in ('known_hosts', 'authorized_keys', 'config'):
            continue
        if key_file.is_file():
            try:
                content = key_file.read_text(errors='ignore')[:500]
                if 'PRIVATE KEY' in content:
                    if 'ENCRYPTED' not in content:
                        findings.append({
                            "type": "ssh_key_no_passphrase",
                            "location": str(key_file),
                            "severity": "critical",
                            "description": "SSH private key WITHOUT passphrase encryption",
                            "fix": f"ssh-keygen -p -f {key_file}  # Add a passphrase",
                        })
                    else:
                        findings.append({
                            "type": "ssh_key_encrypted",
                            "location": str(key_file),
                            "severity": "info",
                            "description": "SSH private key (passphrase protected)",
                        })
            except PermissionError:
                pass
    return findings


def scan_file_for_credentials(filepath: str, description: str) -> List[Dict]:
    """Scan a single file for credential patterns. NEVER includes the actual credential."""
    findings = []
    path = Path(filepath).expanduser()
    if not path.exists() or not path.is_file():
        return findings

    try:
        content = path.read_text(errors='ignore')
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            for pattern_name, (regex, severity, desc) in CREDENTIAL_PATTERNS.items():
                if re.search(regex, line):
                    findings.append({
                        "type": pattern_name,
                        "location": f"{filepath}:{line_num}",
                        "severity": severity,
                        "description": desc,
                        "fix": f"Remove or rotate the credential at {filepath} line {line_num}",
                        # NEVER include the actual credential value
                    })
                    break  # one finding per line is enough

    except PermissionError:
        pass
    except Exception:
        pass

    return findings


def scan_git_repos() -> List[Dict]:
    """Scan for .git/config files with hardcoded credentials in home directory."""
    findings = []
    home = Path.home()

    # Check up to 2 levels deep for git repos
    for git_config in home.glob("*/.git/config"):
        try:
            content = git_config.read_text(errors='ignore')
            if re.search(r'https?://[^:]+:[^@]+@', content):
                findings.append({
                    "type": "git_hardcoded_creds",
                    "location": str(git_config),
                    "severity": "critical",
                    "description": "Git remote URL contains hardcoded credentials",
                    "fix": "Use SSH keys or credential helpers instead of URL-embedded passwords",
                })
        except (PermissionError, Exception):
            pass

    return findings


def scan_env_files() -> List[Dict]:
    """Scan for .env files in common project directories."""
    findings = []
    home = Path.home()

    for env_file in home.glob("*/.env"):
        findings.extend(scan_file_for_credentials(str(env_file), f"Project .env file"))

    for env_file in home.glob("*/*/.env"):
        findings.extend(scan_file_for_credentials(str(env_file), f"Project .env file"))

    return findings


def run_credential_scan() -> List[Dict]:
    """Run all credential scans. Returns findings sorted by severity."""
    all_findings = []

    # Scan known locations
    for filepath, description in SCAN_LOCATIONS:
        all_findings.extend(scan_file_for_credentials(filepath, description))

    # SSH keys
    all_findings.extend(check_ssh_keys())

    # Git repos
    all_findings.extend(scan_git_repos())

    # .env files
    all_findings.extend(scan_env_files())

    return sorted(all_findings, key=lambda x: (
        {"critical": 0, "warning": 1, "info": 2}.get(x.get("severity", "info"), 3)
    ))


if __name__ == '__main__':
    results = run_credential_scan()
    print(f"Found {len(results)} credential findings\n")
    for r in results:
        icon = {"critical": "🔴", "warning": "🟡", "info": "🟢"}.get(r.get("severity"), "⚪")
        print(f"  {icon} {r['severity']:8} | {r['type']:25} | {r['location']}")
        if r.get('fix'):
            print(f"    Fix: {r['fix']}")

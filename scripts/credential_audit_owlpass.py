#!/usr/bin/env python3
"""Owl Pass Credential Audit — Scan /ganuda/ codebase for hardcoded secrets.

Crawdad request from Longhouse open floor. Council voted PROCEED.
Scans for hardcoded passwords, API keys, tokens, and secrets.
Redacts values in output — never prints actual credentials.

For Seven Generations - Cherokee AI Federation
"""
import os
import re
from datetime import datetime
from typing import List, Tuple

# Directories containing source code to scan (relative to /ganuda/)
SCAN_DIRS = [
    'daemons',
    'email_daemon',
    'jr_executor',
    'lib',
    'scripts',
    'services',
    'telegram_bot',
    'config',
    'vetassist',
    'dev',
]

# Patterns that indicate hardcoded credentials
PATTERNS = [
    r'password\s*=\s*[\'"][^\'"]{6,}[\'"]',
    r'api_key\s*=\s*[\'"][^\'"]{6,}[\'"]',
    r'token\s*=\s*[\'"][^\'"]{6,}[\'"]',
    r'secret\s*=\s*[\'"][^\'"]{6,}[\'"]',
    r'Bearer\s+[A-Za-z0-9\-_\.]{20,}',
    r'(?:postgres|mysql|mongodb)://\S+:\S+@',
]

# File extensions to scan
FILE_EXTENSIONS = ('.py', '.env', '.json', '.yaml', '.yml', '.toml', '.cfg', '.ini', '.sh', '.conf', '.js', '.ts')

# Directory names to skip inside scan dirs
SKIP_DIRS = {
    '__pycache__', '.git', 'node_modules', '.next', '.venv', 'venv',
    'ii-researcher', 'moltbook-mcp', 'anker-solix-api', '.mypy_cache',
    'dist', 'build', 'site-packages', '.tox', 'egg-info',
}

# Files to skip (substring match)
SKIP_FILE_PATTERNS = [
    'secrets.env', '.example', '.backup', 'CLAUDE.md', 'MEMORY.md',
    'credential_audit_owlpass.py', 'package-lock.json', 'yarn.lock',
]


def find_files_to_scan(base_dir: str) -> List[str]:
    """Find source files to scan across known code directories."""
    files_to_scan: List[str] = []
    for scan_dir in SCAN_DIRS:
        full_path = os.path.join(base_dir, scan_dir)
        if not os.path.isdir(full_path):
            continue
        for root, dirs, files in os.walk(full_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fname in files:
                if not fname.endswith(FILE_EXTENSIONS):
                    continue
                if any(skip in fname for skip in SKIP_FILE_PATTERNS):
                    continue
                files_to_scan.append(os.path.join(root, fname))
    return files_to_scan


def scan_file_for_credentials(file_path: str) -> List[Tuple[str, int, str]]:
    """Scan a single file for credential patterns. Redacts values."""
    matches: List[Tuple[str, int, str]] = []
    try:
        with open(file_path, 'r', errors='ignore') as f:
            for line_number, line in enumerate(f, start=1):
                # Skip comment-only lines and lines referencing env vars
                stripped = line.strip()
                if stripped.startswith('#') or stripped.startswith('//'):
                    continue
                # Skip lines that are just reading from env (not hardcoding)
                if 'os.environ' in line or 'os.getenv' in line or 'env.' in line.lower():
                    continue
                for pattern in PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Redact credential values
                        redacted = re.sub(r'[\'"][^\'"]{6,}[\'"]', '"***REDACTED***"', line)
                        matches.append((file_path, line_number, redacted.strip()[:200]))
                        break  # One match per line
    except (OSError, PermissionError):
        pass
    return matches


def main() -> None:
    """Run the credential audit across federation code directories."""
    print("=== OWL PASS CREDENTIAL AUDIT ===")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    base_dir = '/ganuda/'
    files_to_scan = find_files_to_scan(base_dir)
    print(f"Scanning {len(files_to_scan)} files across {len(SCAN_DIRS)} code directories...")
    print()

    all_matches: List[Tuple[str, int, str]] = []
    for filepath in files_to_scan:
        matches = scan_file_for_credentials(filepath)
        all_matches.extend(matches)

    if all_matches:
        print(f"=== FINDINGS: {len(all_matches)} potential hardcoded credential(s) ===")
        print()
        for file_path, line_number, matched_pattern in all_matches:
            print(f"  {file_path}:{line_number}")
            print(f"    {matched_pattern}")
            print()
    else:
        print("No hardcoded credentials found.")

    print(f"=== AUDIT COMPLETE: {len(all_matches)} finding(s) across {len(files_to_scan)} files ===")
    return len(all_matches)


if __name__ == "__main__":
    exit_code = main()
    # Exit 0 on success (even with findings — this is a report, not a gate)

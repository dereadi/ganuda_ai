# Jr Instruction: Backup Encryption Audit

**Kanban**: #1877
**Priority**: 4
**Story Points**: 2
**use_rlm**: false
**assigned_jr**: Software Engineer Jr.

---

## Overview

Create a script that scans backup directories for files and checks whether they are encrypted (GPG, age, or openssl enc markers). Reports any unencrypted backups to stdout and saves a JSON report. Uses only standard library (pathlib, struct). Runs on redfin.

---

## Steps

### Step 1: Create the backup encryption audit script

Create `/ganuda/scripts/backup_encryption_audit.py`

```python
#!/usr/bin/env python3
"""
Backup Encryption Audit
Kanban #1877 - Cherokee AI Federation

Scans backup directories for files and checks if they are encrypted
by inspecting file headers for GPG, age, and openssl enc markers.
Reports unencrypted backups.

Usage:
    python3 /ganuda/scripts/backup_encryption_audit.py

Output:
    /ganuda/reports/backup_encryption_audit.json

For Seven Generations
"""

import json
import os
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKUP_DIRS = [
    Path("/ganuda/backups"),
    Path.home() / "backups",
]

REPORT_PATH = Path("/ganuda/reports/backup_encryption_audit.json")

# Magic bytes and markers for encrypted file formats
# GPG binary: starts with 0x84, 0x85, 0x8C, 0x8D, or 0xC0-0xCF (old/new packet tags)
# GPG ASCII armor: starts with "-----BEGIN PGP"
# age: starts with "age-encryption.org"
# openssl enc: starts with "Salted__" (8 bytes)
GPG_ASCII_PREFIX = b"-----BEGIN PGP"
AGE_PREFIX = b"age-encryption.org"
OPENSSL_SALT_PREFIX = b"Salted__"


def is_gpg_binary(header):
    """Check if the header bytes look like a GPG binary packet."""
    if len(header) < 2:
        return False
    first_byte = header[0]
    # Old-format packet tag: bit 7 set, bit 6 clear
    if first_byte & 0x80:
        return True
    return False


def detect_encryption(file_path):
    """Detect if a file is encrypted by reading its header bytes.

    Returns a tuple of (is_encrypted: bool, encryption_type: str or None).
    """
    try:
        with open(file_path, "rb") as f:
            header = f.read(64)
    except (PermissionError, OSError) as e:
        return None, f"unreadable: {e}"

    if len(header) == 0:
        return False, "empty_file"

    # Check GPG ASCII armor
    if header.startswith(GPG_ASCII_PREFIX):
        return True, "gpg_ascii"

    # Check age encryption
    if header.startswith(AGE_PREFIX):
        return True, "age"

    # Check openssl enc (Salted__ prefix)
    if header.startswith(OPENSSL_SALT_PREFIX):
        return True, "openssl_enc"

    # Check GPG binary format
    if is_gpg_binary(header):
        # Additional heuristic: check the packet tag is a valid type
        first_byte = header[0]
        if first_byte & 0x80:
            # Could be GPG — check file extension as secondary signal
            suffix = file_path.suffix.lower()
            if suffix in (".gpg", ".pgp", ".asc", ".sig"):
                return True, "gpg_binary"

    # Check file extension as fallback
    suffix = file_path.suffix.lower()
    if suffix in (".gpg", ".pgp", ".asc", ".age", ".enc"):
        return True, f"extension_{suffix}"

    return False, None


def scan_directory(dir_path):
    """Scan a directory recursively for backup files and check encryption."""
    results = []

    if not dir_path.exists():
        print(f"  Directory does not exist: {dir_path}")
        return results

    if not dir_path.is_dir():
        print(f"  Not a directory: {dir_path}")
        return results

    for file_path in sorted(dir_path.rglob("*")):
        if not file_path.is_file():
            continue

        # Skip very small files (< 16 bytes) and hidden dotfiles
        try:
            size = file_path.stat().st_size
        except OSError:
            continue

        if size < 16:
            continue

        is_encrypted, enc_type = detect_encryption(file_path)

        results.append({
            "path": str(file_path),
            "size_bytes": size,
            "is_encrypted": is_encrypted,
            "encryption_type": enc_type,
            "modified": datetime.fromtimestamp(
                file_path.stat().st_mtime, tz=timezone.utc
            ).isoformat(),
        })

    return results


def main():
    print("Backup Encryption Audit")
    print("=" * 40)
    print()

    all_results = []
    unencrypted = []
    encrypted = []
    errors = []

    for backup_dir in BACKUP_DIRS:
        print(f"Scanning: {backup_dir}")
        results = scan_directory(backup_dir)
        all_results.extend(results)

        for r in results:
            if r["is_encrypted"] is None:
                errors.append(r)
            elif r["is_encrypted"]:
                encrypted.append(r)
            else:
                unencrypted.append(r)

    # Build report
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "directories_scanned": [str(d) for d in BACKUP_DIRS],
        "summary": {
            "total_files": len(all_results),
            "encrypted": len(encrypted),
            "unencrypted": len(unencrypted),
            "unreadable": len(errors),
        },
        "unencrypted_files": unencrypted,
        "encrypted_files": encrypted,
        "errors": errors,
    }

    # Ensure output directory exists
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2, default=str)

    # Print summary
    print()
    print("--- Summary ---")
    print(f"Total files scanned: {len(all_results)}")
    print(f"Encrypted: {len(encrypted)}")
    print(f"Unencrypted: {len(unencrypted)}")
    print(f"Unreadable: {len(errors)}")
    print()

    if unencrypted:
        print("WARNING: Unencrypted backup files found:")
        for uf in unencrypted:
            size_mb = uf["size_bytes"] / (1024 * 1024)
            print(f"  {uf['path']} ({size_mb:.1f} MB)")
    else:
        print("All backup files are encrypted or no backups found.")

    print()
    print(f"Report saved to {REPORT_PATH}")

    # Exit with non-zero if unencrypted backups found
    if unencrypted:
        sys.exit(1)


if __name__ == "__main__":
    main()
```

---

## Verification

After execution, confirm:
1. Script runs without errors: `python3 /ganuda/scripts/backup_encryption_audit.py`
2. Report exists: `cat /ganuda/reports/backup_encryption_audit.json | python3 -m json.tool | head -20`
3. Exit code is 0 if all backups encrypted, 1 if any unencrypted found

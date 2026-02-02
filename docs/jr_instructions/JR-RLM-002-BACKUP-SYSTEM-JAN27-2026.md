# JR Instruction: RLM Pre-Execution Backup System

**JR ID:** JR-RLM-002
**Priority:** P0 (CRITICAL)
**Created:** 2026-01-27
**Author:** TPM via Claude Code
**Council Vote:** 31653da1507b46ec
**Assigned To:** Software Engineer Jr.
**Depends On:** JR-RLM-001
**Effort:** Low

## Problem Statement

When RLM executor modifies files, there is no way to recover the original content if the modification is destructive. A backup system is needed before any file write.

## Required Implementation

### 1. Backup Directory Setup

```bash
# Create backup directory with proper permissions
sudo mkdir -p /ganuda/.rlm-backups
sudo chown dereadi:dereadi /ganuda/.rlm-backups
chmod 755 /ganuda/.rlm-backups
```

### 2. Modify RLM Executor

MODIFY: `/ganuda/lib/rlm_executor.py`

Add backup function after the protected paths code:

```python
import shutil
from datetime import datetime

BACKUP_DIR = Path('/ganuda/.rlm-backups')
BACKUP_RETENTION_DAYS = 7

def backup_file_before_write(file_path: str) -> Optional[str]:
    """
    Create timestamped backup of file before modification.

    Returns:
        Path to backup file, or None if file doesn't exist
    """
    if not os.path.exists(file_path):
        return None

    # Ensure backup directory exists
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # Create timestamped backup path
    timestamp = datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
    file_name = Path(file_path).name

    # Preserve directory structure in backup
    rel_path = file_path.replace('/ganuda/', '')
    backup_subdir = BACKUP_DIR / Path(rel_path).parent
    backup_subdir.mkdir(parents=True, exist_ok=True)

    backup_path = backup_subdir / f"{file_name}.{timestamp}.bak"

    try:
        shutil.copy2(file_path, backup_path)
        logger.info(f"[RLM] Backed up {file_path} -> {backup_path}")
        return str(backup_path)
    except Exception as e:
        logger.error(f"[RLM] Backup failed for {file_path}: {e}")
        return None


def cleanup_old_backups():
    """Remove backups older than BACKUP_RETENTION_DAYS."""
    if not BACKUP_DIR.exists():
        return

    cutoff = datetime.now().timestamp() - (BACKUP_RETENTION_DAYS * 86400)
    removed = 0

    for backup_file in BACKUP_DIR.rglob('*.bak'):
        if backup_file.stat().st_mtime < cutoff:
            backup_file.unlink()
            removed += 1

    if removed:
        logger.info(f"[RLM] Cleaned up {removed} old backups")
```

Add in `_write_files_from_response()` method, BEFORE the file write (around line 382):

```python
                # P0 SAFEGUARD: Backup existing file before any modification
                if os.path.exists(file_path):
                    backup_path = backup_file_before_write(file_path)
                    if backup_path:
                        artifacts.append({
                            'type': 'file_backed_up',
                            'original_path': file_path,
                            'backup_path': backup_path
                        })
```

### 3. Backup Cleanup Cron Job

CREATE: Add to crontab on redfin

```bash
# Add to crontab: cleanup RLM backups older than 7 days
0 3 * * * find /ganuda/.rlm-backups -name "*.bak" -mtime +7 -delete
```

## Verification

```bash
# 1. Check backup directory exists
ls -la /ganuda/.rlm-backups/

# 2. Test backup function
python3 << 'EOF'
import sys
sys.path.insert(0, '/ganuda')

# Create a test file
test_file = '/ganuda/.rlm-backups/test_original.txt'
with open(test_file, 'w') as f:
    f.write('Original content for backup test')

from lib.rlm_executor import backup_file_before_write
backup_path = backup_file_before_write(test_file)

if backup_path:
    print(f'✓ Backup created: {backup_path}')
    with open(backup_path) as f:
        content = f.read()
    print(f'✓ Backup content verified: {len(content)} bytes')
else:
    print('✗ Backup failed')

# Cleanup
import os
os.remove(test_file)
if backup_path:
    os.remove(backup_path)
EOF
```

## Recovery Procedure

If RLM damages a file, recover with:

```bash
# List recent backups for a file
ls -la /ganuda/.rlm-backups/vetassist/frontend/app/wizard/*/

# Restore most recent backup
cp /ganuda/.rlm-backups/path/to/file.tsx.2026-01-27T08-30-00.bak /ganuda/vetassist/frontend/app/wizard/[sessionId]/page.tsx
```

---

FOR SEVEN GENERATIONS

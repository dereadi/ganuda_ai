# Jr Instruction: Executor P3 — Saga Compensation/Rollback

**Task ID:** EXECUTOR-P3-SAGA-ROLLBACK-001
**Assigned:** Software Engineer Jr.
**Priority:** P3 (Lower — safety net for partial writes, synergizes with Safe Edit Mode)
**Created:** 2026-02-03
**TPM:** Claude Opus 4.5
**Council Vote:** APPROVED 7/7 (audit hash: 38a517d5c204a4e7)
**Depends on:** EXECUTOR-P2-CHECKPOINT-GUARDRAILS-001

---

## Context

When a Jr task partially completes — say, it creates 2 of 4 files, then crashes — the system is left in an inconsistent state. The existing RLM Safe Edit Mode creates backups before writes, but there's no automatic rollback mechanism. If a task fails after writing files, those partial writes remain.

The Saga pattern (from Temporal.io) tracks all side effects (file writes, database changes) as a transaction log. On failure, the saga automatically compensates by reverting each completed step in reverse order.

### Source Project
- Temporal (Saga compensation pattern for distributed transactions)

### Council Conditions (Incorporated)
- **Spider (Integration):** Synergize with existing RLM backup system — use `.rlm-backups/` for saga snapshots too.
- **Crawdad (Security):** Saga log must not store file contents (only paths). Rollback must respect RLM protected paths.
- **Raven (Strategy):** Saga rollback should be opt-in per task (not forced on all tasks). Controlled via `use_saga` flag.
- **Turtle (7Gen):** Clean up saga logs after successful completion (same as checkpoints).

### Files to Modify
1. New file: `/ganuda/jr_executor/saga_tracker.py` — Saga transaction tracker
2. `/ganuda/jr_executor/task_executor.py` — Integrate saga tracking into file write operations

---

## Step 1: Create Saga Tracker Module

Create: `/ganuda/jr_executor/saga_tracker.py`

```python
"""
Saga Transaction Tracker for Jr Task Execution.

Tracks file operations as a saga (ordered transaction log).
On failure, compensates by reverting changes in reverse order.

Pattern: Temporal Saga Compensation
Synergy: RLM Safe Edit Mode (uses same backup directory)

For Seven Generations - Cherokee AI Federation
"""

import os
import shutil
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Use the same backup directory as RLM Safe Edit Mode
BACKUP_DIR = "/ganuda/.rlm-backups/saga"


class SagaTracker:
    """Track file operations and provide rollback on failure."""

    def __init__(self, task_id: int, task_title: str = ""):
        self.task_id = task_id
        self.task_title = task_title
        self.operations: List[Dict] = []
        self.started_at = datetime.now().isoformat()
        self._ensure_backup_dir()

    def _ensure_backup_dir(self):
        """Create backup directory for this saga."""
        self.saga_dir = os.path.join(BACKUP_DIR, f"task_{self.task_id}")
        os.makedirs(self.saga_dir, exist_ok=True)

    def record_file_write(self, file_path: str, is_new: bool = False) -> bool:
        """
        Record a file write operation. If the file exists, back it up first.

        Args:
            file_path: Absolute path of the file being written
            is_new: True if this is a new file (no backup needed, just delete on rollback)

        Returns:
            True if operation was recorded (and backup created if needed)
        """
        operation = {
            "type": "file_write",
            "path": file_path,
            "is_new": is_new,
            "backup_path": None,
            "timestamp": datetime.now().isoformat(),
            "step_index": len(self.operations)
        }

        if not is_new and os.path.exists(file_path):
            # Back up existing file before overwrite
            backup_name = f"step_{len(self.operations)}_{os.path.basename(file_path)}"
            backup_path = os.path.join(self.saga_dir, backup_name)
            try:
                shutil.copy2(file_path, backup_path)
                operation["backup_path"] = backup_path
                logger.info(f"[Saga] Backed up {file_path} -> {backup_path}")
            except Exception as e:
                logger.warning(f"[Saga] Failed to backup {file_path}: {e}")
                return False

        self.operations.append(operation)
        self._save_log()
        return True

    def record_file_delete(self, file_path: str) -> bool:
        """
        Record a file deletion. Backs up the file so it can be restored.

        Args:
            file_path: Absolute path of the file being deleted

        Returns:
            True if operation was recorded
        """
        if not os.path.exists(file_path):
            return True  # Nothing to back up

        backup_name = f"step_{len(self.operations)}_deleted_{os.path.basename(file_path)}"
        backup_path = os.path.join(self.saga_dir, backup_name)

        operation = {
            "type": "file_delete",
            "path": file_path,
            "backup_path": backup_path,
            "timestamp": datetime.now().isoformat(),
            "step_index": len(self.operations)
        }

        try:
            shutil.copy2(file_path, backup_path)
            self.operations.append(operation)
            self._save_log()
            return True
        except Exception as e:
            logger.warning(f"[Saga] Failed to backup for delete {file_path}: {e}")
            return False

    def record_db_change(self, table: str, operation_type: str, details: str) -> None:
        """
        Record a database change (for logging only — DB rollback is manual).

        Args:
            table: Table name affected
            operation_type: INSERT, UPDATE, DELETE
            details: Human-readable description
        """
        self.operations.append({
            "type": "db_change",
            "table": table,
            "operation": operation_type,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "step_index": len(self.operations),
            "note": "DB rollback is manual — check saga log for details"
        })
        self._save_log()

    def rollback(self) -> Dict:
        """
        Compensate all recorded operations in reverse order.

        Returns:
            Dict with rollback results: {reverted: int, failed: int, details: [...]}
        """
        results = {
            "reverted": 0,
            "failed": 0,
            "skipped": 0,
            "details": []
        }

        logger.info(f"[Saga] Rolling back {len(self.operations)} operations for task {self.task_id}")

        for op in reversed(self.operations):
            try:
                if op["type"] == "file_write":
                    if op["is_new"]:
                        # New file — delete it
                        if os.path.exists(op["path"]):
                            os.remove(op["path"])
                            results["reverted"] += 1
                            results["details"].append(f"Deleted new file: {op['path']}")
                        else:
                            results["skipped"] += 1
                    elif op.get("backup_path") and os.path.exists(op["backup_path"]):
                        # Existing file was overwritten — restore from backup
                        shutil.copy2(op["backup_path"], op["path"])
                        results["reverted"] += 1
                        results["details"].append(f"Restored: {op['path']}")
                    else:
                        results["skipped"] += 1
                        results["details"].append(f"No backup for: {op['path']}")

                elif op["type"] == "file_delete":
                    if op.get("backup_path") and os.path.exists(op["backup_path"]):
                        # File was deleted — restore it
                        shutil.copy2(op["backup_path"], op["path"])
                        results["reverted"] += 1
                        results["details"].append(f"Restored deleted: {op['path']}")
                    else:
                        results["skipped"] += 1

                elif op["type"] == "db_change":
                    results["skipped"] += 1
                    results["details"].append(f"DB change requires manual rollback: {op['details']}")

            except Exception as e:
                results["failed"] += 1
                results["details"].append(f"Rollback failed for {op.get('path', 'unknown')}: {e}")

        logger.info(f"[Saga] Rollback complete: {results['reverted']} reverted, {results['failed']} failed, {results['skipped']} skipped")
        self._save_log(rollback_result=results)
        return results

    def cleanup(self) -> bool:
        """
        Remove saga backups after successful task completion.
        Called by worker on success (Turtle 7Gen: manage storage).

        Returns:
            True if cleanup succeeded
        """
        try:
            if os.path.exists(self.saga_dir):
                shutil.rmtree(self.saga_dir)
                logger.info(f"[Saga] Cleaned up backups for task {self.task_id}")
            return True
        except Exception as e:
            logger.warning(f"[Saga] Cleanup failed for task {self.task_id}: {e}")
            return False

    def _save_log(self, rollback_result: dict = None):
        """Save the saga log to disk for debugging/auditing."""
        log_path = os.path.join(self.saga_dir, "saga_log.json")
        log_data = {
            "task_id": self.task_id,
            "task_title": self.task_title,
            "started_at": self.started_at,
            "operations_count": len(self.operations),
            "operations": [
                {k: v for k, v in op.items() if k != "backup_path"}  # Don't log backup paths (Crawdad)
                for op in self.operations
            ]
        }
        if rollback_result:
            log_data["rollback"] = rollback_result
            log_data["rolled_back_at"] = datetime.now().isoformat()

        try:
            with open(log_path, 'w') as f:
                json.dump(log_data, f, indent=2)
        except Exception as e:
            logger.warning(f"[Saga] Failed to save log: {e}")

    def get_files_written(self) -> List[str]:
        """Get list of all file paths written in this saga."""
        return [
            op["path"] for op in self.operations
            if op["type"] in ("file_write",) and op.get("path")
        ]
```

---

## Step 2: Integrate Saga into Task Executor

Modify: `/ganuda/jr_executor/task_executor.py`

Read the current file first to understand its structure. The key integration points:

### 2A: Import and initialize saga

At the top of the file, add:
```python
from saga_tracker import SagaTracker
```

### 2B: In `process_queue_task()` (or equivalent method)

Before task execution begins:
```python
# Initialize saga tracker if task uses saga mode
saga = None
if task.get('use_rlm') or task.get('parameters', {}).get('use_saga'):
    saga = SagaTracker(task_id=task['id'], task_title=task.get('title', ''))
    print(f"[TaskExecutor] Saga tracking enabled for task {task['id']}")
```

### 2C: Before each file write

Wherever the executor writes a file (look for `open()` calls, `shutil.copy`, or RLM write operations):
```python
if saga:
    is_new = not os.path.exists(target_path)
    saga.record_file_write(target_path, is_new=is_new)
```

### 2D: On task failure (before returning failure result)

```python
if saga and not result.get('success'):
    print(f"[TaskExecutor] Task failed. Initiating saga rollback...")
    rollback_result = saga.rollback()
    result['saga_rollback'] = rollback_result
    print(f"[TaskExecutor] Saga rollback: {rollback_result['reverted']} reverted, {rollback_result['failed']} failed")
```

### 2E: On task success

```python
if saga and result.get('success'):
    saga.cleanup()  # Remove backups (Turtle 7Gen)
```

---

## Step 3: Verify

```bash
# 1. Verify saga_tracker.py exists
ls -la /ganuda/jr_executor/saga_tracker.py

# 2. Verify backup directory is writable
mkdir -p /ganuda/.rlm-backups/saga/test_verify && rmdir /ganuda/.rlm-backups/saga/test_verify
echo "Backup dir OK"

# 3. Test saga tracker manually
python3 -c "
import sys
sys.path.insert(0, '/ganuda/jr_executor')
from saga_tracker import SagaTracker

# Create a test saga
saga = SagaTracker(task_id=9999, task_title='Test Saga')

# Record a file write to a temp file
import tempfile, os
test_file = tempfile.mktemp(suffix='.txt')
with open(test_file, 'w') as f:
    f.write('original content')

saga.record_file_write(test_file, is_new=False)

# Overwrite the file
with open(test_file, 'w') as f:
    f.write('modified content')

# Verify rollback restores original
result = saga.rollback()
with open(test_file) as f:
    content = f.read()
assert content == 'original content', f'Expected original, got: {content}'
print(f'Rollback test PASSED: {result}')

# Clean up
saga.cleanup()
os.remove(test_file)
print('Cleanup test PASSED')
"

# 4. Verify saga log format
python3 -c "
import sys, json
sys.path.insert(0, '/ganuda/jr_executor')
from saga_tracker import SagaTracker
saga = SagaTracker(task_id=8888, task_title='Log Format Test')
saga.record_db_change('users', 'UPDATE', 'Set va_icn for user 123')
import os
log_path = os.path.join(saga.saga_dir, 'saga_log.json')
with open(log_path) as f:
    log = json.load(f)
print(json.dumps(log, indent=2))
saga.cleanup()
print('Log format test PASSED')
"
```

---

## Acceptance Criteria

1. `saga_tracker.py` created at `/ganuda/jr_executor/saga_tracker.py`
2. `record_file_write()` backs up existing files before overwrite
3. `record_file_delete()` backs up files before deletion
4. `rollback()` reverts operations in reverse order
5. `cleanup()` removes saga backups after success (Turtle 7Gen condition)
6. Saga log saved as JSON (does not contain file contents — Crawdad condition)
7. Saga uses `.rlm-backups/saga/` directory (Spider integration with RLM)
8. Saga is opt-in via `use_rlm` or `use_saga` parameter (Raven strategy condition)
9. DB changes recorded for logging only (manual rollback noted)
10. Self-test passes: write → overwrite → rollback restores original

---

## Rollback

Delete `/ganuda/jr_executor/saga_tracker.py` and remove the import/integration from `task_executor.py`. Remove `/ganuda/.rlm-backups/saga/` directory. No database tables affected.

---

## Architecture Note

```
Task Execution Flow with Saga:

1. Worker claims task (P0 atomic locking)
2. Pre-execution guardrails validate instruction (P2)
3. Saga tracker initialized (P3)
4. For each step:
   a. Save checkpoint (P2)
   b. Record file write in saga (P3)
   c. Execute step
   d. If step fails → check retry count (P1)
5. On success: cleanup saga + checkpoints
6. On failure: saga.rollback() → escalate or DLQ (P1)
```

---

*For Seven Generations*
*Cherokee AI Federation — Jr Executor Architecture Team*

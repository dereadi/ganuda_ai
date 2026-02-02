# JR Instruction: Staging Directory Manager for Jr Execution

**JR ID:** JR-STAGING-MANAGER-JAN29-2026
**Priority:** P0 - CRITICAL
**Assigned To:** Software Engineer Jr.
**Related:** ULTRATHINK-CLUSTER-INFRA-ENHANCEMENT-JAN29-2026
**Council Vote:** 7-0 APPROVE

---

## Objective

Create a staging directory system that allows Jrs to write code safely, with TPM review before merging to production paths.

---

## Problem

15 Jr tasks failed with "Protected path - modification not allowed" because Jrs cannot write to:
- `/ganuda/telegram_bot/`
- `/ganuda/services/`
- `/ganuda/lib/`

The code generated was correct, but security restrictions blocked writes.

---

## Solution

Jrs write to `/ganuda/staging/{task_id}/` instead. Files mirror the production structure:
- `/ganuda/staging/abc123/telegram_bot/chunker.py`
- `/ganuda/staging/abc123/services/worker.py`

TPM reviews and merges approved changes.

---

## Implementation

### Step 1: Create Staging Manager Module

Create `/ganuda/lib/staging_manager.py`:

```python
#!/usr/bin/env python3
"""
Staging Manager - Manage Jr code staging for safe execution.
Cherokee AI Federation - For Seven Generations
"""

import os
import shutil
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

STAGING_ROOT = Path("/ganuda/staging")
PRODUCTION_ROOT = Path("/ganuda")
STAGING_INDEX = STAGING_ROOT / "index.json"


def init_staging():
    """Initialize staging directory structure."""
    STAGING_ROOT.mkdir(exist_ok=True)
    if not STAGING_INDEX.exists():
        with open(STAGING_INDEX, 'w') as f:
            json.dump({"tasks": {}}, f)


def create_task_staging(task_id: str) -> Path:
    """Create staging directory for a task."""
    init_staging()
    task_dir = STAGING_ROOT / task_id
    task_dir.mkdir(exist_ok=True)

    # Update index
    index = load_index()
    index["tasks"][task_id] = {
        "created_at": datetime.now().isoformat(),
        "status": "pending",
        "files": []
    }
    save_index(index)

    return task_dir


def stage_file(task_id: str, relative_path: str, content: str) -> Path:
    """
    Stage a file for a task.

    Args:
        task_id: The task ID
        relative_path: Path relative to /ganuda/ (e.g., "telegram_bot/chunker.py")
        content: File content

    Returns:
        Path to staged file
    """
    task_dir = STAGING_ROOT / task_id
    if not task_dir.exists():
        create_task_staging(task_id)

    staged_path = task_dir / relative_path
    staged_path.parent.mkdir(parents=True, exist_ok=True)

    with open(staged_path, 'w') as f:
        f.write(content)

    # Update index
    index = load_index()
    if task_id in index["tasks"]:
        if relative_path not in index["tasks"][task_id]["files"]:
            index["tasks"][task_id]["files"].append(relative_path)
        save_index(index)

    return staged_path


def get_pending_tasks() -> List[Dict]:
    """Get all pending staging tasks."""
    index = load_index()
    pending = []
    for task_id, info in index["tasks"].items():
        if info.get("status") == "pending":
            pending.append({
                "task_id": task_id,
                "created_at": info.get("created_at"),
                "files": info.get("files", [])
            })
    return pending


def get_task_diff(task_id: str, relative_path: str) -> Dict:
    """Get diff between staged and production file."""
    staged_path = STAGING_ROOT / task_id / relative_path
    prod_path = PRODUCTION_ROOT / relative_path

    result = {
        "relative_path": relative_path,
        "staged_path": str(staged_path),
        "production_path": str(prod_path),
        "staged_exists": staged_path.exists(),
        "production_exists": prod_path.exists(),
    }

    if staged_path.exists():
        with open(staged_path) as f:
            result["staged_content"] = f.read()
            result["staged_lines"] = len(result["staged_content"].splitlines())

    if prod_path.exists():
        with open(prod_path) as f:
            result["production_content"] = f.read()
            result["production_lines"] = len(result["production_content"].splitlines())
        result["is_new"] = False
    else:
        result["is_new"] = True

    return result


def merge_task(task_id: str) -> Dict:
    """
    Merge all staged files for a task to production.

    Returns:
        Dict with merge results
    """
    index = load_index()
    if task_id not in index["tasks"]:
        return {"success": False, "error": "Task not found"}

    task_info = index["tasks"][task_id]
    merged = []
    errors = []

    for relative_path in task_info.get("files", []):
        staged_path = STAGING_ROOT / task_id / relative_path
        prod_path = PRODUCTION_ROOT / relative_path

        try:
            # Ensure parent exists
            prod_path.parent.mkdir(parents=True, exist_ok=True)

            # Backup existing file
            if prod_path.exists():
                backup_path = prod_path.with_suffix(prod_path.suffix + ".backup")
                shutil.copy2(prod_path, backup_path)

            # Copy staged to production
            shutil.copy2(staged_path, prod_path)
            merged.append(relative_path)

        except Exception as e:
            errors.append({"file": relative_path, "error": str(e)})

    # Update status
    index["tasks"][task_id]["status"] = "merged"
    index["tasks"][task_id]["merged_at"] = datetime.now().isoformat()
    index["tasks"][task_id]["merged_files"] = merged
    save_index(index)

    return {
        "success": len(errors) == 0,
        "task_id": task_id,
        "merged": merged,
        "errors": errors
    }


def reject_task(task_id: str, reason: str = None) -> Dict:
    """Reject and cleanup a staged task."""
    index = load_index()
    if task_id not in index["tasks"]:
        return {"success": False, "error": "Task not found"}

    # Update status
    index["tasks"][task_id]["status"] = "rejected"
    index["tasks"][task_id]["rejected_at"] = datetime.now().isoformat()
    index["tasks"][task_id]["reject_reason"] = reason
    save_index(index)

    # Optionally cleanup files
    task_dir = STAGING_ROOT / task_id
    if task_dir.exists():
        shutil.rmtree(task_dir)

    return {"success": True, "task_id": task_id}


def load_index() -> Dict:
    """Load staging index."""
    if STAGING_INDEX.exists():
        with open(STAGING_INDEX) as f:
            return json.load(f)
    return {"tasks": {}}


def save_index(index: Dict):
    """Save staging index."""
    with open(STAGING_INDEX, 'w') as f:
        json.dump(index, f, indent=2)


# CLI interface
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: staging_manager.py <command> [args]")
        print("Commands: pending, diff <task_id>, merge <task_id>, reject <task_id>")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "pending":
        pending = get_pending_tasks()
        print(f"Pending tasks: {len(pending)}")
        for t in pending:
            print(f"  {t['task_id']}: {len(t['files'])} files")

    elif cmd == "diff" and len(sys.argv) > 2:
        task_id = sys.argv[2]
        index = load_index()
        if task_id in index["tasks"]:
            for f in index["tasks"][task_id].get("files", []):
                diff = get_task_diff(task_id, f)
                status = "NEW" if diff["is_new"] else "MODIFY"
                print(f"[{status}] {f}")

    elif cmd == "merge" and len(sys.argv) > 2:
        task_id = sys.argv[2]
        result = merge_task(task_id)
        print(json.dumps(result, indent=2))

    elif cmd == "reject" and len(sys.argv) > 2:
        task_id = sys.argv[2]
        reason = sys.argv[3] if len(sys.argv) > 3 else None
        result = reject_task(task_id, reason)
        print(json.dumps(result, indent=2))
```

### Step 2: Update RLM Executor to Use Staging

Edit `/ganuda/lib/rlm_executor.py`:

Add at the top:
```python
from staging_manager import stage_file, create_task_staging
```

Modify the file writing logic to use staging for protected paths:

```python
PROTECTED_PREFIXES = [
    '/ganuda/lib/',
    '/ganuda/services/',
    '/ganuda/telegram_bot/',
    '/ganuda/jr_executor/',
]

def is_protected_path(filepath: str) -> bool:
    """Check if path is protected."""
    for prefix in PROTECTED_PREFIXES:
        if filepath.startswith(prefix):
            return True
    return False

def write_file_safe(task_id: str, filepath: str, content: str) -> dict:
    """Write file, using staging for protected paths."""
    if is_protected_path(filepath):
        # Use staging
        relative = filepath.replace('/ganuda/', '')
        staged_path = stage_file(task_id, relative, content)
        return {
            "success": True,
            "staged": True,
            "path": str(staged_path),
            "message": f"Staged to {staged_path} - awaiting TPM merge"
        }
    else:
        # Direct write for non-protected paths
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(content)
        return {
            "success": True,
            "staged": False,
            "path": filepath
        }
```

### Step 3: Create Staging Review Command

Add to `/ganuda/telegram_bot/telegram_chief.py`:

```python
async def staging_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /staging command - review pending staged changes."""
    from staging_manager import get_pending_tasks, get_task_diff

    pending = get_pending_tasks()

    if not pending:
        await update.message.reply_text("No pending staged changes.")
        return

    msg = f"📦 *Pending Staged Changes: {len(pending)}*\n\n"

    for task in pending[:5]:  # Show first 5
        msg += f"*Task:* `{task['task_id']}`\n"
        msg += f"*Files:* {len(task['files'])}\n"
        for f in task['files'][:3]:
            msg += f"  • {f}\n"
        if len(task['files']) > 3:
            msg += f"  _...and {len(task['files']) - 3} more_\n"
        msg += "\n"

    msg += "_Use /merge <task_id> to approve_"

    await update.message.reply_text(msg, parse_mode="Markdown")
```

---

## Testing

1. Create staging directory:
   ```bash
   mkdir -p /ganuda/staging
   ```

2. Test staging a file:
   ```python
   from staging_manager import stage_file
   stage_file("test123", "telegram_bot/test.py", "print('hello')")
   ```

3. Check pending:
   ```bash
   python3 /ganuda/lib/staging_manager.py pending
   ```

4. Merge:
   ```bash
   python3 /ganuda/lib/staging_manager.py merge test123
   ```

---

## Files Summary

| File | Action |
|------|--------|
| `/ganuda/lib/staging_manager.py` | CREATE |
| `/ganuda/lib/rlm_executor.py` | MODIFY - use staging for protected paths |
| `/ganuda/telegram_bot/telegram_chief.py` | MODIFY - add /staging command |

---

FOR SEVEN GENERATIONS

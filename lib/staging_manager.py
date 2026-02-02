#!/usr/bin/env python3
"""
Staging Manager - Manage Jr code staging for safe execution.
Cherokee AI Federation - For Seven Generations

Jrs write to /ganuda/staging/{task_id}/ instead of protected paths.
TPM reviews and merges approved changes.
"""

import os
import shutil
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

    # Cleanup files
    task_dir = STAGING_ROOT / task_id
    if task_dir.exists():
        shutil.rmtree(task_dir)

    return {"success": True, "task_id": task_id}


def cleanup_old_tasks(days: int = 7) -> Dict:
    """Cleanup merged/rejected tasks older than N days."""
    index = load_index()
    cleaned = []
    cutoff = datetime.now().timestamp() - (days * 86400)

    for task_id, info in list(index["tasks"].items()):
        if info.get("status") in ["merged", "rejected"]:
            created = datetime.fromisoformat(info.get("created_at", "2020-01-01"))
            if created.timestamp() < cutoff:
                # Remove from index
                del index["tasks"][task_id]
                # Remove directory if exists
                task_dir = STAGING_ROOT / task_id
                if task_dir.exists():
                    shutil.rmtree(task_dir)
                cleaned.append(task_id)

    save_index(index)
    return {"cleaned": len(cleaned), "task_ids": cleaned}


def load_index() -> Dict:
    """Load staging index."""
    init_staging()
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
        print("Staging Manager - Cherokee AI Federation")
        print()
        print("Usage: staging_manager.py <command> [args]")
        print()
        print("Commands:")
        print("  pending              - List pending staged tasks")
        print("  diff <task_id>       - Show diff for task files")
        print("  merge <task_id>      - Merge staged files to production")
        print("  reject <task_id>     - Reject and cleanup task")
        print("  cleanup [days]       - Cleanup old merged/rejected tasks")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "pending":
        pending = get_pending_tasks()
        print(f"Pending staged tasks: {len(pending)}")
        print()
        for t in pending:
            print(f"  Task: {t['task_id']}")
            print(f"  Created: {t['created_at']}")
            print(f"  Files: {len(t['files'])}")
            for f in t['files']:
                print(f"    - {f}")
            print()

    elif cmd == "diff" and len(sys.argv) > 2:
        task_id = sys.argv[2]
        index = load_index()
        if task_id in index["tasks"]:
            for f in index["tasks"][task_id].get("files", []):
                diff = get_task_diff(task_id, f)
                status = "NEW" if diff.get("is_new") else "MODIFY"
                staged_lines = diff.get("staged_lines", 0)
                prod_lines = diff.get("production_lines", 0)
                print(f"[{status}] {f} ({staged_lines} lines, was {prod_lines})")
        else:
            print(f"Task {task_id} not found")

    elif cmd == "merge" and len(sys.argv) > 2:
        task_id = sys.argv[2]
        result = merge_task(task_id)
        if result["success"]:
            print(f"Merged {len(result['merged'])} files:")
            for f in result["merged"]:
                print(f"  ✓ {f}")
        else:
            print(f"Merge failed: {result.get('error')}")
            for e in result.get("errors", []):
                print(f"  ✗ {e['file']}: {e['error']}")

    elif cmd == "reject" and len(sys.argv) > 2:
        task_id = sys.argv[2]
        reason = sys.argv[3] if len(sys.argv) > 3 else None
        result = reject_task(task_id, reason)
        if result["success"]:
            print(f"Rejected task {task_id}")
        else:
            print(f"Reject failed: {result.get('error')}")

    elif cmd == "cleanup":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        result = cleanup_old_tasks(days)
        print(f"Cleaned up {result['cleaned']} old tasks")

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

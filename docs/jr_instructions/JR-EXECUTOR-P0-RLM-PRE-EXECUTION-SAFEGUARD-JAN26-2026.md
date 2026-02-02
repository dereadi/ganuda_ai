# JR Instruction: RLM Pre-Execution Safeguard (P0)

**Priority:** P0 - CRITICAL PRODUCTION FIX
**Sprint:** Infrastructure Emergency
**Created:** 2026-01-26
**Author:** TPM via Claude Code
**Depends On:** JR-EXECUTOR-P0-DISABLE-RLM-MODIFICATIONS-JAN26-2026.md

## Problem Statement

The RLM executor has a safeguard that runs AFTER the RLM library executes generated Python code. By the time the safeguard checks file sizes, the files are already overwritten. This is a defense-in-depth fix.

**Root Cause:** Safeguard at `rlm_executor.py:358-375` runs AFTER `self.rlm.completion()` which already executed destructive code.

## Required Changes

MODIFY: `/ganuda/lib/rlm_executor.py`

### Add Pre-Execution Safeguard to `execute_task` Method

Find the `execute_task` method (approximately line 130-170).

**Add this safeguard block at the BEGINNING of the method, BEFORE any RLM completion calls:**

```python
def execute_task(self, task: Dict) -> Dict:
    """Execute with pre-validation safeguards."""
    import os

    # ============================================================
    # PRE-EXECUTION SAFEGUARD (Added Jan 26, 2026 - Council Emergency)
    # Block RLM execution if ANY modification is requested.
    # RLM is only safe for creating NEW files that don't exist.
    # ============================================================

    # BLOCK if any files_to_modify present
    files_to_modify = task.get('files_to_modify', [])
    if files_to_modify:
        print(f"[RLM PRE-SAFEGUARD] BLOCKED: Task requests modification of {len(files_to_modify)} files")
        return {
            "success": False,
            "error": "RLM cannot modify existing files safely. Use targeted edit approach.",
            "blocked_by": "pre_execution_safeguard",
            "files_blocked": files_to_modify
        }

    # BLOCK if any "create" file already exists
    files_to_create = task.get('files_to_create', [])
    for f in files_to_create:
        path = f[0] if isinstance(f, tuple) else f
        if os.path.exists(path):
            print(f"[RLM PRE-SAFEGUARD] BLOCKED: Create target already exists: {path}")
            return {
                "success": False,
                "error": f"Cannot create file that already exists: {path}",
                "blocked_by": "pre_execution_safeguard",
                "existing_file": path
            }

    # ============================================================
    # END PRE-EXECUTION SAFEGUARD
    # ============================================================

    # ... existing code continues below ...
```

### Locate the Insertion Point

The existing method likely starts with logging or prompt building. Insert the safeguard block immediately after the method signature.

**Before:**
```python
def execute_task(self, task: Dict) -> Dict:
    """Execute task using RLM."""
    prompt = self._build_execution_prompt(task)
    # ... continues
```

**After:**
```python
def execute_task(self, task: Dict) -> Dict:
    """Execute task using RLM."""
    import os

    # PRE-EXECUTION SAFEGUARD (see full block above)
    files_to_modify = task.get('files_to_modify', [])
    if files_to_modify:
        # ... safeguard block ...

    prompt = self._build_execution_prompt(task)
    # ... continues
```

## Verification

After applying this change, run:

```bash
cd /ganuda
python3 -c "
from lib.rlm_executor import RLMExecutor
import tempfile
import os

# Create test file to simulate existing file
with tempfile.NamedTemporaryFile(delete=False, suffix='.tsx') as f:
    f.write(b'// production code')
    test_file = f.name

# Test 1: Should block modifications
task1 = {
    'task_id': 'test1',
    'title': 'Test Modify Block',
    'files_to_modify': [test_file]
}

executor = RLMExecutor()
result1 = executor.execute_task(task1)

assert result1['success'] == False, 'FAIL: RLM should block modifications'
assert 'pre_execution_safeguard' in result1.get('blocked_by', ''), 'FAIL: Wrong blocker'
print('✓ Test 1 PASS: RLM blocked for modifications')

# Test 2: Should block create if file exists
task2 = {
    'task_id': 'test2',
    'title': 'Test Create Existing Block',
    'files_to_create': [(test_file, 'test')]
}

result2 = executor.execute_task(task2)

assert result2['success'] == False, 'FAIL: RLM should block create on existing'
assert 'pre_execution_safeguard' in result2.get('blocked_by', ''), 'FAIL: Wrong blocker'
print('✓ Test 2 PASS: RLM blocked for create-existing')

os.unlink(test_file)
print('\\n✅ All pre-execution safeguard tests passed')
"
```

Expected output:
```
[RLM PRE-SAFEGUARD] BLOCKED: Task requests modification of 1 files
✓ Test 1 PASS: RLM blocked for modifications
[RLM PRE-SAFEGUARD] BLOCKED: Create target already exists: /tmp/...
✓ Test 2 PASS: RLM blocked for create-existing

✅ All pre-execution safeguard tests passed
```

## Deployment

No service restart required - changes take effect on next task execution.

## Rollback

Remove the PRE-EXECUTION SAFEGUARD block from `execute_task()`.

---
FOR SEVEN GENERATIONS

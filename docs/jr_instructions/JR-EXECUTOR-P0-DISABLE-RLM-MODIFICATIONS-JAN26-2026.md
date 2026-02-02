# JR Instruction: Disable RLM for File Modifications (P0)

**Priority:** P0 - CRITICAL PRODUCTION FIX
**Sprint:** Infrastructure Emergency
**Created:** 2026-01-26
**Author:** TPM via Claude Code
**Blocks:** All Jr code modification tasks

## Problem Statement

The RLM executor overwrites entire files when asked to modify them. A 261-line React component was replaced with a 30-line stub, destroying production code.

**Root Cause:** RLM generates Python code that runs `open(file, 'w')` which truncates existing files.

## Required Changes

MODIFY: `/ganuda/jr_executor/task_executor.py`

### Find and Replace `_should_use_rlm` Method

Locate the method `_should_use_rlm` (approximately line 250-280).

**Current logic allows RLM for modifications.**

**Replace entire method with:**

```python
def _should_use_rlm(self, task: Dict, instructions: str) -> bool:
    """
    Determine if task should use RLM recursive execution.

    CRITICAL FIX Jan 26, 2026 (Council Emergency Vote):
    NEVER use RLM for file modifications - it overwrites entire files!
    RLM generates Python code with open('w') which truncates files.
    Only safe for creating NEW files that don't exist.

    See: ULTRATHINK-JR-EXECUTOR-ARCHITECTURE-FIX-JAN26-2026.md
    """
    import os

    # BLOCK: Never use RLM if modifying existing files
    files_to_modify = task.get('files_to_modify', [])
    if files_to_modify:
        print(f"[RLM] BLOCKED: Task has {len(files_to_modify)} files_to_modify - using targeted edit instead")
        return False

    # Only consider RLM for pure creation tasks
    files_to_create = task.get('files_to_create', [])
    if not files_to_create:
        return False

    # Verify all "create" paths are actually new (don't exist)
    for f in files_to_create:
        path = f[0] if isinstance(f, tuple) else f
        if os.path.exists(path):
            print(f"[RLM] BLOCKED: 'Create' file already exists: {path}")
            return False

    # Check for RLM indicators in instructions
    rlm_indicators = [
        'complex logic',
        'recursive',
        'multi-step algorithm',
        'generate from scratch'
    ]

    instructions_lower = instructions.lower()
    if any(indicator in instructions_lower for indicator in rlm_indicators):
        print(f"[RLM] Approved for new file creation task")
        return True

    return False
```

## Verification

After applying this change, run:

```bash
cd /ganuda/jr_executor
python3 -c "
from task_executor import TaskExecutor
import json

t = TaskExecutor()

# Test 1: Should block modifications
task1 = {
    'task_id': 'test1',
    'title': 'Test Modify',
    'files_to_modify': ['/ganuda/test.py']
}
result1 = t._should_use_rlm(task1, 'modify this file')
assert result1 == False, 'FAIL: RLM should be blocked for modifications'
print('✓ Test 1 PASS: RLM blocked for modifications')

# Test 2: Should block if create file exists
import tempfile
with tempfile.NamedTemporaryFile(delete=False, suffix='.py') as f:
    existing_path = f.name
    f.write(b'# existing')

task2 = {
    'task_id': 'test2',
    'title': 'Test Create Existing',
    'files_to_create': [(existing_path, 'test')]
}
result2 = t._should_use_rlm(task2, 'create this file')
assert result2 == False, 'FAIL: RLM should be blocked for existing files'
print('✓ Test 2 PASS: RLM blocked for existing files')

import os
os.unlink(existing_path)

print('\\n✅ All tests passed - RLM safeguard active')
"
```

Expected output:
```
[RLM] BLOCKED: Task has 1 files_to_modify - using targeted edit instead
✓ Test 1 PASS: RLM blocked for modifications
[RLM] BLOCKED: 'Create' file already exists: /tmp/...
✓ Test 2 PASS: RLM blocked for existing files

✅ All tests passed - RLM safeguard active
```

## Deployment

No service restart required - changes take effect on next task execution.

## Rollback

If issues arise, revert to original `_should_use_rlm` method from git history.

---
FOR SEVEN GENERATIONS

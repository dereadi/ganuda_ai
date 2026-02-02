# Ultrathink: Jr Executor False Completion Bug

**Date:** January 27, 2026
**Priority:** P0 - Blocking Jr autonomous work
**TPM:** Claude Opus

---

## Problem Statement

Jrs are marking tasks as "completed" without actually doing work.

Evidence from task #386:
```json
{
  "summary": "Task 'MAGRPO Phase 2: Momentum Learner Integration': No steps executed",
  "steps_executed": [],
  "status": "completed"  // <-- BUG: Should be "failed"
}
```

---

## Root Cause Analysis

### Execution Path Traced

1. **jr_queue_worker.py** polls for task
2. Calls `executor.process_queue_task(task)`
3. Task has `use_rlm = true`, so goes to `_should_use_rlm()` → returns True
4. Calls `_execute_with_rlm(task, instructions)`
5. RLMExecutor.execute_task() runs

### Bug Location 1: rlm_executor.py:213-220

```python
result = {
    "success": True,  # <-- ALWAYS TRUE if no exception
    "result": response_text,
    "subtasks_completed": getattr(response, 'recursion_count', 1)
        if hasattr(response, 'recursion_count') else 1,  # <-- DEFAULTS TO 1
    "artifacts": artifacts,
    ...
}
```

**Problem**:
- `success` is always True if the LLM call succeeds, even if no files were created
- `subtasks_completed` defaults to 1 even when no actual subtasks ran

### Bug Location 2: task_executor.py:759-766

```python
# CRITICAL FIX: RLM must have done actual work
subtasks = result.get('subtasks_completed', 0)
artifacts = result.get('artifacts', [])
if result['success'] and subtasks == 0 and not artifacts:
    result['success'] = False
    result['error'] = 'RLM execution reported success but no subtasks...'
```

**Problem**: The check says `subtasks == 0`, but rlm_executor.py defaults subtasks_completed to 1!

The safeguard never triggers because:
- `subtasks_completed = 1` (default, not 0)
- `artifacts = []` (empty, but check requires BOTH conditions)

### Bug Location 3: jr_queue_worker.py:113-125

```python
if result.get('success'):
    print(f"[{self.jr_name}] Task completed successfully")
    self.client.complete_task(...)
```

Worker trusts the `success` flag from executor without additional validation.

---

## Why Task #386 Failed Silently

1. RLM read the instruction file (7,578 chars)
2. Sent prompt to vLLM Qwen 32B
3. Model generated a response (text)
4. `_write_files_from_response()` parsed response for file patterns
5. Found NO matching patterns (LLM didn't follow expected format)
6. `artifacts = []` (empty)
7. **But** `subtasks_completed = 1` (default)
8. Safeguard check: `subtasks == 0` → False, check doesn't trigger
9. `success = True` returned
10. Worker marks task "completed"

---

## Fixes Required

### Fix 1: rlm_executor.py - Accurate subtask counting

```python
# Line 213-220, change to:
actual_subtasks = getattr(response, 'recursion_count', 0)  # Default 0
artifacts_created = len([a for a in artifacts if a.get('type') == 'file_created'])

result = {
    "success": artifacts_created > 0 or actual_subtasks > 0,  # Success requires work
    "result": response_text,
    "subtasks_completed": actual_subtasks,  # Don't inflate
    "artifacts": artifacts,
    "files_created": artifacts_created,
    ...
}
```

### Fix 2: task_executor.py - Stronger validation

```python
# Line 759-766, change to:
subtasks = result.get('subtasks_completed', 0)
artifacts = result.get('artifacts', [])
files_created = result.get('files_created', 0)

# Require ACTUAL work to have been done
if result['success'] and (subtasks == 0 and files_created == 0):
    result['success'] = False
    result['error'] = 'RLM reported success but created no files'
```

### Fix 3: jr_queue_worker.py - Secondary validation

```python
# After line 113, add:
# Double-check that work was actually done
steps = result.get('steps_executed', [])
artifacts = result.get('artifacts', [])
files_created = result.get('files_created', 0)

if result.get('success') and not steps and not artifacts and files_created == 0:
    result['success'] = False
    result['error'] = 'No actual work performed (0 steps, 0 artifacts, 0 files)'
```

---

## Defense in Depth

Three layers of validation:
1. **RLM Executor**: Must create files to report success
2. **Task Executor**: Validates RLM claims before returning
3. **Queue Worker**: Final check before marking complete

---

## Test Case

After fixes, task #386 behavior:
1. RLM runs, creates no files
2. `files_created = 0`, `subtasks_completed = 0`
3. `success = False` at rlm_executor.py
4. Task marked "failed" with clear error message

---

## Files to Modify

| File | Change |
|------|--------|
| `/ganuda/lib/rlm_executor.py` | Fix success/subtasks logic |
| `/ganuda/jr_executor/task_executor.py` | Strengthen RLM validation |
| `/ganuda/jr_executor/jr_queue_worker.py` | Add secondary validation |

---

FOR SEVEN GENERATIONS

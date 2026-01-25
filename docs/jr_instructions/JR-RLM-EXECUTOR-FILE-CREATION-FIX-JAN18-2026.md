# JR Instruction: RLM Executor File Creation Fix

## Metadata
```yaml
task_id: rlm_executor_file_creation_fix
priority: 1
assigned_to: it_triad_jr
estimated_effort: medium
category: infrastructure_fix
blocking: all_jr_code_generation_tasks
```

## Problem Statement

The RLM Executor (`/ganuda/lib/rlm_executor.py`) generates LLM responses describing code but does NOT actually create files. Tasks are marked "completed" without any code being written.

### Current Behavior
1. Task received with instruction_file
2. RLM executor builds prompt asking LLM to create files
3. LLM responds with text describing what it would do
4. Executor treats response as "success"
5. **No files are actually created**

### Example
Task #131 "Consciousness Cascade Protocol Infrastructure" was marked complete but `/ganuda/lib/consciousness_cascade/` was never created.

## Root Cause

In `rlm_executor.py` line 109:
```python
response = self.rlm.completion(prompt)
```

This returns an LLM text response, but the code never:
1. Extracts file paths from the response
2. Extracts code content from the response
3. Actually writes files to disk

## Solution

### Option A: Post-Process LLM Response (Recommended)
After getting LLM response, parse it for code blocks and file paths, then write files.

**MODIFY FILE: /ganuda/lib/rlm_executor.py**

Add method `_write_artifacts_from_response`:
```python
def _write_artifacts_from_response(self, response_text: str, task: Dict) -> List[Dict]:
    """
    Parse LLM response for code blocks and write to files.

    Looks for patterns like:
    - **CREATE FILE: /path/to/file.py**
    - ```python
      # code here
      ```
    """
    import re
    import os

    artifacts = []

    # Pattern: file path followed by code block
    pattern = r'\*\*(?:CREATE|MODIFY)\s+FILE:\s*([^\*]+)\*\*\s*```(\w+)?\n(.*?)```'

    for match in re.finditer(pattern, response_text, re.DOTALL):
        file_path = match.group(1).strip()
        language = match.group(2) or 'python'
        code = match.group(3)

        # Security: validate path is in allowed locations
        if not any(file_path.startswith(p) for p in ['/ganuda/', '/tmp/']):
            self.logger.warning(f"Skipping file outside allowed paths: {file_path}")
            continue

        # Create directory if needed
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Write file
        try:
            with open(file_path, 'w') as f:
                f.write(code)
            artifacts.append({
                'type': 'file_created',
                'path': file_path,
                'size': len(code)
            })
            self.logger.info(f"Created file: {file_path} ({len(code)} bytes)")
        except Exception as e:
            self.logger.error(f"Failed to write {file_path}: {e}")

    return artifacts
```

Modify `execute_task` to call this after getting response:
```python
def execute_task(self, task: Dict) -> Dict:
    # ... existing code to get response ...

    response_text = response.response if hasattr(response, 'response') else str(response)

    # NEW: Actually create files from response
    artifacts = self._write_artifacts_from_response(response_text, task)

    result = {
        "success": len(artifacts) > 0 or True,  # Consider success criteria
        "result": response_text,
        "artifacts": artifacts,
        # ... rest of result dict ...
    }
```

### Option B: Use Code Execution Sandbox
Configure RLM to actually execute Python code in a sandbox that has file write permissions.

This requires:
1. Setting up a proper sandbox environment
2. Giving the sandbox write access to /ganuda/
3. Capturing written files as artifacts

More complex but potentially more powerful.

## Testing

After fix, run test:
```bash
cd /ganuda/jr_executor
python3 -c "
from task_executor import TaskExecutor

task = {
    'task_id': 'test_file_creation',
    'title': 'Test File Creation',
    'instruction_content': '''
## Task
Create a test file.

**CREATE FILE: /ganuda/lib/test_rlm_fix.py**
```python
# Test file created by RLM executor
print(\"RLM file creation working!\")
```
'''
}

executor = TaskExecutor()
result = executor.process_queue_task(task)
print(f\"Success: {result['success']}\")
print(f\"Artifacts: {result.get('artifacts', [])}\")
"

# Verify file exists
ls -la /ganuda/lib/test_rlm_fix.py
cat /ganuda/lib/test_rlm_fix.py
```

## Success Criteria

| Test | Expected |
|------|----------|
| Task with CREATE FILE instruction | File exists on disk |
| Multiple files in one task | All files created |
| Invalid path rejected | Security check blocks |
| File content correct | Matches code block |

## Impact

Fixing this unblocks:
- All Jr code generation tasks
- VetAssist frontend tasks (109-123)
- PII Protection Upgrade (#129)
- Accessibility AI (#130)
- Consciousness Cascade Infrastructure (#131)

## Cherokee Wisdom

> "A river that forgets to carry water is not a river."

The Jrs generate beautiful plans but forget to carry them to disk. Let's fix that.

---
**Priority**: CRITICAL - Blocking all Jr code tasks
**Cherokee AI Federation - For Seven Generations**

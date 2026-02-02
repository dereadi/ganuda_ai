# JR Instruction: Wire TargetedEditor into TaskExecutor (P1)

**Priority:** P1 - HIGH
**Sprint:** Infrastructure Emergency
**Created:** 2026-01-26
**Author:** TPM via Claude Code
**Depends On:**
- JR-EXECUTOR-P0-DISABLE-RLM-MODIFICATIONS-JAN26-2026.md
- JR-EXECUTOR-P1-TARGETED-EDITOR-MODULE-JAN26-2026.md

## Problem Statement

After disabling RLM for file modifications and creating the TargetedEditor module, we need to wire it into the TaskExecutor so that modification tasks use the safe targeted edit approach.

## Required Changes

MODIFY: `/ganuda/jr_executor/task_executor.py`

### 1. Add Import at Top of File

Find the imports section (approximately lines 1-30) and add:

```python
from lib.targeted_editor import TargetedEditor
```

### 2. Add `_execute_targeted_edit` Method

Find a location after the `_execute_with_rlm` method (approximately line 350-400) and add this new method:

```python
def _execute_targeted_edit(self, task: Dict, instructions: str) -> Dict:
    """
    Execute file modifications using targeted edit approach.
    SAFE alternative to RLM for existing files.

    Added: January 26, 2026 (Council Emergency Fix)
    """
    result = {
        "success": True,
        "task_id": task.get("task_id"),
        "title": task.get("title"),
        "execution_mode": "targeted_edit",
        "edits": [],
        "artifacts": [],
        "error": None
    }

    editor = TargetedEditor()
    files_to_modify = task.get("files_to_modify", [])

    if not files_to_modify:
        result["error"] = "No files_to_modify in task"
        result["success"] = False
        return result

    # Extract specific changes from instructions if available
    changes_by_file = self._extract_changes_from_instructions(instructions)

    for file_info in files_to_modify:
        file_path = file_info[0] if isinstance(file_info, tuple) else file_info

        print(f"[TaskExecutor] Targeted edit: {file_path}")

        # Get file-specific changes if extracted
        file_changes = changes_by_file.get(file_path, None)

        edit_result = editor.modify_file(
            file_path=file_path,
            instructions=instructions,
            specific_changes=file_changes
        )

        result["edits"].append({
            "file": file_path,
            "success": edit_result["success"],
            "backup": edit_result.get("backup_path"),
            "diff_preview": edit_result.get("diff", "")[:500],
            "changes_made": edit_result.get("changes_made", []),
            "error": edit_result.get("error")
        })

        if not edit_result["success"]:
            result["success"] = False
            result["error"] = f"Edit failed for {file_path}: {edit_result.get('error')}"
            # Continue with other files to report all failures

    return result

def _extract_changes_from_instructions(self, instructions: str) -> Dict[str, List[Dict]]:
    """
    Extract specific old->new changes from instruction format.

    Looks for patterns like:
    **Current:**
    ```code
    old code here
    ```

    **Change to:**
    ```code
    new code here
    ```

    Returns:
        {
            "/path/to/file.tsx": [
                {"old": "...", "new": "...", "description": "..."},
            ]
        }
    """
    import re

    changes = {}

    # Find all MODIFY: file paths
    modify_pattern = r'MODIFY:\s*`?([^`\s\n]+)`?'
    modify_files = re.findall(modify_pattern, instructions, re.IGNORECASE)

    # Pattern: **Current:** ... **Change to:**
    change_pattern = r'''
        (?:###\s*\d+\.?\s*([^(\n]+?))?         # Optional step title
        (?:\([^)]*?line[s]?\s*[\d\-]+[^)]*\))? # Optional (line X-Y)
        \s*
        \*\*Current:?\*\*\s*
        ```\w*\n?
        (.*?)
        ```
        \s*
        \*\*Change\s+to:?\*\*\s*
        ```\w*\n?
        (.*?)
        ```
    '''

    for match in re.finditer(change_pattern, instructions, re.DOTALL | re.VERBOSE | re.IGNORECASE):
        step_title = (match.group(1) or "").strip()
        old_code = match.group(2).strip()
        new_code = match.group(3).strip()

        if not old_code:
            continue

        # Find the most recently mentioned MODIFY: file before this match
        before_match = instructions[:match.start()]
        target_file = None

        for f in reversed(modify_files):
            if f in before_match or before_match.endswith(f):
                target_file = f
                break

        # Default to first MODIFY: file if no context match
        if not target_file and modify_files:
            target_file = modify_files[0]

        if target_file:
            if target_file not in changes:
                changes[target_file] = []
            changes[target_file].append({
                "old": old_code,
                "new": new_code,
                "description": step_title
            })

    return changes
```

### 3. Update Task Processing Logic

Find the main task processing method (`process_queue_task` or `execute_task`, approximately line 200-280).

Add routing logic to use targeted edit for modifications:

**Find code similar to:**
```python
# Existing code that checks _should_use_rlm
if self._should_use_rlm(task, instructions):
    return self._execute_with_rlm(task, instructions)
```

**Add BEFORE the RLM check:**
```python
# Route modifications to targeted editor (Jan 26, 2026 fix)
files_to_modify = task.get('files_to_modify', [])
if files_to_modify:
    print(f"[TaskExecutor] Using targeted edit for {len(files_to_modify)} files")
    return self._execute_targeted_edit(task, instructions)
```

**The full section should look like:**
```python
def process_queue_task(self, task: Dict) -> Dict:
    """Process a task from the queue."""
    # ... existing setup code ...

    instructions = self._load_instructions(task)

    # Route modifications to targeted editor (Jan 26, 2026 fix)
    files_to_modify = task.get('files_to_modify', [])
    if files_to_modify:
        print(f"[TaskExecutor] Using targeted edit for {len(files_to_modify)} files")
        return self._execute_targeted_edit(task, instructions)

    # Only use RLM for pure creation tasks
    if self._should_use_rlm(task, instructions):
        return self._execute_with_rlm(task, instructions)

    # ... rest of existing code ...
```

## Verification

After applying these changes, run:

```bash
cd /ganuda/jr_executor
python3 -c "
from task_executor import TaskExecutor
import tempfile
import os

t = TaskExecutor()

# Create test file
test_content = '''
interface Props {
    name: string;
}

export function Hello({ name }: Props) {
    return <div>Hello {name}</div>;
}
'''

with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tsx') as f:
    f.write(test_content)
    test_file = f.name

# Test: Task with files_to_modify should use targeted edit
task = {
    'task_id': 'test-targeted',
    'title': 'Test Targeted Edit',
    'files_to_modify': [test_file],
    'instruction_file': None
}

# Mock instructions
class MockExecutor(TaskExecutor):
    def _load_instructions(self, task):
        return '''
MODIFY: ''' + test_file + '''

### 1. Add age prop

**Current:**
\`\`\`
interface Props {
    name: string;
}
\`\`\`

**Change to:**
\`\`\`
interface Props {
    name: string;
    age: number;
}
\`\`\`
'''

executor = MockExecutor()
result = executor.process_queue_task(task)

assert result.get('execution_mode') == 'targeted_edit', f'FAIL: Wrong mode: {result.get(\"execution_mode\")}'
assert result.get('success', False), f'FAIL: {result.get(\"error\")}'
print('✓ Test PASS: Modifications routed to targeted edit')

# Verify content
with open(test_file) as f:
    new_content = f.read()
assert 'age: number' in new_content, 'FAIL: Change not applied'
assert 'Hello {name}' in new_content, 'FAIL: Other code was removed!'
print('✓ Test PASS: Change applied, other code preserved')

os.unlink(test_file)
print('\\n✅ TaskExecutor integration tests passed')
"
```

Expected output:
```
[TaskExecutor] Using targeted edit for 1 files
[TaskExecutor] Targeted edit: /tmp/...
[TargetedEditor] Backup created: /ganuda/backups/jr_edits/...
[TargetedEditor] Successfully modified: /tmp/...
✓ Test PASS: Modifications routed to targeted edit
✓ Test PASS: Change applied, other code preserved

✅ TaskExecutor integration tests passed
```

## Deployment

No service restart required - changes take effect on next task execution.

---
FOR SEVEN GENERATIONS

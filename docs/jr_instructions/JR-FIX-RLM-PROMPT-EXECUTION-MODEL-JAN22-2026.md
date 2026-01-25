# JR: Fix RLM Prompt to Use Execution Model

**Date:** January 22, 2026
**Priority:** Critical
**Type:** Bug Fix
**Assigned To:** Software Engineer Jr

## Problem

The RLM executor prompt asks the model to output markdown-formatted file content:
```
**CREATE FILE: /path/file.py**
```python
code here
```
```

But the RLM library executes Python code in a sandbox. The model outputs `repl` blocks with Python code that gets executed, causing a mismatch.

## Root Cause

The RLM library's `environment="local"` mode expects the model to:
1. Generate Python code in ````repl` blocks
2. Code gets executed in a sandbox
3. Model calls `FINAL_VAR(result)` to output final answer

Our prompt tells the model to output markdown, but the library executes Python.

## Solution

Change `_build_execution_prompt()` in `/ganuda/lib/rlm_executor.py` to generate Python code that writes files.

## Implementation

### Edit `/ganuda/lib/rlm_executor.py`

Replace the `_build_execution_prompt` method (lines 139-177) with:

```python
    def _build_execution_prompt(self, task: Dict) -> str:
        """Build the RLM execution prompt for a task."""
        files_create = json.dumps(task.get('files_to_create', []))
        files_modify = json.dumps(task.get('files_to_modify', []))

        return f"""You are a Jr engineer executing a task. Write Python code to CREATE the actual files.

TASK: {task.get('title', 'Unknown task')}

INSTRUCTIONS:
{task.get('instructions', '')}

FILES TO CREATE: {files_create}
FILES TO MODIFY: {files_modify}

EXECUTION MODEL:
You must write Python code that ACTUALLY CREATES FILES using open() and write().

Example for creating a file:
```repl
import os

# Create directory if needed
os.makedirs('/ganuda/example/dir', exist_ok=True)

# Write the file
with open('/ganuda/example/dir/myfile.py', 'w') as f:
    f.write('''#!/usr/bin/env python3
# Your actual code content here
def my_function():
    return "hello"
''')

print("Created: /ganuda/example/dir/myfile.py")
```

RULES:
1. Write Python code that uses open() to create each file
2. Use triple-quoted strings for file content (use single quotes ''' to avoid escaping)
3. Always create parent directories with os.makedirs(path, exist_ok=True)
4. Print "Created: <filepath>" after each file
5. Only write to paths starting with /ganuda/ or /tmp/
6. After creating all files, call: FINAL_VAR({{"files_created": [list of paths], "success": True}})

DO NOT output markdown. Write executable Python code that creates the files.
Now write the Python code:
"""
```

## Testing

After the fix, rerun a test task:

```bash
# Reset task 263 to test
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
UPDATE jr_work_queue
SET status = 'assigned',
    result = NULL,
    artifacts = NULL,
    status_message = NULL
WHERE id = 263;
"

# Check logs
tail -f /ganuda/logs/jr_queue_worker.log
```

## Success Criteria

- [ ] Model generates Python code with `open()` calls
- [ ] Files actually created on disk
- [ ] `FINAL_VAR()` called with file list
- [ ] Task 263 completes with artifacts > 0

## For Seven Generations

Teaching the cluster to use the RLM execution model correctly enables autonomous code generation and file creation - a foundational capability for self-improving AI systems.

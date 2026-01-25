# Jr Instructions: Queue Worker Fix - December 20, 2025

**Priority**: 1
**Assigned Jr**: it_triad_jr
**Issue**: Jr queue worker calls `process_queue_task()` but TaskExecutor doesn't have this method

---

## OBJECTIVE

Fix the Jr queue worker infrastructure so that queued tasks are actually executed by the assigned Jr agents.

---

## ROOT CAUSE ANALYSIS

**Current State:**
- `jr_queue_worker.py` calls `self.executor.process_queue_task(task)`
- `task_executor.py` has `execute()` and `execute_steps()` but NO `process_queue_task()`
- Result: Worker crashes with `AttributeError: 'TaskExecutor' object has no attribute 'process_queue_task'`

**Queue Task Structure (from jr_work_queue table):**
```python
task = {
    'task_id': 'abc123...',
    'title': 'Some task title',
    'instruction_file': '/ganuda/docs/jr_instructions/JR_SOME_TASK.md',
    'assigned_jr': 'it_triad_jr',
    'priority': 1,
    'status': 'in_progress'
}
```

**TaskExecutor Expected Input:**
```python
step = {
    'action': 'sql|bash|file',
    'query': '...',  # for SQL
    'command': '...',  # for bash
    'path': '...',  # for file
    'content': '...'  # for file
}
```

---

### Task 1: Add process_queue_task Method to TaskExecutor

**File**: `/ganuda/jr_executor/task_executor.py`

**Add this method after `execute_steps()` (around line 110):**

```python
def process_queue_task(self, task: Dict) -> Dict[str, Any]:
    """
    Process a Jr work queue task by reading and executing instructions.

    Args:
        task: Dict with task_id, title, instruction_file, assigned_jr

    Returns:
        Dict with success status and execution details
    """
    result = {
        'task_id': task.get('task_id'),
        'title': task.get('title'),
        'success': False,
        'steps_executed': [],
        'error': None
    }

    instruction_file = task.get('instruction_file')
    if not instruction_file:
        result['error'] = 'No instruction_file specified in task'
        return result

    # Read the instruction file
    try:
        with open(instruction_file, 'r') as f:
            instructions = f.read()
    except FileNotFoundError:
        result['error'] = f'Instruction file not found: {instruction_file}'
        return result
    except Exception as e:
        result['error'] = f'Failed to read instruction file: {str(e)}'
        return result

    # Extract code blocks from instructions
    steps = self._extract_steps_from_instructions(instructions)

    if not steps:
        result['error'] = 'No executable steps found in instruction file'
        return result

    # Execute extracted steps
    try:
        step_results = self.execute_steps(steps)
        result['steps_executed'] = step_results

        # Check if all steps succeeded
        all_success = all(s.get('status') == 'success' for s in step_results)
        result['success'] = all_success

        if not all_success:
            failed = [s for s in step_results if s.get('status') != 'success']
            result['error'] = f'{len(failed)} step(s) failed'

    except Exception as e:
        result['error'] = f'Execution error: {str(e)}'

    return result


def _extract_steps_from_instructions(self, instructions: str) -> List[Dict]:
    """
    Extract executable steps from a Jr instruction markdown file.

    Looks for code blocks with action hints:
    - ```sql → SQL action
    - ```bash or ```shell → Bash action
    - ```python with Create `/path/file` → File action

    Returns list of step dicts ready for execute_steps()
    """
    import re

    steps = []

    # Pattern to match code blocks with language hint
    code_block_pattern = r'```(\w+)\n(.*?)```'

    # Find all code blocks
    matches = re.findall(code_block_pattern, instructions, re.DOTALL)

    for lang, content in matches:
        content = content.strip()

        if lang.lower() == 'sql':
            steps.append({
                'action': 'sql',
                'query': content
            })
        elif lang.lower() in ('bash', 'shell', 'sh'):
            steps.append({
                'action': 'bash',
                'command': content
            })
        elif lang.lower() == 'python':
            # Look for file creation pattern before this code block
            # Pattern: Create `/path/to/file`:
            file_pattern = r"Create\s+`([^`]+)`"

            # Search in the text before this code block
            block_start = instructions.find(f'```{lang}\n{content}')
            if block_start > 0:
                preceding_text = instructions[max(0, block_start-200):block_start]
                file_match = re.search(file_pattern, preceding_text)

                if file_match:
                    filepath = file_match.group(1)
                    steps.append({
                        'action': 'file',
                        'path': filepath,
                        'content': content
                    })

    return steps
```

---

### Task 2: Add Import for re Module

**File**: `/ganuda/jr_executor/task_executor.py`

**At the top of the file, add:**

```python
import re
```

---

### Task 3: Test the Fix

After applying the fix, test with:

```bash
cd /ganuda/jr_executor
python3 -c "
from task_executor import TaskExecutor
e = TaskExecutor()

# Test with a simple task
task = {
    'task_id': 'test123',
    'title': 'Test Task',
    'instruction_file': '/ganuda/docs/jr_instructions/JR_SAG_UI_FIXES_DEC20.md'
}

result = e.process_queue_task(task)
print('Success:', result.get('success'))
print('Steps:', len(result.get('steps_executed', [])))
print('Error:', result.get('error'))
"
```

---

## SUCCESS CRITERIA

1. `process_queue_task()` method added to TaskExecutor
2. Method reads instruction files and extracts code blocks
3. Extracted steps are passed to `execute_steps()`
4. Worker can process queue tasks without AttributeError
5. Test command runs successfully

---

## QUEUE THE TASK

After fixing, verify by running:

```bash
cd /ganuda/jr_executor
python3 jr_queue_worker.py 'it_triad_jr'
```

Worker should poll and process tasks without crashing.

---

*For Seven Generations - Cherokee AI Federation*

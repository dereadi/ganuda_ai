# Jr Instruction: Fix Task Executor instruction_content Support

**Priority**: P0 - CRITICAL
**Assigned**: it_triad_jr
**Sacred Fire**: YES
**Created**: January 17, 2026

---

## Task

Modify `/ganuda/jr_executor/task_executor.py` to support `instruction_content` in addition to `instruction_file`.

## File to Modify

Path: `/ganuda/jr_executor/task_executor.py`

## Current Code (to replace)

Find this code around line 163-195:

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
```

## New Code (replacement)

```python
    def process_queue_task(self, task: Dict) -> Dict[str, Any]:
        """
        Process a Jr work queue task by reading and executing instructions.

        Supports both instruction_file (path to .md file) and instruction_content
        (inline instructions stored in database).

        Args:
            task: Dict with task_id, title, instruction_file OR instruction_content, assigned_jr

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

        # Try instruction_content first (inline from database), then instruction_file
        instructions = task.get('instruction_content')
        instruction_source = 'instruction_content'

        if not instructions:
            instruction_file = task.get('instruction_file')
            if not instruction_file:
                result['error'] = 'No instruction_file or instruction_content specified in task'
                return result

            instruction_source = 'instruction_file'
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

        print(f"[TaskExecutor] Using instructions from {instruction_source} ({len(instructions)} chars)")
```

## Testing Steps

After applying the fix:

```bash
# 1. Restart the queue worker
sudo systemctl restart jr-queue-worker

# 2. Check that pending tasks with instruction_content get processed
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT id, title, status FROM jr_work_queue
WHERE instruction_content IS NOT NULL
  AND status = 'pending'
ORDER BY id LIMIT 5;
"

# 3. Watch logs for instruction_content processing
journalctl --user -u jr-queue-worker -f
```

---

*Cherokee AI Federation - For Seven Generations*

# KB: Jr Queue Task Requires instruction_file or instruction_content

**Date:** February 9, 2026
**Severity:** P1
**Category:** Jr Executor / Queue Client
**Related Ticket:** #1730 (VetAssist API Routing Fix)

## Problem

Task #661 was queued to the SE Jr worker but immediately failed with:
```
No instruction_file or instruction_content specified in task
```

The Jr instruction file existed at `/ganuda/docs/jr_instructions/JR-VETASSIST-API-ROUTING-FIX-FEB09-2026.md` but was not linked to the queue entry.

## Root Cause

When inserting a task into `jr_work_queue`, the `instruction_file` column was left NULL. The `task_executor.py` requires either:
- `instruction_file` — path to a `.md` file with SEARCH/REPLACE blocks
- `instruction_content` — inline instruction text in the `instruction_content` column

Without either, the executor immediately marks the task as `failed`.

## Fix

Always populate `instruction_file` when queuing tasks that reference Jr instruction documents:

```sql
INSERT INTO jr_work_queue (title, description, assigned_jr, priority, instruction_file, ...)
VALUES ('...', '...', 'Software Engineer Jr.', 2,
        '/ganuda/docs/jr_instructions/JR-EXAMPLE-INSTRUCTION.md', ...);
```

Task #662 was re-queued with the correct `instruction_file` path and completed successfully (4/4 edits applied).

## Prevention

When the TPM or any automation queues a task:
1. Verify the instruction file exists on disk before queuing
2. Always set `instruction_file` to the absolute path
3. Check result of failed tasks with: `SELECT error_message FROM jr_work_queue WHERE id = <task_id>`

## Related

- `jr_executor/task_executor.py` — checks for instruction_file at task load time
- `jr_executor/jr_queue_client.py` — `queue_task()` method should validate instruction_file exists

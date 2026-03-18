# Task Decomposition Guide

## When to Decompose

| Total SP | Action |
|----------|--------|
| 1-3 | Single Jr instruction, 1-5 steps |
| 5-8 | Single Jr instruction, 5-7 steps, OR 2 linked instructions |
| 8-13 | 2-3 linked Jr instructions with blocking dependencies |
| 13-21 | Epic with 3-5 Jr instructions, council review required |
| 21+ | Break into multiple epics first |

## Dependency Types

- **Blocking**: Task B cannot start until Task A completes. Use `Depends On: [TASK-A-ID]`
- **Informing**: Task B benefits from Task A's output but can proceed without it. Note in description, don't block
- **Independent**: No relationship. Can execute in parallel

## Decomposition Checklist

Before submitting a Jr instruction:
1. Can each step be executed independently? (If step 3 needs step 2's output, is that explicit?)
2. Are file paths absolute? (`/ganuda/lib/foo.py`, not `lib/foo.py`)
3. Does verification prove the task succeeded, not just that it ran?
4. If this task fails, does the rollback leave the system in a known state?
5. Is SP estimate realistic? (1 SP = 1-2 hours of Jr work including verification)

## Common Decomposition Mistakes

1. **God instruction**: 15+ steps, 400 lines, tries to do everything. Break it up.
2. **Orphan steps**: Step 4 creates a file that nothing references. Why?
3. **Implicit dependencies**: Step 3 assumes step 2's database migration ran. Make it explicit.
4. **Missing verification**: "Deploy the service" with no health check.
5. **Wrong granularity**: A 1 SP task split into 5 sub-tasks. Overhead > work.

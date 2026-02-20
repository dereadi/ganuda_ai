# KB: Jr Executor SR-FIRST Extraction Fix

**Date**: February 11, 2026
**Severity**: P1 — fixes root cause of 15+ failed Jr tasks
**Related**: KB-JR-EXECUTOR-SR-LARGE-FILE-FAILURE-PATTERN-FEB11-2026.md
**File Modified**: /ganuda/jr_executor/task_executor.py
**Method**: `_extract_steps_via_regex()`

---

## Problem

Jr tasks with SEARCH/REPLACE blocks targeting large files (specialist_council.py, task_executor.py, etc.) would fail with:
```
BLOCKED: Would reduce file from 1108 to 6 lines (>50% loss)
```

The >50% guardrail was doing its job, but the root cause was in the step extraction — not the SR editor itself.

## Root Cause

The `_extract_steps_via_regex()` method had a **collision between two extraction passes**:

1. **Code block scanner** (first pass): Scans for ```python code blocks. When it found a code block with a `File:` header, it created a `type: 'file'` step with `operation: 'write'` — treating the code block content as a FULL FILE REPLACEMENT.

2. **SR block scanner** (second pass): Scanned for `<<<<<<< SEARCH / ======= / >>>>>>> REPLACE` patterns and created proper `type: 'search_replace'` steps.

3. **The collision**: When SR blocks were inside a ```python code fence (as the Jr instruction format specifies), the code block scanner grabbed them FIRST and created a file write step. The write step contained only the REPLACE content (a few lines), not the full file. The guardrail correctly blocked this as >50% content loss.

The SR scanner also found the blocks and created proper SR steps, but the file write step from the code block scanner executed first and failed.

## Fix: SR-FIRST Extraction (Phase 3)

Moved SEARCH/REPLACE block extraction to run BEFORE the code block scanner:

1. **SR blocks extracted first**: All `<<<<<<< SEARCH ... >>>>>>> REPLACE` blocks are parsed and added as `type: 'search_replace'` steps before any code blocks are processed.

2. **SR range tracking**: The character positions of all SR blocks are recorded in `sr_ranges`.

3. **Code block overlap detection**: The code block scanner checks if each code block overlaps with any SR block range. If it does, the code block is **skipped** (it's already been handled as SR steps).

4. **Duplicate removal**: The old SR extraction at the bottom of the method was removed to prevent double-processing.

## Code Changes

In `_extract_steps_via_regex()`:

**Before** (broken order):
```
1. Scan code blocks → creates file write steps (WRONG for SR content)
2. Scan SR blocks → creates search_replace steps (DUPLICATE, runs after write)
```

**After** (SR-FIRST):
```
1. Scan SR blocks FIRST → creates search_replace steps
2. Track SR block positions in sr_ranges
3. Scan code blocks → SKIP any that overlap with sr_ranges
```

## Impact

- Fixes the cascade failure on all 15+ failed tasks (#685, #686, #699, etc.)
- The SearchReplaceEditor module (search_replace_editor.py) was already correct — it applies edits one at a time with backup/validate/rollback
- The guardrail remains in place as a safety net
- Code blocks that do NOT contain SR blocks continue to work as before

## Testing

To verify the fix works, re-queue a previously failed task that used SR blocks on a large file:
```sql
INSERT INTO jr_work_queue (title, instruction_file, priority, status, assigned_jr, use_rlm)
VALUES ('Test SR-FIRST fix on specialist_council.py',
        '/ganuda/docs/jr_instructions/JR-SPECIALIST-PROMPT-ENRICHMENT-FEB10-2026.md',
        3, 'pending', 'Software Engineer Jr.', false)
RETURNING id;
```

Expected: SR blocks extracted as search_replace steps, code blocks containing them skipped, no file write collision.

## Related

- KB-JR-EXECUTOR-SR-LARGE-FILE-FAILURE-PATTERN-FEB11-2026.md (original analysis + recursion proposal)
- KB-JR-INSTRUCTION-FORMAT-REGEX-COMPATIBILITY-FEB08-2026.md (SR format spec)
- search_replace_editor.py (the SR editor module — already correct, not modified)

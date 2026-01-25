# KB: RLM Executor File Creation Fix

**Date:** 2026-01-24
**Author:** TPM (Opus 4.5)
**Category:** Jr Executor Infrastructure
**Status:** Complete

---

## Summary

Fixed the RLM (Recursive Language Model) executor to properly create files during Jr task execution. Two issues were identified and resolved.

---

## Issue 1: use_rlm Field Not Passed to Executor

**Problem:** Tasks with `use_rlm=True` in the database weren't triggering RLM mode because the field wasn't included in the SELECT query.

**File:** `/ganuda/jr_executor/jr_queue_client.py`

**Fix:** Added `use_rlm` to the `get_pending_tasks()` SELECT statement.

```python
# Before
SELECT id, task_id, title, description, priority, sacred_fire_priority,
       instruction_file, instruction_content, parameters,
       seven_gen_impact, tags, created_at
FROM jr_work_queue

# After
SELECT id, task_id, title, description, priority, sacred_fire_priority,
       instruction_file, instruction_content, parameters,
       seven_gen_impact, tags, created_at, use_rlm
FROM jr_work_queue
```

---

## Issue 2: Missing File Extraction Patterns

**Problem:** The RLM executor's pattern matching didn't recognize the LLM's actual output format.

**File:** `/ganuda/lib/rlm_executor.py`

**Old Patterns (4):**
1. `**CREATE FILE: path**` + code block
2. `CREATE FILE: \`path\`` + code block
3. `### /path/file.py` + code block
4. `**/ganuda/path**` + code block

**New Patterns Added (4):**
5. `File: \`path\`` + code block (Qwen/vLLM format)
6. `File: path` (no backticks) + code block
7. `# filepath: path` as first line in code block (fallback)
8. `# /ganuda/path/file.py` as first comment in code block

---

## Key Discovery: RLM Uses Direct Code Execution

Investigation revealed that RLM mode doesn't need pattern extraction at all.

**RLM Execution Flow:**
1. RLM sends task to LLM with `EXECUTION MODEL` prompt
2. LLM generates Python code with `with open(path, 'w')`
3. RLM executes code in local sandbox
4. Files are created **directly on disk** via code execution
5. `FINAL_VAR()` reports results

The pattern extraction in `rlm_executor.py` is only for the **non-RLM path** where the executor tries to extract files from LLM prose responses.

---

## RLM Triggers

Tasks trigger RLM mode when ANY of these conditions are true:
- `use_rlm = True` in task record
- Instruction length > 3000 characters
- Title contains: "implement", "build system", "create api", "authentication", "full stack", "migration", "refactor entire", "redesign"
- More than 3 files mentioned with `Create:` or `Modify:` patterns

---

## Validation

**Test Task:** #294 (RLM-ULTIMATE-001)

**Log Output:**
```
[RLM] Task flagged for recursive execution: RLM Ultimate Test
[RLM] Initializing recursive executor...
[RLM] Executing task with recursive decomposition...
...
Created: /ganuda/tmp/rlm_ultimate.py
```

**Result:** File successfully created at `/ganuda/tmp/rlm_ultimate.py`

---

## Files Modified

1. `/ganuda/jr_executor/jr_queue_client.py` - Added `use_rlm` to SELECT
2. `/ganuda/lib/rlm_executor.py` - Added patterns 5-8 for file extraction

---

## For Seven Generations

Reliable autonomous file creation is essential for air-gapped operation. This fix ensures Jrs can complete complex implementation tasks without TPM intervention.

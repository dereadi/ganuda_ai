# KB Article: RLM Executor File Destruction Incident

**KB ID:** KB-2026-0126-001
**Date:** January 26, 2026
**Author:** TPM via Claude Code
**Category:** Infrastructure / Jr Executor / Post-Incident
**Severity:** P0 - Critical Production Impact

---

## Summary

During VetAssist Sprint 3 testing, the Jr executor's RLM (Recursive Language Model) component **destroyed production files** by overwriting them with LLM-generated stubs. A 261-line React component was replaced with a 30-line stub, and a 419-line page component was similarly truncated.

## Impact

| File | Original Lines | After RLM | Loss |
|------|---------------|-----------|------|
| ReviewStep.tsx | 261 | ~30 | 88% |
| page.tsx | 419 | ~30 | 93% |

Both files required manual restoration from session context.

## Root Cause

### Architecture Flaw

The RLM executor prompt instructs the LLM to "CREATE files using open()" even when the task is to modify an existing file. The RLM library then executes the generated Python code directly:

```python
with open('/path/to/existing/file.tsx', 'w') as f:
    f.write('''stub code here''')
```

The `'w'` mode truncates the file before writing.

### Safeguard Failure

A size-comparison safeguard existed at `rlm_executor.py:358-375`, but it ran **AFTER** the RLM library had already executed the destructive code. The safeguard checked:

```python
if existing_size > new_size * 2 and existing_size > 1000:
    # BLOCK - but too late!
```

By this point, `existing_size` was already the truncated stub size.

### Timeline

1. Jr task dispatched to fix certification checkbox in ReviewStep.tsx
2. TaskExecutor routed task to RLM executor (`_should_use_rlm` returned TRUE)
3. RLM executor built prompt asking LLM to "create" files
4. Qwen 32B generated Python code with `open('w')`
5. RLM library executed the code - **FILE DESTROYED**
6. Post-execution safeguard ran - too late to prevent damage
7. Task marked "complete" despite destroying production code

## Resolution

### Immediate Actions Taken

1. Stopped jr_cli daemon to prevent further damage
2. Manually restored both files from session context
3. Applied checkbox fix manually (was the original task)
4. Created ULTRATHINK analysis document

### JR Instructions Created

| JR | Priority | Title | Status |
|----|----------|-------|--------|
| JR-1 | P0 | Disable RLM for File Modifications | Ready |
| JR-2 | P0 | Add Pre-Execution Safeguard to RLM | Ready |
| JR-3 | P1 | Create Targeted Editor Module | Ready |
| JR-4 | P1 | Wire TargetedEditor into TaskExecutor | Ready |
| JR-5 | P2 | Enhanced Instruction Parser | Ready |

### New Architecture

```
Task with files_to_modify
         │
         ▼
  READ existing file content FIRST
         │
         ▼
  Ask LLM for specific changes only
         │
         ▼
  Create BACKUP before modification
         │
         ▼
  Apply targeted edit (string replace or diff)
         │
         ▼
  Validate syntax (rollback on failure)
         │
         ▼
  Block if file shrinks >50%
```

## Prevention Measures

1. **RLM blocked for modifications** - Will only be used for creating truly new files
2. **Pre-execution safeguard** - Blocks RLM if any modification or existing-file-create detected
3. **TargetedEditor module** - Safe alternative that:
   - Creates backup before any edit
   - Uses string replacement, not full file rewrite
   - Validates syntax after edit
   - Automatic rollback on failure
   - Blocks edits that shrink file by >50%

## Lessons Learned

1. **Post-execution safeguards are insufficient** when the execution itself is destructive
2. **LLM code generation with file write access** must have pre-execution validation
3. **"Modify" and "Create" are fundamentally different operations** - don't use the same code path
4. **Always backup before modification** - restoration should be trivial

## Related Documents

- ULTRATHINK-JR-EXECUTOR-ARCHITECTURE-FIX-JAN26-2026.md
- JR-EXECUTOR-P0-DISABLE-RLM-MODIFICATIONS-JAN26-2026.md
- JR-EXECUTOR-P0-RLM-PRE-EXECUTION-SAFEGUARD-JAN26-2026.md
- JR-EXECUTOR-P1-TARGETED-EDITOR-MODULE-JAN26-2026.md
- JR-EXECUTOR-P1-WIRE-TARGETED-EDITOR-JAN26-2026.md
- JR-EXECUTOR-P2-ENHANCED-INSTRUCTION-PARSER-JAN26-2026.md

## Tags

`jr-executor` `rlm` `file-destruction` `post-incident` `p0` `vetassist`

---

**FOR SEVEN GENERATIONS**

Cherokee AI Federation - Learning from failures to build safer systems.

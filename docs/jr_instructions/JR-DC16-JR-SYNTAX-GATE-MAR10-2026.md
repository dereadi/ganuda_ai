# Jr Instruction: DC-16 Jr Executor File Write Syntax Gate

**Task #:** TBD (will be assigned)
**Title:** DC-16: Jr Executor File Write Syntax Gate
**Date:** March 10, 2026
**Priority:** 1 (DC-16 Fail Loud — Phase 1, prevents silent corruption)

## Context

Last night a Jr wrote markdown fencing (` ```python `) into `fire_guard.py`, corrupting it.
The `_apply_partial_edit` method in `task_executor.py` already has a post-write syntax check
(lines 768-788) that catches this for partial edits. But `safe_file_write` — which handles
regular `write` operations via `_execute_file` — does NOT have the same gate. The write at
lines 2581-2586 happily writes corrupt Python and returns `success: True`.

Fix: Add the same `py_compile` syntax gate to `safe_file_write` so ALL Python file writes
are validated. On failure, restore from the backup that `safe_file_write` already creates
(via `_backup_file`), and return `success: False` with `blocked_by: 'syntax_check'`.

## Task

Add a post-write syntax verification step to `safe_file_write()` in
`/ganuda/jr_executor/task_executor.py`. If the written file is `.py` and fails
`py_compile`, restore the backup and fail the step.

## Steps

File: `/ganuda/jr_executor/task_executor.py`

### Step 1: Add py_compile import at top of file

The file already imports `subprocess` (line 17) which is used by the existing syntax check
in `_apply_partial_edit`. We will use `py_compile` directly instead for cleaner code.
Add the import after the existing stdlib imports.

<<<<<<< SEARCH
import hashlib as _hashlib
=======
import hashlib as _hashlib
import py_compile as _py_compile
>>>>>>> REPLACE

### Step 2: Add syntax gate after the write in safe_file_write

Insert after the successful write block (after `result['written_bytes'] = len(content)`)
but BEFORE the `return result` at line 2590. This catches both APPEND and regular writes.

<<<<<<< SEARCH
            result['success'] = True
            result['written_bytes'] = len(content)
            return result

        except Exception as e:
            result['error'] = f'Write failed: {e}'
            return result
=======
            result['success'] = True
            result['written_bytes'] = len(content)

            # DC-16 Syntax Gate: verify Python files compile after write
            if filepath.endswith('.py'):
                try:
                    _py_compile.compile(filepath, doraise=True)
                    print(f"[SyntaxGate] {filepath} — syntax OK")
                except _py_compile.PyCompileError as pce:
                    print(f"[SyntaxGate] CORRUPTION DETECTED in {filepath}")
                    print(f"[SyntaxGate] Error: {str(pce)[:300]}")
                    # Restore from backup
                    backup_path = result.get('backup')
                    if backup_path and os.path.exists(backup_path):
                        shutil.copy2(backup_path, filepath)
                        print(f"[SyntaxGate] Restored {filepath} from {backup_path}")
                    import logging
                    logging.getLogger("task_executor").warning(
                        "DC-16 SyntaxGate blocked corrupt write to %s: %s",
                        filepath, str(pce)[:200]
                    )
                    result['success'] = False
                    result['error'] = f'Syntax check failed: {str(pce)[:200]}'
                    result['blocked_by'] = 'syntax_check'
                    return result

            return result

        except Exception as e:
            result['error'] = f'Write failed: {e}'
            return result
>>>>>>> REPLACE

## Acceptance Criteria

1. `safe_file_write` returns `success: False` and `blocked_by: 'syntax_check'` when writing
   invalid Python to a `.py` file.
2. The original file is restored from backup after a syntax failure.
3. A WARNING-level log message is emitted with the corruption details.
4. Non-`.py` files (`.md`, `.json`, `.html`, etc.) are unaffected — no syntax check runs.
5. The existing syntax check in `_apply_partial_edit` (line 768) continues to work as before.
6. Test: write intentionally broken Python (e.g., `def foo(\n`) via `safe_file_write` to a
   temp `.py` file and confirm it is rejected and the backup is restored.

## Constraints

- Do NOT modify `_apply_partial_edit` — it already has its own syntax check.
- Do NOT add external dependencies. `py_compile` is stdlib.
- The syntax gate must not slow normal writes by more than ~50ms (py_compile is fast).
- Keep the print format consistent with `[SyntaxGate]` prefix for log grep-ability.
- If no backup exists (new file creation), still fail the write but skip the restore step.

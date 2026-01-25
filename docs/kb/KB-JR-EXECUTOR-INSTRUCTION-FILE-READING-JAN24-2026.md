# KB Article: Jr Executor Instruction File Reading Fix

**KB ID:** KB-JR-EXECUTOR-INSTR-001
**Date:** January 24, 2026
**Category:** Bug Fix / Architecture Enhancement
**Severity:** Critical (blocks Jr task execution)

---

## Problem Statement

Jr tasks referencing instruction files via "See /path/to/instruction.md" pattern fail because the executor doesn't read the referenced files. It only uses the brief task summary as the LLM prompt.

### Example Failure

**Task Content:**
```
CRITICAL: Centralize VetAssist database config. Remove hardcoded credentials from 12 files.
Create /ganuda/vetassist/backend/app/core/database_config.py.
See /ganuda/docs/jr_instructions/JR-VETASSIST-SECURITY-CENTRALIZE-DB-JAN24-2026.md
```

**Result:** LLM receives only the summary, not the detailed 250+ line instruction file. Generates incomplete code with syntax errors.

**Error:** `Code syntax validation failed: Python syntax error: unterminated triple-quoted string literal`

---

## Root Cause Analysis

1. **Task queuing pattern:** TPM creates detailed instruction file, queues task with brief summary + file reference
2. **Executor assumption:** Code expected executor to read referenced instruction files
3. **Actual behavior:** Executor passes task_content directly to LLM without reading referenced files
4. **Result:** Insufficient context leads to incomplete/invalid code generation

---

## Solution

Add instruction file reading to `_execute_code_task()`:

```python
def _read_instruction_file(self, content: str) -> str:
    """
    Read instruction file if referenced in task content.

    Patterns detected:
    - "See /path/to/file.md"
    - "Instruction: /path/to/file.md"
    - "Follow /path/to/file.md"
    """
    import re

    patterns = [
        r'[Ss]ee\s+(/\S+\.md)',
        r'[Ii]nstruction[s]?:\s*(/\S+\.md)',
        r'[Ff]ollow\s+(/\S+\.md)',
        r'[Dd]etails\s+(?:in|at)\s+(/\S+\.md)',
    ]

    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            file_path = match.group(1)
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        instruction_content = f.read()
                    print(f"[{self.agent_id}] Read instruction file: {file_path} ({len(instruction_content)} chars)")
                    return instruction_content
            except Exception as e:
                print(f"[{self.agent_id}] Could not read instruction file {file_path}: {e}")

    return ""
```

Update `_execute_code_task()` to use expanded content:

```python
# At start of _execute_code_task, after getting content:
instruction_content = self._read_instruction_file(content)
if instruction_content:
    content = f"{content}\n\n=== DETAILED INSTRUCTIONS ===\n{instruction_content}"
```

---

## Testing Verification

After fix:
1. VETASSIST-SEC-001 should read `/ganuda/docs/jr_instructions/JR-VETASSIST-SECURITY-CENTRALIZE-DB-JAN24-2026.md`
2. LLM receives full context (~250 lines vs 3 lines)
3. Code generation succeeds with valid syntax

---

## Lessons Learned

1. **Always verify data flow:** When designing task systems, trace the full path from task creation to execution
2. **Log context size:** Add logging to show how much context the LLM receives
3. **Test with real instructions:** Unit tests should use actual instruction file patterns, not simplified mocks
4. **Fail gracefully:** If instruction file can't be read, warn but continue with summary

---

## Related Artifacts

- **Fix commit:** Applied to `/ganuda/jr_executor/jr_task_executor.py`
- **Ultrathink:** `/ganuda/docs/ultrathink/ULTRATHINK-JR-TASK-HYBRID-ARCHITECTURE-JAN24-2026.md`
- **Failed task:** VETASSIST-SEC-001 (reset to open after fix)

---

**FOR SEVEN GENERATIONS** - Systems that read their instructions work better.

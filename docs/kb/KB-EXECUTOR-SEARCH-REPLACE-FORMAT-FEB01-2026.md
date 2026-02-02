# KB: Jr Instruction Format — SEARCH/REPLACE Required for File Edits

**Date:** February 1, 2026
**Author:** TPM (Claude Opus 4.5)
**Category:** Executor Operations
**Severity:** Critical — Incorrect format causes 100% task failure

## Problem

Jr instructions that modify existing files using standard markdown code blocks (```python) will FAIL. The executor treats the code snippet as a full file replacement, which triggers the safety guardrail that blocks >50% file reduction.

5 consecutive tasks (#514-518) failed this way on February 1, 2026.

## Solution: Use SEARCH/REPLACE Format

### For Modifying Existing Files

```markdown
**File:** `/ganuda/path/to/file.py`

<<<<<<< SEARCH
exact old code as it appears in the file
=======
new replacement code
>>>>>>> REPLACE
```

The SEARCH text must:
- Match EXACTLY one location in the file
- Include enough surrounding context to be unique
- Preserve exact indentation/whitespace

### For Creating New Files

```markdown
**Create:** `/ganuda/path/to/new_file.py`

\`\`\`python
full file content here
\`\`\`
```

New files bypass the guardrails because the file doesn't exist yet.

### For Adding to an Existing File (Append)

If you're ADDING new code (not changing existing code), you can use the **Add** verb:

```markdown
**File:** `/ganuda/path/to/file.py`

Add this new function after `existing_function()`:

\`\`\`python
def new_function():
    pass
\`\`\`
```

The executor's mode detection will match "Add this new function after" and use partial_edit mode.

## Why Standard Code Blocks Fail

1. Executor extracts code block → calls `_determine_edit_mode()`
2. Prose patterns don't match → defaults to `mode = 'write'`
3. Step becomes `{operation: 'write', content: <snippet>}`
4. `safe_file_write()` → `validate_file_write()`
5. Guardrail sees snippet is smaller than existing file → BLOCKED

## References

- ULTRATHINK-EXECUTOR-FILE-EDIT-PIPELINE-FEB01-2026
- JR-EXECUTOR-FILE-EDIT-PIPELINE-FIX-FEB01-2026
- SearchReplaceEditor module: `/ganuda/jr_executor/search_replace_editor.py`

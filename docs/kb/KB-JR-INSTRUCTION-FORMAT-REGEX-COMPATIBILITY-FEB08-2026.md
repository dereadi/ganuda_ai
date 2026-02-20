# KB: Jr Instruction File Format — Regex Compatibility Requirements

**Date:** February 8, 2026
**Author:** TPM (Claude Opus 4.6)
**Category:** Jr Executor / Instruction Format / Debugging
**Triggered By:** Tasks #656 and #657 both failing on first execution

## The Problem

Two Jr tasks failed because the instruction files used heading formats that the executor's regex couldn't match:

| Task | Format Used | What Executor Expected |
|------|------------|----------------------|
| #657 (Ritual Engine) | `### File 1: \`/path\`` | `Create \`/path\`` |
| #656 (Council Routing) | Prose + inline code blocks | SEARCH/REPLACE blocks with `File: \`/path\`` |

The executor's `_extract_steps_via_regex()` (task_executor.py:1453) looks for these patterns before code blocks:
- `Create \`path\``
- `**File:** \`path\``
- `File: \`path\``
- `Modify: \`path\``

The heading `### File 1: \`path\`` does NOT match `File: \`path\`` because `File 1:` has `1` between `File` and `:`.

## The Fix

### For NEW file creation (like ritual_review.py):
Use `Create \`/ganuda/path/file.py\`` immediately before the code block:

    Create `/ganuda/scripts/ritual_review.py`

    ```python
    #!/usr/bin/env python3
    ...
    ```

### For EDITING existing files (like specialist_council.py):
Use SEARCH/REPLACE blocks with `File: \`/path\`` preceding:

    File: `/ganuda/lib/specialist_council.py`

    <<<<<<< SEARCH
    [exact text from source file]
    =======
    [replacement text]
    >>>>>>> REPLACE

### For bash/SQL blocks:
These are auto-detected by language hint and executed directly. **WARNING**: Do NOT include bash testing blocks in instruction files — the executor will try to run them immediately, potentially before the files they test have been created. Use indented text (not code fences) for manual testing instructions.

## Task #656 Specific Failure

The LLM fallback tried to regenerate the entire specialist_council.py (1005 lines) but produced only 25 lines. The guardrail correctly blocked this:

    BLOCKED: Would reduce file from 1005 to 25 lines (>50% loss).
    This looks like a replacement, not an edit.

**Fix:** Created v2 instruction file with 4 SEARCH/REPLACE blocks for surgical edits.

## Task #657 Specific Failure

The executor found and executed the `bash` testing block before creating the Python file:

    chmod: cannot access '/ganuda/scripts/ritual_review.py': No such file or directory

**Fix:** Changed headings to `Create \`path\`` format and converted bash testing section to non-executable indented text.

## Rules for All Future Jr Instructions

1. **New files**: `Create \`/ganuda/path/file.ext\`` before code block
2. **Edit existing files**: Use `<<<<<<< SEARCH` / `=======` / `>>>>>>> REPLACE` blocks
3. **File path before SR blocks**: `File: \`/ganuda/path/file.ext\``
4. **No executable bash in testing sections**: Use indented text, not code fences
5. **Keep SEARCH blocks small**: Match only the lines being changed, not the whole file
6. **SEARCH text must be EXACT**: Whitespace, indentation, and line breaks must match the source file precisely

## Related

- task_executor.py:1453 (`_extract_steps_via_regex`)
- task_executor.py:1574 (SEARCH/REPLACE parser)
- KB-JR-EXECUTOR-MOLTBOOK-FAILURES-FEB03-2026.md (previous executor format issues)
- Behavioral pattern: "Jr instructions must be literal" (thermal memory)

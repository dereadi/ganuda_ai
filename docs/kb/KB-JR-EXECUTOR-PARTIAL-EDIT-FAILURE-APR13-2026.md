# KB: Jr Executor Partial Edit Failure Mode

**Created:** April 13, 2026
**Severity:** High — blocks code-heavy Jr tasks
**Affected Tasks:** #1501, #1502, #1503, #1504, #1505

## Problem

The Jr executor's `PartialEdit` system fails on multi-file code modifications when:
1. It can't find the anchor text to insert after (`Could not find anchor 'None'`)
2. It falls back to appending at the end of the file
3. The appended code has wrong indentation relative to the file
4. Syntax check catches it and rolls back via SAGA transaction

## Error Pattern

```
[PartialEdit] Could not find anchor 'None', appending at end
[PartialEdit] Syntax check FAILED, restoring backup
[PartialEdit] Error: Sorry: IndentationError: unindent does not match any outer indentation level (ganuda_agent.py, line 504)
[SAGA] Transaction rolled back
```

## Root Cause

The LLM generating the edit plan produces code blocks without clear file attribution or anchor context. The `SmartExtract` step can't determine which file a code block belongs to or where in the file it should go. The `PartialEdit` step then:
- Uses `None` as anchor (no anchor found)
- Appends at EOF
- Indentation mismatches with surrounding code
- Syntax check catches it

The SAGA rollback works correctly — no files are damaged. But the task fails.

## Retry Behavior

The executor retries 2 times with re-reflection. Each retry hits the same IndentationError because the re-prompted LLM generates the same structural approach.

After 2 retries, the task goes to the Dead Letter Queue (DLQ).

## Workarounds

### 1. Write standalone modules (preferred)
Write new code as NEW FILES (not edits to existing files). The Jr executor handles file creation reliably. Then dispatch a separate atomic task for the 1-2 line integration edits.

### 2. Atomic single-file edits
Break multi-file tasks into one-file-per-task instructions. Each instruction has:
- ONE target file
- EXACT anchor text (copy from the file, not paraphrased)
- EXACT replacement text with correct indentation
- Verification command

### 3. Direct code work
For complex multi-file changes, the TPM writes the code directly. This bypasses the Jr executor entirely but doesn't burn Jr tokens or build the Jr's capability.

## Files Affected Today

| Task | File | Error |
|---|---|---|
| #1503 | ganuda_agent.py (L504) | IndentationError on append |
| #1504 | ganuda_agent.py (L504) | Same — atomic edit still too complex |
| #1501 | Multiple (longhouse repo) | Ran for only 19s — couldn't parse multi-phase |
| #1502 | Multiple (arc_agi_3) | Preflect caught syntax error before execution |
| #1505 | Git operations | Different failure mode — needs investigation |

## Recommendation

The Jr executor needs improvement to the `PartialEdit` system:
1. Require explicit anchor text in all edit plans (never use `None`)
2. When anchor not found, fail fast instead of appending at EOF
3. Add indentation inference from surrounding context
4. Consider using AST-aware editing for Python files instead of text-based editing

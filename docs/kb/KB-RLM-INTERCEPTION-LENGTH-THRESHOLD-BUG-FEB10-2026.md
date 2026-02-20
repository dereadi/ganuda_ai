# KB: RLM Interception Length Threshold Bug

**Date:** February 10, 2026
**Severity:** P1 — causes total task failure for well-documented instructions
**Affected:** task_executor.py `_should_use_rlm()` function
**Status:** Fix queued (JR-EXECUTOR-RLM-THRESHOLD-FIX-FEB10-2026.md)

## Symptom

Jr tasks fail with "No executable steps found in instruction file" even though the instruction file contains valid `Create` directives with properly formatted code blocks that the regex extractor can parse.

## Root Cause

`_should_use_rlm()` at task_executor.py:1302 has three auto-detection conditions. The **length check** (line 1323) triggers for any instruction over 3000 characters:

```python
if len(instructions) > 3000:
    return True
```

When RLM intercepts, it attempts LLM-based task decomposition instead of regex extraction. The RLM decomposer fails to recognize the `Create \`path\`` format and returns zero steps.

**Contributing factor:** The file-counting regex (line 1334) uses `Create:` (with colon) instead of `Create ` (with space), so the file count check never works as a safeguard:

```python
# BUG: Colon instead of space — never matches our instruction format
file_patterns = re.findall(r'(?:Create|Modify|Update):\s*[`/][^\s`]+', instructions)
```

## Impact

Any instruction exceeding 3000 characters — which includes most well-documented tasks with Background sections, Design Decisions, and Acceptance Criteria — is silently routed to RLM and fails. This affected:

- **#670 / #674**: Ritual Engine Timer (8013 chars, 2 files) — "No executable steps"
- **#669 / #675**: Lens Calibration (also over 3000 chars) — RLM partial execution caused EOF corruption in speed_detector.py

## Workaround

Set `use_rlm` to `false` explicitly when queueing tasks:

```sql
INSERT INTO jr_work_queue (title, instruction_file, ..., use_rlm)
VALUES ('...', '...', ..., false);
```

## Fix

JR-EXECUTOR-RLM-THRESHOLD-FIX-FEB10-2026.md removes the standalone length check and replaces it with a combined condition: only trigger RLM when instructions exceed 8000 chars AND reference more than 3 files. The file-counting regex is also corrected to match the KB-defined `Create \`path\`` format.

## Lessons

1. **Length is a poor proxy for complexity.** A 6000-char instruction creating 2 files is simpler than a 2000-char instruction creating 8 files.
2. **Auto-detection should be conservative.** False positives (unnecessary RLM) cause total failure. False negatives (missing RLM) just mean slightly less optimal execution.
3. **Test regexes against real instruction files**, not theoretical patterns.

---
*Cherokee AI Federation — Knowledge Base*
*For Seven Generations*

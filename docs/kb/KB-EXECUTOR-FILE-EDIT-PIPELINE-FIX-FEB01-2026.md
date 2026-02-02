# KB: Jr Executor File-Edit Pipeline Fix — February 1, 2026

**Date:** February 1, 2026
**Author:** TPM (Claude Opus 4.5)
**Category:** Executor Operations / Bug Fix
**Severity:** P0 — 100% file-edit failure rate
**Files Modified:** `/ganuda/jr_executor/task_executor.py`

## Incident

5 consecutive Jr tasks (#514-518) failed on February 1, 2026. All failures were in file-edit operations. The executor has three file-edit subsystems that weren't coordinating:

| Subsystem | Location | Purpose |
|-----------|----------|---------|
| Partial Edit | `_apply_partial_edit()` line 450 | Insert/append code to existing files |
| Safe File Write | `safe_file_write()` line 2110 | Full file write with guardrails |
| SearchReplaceEditor | `search_replace_editor.py` | Exact-match search and replace |

## Root Causes

### 1. Mode Detection Too Narrow (CRITICAL)
`_determine_edit_mode()` at line 361 only matched phrases like "add this new method" or "add new function". Real Jr instructions say things like "Find the VA_SCOPES list and add..." or "Change the ML crisis detection from primary to advisory" — none matched. Default: `mode = 'write'` (full file replacement).

### 2. Guardrails Block Snippet Writes (CRITICAL)
`validate_file_write()` at line 2062 blocks writes that reduce a file by >50% lines. When a snippet (17 lines) is written as a full replacement for a large file (456 lines), the guardrail correctly blocks it. But the snippet should never have been treated as a full replacement.

### 3. False Positive Idempotency
`_apply_partial_edit()` at line 478 used a 3-line fingerprint (first 3 non-blank, non-comment lines). Common patterns like `import logging`, `from app.core.config import settings` triggered false matches, causing legitimate inserts to be skipped.

### 4. Retry Re-Applies All Steps
`_retry_with_reflection()` at line 1184 re-extracts and re-executes ALL steps on retry, including ones that already succeeded (e.g., task #517 created HelpTip.tsx successfully, then retry tried to create it again).

## Fixes Applied (Direct — Chicken-and-Egg)

The executor can't fix itself via Jr queue, so these were applied directly by the TPM.

### Fix 1: Broadened Mode Detection (line 361)

Added patterns BEFORE the existing narrow ones:

```python
# "Add X to the list/scopes" → insert_after
add_to_match = re.search(r'add\s+[`\'"]?[\w._]+[`\'"]?\s+to\s+', text)

# "Find X and replace/change/update" → insert_after (find_and_modify)
find_and_match = re.search(r'(?:find|locate|look\s+for)\s+.*?\s+(?:and|then)\s+(?:replace|change|update|add|modify)', text)

# "Change X to Y" / "Replace X with Y" → insert_after (replace)
change_match = re.search(r'(?:change|replace|update|swap|switch)\s+.*?\s+(?:to|with|from)', text)

# Broadened the existing add_match to include: endpoint, route, import, scope, button, component
```

### Fix 2: Improved Idempotency Fingerprinting (line 478)

- Increased from 3 to 5 required fingerprint lines
- Added boilerplate exclusion list: `import `, `from `, `logger`, `logging`, `return`, `pass`, `def __init__`
- If fewer than 5 significant lines available, skip the idempotency check entirely (log it)

### Fix 3: Step Completion Tracking in Retries (line 1184)

- Added `previous_result` parameter to `_retry_with_reflection()`
- On retry, collects paths from previously-succeeded steps into `completed_paths` set
- Skips steps targeting already-completed paths
- If all steps already completed, returns success immediately

## Verification

```bash
cd /ganuda/jr_executor && python3 -c "import py_compile; py_compile.compile('task_executor.py', doraise=True); print('SYNTAX OK')"
```

Result: `SYNTAX OK`

## Lesson Learned

**Jr instructions for file MODIFICATIONS should use SEARCH/REPLACE format**, not standard markdown code blocks. The executor already has full support for `<<<<<<< SEARCH / ======= / >>>>>>> REPLACE` blocks (lines 1517-1556 in task_executor.py), routing them through `SearchReplaceEditor` which has its own safety (unique match, backup, syntax validation, rollback). This path bypasses the problematic write guardrails entirely.

See: `KB-EXECUTOR-SEARCH-REPLACE-FORMAT-FEB01-2026.md`

## Prevention

1. All future Jr instructions for file edits MUST use SEARCH/REPLACE format
2. New file creation continues to use standard `**Create:** \`path\`` + code block format
3. The mode detection broadening serves as a safety net for instructions that don't use SEARCH/REPLACE
4. The ultrathink document has the full analysis: `ULTRATHINK-EXECUTOR-FILE-EDIT-PIPELINE-FEB01-2026.md`

## References

- ULTRATHINK-EXECUTOR-FILE-EDIT-PIPELINE-FEB01-2026
- JR-EXECUTOR-FILE-EDIT-PIPELINE-FIX-FEB01-2026
- KB-EXECUTOR-SEARCH-REPLACE-FORMAT-FEB01-2026
- KB-JR-EXECUTOR-EDIT-CAPABILITY-GAP-JAN29-2026 (prior related finding)
- Council Vote b75dced893145a4c (Hybrid Smart Extraction)
- Council Vote 6428bcda34efc7f9 (Self-Healing Retry)

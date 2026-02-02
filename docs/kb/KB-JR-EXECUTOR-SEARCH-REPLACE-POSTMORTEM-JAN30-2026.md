# KB: Jr Executor SEARCH/REPLACE Postmortem

**Date:** January 30, 2026
**Author:** TPM (Claude Opus 4.5)
**Severity:** P1 — Silent data corruption (duplicate content injected into production files)
**Status:** Resolved

## Incident Summary

Five VA Account Linking Jr tasks (#498-#502) using the new SEARCH/REPLACE editing mechanism all reported "failed" despite the first edit in each task landing on disk. The executor's retry mechanism then re-applied the same additive edits multiple times, injecting duplicate content into `user.py` (6 copies of a column block) and `schemas/auth.py` (9 copies of a class definition).

## Timeline

| Time | Event |
|------|-------|
| ~21:00 | 5 VA Linking tasks queued with SEARCH/REPLACE instruction format |
| ~21:05 | First run: all 5 "completed" but edits were silently skipped (stale workers had pre-SR code) |
| ~21:15 | Root cause #1 identified — workers started Jan 28-29 had old `task_executor.py` in memory |
| ~21:20 | Workers killed and restarted with fresh code |
| ~21:22 | Tasks reset to pending, picked up by fresh workers |
| ~21:25 | Tasks #498 and #499 fail with "1 step(s) failed" |
| ~21:30 | Root cause #2 identified — audit function argument mismatch crashes after edit succeeds |
| ~21:35 | Root cause #3 — executor stops on first step failure; subsequent SEARCH/REPLACE blocks never run |
| ~21:40 | Root cause #4 — retry mechanism re-applies ALL steps, causing additive duplicate content |
| ~21:45 | Emergency: workers killed, audit bug fixed, duplicates manually cleaned, all edits manually applied |
| ~21:50 | Workers restarted with fixed code; tasks marked completed |

## Root Causes

### RC1: Stale Worker Code (Pre-deployment)

Workers are long-running Python processes that import `task_executor.py` at startup. Code changes to the executor require a worker restart. The SEARCH/REPLACE parser (`_execute_search_replace` method) was deployed to `task_executor.py` but workers started 2 days earlier were still running the old code.

**Impact:** SEARCH/REPLACE blocks in Jr instructions were silently ignored. Only bash commands executed.

**Fix:** Kill and restart workers after any `task_executor.py` change.

**Prevention:** Add a code-version check at startup — workers should log the file mtime of `task_executor.py` and optionally auto-exit if the file changes (external watchdog or self-check on each poll cycle).

### RC2: Audit Function Argument Mismatch

The `_execute_search_replace` method called `_audit_file_operation()` with the wrong argument count and order:

```python
# BROKEN (3 args, wrong order):
self._audit_file_operation(filepath, "search_replace", f"success={result['success']}")

# CORRECT signature requires 4 positional args:
def _audit_file_operation(self, operation: str, path: str, size: int, backup_path: str)
```

The `SearchReplaceEditor.apply_search_replace()` successfully modified the file on disk. Then the audit call crashed with a TypeError. The outer `except` clause caught it and returned `{"success": False}`, masking the successful edit.

**Impact:** Steps reported failure despite edits landing on disk. This triggered retry behavior.

**Fix:**
1. Corrected argument order: `("search_replace", filepath, result.get('lines_changed', 0), result.get('backup_path', ''))`
2. Wrapped audit call in its own try/except so audit failures never mask edit success:

```python
try:
    if hasattr(self, "_audit_file_operation"):
        self._audit_file_operation(
            "search_replace", filepath,
            result.get('lines_changed', 0), result.get('backup_path', '')
        )
except Exception:
    pass  # Audit failure must not mask edit success
```

### RC3: Stop-on-First-Failure Execution Model

The executor processes steps sequentially and stops when any step fails. For multi-step SEARCH/REPLACE instructions (e.g., Phase 2 had 3 SEARCH/REPLACE blocks targeting different files), only the first block executed. The remaining blocks were never attempted.

**Impact:** Partial application of multi-step instructions. Files that depended on earlier edits were left untouched.

**Not fixed in this incident.** Changing execution semantics mid-sprint was too risky.

**Future consideration:** Add a `continue_on_failure` option per task or per step type. SEARCH/REPLACE edits targeting different files are independent and should not block each other.

### RC4: Retry Mechanism Re-applies ALL Steps

When a task fails, the executor retries it (up to 2 retries). On each retry, it re-extracts ALL steps from the instruction and re-applies them from the beginning. For additive edits (adding new code blocks), the SEARCH text still matches in the file, so the edit applies again — creating duplicate content.

**Impact:**
- `user.py`: 6 copies of the `va_icn` / `va_linked_at` column block
- `schemas/auth.py`: 9 copies of the `VALinkRequest` class

**Not fixed in this incident.**

**Future fixes (prioritized):**
1. **Idempotency check:** Before applying a SEARCH/REPLACE, verify the REPLACE text isn't already present at the target location
2. **Step-level retry tracking:** Track which steps succeeded and only retry failed steps
3. **Checksum guard:** Hash file content before/after each step; skip step if file already matches expected post-state

## Affected Files

| File | Damage | Repair |
|------|--------|--------|
| `app/models/user.py` | 6 duplicate va_icn blocks | Manually removed 5 duplicates, applied remaining edits |
| `app/schemas/auth.py` | 9 duplicate VALinkRequest classes | Manually removed 8 duplicates, added missing fields |
| `task_executor.py` | Audit bug at line ~1627 | Fixed argument order + try/except wrapper |

## Lessons Learned

1. **Worker restart protocol is mandatory** after any change to `task_executor.py`, `jr_queue_worker.py`, or any imported module. Add this to the deployment checklist.

2. **Audit/logging code must never mask operational success.** Wrap all post-operation instrumentation in isolated try/except blocks.

3. **SEARCH/REPLACE edits are not idempotent by default.** Additive edits (inserting new code after an anchor point) will re-apply on retry. The editor needs a pre-check: "does the REPLACE text already exist at this location?"

4. **Multi-step instructions need independent step execution.** The stop-on-first-failure model is appropriate for sequential bash commands but wrong for independent file edits targeting different files.

5. **The TPM should verify one task fully before approving batch execution.** Running all 5 phases simultaneously amplified the damage from a single bug.

## Action Items

| # | Item | Owner | Priority |
|---|------|-------|----------|
| 1 | Add idempotency check to SearchReplaceEditor | Software Engineer Jr | P1 |
| 2 | Add worker auto-reload or version check | Infrastructure Jr | P2 |
| 3 | Add `continue_on_failure` option for independent steps | Software Engineer Jr | P2 |
| 4 | Add step-level retry tracking (skip succeeded steps on retry) | Software Engineer Jr | P2 |
| 5 | Add worker restart to deployment checklist | TPM | P0 (done) |
| 6 | Integration test: multi-step SEARCH/REPLACE instruction | Software Engineer Jr | P1 |

# KB: Jr Executor — RLM Retry Failure Pattern

**Date:** 2026-02-04
**Discovered by:** TPM (Claude Opus 4.5)
**Severity:** Medium — causes task retry failures, does not cause data loss
**Status:** Documented, workaround identified

## Summary

When a Jr task partially completes (e.g., 22/23 steps succeed, 1 final bash step fails), the task is marked `failed`. If the task is reset to `pending` for retry, the RLM safety guard in `rlm_executor.py` blocks all file write steps because the files already exist from the first successful run. This causes the retry to fail on step 1, creating a worse outcome than the original partial success.

## Root Cause

The RLM executor (`/ganuda/lib/rlm_executor.py`, lines 568-619) has two safety gates:

### Gate 1: Size Reduction Block (line 574)
```python
if existing_size > new_size * 2 and existing_size > 1000:
    # BLOCKED: Would overwrite larger file with smaller content
```
When SmartExtract re-parses the instruction markdown, it may extract code blocks at slightly different sizes than the original write. If the existing file (from run 1) is >2x the size of the re-extracted content, the write is blocked.

### Gate 2: Import Overlap Check (line 604)
```python
if overlap_ratio < 0.2 and len(existing_imports) >= 3:
    # BLOCKED: Import mismatch suggests hallucinated replacement
```
On retry, the re-extracted code may have different import patterns than what was written in run 1, triggering the framework mismatch guard.

### The Cascade
1. Jr task runs: 22/23 file writes succeed, final bash verification fails
2. Task marked `failed`, all 22 files exist on disk
3. Task reset to `pending` for retry
4. Queue worker picks up task, SmartExtract re-parses instruction
5. Executor attempts to re-write all 22 files
6. RLM blocks most/all writes (files already exist, size mismatch)
7. Blocked writes counted as failures → task fails again
8. Worse: Each attempt creates `.backup_*` files (75 backups created in one session)

## Evidence

From `journalctl -u jr-queue-worker`:
```
[REFLECT] Analysis: The task was blocked due to a significant reduction
in the file content from 19 to 9 lines
[REFLECT] Analysis: The task was blocked because the proposed action
would significantly reduce the content of the file
[RETRY] Attempt 2 failed: 1 step(s)
[M-GRPO] Recorded: direct_code -> FAIL
```

### Impact on 2026-02-04 Session
- 10 scaffold tasks queued (#569-578)
- 2 completed on first run (#573, #577)
- 8 partially completed (80-96% of steps)
- Reset to pending → all 8 failed again on retry
- 75 `.backup_*` files created in `/ganuda/assist/`
- M-GRPO recorded 8 FAIL events (polluting learning signal)

## Workaround

**Gap-Fill Pattern**: Instead of retrying the full instruction, write new Jr instructions that target ONLY the missing files. Since these files don't exist yet, the RLM guard won't trigger.

Steps:
1. Audit what files were actually created by the partial run
2. Compare against the plan to identify gaps
3. Mark original tasks as `completed` (partial) to prevent further retries
4. Write gap-fill instructions covering only missing files
5. Queue gap-fill instructions as new tasks

## Recommended Fixes

### Short-term: Idempotent Write Mode
Add a `--force` or `idempotent` flag to the executor that:
- Skips files that already exist AND match expected content (hash comparison)
- Only writes files that are missing or have different content
- Does NOT trigger on retry if content matches

### Medium-term: Step-Level Retry
Instead of retrying the entire task:
- Track which specific steps succeeded/failed
- On retry, skip completed steps and only execute failed ones
- Store step completion state in `jr_work_queue.progress_data` JSONB

### Long-term: M-GRPO Signal Correction
- Don't record FAIL for tasks where the failure was caused by RLM blocking
- Distinguish between "Jr wrote bad code" (real failure) and "safety guard triggered on retry" (infrastructure issue)
- Add a `failure_type` field: `jr_error`, `rlm_block`, `dependency_error`, `shell_compat`

## Additional Failure Modes Discovered

### Shell Compatibility (#572)
`set -o pipefail` is not supported in `/bin/sh` (Debian dash). Generator scripts that use bash features must specify `#!/bin/bash` explicitly.

### Dependency Resolution (#575)
`pip install docling` has heavy dependencies that may fail on constrained systems. Jrs should use `--no-deps` and manually specify required packages.

### Git Clone (#578)
Git clone operations in Jr bash steps may fail due to network configuration, SSH key issues, or proxy settings on the executor node.

### LEARNING System Bug
```
[LEARNING] Failed to record: 'NoneType' object has no attribute 'encode'
```
The hive learning system has a bug where it can't encode None values when recording task outcomes.

## Related KB Articles
- KB-JR-EXECUTOR-P0-FIXES-JAN27-2026
- KB-JR-EXECUTOR-EDIT-CAPABILITY-GAP-JAN29-2026
- KB-RLM-EXECUTOR-FILE-DESTRUCTION-INCIDENT-JAN26-2026

## Seven Generations Impact
This pattern will recur every time a multi-step Jr task partially fails. The gap-fill workaround is labor-intensive. Implementing step-level retry would eliminate the need for manual gap-fill instructions and improve Jr task completion rates across the federation.

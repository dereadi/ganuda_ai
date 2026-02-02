# KB: Cascade Fixer -- Drift Detection Pipeline Bugs & Fixes

**Date:** February 2, 2026
**Author:** TPM (Claude Opus 4.5)
**Pipeline:** Drift Detection (Phases 1A through 3B)
**Status:** Resolved -- all blockers cleared, pipeline operational

---

## Summary

During the deployment of the Drift Detection pipeline on February 2, 2026, five bugs were discovered that blocked or degraded execution. Three were P0 blockers, one was P1, and one was a critical production file destruction. This article documents each bug, its root cause, the fix applied, and recommendations to prevent recurrence.

A new operational pattern -- the "cascade fixer" -- was developed and validated during this incident to handle waterfall unblocking of dependent tasks.

---

## Bug 1: Executor Cannot Execute SEARCH/REPLACE Blocks

**Severity:** Architectural limitation
**Impact:** All Jr instructions containing file edits fail silently. The executor skips SEARCH/REPLACE blocks and only executes `sql` and `bash` code blocks.

**Root cause:** The task executor (`/ganuda/jr_executor/task_executor.py`) parses instruction markdown and extracts steps by code block type. The SEARCH/REPLACE format (`<<<<<<< SEARCH` / `=======` / `>>>>>>> REPLACE`) is not recognized as an executable step type. Steps using this format are silently dropped during parsing.

**Resolution:** TPM applies file edits directly. Jr instructions were rewritten to contain only `sql` and `bash` blocks. New file creation uses bash heredoc (`cat > file << 'EOF'`).

**Recommendation:** The executor needs a file-edit step type. This was previously documented in `KB-JR-EXECUTOR-EDIT-CAPABILITY-GAP-JAN29-2026.md`. Until resolved, all Jr instructions must avoid SEARCH/REPLACE and use only `sql` and `bash` blocks.

---

## Bug 2: PostgreSQL `::bytea` Cast Fails on Multi-Byte Content

**Severity:** P0 -- blocked entire drift detection pipeline
**Impact:** Phase 1A SQL migration rolled back completely because `encode(sha256(original_content::bytea), 'hex')` failed on thermal memories containing non-ASCII characters.

**Root cause:** Direct `::bytea` cast treats the string as raw bytes without encoding awareness. Some thermal memory content contains UTF-8 multi-byte characters (emojis, non-English text) that break this cast.

**Fix:** Replace `original_content::bytea` with `convert_to(original_content, 'UTF8')` in all SQL statements. Verified working on all 60,542 memories.

**Files affected:**
- Phase 1A migration SQL
- Phase 1B validation SQL
- Phase 3A sanctuary daemon SQL
- Phase 3B governance agent SQL

**Before (broken):**
```sql
encode(sha256(original_content::bytea), 'hex')
```

**After (fixed):**
```sql
encode(sha256(convert_to(original_content, 'UTF8')), 'hex')
```

---

## Bug 3: research_worker.py -- Module-Level `continue` Statement

**Severity:** P0 -- blocked any task that validates research_worker.py
**Impact:** `SyntaxError: 'continue' not properly in loop` at line 23. File would not compile.

**Root cause:** A previous Jr task (likely an attempt at adding sanctuary pause functionality) injected a pause flag check at module level with a `continue` statement. `continue` is only valid inside `for`/`while` loops, not at module level.

**Code injected:**
```python
# Check sanctuary pause flag
if os.path.exists('/tmp/research_worker_paused'):
    logging.info("Research worker paused for sanctuary state -- waiting 30s")
    time.sleep(30)
    continue  # <-- INVALID at module level
```

**Fix:** Removed the block entirely. The sanctuary state daemon uses file-based pause flags checked inside each service's polling loop, not at module level.

---

## Bug 4: research_worker.py -- Dead Stub Function After __main__

**Severity:** P1 -- caused compilation failure
**Impact:** `SyntaxError: invalid syntax` at `def notify_vetassist(...)`. The `...` (Ellipsis) is not valid as a function parameter.

**Root cause:** A previous Jr task left an incomplete stub function after the `if __name__ == "__main__": main()` block. The function used Python Ellipsis literal as a parameter placeholder, which is syntactically invalid.

**Code:**
```python
def notify_vetassist(...):  # <-- Ellipsis is not a valid parameter
    if USE_VETASSIST_CONFIG:
        conn = get_non_pii_connection()
    else:
        conn = get_conn()
    # ... rest of function ...
```

**Fix:** Removed the dead stub entirely along with its associated import block.

---

## Bug 5: rlm_bootstrap.py Overwritten by Staleness Scorer

**Severity:** CRITICAL -- production file destroyed
**Impact:** `/ganuda/lib/rlm_bootstrap.py` (the RLM thermal memory bootstrap module used for TPM session continuity) was completely overwritten with the staleness scorer daemon code. The `ThermalBootstrap` class, `get_recent_memories()`, `generate_bootstrap_context()` and all other methods were destroyed.

**Root cause:** Phase 2A Jr instruction told the Jr to create `/ganuda/daemons/staleness_scorer.py`. The executor created the file at the wrong path, writing it to `rlm_bootstrap.py` instead. The executor's `rlm_protected_paths.yaml` configuration exists but was not enforced, or the Jr routed the file write incorrectly. Ten backup files were created (`.backup_20260202_*`) but all contain the staleness scorer code, not the original.

**Fix:** Restored from the original Jr instruction source in `JR-RLM-THERMAL-BOOTSTRAP-FIXED-JAN21-2026.md`. Applied the Phase 2A staleness filter modification (`AND COALESCE(staleness_flagged, false) = false`) during restoration.

**Recommendation:** This is the same file destruction pattern documented in `KB-RLM-EXECUTOR-FILE-DESTRUCTION-INCIDENT-JAN26-2026.md`. The executor's backup-before-write creates backups AFTER the damage occurs, making them useless for recovery. Pre-write verification must be added to the executor. Specifically:
1. Before any file write, hash the existing file and compare against known good checksums.
2. If the target path is in `rlm_protected_paths.yaml`, refuse the write and fail the task.
3. Backup must capture the ORIGINAL content, not the content being written.

---

## Cascade Fixer Pattern

A "cascade fixer" Jr instruction was developed during this incident to handle waterfall unblocking of dependent pipeline tasks.

### How It Works

1. **Fix root blockers** -- TPM applies file edits directly; executor runs corrected SQL.
2. **Re-queue downstream tasks** -- SQL UPDATE sets blocked tasks back to `queued` status.
3. **Priority ordering** -- Creates natural execution waterfall so tasks run in dependency order.

### Validated Execution

- Task #536 (cascade fixer) fixed Phase 1A migration --> succeeded
- Tasks #531-535 re-queued in priority order --> waterfall continues

### Formalization Recommendation

The cascade fixer pattern should be formalized as a standard operating procedure for future pipeline unblocking operations. A template Jr instruction should be created that:
- Accepts a list of blocked task IDs
- Applies root-cause fixes (SQL corrections, file repairs)
- Re-queues downstream tasks with correct priority ordering
- Includes validation queries to confirm the cascade completed

---

## Files Modified by TPM (Direct Intervention)

| File | Change | Bug Fixed |
|------|--------|-----------|
| `/ganuda/services/research_worker.py` | Removed module-level `continue` + dead stub | Bugs 3, 4 |
| `/ganuda/lib/rlm_bootstrap.py` | Restored from Jr instruction source + applied staleness filter | Bug 5 |
| `/ganuda/telegram_bot/thermal_memory_methods.py` | Added SHA-256 checksum to `seed_memory()` | Phase 1B edit |
| `/ganuda/services/research_worker.py` | Added SHA-256 checksum to `store_in_thermal_memory()` | Phase 1B edit |
| `/ganuda/lib/vlm_relationship_storer.py` | Added SHA-256 checksum to `store_entity_as_memory()` | Phase 1B edit |
| `/ganuda/lib/specialist_council.py` | Added circuit breaker integration to `vote()` | Phase 2B edit |
| `/ganuda/jr_executor/jr_queue_worker.py` | Added sanctuary pause flag check to polling loop | Phase 3A edit |

---

## Related KB Articles

- `KB-JR-EXECUTOR-EDIT-CAPABILITY-GAP-JAN29-2026.md` -- Executor lacks SEARCH/REPLACE support (Bug 1)
- `KB-RLM-EXECUTOR-FILE-DESTRUCTION-INCIDENT-JAN26-2026.md` -- Same file destruction pattern (Bug 5)
- `KB-JR-EXECUTOR-P0-FIXES-JAN27-2026.md` -- Previous executor reliability fixes

---

## Lessons Learned

1. **Never trust `::bytea` with user-generated content.** Always use `convert_to(content, 'UTF8')` for PostgreSQL SHA-256 hashing.
2. **Module-level code injections are dangerous.** Jr tasks that modify service files must be validated for syntactic correctness before deployment.
3. **Backup-after-write is useless for recovery.** The executor must capture the original file content before overwriting, not after.
4. **The cascade fixer pattern works.** When a pipeline has sequential dependencies, fixing the root blocker and re-queuing downstream tasks creates efficient waterfall recovery.
5. **Jr instructions must use only `sql` and `bash` blocks.** Until the executor gains file-edit capability, SEARCH/REPLACE blocks will be silently dropped.

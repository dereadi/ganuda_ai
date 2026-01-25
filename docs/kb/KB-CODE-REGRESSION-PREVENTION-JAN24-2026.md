# KB Article: Code Regression Prevention in Jr Executor

**KB ID:** KB-CODE-REGRESSION-JAN24-2026
**Date:** January 24, 2026
**Severity:** CRITICAL
**Category:** Infrastructure / Jr Executor

---

## Incident Summary

On January 24, 2026, the Jr executor overwrote `/ganuda/lib/specialist_council.py` v1.3 (36KB) with an older v1.2 version (18KB), causing loss of 18KB of working code.

**Root Cause:** When modifying existing files, the LLM generated a complete file replacement instead of targeted edits.

**Impact:** Lost functions, classes, and features that had been developed over multiple iterations.

---

## Lessons Learned

### 1. Full File Generation is Dangerous for Existing Files

When an LLM is asked to "add feature X to file Y", it may regenerate the entire file from memory, which can:
- Lose code that wasn't in training data
- Revert to older versions the model has seen
- Drop functions/classes the model considers "unnecessary"

### 2. SEARCH/REPLACE is Safer

Instead of full file generation, use targeted SEARCH/REPLACE blocks:
```
<<<<<<< SEARCH
[exact code to find]
=======
[code to replace with]
>>>>>>> REPLACE
```

### 3. Validation Guards Prevent Damage

Before applying any file modification, check:
- Size reduction >20% = REJECT
- Lost functions/classes = REJECT
- Version downgrade = REJECT

---

## Prevention Measures Implemented

### 1. Safe Edit Mode (SAFE-EDIT-001)

**File:** `/ganuda/jr_executor/safe_edit.py`
**Instruction:** `/ganuda/docs/jr_instructions/JR-SAFE-EDIT-MODE-JAN24-2026.md`
**Status:** Queued for implementation (Task #275)

**Key Features:**
- Detects existing files and switches to SEARCH/REPLACE mode
- Parses and applies targeted edit blocks
- Validates modifications before writing
- Logs failures to thermal memory for learning

### 2. Research Foundation

Council-approved research papers informing the solution:
- **Reflection-Driven Control** (arXiv:2512.21354) - Self-reflection as explicit reasoning step
- **Verifiably Safe Tool Use** (arXiv:2601.08012) - Tool-level guardrails
- **Repository Memory** (arXiv:2510.01003) - Long-term code history awareness

### 3. Backup Protocol

Before any file modification:
1. Check if file exists
2. If yes, create backup: `{filename}.backup-{timestamp}`
3. Use SEARCH/REPLACE mode
4. Validate before writing
5. Keep backup for 7 days

---

## Recovery Steps (When Regression Occurs)

1. **Check for backups:**
   ```bash
   ls -la /ganuda/lib/*.backup* /ganuda/lib/*.original
   ```

2. **Restore from backup:**
   ```bash
   cp /ganuda/lib/specialist_council.py.original /ganuda/lib/specialist_council.py
   ```

3. **Verify restoration:**
   ```bash
   wc -l /ganuda/lib/specialist_council.py  # Should match original
   grep "def " /ganuda/lib/specialist_council.py | wc -l  # Function count
   ```

4. **Log incident to thermal memory:**
   ```sql
   INSERT INTO thermal_memory_archive (source, memory_type, content, temperature)
   VALUES ('jr-executor', 'regression_incident', '...', 0.9);
   ```

---

## Cherokee Principle Applied

**Seven Generations:** Don't break what previous generations built.

The safe edit mode ensures that when we improve code, we don't accidentally destroy the work that came before. Each generation builds on the last.

---

## Related Documents

- Research: `/ganuda/docs/research/RESEARCH-SAFE-CODE-MODIFICATION-JAN24-2026.md`
- Jr Instruction: `/ganuda/docs/jr_instructions/JR-SAFE-EDIT-MODE-JAN24-2026.md`
- Original incident: specialist_council.py v1.3 → v1.2 regression

---

## Tags

`#regression` `#safe-edit` `#jr-executor` `#seven-generations` `#P0`

---

**Wado to the ancestors who teach us to build on what came before, not destroy it.**

# KB Article: Smart Extraction Phase 2 - Partial Code Edits

**KB ID:** KB-SMART-EXTRACTION-PHASE2-JAN28-2026
**Category:** Feature Enhancement
**Severity:** P1 - Enables autonomous Jr partial edits
**Author:** Claude Opus (TPM)
**Council Vote:** b75dced893145a4c (84.3% confidence)

---

## Summary

Phase 2 of Hybrid Smart Extraction adds support for partial code edits, enabling Jrs to apply code fragments (add imports, insert methods, modify functions) without overwriting entire files.

---

## Edit Modes Implemented

| Mode | Trigger Pattern | Action |
|------|-----------------|--------|
| `insert_top` | "Add import", "at the top of the file", "after existing imports" | Insert near top of file, after imports section |
| `append` | "Add this method", "Add new method" | Append at end of file |
| `insert_after` | "Add after X", "around line N" | Insert after specified anchor or line |
| `replace_method` | "Modify X method", "Update X" + `def X()` in code | Replace entire method with new version |
| `write` | No partial pattern detected | Full file write (Phase 1 behavior) |

---

## Key Features

### 1. Position Tracking
Changed from `re.findall()` to `re.finditer()` to get accurate positions for each code block's preceding prose.

### 2. Indentation Preservation
For partial edits, raw content (with leading indentation) is preserved instead of `strip()` which broke class method indentation.

### 3. Idempotency Check
Insert/append modes skip if content fingerprint (first 3 non-blank non-comment lines) already exists in file. Prevents duplicate insertions on retry.

### 4. Syntax Validation
Python files run `py_compile` after edit. If syntax check fails, backup is restored automatically.

### 5. Method Range Detection
`_find_method_range()` locates start/end of methods by parsing indentation and looking for next `def`/`class` at same or lower indent level.

---

## Files Modified

| File | Change |
|------|--------|
| `/ganuda/jr_executor/task_executor.py` | Added `_determine_edit_mode()`, `_apply_partial_edit()`, `_find_method_range()`, `_find_import_end()`, `_find_insert_position()` |

---

## Verification

Task #398 successfully:
- Skipped already-present imports (idempotency)
- Replaced `__init__` method with MAGRPO-enabled version (493 → 479 lines)
- Passed syntax check
- 9/10 steps successful (1 bash test failed due to external deps)

---

## Safety Constraints

1. **Backup always**: Creates `.bak` before any edit
2. **Syntax check**: Python files validated after edit
3. **Rollback on failure**: Backup restored if syntax check fails
4. **Idempotency**: Duplicate insertions prevented on retry

---

## Known Limitations

1. **Multi-method replace not supported**: Each code block targets one method
2. **Line hints are fuzzy**: "around line X" searches ±20 lines for anchor
3. **Complex merges may fail**: Very tangled code may need manual review

---

## Related Documents

- `/ganuda/docs/ultrathink/ULTRATHINK-SMART-EXTRACTION-PHASE2-PARTIAL-EDITS-JAN28-2026.md`
- `/ganuda/docs/jr_instructions/JR-SMART-EXTRACTION-PHASE2-PARTIAL-EDITS-JAN28-2026.md`
- `/ganuda/docs/kb/KB-JR-EXECUTOR-P0-FIXES-JAN27-2026.md` (Phase 1)

---

FOR SEVEN GENERATIONS

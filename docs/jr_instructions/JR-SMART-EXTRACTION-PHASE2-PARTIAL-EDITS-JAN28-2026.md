# JR Instruction: Smart Extraction Phase 2 - Partial Code Edits

**JR ID:** JR-SMART-EXTRACTION-PHASE2-PARTIAL-EDITS-JAN28-2026
**Priority:** P1
**Assigned To:** TPM Direct (Bootstrap problem - Jrs can't self-modify)
**Council Vote:** b75dced893145a4c (84.3% confidence)
**Ultrathink:** ULTRATHINK-SMART-EXTRACTION-PHASE2-PARTIAL-EDITS-JAN28-2026.md
**Depends On:** Phase 1 Smart Extraction (live, verified Task #392)

---

## Objective

Add partial code edit support to task_executor.py so Jrs can apply code fragments (add methods, insert imports, modify functions) without overwriting entire files.

---

## Files Modified

| File | Change |
|------|--------|
| `/ganuda/jr_executor/task_executor.py` | Add partial edit detection and application |

---

## Changes Required

### 1. Add `_determine_edit_mode()` method
### 2. Add `_apply_partial_edit()` method
### 3. Add `_llm_merge_code()` method
### 4. Update `_extract_steps_via_regex()` to detect partial edits
### 5. Update `execute_steps()` to handle partial_edit operation

---

## Bootstrap Note

This instruction modifies the Jr executor itself. Since Jrs cannot apply partial edits yet (that's what this instruction adds), the TPM must apply these changes directly.

---

FOR SEVEN GENERATIONS

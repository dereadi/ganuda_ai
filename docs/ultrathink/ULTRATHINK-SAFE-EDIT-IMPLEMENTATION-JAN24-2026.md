# ULTRATHINK: Safe Edit Mode Implementation

**Date:** January 24, 2026
**Priority:** P0 - Critical Infrastructure
**Audit Hash:** safe_edit_ultrathink_jan24_2026

---

## Executive Summary

Implement SEARCH/REPLACE-based safe editing in the Jr executor to prevent code regression. This addresses the January 24, 2026 incident where specialist_council.py v1.3 (36KB) was overwritten with v1.2 (18KB), losing 18KB of working code.

**Council Vote:** 7/7 APPROVED (Tie resolved: implement both Reflection-Driven Control + Verifiably Safe Tool Use)

**Duplo Check:** PROCEED - 5 synergy opportunities, 0 conflicts

---

## Problem Statement

### The Incident
```
Task: "Add Triple Ethics to specialist_council.py"
Expected: Targeted edit adding ~50 lines
Actual: Complete file regeneration, lost 18KB of code
Root Cause: LLM generated full file from training memory (v1.2) instead of editing current file (v1.3)
```

### Why This Happens
1. **Training Data Bias**: LLMs have seen file patterns in training, may regenerate from memory
2. **No Edit Boundaries**: Without SEARCH/REPLACE format, LLM doesn't know what to preserve
3. **No Validation**: No guardrails to catch regression before write

### Impact
- Lost functions, classes, and features
- Version downgrade (v1.3 → v1.2)
- Hours of development work destroyed
- Violates Seven Generations principle

---

## Research Foundation

### Council-Evaluated Papers

| Paper | Votes | Key Contribution |
|-------|-------|------------------|
| **Reflection-Driven Control** (arXiv:2512.21354) | 3 | Self-reflection + reflective memory |
| **Verifiably Safe Tool Use** (arXiv:2601.08012) | 3 | Tool-level guardrails |
| Repository Memory (arXiv:2510.01003) | 1 | Long-term code history |

### Industry Solutions

| Tool | Approach | Adoption |
|------|----------|----------|
| **Aider** | SEARCH/REPLACE blocks | Widely used |
| **OpenAI V4A** | Context-based patches | Official recommendation |
| **SWE-Agent** | Precise file editing | 74%+ on SWE-bench |

### Council Resolution
Tie (3-3) resolved by Peace Chief observation: approaches are **complementary, not competing**.
- **Verifiably Safe Tool Use** = Prevention (guardrails)
- **Reflection-Driven Control** = Learning (don't repeat mistakes)

**Implementation: Both integrated into safe_edit.py**

---

## Duplo Interaction Check

```
=== UKTENA INTERACTION CHECK ===

Characteristics Detected:
  requires_multi_pass: False
  is_memory_technique: True

Synergies (5):
  + Thermal Memory - Edit failures logged for learning
  + A-MEM - Associative linking finds similar patterns
  + Consciousness Cascade - Uncertainty detection
  + Tribal Vision - Infrastructure compatibility

Conflicts: None

RECOMMENDATION: PROCEED
```

---

## Architecture

### Safe Edit Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     Jr Task Executor                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Receive task: "Modify file X"                               │
│                    │                                             │
│                    ▼                                             │
│  2. Check: Does file exist?                                      │
│            │                                                     │
│     ┌──────┴──────┐                                             │
│     │             │                                              │
│    YES           NO                                              │
│     │             │                                              │
│     ▼             ▼                                              │
│  SAFE EDIT    FULL GEN                                          │
│  MODE         MODE                                               │
│     │             │                                              │
│     ▼             │                                              │
│  3. Read existing content                                        │
│     │                                                            │
│     ▼                                                            │
│  4. Build SAFE_EDIT_PROMPT                                       │
│     - Include existing file (truncated if >8KB)                  │
│     - Request SEARCH/REPLACE blocks only                         │
│     │                                                            │
│     ▼                                                            │
│  5. LLM generates SEARCH/REPLACE blocks                          │
│     │                                                            │
│     ▼                                                            │
│  6. Parse blocks with parse_search_replace_blocks()              │
│     │                                                            │
│     ▼                                                            │
│  7. Apply with apply_edit_blocks()                               │
│     - Exact match first                                          │
│     - Fuzzy match (threshold 0.8) if needed                      │
│     │                                                            │
│     ▼                                                            │
│  8. VALIDATE with validate_modification()                        │
│     │                                                            │
│     ├── Size reduction >20%? → REJECT                           │
│     ├── Lost functions? → REJECT                                 │
│     ├── Lost classes? → REJECT                                   │
│     ├── Version downgrade? → REJECT                              │
│     │                                                            │
│     ▼                                                            │
│  9. If valid: Write file                                         │
│     If invalid: Log to thermal memory, return error              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### SEARCH/REPLACE Format

```
<<<<<<< SEARCH
[exact existing code to find - include 2-3 lines context]
=======
[new code to replace with]
>>>>>>> REPLACE
```

**Rules:**
1. SEARCH must EXACTLY match existing code (whitespace matters)
2. Include 2-3 lines of unchanged context
3. Make MINIMAL changes
4. Multiple blocks for multiple changes
5. NEVER replace entire functions unless necessary

---

## Implementation Files

### File 1: `/ganuda/jr_executor/safe_edit.py` (NEW)

Core module implementing:

| Function | Purpose |
|----------|---------|
| `parse_search_replace_blocks()` | Extract edit blocks from LLM output |
| `find_best_match()` | Locate code with exact + fuzzy matching |
| `apply_edit_blocks()` | Apply edits to content |
| `validate_modification()` | Guard against regression |
| `safe_edit_file()` | Main entry point |
| `SAFE_EDIT_PROMPT` | Prompt template for LLM |

### File 2: `/ganuda/jr_executor/jr_task_executor.py` (MODIFY)

Integration in `_execute_code_task()`:

```python
# Detect if modifying existing file
if file_exists:
    # SAFE EDIT MODE
    prompt = f"{SAFE_EDIT_PROMPT}\n\n=== EXISTING FILE ===\n{existing_content[:8000]}\n\n=== TASK ===\n{task_content}"
    llm_response = self._query_llm(prompt)
    success, message = safe_edit_file(output_path, llm_response)
else:
    # NEW FILE MODE (existing logic)
    ...
```

---

## Validation Guards

### Guard 1: Size Check
```python
if len(modified) < len(original) * 0.8:
    return False, f"Code size reduced >20%"
```

### Guard 2: Function Preservation
```python
original_funcs = set(re.findall(r'def (\w+)\s*\(', original))
modified_funcs = set(re.findall(r'def (\w+)\s*\(', modified))
lost_funcs = original_funcs - modified_funcs
if lost_funcs:
    return False, f"Would lose functions: {lost_funcs}"
```

### Guard 3: Class Preservation
```python
original_classes = set(re.findall(r'class (\w+)\s*[:\(]', original))
modified_classes = set(re.findall(r'class (\w+)\s*[:\(]', modified))
lost_classes = original_classes - modified_classes
if lost_classes:
    return False, f"Would lose classes: {lost_classes}"
```

### Guard 4: Version Protection
```python
if has_version_downgrade(original, modified):
    return False, "Version downgrade detected"
```

---

## Thermal Memory Integration (Reflection-Driven Control)

When an edit fails validation:

```python
def _log_edit_failure(task_id: str, filepath: str, reason: str):
    """Log edit failure to thermal memory for learning."""
    memory = {
        'memory_type': 'edit_failure',
        'content': f"Safe edit rejected: {filepath} - {reason}",
        'metadata': {
            'task_id': task_id,
            'filepath': filepath,
            'rejection_reason': reason,
            'timestamp': datetime.now().isoformat()
        },
        'temperature_score': 95.0,  # Hot - recent failure
        'tags': ['safe-edit', 'regression-prevention', 'learning']
    }
    store_to_thermal_memory(memory)
```

Future enhancement: Query past failures before editing to avoid repeated mistakes.

---

## Cherokee Principles Alignment

| Principle | Application |
|-----------|-------------|
| **Seven Generations** | Don't destroy what previous generations built |
| **Mitakuye Oyasin** | Protect all code relations (functions depend on each other) |
| **Gadugi** | Collective learning from edit failures |
| **Distance=0** | Validation runs locally, no external dependency |

---

## Testing Plan

### Test 1: Basic SEARCH/REPLACE
```python
content = "def hello():\n    print('Hello')"
llm_output = "<<<<<<< SEARCH\ndef hello():\n    print('Hello')\n=======\ndef hello():\n    print('Hello, Cherokee!')\n>>>>>>> REPLACE"
# Expected: Successfully modifies greeting
```

### Test 2: Fuzzy Matching
```python
content = "def hello():  \n    print('Hello')"  # Extra space
llm_output = "<<<<<<< SEARCH\ndef hello():\n    print('Hello')\n=======\n..."
# Expected: Fuzzy match succeeds (ratio > 0.8)
```

### Test 3: Regression Rejection
```python
original = "# 500 lines of code..."
proposed = "# 100 lines of code..."
# Expected: REJECTED - >20% size reduction
```

### Test 4: Function Loss Rejection
```python
original = "def foo():\n    pass\n\ndef bar():\n    pass"
proposed = "def foo():\n    pass"
# Expected: REJECTED - Would lose function 'bar'
```

---

## Acceptance Criteria

| # | Criterion | Test |
|---|-----------|------|
| 1 | Existing files use SEARCH/REPLACE mode | Check prompt includes SAFE_EDIT_PROMPT |
| 2 | Validation rejects >20% size reduction | Unit test with small proposed file |
| 3 | Lost functions detected and blocked | Unit test removing a function |
| 4 | Lost classes detected and blocked | Unit test removing a class |
| 5 | Version downgrade blocked | Unit test with v1.3 → v1.2 |
| 6 | New files still use full generation | Check file_exists branch |
| 7 | Edit failures logged to thermal memory | Check memory entry created |
| 8 | Fuzzy matching handles whitespace | Test with trailing spaces |

---

## Rollback Plan

If safe edit causes issues:

```bash
# 1. Disable safe edit mode
export SAFE_EDIT_DISABLED=true

# 2. Restart executor
systemctl restart jr-executor

# 3. Remove the module (if needed)
rm /ganuda/jr_executor/safe_edit.py

# 4. Revert jr_task_executor.py changes
git checkout jr_executor/jr_task_executor.py
```

Total rollback time: < 5 minutes

---

## Task Dependencies

```
SAFE-EDIT-001 (P0, Task #275) ─────┬─── Must complete first
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        ▼                          ▼                          ▼
COUNCIL-ETHICS-001          AUQ-CASCADE-001          AWARENESS-MANIFEST-001
(P1, Task #276)             (P1, Task #277)          (P1, Task #278)
```

---

## Jr Assignment

**Assigned To:** Software Engineer Jr (Primary)
**Support:** IT Triad Jr (Code review)
**Estimated Effort:** 4-6 hours

**Instructions File:** `/ganuda/docs/jr_instructions/JR-SAFE-EDIT-MODE-JAN24-2026.md`

---

## Success Metrics (30-Day)

| Metric | Target |
|--------|--------|
| Code regressions prevented | 100% (zero regressions) |
| Edit validation false positives | <5% |
| Additional latency per edit | <500ms |
| Thermal memory learnings captured | >10 entries |

---

## Signatures

**TPM:** Claude Opus 4.5
**Council:** 7/7 APPROVED
**Duplo/Uktena:** PROCEED (5 synergies, 0 conflicts)

---

*Cherokee AI Federation - For Seven Generations*
*"Don't break what works. Build on what came before."*

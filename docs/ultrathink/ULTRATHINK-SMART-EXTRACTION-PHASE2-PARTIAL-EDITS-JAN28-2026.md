# Ultrathink: Smart Extraction Phase 2 - Partial Code Edits

**Date:** January 28, 2026
**Priority:** P1 - Enables Jr partial code edits
**Council Vote:** b75dced893145a4c (84.3% confidence, Option 5 Hybrid approved)
**Depends On:** Phase 1 Smart Extraction (live, verified Task #392)
**TPM:** Claude Opus

---

## Problem Statement

Phase 1 smart extraction correctly identifies target files from instruction headers and prose. However, JR instructions contain **partial edits** (add a method, modify __init__, insert imports) - not full file replacements.

Task #393 proved the gap:
- Smart extraction found target file `/ganuda/lib/jr_momentum_learner.py`
- Tried to write 7-line import snippet as the full 493-line file
- Guardrail correctly blocked: "Would reduce file from 493 to 7 lines"

---

## Council-Approved Design: Hybrid Partial Edit System

Three modes in priority order:

### Mode 1: APPEND (for "Add" verbs)

Detect patterns like:
- "Add this method after X"
- "Add new method: Y"
- "Add this new method after `filter_low_entropy_solutions`"

Action: Read existing file, append code block at end of class or file.

**Safety:** File can only grow. No data loss possible.

### Mode 2: LINE-TARGETED INSERTION (for "around line X" hints)

Detect patterns like:
- "around line 45"
- "after existing imports (around line 20)"
- "after `_validate_path()` (around line 240)"

Action: Read existing file, find the target location, insert code block.

**Safety:** File grows. Original content preserved. Line hints are fuzzy (use as starting point, search for anchor text).

### Mode 3: LLM-ASSISTED MERGE (fallback)

When Mode 1 and 2 can't determine the edit type:
- Send existing file content + code fragment + surrounding prose to vLLM
- Ask: "Merge this code fragment into the existing file at the appropriate location"
- Validate result: must not lose >10% of original content

**Safety:** Guardrail validates output. Backup created before write.

---

## Implementation Design

### New Method: `_determine_edit_mode()`

```python
def _determine_edit_mode(self, preceding_text: str, code_content: str,
                          target_file: str) -> dict:
    """
    Determine the appropriate edit mode for a code block.

    Returns dict with:
        mode: 'append' | 'insert' | 'replace' | 'llm_merge'
        anchor: Optional text to search for in existing file
        line_hint: Optional approximate line number
        verb: The action verb detected
    """
```

Patterns to detect:
- `Add.*method` → append mode
- `Add.*import` → insert at top
- `Modify.*method.*around line (\d+)` → insert/replace at line
- `Replace.*section` → replace mode
- `Update.*method` → replace mode (find method, replace body)
- No clear pattern → llm_merge fallback

### New Method: `_apply_partial_edit()`

```python
def _apply_partial_edit(self, filepath: str, content: str,
                         edit_info: dict) -> dict:
    """
    Apply a partial edit to an existing file.

    Args:
        filepath: Target file path
        content: Code fragment to apply
        edit_info: Dict from _determine_edit_mode()

    Returns:
        Result dict with success, written bytes, mode used
    """
```

Logic:
1. Read existing file
2. Create backup
3. Based on mode:
   - **append**: Find last line of target class/module, insert before it
   - **insert**: Find anchor text or line hint, insert after
   - **replace**: Find method signature, replace method body
   - **llm_merge**: Call vLLM to merge
4. Validate result (no excessive content loss)
5. Write merged file

### Enhanced `_extract_steps_via_regex()`

Instead of creating `write` steps for all code blocks, create `partial_edit` steps:

```python
steps.append({
    'type': 'file',
    'args': {
        'operation': 'partial_edit',  # NEW
        'path': filepath,
        'content': content,
        'edit_mode': edit_info['mode'],
        'anchor': edit_info.get('anchor'),
        'line_hint': edit_info.get('line_hint'),
    }
})
```

### Update `execute_steps()` to handle partial_edit

In the file operation handler, check for `operation == 'partial_edit'` and call `_apply_partial_edit()`.

---

## Safety Constraints (Council Security Guidance)

1. **Backup always**: Create `.bak` before any partial edit
2. **Size guardrail**: Merged file must be >= 90% of original size (for add/insert) or >= 50% (for replace)
3. **Syntax check**: Run `python3 -m py_compile` after edit to Python files
4. **Rollback on failure**: Restore backup if syntax check fails
5. **LLM merge limit**: Only for files < 500 lines (context window safety)

---

## Test Cases

### Test 1: Append Mode
```
"Add this new method after existing methods:"
```python
def new_method(self):
    pass
```
```
Expected: Method appended before class closing

### Test 2: Insert at Line
```
"Add import at the top of the file (around line 5):"
```python
import new_module
```
```
Expected: Import inserted near line 5

### Test 3: LLM Merge Fallback
```
"Update the `__init__` method:"
```python
def __init__(self, new_param=None):
    self.new_param = new_param
```
```
Expected: LLM merges new __init__ with existing one

---

## Files to Modify

| File | Change |
|------|--------|
| `/ganuda/jr_executor/task_executor.py` | Add partial edit methods and enhance step extraction |

---

## Rollback

```bash
git -C /ganuda checkout jr_executor/task_executor.py
```

---

FOR SEVEN GENERATIONS

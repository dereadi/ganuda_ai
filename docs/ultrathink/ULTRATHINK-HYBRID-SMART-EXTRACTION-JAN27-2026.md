# Ultrathink: Hybrid Smart Extraction - Phase 1 Enhanced Regex

**Date:** January 27, 2026
**Priority:** P1 - Enables Jr autonomous code execution
**Council Vote:** 8f3a1e9f4b86ded5 (85% confidence, Option 4 approved)
**TPM:** Claude Opus

---

## Problem Statement

Jr instructions use prose-style descriptions for partial code edits:
```
Modify the `__init__` method (around line 45):
```python
<code>
```

But the regex extractor in `task_executor.py` only matches explicit path patterns:
```
Modify: `/ganuda/lib/file.py`
```python
<code>
```

Result: Jrs extract bash verification steps but miss the actual code changes.

---

## Current Regex Patterns (task_executor.py:820-825)

```python
file_patterns = [
    r"Create\s+`([^`]+)`",           # Create `/path/file`
    r"\*\*File:\*\*\s*`([^`]+)`",    # **File:** `/path/file`
    r"File:\s*`([^`]+)`",            # File: `/path/file`
    r"Modify:\s*`([^`]+)`",          # Modify: `/path/file`
]
```

These patterns require the path to be explicitly stated before the code block.

---

## Analysis of JR Instruction Formats

### Pattern 1: Section Header with File Path
Found in many JR instructions:
```markdown
### 1. Add MAGRPO Import

At the top of the file, after existing imports (around line 20):
```

**Problem:** File path is in the document header, not before code block.

**Solution:** Track the "target file" from instruction metadata/headers.

### Pattern 2: Implicit File from Context
```markdown
## Changes Required

### 1. Add MAGRPO Import

At the top of the file, after existing imports (around line 20):

```python
# MAGRPO multi-agent cooperation (Phase 2)
```

**Problem:** "the file" refers to a file mentioned earlier in the document.

**Solution:** Parse instruction header for file paths like:
- `Files Modified: /ganuda/lib/jr_momentum_learner.py`
- `File: /ganuda/lib/file.py`

### Pattern 3: Explicit File in Prose
```markdown
Modify `/ganuda/lib/jr_momentum_learner.py` to add:

```python
<code>
```

**Solution:** New regex pattern for prose file mentions.

---

## Enhanced Extraction Strategy

### Step 1: Extract Target File from Instruction Header

Parse the instruction file header for patterns:
```
| File | Change |
|------|--------|
| `/ganuda/lib/jr_momentum_learner.py` | Add MAGRPO integration |
```

Or:
```
## Files Modified

| File | Change |
| `/ganuda/lib/file.py` | Description |
```

Or YAML-style:
```
Files Modified:
- /ganuda/lib/file.py
```

### Step 2: Track Current Target File

When parsing code blocks, maintain state:
- If header specifies a single file → all code blocks target that file
- If multiple files → look for section headers indicating which file

### Step 3: New Prose Patterns

Add patterns to detect file paths in prose before code blocks:

```python
# Pattern: "Modify `/path/file.py`" in prose
r"[Mm]odify\s+`(/[^`]+)`"

# Pattern: "Update `/path/file.py`" in prose
r"[Uu]pdate\s+`(/[^`]+)`"

# Pattern: "In `/path/file.py`" before code
r"[Ii]n\s+`(/[^`]+)`.*?```"

# Pattern: "to `/path/file.py`" (add to file)
r"to\s+`(/[^`]+)`"

# Pattern: File path in markdown table
r"\|\s*`(/ganuda/[^`]+)`\s*\|"
```

### Step 4: Fallback - Single File Instructions

If instruction mentions only ONE file in the entire document, assume all code blocks modify that file.

---

## Implementation Design

### New Method: `_extract_target_file_from_header()`

```python
def _extract_target_file_from_header(self, instructions: str) -> Optional[str]:
    """
    Extract the primary target file from instruction header/metadata.

    Looks for patterns like:
    - | `/ganuda/lib/file.py` | in markdown tables
    - Files Modified: /path/file
    - File: /path/file.py in YAML-style headers

    Returns the file path if exactly ONE target file found, else None.
    """
```

### Enhanced `_extract_steps_via_regex()`

```python
def _extract_steps_via_regex(self, instructions: str) -> List[Dict]:
    """
    Enhanced regex extraction with smart file detection.

    Phase 1 Enhancement (Council Vote 8f3a1e9f4b86ded5):
    1. First extract target file from instruction header
    2. Then extract code blocks with existing patterns
    3. For unmatched Python blocks, use target file if available
    4. Validate all paths before returning
    """
```

---

## Safety Constraints (Council Security Guidance)

1. **Path Validation**: All extracted paths must pass `_validate_path()`
2. **Single File Safety**: Only use header-extracted file if it's the ONLY file mentioned
3. **No Guessing**: If multiple files mentioned and no explicit pattern, skip the block
4. **Backup Required**: Task executor already creates backups (existing safeguard)

---

## Test Cases

### Test 1: Single Target File in Header
```markdown
## Files Modified
| File | Change |
| `/ganuda/lib/jr_momentum_learner.py` | Add MAGRPO |

### Add Import
```python
from magrpo import tracker
```
```

**Expected:** Code block attributed to `/ganuda/lib/jr_momentum_learner.py`

### Test 2: Explicit Path in Prose
```markdown
Modify `/ganuda/lib/file.py` to include:

```python
def new_function():
    pass
```
```

**Expected:** Code block attributed to `/ganuda/lib/file.py`

### Test 3: Multiple Files - No Attribution
```markdown
## Files
- /ganuda/lib/a.py
- /ganuda/lib/b.py

```python
# Which file is this for?
```
```

**Expected:** Code block SKIPPED (ambiguous)

---

## Files to Modify

| File | Change |
|------|--------|
| `/ganuda/jr_executor/task_executor.py` | Add enhanced regex extraction |

---

## Rollback

```bash
git -C /ganuda checkout jr_executor/task_executor.py
```

---

FOR SEVEN GENERATIONS

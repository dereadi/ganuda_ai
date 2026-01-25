# KB: JR Instruction Format Requirements
## KB-JR-FORMAT-001
## Date: January 21, 2026
## Cherokee AI Federation

---

## Problem

JR tasks marked as "completed" but files not created. Root cause: instruction file format doesn't match what the task executor regex expects.

---

## Root Cause Analysis

The `task_executor.py` uses regex patterns to extract file creation steps from markdown instructions. If patterns don't match, no steps are extracted, and task completes with 0 steps (false success).

**Location**: `/ganuda/jr_executor/task_executor.py` lines 687-704

---

## Supported Patterns

The regex extraction supports ONLY these patterns for file creation:

### Pattern 1: Create with backticks (RECOMMENDED)
```markdown
Create `/ganuda/lib/myfile.py`:

```python
# code here
```
```

### Pattern 2: Bold File label
```markdown
**File:** `/ganuda/lib/myfile.py`

```python
# code here
```
```

### Pattern 3: File label (plain)
```markdown
File: `/ganuda/lib/myfile.py`

```python
# code here
```
```

### Pattern 4: Modify label
```markdown
Modify: `/ganuda/lib/existing.py`

```python
# modified code
```
```

---

## UNSUPPORTED Patterns (Will NOT Extract)

These formats look correct but WILL NOT be extracted:

```markdown
# WON'T WORK - extra word between Create and backtick
Create file `/ganuda/lib/myfile.py`:

# WON'T WORK - markdown header before code
### Create the file /ganuda/lib/myfile.py

# WON'T WORK - no backticks around path
Create /ganuda/lib/myfile.py:

# WON'T WORK - path in bold instead of backticks
Create **/ganuda/lib/myfile.py**:
```

---

## Code Block Language Requirements

The executor only extracts code for these languages:
- `python`
- `typescript`
- `javascript`
- `sql` (executed directly, no file)
- `bash` / `shell` / `sh` (executed directly, no file)

Other language hints (yaml, json, ini) are IGNORED for file creation.

---

## Correct JR Instruction Template

```markdown
# JR Instruction: [Task Name]
## Task ID: [ID]
## Priority: P1/P2/P3

---

## Objective

[Clear description of what to accomplish]

---

## Implementation

### Step 1: Create the main module

Create `/ganuda/lib/mymodule.py`:

```python
#!/usr/bin/env python3
"""Module docstring."""

def main():
    pass

if __name__ == "__main__":
    main()
```

### Step 2: Create the helper script

Create `/ganuda/scripts/helper.sh`:

```bash
#!/bin/bash
echo "Helper script"
```

### Step 3: Run database migration

```sql
CREATE TABLE IF NOT EXISTS my_table (
    id SERIAL PRIMARY KEY
);
```

---

## Verification

```bash
# Test commands (will be executed)
python3 /ganuda/lib/mymodule.py
```
```

---

## Diagnostic Query

Check if a task extracted any steps:

```sql
SELECT
    title,
    status,
    progress_percent,
    artifacts,
    LEFT(status_message, 100) as msg
FROM jr_work_queue
WHERE title LIKE '%your task%'
ORDER BY created_at DESC;
```

If `artifacts` is empty and `status = 'completed'`, the regex didn't extract any steps.

---

## Fix for Existing Instructions

Search and replace in JR instructions:
- `Create file \`` → `Create \``
- `Create the file \`` → `Create \``
- Ensure code blocks immediately follow the pattern (within 300 chars)

---

## Future Enhancement

Consider updating `task_executor.py` to support more flexible patterns:
- Allow "Create file" with word between
- Support markdown headers as file indicators
- Extract from yaml/json/ini blocks

**JR Instruction needed**: JR-FIX-INSTRUCTION-PARSER-FLEXIBLE-JAN21-2026

---

*For Seven Generations - Learn from every failure*

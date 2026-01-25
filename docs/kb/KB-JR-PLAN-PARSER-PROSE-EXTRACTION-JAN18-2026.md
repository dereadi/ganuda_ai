# KB Article: Jr Plan Parser - Prose Extraction Bug Fix

**KB ID**: KB-2026-0118-001
**Date**: January 18, 2026
**Category**: Bug Fix / Jr Executor
**Severity**: High
**Status**: Partially Resolved

## Summary

The Jr task executor was marking tasks as "completed" without actually creating files. This occurred because the prose-to-code extraction pipeline couldn't parse instruction formats using "CREATE FILES:" (plural) with numbered lists.

## Root Cause Analysis

Three bugs were identified:

### Bug 1: instruction_content Not Supported
**File**: `/ganuda/jr_executor/task_executor.py`
**Issue**: `process_queue_task()` only read from `instruction_file`, ignoring `instruction_content` field.
**Fix**: Added check for instruction_content before instruction_file:
```python
instructions = task.get('instruction_content')
if not instructions:
    instruction_file = task.get('instruction_file')
    # ... read from file
```

### Bug 2: Structured Planning Response Not Generating Actionable Steps
**File**: `/ganuda/lib/jr_llm_reasoner.py`
**Issue**: `understand_instruction()` returned parsed JSON but without files_to_create/files_to_modify that the executor could act on.
**Fix**: Created Devika AI-style planning prompt system:
- `/ganuda/lib/jr_planning_prompt.py` - Structured planning prompts
- `/ganuda/lib/jr_plan_parser.py` - Response parser with prose extraction

### Bug 3: Prose Extraction Missing Base Path
**File**: `/ganuda/lib/jr_plan_parser.py`
**Issue**: `extract_files_from_prose()` found filenames but not full paths when instructions used:
```
FRONTEND LOCATION: /ganuda/vetassist/frontend/src/app/workbench/
CREATE FILES:
1. page.tsx
2. layout.tsx
```
**Fix**: Added logic to combine BACKEND/FRONTEND LOCATION with filenames:
```python
location_match = re.search(r'(?:BACKEND|FRONTEND)\s+LOCATION:\s*([/\w\.\-_/]+)', instructions, re.IGNORECASE)
base_path = location_match.group(1).rstrip('/') if location_match else None
# Combine with filenames found in CREATE FILES section
```

## Remaining Issue

**Still Broken**: The "CREATE FILES:" (plural) pattern with numbered list format:
```
CREATE FILES:
1. page.tsx
2. layout.tsx
```

The current regex only handles single file pattern:
```python
single_file_match = re.search(r'CREATE\s+FILE:\s*(\w+\.(?:py|tsx?|jsx?|sql|md))', ...)
```

**Needed Fix**: Add pattern to handle numbered list after "CREATE FILES:":
```python
create_section = re.search(r'CREATE\s+FILES?:\s*(.*?)(?:FEATURES|API|DATABASE|SECURITY|$)', instructions, re.DOTALL | re.IGNORECASE)
if create_section:
    file_names = re.findall(r'^\s*\d+\.\s+(\w+\.(?:py|tsx?|jsx?|sql|md))', create_section.group(1), re.MULTILINE)
```

## Files Modified

| File | Change |
|------|--------|
| `/ganuda/jr_executor/task_executor.py` | Added instruction_content support |
| `/ganuda/lib/jr_llm_reasoner.py` | Added simple_completion() method |
| `/ganuda/lib/jr_planning_prompt.py` | NEW - Planning prompt templates |
| `/ganuda/lib/jr_plan_parser.py` | NEW - Response parser with prose extraction |

## Verification

Backend task 108 (Document Upload API) successfully created:
- `/ganuda/vetassist/backend/app/api/v1/endpoints/workbench_documents.py` (4,256 bytes)

Frontend tasks 109-123 completed but did NOT create files due to remaining plural pattern bug.

## Next Steps

1. Create JR instruction to fix the "CREATE FILES:" plural pattern
2. Re-run frontend tasks 109, 113, and others after fix
3. Add unit tests for jr_plan_parser.py

## References

- Devika AI (github.com/stitionai/devika) - Planning agent architecture reference
- GPT-Engineer (github.com/AntonOsika/gpt-engineer) - File extraction patterns

---
Cherokee AI Federation - For Seven Generations

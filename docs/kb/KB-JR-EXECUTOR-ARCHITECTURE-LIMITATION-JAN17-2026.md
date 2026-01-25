# KB Article: Jr Executor Architecture Limitation

**ID**: KB-2026-0117-001
**Created**: January 17, 2026
**Category**: Infrastructure / Jr System
**Impact**: High - Affects all Jr task execution

---

## Summary

The Jr task executor marks tasks as "completed" even when no actual work is performed. This occurs because the LLM step extraction process doesn't generate actionable steps from prose instructions.

## Root Cause

The `_extract_steps_via_llm()` method in `/ganuda/jr_executor/task_executor.py` relies on the LLM to:
1. Understand the instruction content
2. Return structured data including `files_to_create` and `files_to_modify`
3. Generate code for each file

However, when instructions are written in prose format (like JR instruction markdown files), the LLM understanding phase doesn't reliably extract file paths. This results in:
- `files_to_create = []`
- `files_to_modify = []`
- No steps generated
- Task marked "completed" with empty `steps_executed`

## Evidence

Tasks 108-123 (VetAssist Claim Workbench) were all marked "completed" but:
- No workbench frontend files created
- No workbench backend files created
- `steps_executed` array is empty for all tasks

## Affected Tasks

Any task using `instruction_content` with prose-style instructions will experience this issue.

## Workarounds

### Option 1: Include Explicit Code Blocks
Instructions should include explicit ```python or ```typescript code blocks with complete file contents. The regex fallback can extract these.

### Option 2: Use instruction_file with Scaffolded Content
Write instruction files that include full file contents rather than descriptions of what to create.

### Option 3: Direct Infrastructure Intervention
For critical path items, TPM may need to create scaffolding files directly.

## Recommended Fix

Enhance the `_extract_steps_via_llm()` method to:
1. Parse markdown headers for file paths (e.g., "## File to Create: /path/to/file.py")
2. Generate code based on prose descriptions using code generation prompts
3. Fall back to creating stub files when uncertain

## Related Tasks

- Task 124: Fix Task Executor instruction_content Support (completed - partial)
- Tasks 108-123: VetAssist Claim Workbench (affected)

---

*Cherokee AI Federation - For Seven Generations*

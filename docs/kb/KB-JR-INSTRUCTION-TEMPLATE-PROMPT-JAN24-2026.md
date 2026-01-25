# KB Article: Jr Executor Instruction Template Handling

**ID:** KB-JR-INSTRUCTION-TEMPLATE-PROMPT-JAN24-2026
**Date:** January 24, 2026
**Category:** Jr Executor
**Status:** Issue Identified - Fix Pending

## Problem

Jr instruction files contain complete code templates (ready-to-use code snippets), but the executor prompt tells the LLM to "Generate the code" which causes it to create new code from scratch instead of using the provided templates.

## Observed Behavior

1. Instruction file is read correctly (logged: "Read instruction file: ... 3097 chars")
2. Content is appended after "=== DETAILED INSTRUCTIONS ===" marker
3. LLM ignores the templates and generates completely different code
4. Example: Instruction file has FastAPI/Next.js templates, LLM generates Flask code

## Root Cause

In `jr_task_executor.py` line 731-755:

```python
# Build strict code generation prompt
prompt = f"""You are a code generator for Cherokee AI Federation.

OUTPUT RULES - FOLLOW EXACTLY:
1. Output ONLY executable {language} code
...

TASK:
{content}  # <-- instruction file appended here

Generate the {language} code now. Output ONLY code, starting immediately:"""
```

The word "Generate" triggers the LLM to create new code. The instruction templates are buried in the TASK section without emphasis.

## Proposed Fix

Restructure the prompt to emphasize template usage:

```python
prompt = f"""You are a code implementer for Cherokee AI Federation.

CRITICAL: This task includes CODE TEMPLATES you MUST use as the foundation.
Do NOT create new code from scratch. MODIFY and COMPLETE the provided templates.

OUTPUT RULES:
1. Start with the template code provided below
2. Fill in any placeholder comments (e.g., "# TODO", "// implement")
3. Preserve the existing structure and imports
4. Output ONLY the completed code, no explanations

=== TEMPLATE CODE TO IMPLEMENT ===
{instruction_content if instruction_content else "No template provided - generate from scratch"}

=== TASK CONTEXT ===
{original_task_content}

Implement the code following the template above:"""
```

## Workaround (Current)

Until the fix is deployed, TPM should:
1. Review Jr output before accepting
2. Manually apply templates from instruction files
3. Use Jr output for logic reference only

## Files to Modify

- `/ganuda/jr_executor/jr_task_executor.py` - `_execute_code_task()` method

## Success Criteria

- [ ] Jr generates code matching instruction file stack (FastAPI, Next.js)
- [ ] Template imports and structure preserved
- [ ] Only gaps/placeholders filled by LLM

## Related

- KB-QWEN-MULTIFILE-LIMIT-JAN24-2026 (task complexity limits)
- KB-JR-EXECUTOR-INSTRUCTION-FILE-READING-JAN24-2026 (file reading fix)

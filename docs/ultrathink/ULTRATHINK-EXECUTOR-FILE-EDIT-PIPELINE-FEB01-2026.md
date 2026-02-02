# ULTRATHINK: Jr Executor File-Edit Pipeline — 100% Failure Rate Root Cause

**Date:** February 1, 2026
**TPM:** Claude Opus 4.5
**Trigger:** 5 consecutive Jr task failures (#514-518), all on file edit operations
**Source File:** `/ganuda/jr_executor/task_executor.py`

## Executive Summary

The Jr executor has three file-edit subsystems that don't coordinate. When a Jr instruction says "modify this file" with a code snippet, the executor defaults to full-file write mode, which triggers the safety guardrails. The `SearchReplaceEditor` (added Jan 31) would handle this correctly, but Jr instructions aren't written in the format it expects.

**Bottom line:** The executor already has the right tool. The instructions aren't speaking its language.

## Failure Evidence

| Task | Title | Error | Root Cause |
|------|-------|-------|------------|
| #514 | Crisis Detection Fix | `partial_edit:insert_after:skipped` | False positive idempotency (RC-4) |
| #515 | PII Over-Redaction | BLOCKED 456→17 lines | Mode default to write (RC-1) |
| #516 | Calculator localStorage | BLOCKED 595→240 lines | Mode default to write (RC-1) |
| #517 | Tooltips (partial) | BLOCKED 595→230 lines | Mode default to write (RC-1), 2 new files created OK |
| #518 | VA Ratings API | BLOCKED 154→7 lines | Mode default to write (RC-1) |

## The Three Subsystems

### Subsystem A: Partial Edit (`_apply_partial_edit()`, line 430)
- Modes: `insert_top`, `append`, `insert_after`
- Activated when `_determine_edit_mode()` (line 330) returns non-write mode
- Uses prose pattern matching to detect intent (e.g., "add this new method")
- **Problem:** Narrow regex patterns. Only matches `add\s+(?:this\s+)?(?:new\s+)?(?:method|function|class)`

### Subsystem B: Safe File Write (`safe_file_write()`, line 2110)
- The default path when mode detection returns 'write'
- Goes through `validate_file_write()` (line 2050) guardrails
- **Problem:** Guardrails block any write that reduces file by >50% lines — catches ALL snippet-based edits

### Subsystem C: Search Replace Editor (`SearchReplaceEditor`, line 1517-1548 extraction + line 1603 execution)
- Activated by `<<<<<<< SEARCH / ======= / >>>>>>> REPLACE` blocks in instructions
- Uses exact text matching, backup, syntax validation, automatic rollback
- **This is the RIGHT tool.** But no Jr instructions use this format.

## Root Causes (Prioritized)

### RC-1: Mode Detection Defaults to Full-File Write (CRITICAL)

**Location:** `_determine_edit_mode()`, line 330-420

When the regex extractor finds a code block preceded by `**File:** \`path\``, it calls `_determine_edit_mode()` to decide if it's a partial edit or full write. The detection relies on narrow patterns:

```python
# Only matches: "add this new method", "add new function", "add class"
add_match = re.search(r'add\s+(?:this\s+)?(?:new\s+)?(?:method|function|class)', text)
```

Our Jr instructions say things like:
- "Find the VA_SCOPES list and add `disability_rating.read`"
- "Change the ML crisis detection from primary to advisory"
- "Add a new endpoint that fetches the veteran's rated disabilities"

None of these match the narrow patterns. Mode defaults to `'write'`, treating the code snippet as the ENTIRE file content.

### RC-2: Guardrails Block Legitimate Snippets (CRITICAL)

**Location:** `validate_file_write()`, line 2062-2072

```python
# Rule 1: Block if losing more than 50% of lines
if old_lines > 10 and new_lines < old_lines * 0.5:
    return False, f"BLOCKED: Would reduce file from {old_lines} to {new_lines} lines"

# Rule 3: Block suspiciously small replacement of large file
if old_lines > 50 and new_lines < 30:
    return False, f"BLOCKED: New content ({new_lines} lines) suspiciously small"
```

These guardrails are correct for preventing accidental file destruction. The problem is that RC-1 routes code snippets through this path when they should never reach it.

### RC-3: SEARCH/REPLACE Format Not Used in Instructions

**Location:** `_extract_steps_via_regex()`, lines 1517-1548

The extractor correctly parses `<<<<<<< SEARCH / ======= / >>>>>>> REPLACE` blocks and routes them to `_execute_search_replace()`, which uses the robust `SearchReplaceEditor`. But:
- No Jr instructions use this format
- The TPM has been writing instructions with standard markdown code blocks

### RC-4: False Positive Idempotency Check

**Location:** `_apply_partial_edit()`, line 459-474

```python
fingerprint_lines = [l.strip() for l in new_lines
                     if l.strip() and not l.strip().startswith('#')][:3]
existing_stripped = [l.strip() for l in existing_lines]
if fingerprint_lines and all(fp in existing_stripped for fp in fingerprint_lines):
    print(f"[PartialEdit] SKIP: Content already present ({mode})")
```

Uses first 3 non-blank, non-comment lines as a fingerprint. Common patterns like `import logging`, `from app.core.config import settings`, `logger = logging.getLogger(__name__)` exist in many files and trigger false matches.

### RC-5: Retry Re-Applies All Steps

**Location:** `_retry_with_reflection()`, line 1199

```python
steps = self._extract_steps_from_instructions(augmented_instructions)
step_results = self.execute_steps(steps)
```

On retry, ALL steps are re-extracted and re-executed, including ones that already succeeded (e.g., task #517 created HelpTip.tsx and PageHelpLink.tsx successfully, but retry would try to create them again).

## Recommended Fix: Two-Part Strategy

### Part 1: Adopt SEARCH/REPLACE Format in Jr Instructions (IMMEDIATE)

The executor already supports this. All future Jr instructions for file MODIFICATIONS (not new file creation) should use:

```
**File:** `/path/to/file.py`

<<<<<<< SEARCH
old code exactly as it appears in the file
=======
new code to replace it with
>>>>>>> REPLACE
```

For NEW file creation, continue using:
```
**Create:** `/path/to/new_file.py`

\`\`\`python
full file content
\`\`\`
```

This routes modifications through `SearchReplaceEditor` (exact match, backup, validation, rollback) and new files through the standard write path (no guardrail issue since file doesn't exist).

### Part 2: Executor Code Fixes (SECONDARY)

These fixes improve robustness for instructions that don't use SEARCH/REPLACE format:

1. **Broaden `_determine_edit_mode()` patterns** — Add: "find X and", "change X to", "replace X with", "add X to the list", "update the X"
2. **Bypass guardrails for search_replace type** — `validate_file_write()` should not apply to search_replace steps (they have their own safety in the SearchReplaceEditor)
3. **Fix idempotency fingerprinting** — Use 5+ lines minimum, exclude common patterns like `import`, `from`, `logger`
4. **Track step completion in retries** — Add `completed_step_ids` set, skip already-succeeded steps on retry

## Impact on Pending Tasks

Tasks #515-518 need to be re-queued with SEARCH/REPLACE format. The original instructions used markdown code blocks that the executor treats as full-file replacements.

## References

- Council Vote b75dced893145a4c: Hybrid Smart Extraction Phase 2
- Council Vote 6428bcda34efc7f9: Self-Healing Retry
- ULTRATHINK-JR-EXECUTOR-ARCHITECTURE-FIX-JAN26-2026
- KB-JR-EXECUTOR-EDIT-CAPABILITY-GAP-JAN29-2026
- SearchReplaceEditor: ULTRATHINK-EXECUTOR-SEARCH-REPLACE-ARCHITECTURE-JAN31-2026

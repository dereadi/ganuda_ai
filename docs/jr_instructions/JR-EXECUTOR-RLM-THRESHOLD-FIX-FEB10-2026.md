# Jr Instruction: Fix Executor RLM Auto-Detection Threshold

**Task ID:** EXECUTOR-FIX-003
**Priority:** P1
**Assigned To:** Software Engineer Jr.
**Date:** February 10, 2026
**KB:** KB-RLM-INTERCEPTION-LENGTH-THRESHOLD-BUG-FEB10-2026.md

## Context

The `_should_use_rlm()` function in task_executor.py auto-detects "complex" tasks and routes them through RLM recursive decomposition. The length threshold of 3000 characters is too low — well-documented infrastructure instructions (systemd units, calibration pipelines) routinely exceed 3000 chars but only create 2-3 files. RLM decomposition then fails to parse the `Create` format, returning "No executable steps found."

Additionally, the file-counting regex uses `Create:` (with colon) instead of `Create ` (with space), so the file count safeguard never triggers.

## Edit 1: Raise length threshold and fix file pattern

File: `/ganuda/jr_executor/task_executor.py`

```
<<<<<<< SEARCH
        # Auto-detection only applies if use_rlm was not explicitly set
        # Check instruction length
        if len(instructions) > 3000:
            return True

        # Check for complex task keywords in title
        title = task.get('title', '').lower()
        complex_keywords = ['implement', 'build system', 'create api', 'authentication',
                          'full stack', 'migration', 'refactor entire', 'redesign']
        if any(kw in title for kw in complex_keywords):
            return True

        # Count files mentioned in instructions
        file_patterns = re.findall(r'(?:Create|Modify|Update):\s*[`/][^\s`]+', instructions)
        if len(file_patterns) > 3:
            return True
=======
        # Auto-detection only applies if use_rlm was not explicitly set
        # Check for complex task keywords in title
        title = task.get('title', '').lower()
        complex_keywords = ['implement', 'build system', 'create api', 'authentication',
                          'full stack', 'migration', 'refactor entire', 'redesign']
        if any(kw in title for kw in complex_keywords):
            return True

        # Count files mentioned in instructions (space-delimited, per KB format)
        file_patterns = re.findall(r'(?:Create|Modify|Update)\s+`[^`]+`', instructions)
        if len(file_patterns) > 5:
            return True

        # Only use RLM for very long instructions with many files
        if len(instructions) > 8000 and len(file_patterns) > 3:
            return True
>>>>>>> REPLACE
```

## Design Decisions

- **Removed standalone length check**: Length alone is a poor proxy for complexity. A 6000-char instruction creating 2 files should use regex extraction, not RLM.
- **Fixed file pattern regex**: Changed from `Create:` (colon) to `Create ` (space + backtick) to match the KB-defined instruction format (`Create \`path\``).
- **Raised file threshold to >5**: Simple multi-file instructions (2-3 files) should use regex. Only truly complex tasks (6+ files) benefit from RLM decomposition.
- **Combined length + file check**: Only triggers RLM when BOTH conditions are met: very long (>8000 chars) AND many files (>3).

## Do NOT

- Do not modify `_extract_steps_via_regex()` — that function works correctly
- Do not modify `_execute_with_rlm()` — the RLM executor itself is fine
- Do not remove the `use_rlm` flag check — explicit overrides must be respected

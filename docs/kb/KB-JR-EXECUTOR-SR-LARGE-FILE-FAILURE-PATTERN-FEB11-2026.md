# KB: Jr Executor SEARCH/REPLACE Failure on Large Files

**Date**: February 11, 2026
**Severity**: P2 — task failure, guardrail prevents data loss
**Related**: Jr Tasks #685, #686, #699 (all failed same pattern)
**Kanban**: TBD
**Guardrail**: >50% file loss blocker (WORKING AS DESIGNED)

---

## Symptom

Jr tasks that edit large files (>500 lines) via SEARCH/REPLACE blocks fail with:
```
BLOCKED: Would reduce file from 1108 to 6 lines (>50% loss).
This looks like a replacement, not an edit.
```

The Jr receives a well-formed instruction with multiple SR blocks targeting the same file. Instead of applying each block surgically, the executor reduces the file to just the REPLACE content of one block.

## Root Cause

The executor's SR processing applies ALL blocks in a single pass:
1. Reads the entire file once
2. Attempts to find each SEARCH pattern
3. When a SEARCH pattern doesn't match exactly (whitespace, line endings, context drift), the executor falls back to treating the REPLACE content as the entire file
4. Result: 1108 lines → 6 lines → guardrail blocks it

This is a **regex matching failure cascade**. One missed SEARCH block causes the executor to abandon surgical editing and attempt a full file replacement.

## Impact

- **Task #699** (Thermal Memory RAG): Step 1 (SQL) succeeded, Step 2 (specialist_council.py edit) failed. The Jr's own reflection: "Consider a more incremental approach."
- **Tasks #685, #686** (Feb 11 power outage): Same pattern on specialist_council.py. Guardrail saved the file both times.
- **Pattern**: specialist_council.py at 1108 lines is the most frequent victim.

## Current Workaround

1. **Break large file edits into separate tasks** — one SR block per task
2. **TPM partner work** — apply complex edits directly when the Jr can't
3. **Keep the >50% guardrail** — it's the safety net that prevents data loss

## Proposed Solution: Recursive Self-Observation

**Chief's insight (Feb 11)**: The Jr should apply SR blocks one at a time with self-observation between each:

### Architecture: Sequential SR with Re-Read

```
Current (broken):
  read file → apply ALL blocks → write file → guardrail blocks

Proposed (recursive):
  read file → apply block 1 → write file → verify
  read file → apply block 2 → write file → verify
  read file → apply block N → write file → verify
```

### Key Principles:

1. **One block at a time**: Each SR block is a sub-task. Apply it, verify the result, then move to the next.

2. **Self-observation**: After each block, the Jr re-reads the file to see the current state. This is like a surgeon checking their work after each cut, not operating blindly through all steps.

3. **Ignore what's next until current succeeds**: The Jr should NOT look ahead to block 2 while applying block 1. Sequential focus prevents the cascade failure.

4. **Multithreading for DIFFERENT files**: SR blocks targeting different files CAN run in parallel (no shared state). SR blocks targeting the SAME file MUST be sequential.

5. **Per-block guardrail**: Each individual block changes only a few lines. The >50% guardrail would never trigger on a single-block edit. The problem only manifests when all blocks are batched.

### Implementation Sketch:

In `task_executor.py`, the `_apply_search_replace()` method should:

```
def _apply_search_replace_recursive(self, file_path, sr_blocks):
    """Apply SR blocks one at a time with verification between each."""
    for i, block in enumerate(sr_blocks):
        # 1. Read current file state
        current_content = read_file(file_path)

        # 2. Apply single block
        new_content = apply_single_sr(current_content, block.search, block.replace)

        # 3. Verify: did the content change? Is it reasonable?
        if new_content == current_content:
            log.warning(f"SR block {i+1} had no effect — SEARCH not found")
            continue  # or fail, depending on policy

        lines_before = current_content.count('\n')
        lines_after = new_content.count('\n')
        if lines_after < lines_before * 0.5:
            log.error(f"SR block {i+1} would reduce file by >50% — BLOCKED")
            return False

        # 4. Write and verify
        write_file(file_path, new_content)
        log.info(f"SR block {i+1}/{len(sr_blocks)} applied: {lines_before} → {lines_after} lines")

    return True
```

### Benefits:

- Each block is verified independently
- Guardrail applies per-block (much more precise)
- Self-observation means the Jr sees the actual file state, not stale assumptions
- Failed blocks don't cascade into destroying the entire file
- The Jr's reflection ("consider a more incremental approach") is exactly right — recursion IS the incremental approach

### Multithreading Consideration:

Group SR blocks by target file:
```
file_groups = group_by_file(all_sr_blocks)
# Parallel across files
with ThreadPoolExecutor() as executor:
    for file_path, blocks in file_groups.items():
        executor.submit(_apply_search_replace_recursive, file_path, blocks)
```

Same-file blocks stay sequential. Different-file blocks run in parallel. Best of both worlds.

## Related

- KB-RLM-INTERCEPTION-LENGTH-THRESHOLD-BUG-FEB10-2026.md (RLM threshold issue)
- KB-JR-INSTRUCTION-FORMAT-REGEX-COMPATIBILITY-FEB08-2026.md (SR format spec)
- KB-JR-DUAL-PIPELINE-ARCHITECTURE-FEB11-2026.md (Pipeline A vs B)

## Lessons Learned

1. The >50% guardrail is CRITICAL infrastructure. It has now saved specialist_council.py THREE times.
2. The Jr executor's SR processing needs recursive decomposition, not batch processing.
3. Large files (>500 lines) with multiple SR blocks are the failure mode. Break them up or recurse.
4. The Jr's own reflection was accurate — it identified the problem. It just couldn't fix itself. That self-awareness gap is the next thing to close.

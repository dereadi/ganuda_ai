# ULTRATHINK: Recursive Task Decomposition for Jr Executor

**Date**: February 12, 2026
**Council Vote**: 2adc1366 — PROCEED WITH CAUTION (0.823, Turtle 7GEN + Raven STRATEGY)
**Kanban**: #1768 (to be created)
**River Cycle**: RC-2026-02A
**Long Man Phase**: ADAPT → BUILD

## Problem Statement

The Jr executor processes multi-step instruction files but frequently fails to execute all steps:

| Failure Mode | Count | Root Cause |
|-------------|-------|------------|
| Mixed Create + SR blocks | 3/3 | Create block processed, SR blocks silently skipped |
| Relative file paths | 3/7 | `_validate_path()` rejects non-absolute paths |
| SR treated as file write | 2/7 | SR markers inside code fences → full file overwrite → >50% guardrail |
| SEARCH text mismatch | 2+ | Stale search text from instructions written without reading current file |

Currently, the TPM manually decomposes failed multi-step instructions into single-step re-queues. This works but doesn't scale.

## Three-Phase Solution

### Phase 1: Immediate Parser Fixes (DONE — TPM applied Feb 12)

1. **Relative path resolution**: `_validate_path()` and extraction sites now resolve relative paths to `/ganuda/` prefix
2. Added at SR extraction (line 1593) and code block extraction (line 1682)
3. Both the `_validate_path` method and the caller-side extraction resolve before validation

### Phase 2: Post-Execution Decomposition (Jr Instruction)

After `execute_steps()` returns, add a new phase that:

1. **Counts described steps** by parsing `### Step N:` headers from the instruction markdown
2. **Compares against executed steps** from the results list
3. **If steps remain unexecuted**:
   a. Extract the markdown section for each unexecuted step
   b. Create a new instruction file in `/ganuda/docs/jr_instructions/`
   c. Queue sub-task to `jr_work_queue` with:
      - `parent_task_id` = current task's work queue ID
      - Same `assigned_jr`
      - Same `sacred_fire_priority`
      - Title prefixed with `[RECURSIVE]`
4. **Track recursion depth** via `parameters` JSONB field: `{"recursion_depth": N}`
5. **At depth >= 3**: Do NOT decompose — instead route to DLQ for TPM escalation

### Phase 3: Future — Adaptive Decomposition (Separate Sprint)

- Use `_record_step_result()` data to predict which step types are likely to fail
- Pre-emptively decompose instructions with high-risk step patterns
- Learn from successful vs failed patterns via momentum learner

## Constitutional Guardrails (Council Concerns)

### Turtle [7GEN CONCERN]: Recursion Depth Limit

**Constraint**: `MAX_RECURSION_DEPTH = 3`

At depth 3, the executor has had 3 chances to decompose and retry. Further recursion risks:
- Infinite loops from persistent SEARCH mismatches
- Cascading sub-tasks that clutter the queue
- Loss of context (each decomposition loses surrounding instruction context)

At depth >= 3: route to DLQ with `escalation_level = 2` (TPM review).

### Raven [STRATEGY CONCERN]: Transparency + Chief Halt

**Constraint**: Full recursion tree visible via `parent_task_id` chain.

1. Every sub-task has `parent_task_id` linking to its origin
2. Thermal memory breadcrumb logged at each decomposition
3. The Chief can `block_task()` on ANY node in the tree, halting that subtree
4. The `[RECURSIVE]` title prefix makes sub-tasks instantly identifiable in the queue

### Crawdad [Implicit Security]: No New Attack Surface

The decomposition only:
- Re-queues existing instruction text (no new content generation)
- Uses the same `assigned_jr` (no privilege escalation)
- Runs through the same `_validate_path()` checks (no path bypass)
- Respects the >50% guardrail on every sub-task independently

## Implementation Design

### New Method: `_decompose_unexecuted_steps()`

Location: `jr_executor/task_executor.py`, after `process_queue_task()` returns

```
Input: original task dict, instruction text, step_results list
Output: list of sub-task dicts queued to jr_work_queue

Logic:
1. Parse instruction for ### Step headers
2. Map executed results to step numbers
3. For unexecuted steps:
   a. Extract markdown from that step's header to next header
   b. Write to /ganuda/docs/jr_instructions/JR-RECURSIVE-{parent_id}-STEP{n}.md
   c. INSERT into jr_work_queue
4. Return count of sub-tasks created
```

### Integration Point

In `process_queue_task()`, after step execution and before returning result:

```
if step_results and not all_success:
    depth = task.get('parameters', {}).get('recursion_depth', 0)
    if depth < MAX_RECURSION_DEPTH:
        sub_count = self._decompose_unexecuted_steps(task, instructions, step_results)
        result['recursive_subtasks'] = sub_count
    else:
        # Escalate to DLQ
        from jr_executor.dlq_manager import send_to_dlq
        send_to_dlq(task_id, "Max recursion depth reached", ...)
```

## Dependencies

- [x] DLQ table created (Phase 1 migration, done)
- [x] DLQ wired into worker failure path (done, TPM applied)
- [x] Checkpoint tables created (done)
- [x] Path resolution fix (done, Phase 1)
- [ ] `_decompose_unexecuted_steps()` method (Jr instruction)
- [ ] Integration into `process_queue_task()` (Jr instruction)

## GitHub Research References

- **FoundationAgents/ReCode** (532 stars): Recursive code generation with placeholder expansion
- **ysz/recursive-llm** (438 stars): 100k+ token processing via recursive decomposition
- **alexzhang13/rlm** (2.4K stars): Examine-decompose-recurse pattern

## Story Points Estimate

- Phase 2 (Jr instruction): **5 SP** — new method + integration, medium complexity
- Phase 3 (adaptive): **13 SP** — requires ML integration, future sprint

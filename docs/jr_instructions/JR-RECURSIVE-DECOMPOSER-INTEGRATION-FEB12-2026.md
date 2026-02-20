# Jr Instruction: Wire Recursive Decomposer into Task Executor

**Priority**: P0 — Core executor enhancement
**Council Vote**: 2adc1366 — PROCEED WITH CAUTION (0.823)
**Kanban**: #1768
**Assigned Jr**: Software Engineer Jr.
**Depends on**: JR-RECURSIVE-DECOMPOSER-MODULE-FEB12-2026

## Context

The recursive decomposer module (`/ganuda/jr_executor/recursive_decomposer.py`) has been created. Now we need to wire it into the task executor's `process_queue_task()` method. The integration point is AFTER the retry loop (Phase 11) and BEFORE the learning recording (Phase 7). When retries fail to recover a task, the decomposer extracts unexecuted steps and re-queues them as individual sub-tasks.

## Step 1: Add recursive decomposition after retry loop in task_executor.py

File: `/ganuda/jr_executor/task_executor.py`

<<<<<<< SEARCH
                    # Phase 7: Record execution outcome for learning (after retries)
                    if self.learning_store:
                        try:
                            self.learning_store.record_execution(task, result, reflection)
                            retries = len(result.get('retry_attempts', []))
                            print(f"[LEARNING] Recorded outcome: success={result.get('success')}, retries={retries}")
                        except Exception as le:
                            print(f"[LEARNING] Failed to record: {le}")
=======
                    # Phase 13: Recursive Task Decomposition (Council vote 2adc1366)
                    # If retries didn't fix it, decompose remaining steps into sub-tasks
                    if not result.get('success'):
                        try:
                            from jr_executor.recursive_decomposer import (
                                decompose_unexecuted_steps, MAX_RECURSION_DEPTH
                            )
                            params = task.get('parameters') or {}
                            if isinstance(params, str):
                                import json as _json
                                try:
                                    params = _json.loads(params)
                                except (json.JSONDecodeError, TypeError):
                                    params = {}
                            rec_depth = (params or {}).get('recursion_depth', 0)

                            if rec_depth < MAX_RECURSION_DEPTH:
                                sub_tasks = decompose_unexecuted_steps(
                                    task, instructions, step_results
                                )
                                if sub_tasks:
                                    result['recursive_subtasks'] = len(sub_tasks)
                                    result['recursive_subtask_ids'] = [
                                        s['id'] for s in sub_tasks
                                    ]
                                    print(f"[RECURSIVE] Created {len(sub_tasks)} sub-tasks")
                            else:
                                print(f"[RECURSIVE] Max depth {rec_depth} reached — DLQ escalation")
                                try:
                                    from jr_executor.dlq_manager import send_to_dlq
                                    send_to_dlq(
                                        task_id=task.get('id'),
                                        failure_reason=f"Max recursion depth {rec_depth} reached",
                                    )
                                except Exception as dlq_e:
                                    print(f"[RECURSIVE] DLQ send failed: {dlq_e}")
                        except ImportError:
                            print("[RECURSIVE] recursive_decomposer not available — skipping")
                        except Exception as rec_err:
                            print(f"[RECURSIVE] Decomposition error (non-fatal): {rec_err}")

                    # Phase 7: Record execution outcome for learning (after retries)
                    if self.learning_store:
                        try:
                            self.learning_store.record_execution(task, result, reflection)
                            retries = len(result.get('retry_attempts', []))
                            print(f"[LEARNING] Recorded outcome: success={result.get('success')}, retries={retries}")
                        except Exception as le:
                            print(f"[LEARNING] Failed to record: {le}")
>>>>>>> REPLACE

## Verification

After applying, confirm:
1. `Phase 13: Recursive Task Decomposition` comment appears in task_executor.py
2. `from jr_executor.recursive_decomposer import` appears in the file
3. The Phase 7 learning block is still present (not deleted)
4. The indentation matches (20 spaces for `if not result.get('success')`)

## For Seven Generations

# Jr Instruction: Wire Step Recording into execute_steps Loop

**Kanban**: #1751 (Executor Checkpointing — continued)
**Sacred Fire Priority**: 13
**Long Man Step**: BUILD (recursive — migration script created by #715, executor wiring skipped)

## Context

The checkpoint tables migration script was created by Jr #715. Now wire the existing `_record_step_result()` and `_step_already_succeeded()` methods into the `execute_steps()` loop.

## Steps

### Step 1: Add checkpoint logic to the step execution loop

File: `jr_executor/task_executor.py`

```python
<<<<<<< SEARCH
        for step in steps:
            result = self.execute(step)
            results.append(result)

            # Phase 10: Register completed step for potential rollback
            if result.get('success') and saga_tx and self.saga_manager:
=======
        for step_index, step in enumerate(steps):
            # Phase 11: Check if step already succeeded (retry idempotency)
            task_id = getattr(self, '_current_task_id', None)
            if task_id and self._step_already_succeeded(task_id, step_index):
                print(f"[CHECKPOINT] Step {step_index} already succeeded, skipping")
                results.append({'success': True, 'skipped': True, 'checkpoint_hit': True})
                continue

            import time as _time
            _step_start = _time.time()
            result = self.execute(step)
            _step_elapsed_ms = int((_time.time() - _step_start) * 1000)
            results.append(result)

            # Phase 11: Record step result for checkpoint tracking
            if task_id:
                self._record_step_result(
                    task_id=task_id,
                    step_number=step_index,
                    step_type=step.get('type', 'unknown'),
                    target_file=step.get('path', step.get('filepath', '')),
                    result=result,
                    execution_time_ms=_step_elapsed_ms,
                )

            # Phase 10: Register completed step for potential rollback
            if result.get('success') and saga_tx and self.saga_manager:
>>>>>>> REPLACE
```

## Verification

```text
python3 -c "
with open('/ganuda/jr_executor/task_executor.py') as f:
    content = f.read()
assert 'step_index, step in enumerate(steps)' in content, 'enumerate not wired'
assert '_step_already_succeeded' in content.split('execute_steps')[1][:2000], 'checkpoint check not in loop'
assert '_record_step_result' in content.split('execute_steps')[1][:2000], 'step recording not in loop'
print('OK: Checkpointing wired into execute_steps loop')
"
```

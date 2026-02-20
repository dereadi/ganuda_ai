# Jr Instruction: Wire saga_transactions.py into Task Executor

**Task:** Integrate the existing SagaTransactionManager into the Jr task executor for rollback capability
**Priority:** P3
**Assigned:** Software Engineer Jr.
**Use RLM:** false

## Context

`/ganuda/lib/saga_transactions.py` (801 lines) is fully implemented with:
- `SagaTransactionManager` class (line 402)
- `SagaContext` context manager (line 719)
- `CompensatingAction` dataclass
- `Transaction` three-state model (S_A, S_O, S_D)
- Database tables: `council_saga_transactions`, `council_compensation_registry`

But it is **never imported** by task_executor.py. This instruction wires it in.

## Step 1: Add import to task_executor.py

File: `/ganuda/jr_executor/task_executor.py`

```python
<<<<<<< SEARCH
import json
import os
import re
=======
import json
import os
import re
from lib.saga_transactions import SagaTransactionManager
>>>>>>> REPLACE
```

## Step 2: Initialize saga manager in __init__

File: `/ganuda/jr_executor/task_executor.py`

Add after the momentum learner initialization inside `__init__`:

```python
<<<<<<< SEARCH
        self.momentum_learner = JrMomentumLearner()
=======
        self.momentum_learner = JrMomentumLearner()
        try:
            self.saga_manager = SagaTransactionManager()
        except Exception as e:
            print(f"[SAGA] Init failed (non-fatal): {e}")
            self.saga_manager = None
>>>>>>> REPLACE
```

## Step 3: Begin transaction before step execution

File: `/ganuda/jr_executor/task_executor.py`

Find the `execute_steps` method (line 196). Add transaction begin before the step loop:

```python
<<<<<<< SEARCH
    def execute_steps(self, steps: List[Dict]) -> List[Dict[str, Any]]:
        """Execute a list of steps."""
        step_results = []
=======
    def execute_steps(self, steps: List[Dict]) -> List[Dict[str, Any]]:
        """Execute a list of steps."""
        step_results = []
        saga_tx = None
        if self.saga_manager:
            try:
                saga_tx = self.saga_manager.begin_transaction(
                    query_id=str(getattr(self, '_current_task_id', 'unknown')),
                    audit_hash='',
                    query=f"execute_steps: {len(steps)} steps",
                    domain='engineering'
                )
            except Exception as e:
                print(f"[SAGA] Begin transaction failed (non-fatal): {e}")
>>>>>>> REPLACE
```

## Step 4: Register compensation after each successful step

File: `/ganuda/jr_executor/task_executor.py`

In the `execute_steps` loop, after each step executes successfully, register compensation. Find the loop body where step results are appended:

```python
<<<<<<< SEARCH
            step_results.append(result)
            if not result.get('success') and step.get('critical', True):
                break
=======
            step_results.append(result)
            if result.get('success') and saga_tx and self.saga_manager:
                try:
                    self.saga_manager.execute_operation(
                        saga_tx,
                        operation_type=step.get('type', 'unknown'),
                        specialist='task_executor',
                        execute_fn=lambda: result,
                        compensation_data={'step_index': len(step_results) - 1, 'step': step}
                    )
                except Exception:
                    pass
            if not result.get('success') and step.get('critical', True):
                break
>>>>>>> REPLACE
```

## Step 5: Rollback on critical failure, commit on success

File: `/ganuda/jr_executor/task_executor.py`

After the step loop completes, add saga finalization:

```python
<<<<<<< SEARCH
        return step_results
=======
        all_success = all(r.get('success') for r in step_results)
        if saga_tx and self.saga_manager:
            try:
                if all_success:
                    self.saga_manager.commit(saga_tx)
                    print(f"[SAGA] Transaction committed: {saga_tx.transaction_id}")
                else:
                    self.saga_manager.rollback(saga_tx)
                    print(f"[SAGA] Transaction rolled back: {saga_tx.transaction_id}")
            except Exception as e:
                print(f"[SAGA] Finalization error (non-fatal): {e}")
        return step_results
>>>>>>> REPLACE
```

## Verification

After applying all edits, verify:

```text
cd /ganuda && python -c "
from jr_executor.task_executor import TaskExecutor
te = TaskExecutor()
print(f'saga_manager: {te.saga_manager}')
print('Saga integration OK' if te.saga_manager else 'Saga init failed (check DB)')
"
```

## Notes

- All saga operations are wrapped in try/except so failures are non-fatal
- The saga manager depends on database connectivity (council_saga_transactions table)
- This is a **Phase 1 integration** — compensation handlers (file undo, SQL reverse) are NOT yet registered. That's a future task.
- The saga manager logs all operations for post-hoc audit

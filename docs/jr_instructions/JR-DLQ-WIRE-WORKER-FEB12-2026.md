# Jr Instruction: Wire DLQ into jr_queue_worker.py Failure Path

**Kanban**: #1750 (Executor DLQ Wiring — continued)
**Sacred Fire Priority**: 13
**Long Man Step**: BUILD (recursive — migration script created by #714, wiring skipped)

## Context

The DLQ table migration script was created by Jr #714. Now wire the DLQ into the worker failure path.

## Steps

### Step 1: Replace dead-end failure handling with DLQ routing

File: `jr_executor/jr_queue_worker.py`

```python
<<<<<<< SEARCH
                        else:
                            error_msg = result.get('error', 'Unknown error')
                            print(f"[{self.jr_name}] Task failed: {error_msg}")
                            # Mark as failed explicitly
                            self.client.fail_task(task['id'], error_msg, result)  # Use integer id
                    except Exception as task_error:
                        # Task execution error - mark as FAILED, not skip
                        error_msg = f"Task execution error: {task_error}"
                        print(f"[{self.jr_name}] {error_msg}")
                        traceback.print_exc()
                        try:
                            self.client.fail_task(task['id'], error_msg)  # Use integer id
                        except Exception as mark_error:
                            print(f"[{self.jr_name}] Could not mark task as failed: {mark_error}")
=======
                        else:
                            error_msg = result.get('error', 'Unknown error')
                            print(f"[{self.jr_name}] Task failed: {error_msg}")
                            # DLQ integration: route failures for retry + escalation
                            try:
                                sys.path.insert(0, '/ganuda')
                                from jr_executor.dlq_manager import send_to_dlq
                                dlq_id = send_to_dlq(
                                    task_id=task['id'],
                                    failure_reason=error_msg,
                                    failure_traceback=result.get('traceback'),
                                )
                                print(f"[{self.jr_name}] Task {task['id']} routed to DLQ (entry {dlq_id})")
                            except Exception as dlq_err:
                                print(f"[{self.jr_name}] DLQ routing failed ({dlq_err}), falling back to fail_task")
                                self.client.fail_task(task['id'], error_msg, result)
                    except Exception as task_error:
                        # Task execution error - route through DLQ for retry
                        error_msg = f"Task execution error: {task_error}"
                        print(f"[{self.jr_name}] {error_msg}")
                        traceback.print_exc()
                        try:
                            sys.path.insert(0, '/ganuda')
                            from jr_executor.dlq_manager import send_to_dlq
                            send_to_dlq(
                                task_id=task['id'],
                                failure_reason=error_msg,
                                failure_traceback=traceback.format_exc(),
                            )
                        except Exception as dlq_err:
                            print(f"[{self.jr_name}] DLQ routing failed ({dlq_err}), falling back to fail_task")
                            try:
                                self.client.fail_task(task['id'], error_msg)
                            except Exception as mark_error:
                                print(f"[{self.jr_name}] Could not mark task as failed: {mark_error}")
>>>>>>> REPLACE
```

## Verification

```text
python3 -c "
import sys; sys.path.insert(0, '/ganuda')
with open('/ganuda/jr_executor/jr_queue_worker.py') as f:
    content = f.read()
assert 'send_to_dlq' in content, 'DLQ not wired'
print('OK: jr_queue_worker.py has DLQ routing')
"
```

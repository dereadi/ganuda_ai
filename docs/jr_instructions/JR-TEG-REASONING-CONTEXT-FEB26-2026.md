# Jr Instruction: TEG Reasoning Context — Parent Context Flow + DLQ Augmented Retry

**Task**: TEG Reasoning Interrupts (AgentOS Diamond 2, Gecko + Eagle Eye insights)
**Assigned To**: Software Engineer Jr.
**Priority**: P2 (architecture)
**Date**: 2026-02-26

## Context

When TEG decomposes a parent task into child nodes, zero semantic context flows from parent to children. When a child fails and gets DLQ requeued, it replays the original instructions blind — no failure analysis, no correction suggestions. The retry-with-reflection system exists for single tasks but is NOT wired into TEG children. This instruction adds two capabilities:
1. Parent reasoning context flows to children via parameters JSONB
2. DLQ requeue augments instructions with failure context (like single-task retries do)

## Step 1: Add parent context to TEG child parameters

File: `/ganuda/jr_executor/teg_planner.py`

```
<<<<<<< SEARCH
                # Build parameters
                node_params = json.dumps({
                    'teg_node_id': node['node_id'],
                    'teg_parent_id': parent_id,
                    'teg_deps': node['deps'],
                    'teg_target_file': node['filepath'],
                    'teg_op_type': node['op_type']
                })
=======
                # Build parameters with parent reasoning context
                node_params = json.dumps({
                    'teg_node_id': node['node_id'],
                    'teg_parent_id': parent_id,
                    'teg_deps': node['deps'],
                    'teg_target_file': node['filepath'],
                    'teg_op_type': node['op_type'],
                    'teg_parent_title': parent_title[:200],
                    'teg_parent_instruction': task.get('instruction_file', ''),
                    'teg_total_nodes': len(dag)
                })
>>>>>>> REPLACE
```

## Step 2: Capture sibling failure context in fail hook

When a TEG child fails, capture the error details so downstream siblings and DLQ retries can access them.

File: `/ganuda/jr_executor/jr_queue_client.py`

```
<<<<<<< SEARCH
    def _teg_child_fail_hook(self, task_id: int):
        """When a TEG child fails, cancel downstream dependents and fail parent."""
        rows = self._execute("""
            SELECT parent_task_id, parameters FROM jr_work_queue WHERE id = %s
        """, (task_id,))
        if not rows:
            return
        row = rows[0]
        parent_id = row['parent_task_id']
        params = row['parameters']
        if not parent_id:
            return
        params = json.loads(params) if isinstance(params, str) else (params or {})
        my_node_id = params.get('teg_node_id')
        if not my_node_id:
            return
=======
    def _teg_child_fail_hook(self, task_id: int):
        """When a TEG child fails, capture context, cancel downstream dependents, fail parent."""
        rows = self._execute("""
            SELECT parent_task_id, parameters, error_message FROM jr_work_queue WHERE id = %s
        """, (task_id,))
        if not rows:
            return
        row = rows[0]
        parent_id = row['parent_task_id']
        params = row['parameters']
        error_msg = row.get('error_message', '') or ''
        if not parent_id:
            return
        params = json.loads(params) if isinstance(params, str) else (params or {})
        my_node_id = params.get('teg_node_id')
        if not my_node_id:
            return

        # Store failure context on parent for sibling awareness
        try:
            parent_rows = self._execute("""
                SELECT parameters FROM jr_work_queue WHERE id = %s
            """, (parent_id,))
            if parent_rows:
                p_params = parent_rows[0]['parameters']
                p_params = json.loads(p_params) if isinstance(p_params, str) else (p_params or {})
                failures = p_params.get('teg_failures', {})
                failures[my_node_id] = {
                    'task_id': task_id,
                    'error': error_msg[:500],
                    'target_file': params.get('teg_target_file', ''),
                    'op_type': params.get('teg_op_type', '')
                }
                p_params['teg_failures'] = failures
                self._execute("""
                    UPDATE jr_work_queue SET parameters = %s WHERE id = %s
                """, (json.dumps(p_params), parent_id), fetch=False)
        except Exception:
            pass  # Context capture is non-critical
>>>>>>> REPLACE
```

## Step 3: Augment DLQ requeue with failure context for TEG children

File: `/ganuda/jr_executor/jr_queue_client.py`

```
<<<<<<< SEARCH
    def requeue_from_dlq(self, task_id: int) -> bool:
        """Re-queue a failed task by resetting its status to pending."""
        try:
            self._execute("""
                UPDATE jr_work_queue
                SET status = 'pending',
                    error_message = NULL,
                    started_at = NULL,
                    completed_at = NULL,
                    progress_percent = 0,
                    status_message = 'Re-queued from DLQ'
                WHERE id = %s
            """, (task_id,), fetch=False)
            return True
        except Exception as e:
            print(f"[JrQueue] Failed to requeue task {task_id} from DLQ: {e}")
            return False
=======
    def requeue_from_dlq(self, task_id: int) -> bool:
        """Re-queue a failed task by resetting its status to pending.
        For TEG children, augments instruction_content with failure context."""
        try:
            # Check if this is a TEG child — if so, augment with failure context
            rows = self._execute("""
                SELECT parameters, error_message, instruction_file
                FROM jr_work_queue WHERE id = %s
            """, (task_id,))
            retry_context = ''
            if rows:
                params = rows[0]['parameters']
                params = json.loads(params) if isinstance(params, str) else (params or {})
                if params.get('teg_node_id'):
                    prev_error = rows[0].get('error_message', '') or ''
                    target_file = params.get('teg_target_file', '')
                    retry_context = (
                        f"\n\n## RETRY CONTEXT (DLQ Requeue)\n\n"
                        f"This task previously failed with error:\n"
                        f"```\n{prev_error[:1000]}\n```\n\n"
                        f"Target file: `{target_file}`\n"
                        f"Read the actual file content before applying SEARCH/REPLACE.\n"
                        f"If the SEARCH string does not match, read the file and adapt.\n"
                    )

            self._execute("""
                UPDATE jr_work_queue
                SET status = 'pending',
                    error_message = NULL,
                    started_at = NULL,
                    completed_at = NULL,
                    progress_percent = 0,
                    status_message = %s
                WHERE id = %s
            """, (
                'Re-queued from DLQ' + (' (TEG augmented)' if retry_context else ''),
                task_id
            ), fetch=False)

            # If we have retry context, append to instruction_content
            if retry_context:
                self._execute("""
                    UPDATE jr_work_queue
                    SET instruction_content = COALESCE(instruction_content, '') || %s
                    WHERE id = %s
                """, (retry_context, task_id), fetch=False)
                print(f"[TEG] Augmented task {task_id} with DLQ retry context")

            return True
        except Exception as e:
            print(f"[JrQueue] Failed to requeue task {task_id} from DLQ: {e}")
            return False
>>>>>>> REPLACE
```

## Verification

After applying:

1. **Parent context flow**: Create a TEG task. Child parameters should now include `teg_parent_title`, `teg_parent_instruction`, and `teg_total_nodes`.
2. **Failure context capture**: Force-fail a TEG child. Parent's parameters JSONB should have `teg_failures` dict with the failed node's error, target file, and op type.
3. **DLQ augmented retry**: Requeue a failed TEG child from DLQ. Its `instruction_content` should now include a "RETRY CONTEXT" section with the previous error and guidance to read the actual file.

## Notes

- All changes are additive to parameters JSONB — no schema changes needed
- Failure context capture is wrapped in try/except — non-critical path
- DLQ augmentation only triggers for TEG children (checks `teg_node_id` in params)
- Non-TEG tasks requeue unchanged (backward compatible)
- The augmented retry context tells the executor to read the file before applying SR — this is the key insight that prevents stale SEARCH string failures on retry

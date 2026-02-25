# TEG Worker Wiring — Intercept + Child Completion Hooks

**Task**: Wire TEG planner into the Jr executor pipeline
**Priority**: P0 — Sacred Fire 90
**Council Vote**: #ec088d89 — PROCEED WITH CAUTION (0.843)
**Depends on**: JR-TEG-PLANNER-CREATE-FEB25-2026.md (teg_planner.py must exist)

---

## Overview

Two surgical edits:
1. **jr_queue_worker.py**: Intercept `teg_plan=true` tasks before execution, call TEG planner
2. **jr_queue_client.py**: When a TEG child completes/fails, unblock dependents and auto-complete/fail the parent

---

## Edit 1: TEG Intercept in Worker

File: `/ganuda/jr_executor/jr_queue_worker.py`

<<<<<<< SEARCH
                    try:
                        result = self.executor.process_queue_task(task)

                        # P0 FIX Jan 27, 2026: Defense in depth - validate work was done
=======
                    try:
                        # TEG intercept: expand teg_plan tasks before execution
                        # Council Vote #ec088d89 — OpenSage Diamond 1
                        _params = task.get('parameters') or {}
                        if isinstance(_params, str):
                            _params = json.loads(_params) if 'json' in dir() else __import__('json').loads(_params)
                        if _params.get('teg_plan') and not _params.get('teg_expanded'):
                            try:
                                from teg_planner import TEGPlanner
                                _planner = TEGPlanner()
                                _expanded = _planner.expand_task(task)
                                if _expanded:
                                    print(f"[{self.jr_name}] TEG expanded task {task['id']} into child nodes")
                                    time.sleep(2)  # Brief pause before next poll
                                    continue  # Parent now blocked, poll for children
                            except Exception as _teg_err:
                                print(f"[{self.jr_name}] TEG expansion failed ({_teg_err}), falling through to normal execution")
                                import traceback as _tb
                                _tb.print_exc()
                            # If expansion failed, fall through to normal execution

                        result = self.executor.process_queue_task(task)

                        # P0 FIX Jan 27, 2026: Defense in depth - validate work was done
>>>>>>> REPLACE

---

## Edit 2: TEG Child Completion Hook in Queue Client

File: `/ganuda/jr_executor/jr_queue_client.py`

<<<<<<< SEARCH
            except Exception:
                pass  # completion tracking is non-critical

            return True
        except Exception as e:
            print(f"[JrQueue] Failed to complete task: {e}")
            return False

    def fail_task(self, task_id: int, error_message: str, result: Dict = None) -> bool:
=======
            except Exception:
                pass  # completion tracking is non-critical

            # TEG child completion hook: unblock dependents + check parent
            # Council Vote #ec088d89 — OpenSage Diamond 1
            try:
                self._teg_child_hook(task_id)
            except Exception:
                pass  # TEG tracking is non-critical

            return True
        except Exception as e:
            print(f"[JrQueue] Failed to complete task: {e}")
            return False

    def _teg_child_hook(self, task_id: int):
        """When a TEG child completes, unblock dependents and check parent."""
        # Get this task's TEG metadata
        rows = self._execute("""
            SELECT parent_task_id, parameters FROM jr_work_queue WHERE id = %s
        """, (task_id,))
        if not rows:
            return
        parent_id, params = rows[0]
        if not parent_id:
            return
        params = json.loads(params) if isinstance(params, str) else (params or {})
        my_node_id = params.get('teg_node_id')
        if not my_node_id:
            return  # Not a TEG child

        # Unblock siblings whose deps include my node_id
        siblings = self._execute("""
            SELECT id, parameters FROM jr_work_queue
            WHERE parent_task_id = %s AND status = 'blocked'
        """, (parent_id,))

        for sib_id, sib_params in (siblings or []):
            sp = json.loads(sib_params) if isinstance(sib_params, str) else (sib_params or {})
            deps = sp.get('teg_deps', [])
            if my_node_id not in deps:
                continue
            # Check if ALL deps for this sibling are now completed
            all_done = True
            for dep_node_id in deps:
                dep_rows = self._execute("""
                    SELECT status FROM jr_work_queue
                    WHERE parent_task_id = %s
                      AND parameters->>'teg_node_id' = %s
                """, (parent_id, dep_node_id))
                if not dep_rows or dep_rows[0][0] != 'completed':
                    all_done = False
                    break
            if all_done:
                self._execute("""
                    UPDATE jr_work_queue SET status = 'pending',
                        status_message = 'TEG: dependencies resolved, unblocked'
                    WHERE id = %s
                """, (sib_id,), fetch=False)
                print(f"[TEG] Unblocked node {sib_id} (all deps resolved)")

        # Check if ALL children of parent are complete
        remaining = self._execute("""
            SELECT COUNT(*) FROM jr_work_queue
            WHERE parent_task_id = %s AND status NOT IN ('completed', 'cancelled')
        """, (parent_id,))
        if remaining and remaining[0][0] == 0:
            # All children done — auto-complete the parent
            self._execute("""
                UPDATE jr_work_queue SET status = 'completed',
                    progress_percent = 100,
                    completed_at = NOW(),
                    status_message = 'TEG: all child nodes completed'
                WHERE id = %s
            """, (parent_id,), fetch=False)
            print(f"[TEG] Parent task {parent_id} auto-completed (all children done)")

    def _teg_child_fail_hook(self, task_id: int):
        """When a TEG child fails, cancel downstream dependents and fail parent."""
        rows = self._execute("""
            SELECT parent_task_id, parameters FROM jr_work_queue WHERE id = %s
        """, (task_id,))
        if not rows:
            return
        parent_id, params = rows[0]
        if not parent_id:
            return
        params = json.loads(params) if isinstance(params, str) else (params or {})
        my_node_id = params.get('teg_node_id')
        if not my_node_id:
            return

        # Cancel any blocked siblings that depend on me
        siblings = self._execute("""
            SELECT id, parameters FROM jr_work_queue
            WHERE parent_task_id = %s AND status = 'blocked'
        """, (parent_id,))

        cancelled = []
        for sib_id, sib_params in (siblings or []):
            sp = json.loads(sib_params) if isinstance(sib_params, str) else (sib_params or {})
            deps = sp.get('teg_deps', [])
            if my_node_id in deps:
                self._execute("""
                    UPDATE jr_work_queue SET status = 'cancelled',
                        status_message = %s
                    WHERE id = %s
                """, (
                    f'TEG: cancelled — dependency {my_node_id} failed',
                    sib_id
                ), fetch=False)
                cancelled.append(sib_id)
                print(f"[TEG] Cancelled node {sib_id} (dependency {my_node_id} failed)")

        # Check remaining active children
        remaining = self._execute("""
            SELECT COUNT(*) FROM jr_work_queue
            WHERE parent_task_id = %s AND status NOT IN ('completed', 'cancelled', 'failed')
        """, (parent_id,))

        if remaining and remaining[0][0] == 0:
            # No more active children — fail the parent with summary
            completed = self._execute("""
                SELECT COUNT(*) FROM jr_work_queue
                WHERE parent_task_id = %s AND status = 'completed'
            """, (parent_id,))
            total = self._execute("""
                SELECT COUNT(*) FROM jr_work_queue
                WHERE parent_task_id = %s
            """, (parent_id,))

            c_count = completed[0][0] if completed else 0
            t_count = total[0][0] if total else 0

            self._execute("""
                UPDATE jr_work_queue SET status = 'failed',
                    completed_at = NOW(),
                    error_message = %s,
                    status_message = 'TEG: partial failure'
                WHERE id = %s
            """, (
                f'TEG partial failure: {c_count}/{t_count} nodes completed. '
                f'Failed node: {my_node_id}. Cancelled: {cancelled}',
                parent_id
            ), fetch=False)
            print(f"[TEG] Parent {parent_id} failed ({c_count}/{t_count} nodes completed)")

    def fail_task(self, task_id: int, error_message: str, result: Dict = None) -> bool:
>>>>>>> REPLACE

---

## Edit 3: Wire Fail Hook into fail_task

File: `/ganuda/jr_executor/jr_queue_client.py`

<<<<<<< SEARCH
            self._execute("""
                UPDATE jr_work_queue
                SET status = 'failed',
                    completed_at = NOW(),
                    error_message = %s,
                    result = %s,
                    status_message = 'Task failed'
                WHERE id = %s AND assigned_jr = %s
            """, (
                error_message,
                json.dumps(result) if result else None,
                task_id,
                self.jr_name
            ), fetch=False)
            return True
        except Exception as e:
            print(f"[JrQueue] Failed to mark task failed: {e}")
            return False

    def block_task(self, task_id: int, reason: str) -> bool:
=======
            self._execute("""
                UPDATE jr_work_queue
                SET status = 'failed',
                    completed_at = NOW(),
                    error_message = %s,
                    result = %s,
                    status_message = 'Task failed'
                WHERE id = %s AND assigned_jr = %s
            """, (
                error_message,
                json.dumps(result) if result else None,
                task_id,
                self.jr_name
            ), fetch=False)

            # TEG child failure hook: cancel dependents + check parent
            try:
                self._teg_child_fail_hook(task_id)
            except Exception:
                pass  # TEG tracking is non-critical

            return True
        except Exception as e:
            print(f"[JrQueue] Failed to mark task failed: {e}")
            return False

    def block_task(self, task_id: int, reason: str) -> bool:
>>>>>>> REPLACE

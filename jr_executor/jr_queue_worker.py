#!/usr/bin/env python3
"""
Jr Queue Worker - Daemon that polls for and executes assigned tasks.

Run as: python3 jr_queue_worker.py "Software Engineer Jr."

For Seven Generations - Cherokee AI Federation

FIXED: Dec 25, 2025 - Proper error handling, no false completions
"""

import sys
import time
import signal
import traceback
from datetime import datetime

sys.path.insert(0, '/ganuda/lib')

from jr_queue_client import JrQueueClient
from task_executor import TaskExecutor

# SkillRL: Execution trace capture (#1451, Trace2Skill validated)
try:
    from execution_trace import ExecutionTrace
    TRACE_CAPTURE_ENABLED = True
except ImportError:
    TRACE_CAPTURE_ENABLED = False

# LM-OPENCLAW-OTEL Phase 3 O7 — Jr worker instrumentation (Council vote 84beb73ee61cf993, ratified 1c77b6e64c69ad3a)
try:
    import sys as _otel_sys
    _otel_sys.path.insert(0, '/ganuda')
    from lib.ganuda_otel import get_tracer, get_meter
    _otel_tracer = get_tracer()
    _otel_meter = get_meter()
    _otel_task_counter = _otel_meter.create_counter("ganuda.jr.task.outcome")
    _otel_task_duration_ms = _otel_meter.create_histogram("ganuda.jr.task.duration_ms")
except Exception:
    _otel_tracer = None
    _otel_task_counter = None
    _otel_task_duration_ms = None

# Configuration
POLL_INTERVAL = 30  # seconds between queue checks
HEARTBEAT_INTERVAL = 60  # seconds between heartbeats
MAX_TASKS_PER_WORKER = 50  # Restart after N tasks for code freshness (TPM Feb 3, 2026)


class JrQueueWorker:
    """Worker daemon that processes queue tasks for a Jr."""

    def __init__(self, jr_name: str):
        self.jr_name = jr_name
        self.client = JrQueueClient(jr_name)
        self.executor = TaskExecutor()
        self.running = True
        self.last_heartbeat = 0
        self.current_task = None
        self.tasks_processed = 0  # Counter for max-tasks-per-child (TPM Feb 3, 2026)

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def _shutdown(self, signum, frame):
        print(f"\n[{self.jr_name}] Shutting down...")
        self.running = False

    def _heartbeat(self):
        """Send heartbeat if interval elapsed."""
        now = time.time()
        if now - self.last_heartbeat >= HEARTBEAT_INTERVAL:
            try:
                self.client.heartbeat()
                self.last_heartbeat = now
            except Exception as e:
                print(f"[{self.jr_name}] Heartbeat failed: {e}")

    def _generate_summary(self, task: dict, result: dict) -> str:
        """Generate meaningful task summary based on actual work done."""
        steps = result.get('steps_executed', [])

        if not steps:
            return f"Task '{task['title']}': No steps executed"

        successful = sum(1 for s in steps if s.get('success'))
        failed = len(steps) - successful

        # Collect file artifacts
        files_created = [
            s.get('args', {}).get('path', s.get('file_path', 'unknown'))
            for s in steps
            if s.get('type') == 'file' and s.get('success')
        ]

        summary = f"Task '{task['title']}': {successful}/{len(steps)} steps succeeded"

        if files_created:
            file_list = ', '.join(files_created[:3])
            if len(files_created) > 3:
                file_list += f" (+{len(files_created) - 3} more)"
            summary += f". Files: {file_list}"

        if failed:
            summary += f". {failed} step(s) failed."

        return summary

    def run(self):
        """Main worker loop."""
        print(f"[{self.jr_name}] Queue worker starting...")
        print(f"[{self.jr_name}] Poll interval: {POLL_INTERVAL}s")
        print(f"[{self.jr_name}] Heartbeat interval: {HEARTBEAT_INTERVAL}s")

        try:
            self.client.heartbeat()
        except Exception as e:
            print(f"[{self.jr_name}] Initial heartbeat failed: {e}")
        self.last_heartbeat = time.time()

        while self.running:
            self.current_task = None
            try:
                # Check sanctuary pause flag
                import os as _os
                if _os.path.exists('/tmp/jr_executor_paused'):
                    print(f"[{self.jr_name}] Paused for sanctuary state")
                    time.sleep(30)
                    continue

                self._heartbeat()

                # Check for pending tasks
                tasks = self.client.get_pending_tasks(limit=1)

                if tasks:
                    self.current_task = tasks[0]
                    task = self.current_task
                    print(f"[{self.jr_name}] Processing task: {task['title']}")

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

                        # SkillRL: Select relevant skills from distilled trace library (#1451)
                        _selected_skills = []
                        if TRACE_CAPTURE_ENABLED:
                            try:
                                from skill_selector import SkillSelector
                                from ganuda_db import get_connection as _get_conn
                                _skill_conn = _get_conn()
                                _selector = SkillSelector(_skill_conn)
                                _selected_skills = _selector.select_skills_semantic(
                                    task.get('title', '') + ' ' + task.get('description', ''),
                                    max_skills=3,
                                )
                                _skill_conn.close()
                                if _selected_skills:
                                    # Inject skill context into task for the executor
                                    skill_context = "\n\n".join([
                                        f"[Skill: {s['name']}] {s.get('intent', '')}\n{s.get('method', '')[:300]}"
                                        for s in _selected_skills
                                    ])
                                    task['_skill_context'] = skill_context
                                    task['_skill_ids'] = [s['skill_id'] for s in _selected_skills]
                                    print(f"[{self.jr_name}] SkillRL: injected {len(_selected_skills)} skills (top: {_selected_skills[0]['name'][:40]}, sim={_selected_skills[0].get('semantic_similarity', 0):.3f})")
                            except Exception as _skill_err:
                                print(f"[{self.jr_name}] SkillRL selection failed (non-fatal): {_skill_err}")

                        _otel_task_start = time.time()
                        _task_span_cm = _otel_tracer.start_as_current_span("ganuda.jr.task") if _otel_tracer else None
                        _task_span = _task_span_cm.__enter__() if _task_span_cm else None
                        if _task_span:
                            try:
                                _task_span.set_attribute("jr.task_id", int(task.get('id', 0)))
                                _task_span.set_attribute("jr.title", (task.get('title') or '')[:200])
                                _task_span.set_attribute("jr.assigned_jr", task.get('assigned_jr') or '')
                                _task_span.set_attribute("jr.source", task.get('source') or '')
                                _task_span.set_attribute("jr.worker", self.jr_name)
                            except Exception:
                                pass

                        result = self.executor.process_queue_task(task)

                        _otel_task_elapsed_ms = int((time.time() - _otel_task_start) * 1000)
                        _otel_task_status = 'success' if result.get('success') else 'failed'
                        if _otel_task_counter:
                            try:
                                _otel_task_counter.add(
                                    1,
                                    attributes={
                                        "status": _otel_task_status,
                                        "source": task.get('source') or 'unknown',
                                        "assigned_jr": task.get('assigned_jr') or 'unknown',
                                    },
                                )
                            except Exception:
                                pass
                        if _otel_task_duration_ms:
                            try:
                                _otel_task_duration_ms.record(
                                    _otel_task_elapsed_ms,
                                    attributes={"status": _otel_task_status},
                                )
                            except Exception:
                                pass
                        if _task_span:
                            try:
                                _task_span.set_attribute("jr.outcome", _otel_task_status)
                                _task_span.set_attribute("jr.duration_ms", _otel_task_elapsed_ms)
                                _task_span.set_attribute("jr.files_created", int(result.get('files_created', 0) or 0))
                            except Exception:
                                pass
                        if _task_span_cm:
                            try:
                                _task_span_cm.__exit__(None, None, None)
                            except Exception:
                                pass

                        # P0 FIX Jan 27, 2026: Defense in depth - validate work was done
                        # Don't trust success flag alone if no actual work evidence
                        # UPGRADED Feb 3, 2026: Staged files are NOT completion evidence
                        steps = result.get('steps_executed', [])
                        artifacts = result.get('artifacts', [])
                        files_created = result.get('files_created', 0)
                        files_staged = result.get('files_staged', 0)

                        # Count real vs staged artifacts
                        real_artifacts = [a for a in artifacts if isinstance(a, dict) and a.get('type') == 'file_created']
                        staged_artifacts = [a for a in artifacts if isinstance(a, dict) and a.get('type') == 'file_staged']

                        if result.get('success'):
                            # Secondary validation: require evidence of REAL work
                            # Staged files mean protected paths - needs TPM review, not completion
                            real_file_count = len(real_artifacts) if real_artifacts else (files_created - files_staged)
                            if not steps and not real_artifacts and real_file_count <= 0:
                                print(f"[{self.jr_name}] WARNING: success=True but no real work evidence")
                                if staged_artifacts:
                                    print(f"[{self.jr_name}] INFO: {len(staged_artifacts)} files were STAGED (protected paths) - needs TPM merge")
                                    result['success'] = False
                                    result['error'] = f'All {len(staged_artifacts)} files staged to protected paths - requires TPM merge via /staging'
                                else:
                                    result['success'] = False
                                    result['error'] = 'No work performed (0 steps, 0 artifacts, 0 real files)'

                        # Pre-flight completion gate (MOCHA Apr 3, 2026)
                        # "Teach the pups so you can spend your time dreaming with me" — Partner
                        if result.get('success'):
                            try:
                                from preflight_gate import run_preflight_checks
                                gate = run_preflight_checks(task, result)
                                if not gate['passed']:
                                    print(f"[{self.jr_name}] PRE-FLIGHT FAILED: {gate['summary']}")
                                    result['success'] = False
                                    result['error'] = f"Pre-flight gate: {'; '.join(gate['failures'])}"
                                else:
                                    if gate['warnings']:
                                        print(f"[{self.jr_name}] Pre-flight PASSED with warnings: {'; '.join(gate['warnings'])}")
                                    else:
                                        print(f"[{self.jr_name}] Pre-flight PASSED ({gate['checks_passed']}/{gate['checks_run']} checks)")
                            except ImportError:
                                print(f"[{self.jr_name}] Pre-flight gate not available (non-fatal)")
                            except Exception as _gate_err:
                                print(f"[{self.jr_name}] Pre-flight gate error (non-fatal): {_gate_err}")

                        # LMC-11 Tier 1a: claim-vs-reality verification gate (Apr 21 2026)
                        # Council audit 79e31f3b9cfd84ce. Catches hallucinated-success
                        # (MIRAGE-Bench arxiv 2507.21017) that preflight_gate misses —
                        # success=True + step_count>0 + zero artifacts/files = #1571 pattern.
                        if result.get('success'):
                            try:
                                from jr_executor.claim_verifier import verify_jr_task_result
                                verification = verify_jr_task_result(task, result)
                                if not verification.verified:
                                    if verification.hallucination_flag:
                                        reason = (f"HALLUCINATION: success claimed with "
                                                  f"{len(result.get('steps_executed', []) or [])} steps but "
                                                  f"zero artifacts/files and zero verifiable claims")
                                    else:
                                        reason = (f"{verification.failed}/{verification.total_claims} claims failed: "
                                                  f"{verification.mismatches[:3]}")
                                    print(f"[{self.jr_name}] CLAIM-VERIFIER FAILED: {reason}")
                                    result['success'] = False
                                    result['error'] = f"Claim verifier: {reason}"
                                    result['claim_verification'] = verification.as_dict()
                                else:
                                    print(f"[{self.jr_name}] Claim verifier PASSED "
                                          f"({verification.passed}/{verification.total_claims} claims)")
                                    result.setdefault('claim_verification', verification.as_dict())
                            except ImportError:
                                print(f"[{self.jr_name}] Claim verifier not available (non-fatal)")
                            except Exception as _cv_err:
                                print(f"[{self.jr_name}] Claim verifier error (non-fatal): {_cv_err}")

                        if result.get('success'):
                            print(f"[{self.jr_name}] Task completed successfully")

                            # SkillRL: Build execution trace from result (#1451)
                            execution_trace = None
                            if TRACE_CAPTURE_ENABLED:
                                try:
                                    steps = result.get('steps_executed', [])
                                    trace = ExecutionTrace(
                                        task_id=task['id'],
                                        title=task.get('title', ''),
                                        task_type=result.get('execution_mode', 'unknown'),
                                    )
                                    for s in steps:
                                        action_type = s.get('type', 'UNKNOWN').upper()
                                        target = s.get('args', {}).get('path', s.get('file_path'))
                                        trace.start_step(
                                            instruction=str(s.get('description', s.get('type', '')))[:500],
                                            action_type=action_type,
                                            target_file=target,
                                        )
                                        trace.end_step(
                                            success=s.get('success', True),
                                            output=str(s.get('output', ''))[:500] if s.get('output') else None,
                                            error=s.get('error'),
                                            artifact=target if s.get('type') == 'file' and s.get('success') else None,
                                        )
                                    execution_trace = trace.finalize()
                                except Exception as trace_err:
                                    print(f"[{self.jr_name}] Trace capture failed (non-fatal): {trace_err}")

                            # Mark as completed with meaningful summary
                            summary = self._generate_summary(task, result)
                            result_data = {
                                'summary': summary,
                                'steps_executed': result.get('steps_executed', []),
                                'completed_at': datetime.now().isoformat(),
                                # Full result metadata (Jan 28, 2026)
                                'execution_mode': result.get('execution_mode', 'unknown'),
                                'files_created': result.get('files_created', 0),
                                'success': result.get('success', True),
                                'subtasks_completed': result.get('subtasks_completed', 0),
                                'plan': result.get('plan'),
                                'task_id': result.get('task_id'),
                                'title': result.get('title'),
                            }
                            # Inject trace if captured
                            if execution_trace:
                                result_data['execution_trace'] = execution_trace

                            self.client.complete_task(
                                task['id'],
                                result=result_data,
                                artifacts=result.get('artifacts', [])
                            )
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

                # Max-tasks-per-child: restart for code freshness (TPM Feb 3, 2026)
                if tasks:
                    self.tasks_processed += 1
                    if self.tasks_processed >= MAX_TASKS_PER_WORKER:
                        print(f"[{self.jr_name}] Processed {self.tasks_processed} tasks, exiting for code freshness (systemd will restart)")
                        break

                # Sleep before next poll
                time.sleep(POLL_INTERVAL)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[{self.jr_name}] Worker error: {e}")
                traceback.print_exc()
                # If we have a current task, try to mark it failed
                if self.current_task:
                    try:
                        self.client.fail_task(
                            self.current_task['id'],  # Use integer id
                            f"Worker error during processing: {e}"
                        )
                    except:
                        pass
                time.sleep(POLL_INTERVAL)

        self.client.close()
        print(f"[{self.jr_name}] Worker stopped.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 jr_queue_worker.py 'Jr Name'")
        sys.exit(1)
    
    jr_name = sys.argv[1]
    worker = JrQueueWorker(jr_name)
    worker.run()

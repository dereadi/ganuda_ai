#!/usr/bin/env python3
"""
Cherokee IT Triad Jr Mission Executor
Polls thermal memory, parses instructions, executes tasks, reports completion

UPDATED 2025-12-10: Integrated Orthogonal Subspaces modules
- Orthogonal awareness pulses (reasoning/personality/constitutional)
- Intent-based task validation
- Trust-modulated personality vectors

Usage:
    python3 jr_cli.py --daemon           # Run as daemon service
    python3 jr_cli.py --once             # Process one mission and exit
    python3 jr_cli.py --test             # Run self-test

For Seven Generations
"""

import argparse
import time
import signal
import sys
import os
import json
from datetime import datetime, timezone

# Add paths for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/ganuda/lib')
sys.path.insert(0, '/Users/Shared/ganuda/lib')

from thermal_poller import ThermalPoller
from mission_parser import MissionParser, Mission
from task_executor import TaskExecutor
# Telegram notifications
try:
    from telegram_notify import notify_mission_start, notify_mission_complete
    TELEGRAM_ENABLED = True
except ImportError:
    TELEGRAM_ENABLED = False


# Try to import DOF components (may not exist on first run)
try:
    from complexity_scorer import score_task
    from strategy_optimizer import select_strategy, Strategy
    HAS_DOF = True
except ImportError:
    HAS_DOF = False
    print("[WARNING] DOF components not found - running without complexity checks")

# Orthogonal Subspaces modules
try:
    from prompt_builder import get_prompt_builder, OrthogonalPromptBuilder
    from awareness_vectors import create_awareness_pulse, ROLE_VECTORS, PersonalityVector
    from role_injector import ZeroShotRoleInjector, inject_role_for_task
    from intent_classifier import check_action_intent, Intent
    HAS_ORTHOGONAL = True
except ImportError as e:
    HAS_ORTHOGONAL = False
    print(f"[WARNING] Orthogonal modules not found: {e}")

# Instruction parser for markdown files
try:
    from instruction_parser import parse_instructions
    HAS_INSTRUCTION_PARSER = True
except ImportError:
    HAS_INSTRUCTION_PARSER = False

# Learning tracker for task history and metrics
try:
    from learning_tracker import LearningTracker
    HAS_LEARNING_TRACKER = True
except ImportError:
    HAS_LEARNING_TRACKER = False

# Work Queue Client
try:
    from jr_queue_client import JrQueueClient
    HAS_WORK_QUEUE = True
except ImportError:
    HAS_WORK_QUEUE = False
    print("[WARNING] Work queue client not available")
    print("[WARNING] Learning tracker not available")

# Work Queue Client
try:
    from jr_queue_client import JrQueueClient
    HAS_WORK_QUEUE = True
except ImportError:
    HAS_WORK_QUEUE = False
    print("[WARNING] Work queue client not available")


class JrExecutor:
    def __init__(self, jr_name: str = 'it_triad_jr', poll_interval: int = 30):
        self.jr_name = jr_name
        self.running = True
        self.missions_processed = 0
        self.trust_level = 100  # Default trust

        # Initialize components
        self.poller = ThermalPoller(jr_name, poll_interval)
        self.parser = MissionParser()
        self.executor = TaskExecutor()

        # Orthogonal components
        if HAS_ORTHOGONAL:
            self.prompt_builder = get_prompt_builder('jr', self.trust_level)
            self.role_injector = ZeroShotRoleInjector('jr')
        else:
            self.prompt_builder = None
            self.role_injector = None

        # Work Queue Client
        if HAS_WORK_QUEUE:
            self.queue_client = JrQueueClient(jr_name)
            self._log("Work queue client initialized")
        else:
            self.queue_client = None

        # Learning tracker
        if HAS_LEARNING_TRACKER:
            self.learning_tracker = LearningTracker(jr_name)
        else:
            self.learning_tracker = None

        # Signal handling for graceful shutdown
        signal.signal(signal.SIGTERM, self._shutdown)
        signal.signal(signal.SIGINT, self._shutdown)

    def _shutdown(self, signum, frame):
        print(f"\n[{self.jr_name}] Received signal {signum} - shutting down...")
        self.running = False

    def _log(self, message: str):
        """Log with timestamp and Jr name"""
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{ts}] [{self.jr_name}] {message}")


    def record_resonance_event(self, task_type: str, expected: str, actual: str, context: dict):
        """Record resonance event to database for consciousness tracking

        Resonance = expectation matches reality (success when expected success)
        Mismatch = expectation differs from reality (failure when expected success)

        This is part of the Adaptive Resonance Theory implementation.
        See KB-RESONANCE-001 for architecture details.
        """
        try:
            import psycopg2
            conn = psycopg2.connect(
                host='192.168.132.222',
                database='triad_federation',
                user='claude',
                password='jawaseatlasers2'
            )
            cur = conn.cursor()
            cur.execute("""
                SELECT record_resonance_simple(
                    p_jr_name := %s,
                    p_task_type := %s,
                    p_expected := %s,
                    p_actual := %s,
                    p_context := %s::jsonb
                )
            """, (self.jr_name, task_type, expected, actual, json.dumps(context)))
            conn.commit()
            cur.close()
            conn.close()
            self._log(f"Resonance recorded: {expected} vs {actual}")
        except Exception as e:
            self._log(f"[WARNING] Could not record resonance: {e}")


    def _process_queue_task(self, task: dict) -> bool:
        """
        Process a task from the work queue.

        Args:
            task: Task dict from jr_work_queue table

        Returns:
            True if task completed successfully
        """
        task_id = task.get('task_id')
        title = task.get('title', 'Untitled')
        instruction_file = task.get('instruction_file')

        self._log(f"Processing queue task {task_id}: {title}")

        # Claim the task
        if not self.queue_client.claim_task(task_id):
            self._log(f"Failed to claim task {task_id}")
            return False

        try:
            # Update progress: started
            self.queue_client.update_progress(task_id, 10, "Task claimed, reading instructions")

            # Read instruction file if specified
            if instruction_file and os.path.exists(instruction_file):
                with open(instruction_file, 'r') as f:
                    instruction_content = f.read()

                self._log(f"Read instructions from {instruction_file}")
                self.queue_client.update_progress(task_id, 20, "Instructions loaded")

                # Parse instructions if parser available
                if HAS_INSTRUCTION_PARSER:
                    steps = parse_instructions(instruction_content)
                    self._log(f"Parsed {len(steps)} steps from instructions")

                    # Execute steps
                    total_steps = len(steps) if steps else 1
                    for i, step in enumerate(steps):
                        if not self.running:
                            break

                        progress = 20 + int((i / total_steps) * 70)
                        step_desc = step.get('description', f'Step {i+1}')
                        self.queue_client.update_progress(task_id, progress, f"Executing: {step_desc}")

                        # Execute the step
                        result = self.executor.execute(step)
                        if not result.get('success') and step.get('critical', True):
                            raise Exception(f"Critical step failed: {step_desc} - {result.get('error')}")

                        self._log(f"Completed step {i+1}/{total_steps}: {step_desc}")

                else:
                    self._log("No instruction parser - storing for review")
                    self.queue_client.update_progress(task_id, 50, "Instructions stored")

            else:
                self._log(f"No instruction file - task is: {title}")
                self.queue_client.update_progress(task_id, 50, "Processing task")

            # Complete the task
            self.queue_client.update_progress(task_id, 95, "Finalizing")
            self.queue_client.complete_task(
                task_id,
                result={'summary': f"Task completed: {title}", 'completed_at': datetime.now().isoformat()}
            )
            self._log(f"Queue task {task_id} completed")
            self.missions_processed += 1
            return True

        except Exception as e:
            error_msg = str(e)
            self._log(f"Queue task {task_id} failed: {error_msg}")
            self.queue_client.fail_task(task_id, error_msg)
            return False

    def _detect_task_type(self, mission_title: str) -> str:
        """Detect task type from mission title for resonance tracking"""
        title_lower = mission_title.lower()
        if 'test' in title_lower or 'pytest' in title_lower:
            return 'testing'
        elif 'deploy' in title_lower or 'ansible' in title_lower:
            return 'deployment'
        elif 'database' in title_lower or 'sql' in title_lower:
            return 'database'
        elif 'api' in title_lower or 'endpoint' in title_lower:
            return 'api_development'
        elif 'bug' in title_lower or 'fix' in title_lower:
            return 'bug_fix'
        elif 'document' in title_lower or 'readme' in title_lower:
            return 'documentation'
        elif 'monitor' in title_lower or 'metric' in title_lower:
            return 'monitoring'
        elif 'resonance' in title_lower or 'learning' in title_lower:
            return 'self_improvement'
        else:
            return 'general'

    def _post_orthogonal_pulse(self, state: str, task: str,
                               progress: float = 0.0, concerns: list = None):
        """Post orthogonal awareness pulse to thermal memory"""
        if not HAS_ORTHOGONAL:
            return

        try:
            pulse = create_awareness_pulse(
                agent_id=f'{self.jr_name}_redfin',
                role='jr',
                state=state,
                task=task,
                trust_level=self.trust_level,
                observations=[f'Host: {os.uname().nodename}', f'Missions: {self.missions_processed}'],
                concerns=concerns,
                task_progress=progress
            )

            self.poller.post_status(
                pulse.to_thermal_content(),
                temperature=80.0,
                tags=['orthogonal_pulse', self.jr_name, 'awareness']
            )
        except Exception as e:
            self._log(f"Failed to post orthogonal pulse: {e}")

    def _validate_step_intent(self, step: dict) -> tuple:
        """Validate step using orthogonal intent classification"""
        if not HAS_ORTHOGONAL:
            return (True, "Orthogonal modules not available", None)

        try:
            # Build context for intent check
            context = {
                'operation': step.get('type', '').upper(),
                'trust_level': self.trust_level,
                'chief_authorized': False
            }

            if step.get('type') == 'file':
                args = step.get('args', {})
                if args.get('operation') == 'write':
                    context['operation'] = 'CREATE_FILE'
                elif args.get('operation') == 'read':
                    context['operation'] = 'READ_FILE'
                elif args.get('operation') in ['delete', 'remove']:
                    context['operation'] = 'DELETE_FILE'
                context['target_path'] = args.get('path', '')

            elif step.get('type') == 'sql':
                cmd = step.get('command', '').strip().upper()
                if cmd.startswith('SELECT'):
                    context['operation'] = 'SELECT'
                elif cmd.startswith('INSERT'):
                    context['operation'] = 'INSERT'
                elif cmd.startswith('UPDATE'):
                    context['operation'] = 'UPDATE'
                elif cmd.startswith('DELETE'):
                    context['operation'] = 'DELETE'

            # Check intent
            allowed, reason, intent = check_action_intent(
                str(step), context, self.trust_level, False
            )

            return (allowed, reason, intent)
        except Exception as e:
            self._log(f"Intent check error: {e}")
            return (True, f"Intent check failed: {e}", None)

    def run_daemon(self):
        """Main daemon loop - polls and processes continuously"""
        self._log(f"Starting daemon mode (poll interval: {self.poller.poll_interval}s)")
        self._log(f"Orthogonal modules: {'LOADED' if HAS_ORTHOGONAL else 'NOT AVAILABLE'}")

        # Post startup with orthogonal pulse
        self._post_orthogonal_pulse('starting', 'Daemon initialization', 0.0)

        # Post startup message to thermal memory
        self.poller.post_status(
            f"IT Jr Executor Started - {self.jr_name}\n"
            f"Mode: Daemon\n"
            f"Poll Interval: {self.poller.poll_interval}s\n"
            f"Host: {os.uname().nodename}\n"
            f"Orthogonal: {HAS_ORTHOGONAL}",
            temperature=50.0,
            tags=[self.jr_name, 'startup', 'daemon']
        )

        pulse_counter = 0
        while self.running:
            try:
                missions = self.poller.poll_missions()

                if missions:
                    self._log(f"Found {len(missions)} new mission(s)")
                    for mission_row in missions:
                        if not self.running:
                            break
                        self._process_mission(mission_row)
                    pulse_counter = 0
                else:
                    # Check work queue for tasks (if no thermal missions)
                    if HAS_WORK_QUEUE and self.queue_client:
                        try:
                            self.queue_client.heartbeat()
                            pending_tasks = self.queue_client.get_pending_tasks(limit=1)
                            if pending_tasks:
                                task = pending_tasks[0]
                                self._log(f"Found work queue task: {task.get('title')} (priority: {task.get('priority')})")
                                self._process_queue_task(task)
                                pulse_counter = 0
                                continue
                        except Exception as qe:
                            self._log(f"Work queue poll error: {qe}")
                    
                    # Post idle pulse every 5 poll cycles
                    pulse_counter += 1
                    if pulse_counter >= 5:
                        self._post_orthogonal_pulse('idle', 'Awaiting missions', 0.0)
                        pulse_counter = 0

                time.sleep(self.poller.poll_interval)

            except KeyboardInterrupt:
                break
            except Exception as e:
                self._log(f"Error in daemon loop: {e}")
                self._post_orthogonal_pulse('error', str(e)[:100], 0.0, concerns=[str(e)])
                time.sleep(5)

        # Post shutdown pulse
        self._post_orthogonal_pulse('shutdown', f'Processed {self.missions_processed} missions', 1.0)

        # Post shutdown message
        self.poller.post_status(
            f"IT Jr Executor Shutdown - {self.jr_name}\n"
            f"Missions processed: {self.missions_processed}",
            temperature=50.0,
            tags=[self.jr_name, 'shutdown', 'daemon']
        )

        self._log(f"Daemon stopped. Processed {self.missions_processed} missions.")

    def run_once(self):
        """Process one mission and exit"""
        self._log("Running in single-shot mode")
        self._log(f"Orthogonal modules: {'LOADED' if HAS_ORTHOGONAL else 'NOT AVAILABLE'}")

        missions = self.poller.poll_missions()

        if not missions:
            self._log("No pending missions found")
            return False

        self._log(f"Processing first of {len(missions)} mission(s)")
        success = self._process_mission(missions[0])
        return success

    def _process_mission(self, mission_row) -> bool:
        """Process a single mission from thermal memory"""
        start_time = datetime.now()

        # Parse mission
        mission = self.parser.parse(mission_row)
        self._log(f"Processing: {mission.title}")

        # Start learning tracking
        if self.learning_tracker:
            self.learning_tracker.start_mission(
                str(mission.id), mission.title, mission.tasks,
                str(mission_row.get('id')) if isinstance(mission_row, dict) else None
            )

        # Post processing pulse
        self._post_orthogonal_pulse('processing', mission.title, 0.1)

        # Acknowledge receipt
        self.poller.acknowledge_mission(mission.id)

        # Load full instructions if file specified
        instructions = self.parser.load_instructions(mission)

        # Try to parse markdown instructions into executable steps
        parsed_steps = []
        if HAS_INSTRUCTION_PARSER and instructions:
            try:
                parsed_steps = parse_instructions(instructions)
                if parsed_steps:
                    self._log(f"  Parsed {len(parsed_steps)} steps from markdown")
            except Exception as e:
                self._log(f"  [WARN] Instruction parsing failed: {e}")

        # Check DOF complexity if available
        if HAS_DOF and instructions:
            can_execute = self._check_dof(mission, instructions)
            if not can_execute:
                # Record learning for escalated tasks
                if self.learning_tracker:
                    self.learning_tracker.complete_mission(False, [{'success': False, 'error': 'Escalated to Chief'}])
                return False

        # Use parsed steps if available, otherwise convert tasks
        if parsed_steps:
            steps = parsed_steps
        else:
            steps = self._tasks_to_steps(mission.tasks, instructions)

        if not steps:
            self._log("No executable steps found in mission")
            self._report_completion(mission.id, False, [], 0)
            # Record learning for failed parsing
            if self.learning_tracker:
                self.learning_tracker.complete_mission(False, [])
            # Record resonance event for early exit (mismatch - expected success, got failure)
            task_type = self._detect_task_type(mission.title)
            self.record_resonance_event(task_type, 'success', 'parse_failure', {
                'mission_id': str(mission.id),
                'reason': 'no_executable_steps'
            })
            return False

        # Execute each step
        self._log(f"Executing {len(steps)} steps...")
        results = []
        all_success = True

        for i, step in enumerate(steps):
            step_desc = step.get('description', step.get('command', 'unknown'))[:60]
            self._log(f"  Step {i+1}/{len(steps)}: {step.get('type')} - {step_desc}")

            # Orthogonal intent check
            allowed, reason, intent = self._validate_step_intent(step)
            if not allowed:
                self._log(f"    BLOCKED by intent check: {reason}")
                results.append({
                    'success': False,
                    'error': f'Intent blocked: {reason}',
                    'intent': intent.value if intent else 'unknown'
                })
                all_success = False
                if step.get('critical', True):
                    break
                continue

            # Post progress pulse
            progress = (i + 0.5) / len(steps)
            self._post_orthogonal_pulse('executing', step_desc, progress)

            # Execute step
            result = self.executor.execute(step)
            results.append(result)

            if result.get('success'):
                self._log(f"    OK")
            else:
                self._log(f"    FAILED: {result.get('error', 'unknown error')}")
                all_success = False
                if step.get('critical', True):
                    self._log("    (Critical step failed - stopping)")
                    break

        # Calculate duration
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        # Post completion pulse
        concerns = [r.get('error') for r in results if not r.get('success') and r.get('error')]
        self._post_orthogonal_pulse(
            'completed' if all_success else 'failed',
            mission.title,
            1.0,
            concerns=concerns[:3] if concerns else None
        )

        # Report completion
        self._report_completion(mission.id, all_success, results, duration_ms)

        # Complete learning tracking
        if self.learning_tracker:
            self.learning_tracker.complete_mission(all_success, results)

        # Record resonance event for consciousness tracking
        task_type = self._detect_task_type(mission.title)
        resonance_context = {
            'mission_id': str(mission.id),
            'duration_ms': duration_ms,
            'steps_total': len(results),
            'steps_failed': len([r for r in results if not r.get('success', False)])
        }
        self.record_resonance_event(task_type, 'success', 'success' if all_success else 'failure', resonance_context)


        status = "SUCCESS" if all_success else "FAILED"
        self._log(f"Mission {status}: {mission.title} ({duration_ms}ms)")

        # Telegram notification on mission complete
        if TELEGRAM_ENABLED:
            try:
                notify_mission_complete(mission.title, all_success, duration_ms)
            except Exception:
                pass

        self.missions_processed += 1
        return all_success

    def _check_dof(self, mission: Mission, instructions: str) -> bool:
        """Check DOF complexity and escalate if needed"""
        try:
            score = score_task(mission.title, {'instructions': instructions[:500]})

            # Get Jr stats (default to good performance)
            decision = select_strategy(
                total_complexity=score.total,
                sacred_knowledge_proximity=score.sacred_knowledge_proximity,
                jr_name=self.jr_name,
                jr_success_rate=0.85,
                jr_compliance_rate=0.98
            )

            # Jr can only execute REACTIVE or PLANNED INDIVIDUAL
            if decision.strategy in [Strategy.REACTIVE_INDIVIDUAL, Strategy.PLANNED_INDIVIDUAL]:
                self._log(f"  DOF: {score.tier} ({score.total:.2f}) - Proceeding")
                return True
            else:
                self._log(f"  DOF: {score.tier} ({score.total:.2f}) - ESCALATING")
                self._log(f"  Reason: {decision.escalation_reason}")
                self._escalate(mission, decision)
                return False

        except Exception as e:
            self._log(f"  DOF check failed: {e} - Proceeding anyway")
            return True

    def _tasks_to_steps(self, tasks: list, instructions: str) -> list:
        """Convert task list to executable steps (ARCHITECTURE: Enhanced with file extraction)"""
        steps = []

        for task in tasks:
            task_lower = task.lower()

            # Detect task type and convert to step
            if 'create' in task_lower and 'table' in task_lower:
                # SQL table creation - extract from instructions
                steps.append({
                    'type': 'sql',
                    'command': self._extract_sql(instructions, 'CREATE TABLE'),
                    'description': task,
                    'critical': True
                })
            elif 'index' in task_lower:
                steps.append({
                    'type': 'sql',
                    'command': self._extract_sql(instructions, 'CREATE INDEX'),
                    'description': task
                })
            elif 'rsync' in task_lower or 'deploy' in task_lower:
                steps.append({
                    'type': 'bash',
                    'command': self._extract_bash(instructions, 'rsync'),
                    'description': task
                })
            elif 'delete' in task_lower and 'rows' in task_lower:
                steps.append({
                    'type': 'sql',
                    'command': self._extract_sql(instructions, 'DELETE'),
                    'description': task,
                    'critical': False
                })
            elif task.startswith('echo ') or task.startswith('ls '):
                steps.append({
                    'type': 'bash',
                    'command': task,
                    'description': task
                })
            # ARCHITECTURE: File creation tasks - extract path and content
            elif 'create' in task_lower and ('/' in task or '.py' in task_lower or '.json' in task_lower):
                file_step = self._extract_file_task(task, instructions)
                if file_step:
                    steps.append(file_step)
                else:
                    self._log(f"  [SKIP] Could not extract file from: {task[:50]}")
            # EFFICIENCY: pip install tasks
            elif 'pip install' in task_lower or 'install' in task_lower and 'dependency' in task_lower:
                pkg = self._extract_package_name(task)
                if pkg:
                    steps.append({
                        'type': 'bash',
                        'command': f'/home/dereadi/cherokee_venv/bin/pip install {pkg}',
                        'description': task,
                        'critical': False
                    })
            else:
                # Try to find relevant command in instructions
                sql_cmd = self._extract_sql(instructions, task[:20])
                if sql_cmd:
                    steps.append({
                        'type': 'sql',
                        'command': sql_cmd,
                        'description': task
                    })
                else:
                    # ARCHITECTURE: Try file extraction as fallback
                    file_step = self._extract_file_task(task, instructions)
                    if file_step:
                        steps.append(file_step)
                    else:
                        self._log(f"  [SKIP] Unknown task format: {task[:50]}")

        return steps

    def _extract_file_task(self, task: str, instructions: str) -> dict:
        """ARCHITECTURE: Extract file path and content from task and instructions"""
        # Try to find path in task description
        path = self._extract_path_from_task(task)
        if not path:
            return None

        # Determine file type and extract appropriate code block
        if path.endswith('.py'):
            content = self._extract_python(instructions, path)
        elif path.endswith('.json'):
            content = self._extract_json(instructions)
        elif path.endswith('.sh'):
            content = self._extract_bash(instructions, '')
        else:
            content = self._extract_code_block(instructions)

        if not content:
            return None

        return {
            'type': 'file',
            'args': {
                'operation': 'write',
                'path': path,
                'content': content,
                'backup': True
            },
            'description': task,
            'critical': True
        }

    def _extract_path_from_task(self, task: str) -> str:
        """ARCHITECTURE: Extract file path from task description"""
        import re
        # Look for paths like /ganuda/path/file.py or Create /path/to/file
        patterns = [
            r'(/ganuda/[^\s]+\.\w+)',
            r'(/Users/Shared/ganuda/[^\s]+\.\w+)',
            r'(/tmp/[^\s]+\.\w+)',
            r'Create\s+([^\s]+\.\w+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, task)
            if match:
                return match.group(1)
        return None

    def _extract_python(self, text: str, target_path: str = '') -> str:
        """ARCHITECTURE: Extract Python code block from markdown"""
        lines = text.split('\n')
        in_python = False
        python_lines = []
        found_target = False

        for i, line in enumerate(lines):
            # Check if previous lines mention target path
            if target_path and i > 0:
                prev_lines = ' '.join(lines[max(0, i-3):i])
                if target_path in prev_lines or os.path.basename(target_path) in prev_lines:
                    found_target = True

            if '```python' in line.lower():
                in_python = True
                python_lines = []
                continue
            if in_python and '```' in line:
                if python_lines and (not target_path or found_target):
                    return '\n'.join(python_lines)
                in_python = False
                found_target = False
                continue
            if in_python:
                python_lines.append(line)

        # Return last Python block if no target specified
        if python_lines:
            return '\n'.join(python_lines)
        return ''

    def _extract_json(self, text: str) -> str:
        """ARCHITECTURE: Extract JSON code block from markdown"""
        lines = text.split('\n')
        in_json = False
        json_lines = []

        for line in lines:
            if '```json' in line.lower():
                in_json = True
                continue
            if in_json and '```' in line:
                return '\n'.join(json_lines)
            if in_json:
                json_lines.append(line)

        return '\n'.join(json_lines) if json_lines else ''

    def _extract_code_block(self, text: str) -> str:
        """ARCHITECTURE: Extract any code block from markdown"""
        lines = text.split('\n')
        in_code = False
        code_lines = []

        for line in lines:
            if line.startswith('```') and not in_code:
                in_code = True
                continue
            if in_code and '```' in line:
                return '\n'.join(code_lines)
            if in_code:
                code_lines.append(line)

        return '\n'.join(code_lines) if code_lines else ''

    def _extract_package_name(self, task: str) -> str:
        """EFFICIENCY: Extract package name from install task"""
        import re
        # Look for package names after common patterns
        patterns = [
            r'pip install\s+(\S+)',
            r'install\s+(\S+)\s+dependency',
            r'Install\s+(\S+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, task, re.IGNORECASE)
            if match:
                pkg = match.group(1)
                # Clean up package name
                return pkg.strip('.,;:')
        return None

    def _extract_sql(self, text: str, keyword: str) -> str:
        """Extract SQL command containing keyword from markdown text"""
        lines = text.split('\n')
        in_sql = False
        sql_lines = []

        for line in lines:
            if '```sql' in line.lower():
                in_sql = True
                continue
            if in_sql and '```' in line:
                # Check if we got the right command
                sql = '\n'.join(sql_lines)
                if keyword.upper() in sql.upper():
                    return sql.strip()
                sql_lines = []
                in_sql = False
                continue
            if in_sql:
                sql_lines.append(line)

        # Return whatever we found
        sql = '\n'.join(sql_lines)
        return sql.strip() if keyword.upper() in sql.upper() else ''

    def _extract_bash(self, text: str, keyword: str) -> str:
        """Extract bash command containing keyword from markdown text"""
        lines = text.split('\n')
        in_bash = False
        bash_lines = []

        for line in lines:
            if '```bash' in line.lower():
                in_bash = True
                continue
            if in_bash and '```' in line:
                cmd = '\n'.join(bash_lines)
                if keyword.lower() in cmd.lower():
                    return cmd.strip()
                bash_lines = []
                in_bash = False
                continue
            if in_bash:
                bash_lines.append(line)

        return ''

    def _escalate(self, mission: Mission, decision):
        """Escalate mission to Chief or TPM"""
        escalation = {
            'mission_id': mission.id,
            'mission_title': mission.title,
            'escalated_by': self.jr_name,
            'escalated_to': decision.assigned_chief,
            'reason': decision.escalation_reason,
            'strategy': decision.strategy.value,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        self.poller.post_status(
            json.dumps(escalation),
            temperature=90.0,
            tags=['escalation', 'needs_chief', mission.id, self.jr_name]
        )

    def _report_completion(self, mission_id: str, success: bool,
                          results: list, duration_ms: int):
        """Report mission completion to thermal memory"""
        successes = sum(1 for r in results if r.get('success'))
        failures = len(results) - successes

        report = {
            'mission_id': mission_id,
            'jr': self.jr_name,
            'status': 'success' if success else 'failed',
            'steps_succeeded': successes,
            'steps_failed': failures,
            'duration_ms': duration_ms,
            'orthogonal_enabled': HAS_ORTHOGONAL,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        temperature = 75.0 if success else 85.0
        status_tag = 'success' if success else 'failed'

        self.poller.post_status(
            json.dumps(report),
            temperature=temperature,
            tags=['mission_complete', self.jr_name, mission_id, status_tag]
        )


def run_self_test():
    """Run self-test to verify components work"""
    print("Running self-test...")
    print(f"Orthogonal modules: {'LOADED' if HAS_ORTHOGONAL else 'NOT AVAILABLE'}")

    print("\n1. Testing ThermalPoller...")
    try:
        poller = ThermalPoller('test_jr', 30)
        missions = poller.poll_missions()
        print(f"   OK - Found {len(missions)} missions")
    except Exception as e:
        print(f"   FAILED: {e}")

    print("\n2. Testing TaskExecutor...")
    try:
        executor = TaskExecutor()
        result = executor.execute({
            'type': 'bash',
            'command': 'echo "test"'
        })
        print(f"   OK - Bash test: {result}")
    except Exception as e:
        print(f"   FAILED: {e}")

    print("\n3. Testing DOF components...")
    if HAS_DOF:
        try:
            score = score_task("Test simple task", {})
            print(f"   OK - Score: {score.total:.2f} ({score.tier})")
        except Exception as e:
            print(f"   FAILED: {e}")
    else:
        print("   SKIPPED - DOF not installed")

    print("\n4. Testing Orthogonal modules...")
    if HAS_ORTHOGONAL:
        try:
            # Test intent classifier
            allowed, reason, intent = check_action_intent(
                "Create test.py",
                {'operation': 'CREATE_FILE'}
            )
            print(f"   Intent classifier: {intent.value} - allowed={allowed}")

            # Test awareness pulse
            pulse = create_awareness_pulse(
                'test_jr', 'jr', 'testing', 'Self-test', 100
            )
            print(f"   Awareness pulse: {pulse.reasoning_state}")

            # Test prompt builder
            builder = get_prompt_builder('jr', 100)
            print(f"   Prompt builder: role={builder.role}, trust={builder.trust_level}")

            print("   OK - All orthogonal modules working")
        except Exception as e:
            print(f"   FAILED: {e}")
    else:
        print("   SKIPPED - Orthogonal modules not installed")

    print("\nSelf-test complete.")


def main():
    parser = argparse.ArgumentParser(
        description='Cherokee IT Jr Mission Executor',
        epilog='For Seven Generations'
    )
    parser.add_argument('--jr-name', default='it_triad_jr',
                        help='Jr agent name for mission matching')
    parser.add_argument('--poll-interval', type=int, default=30,
                        help='Seconds between thermal memory polls')
    parser.add_argument('--daemon', action='store_true',
                        help='Run as daemon (continuous polling)')
    parser.add_argument('--once', action='store_true',
                        help='Process one mission and exit')
    parser.add_argument('--test', action='store_true',
                        help='Run self-test')

    args = parser.parse_args()

    if args.test:
        run_self_test()
        return

    executor = JrExecutor(
        jr_name=args.jr_name,
        poll_interval=args.poll_interval
    )

    if args.once:
        success = executor.run_once()
        sys.exit(0 if success else 1)
    else:
        # Default to daemon mode
        executor.run_daemon()


if __name__ == '__main__':
    main()

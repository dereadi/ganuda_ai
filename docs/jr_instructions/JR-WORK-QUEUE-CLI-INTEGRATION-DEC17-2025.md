# JR INSTRUCTIONS: Integrate Work Queue with Jr CLI
## JR-WORK-QUEUE-CLI-INTEGRATION-DEC17-2025
## December 17, 2025

### OBJECTIVE
Add work queue polling to jr_cli.py so Jrs can receive tasks from both thermal memory AND the jr_work_queue table.

---

## BACKGROUND

Currently jr_cli.py polls thermal memory for missions. We want to add a secondary polling source from jr_work_queue which provides:
- Database-backed task queue with priorities
- Progress tracking (0-100%)
- Result/artifact storage
- Sacred fire priority support

---

## TASK 1: Add JrQueueClient import

**File:** /ganuda/jr_executor/jr_cli.py

**Find this section (around line 65-75):**
```python
# Learning tracker for task history and metrics
try:
    from learning_tracker import LearningTracker
    HAS_LEARNING_TRACKER = True
except ImportError:
    HAS_LEARNING_TRACKER = False
    print("[WARNING] Learning tracker not available")
```

**Add after it:**
```python

# Work Queue Client
try:
    from jr_queue_client import JrQueueClient
    HAS_WORK_QUEUE = True
except ImportError:
    HAS_WORK_QUEUE = False
    print("[WARNING] Work queue client not available")
```

---

## TASK 2: Initialize queue client in JrExecutor.__init__

**File:** /ganuda/jr_executor/jr_cli.py

**Find this section in __init__ (around line 95-100):**
```python
        # Learning tracker
        if HAS_LEARNING_TRACKER:
```

**Add before it:**
```python
        # Work Queue Client
        if HAS_WORK_QUEUE:
            self.queue_client = JrQueueClient(jr_name)
            self._log("Work queue client initialized")
        else:
            self.queue_client = None

```

---

## TASK 3: Add work queue polling to daemon loop

**File:** /ganuda/jr_executor/jr_cli.py

**Find the daemon loop section (around line 267-278):**
```python
                missions = self.poller.poll_missions()

                if missions:
                    self._log(f"Found {len(missions)} new mission(s)")
                    for mission_row in missions:
                        if not self.running:
                            break
                        self._process_mission(mission_row)
                    pulse_counter = 0
```

**Replace with:**
```python
                # Poll thermal memory for missions
                missions = self.poller.poll_missions()

                if missions:
                    self._log(f"Found {len(missions)} thermal mission(s)")
                    for mission_row in missions:
                        if not self.running:
                            break
                        self._process_mission(mission_row)
                    pulse_counter = 0

                # Also check work queue for tasks (if no thermal missions)
                elif HAS_WORK_QUEUE and self.queue_client:
                    try:
                        self.queue_client.heartbeat()
                        pending_tasks = self.queue_client.get_pending_tasks(limit=1)
                        if pending_tasks:
                            task = pending_tasks[0]
                            self._log(f"Found work queue task: {task.get('title')} (priority: {task.get('priority')})")
                            self._process_queue_task(task)
                            pulse_counter = 0
                    except Exception as qe:
                        self._log(f"Work queue poll error: {qe}")
```

---

## TASK 4: Add _process_queue_task method

**File:** /ganuda/jr_executor/jr_cli.py

**Add this new method after the _process_mission method (around line 450):**
```python
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
            if instruction_file:
                if not os.path.exists(instruction_file):
                    raise FileNotFoundError(f"Instruction file not found: {instruction_file}")

                with open(instruction_file, 'r') as f:
                    instruction_content = f.read()

                self._log(f"Read instructions from {instruction_file}")
                self.queue_client.update_progress(task_id, 20, "Instructions loaded")

                # Parse instructions if parser available
                if HAS_INSTRUCTION_PARSER:
                    steps = parse_instructions(instruction_content)
                    self._log(f"Parsed {len(steps)} steps from instructions")

                    # Execute steps
                    total_steps = len(steps)
                    for i, step in enumerate(steps):
                        if not self.running:
                            break

                        progress = 20 + int((i / total_steps) * 70)  # 20% to 90%
                        step_desc = step.get('description', f'Step {i+1}')
                        self.queue_client.update_progress(task_id, progress, f"Executing: {step_desc}")

                        # Execute the step
                        result = self.executor.execute_step(step)
                        if not result.get('success') and step.get('critical', True):
                            raise Exception(f"Critical step failed: {step_desc} - {result.get('error')}")

                        self._log(f"Completed step {i+1}/{total_steps}: {step_desc}")

                else:
                    # No parser - store content for manual processing
                    self._log("No instruction parser - storing content as artifact")
                    self.queue_client.update_progress(task_id, 50, "Instructions stored for review")

            else:
                # No instruction file - treat title as the task
                self._log(f"No instruction file - task is: {title}")
                self.queue_client.update_progress(task_id, 50, "Processing task description")

            # Complete the task
            self.queue_client.update_progress(task_id, 95, "Finalizing")
            self.queue_client.complete_task(
                task_id,
                result_summary=f"Task '{title}' completed successfully",
                artifacts={'completed_at': datetime.now().isoformat()}
            )
            self._log(f"Queue task {task_id} completed")
            self.missions_processed += 1
            return True

        except Exception as e:
            error_msg = str(e)
            self._log(f"Queue task {task_id} failed: {error_msg}")
            self.queue_client.fail_task(task_id, error_msg)
            return False
```

---

## TASK 5: Update startup message

**File:** /ganuda/jr_executor/jr_cli.py

**Find the startup status post (around line 254-260):**
```python
        self.poller.post_status(
            f"IT Jr Executor Started - {self.jr_name}\n"
            f"Mode: Daemon\n"
            f"Poll Interval: {self.poller.poll_interval}s\n"
            f"Host: {os.uname().nodename}\n"
            f"Orthogonal: {HAS_ORTHOGONAL}",
```

**Replace with:**
```python
        self.poller.post_status(
            f"IT Jr Executor Started - {self.jr_name}\n"
            f"Mode: Daemon\n"
            f"Poll Interval: {self.poller.poll_interval}s\n"
            f"Host: {os.uname().nodename}\n"
            f"Orthogonal: {HAS_ORTHOGONAL}\n"
            f"WorkQueue: {HAS_WORK_QUEUE}",
```

---

## Verification

```bash
cd /ganuda/jr_executor && grep -c "HAS_WORK_QUEUE" jr_cli.py && grep -c "_process_queue_task" jr_cli.py && echo "Integration verified"
```

Expected output:
```
4
2
Integration verified
```

---

## SUCCESS CRITERIA

1. jr_cli.py imports JrQueueClient
2. JrExecutor initializes queue_client
3. Daemon loop checks work queue when no thermal missions
4. _process_queue_task method exists and handles tasks
5. Startup message includes WorkQueue status

---

## TESTING (After Integration)

```bash
# Add a test task to queue
PGPASSWORD='jawaseatlasers2' psql -h 192.168.132.222 -U claude -d zammad_production -c "
INSERT INTO jr_work_queue (title, assigned_jr, priority, status)
VALUES ('Test Queue Integration', 'Software Engineer Jr.', 3, 'pending');
"

# Start Jr and watch for task pickup
cd /ganuda/jr_executor && /home/dereadi/cherokee_venv/bin/python3 jr_cli.py --once
```

---

*Jr Instructions issued: December 17, 2025*
*For Seven Generations - Cherokee AI Federation*

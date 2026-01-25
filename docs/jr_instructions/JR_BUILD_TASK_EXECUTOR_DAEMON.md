# Jr Task: Build Jr Task Executor Daemon

**Task ID:** task-build-jr-executor-001
**Priority:** P1 (Core Infrastructure)
**Node:** redfin (primary), then deploy to all nodes
**Created:** December 22, 2025
**TPM:** Cherokee AI Federation

---

## Executive Summary

Build a daemon that executes tasks assigned to Jr agents via the Contract Net Protocol bidding system. The executor monitors `jr_task_announcements` for tasks assigned to this agent, executes the corresponding Jr instruction, and reports results back to the database.

---

## Context

The Jr Bidding Daemon (`jr_bidding_daemon.py`) handles the **bidding phase** of task assignment:
1. TPM announces task to `jr_task_announcements` (status='open')
2. Jr agents submit bids to `jr_task_bids`
3. `close_bidding.py` selects winner and updates `assigned_to` (status='assigned')

**Missing piece:** Nothing currently **executes** the assigned tasks. The Jr Task Executor fills this gap.

---

## Architecture

```
jr_task_announcements (status='assigned')
         │
         ▼
  Jr Task Executor Daemon
         │
    ┌────┴────┐
    │         │
    ▼         ▼
Read Jr     Execute
Instruction  Task
    │         │
    └────┬────┘
         │
         ▼
  Update task status
  (completed/failed)
         │
         ▼
  Log to thermal_memory
```

---

## Database Schema

The executor uses these existing tables:

### jr_task_announcements (read/update)
```sql
-- Relevant columns:
task_id VARCHAR PRIMARY KEY
task_type VARCHAR          -- 'research', 'implementation', 'review'
task_content TEXT          -- Full task description
assigned_to VARCHAR        -- Agent ID that won bid
status VARCHAR             -- 'open' → 'assigned' → 'in_progress' → 'completed'/'failed'
result TEXT                -- Execution result (populated by executor)
completed_at TIMESTAMP     -- When task finished
```

### New columns needed (if not present):
```sql
ALTER TABLE jr_task_announcements
ADD COLUMN IF NOT EXISTS started_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS execution_log TEXT,
ADD COLUMN IF NOT EXISTS error_message TEXT;
```

---

## Implementation Specification

### File: `/ganuda/jr_executor/jr_task_executor.py`

### Class: JrTaskExecutor

```python
class JrTaskExecutor:
    """
    Daemon that executes tasks assigned to this Jr agent.

    Lifecycle:
    1. Poll for tasks where assigned_to = self.agent_id AND status = 'assigned'
    2. For each task:
       a. Update status to 'in_progress', set started_at
       b. Load task content/instructions
       c. Execute task based on task_type
       d. Update status to 'completed' or 'failed'
       e. Store result and log execution to thermal memory
    """

    def __init__(self, agent_id: str, node_name: str):
        self.agent_id = agent_id
        self.node_name = node_name
        # ... DB connection, signal handlers

    def get_assigned_tasks(self) -> List[dict]:
        """Get tasks assigned to this agent that haven't started."""
        # SELECT * FROM jr_task_announcements
        # WHERE assigned_to = %s AND status = 'assigned'
        pass

    def start_task(self, task_id: str):
        """Mark task as in_progress."""
        # UPDATE jr_task_announcements
        # SET status = 'in_progress', started_at = NOW()
        # WHERE task_id = %s
        pass

    def execute_task(self, task: dict) -> tuple[bool, str]:
        """
        Execute task based on type.

        Returns:
            (success: bool, result: str)
        """
        task_type = task['task_type']

        if task_type == 'research':
            return self._execute_research_task(task)
        elif task_type == 'implementation':
            return self._execute_implementation_task(task)
        elif task_type == 'review':
            return self._execute_review_task(task)
        else:
            return False, f"Unknown task type: {task_type}"

    def _execute_research_task(self, task: dict) -> tuple[bool, str]:
        """
        Execute research task.

        Research tasks involve:
        - Reading Jr instruction files from /ganuda/docs/jr_instructions/
        - Querying thermal memory for context
        - Making LLM calls via gateway to analyze/summarize
        - Writing findings to /ganuda/docs/research/ or thermal memory
        """
        pass

    def _execute_implementation_task(self, task: dict) -> tuple[bool, str]:
        """
        Execute implementation task.

        Implementation tasks:
        - Read Jr instruction file
        - Execute the steps (may involve subprocess calls)
        - Validate results
        - Report success/failure

        SECURITY: Implementation tasks should be sandboxed.
        Only allow pre-approved operations.
        """
        pass

    def complete_task(self, task_id: str, result: str):
        """Mark task as completed."""
        # UPDATE jr_task_announcements
        # SET status = 'completed', result = %s, completed_at = NOW()
        # WHERE task_id = %s
        pass

    def fail_task(self, task_id: str, error: str):
        """Mark task as failed."""
        # UPDATE jr_task_announcements
        # SET status = 'failed', error_message = %s, completed_at = NOW()
        # WHERE task_id = %s
        pass

    def log_to_thermal_memory(self, task: dict, success: bool, result: str):
        """Store task execution in thermal memory."""
        # INSERT INTO thermal_memory_archive
        # memory_hash, original_content, temperature_score, metadata
        pass

    def run(self):
        """Main daemon loop."""
        while self.running:
            tasks = self.get_assigned_tasks()
            for task in tasks:
                self.start_task(task['task_id'])
                success, result = self.execute_task(task)
                if success:
                    self.complete_task(task['task_id'], result)
                else:
                    self.fail_task(task['task_id'], result)
                self.log_to_thermal_memory(task, success, result)
            time.sleep(POLL_INTERVAL)
```

---

## Task Type Handlers

### Research Tasks

Research tasks query information and produce reports:

```python
def _execute_research_task(self, task: dict) -> tuple[bool, str]:
    """
    Steps:
    1. Parse task_content for research question
    2. Query thermal memory for related context
    3. If task references arXiv, fetch paper summary
    4. Call LLM Gateway to synthesize findings
    5. Write research report to /ganuda/docs/research/
    6. Return summary as result
    """

    # Extract research parameters from task_content
    content = task['task_content']

    # Query thermal memory for context
    context = self._query_thermal_memory(content[:100])

    # Call LLM for analysis
    prompt = f"""Research Task: {content}

    Context from thermal memory:
    {context}

    Provide a structured research summary with:
    1. Key findings
    2. Relevance to Cherokee AI
    3. Recommended next steps
    """

    result = self._call_llm(prompt)

    # Save to research docs
    report_path = f"/ganuda/docs/research/{task['task_id']}_report.md"
    with open(report_path, 'w') as f:
        f.write(f"# Research Report: {task['task_id']}\n\n{result}")

    return True, f"Research complete. Report: {report_path}"
```

### Implementation Tasks

Implementation tasks execute specific changes:

```python
def _execute_implementation_task(self, task: dict) -> tuple[bool, str]:
    """
    Steps:
    1. Parse task_content for instruction file path
    2. Read Jr instruction file
    3. Parse implementation steps
    4. Execute each step (with safety checks)
    5. Validate results
    """

    # Look for instruction file reference
    instruction_path = self._extract_instruction_path(task['task_content'])

    if instruction_path and os.path.exists(instruction_path):
        with open(instruction_path) as f:
            instructions = f.read()

        # Parse and execute steps
        # SECURITY: Only allow whitelisted operations
        steps = self._parse_instructions(instructions)
        results = []

        for step in steps:
            if self._is_safe_operation(step):
                result = self._execute_step(step)
                results.append(result)
            else:
                return False, f"Unsafe operation blocked: {step}"

        return True, f"Completed {len(steps)} steps: {results}"

    return False, "No valid instruction file found"
```

---

## Security Considerations (Crawdad Review)

### Whitelisted Operations

Implementation tasks can only:
1. Read files from `/ganuda/docs/`
2. Write files to `/ganuda/docs/research/`, `/ganuda/docs/reports/`
3. Query thermal_memory_archive (SELECT only)
4. Call LLM Gateway API
5. Execute pre-approved scripts from `/ganuda/scripts/approved/`

### Blocked Operations

- Shell command execution (subprocess)
- Writing to system directories
- Network calls outside Cherokee AI endpoints
- Database writes (except task status updates)
- File deletion

### Sandbox Mode

```python
SAFE_READ_PATHS = [
    '/ganuda/docs/',
    '/ganuda/lib/',
    '/Users/Shared/ganuda/docs/',
]

SAFE_WRITE_PATHS = [
    '/ganuda/docs/research/',
    '/ganuda/docs/reports/',
    '/Users/Shared/ganuda/docs/research/',
]

def _is_safe_operation(self, operation: dict) -> bool:
    """Validate operation against whitelist."""
    op_type = operation.get('type')

    if op_type == 'read_file':
        return any(operation['path'].startswith(p) for p in SAFE_READ_PATHS)

    if op_type == 'write_file':
        return any(operation['path'].startswith(p) for p in SAFE_WRITE_PATHS)

    if op_type == 'llm_call':
        return True  # Gateway handles auth/quota

    if op_type == 'thermal_query':
        return True  # Read-only

    return False
```

---

## Configuration

### Environment Variables

```bash
CHEROKEE_DB_HOST=192.168.132.222
CHEROKEE_DB_NAME=zammad_production
CHEROKEE_DB_USER=claude
CHEROKEE_DB_PASS=jawaseatlasers2
CHEROKEE_GATEWAY_URL=http://192.168.132.223:8080
CHEROKEE_API_KEY=ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5
```

### Constants

```python
POLL_INTERVAL = 30  # seconds between task checks
MAX_TASK_DURATION = 3600  # 1 hour timeout
MAX_CONCURRENT_TASKS = 2  # Limit parallel execution
```

---

## Usage

```bash
# Start executor for a specific agent
python3 /ganuda/jr_executor/jr_task_executor.py jr-redfin-gecko redfin

# Or run alongside bidding daemon
python3 /ganuda/jr_executor/jr_bidding_daemon.py jr-redfin-gecko redfin &
python3 /ganuda/jr_executor/jr_task_executor.py jr-redfin-gecko redfin &
```

---

## Testing

### Test 1: Research Task Execution

```bash
# Create test research task assigned to our agent
PGPASSWORD='jawaseatlasers2' psql -h 192.168.132.222 -U claude -d zammad_production << 'EOF'
INSERT INTO jr_task_announcements
(task_id, task_type, task_content, assigned_to, status)
VALUES
('test-executor-research-001', 'research',
 'Research the thermal memory temperature decay algorithm and summarize its purpose.',
 'jr-redfin-gecko', 'assigned');
EOF

# Start executor
python3 /ganuda/jr_executor/jr_task_executor.py jr-redfin-gecko redfin

# Check results after ~1 minute
PGPASSWORD='jawaseatlasers2' psql -h 192.168.132.222 -U claude -d zammad_production \
  -c "SELECT task_id, status, result FROM jr_task_announcements WHERE task_id = 'test-executor-research-001';"
```

### Test 2: Verify Safety Blocks

```bash
# Try to assign task with unsafe operation (should fail)
# The executor should reject and mark as failed
```

---

## Success Criteria

1. [ ] Executor daemon starts and polls for assigned tasks
2. [ ] Research tasks execute and produce reports
3. [ ] Implementation tasks execute with safety validation
4. [ ] Failed tasks are marked with error messages
5. [ ] All executions logged to thermal_memory
6. [ ] Daemon handles signals (SIGTERM, SIGINT) gracefully
7. [ ] Multiple executors can run on different nodes

---

## Integration with Bidding System

The complete task lifecycle:

```
1. TPM announces task
   └─► jr_task_announcements (status='open')

2. Jr agents bid
   └─► jr_task_bids (composite scores)

3. close_bidding.py selects winner
   └─► jr_task_announcements (status='assigned', assigned_to='jr-xxx')

4. Jr Task Executor picks up task ← THIS COMPONENT
   └─► jr_task_announcements (status='in_progress')

5. Executor completes task
   └─► jr_task_announcements (status='completed', result='...')
   └─► thermal_memory_archive (execution log)
```

---

## Deliverables

1. **Source code**: `/ganuda/jr_executor/jr_task_executor.py`
2. **Unit tests**: `/ganuda/jr_executor/tests/test_executor.py`
3. **DB migration**: Add new columns to jr_task_announcements
4. **Systemd service**: `/etc/systemd/system/jr-executor@.service` (for production)

---

## Related Documents

- `JR_TASK_BIDDING_SYSTEM.md` - Overall bidding architecture
- `jr_bidding_daemon.py` - The bidding half of this system
- `close_bidding.py` - Task assignment script

---

*For Seven Generations - Cherokee AI Federation*

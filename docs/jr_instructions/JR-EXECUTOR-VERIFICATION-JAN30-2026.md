# JR-EXECUTOR-VERIFICATION-JAN30-2026
## Phase 17: Add Verification Executor to Task Executor

**Priority:** P1 — Tasks report success without confirming side effects
**Target Node:** redfin
**Estimated Scope:** ~90 lines added to existing file
**Reference Repos:** MineDojo/Voyager (execute-verify-store), microsoft/clinical-self-verification
**Companion Document:** `ULTRATHINK-JR-EXECUTOR-ARCHITECTURE-FUTURE-JAN30-2026.md`

---

### Background

The task executor currently trusts its own success. If `_execute_sql()` returns `{'success': True}`, the task is marked complete. But:

- An INSERT that returns success might have inserted 0 rows (due to ON CONFLICT DO NOTHING)
- A file write that returns success might have written a syntactically invalid file
- A bash command that returns exit code 0 might not have produced the expected output

The Voyager pattern (MineDojo, 2023) establishes the gold standard: **Execute → Verify with Critic → Store to Skill Library**. Verification is cognitively easier than generation — a smaller/faster model can verify what a larger model generated.

### Key Insight from microsoft/clinical-self-verification

> "Verification exploits the asymmetry between generation and verification — checking if output meets requirements is much simpler than generating the output."

This means verification can use a lightweight check (SQL SELECT, file stat, regex match) rather than calling the LLM again.

### Task: Add `_verify_step_result()` Method

**File to Modify:** `/ganuda/jr_executor/task_executor.py`

#### Step 1: Add Verification Method

Add to the `TaskExecutor` class:

```python
def _verify_step_result(self, step: dict, result: dict) -> dict:
    """
    Phase 17: Verify that a step's execution actually achieved its intent.

    Verification is type-specific:
    - SQL INSERT → SELECT COUNT to confirm rows exist
    - SQL CREATE TABLE → Check table exists in information_schema
    - File write → Check file exists, size > 0, optional syntax check
    - Bash → Check expected output patterns

    Reference: MineDojo/Voyager execute-verify-store pattern

    Returns: {verified: bool, verification_type: str, details: str}
    """
    step_type = step.get('type', 'unknown')
    verification = {
        'verified': False,
        'verification_type': 'none',
        'details': 'No verification available'
    }

    if not result.get('success'):
        verification['details'] = 'Step failed — skipping verification'
        return verification

    try:
        if step_type == 'sql':
            verification = self._verify_sql_step(step, result)
        elif step_type == 'file':
            verification = self._verify_file_step(step, result)
        elif step_type == 'bash':
            verification = self._verify_bash_step(step, result)
        else:
            verification['details'] = f'No verifier for type: {step_type}'
    except Exception as e:
        verification['details'] = f'Verification error: {e}'

    return verification


def _verify_sql_step(self, step: dict, result: dict) -> dict:
    """Verify SQL step executed correctly."""
    command = step.get('command', '').strip().upper()

    # INSERT verification: check rows exist
    if command.startswith('INSERT'):
        import re
        table_match = re.search(r'INSERT\s+INTO\s+(\w+)', step.get('command', ''), re.IGNORECASE)
        if table_match:
            table_name = table_match.group(1)
            verify_result = self._execute_sql({
                'type': 'sql',
                'command': f'SELECT COUNT(*) FROM {table_name}'
            })
            if verify_result.get('success'):
                count = verify_result.get('result', [[0]])[0][0]
                return {
                    'verified': count > 0,
                    'verification_type': 'sql_row_count',
                    'details': f'{table_name}: {count} rows',
                    'row_count': count
                }

    # CREATE TABLE verification: check in information_schema
    if command.startswith('CREATE'):
        table_match = re.search(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)', step.get('command', ''), re.IGNORECASE)
        if table_match:
            table_name = table_match.group(1)
            verify_result = self._execute_sql({
                'type': 'sql',
                'command': f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{table_name}'"
            })
            if verify_result.get('success'):
                exists = verify_result.get('result', [[0]])[0][0] > 0
                return {
                    'verified': exists,
                    'verification_type': 'sql_table_exists',
                    'details': f'Table {table_name} {"exists" if exists else "NOT FOUND"}'
                }

    # UPDATE/DELETE verification: check rowcount
    if command.startswith(('UPDATE', 'DELETE')):
        rowcount = result.get('result', 0)
        return {
            'verified': rowcount > 0,
            'verification_type': 'sql_rowcount',
            'details': f'{rowcount} rows affected'
        }

    # SELECT: always verified if it returned results
    if command.startswith('SELECT'):
        rows = result.get('result', [])
        return {
            'verified': True,
            'verification_type': 'sql_select',
            'details': f'Returned {len(rows)} rows'
        }

    return {'verified': True, 'verification_type': 'sql_passthrough', 'details': 'No specific verifier'}


def _verify_file_step(self, step: dict, result: dict) -> dict:
    """Verify file step executed correctly."""
    import os

    args = step.get('args', {})
    operation = args.get('operation', '')
    path = args.get('path', '') or result.get('path', '')

    if operation == 'write' and path:
        # Check file exists and has content
        if not os.path.exists(path):
            return {
                'verified': False,
                'verification_type': 'file_exists',
                'details': f'File not found after write: {path}'
            }

        file_size = os.path.getsize(path)
        if file_size == 0:
            return {
                'verified': False,
                'verification_type': 'file_size',
                'details': f'File is empty: {path}'
            }

        # Python syntax check
        if path.endswith('.py'):
            try:
                with open(path, 'r') as f:
                    compile(f.read(), path, 'exec')
                return {
                    'verified': True,
                    'verification_type': 'file_syntax',
                    'details': f'{path}: {file_size} bytes, Python syntax OK'
                }
            except SyntaxError as e:
                return {
                    'verified': False,
                    'verification_type': 'file_syntax',
                    'details': f'{path}: Python syntax error at line {e.lineno}: {e.msg}'
                }

        return {
            'verified': True,
            'verification_type': 'file_exists_with_content',
            'details': f'{path}: {file_size} bytes'
        }

    if operation == 'read':
        content = result.get('content', '')
        return {
            'verified': len(content) > 0,
            'verification_type': 'file_read',
            'details': f'Read {len(content)} chars'
        }

    return {'verified': True, 'verification_type': 'file_passthrough', 'details': 'No specific verifier'}


def _verify_bash_step(self, step: dict, result: dict) -> dict:
    """Verify bash step executed correctly."""
    stdout = result.get('stdout', '')
    stderr = result.get('stderr', '')
    returncode = result.get('returncode', -1)

    # Check for common error patterns even with exit code 0
    error_patterns = ['error:', 'fatal:', 'traceback', 'exception:', 'permission denied']
    has_error = any(p in (stdout + stderr).lower() for p in error_patterns)

    if has_error and returncode == 0:
        return {
            'verified': False,
            'verification_type': 'bash_error_in_output',
            'details': f'Exit 0 but error patterns found in output'
        }

    return {
        'verified': returncode == 0,
        'verification_type': 'bash_exit_code',
        'details': f'Exit code: {returncode}, stdout: {len(stdout)} chars'
    }
```

#### Step 2: Wire Into execute() Method

In the `execute()` method (around line 1395), after each step execution, add verification:

```python
    def execute(self, step: Dict) -> Dict:
        """Execute a single step with safety checks"""
        # ... existing forbidden check ...

        try:
            # ... existing execution logic ...
            result = ...  # existing result from _execute_sql/_execute_bash/_execute_file

            # Phase 17: Post-execution verification
            if result.get('success'):
                verification = self._verify_step_result(step, result)
                result['verification'] = verification

                if not verification.get('verified'):
                    print(f"[VERIFY] WARNING: Step succeeded but verification failed: {verification.get('details')}")
                    # Don't override success — log the warning for now
                    # Future: can choose to mark as failure if verification fails
                else:
                    print(f"[VERIFY] Confirmed: {verification.get('details')}")

            return result
```

### What This Does NOT Do (By Design)

- Does NOT mark verified=False as a task failure. Verification is informational in Phase 17.
- Does NOT call the LLM for verification. Uses lightweight checks (file stats, SQL SELECTs, regex).
- Does NOT add latency for simple tasks. Verification queries are sub-millisecond.

### Future Enhancement (Phase 17b)

Once verification data accumulates in the Learning Store, we can:
1. Identify patterns where tasks "succeed" but verification fails (false positives)
2. Upgrade specific verification types from informational to blocking
3. Use LLM-based verification for complex tasks (the Voyager Critic Agent pattern)

### Testing

```bash
# Run any existing Jr task and check for VERIFY log lines
tail -f /ganuda/logs/jr_queue_worker.log | grep VERIFY

# Queue a test SQL task
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
INSERT INTO jr_work_queue (title, description, tags, instruction_content, status, assigned_jr, priority)
VALUES (
    'Test Verification Executor Phase 17',
    'Test that verification runs after SQL INSERT',
    ARRAY['test', 'verification', 'phase-17'],
    E'## Test Verification\n\nInsert a test row and verify:\n\n\`\`\`sql\nINSERT INTO educational_content (title, slug, content_type, content, summary, is_published) VALUES (''Verification Test'', ''verification-test'', ''article'', ''Test content for verification'', ''Testing Phase 17 verification'', true) ON CONFLICT (slug) DO NOTHING;\n\`\`\`',
    'pending',
    'Software Engineer Jr.',
    3
);
"
```

### Files to Modify

| File | Change | Lines Added |
|------|--------|-------------|
| `/ganuda/jr_executor/task_executor.py` | Add `_verify_step_result()`, `_verify_sql_step()`, `_verify_file_step()`, `_verify_bash_step()`, wire into `execute()` | ~90 |

---

*For Seven Generations*

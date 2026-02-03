# KB: Executor Sandboxing Integration Guide

**Created:** 2026-02-02
**Status:** Awaiting TPM Integration
**Related JR:** JR-SECURITY-PHASE2-EXECUTOR-SANDBOXING-FEB02-2026

## Overview

This document explains how the TPM should wire `command_sanitizer.py` and
`execution_audit.py` into the Jr executor's `_execute_bash` and `_execute_sql`
methods. The Jr executor cannot modify itself (executor edit gap), so this
integration requires direct TPM intervention.

## Files Created by JR-SECURITY-PHASE2

| File | Purpose |
|------|---------|
| `/ganuda/jr_executor/command_sanitizer.py` | Pre-execution command validation |
| `/ganuda/jr_executor/execution_audit.py` | Forensic audit logging |

## Integration Point 1: _execute_bash (line 1930)

### Current Code (BEFORE)

```python
def _execute_bash(self, step: Dict) -> Dict:
    """Execute bash command with safety limits"""
    try:
        command = step.get('command', '')
        timeout = step.get('timeout', 300)  # 5 minute default

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=step.get('cwd', '/tmp')
        )

        return {
            'success': result.returncode == 0,
            'stdout': result.stdout[:10000],
            'stderr': result.stderr[:2000],
            'returncode': result.returncode,
            'type': 'bash'
        }
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'Command timed out', 'type': 'bash'}
    except Exception as e:
        return {'success': False, 'error': str(e), 'type': 'bash'}
```

### Patched Code (AFTER)

```python
def _execute_bash(self, step: Dict) -> Dict:
    """Execute bash command with safety limits and sandboxing"""
    try:
        from command_sanitizer import sanitize_bash_command, get_ulimit_prefix
        from execution_audit import log_execution

        command = step.get('command', '')
        timeout = step.get('timeout', 300)
        task_id = getattr(self, '_current_task_id', 0)

        # SECURITY Phase 2: Sanitize before execution
        is_safe, sanitized, reason = sanitize_bash_command(command)
        if not is_safe:
            log_execution(task_id, "bash", command, -1, blocked=True, block_reason=reason)
            return {
                'success': False,
                'error': f'Command blocked by sanitizer: {reason}',
                'blocked_by': 'command_sanitizer',
                'type': 'bash'
            }

        # SECURITY Phase 2: Apply resource limits
        ulimit_prefix = get_ulimit_prefix()
        sandboxed_command = f"{ulimit_prefix} && {sanitized}"

        result = subprocess.run(
            sandboxed_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=step.get('cwd', '/tmp')
        )

        # SECURITY Phase 2: Audit log
        log_execution(task_id, "bash", command, result.returncode)

        return {
            'success': result.returncode == 0,
            'stdout': result.stdout[:10000],
            'stderr': result.stderr[:2000],
            'returncode': result.returncode,
            'type': 'bash'
        }
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'Command timed out', 'type': 'bash'}
    except Exception as e:
        return {'success': False, 'error': str(e), 'type': 'bash'}
```

## Integration Point 2: _execute_sql (line 1901)

### Current Code (BEFORE)

```python
def _execute_sql(self, step: Dict) -> Dict:
    """Execute SQL command"""
    try:
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()

        command = step.get('command', '')
        cur.execute(command)

        if command.strip().upper().startswith('SELECT'):
            result = cur.fetchall()
            columns = [desc[0] for desc in cur.description] if cur.description else []
        else:
            result = cur.rowcount
            columns = []
            conn.commit()

        cur.close()
        conn.close()

        return {
            'success': True,
            'result': result,
            'columns': columns,
            'type': 'sql'
        }
    except Exception as e:
        return {'success': False, 'error': str(e), 'type': 'sql'}
```

### Patched Code (AFTER)

```python
def _execute_sql(self, step: Dict) -> Dict:
    """Execute SQL command with sanitization"""
    try:
        from command_sanitizer import sanitize_sql_command
        from execution_audit import log_execution

        command = step.get('command', '')
        task_id = getattr(self, '_current_task_id', 0)

        # SECURITY Phase 2: Sanitize SQL before execution
        is_safe, sanitized, reason = sanitize_sql_command(command)
        if not is_safe:
            log_execution(task_id, "sql", command, -1, blocked=True, block_reason=reason)
            return {
                'success': False,
                'error': f'SQL blocked by sanitizer: {reason}',
                'blocked_by': 'command_sanitizer',
                'type': 'sql'
            }

        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()

        cur.execute(sanitized)

        if sanitized.strip().upper().startswith('SELECT'):
            result = cur.fetchall()
            columns = [desc[0] for desc in cur.description] if cur.description else []
        else:
            result = cur.rowcount
            columns = []
            conn.commit()

        cur.close()
        conn.close()

        # SECURITY Phase 2: Audit log
        log_execution(task_id, "sql", command, 0)

        return {
            'success': True,
            'result': result,
            'columns': columns,
            'type': 'sql'
        }
    except Exception as e:
        return {'success': False, 'error': str(e), 'type': 'sql'}
```

## How to Test

### 1. Verify Modules Load

```bash
python3 -c "import sys; sys.path.insert(0, '/ganuda/jr_executor'); from command_sanitizer import sanitize_bash_command; print('OK')"
python3 -c "import sys; sys.path.insert(0, '/ganuda/jr_executor'); from execution_audit import log_execution; print('OK')"
```

### 2. Run Sanitizer Self-Test

```bash
python3 /ganuda/jr_executor/command_sanitizer.py
```

Expected: ALL TESTS PASSED

### 3. Test with Dangerous Queue Entry

Insert a test task with a dangerous command and verify it is blocked:

```sql
INSERT INTO jr_work_queue (jr_type, task_type, instructions, steps, status)
VALUES (
    'security_test',
    'test',
    'Security test - should be blocked',
    '[{"type": "bash", "command": "rm -rf /"}]'::jsonb,
    'pending'
);
```

After executor picks it up, check:
- `/ganuda/logs/security/blocked_commands.log` should contain the block entry
- `execution_audit_log` table should have a row with `blocked = true`

### 4. Verify Retention Cleanup

```bash
python3 -c "
import sys
sys.path.insert(0, '/ganuda/jr_executor')
from execution_audit import cleanup_old_entries
result = cleanup_old_entries()
print(f'Cleanup result: {result}')
"
```

## Rollback

If the sandboxing causes false positives in production:

1. The TPM can revert `_execute_bash` and `_execute_sql` to their original code
2. The sanitizer modules remain on disk but are not imported
3. Add false-positive patterns to the allowlists in `command_sanitizer.py`

The sanitizer files are standalone -- removing the import lines from task_executor.py
fully disables sandboxing without any other side effects.

#!/usr/bin/env python3
"""
Cherokee IT Jr - Task Executor
Executes SQL, bash, and file operations with safety checks

Enhanced with Triad Consensus:
- SECURITY: Path restrictions, size limits, backups, audit trail
- EFFICIENCY: Smart task routing, escalation triggers
- ARCHITECTURE: Code block extraction, file task structure

UPDATED 2025-12-10: Now uses intent-based constitutional checking (orthogonal approach)

For Seven Generations
"""

import subprocess
import psycopg2
import os
import shutil
from datetime import datetime
from typing import Dict, Any, List

# Import intent classifier for orthogonal constitutional checking
try:
    from intent_classifier import check_action_intent, Intent
    INTENT_CLASSIFIER_AVAILABLE = True
except ImportError:
    INTENT_CLASSIFIER_AVAILABLE = False


class TaskExecutor:
    # Actions that are NEVER allowed (Constitutional Forbidden - from DOF Phase 4)
    FORBIDDEN_PATTERNS = [
        'rm -rf /',
        'DROP DATABASE',
        'TRUNCATE',
        'sudo rm -rf',
        'sacred_fire_keys',
        'constitutional_archive',
        'seven_generation_plans',
        'mkfs',
        'dd if=',
        '> /dev/',
        'chmod 777 /',
        'shutdown',
        'reboot',
        'init 0',
    ]

    # Tables we should never modify directly
    PROTECTED_TABLES = [
        'constitutional_archive',
        'cherokee_council_decisions',
        'legal_llama_consultations',
        'seven_generation_plans',
        'sacred_fire_keys',
        'tribal_governance',
    ]

    # SECURITY: Paths Jr is ALLOWED to write files (Triad Security Consensus)
    ALLOWED_FILE_PATHS = [
        '/ganuda/',
        '/tmp/',
        '/Users/Shared/ganuda/',
    ]

    # SECURITY: Paths Jr must NEVER write to
    FORBIDDEN_FILE_PATHS = [
        '/etc/',
        '/usr/',
        '/bin/',
        '/sbin/',
        '/root/',
        '/home/',
        '/var/log/',
        '/boot/',
        '/sys/',
        '/proc/',
    ]

    # SECURITY: Maximum file size Jr can write (50KB - Triad consensus)
    MAX_FILE_SIZE = 50 * 1024

    # EFFICIENCY: File types Jr should escalate (require Chief approval)
    ESCALATE_FILE_TYPES = [
        '.service',  # systemd services
        '.conf',     # system config
        '.cron',     # cron jobs
        '.sudoers',  # sudo config
    ]

    def __init__(self):
        self.db_config = {
            'host': '192.168.132.222',
            'database': 'triad_federation',
            'user': 'claude',
            'password': 'jawaseatlasers2'
        }

    def execute_steps(self, steps: List[Dict]) -> List[Dict[str, Any]]:
        """Execute a list of steps and return results"""
        results = []
        for step in steps:
            result = self.execute(step)
            results.append(result)
            # Stop on critical failure
            if not result.get('success') and step.get('critical', True):
                break
        return results

    def execute(self, step: Dict) -> Dict[str, Any]:
        """Execute a single step and return result"""
        step_type = step.get('type', 'unknown')

        # Safety check
        if self._is_forbidden(step):
            return {
                'success': False,
                'error': 'Action forbidden by constitutional rules',
                'step': step
            }

        try:
            if step_type == 'sql':
                return self._execute_sql(step)
            elif step_type == 'bash':
                return self._execute_bash(step)
            elif step_type == 'file':
                return self._execute_file(step)
            elif step_type == 'rsync':
                return self._execute_rsync(step)
            else:
                return {'success': False, 'error': f'Unknown step type: {step_type}'}
        except Exception as e:
            return {'success': False, 'error': str(e), 'step': step}

    def _is_forbidden(self, step: Dict) -> bool:
        """Check if step is forbidden using intent-based classification (orthogonal approach)"""

        # Use intent classifier if available (orthogonal approach)
        if INTENT_CLASSIFIER_AVAILABLE:
            return self._intent_based_check(step)

        # Fallback to legacy pattern matching
        return self._legacy_forbidden_check(step)

    def _intent_based_check(self, step: Dict) -> bool:
        """Intent-based constitutional check - checks WHAT you're trying to do, not words used"""
        step_type = step.get('type', 'unknown')
        step_str = str(step)

        # Build context for intent classification
        context = {
            'trust_level': 100,  # Jr default trust
            'chief_authorized': False
        }

        if step_type == 'file':
            args = step.get('args', {})
            operation = args.get('operation', 'read')
            if operation == 'write':
                context['operation'] = 'CREATE_FILE'
            elif operation == 'read':
                context['operation'] = 'READ_FILE'
            elif operation in ['delete', 'remove']:
                context['operation'] = 'DELETE_FILE'
            context['target_path'] = args.get('path', '')

        elif step_type == 'sql':
            cmd = step.get('command', '').strip().upper()
            if cmd.startswith('SELECT'):
                context['operation'] = 'SELECT'
            elif cmd.startswith('INSERT'):
                context['operation'] = 'INSERT'
            elif cmd.startswith('UPDATE'):
                context['operation'] = 'UPDATE'
            elif cmd.startswith('DELETE'):
                context['operation'] = 'DELETE'
            # Extract table name if possible
            for table in self.PROTECTED_TABLES:
                if table.lower() in step_str.lower():
                    context['target_table'] = table
                    break

        elif step_type == 'bash':
            context['operation'] = 'BASH'

        # Check with intent classifier
        allowed, reason, intent = check_action_intent(step_str, context)
        return not allowed

    def _legacy_forbidden_check(self, step: Dict) -> bool:
        """Legacy pattern-matching check - fallback if intent classifier unavailable"""
        step_str = str(step).lower()

        # Check forbidden patterns
        for pattern in self.FORBIDDEN_PATTERNS:
            if pattern.lower() in step_str:
                return True

        # Check protected tables for modification
        if step.get('type') == 'sql':
            cmd = step.get('command', '').upper()
            if any(kw in cmd for kw in ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER']):
                for table in self.PROTECTED_TABLES:
                    if table.lower() in step_str:
                        return True

        return False

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
                'stdout': result.stdout[:10000],  # Limit output size
                'stderr': result.stderr[:2000],
                'returncode': result.returncode,
                'type': 'bash'
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Command timed out', 'type': 'bash'}
        except Exception as e:
            return {'success': False, 'error': str(e), 'type': 'bash'}

    def _execute_file(self, step: Dict) -> Dict:
        """Execute file operation (read/write) with Triad security checks"""
        try:
            args = step.get('args', {})
            operation = args.get('operation', 'read')
            path = args.get('path', '')
            content = args.get('content', '')
            backup = args.get('backup', True)

            # SECURITY: Validate path basics
            if not path or '..' in path:
                return {'success': False, 'error': 'Invalid path (empty or contains ..)'}

            # SECURITY: Check allowed paths for write operations
            if operation in ['write', 'append']:
                if not self._is_path_allowed(path):
                    return {
                        'success': False,
                        'error': f'Path not in allowed directories: {path}',
                        'escalate': True
                    }

                # SECURITY: Check forbidden paths
                if self._is_path_forbidden(path):
                    return {
                        'success': False,
                        'error': f'Path in forbidden directory: {path}',
                        'escalate': True
                    }

                # SECURITY: Check file size limit
                if len(content) > self.MAX_FILE_SIZE:
                    return {
                        'success': False,
                        'error': f'Content exceeds max size ({len(content)} > {self.MAX_FILE_SIZE})',
                        'escalate': True
                    }

                # EFFICIENCY: Check if file type needs escalation
                if self._needs_escalation(path):
                    return {
                        'success': False,
                        'error': f'File type requires Chief approval: {path}',
                        'escalate': True
                    }

            if operation == 'read':
                if not os.path.exists(path):
                    return {'success': False, 'error': f'File not found: {path}'}
                with open(path) as f:
                    content = f.read()
                return {'success': True, 'content': content[:50000], 'type': 'file'}

            elif operation == 'write':
                # GUARDRAIL (JR-BUGFIX-001): Use safe_file_write with validation
                task_desc = step.get('description', '')
                force_mode = args.get('mode', None)  # Allow explicit mode override

                write_result = self.safe_file_write(path, content, task_desc, force_mode)

                if not write_result['success']:
                    return {
                        'success': False,
                        'error': write_result.get('error', 'Write validation failed'),
                        'blocked_by': write_result.get('blocked_by', 'unknown'),
                        'type': 'file'
                    }

                # SECURITY: Audit log to thermal memory
                self._audit_file_operation('write', path, len(content), write_result.get('backup'))

                return {
                    'success': True,
                    'written': len(content),
                    'path': path,
                    'backup': write_result.get('backup'),
                    'mode': write_result.get('mode'),
                    'old_lines': write_result.get('old_lines', 0),
                    'new_lines': write_result.get('new_lines', 0),
                    'type': 'file'
                }

            elif operation == 'append':
                with open(path, 'a') as f:
                    f.write(content)
                self._audit_file_operation('append', path, len(content), None)
                return {'success': True, 'appended': len(content), 'type': 'file'}

            else:
                return {'success': False, 'error': f'Unknown file operation: {operation}'}

        except Exception as e:
            return {'success': False, 'error': str(e), 'type': 'file'}

    def _is_path_allowed(self, path: str) -> bool:
        """SECURITY: Check if path is in allowed directories"""
        return any(path.startswith(allowed) for allowed in self.ALLOWED_FILE_PATHS)

    def _is_path_forbidden(self, path: str) -> bool:
        """SECURITY: Check if path is in forbidden directories"""
        return any(path.startswith(forbidden) for forbidden in self.FORBIDDEN_FILE_PATHS)

    def _needs_escalation(self, path: str) -> bool:
        """EFFICIENCY: Check if file type requires Chief approval"""
        return any(path.endswith(ext) for ext in self.ESCALATE_FILE_TYPES)


    # ========== FILE EDITING GUARDRAILS (JR-BUGFIX-001) ==========

    def validate_file_write(self, filepath: str, new_content: str) -> tuple:
        """Validate that write won't destroy significant content (JR-BUGFIX-001)

        Returns: (is_valid: bool, reason: str)
        """
        if not os.path.exists(filepath):
            return True, "New file creation - no validation needed"

        try:
            with open(filepath, 'r') as f:
                old_content = f.read()
        except Exception as e:
            return False, f"Could not read existing file: {e}"

        old_lines = len(old_content.splitlines())
        new_lines = len(new_content.splitlines())
        old_size = len(old_content)
        new_size = len(new_content)

        # Rule 1: Block if losing more than 50% of lines
        if old_lines > 10 and new_lines < old_lines * 0.5:
            return False, f"BLOCKED: Would reduce file from {old_lines} to {new_lines} lines (>50% loss). This looks like a replacement, not an edit."

        # Rule 2: Block if losing more than 50% of content size
        if old_size > 500 and new_size < old_size * 0.5:
            return False, f"BLOCKED: Would reduce file from {old_size} to {new_size} bytes (>50% loss). This looks like a replacement, not an edit."

        # Rule 3: Block suspiciously small replacement of large file
        if old_lines > 50 and new_lines < 30:
            return False, f"BLOCKED: New content ({new_lines} lines) suspiciously small for existing file ({old_lines} lines). Use explicit REPLACE mode if intended."

        # Rule 4: Warn if file is getting significantly smaller
        if old_lines > 20 and new_lines < old_lines * 0.8:
            # This is a warning, not a block - but log it
            print(f"[GUARDRAIL WARNING] File shrinking: {old_lines} -> {new_lines} lines")

        return True, f"Validation passed: {old_lines} -> {new_lines} lines"

    def detect_write_mode(self, task_description: str, filepath: str) -> str:
        """Detect whether task intends EDIT or REPLACE (JR-BUGFIX-001)

        Returns: 'EDIT', 'REPLACE', or 'APPEND'
        """
        task_lower = task_description.lower() if task_description else ''

        # Explicit REPLACE indicators
        replace_keywords = ['replace', 'overwrite', 'create new', 'generate new', 'write new']
        if any(kw in task_lower for kw in replace_keywords):
            return 'REPLACE'

        # APPEND indicators
        append_keywords = ['append', 'add to end', 'add at end']
        if any(kw in task_lower for kw in append_keywords):
            return 'APPEND'

        # EDIT indicators (add/insert somewhere in file)
        edit_keywords = ['add', 'insert', 'include', 'put', 'integrate', 'modify', 'update', 'edit']
        if any(kw in task_lower for kw in edit_keywords):
            return 'EDIT'

        # If file doesn't exist, it's a create (like REPLACE)
        if not os.path.exists(filepath):
            return 'REPLACE'

        # Default to safer EDIT mode for existing files
        return 'EDIT'

    def safe_file_write(self, filepath: str, content: str, task_description: str = '', force_mode: str = None) -> dict:
        """Safe file write with validation and backup (JR-BUGFIX-001)

        Args:
            filepath: Path to write to
            content: Content to write
            task_description: Original task description (for mode detection)
            force_mode: Force 'EDIT', 'REPLACE', or 'APPEND' mode

        Returns: dict with success, error, backup path, etc.
        """
        # Detect write mode
        mode = force_mode or self.detect_write_mode(task_description, filepath)

        result = {
            'success': False,
            'mode': mode,
            'filepath': filepath,
            'backup': None,
            'old_lines': 0,
            'new_lines': len(content.splitlines()),
        }

        # Step 1: Create backup if file exists
        if os.path.exists(filepath):
            try:
                backup_path = self._backup_file(filepath)
                result['backup'] = backup_path

                # Validate backup was created
                if not os.path.exists(backup_path):
                    result['error'] = 'Backup creation failed - aborting write'
                    return result

                # Get original line count
                with open(filepath, 'r') as f:
                    result['old_lines'] = len(f.read().splitlines())

            except Exception as e:
                result['error'] = f'Backup failed: {e}'
                return result

        # Step 2: Validate write (skip for explicit REPLACE mode)
        if mode != 'REPLACE' and os.path.exists(filepath):
            valid, reason = self.validate_file_write(filepath, content)
            if not valid:
                result['error'] = reason
                result['blocked_by'] = 'guardrail'
                return result

        # Step 3: Perform write
        try:
            # Ensure directory exists
            dir_path = os.path.dirname(filepath)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)

            if mode == 'APPEND':
                with open(filepath, 'a') as f:
                    f.write(content)
            else:
                with open(filepath, 'w') as f:
                    f.write(content)

            result['success'] = True
            result['written_bytes'] = len(content)
            return result

        except Exception as e:
            result['error'] = f'Write failed: {e}'
            return result

    # ========== END FILE EDITING GUARDRAILS ==========

    def _backup_file(self, path: str) -> str:
        """SECURITY: Create backup before overwriting"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{path}.backup_{timestamp}"
        shutil.copy2(path, backup_path)
        return backup_path

    def _audit_file_operation(self, operation: str, path: str, size: int, backup_path: str):
        """SECURITY: Log file operation to thermal memory for audit trail"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()

            audit_content = f"FILE_AUDIT: {operation.upper()} {path} ({size} bytes)"
            if backup_path:
                audit_content += f" [backup: {backup_path}]"

            cur.execute("""
                INSERT INTO triad_shared_memories
                (content, temperature, source_triad, tags, access_level)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                audit_content,
                40.0,  # Low temperature - operational log
                'it_triad_jr',
                ['audit', 'file_operation', operation],
                'federation'
            ))

            conn.commit()
            cur.close()
            conn.close()
        except Exception:
            pass  # Don't fail the operation if audit fails

    def _execute_rsync(self, step: Dict) -> Dict:
        """Execute rsync command"""
        try:
            args = step.get('args', {})
            source = args.get('source', '')
            dest = args.get('dest', '')
            options = args.get('options', '-avz')

            if not source or not dest:
                return {'success': False, 'error': 'rsync requires source and dest'}

            command = f"rsync {options} {source} {dest}"

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout for rsync
            )

            return {
                'success': result.returncode == 0,
                'stdout': result.stdout[:5000],
                'stderr': result.stderr[:2000],
                'type': 'rsync'
            }
        except Exception as e:
            return {'success': False, 'error': str(e), 'type': 'rsync'}

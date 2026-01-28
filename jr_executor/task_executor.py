#!/usr/bin/env python3
"""
Cherokee IT Jr - Task Executor
Executes SQL, bash, and file operations with safety checks

Enhanced with Triad Consensus:
- SECURITY: Path restrictions, size limits, backups, audit trail
- EFFICIENCY: Smart task routing, escalation triggers
- ARCHITECTURE: Code block extraction, file task structure

UPDATED 2025-12-10: Now uses intent-based constitutional checking (orthogonal approach)
UPDATED 2026-01-17: Phase 3 - Wired JrLLMReasoner for instruction understanding

For Seven Generations
"""

import subprocess
import psycopg2
import os
import sys
import shutil
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add lib to path for reasoner import
sys.path.insert(0, '/ganuda/lib')

# Import intent classifier for orthogonal constitutional checking
try:
    from intent_classifier import check_action_intent, Intent
    INTENT_CLASSIFIER_AVAILABLE = True
except ImportError:
    INTENT_CLASSIFIER_AVAILABLE = False

# Import JrLLMReasoner for instruction understanding (Phase 3)
try:
    from jr_llm_reasoner import get_reasoner_sync
    LLM_REASONER_AVAILABLE = True
    print("[INFO] JrLLMReasoner loaded - using Qwen 32B for instruction understanding")
except ImportError as e:
    LLM_REASONER_AVAILABLE = False
    print(f"[WARN] JrLLMReasoner not available: {e}, falling back to regex parsing")

# Import RLM Executor for recursive task decomposition (Phase 4)
try:
    from rlm_executor import RLMExecutor, RLM_AVAILABLE
    if RLM_AVAILABLE:
        print("[INFO] RLM Executor loaded - recursive task decomposition enabled")
    else:
        print("[WARN] RLM library not installed, recursive execution disabled")
except ImportError as e:
    RLM_AVAILABLE = False
    print(f"[WARN] RLM Executor not available: {e}")

# Import M-GRPO Momentum Learner for self-improvement (Phase 5)
try:
    from jr_momentum_learner import MomentumJrLearner
    MGRPO_AVAILABLE = True
    print("[INFO] M-GRPO Momentum Learner loaded - self-improvement enabled")
except ImportError as e:
    MGRPO_AVAILABLE = False
    print(f"[WARN] M-GRPO not available: {e}")

# Import ICL Dynamics for implicit learning measurement (Phase 6)
try:
    from icl_dynamics import ICLDynamicsMeasurer
    ICL_AVAILABLE = True
    print("[INFO] ICL Dynamics loaded - implicit learning measurement enabled")
except ImportError as e:
    ICL_AVAILABLE = False
    print(f"[WARN] ICL Dynamics not available: {e}")

# Import Learning Store for recording execution outcomes (Phase 7)
try:
    from jr_learning_store import JrLearningStore
    LEARNING_STORE_AVAILABLE = True
    print("[INFO] JrLearningStore loaded - execution learning enabled")
except ImportError as e:
    LEARNING_STORE_AVAILABLE = False
    print(f"[WARN] JrLearningStore not available: {e}")

# Import Research Task Executor for web research tasks (Phase 8 - Jan 22, 2026)
try:
    from research_task_executor import ResearchTaskExecutor, is_research_task
    RESEARCH_EXECUTOR_AVAILABLE = True
    print("[INFO] ResearchTaskExecutor loaded - web research enabled")
except ImportError as e:
    RESEARCH_EXECUTOR_AVAILABLE = False
    print(f"[WARN] ResearchTaskExecutor not available: {e}")


class TaskExecutor:
    # Path validation constants (Phase 9 - Jan 23, 2026 - Council Vote 28d18d80e447505f)
    PLACEHOLDER_PATTERNS = [
        r'/path/to/',
        r'/example/',
        r'<[^>]+>',           # <placeholder>
        r'\$\{[^}]+\}',       # ${variable}
        r'\{\{[^}]+\}\}',     # {{template}}
        r'/your/',
        r'/my/',
        r'TODO',
        r'FIXME',
    ]

    ALLOWED_PATH_PREFIXES = ['/ganuda/', '/tmp/', '/home/dereadi/']

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

    def __init__(self, jr_type: str = "it_triad_jr"):
        self.jr_type = jr_type
        self.db_config = {
            'host': '192.168.132.222',
            'database': 'zammad_production',
            'user': 'claude',
            'password': 'jawaseatlasers2'
        }

        # Phase 5: Initialize M-GRPO momentum learner
        if MGRPO_AVAILABLE:
            self.momentum_learner = MomentumJrLearner(jr_type)
            print(f"[M-GRPO] Momentum learner initialized for {jr_type}")
        else:
            self.momentum_learner = None

        # Phase 7: Initialize learning store for recording outcomes
        if LEARNING_STORE_AVAILABLE:
            self.learning_store = JrLearningStore(jr_name=jr_type)
            print(f"[LEARNING] Learning store initialized for {jr_type}")
        else:
            self.learning_store = None

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

    def _validate_path(self, path: str) -> tuple:
        """
        Validate a file path before any file operations.

        Phase 9 Security Layer (Council Vote 28d18d80e447505f - Crawdad requirement)
        Prevents placeholder paths and directory traversal attacks.

        Args:
            path: The file path to validate

        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        if not path:
            return False, "Empty path"

        # Check for placeholder patterns (LLM hallucination detection)
        for pattern in self.PLACEHOLDER_PATTERNS:
            if re.search(pattern, path, re.IGNORECASE):
                return False, f"Placeholder pattern detected: {pattern}"

        # Require absolute path
        if not path.startswith('/'):
            return False, "Path must be absolute (start with /)"

        # Check allowed directories
        if not any(path.startswith(prefix) for prefix in self.ALLOWED_PATH_PREFIXES):
            return False, f"Path not in allowed directories: {self.ALLOWED_PATH_PREFIXES}"

        # Reject directory traversal
        if '..' in path:
            return False, "Directory traversal (..) not allowed"

        # Reject paths with shell injection characters
        if any(c in path for c in [';', '|', '&', '`', '\n', '\r']):
            return False, "Path contains forbidden shell characters"

        return True, ""

    def _extract_target_file_from_header(self, instructions: str) -> Optional[str]:
        """
        Extract the primary target file from instruction header/metadata.

        Phase 1 of Hybrid Smart Extraction (Council Vote 8f3a1e9f4b86ded5).

        Looks for patterns like:
        - | `/ganuda/lib/file.py` | in markdown tables
        - Files Modified: /path/file in headers
        - **File:** `/path/file.py` in bold headers

        Returns:
            File path if exactly ONE target file found in /ganuda/ or /tmp/, else None.
        """
        # Pattern 1: Markdown table with file path
        # | `/ganuda/lib/file.py` | or | /ganuda/lib/file.py |
        table_pattern = r'\|\s*`?(/(?:ganuda|tmp)/[^\s`|]+)`?\s*\|'

        # Pattern 2: "Files Modified:" or "File:" header
        header_pattern = r'(?:Files?\s+(?:Modified|to\s+Modify)|File):\s*`?(/(?:ganuda|tmp)/[^\s`\n]+)`?'

        # Pattern 3: Bold file reference **File:** `/path`
        bold_pattern = r'\*\*File:\*\*\s*`(/(?:ganuda|tmp)/[^\s`]+)`'

        all_files = set()

        for pattern in [table_pattern, header_pattern, bold_pattern]:
            matches = re.findall(pattern, instructions, re.IGNORECASE)
            for match in matches:
                # Clean the path
                clean_path = match.strip('`').strip()
                # Validate it's a real file path (has extension)
                if '.' in clean_path.split('/')[-1]:
                    all_files.add(clean_path)

        # Only return if exactly ONE file found (unambiguous)
        if len(all_files) == 1:
            target_file = all_files.pop()
            print(f"[SmartExtract] Found single target file: {target_file}")
            return target_file
        elif len(all_files) > 1:
            print(f"[SmartExtract] Multiple files found ({len(all_files)}), cannot auto-attribute")
            return None
        else:
            print("[SmartExtract] No target file found in header")
            return None

    def _extract_file_from_prose(self, text: str) -> Optional[str]:
        """
        Extract file path from prose text before a code block.

        Looks for patterns like:
        - "Modify `/ganuda/lib/file.py`"
        - "Update `/ganuda/lib/file.py`"
        - "In `/ganuda/lib/file.py`, add:"
        - "to `/ganuda/lib/file.py`:"

        Args:
            text: The prose text before a code block (typically 300-500 chars)

        Returns:
            File path if found, else None.
        """
        # Patterns for file paths in prose (with backticks)
        prose_patterns = [
            r'[Mm]odify\s+`(/(?:ganuda|tmp)/[^`]+)`',
            r'[Uu]pdate\s+`(/(?:ganuda|tmp)/[^`]+)`',
            r'[Ii]n\s+`(/(?:ganuda|tmp)/[^`]+)`',
            r'[Tt]o\s+`(/(?:ganuda|tmp)/[^`]+)`',
            r'[Ee]dit\s+`(/(?:ganuda|tmp)/[^`]+)`',
            r'[Ff]ile\s+`(/(?:ganuda|tmp)/[^`]+)`',
        ]

        for pattern in prose_patterns:
            match = re.search(pattern, text)
            if match:
                filepath = match.group(1).strip()
                # Validate it has an extension
                if '.' in filepath.split('/')[-1]:
                    return filepath

        return None

    def _determine_edit_mode(self, preceding_text: str, code_content: str,
                              target_file: str) -> dict:
        """
        Determine the appropriate edit mode for a code block.

        Phase 2 of Hybrid Smart Extraction (Council Vote b75dced893145a4c).

        Detects whether code should be appended, inserted at a location,
        or merged via LLM.

        Returns dict with:
            mode: 'append' | 'insert_top' | 'insert_after' | 'write' (full file)
            anchor: Optional text to search for in existing file
            line_hint: Optional approximate line number
            verb: The action verb detected
        """
        result = {
            'mode': 'write',  # Default: full file write (Phase 1 behavior)
            'anchor': None,
            'line_hint': None,
            'verb': None
        }

        text = preceding_text.lower()

        # Check if target file exists (new files always use write mode)
        if target_file and not os.path.exists(target_file):
            result['mode'] = 'write'
            result['verb'] = 'create'
            return result

        # Pattern: "Add this method after X" or "Add new method"
        add_match = re.search(r'add\s+(?:this\s+)?(?:new\s+)?(?:method|function|class)',
                              text)
        if add_match:
            result['mode'] = 'append'
            result['verb'] = 'add_method'
            # Look for "after X" anchor
            after_match = re.search(r'after\s+`?([a-zA-Z_]\w*(?:\(\))?)`?', text)
            if after_match:
                result['anchor'] = after_match.group(1).strip('`')
                result['mode'] = 'insert_after'
            return result

        # Pattern: "Add import" or "At the top of the file"
        import_match = re.search(r'(?:add\s+(?:this\s+)?import|at\s+the\s+top\s+of\s+the\s+file|after\s+existing\s+imports)',
                                 text)
        if import_match:
            result['mode'] = 'insert_top'
            result['verb'] = 'add_import'
            # Look for line hint
            line_match = re.search(r'around\s+line\s+(\d+)', text)
            if line_match:
                result['line_hint'] = int(line_match.group(1))
            return result

        # Pattern: "Modify the X method" or "Update X" or "Replace X"
        modify_match = re.search(r'(?:modify|update|replace|change)\s+(?:the\s+)?`?([a-zA-Z_]\w*(?:\(\))?)`?',
                                 text)
        if modify_match:
            anchor = modify_match.group(1).strip('`').rstrip('()')
            # Check if the code block looks like a method/function def
            if re.match(r'\s*def\s+', code_content) or re.match(r'\s*class\s+', code_content):
                result['mode'] = 'replace_method'
                result['verb'] = 'modify'
            else:
                result['mode'] = 'insert_after'
                result['verb'] = 'modify'
            result['anchor'] = anchor
            line_match = re.search(r'around\s+line\s+(\d+)', text)
            if line_match:
                result['line_hint'] = int(line_match.group(1))
            return result

        # Pattern: line hint without verb
        line_match = re.search(r'around\s+line\s+(\d+)', text)
        if line_match:
            result['mode'] = 'insert_after'
            result['verb'] = 'insert'
            result['line_hint'] = int(line_match.group(1))
            return result

        # No partial edit pattern detected - use write (Phase 1 behavior)
        return result

    def _apply_partial_edit(self, filepath: str, content: str,
                             edit_info: dict) -> dict:
        """
        Apply a partial edit to an existing file.

        Phase 2 of Hybrid Smart Extraction (Council Vote b75dced893145a4c).

        Modes:
        - append: Add code at end of file (before final class closing or EOF)
        - insert_top: Insert near top of file (after imports)
        - insert_after: Insert after an anchor function/method/line
        - write: Full file write (delegates to safe_file_write)

        Returns:
            Result dict with success, written bytes, mode used
        """
        mode = edit_info.get('mode', 'write')

        # If file doesn't exist, always use write mode
        if not os.path.exists(filepath):
            return self.safe_file_write(filepath, content, f"partial_edit:{mode}")

        # Read existing file
        try:
            with open(filepath, 'r') as f:
                existing_lines = f.readlines()
        except Exception as e:
            return {'success': False, 'error': f'Cannot read existing file: {e}'}

        existing_content = ''.join(existing_lines)
        original_line_count = len(existing_lines)

        # Create backup
        backup_path = filepath + '.bak'
        try:
            shutil.copy2(filepath, backup_path)
        except Exception as e:
            print(f"[PartialEdit] Backup failed: {e}")

        new_lines = content.rstrip('\n').split('\n')
        merged_lines = list(existing_lines)  # Copy

        # Idempotency check: skip if content already present in file
        # Only for insert/append modes (not replace - the point of replace is to change existing code)
        if mode in ('insert_top', 'append', 'insert_after'):
            # Use a unique multi-line fingerprint (first 3 non-blank non-comment lines)
            fingerprint_lines = [l.strip() for l in new_lines
                                 if l.strip() and not l.strip().startswith('#')][:3]
            existing_stripped = [l.strip() for l in existing_lines]
            if fingerprint_lines and all(fp in existing_stripped for fp in fingerprint_lines):
                print(f"[PartialEdit] SKIP: Content already present ({mode})")
                return {
                    'success': True,
                    'written': len(existing_content),
                    'path': filepath,
                    'mode': f'partial_edit:{mode}:skipped',
                    'old_lines': original_line_count,
                    'new_lines': original_line_count,
                    'note': 'Content already present, skipped'
                }

        if mode == 'insert_top':
            # Insert after imports section
            insert_pos = self._find_import_end(existing_lines)
            # Add blank line before and after
            insert_block = ['\n'] + [line + '\n' for line in new_lines] + ['\n']
            merged_lines[insert_pos:insert_pos] = insert_block
            print(f"[PartialEdit] insert_top at line {insert_pos}")

        elif mode == 'append':
            # Append at end of file with blank line separator
            append_block = ['\n'] + [line + '\n' for line in new_lines] + ['\n']
            merged_lines.extend(append_block)
            print(f"[PartialEdit] append at end of file")

        elif mode == 'insert_after':
            anchor = edit_info.get('anchor')
            line_hint = edit_info.get('line_hint')
            insert_pos = self._find_insert_position(existing_lines, anchor, line_hint)

            if insert_pos is not None:
                insert_block = ['\n'] + [line + '\n' for line in new_lines] + ['\n']
                merged_lines[insert_pos:insert_pos] = insert_block
                print(f"[PartialEdit] insert_after at line {insert_pos} (anchor={anchor})")
            else:
                # Fallback: append at end
                print(f"[PartialEdit] Could not find anchor '{anchor}', appending at end")
                append_block = ['\n'] + [line + '\n' for line in new_lines] + ['\n']
                merged_lines.extend(append_block)

        elif mode == 'replace_method':
            # Replace an existing method/function with new version
            anchor = edit_info.get('anchor')
            line_hint = edit_info.get('line_hint')
            replace_range = self._find_method_range(existing_lines, anchor, line_hint)

            if replace_range:
                start, end = replace_range
                # Replace the method lines with new content
                new_method_lines = [line + '\n' for line in new_lines]
                # Preserve a blank line after the method
                new_method_lines.append('\n')
                merged_lines[start:end] = new_method_lines
                print(f"[PartialEdit] replace_method '{anchor}' lines {start}-{end} with {len(new_method_lines)} lines")
            else:
                # Method not found - insert after line hint or append
                print(f"[PartialEdit] Method '{anchor}' not found for replace, appending")
                append_block = ['\n'] + [line + '\n' for line in new_lines] + ['\n']
                merged_lines.extend(append_block)

        else:
            # Full write mode - delegate to safe_file_write
            return self.safe_file_write(filepath, content, f"partial_edit:write")

        # Write merged content
        merged_content = ''.join(merged_lines)
        try:
            with open(filepath, 'w') as f:
                f.write(merged_content)
        except Exception as e:
            # Restore backup
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, filepath)
            return {'success': False, 'error': f'Write failed: {e}'}

        # Syntax check for Python files
        if filepath.endswith('.py'):
            try:
                result = subprocess.run(
                    ['python3', '-m', 'py_compile', filepath],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode != 0:
                    print(f"[PartialEdit] Syntax check FAILED, restoring backup")
                    print(f"[PartialEdit] Error: {result.stderr[:200]}")
                    if os.path.exists(backup_path):
                        shutil.copy2(backup_path, filepath)
                    return {
                        'success': False,
                        'error': f'Syntax check failed after edit: {result.stderr[:200]}',
                        'blocked_by': 'syntax_check'
                    }
                else:
                    print(f"[PartialEdit] Syntax check passed")
            except Exception as e:
                print(f"[PartialEdit] Syntax check error: {e}")

        new_line_count = len(merged_lines)
        print(f"[PartialEdit] {mode}: {original_line_count} -> {new_line_count} lines")

        return {
            'success': True,
            'written': len(merged_content),
            'path': filepath,
            'backup': backup_path,
            'mode': f'partial_edit:{mode}',
            'old_lines': original_line_count,
            'new_lines': new_line_count
        }

    def _find_import_end(self, lines: list) -> int:
        """Find the line after the last import statement."""
        last_import = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                last_import = i + 1
            elif stripped.startswith('try:') or stripped.startswith('except'):
                # Import blocks often wrapped in try/except
                continue
            elif last_import > 0 and stripped and not stripped.startswith('#'):
                # First non-import, non-comment line after imports
                break
        return last_import

    def _find_insert_position(self, lines: list, anchor: Optional[str],
                               line_hint: Optional[int]) -> Optional[int]:
        """
        Find the position to insert code after an anchor or near a line hint.

        Strategy:
        1. If anchor provided, search for it (function/method def)
        2. Find the end of that function/method block
        3. Insert after it
        4. If anchor not found, use line_hint as approximate position
        """
        if anchor:
            # Search for anchor as function/method name
            anchor_clean = anchor.rstrip('()')
            for i, line in enumerate(lines):
                # Match def anchor_name( or class anchor_name
                if re.search(rf'def\s+{re.escape(anchor_clean)}\s*\(', line):
                    # Find end of this method (next def at same or lower indent, or end of class)
                    indent = len(line) - len(line.lstrip())
                    end_pos = i + 1
                    for j in range(i + 1, len(lines)):
                        stripped = lines[j].strip()
                        if stripped and not stripped.startswith('#'):
                            j_indent = len(lines[j]) - len(lines[j].lstrip())
                            if j_indent <= indent and stripped:
                                end_pos = j
                                break
                            end_pos = j + 1
                    return end_pos

                # Match class anchor_name
                if re.search(rf'class\s+{re.escape(anchor_clean)}[\s(:]', line):
                    return i + 1

        # Fallback to line hint
        if line_hint:
            # Use line hint as approximate position (0-indexed)
            pos = min(line_hint, len(lines))
            return pos

        return None

    def _find_method_range(self, lines: list, anchor: Optional[str],
                            line_hint: Optional[int]) -> Optional[tuple]:
        """
        Find the start and end line indices of a method/function.

        Returns (start, end) tuple where lines[start:end] is the full method.
        """
        if not anchor:
            return None

        anchor_clean = anchor.rstrip('()')
        start = None

        for i, line in enumerate(lines):
            if re.search(rf'def\s+{re.escape(anchor_clean)}\s*\(', line):
                start = i
                break

        # If not found by name, try line hint
        if start is None and line_hint:
            # Look around the hint for a def
            for offset in range(0, 20):
                for idx in [line_hint - 1 + offset, line_hint - 1 - offset]:
                    if 0 <= idx < len(lines):
                        if re.search(rf'def\s+', lines[idx]):
                            start = idx
                            break
                if start is not None:
                    break

        if start is None:
            return None

        # Find end of method: next def/class at same or lower indent level
        indent = len(lines[start]) - len(lines[start].lstrip())
        end = start + 1
        for j in range(start + 1, len(lines)):
            stripped = lines[j].strip()
            if not stripped:
                # Blank line - continue
                end = j + 1
                continue
            j_indent = len(lines[j]) - len(lines[j].lstrip())
            if j_indent <= indent and (stripped.startswith('def ') or
                                        stripped.startswith('class ') or
                                        stripped.startswith('@') or
                                        stripped.startswith('# ')):
                end = j
                break
            end = j + 1

        return (start, end)

    def process_queue_task(self, task: Dict) -> Dict[str, Any]:
        """
        Process a Jr work queue task by reading and executing instructions.

        Supports both instruction_file (path to .md file) and instruction_content
        (inline instructions stored in database). Fixed Jan 17, 2026.

        Args:
            task: Dict with task_id, title, instruction_file OR instruction_content, assigned_jr

        Returns:
            Dict with success status and execution details
        """
        result = {
            'task_id': task.get('task_id'),
            'title': task.get('title'),
            'success': False,
            'steps_executed': [],
            'error': None
        }

        # Try instruction_content first (inline from database), then instruction_file
        instructions = task.get('instruction_content')
        instruction_source = 'instruction_content'

        if not instructions:
            instruction_file = task.get('instruction_file')
            if not instruction_file:
                result['error'] = 'No instruction_file or instruction_content specified in task'
                return result

            instruction_source = 'instruction_file'
            # Read the instruction file
            try:
                with open(instruction_file, 'r') as f:
                    instructions = f.read()
            except FileNotFoundError:
                result['error'] = f'Instruction file not found: {instruction_file}'
                return result
            except Exception as e:
                result['error'] = f'Failed to read instruction file: {str(e)}'
                return result

        print(f"[TaskExecutor] Using instructions from {instruction_source} ({len(instructions)} chars)")

        # Phase 8: Check if task should use Research Executor (web research)
        if RESEARCH_EXECUTOR_AVAILABLE and is_research_task(task, instructions):
            print(f"[Research] Task flagged for web research: {task.get('title')}")
            try:
                research_executor = ResearchTaskExecutor()
                research_result = research_executor.execute_research_task({
                    'title': task.get('title'),
                    'instructions': instructions,
                    'parameters': task.get('parameters', {})
                })
                # Map research result to standard format
                result['success'] = research_result.get('success', False)
                result['steps_executed'] = research_result.get('steps_executed', [])
                result['artifacts'] = research_result.get('artifacts', [])
                result['error'] = None if research_result.get('success') else 'Research task failed'
                print(f"[Research] Complete: {research_result.get('summary')}")
                return result
            except Exception as e:
                print(f"[Research] Executor error: {e}")
                result['error'] = f'Research executor error: {e}'
                return result

        # Phase 4: Check if task should use RLM recursive execution
        if self._should_use_rlm(task, instructions):
            print(f"[RLM] Task flagged for recursive execution: {task.get('title')}")
            return self._execute_with_rlm(task, instructions)

        # Extract code blocks from instructions
        steps = self._extract_steps_from_instructions(instructions)

        if not steps:
            result['error'] = 'No executable steps found in instruction file'
            return result

        # Execute extracted steps
        try:
            step_results = self.execute_steps(steps)
            result['steps_executed'] = step_results

            # CRITICAL FIX: Empty step_results = failure, not success
            # Python's all([]) returns True, which caused false completions
            if not step_results:
                result['success'] = False
                result['error'] = f'No steps were executed (extracted {len(steps)} steps but execution returned empty)'
                print(f"[EXECUTOR] FAIL: 0 steps executed despite {len(steps)} steps extracted")
                return result

            # Check if all steps succeeded
            all_success = all(s.get('success') for s in step_results)
            result['success'] = all_success

            if not all_success:
                failed = [s for s in step_results if not s.get('success')]
                error_msg = f'{len(failed)} step(s) failed'
                result['error'] = error_msg

                # Phase 3: Use MAR Reflexion to analyze failure
                if LLM_REASONER_AVAILABLE:
                    failed_details = "; ".join([
                        f"{s.get('type', 'unknown')}: {s.get('error', 'unknown error')}"
                        for s in failed
                    ])
                    reflection = self.reflect_on_failure(task, error_msg, failed_details)
                    result['reflection'] = reflection

                    # Log improvements for future learning
                    if reflection.get('improvements'):
                        print(f"[REFLECT] Improvements suggested: {reflection['improvements']}")

                    # Phase 7: Record execution outcome for learning
                    if self.learning_store:
                        try:
                            self.learning_store.record_execution(task, result, reflection)
                            print(f"[LEARNING] Recorded outcome: success={result.get('success')}")
                        except Exception as le:
                            print(f"[LEARNING] Failed to record: {le}")

        except Exception as e:
            result['error'] = f'Execution error: {str(e)}'

            # Reflect on execution errors too
            if LLM_REASONER_AVAILABLE:
                reflection = self.reflect_on_failure(task, str(e), "")
                result['reflection'] = reflection

        # Phase 5: Record outcome for M-GRPO momentum learning
        if self.momentum_learner:
            execution_mode = result.get('execution_mode', 'standard')
            approach = 'use_rlm' if execution_mode == 'rlm' else 'direct_code'
            self.momentum_learner.record_outcome(task, approach, result['success'])
            print(f"[M-GRPO] Recorded: {approach} -> {'SUCCESS' if result['success'] else 'FAIL'}")

        return result

    def _extract_steps_from_instructions(self, instructions: str) -> List[Dict]:
        """
        Extract executable steps from a Jr instruction markdown file.

        Phase 9 Enhancement (Jan 23, 2026 - Council Vote 28d18d80e447505f):
        REGEX-FIRST strategy to prevent LLM path hallucination.

        Order:
        1. Try regex extraction first (reliable for ATOMIC format)
        2. Validate all paths before accepting
        3. Only use LLM if regex finds nothing

        Returns list of step dicts ready for execute_steps()
        """
        # Phase 9: Try regex FIRST (more reliable, no hallucination)
        regex_steps = self._extract_steps_via_regex(instructions)

        if regex_steps:
            # Validate paths in regex-extracted steps
            validated_steps = []
            for step in regex_steps:
                if step.get('type') == 'file':
                    path = step.get('args', {}).get('path', '')
                    is_valid, error = self._validate_path(path)
                    if is_valid:
                        validated_steps.append(step)
                        print(f"[Regex] Valid path: {path}")
                    else:
                        print(f"[Regex] REJECTED path: {path} - {error}")
                else:
                    # Non-file steps (sql, bash) pass through
                    validated_steps.append(step)

            if validated_steps:
                print(f"[Extraction] Regex-first found {len(validated_steps)} valid steps")
                return validated_steps

        # Fallback: Try LLM only if regex found nothing
        if LLM_REASONER_AVAILABLE:
            print("[Extraction] No regex matches, trying LLM extraction...")
            try:
                llm_steps = self._extract_steps_via_llm(instructions)

                # Validate LLM-extracted paths (critical - prevents hallucination)
                validated_llm = []
                for step in llm_steps:
                    if step.get('type') == 'file':
                        path = step.get('path', '') or step.get('args', {}).get('path', '')
                        is_valid, error = self._validate_path(path)
                        if is_valid:
                            validated_llm.append(step)
                            print(f"[LLM] Valid path: {path}")
                        else:
                            print(f"[LLM] REJECTED hallucinated path: {path} - {error}")
                    else:
                        validated_llm.append(step)

                if validated_llm:
                    print(f"[Extraction] LLM found {len(validated_llm)} valid steps")
                    return validated_llm

            except Exception as e:
                print(f"[WARN] LLM extraction failed: {e}")

        print("[Extraction] WARNING: No valid steps extracted from instructions")
        return []

    def _extract_steps_via_llm(self, instructions: str) -> List[Dict]:
        """
        Use structured planning approach to extract steps (Devika AI pattern).

        Two-phase approach:
        1. Planning phase: Extract structure (files, steps) using structured prompt
        2. Code generation phase: Generate code for each identified file

        Enhanced Jan 17, 2026 based on Devika AI and GPT-Engineer research.
        """
        # Import planning modules
        try:
            from jr_planning_prompt import get_planning_prompt, get_code_generation_prompt
            from jr_plan_parser import parse_planning_response, extract_files_from_prose
        except ImportError as e:
            print(f"[WARN] Planning modules not available: {e}, using legacy approach")
            return self._extract_steps_via_legacy_llm(instructions)

        reasoner = get_reasoner_sync()
        steps = []

        # Phase 1: Planning - get structured breakdown
        print("[LLM] Phase 1: Generating structured plan...")
        planning_prompt = get_planning_prompt(instructions)

        try:
            plan_response = reasoner.simple_completion(planning_prompt)
        except Exception as e:
            print(f"[LLM] Planning failed: {e}, trying prose extraction")
            plan_response = ""

        print(f"[LLM] Planning response received ({len(plan_response)} chars)")

        # Parse the structured response
        plan = parse_planning_response(plan_response)

        print(f"[LLM] Parsed plan: {plan['project_name']}")
        print(f"[LLM] Focus: {plan['focus'][:80] if plan['focus'] else 'none'}")
        print(f"[LLM] Files to create: {len(plan['files_to_create'])}")
        print(f"[LLM] Files to modify: {len(plan['files_to_modify'])}")
        print(f"[LLM] Steps: {len(plan['steps'])}")

        # Fallback: if no files found, try prose extraction
        if not plan['files_to_create'] and not plan['files_to_modify']:
            print("[LLM] No files in plan, trying prose extraction fallback...")
            prose_files = extract_files_from_prose(instructions)
            plan['files_to_create'] = [(f, 'Extracted from prose') for f in prose_files['files_to_create']]
            plan['files_to_modify'] = [(f, 'Extracted from prose') for f in prose_files['files_to_modify']]
            print(f"[LLM] Prose extraction found: {len(plan['files_to_create'])} create, {len(plan['files_to_modify'])} modify")

        # Phase 2: Code generation for each file
        print("[LLM] Phase 2: Generating code for files...")

        for file_path, description in plan['files_to_create']:
            print(f"[LLM] Generating: {file_path}")
            code_prompt = get_code_generation_prompt(file_path, description, instructions)

            try:
                code = reasoner.simple_completion(code_prompt)

                # Extract code from markdown block if present
                code_match = re.search(r'```\w*\n(.*?)```', code, re.DOTALL)
                if code_match:
                    code = code_match.group(1)

                if code and len(code.strip()) > 10:
                    steps.append({
                        'type': 'file',
                        'args': {
                            'operation': 'write',
                            'path': file_path,
                            'content': code.strip()
                        },
                        'description': f"Create {file_path}: {description}"
                    })
                    print(f"[LLM] Generated {len(code)} chars for {file_path}")
                else:
                    print(f"[WARN] Empty or too short code for {file_path}")
            except Exception as e:
                print(f"[ERROR] Code generation failed for {file_path}: {e}")

        for file_path, description in plan['files_to_modify']:
            print(f"[LLM] Modifying: {file_path}")
            # Read existing file
            existing_code = None
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        existing_code = f.read()
                except Exception as e:
                    print(f"[WARN] Could not read existing file {file_path}: {e}")

            context = instructions
            if existing_code:
                context += f"\n\n## EXISTING CODE IN {file_path}:\n```\n{existing_code}\n```"

            code_prompt = get_code_generation_prompt(file_path, description, context)

            try:
                code = reasoner.simple_completion(code_prompt)

                # Extract code from markdown block
                code_match = re.search(r'```\w*\n(.*?)```', code, re.DOTALL)
                if code_match:
                    code = code_match.group(1)

                if code and len(code.strip()) > 10:
                    steps.append({
                        'type': 'file',
                        'args': {
                            'operation': 'write',
                            'path': file_path,
                            'content': code.strip()
                        },
                        'description': f"Modify {file_path}: {description}"
                    })
                    print(f"[LLM] Generated {len(code)} chars for {file_path}")
            except Exception as e:
                print(f"[ERROR] Code generation failed for {file_path}: {e}")

        # ALWAYS run regex extraction to capture SQL/bash blocks
        # that LLM file generation may have missed (FIX: Jan 20, 2026)
        regex_steps = self._extract_steps_via_regex(instructions)
        if regex_steps:
            print(f"[LLM] Regex found {len(regex_steps)} additional steps (SQL/bash)")
            # Add regex steps BEFORE file steps so dependencies (tables) are created first
            steps = regex_steps + steps
        elif not steps:
            print("[LLM] No steps from LLM or regex - task may need manual review")

        print(f"[LLM] Total steps generated: {len(steps)} (file: {len(steps) - len(regex_steps)}, sql/bash: {len(regex_steps)})")
        return steps

    def _extract_steps_via_legacy_llm(self, instructions: str) -> List[Dict]:
        """Legacy LLM extraction for backwards compatibility."""
        reasoner = get_reasoner_sync()
        understanding = reasoner.understand_instruction(instructions)

        steps = []
        files_to_create = understanding.get('files_to_create', [])
        files_to_modify = understanding.get('files_to_modify', [])
        language = understanding.get('language', 'python')

        for filepath in files_to_create:
            step_desc = f"Create {filepath}: {understanding.get('summary', '')}"
            code = reasoner.generate_code(step_desc, {
                'language': language,
                'file_path': filepath,
                'patterns': []
            })
            if code and len(code) > 10:
                steps.append({
                    'type': 'file',
                    'args': {'operation': 'write', 'path': filepath, 'content': code},
                    'description': step_desc
                })

        for filepath in files_to_modify:
            existing_code = None
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r') as f:
                        existing_code = f.read()
                except:
                    pass
            step_desc = f"Modify {filepath}: {understanding.get('summary', '')}"
            code = reasoner.generate_code(step_desc, {
                'language': language,
                'file_path': filepath,
                'existing_code': existing_code,
                'patterns': []
            })
            if code and len(code) > 10:
                steps.append({
                    'type': 'file',
                    'args': {'operation': 'write', 'path': filepath, 'content': code},
                    'description': step_desc
                })

        # ALWAYS capture SQL/bash from regex (FIX: Jan 20, 2026)
        regex_steps = self._extract_steps_via_regex(instructions)
        if regex_steps:
            steps = regex_steps + steps

        return steps

    def reflect_on_failure(self, task: Dict, error: str, result: str = "") -> Dict:
        """
        Use MAR Reflexion to analyze task failure and suggest improvements.
        Phase 3 enhancement for self-improving execution.

        Returns:
            {
                "should_retry": bool,
                "modified_approach": str,
                "analysis": str
            }
        """
        if not LLM_REASONER_AVAILABLE:
            return {"should_retry": False, "analysis": "LLM not available for reflection"}

        try:
            reasoner = get_reasoner_sync()
            task_desc = f"{task.get('title', 'Unknown')} - {task.get('instruction_file', '')}"

            reflection = reasoner.reflect_on_execution(
                task=task_desc,
                result=result,
                error=error
            )

            print(f"[REFLECT] Success: {reflection.get('success')}")
            print(f"[REFLECT] Retry suggested: {reflection.get('retry_suggested')}")
            print(f"[REFLECT] Analysis: {reflection.get('analysis', '')[:100]}")

            return {
                "should_retry": reflection.get('retry_suggested', False),
                "modified_approach": reflection.get('modified_approach'),
                "analysis": reflection.get('analysis', ''),
                "improvements": reflection.get('improvements', [])
            }
        except Exception as e:
            print(f"[REFLECT] Reflection error: {e}")
            return {"should_retry": False, "analysis": f"Reflection failed: {e}"}

    def _should_use_rlm(self, task: Dict, instructions: str) -> bool:
        """
        Determine if a task should use RLM recursive execution.
        Phase 4 enhancement for complex task decomposition.

        Criteria:
        - use_rlm flag is True in task
        - Task has many files to create/modify (>3)
        - Instructions are very long (>3000 chars)
        - Task title contains keywords like 'implement', 'build', 'create system'
        """
        if not RLM_AVAILABLE:
            return False

        # P0 FIX Jan 27, 2026: Explicit use_rlm=false should be respected
        # Check if use_rlm was explicitly set (present in task dict)
        if 'use_rlm' in task:
            return bool(task['use_rlm'])

        # Auto-detection only applies if use_rlm was not explicitly set
        # Check instruction length
        if len(instructions) > 3000:
            return True

        # Check for complex task keywords in title
        title = task.get('title', '').lower()
        complex_keywords = ['implement', 'build system', 'create api', 'authentication',
                          'full stack', 'migration', 'refactor entire', 'redesign']
        if any(kw in title for kw in complex_keywords):
            return True

        # Count files mentioned in instructions
        file_patterns = re.findall(r'(?:Create|Modify|Update):\s*[`/][^\s`]+', instructions)
        if len(file_patterns) > 3:
            return True

        return False

    def _execute_with_rlm(self, task: Dict, instructions: str) -> Dict[str, Any]:
        """
        Execute a task using RLM recursive decomposition.
        Phase 4 enhancement for complex multi-step tasks.
        """
        result = {
            'task_id': task.get('task_id'),
            'title': task.get('title'),
            'success': False,
            'steps_executed': [],
            'error': None,
            'execution_mode': 'rlm'
        }

        try:
            from rlm_executor import RLMExecutor

            print(f"[RLM] Initializing recursive executor...")
            executor = RLMExecutor(sandbox="local")

            # Build task dict for RLM
            rlm_task = {
                "task_id": task.get('task_id', 'unknown'),
                "title": task.get('title', 'Unknown task'),
                "instructions": instructions,
                "files_to_create": [],
                "files_to_modify": []
            }

            # Extract files from instructions if LLM reasoner is available
            if LLM_REASONER_AVAILABLE:
                try:
                    reasoner = get_reasoner_sync()
                    understanding = reasoner.understand_instruction(instructions)
                    rlm_task["files_to_create"] = understanding.get('files_to_create', [])
                    rlm_task["files_to_modify"] = understanding.get('files_to_modify', [])
                    print(f"[RLM] Files to create: {rlm_task['files_to_create']}")
                    print(f"[RLM] Files to modify: {rlm_task['files_to_modify']}")
                except Exception as e:
                    print(f"[RLM] Could not extract files via LLM: {e}")

            # Execute with RLM
            print(f"[RLM] Executing task with recursive decomposition...")
            rlm_result = executor.execute_task(rlm_task)

            result['success'] = rlm_result.get('success', False)
            result['rlm_result'] = rlm_result.get('result', '')
            result['subtasks_completed'] = rlm_result.get('subtasks_completed', 0)
            result['artifacts'] = rlm_result.get('artifacts', [])

            # CRITICAL FIX: RLM must have done actual work to be successful
            # P0 FIX Jan 27, 2026: Check files_created specifically, not just artifacts list
            subtasks = result.get('subtasks_completed', 0)
            artifacts = result.get('artifacts', [])
            files_created = result.get('files_created', 0)

            # Require ACTUAL files to have been created for RLM success
            if result['success'] and files_created == 0 and subtasks == 0:
                result['success'] = False
                result['error'] = 'RLM execution reported success but created 0 files'
                print(f"[RLM] FAIL: Reported success but 0 files created")

            # Also fail if RLM claims success but only has empty artifacts
            if result['success'] and not artifacts and files_created == 0:
                result['success'] = False
                result['error'] = 'RLM execution completed but produced no output'
                print(f"[RLM] FAIL: No artifacts or files produced")

            if not result['success']:
                result['error'] = result.get('error') or rlm_result.get('error', 'RLM execution failed')

            print(f"[RLM] Execution complete. Success: {result['success']}, Subtasks: {subtasks}, Artifacts: {len(artifacts)}")
            return result

        except ImportError as e:
            result['error'] = f"RLM not available: {e}"
            print(f"[RLM] Import error: {e}")
            return result
        except Exception as e:
            result['error'] = f"RLM execution error: {e}"
            print(f"[RLM] Execution error: {e}")
            return result

    def _extract_steps_via_regex(self, instructions: str) -> List[Dict]:
        """
        Enhanced regex-based extraction with smart file detection.

        Phase 1 of Hybrid Smart Extraction (Council Vote 8f3a1e9f4b86ded5).

        Enhancements:
        1. Extract target file from instruction header
        2. Look for file paths in prose before code blocks
        3. Attribute unmatched Python blocks to target file if unambiguous

        Returns list of step dicts ready for execute_steps()
        """
        steps = []

        # Phase 1: Extract target file from header (for single-file instructions)
        target_file = self._extract_target_file_from_header(instructions)

        # Pattern to match code blocks with language hint - use finditer for positions
        code_block_pattern = r'```(\w+)\n(.*?)```'

        for match in re.finditer(code_block_pattern, instructions, re.DOTALL):
            lang = match.group(1)
            raw_content = match.group(2)
            content = raw_content.strip()
            block_start = match.start()

            if lang.lower() == 'sql':
                steps.append({
                    'type': 'sql',
                    'command': content
                })
            elif lang.lower() in ('bash', 'shell', 'sh'):
                steps.append({
                    'type': 'bash',
                    'command': content
                })
            elif lang.lower() in ('python', 'typescript', 'javascript', 'yaml', 'json'):
                filepath = None

                if block_start > 0:
                    # Check preceding 500 chars for file path patterns
                    preceding_text = instructions[max(0, block_start-500):block_start]

                    # Try existing explicit patterns first
                    file_patterns = [
                        r"Create\s+`([^`]+)`",
                        r"\*\*File:\*\*\s*`([^`]+)`",
                        r"File:\s*`([^`]+)`",
                        r"Modify:\s*`([^`]+)`",
                    ]

                    for pattern in file_patterns:
                        file_match = re.search(pattern, preceding_text)
                        if file_match:
                            filepath = file_match.group(1).strip('`').strip()
                            break

                    # If no match, try prose extraction (Phase 1 enhancement)
                    if not filepath:
                        filepath = self._extract_file_from_prose(preceding_text)

                # If still no filepath but we have a single target file, use it
                if not filepath and target_file:
                    # Only for code files modifying the target
                    target_ext = target_file.split('.')[-1] if '.' in target_file else ''
                    lang_ext_map = {
                        'python': 'py',
                        'typescript': 'ts',
                        'javascript': 'js',
                        'yaml': 'yaml',
                        'json': 'json'
                    }
                    if lang_ext_map.get(lang.lower()) == target_ext:
                        filepath = target_file
                        print(f"[SmartExtract] Attributing {lang} block to target: {filepath}")

                if filepath:
                    # Validate path before adding
                    is_valid, error = self._validate_path(filepath)
                    if is_valid:
                        # Phase 2: Determine edit mode from preceding prose
                        prose_for_mode = instructions[max(0, block_start-500):block_start] if block_start > 0 else ''
                        edit_info = self._determine_edit_mode(prose_for_mode, content, filepath)

                        if edit_info['mode'] != 'write':
                            # Partial edit detected - preserve indentation from raw content
                            # Strip only trailing whitespace, keep leading indent
                            edit_content = raw_content.rstrip()
                            # Remove leading blank lines but keep indentation
                            edit_lines = edit_content.split('\n')
                            while edit_lines and not edit_lines[0].strip():
                                edit_lines.pop(0)
                            edit_content = '\n'.join(edit_lines)

                            steps.append({
                                'type': 'file',
                                'args': {
                                    'operation': 'partial_edit',
                                    'path': filepath,
                                    'content': edit_content,
                                    'edit_info': edit_info
                                }
                            })
                            print(f"[SmartExtract] Partial edit step: {filepath} mode={edit_info['mode']} verb={edit_info.get('verb')} ({len(edit_content)} chars)")
                        else:
                            steps.append({
                                'type': 'file',
                                'args': {
                                    'operation': 'write',
                                    'path': filepath,
                                    'content': content
                                }
                            })
                            print(f"[SmartExtract] Write step: {filepath} ({len(content)} chars)")
                    else:
                        print(f"[SmartExtract] Rejected invalid path: {filepath} - {error}")
                else:
                    print(f"[SmartExtract] Skipping {lang} block - no file path found")

        print(f"[SmartExtract] Total steps extracted: {len(steps)}")
        return steps

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
            if operation in ('write', 'partial_edit'):
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

            # SECURITY Phase 9: Validate path against placeholder patterns
            is_valid, error = self._validate_path(path)
            if not is_valid:
                return {
                    'success': False,
                    'error': f'Path validation failed: {error}',
                    'blocked_by': 'path_validator'
                }

            # SECURITY: Validate path basics (legacy, kept for defense in depth)
            if not path or '..' in path:
                return {'success': False, 'error': 'Invalid path (empty or contains ..)'}

            # SECURITY: Check allowed paths for write operations
            if operation in ['write', 'append', 'partial_edit']:
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

            elif operation == 'partial_edit':
                # Phase 2 Smart Extraction: Apply partial edit (append/insert/modify)
                edit_info = args.get('edit_info', {'mode': 'append'})
                edit_result = self._apply_partial_edit(path, content, edit_info)

                if not edit_result.get('success'):
                    return {
                        'success': False,
                        'error': edit_result.get('error', 'Partial edit failed'),
                        'blocked_by': edit_result.get('blocked_by', 'partial_edit'),
                        'type': 'file'
                    }

                self._audit_file_operation('partial_edit', path, edit_result.get('written', 0), edit_result.get('backup'))

                return {
                    'success': True,
                    'written': edit_result.get('written', 0),
                    'path': path,
                    'backup': edit_result.get('backup'),
                    'mode': edit_result.get('mode', 'partial_edit'),
                    'old_lines': edit_result.get('old_lines', 0),
                    'new_lines': edit_result.get('new_lines', 0),
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

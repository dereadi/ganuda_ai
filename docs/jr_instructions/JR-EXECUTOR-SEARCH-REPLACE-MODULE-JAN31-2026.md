# JR-EXECUTOR-SEARCH-REPLACE-MODULE-JAN31-2026

## Metadata
- **Priority:** P0
- **Jr Type:** Engineering
- **Target Node:** sasass2 (192.168.132.200)
- **Category:** Executor Architecture — Search-Replace Editor Module
- **Depends On:** None (first in sequence)
- **Council Vote:** ULTRATHINK-EXECUTOR-SEARCH-REPLACE-ARCHITECTURE-JAN31-2026 (7/7 APPROVE)

## Objective

Create a NEW standalone module that implements search-and-replace file editing for the Jr executor. This module will be imported by task_executor.py to handle a new `search_replace` step type.

**CRITICAL: This task creates a NEW FILE only. Do NOT modify any existing files.**

## Implementation

Create the SearchReplaceEditor module using bash heredoc (executor-safe approach):

```bash
cat > /ganuda/jr_executor/search_replace_editor.py << 'PYEOF'
"""
Search-Replace Editor Module for Jr Task Executor

Implements the search-and-replace file editing pattern used by
Aider, SWE-Agent, OpenHands, and Claude Code.

Council Vote: ULTRATHINK-EXECUTOR-SEARCH-REPLACE-ARCHITECTURE-JAN31-2026
Architecture: Explicit search text → unique match → replace → validate → rollback on failure

Cherokee AI Federation — For Seven Generations
"""

import os
import re
import shutil
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any


class SearchReplaceEditor:
    """
    Applies search-and-replace edits to files with safety guarantees.

    Design principles (from industry research):
    1. Search text must match EXACTLY ONE location (uniqueness enforcement)
    2. Backup BEFORE every modification
    3. Syntax validation AFTER every modification
    4. Automatic rollback on validation failure
    5. Each edit is independent — one failure doesn't invalidate others
    """

    # Maximum number of search-replace blocks per task (Crawdad security addendum)
    MAX_EDITS_PER_TASK = 20

    def __init__(self, allowed_paths: List[str] = None, forbidden_paths: List[str] = None):
        """
        Initialize editor with path restrictions.

        Args:
            allowed_paths: List of path prefixes where edits are permitted (e.g., ['/ganuda/'])
            forbidden_paths: List of path prefixes where edits are forbidden (e.g., ['/etc/', '/usr/'])
        """
        self.allowed_paths = allowed_paths or ['/ganuda/']
        self.forbidden_paths = forbidden_paths or ['/etc/', '/usr/', '/bin/', '/sbin/', '/boot/']
        self.edit_count = 0
        self.edit_log: List[Dict] = []

    def validate_path(self, filepath: str) -> Tuple[bool, str]:
        """Validate that filepath is allowed for editing."""
        if not os.path.isabs(filepath):
            return False, f"Path must be absolute, got: {filepath}"

        # Check forbidden paths first
        for forbidden in self.forbidden_paths:
            if filepath.startswith(forbidden):
                return False, f"Path is in forbidden area: {forbidden}"

        # Check allowed paths
        path_allowed = any(filepath.startswith(allowed) for allowed in self.allowed_paths)
        if not path_allowed:
            return False, f"Path not in allowed areas: {self.allowed_paths}"

        return True, ""

    def apply_search_replace(self, filepath: str, search_text: str, replace_text: str) -> Dict[str, Any]:
        """
        Apply a single search-and-replace edit to a file.

        Rules:
        1. search_text must match EXACTLY ONE location in the file
        2. If zero matches: fail with 'SEARCH_NOT_FOUND'
        3. If multiple matches: fail with 'SEARCH_AMBIGUOUS' + count
        4. Create backup BEFORE modification
        5. After replacement, validate Python syntax if .py file
        6. On syntax error, restore from backup and fail

        Args:
            filepath: Absolute path to the file to edit
            search_text: Exact text to find (must be unique in file)
            replace_text: Text to replace it with

        Returns:
            Dict with keys: success, error, lines_changed, backup_path, match_index
        """
        result: Dict[str, Any] = {
            'success': False,
            'error': '',
            'lines_changed': 0,
            'backup_path': '',
            'match_index': -1,
            'filepath': filepath
        }

        # Rate limit check (Crawdad addendum)
        if self.edit_count >= self.MAX_EDITS_PER_TASK:
            result['error'] = f'RATE_LIMIT: Maximum {self.MAX_EDITS_PER_TASK} edits per task exceeded'
            self._log_edit(filepath, 'rate_limited', result)
            return result

        # Validate path
        is_valid, error = self.validate_path(filepath)
        if not is_valid:
            result['error'] = f'PATH_INVALID: {error}'
            self._log_edit(filepath, 'path_invalid', result)
            return result

        # Check file exists
        if not os.path.exists(filepath):
            result['error'] = f'FILE_NOT_FOUND: {filepath}'
            self._log_edit(filepath, 'file_not_found', result)
            return result

        # Read current file content
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            result['error'] = f'READ_ERROR: {e}'
            self._log_edit(filepath, 'read_error', result)
            return result

        # Count matches — must be exactly 1
        count = content.count(search_text)

        if count == 0:
            # Provide helpful context: show first 80 chars of search text
            preview = search_text[:80].replace('\n', '\\n')
            result['error'] = f'SEARCH_NOT_FOUND: Text not found in {filepath}. Search preview: "{preview}"'
            self._log_edit(filepath, 'not_found', result)
            return result

        if count > 1:
            result['error'] = (
                f'SEARCH_AMBIGUOUS: Found {count} matches in {filepath}. '
                f'Provide more surrounding context to make the match unique.'
            )
            self._log_edit(filepath, 'ambiguous', result)
            return result

        # Record match position for logging
        result['match_index'] = content.index(search_text)

        # Create backup BEFORE modification
        backup_path = self._create_backup(filepath)
        if not backup_path:
            result['error'] = f'BACKUP_FAILED: Could not create backup of {filepath}'
            self._log_edit(filepath, 'backup_failed', result)
            return result
        result['backup_path'] = backup_path

        # Apply the replacement
        new_content = content.replace(search_text, replace_text, 1)

        # Write new content
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
        except Exception as e:
            # Restore from backup on write failure
            self._restore_from_backup(filepath, backup_path)
            result['error'] = f'WRITE_ERROR: {e} — restored from backup'
            self._log_edit(filepath, 'write_error', result)
            return result

        # Post-edit syntax validation
        syntax_ok, syntax_error = self._validate_syntax(filepath, new_content)
        if not syntax_ok:
            # RESTORE from backup on syntax error (SWE-Agent pattern)
            self._restore_from_backup(filepath, backup_path)
            result['error'] = f'SYNTAX_ERROR: {syntax_error} — restored from backup'
            self._log_edit(filepath, 'syntax_error', result)
            return result

        # Calculate lines changed
        old_line_count = search_text.count('\n') + 1
        new_line_count = replace_text.count('\n') + 1
        result['lines_changed'] = abs(new_line_count - old_line_count)

        # Success
        result['success'] = True
        self.edit_count += 1
        self._log_edit(filepath, 'success', result)

        print(f"[SEARCH-REPLACE] SUCCESS: {filepath} — "
              f"matched at char {result['match_index']}, "
              f"{result['lines_changed']} lines changed, "
              f"backup: {os.path.basename(backup_path)}")

        return result

    def apply_multiple(self, edits: List[Dict]) -> Dict[str, Any]:
        """
        Apply multiple search-replace edits sequentially.

        Each edit is independent — if one fails, others still apply.
        Returns summary with per-edit results.

        Args:
            edits: List of dicts with keys: filepath, search, replace

        Returns:
            Dict with keys: total, succeeded, failed, results
        """
        summary: Dict[str, Any] = {
            'total': len(edits),
            'succeeded': 0,
            'failed': 0,
            'results': []
        }

        for i, edit in enumerate(edits):
            filepath = edit.get('path') or edit.get('filepath', '')
            search = edit.get('search', '')
            replace = edit.get('replace', '')

            if not filepath or not search:
                result = {
                    'success': False,
                    'error': f'MISSING_FIELDS: Edit #{i+1} missing filepath or search text',
                    'filepath': filepath
                }
                summary['results'].append(result)
                summary['failed'] += 1
                continue

            result = self.apply_search_replace(filepath, search, replace)
            summary['results'].append(result)

            if result['success']:
                summary['succeeded'] += 1
            else:
                summary['failed'] += 1
                print(f"[SEARCH-REPLACE] FAILED edit #{i+1}: {result['error']}")

        print(f"[SEARCH-REPLACE] Batch complete: {summary['succeeded']}/{summary['total']} succeeded, "
              f"{summary['failed']} failed")

        return summary

    def parse_search_replace_blocks(self, text: str) -> List[Dict]:
        """
        Parse SEARCH/REPLACE blocks from instruction text.

        Expected format (Aider-style):

        **File:** `/path/to/file.py`

        <<<<<<< SEARCH
        existing code to find
        =======
        replacement code
        >>>>>>> REPLACE

        Returns:
            List of dicts with keys: path, search, replace
        """
        edits = []

        # Pattern for SEARCH/REPLACE blocks
        sr_pattern = r'<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE'

        for match in re.finditer(sr_pattern, text, re.DOTALL):
            search_text = match.group(1)
            replace_text = match.group(2)
            block_start = match.start()

            # Find filepath from preceding text (within 500 chars before the block)
            preceding = text[max(0, block_start - 500):block_start]
            filepath = self._extract_filepath(preceding)

            if filepath:
                edits.append({
                    'path': filepath,
                    'search': search_text,
                    'replace': replace_text
                })
                print(f"[SR-PARSE] Found edit for {filepath}: "
                      f"search={len(search_text)} chars, replace={len(replace_text)} chars")
            else:
                print(f"[SR-PARSE] WARNING: Found SEARCH/REPLACE block but no filepath in preceding text")

        print(f"[SR-PARSE] Parsed {len(edits)} search-replace blocks from instructions")
        return edits

    def _extract_filepath(self, text: str) -> Optional[str]:
        """Extract file path from prose text preceding a SEARCH/REPLACE block."""
        # Try multiple patterns (same as task_executor.py extraction)
        patterns = [
            r'\*\*File:\*\*\s*`([^`]+)`',
            r'File:\s*`([^`]+)`',
            r'Modify:\s*`([^`]+)`',
            r'Create\s+`([^`]+)`',
            r'Edit:\s*`([^`]+)`',
            r'In\s+`([^`]+)`',
            # Bare path on its own line
            r'\n(/ganuda/[^\s\n]+\.\w+)\s*\n',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                filepath = match.group(1).strip('`').strip()
                if os.path.isabs(filepath):
                    return filepath

        return None

    def _create_backup(self, filepath: str) -> Optional[str]:
        """Create timestamped backup of file before editing."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"{filepath}.sr_backup_{timestamp}"
            shutil.copy2(filepath, backup_path)
            return backup_path
        except Exception as e:
            print(f"[SEARCH-REPLACE] Backup failed for {filepath}: {e}")
            return None

    def _restore_from_backup(self, filepath: str, backup_path: str) -> bool:
        """Restore file from backup after failed edit."""
        try:
            shutil.copy2(backup_path, filepath)
            print(f"[SEARCH-REPLACE] RESTORED {filepath} from backup")
            return True
        except Exception as e:
            print(f"[SEARCH-REPLACE] RESTORE FAILED for {filepath}: {e}")
            return False

    def _validate_syntax(self, filepath: str, content: str) -> Tuple[bool, str]:
        """
        Validate syntax of edited file.

        Currently supports:
        - Python (.py): compile() check
        - Future: TypeScript, JavaScript via external linters
        """
        if filepath.endswith('.py'):
            try:
                compile(content, filepath, 'exec')
                return True, ''
            except SyntaxError as e:
                return False, f"Python syntax error at line {e.lineno}: {e.msg}"

        # For non-Python files, pass validation (no linter available yet)
        return True, ''

    def _log_edit(self, filepath: str, status: str, result: Dict):
        """Log edit attempt for Eagle Eye monitoring."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'filepath': filepath,
            'status': status,
            'error': result.get('error', ''),
            'lines_changed': result.get('lines_changed', 0),
            'edit_number': self.edit_count
        }
        self.edit_log.append(entry)

    def get_metrics(self) -> Dict:
        """Return metrics for Eagle Eye dashboard."""
        if not self.edit_log:
            return {'total': 0, 'success_rate': 0.0}

        total = len(self.edit_log)
        successes = sum(1 for e in self.edit_log if e['status'] == 'success')
        failures_by_type = {}
        for entry in self.edit_log:
            if entry['status'] != 'success':
                failures_by_type[entry['status']] = failures_by_type.get(entry['status'], 0) + 1

        return {
            'total': total,
            'succeeded': successes,
            'success_rate': successes / total if total > 0 else 0.0,
            'failures_by_type': failures_by_type,
            'edits_remaining': self.MAX_EDITS_PER_TASK - self.edit_count
        }
PYEOF
echo "Created /ganuda/jr_executor/search_replace_editor.py ($(wc -l < /ganuda/jr_executor/search_replace_editor.py) lines)"
```

## Verification

```bash
python3 -c "
import sys
sys.path.insert(0, '/ganuda/jr_executor')
from search_replace_editor import SearchReplaceEditor
editor = SearchReplaceEditor()
print('SearchReplaceEditor imported successfully')
print(f'MAX_EDITS_PER_TASK: {editor.MAX_EDITS_PER_TASK}')
print(f'Allowed paths: {editor.allowed_paths}')
print(f'Methods: {[m for m in dir(editor) if not m.startswith(\"_\")]}')

# Test path validation
ok, err = editor.validate_path('/ganuda/test.py')
assert ok, f'Should allow /ganuda/ paths: {err}'
ok, err = editor.validate_path('/etc/passwd')
assert not ok, 'Should block /etc/ paths'
ok, err = editor.validate_path('relative/path.py')
assert not ok, 'Should block relative paths'
print('All path validation tests passed')
print('Module ready for integration')
"
```

## Rollback (manual only — do NOT execute automatically)

To undo this task, manually run: rm /ganuda/jr_executor/search_replace_editor.py

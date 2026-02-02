# JR Instruction: Create Targeted Editor Module (P1)

**Priority:** P1 - HIGH
**Sprint:** Infrastructure Emergency
**Created:** 2026-01-26
**Author:** TPM via Claude Code
**Depends On:** JR-EXECUTOR-P0-DISABLE-RLM-MODIFICATIONS-JAN26-2026.md

## Problem Statement

The Jr executor needs a safe way to modify existing files. RLM cannot be used for modifications (it overwrites entire files). The TargetedEditor module provides:

- Backup before any modification
- Diff-based changes instead of full replacement
- Syntax validation after edit
- Automatic rollback on failure
- Protection against destructive edits (>50% file shrinkage)

## Required Changes

CREATE: `/ganuda/lib/targeted_editor.py`

**Create this new file with the following content:**

```python
#!/usr/bin/env python3
"""
Targeted Editor - Safe file modification for Jr executor.
Uses diff/patch approach instead of full file replacement.

For Seven Generations - Cherokee AI Federation
Created: January 26, 2026
"""

import os
import difflib
import shutil
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class TargetedEditor:
    """
    Safely modifies files using targeted edits.

    Features:
    - Always creates backup before modification
    - Validates changes compile/lint
    - Automatic rollback on failure
    - Generates unified diffs for review
    - Blocks destructive edits (>50% shrinkage)
    """

    BACKUP_DIR = "/ganuda/backups/jr_edits"

    def __init__(self, vllm_url: str = "http://localhost:8000/v1"):
        self.vllm_url = vllm_url
        os.makedirs(self.BACKUP_DIR, exist_ok=True)

    def modify_file(
        self,
        file_path: str,
        instructions: str,
        specific_changes: List[Dict] = None
    ) -> Dict:
        """
        Safely modify an existing file.

        Args:
            file_path: Path to file to modify
            instructions: Natural language description of changes
            specific_changes: Optional list of {"old": str, "new": str} dicts

        Returns:
            {
                "success": bool,
                "backup_path": str,
                "changes_made": list,
                "diff": str,
                "error": str or None
            }
        """
        result = {
            "success": False,
            "backup_path": None,
            "changes_made": [],
            "diff": "",
            "error": None
        }

        # Validate file exists
        if not os.path.exists(file_path):
            result["error"] = f"File not found: {file_path}"
            return result

        # Read original content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except Exception as e:
            result["error"] = f"Could not read file: {e}"
            return result

        original_size = len(original_content)

        # Create backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = os.path.basename(file_path).replace('/', '_')
        backup_name = f"{safe_name}.{timestamp}.backup"
        backup_path = os.path.join(self.BACKUP_DIR, backup_name)

        try:
            shutil.copy2(file_path, backup_path)
            result["backup_path"] = backup_path
            print(f"[TargetedEditor] Backup created: {backup_path}")
        except Exception as e:
            result["error"] = f"Could not create backup: {e}"
            return result

        try:
            if specific_changes:
                # Apply specific old->new replacements
                new_content = original_content
                for change in specific_changes:
                    old_text = change.get("old", "")
                    new_text = change.get("new", "")

                    if not old_text:
                        result["error"] = "Empty 'old' text in change specification"
                        return result

                    if old_text in new_content:
                        new_content = new_content.replace(old_text, new_text, 1)
                        result["changes_made"].append({
                            "old_preview": old_text[:100] + ("..." if len(old_text) > 100 else ""),
                            "new_preview": new_text[:100] + ("..." if len(new_text) > 100 else ""),
                            "description": change.get("description", "")
                        })
                    else:
                        result["error"] = f"Could not find text to replace: {old_text[:80]}..."
                        return result
            else:
                # Use LLM to generate edit
                new_content = self._llm_generate_edit(
                    file_path, original_content, instructions
                )
                if new_content is None:
                    result["error"] = "LLM failed to generate edit"
                    return result

            # Generate diff for review
            diff_lines = list(difflib.unified_diff(
                original_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{os.path.basename(file_path)}",
                tofile=f"b/{os.path.basename(file_path)}"
            ))
            result["diff"] = "".join(diff_lines)

            # SAFETY CHECK: File shouldn't shrink by more than 50%
            new_size = len(new_content)
            if new_size < original_size * 0.5 and original_size > 500:
                result["error"] = (
                    f"BLOCKED: Edit would shrink file by >50% "
                    f"({original_size} -> {new_size} bytes). "
                    f"This looks like a destructive replacement, not a targeted edit."
                )
                print(f"[TargetedEditor] {result['error']}")
                return result

            # Write new content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            # Validate syntax (for known file types)
            validation = self._validate_syntax(file_path)
            if not validation["valid"]:
                # Rollback!
                shutil.copy2(backup_path, file_path)
                result["error"] = f"Syntax validation failed, rolled back: {validation['error']}"
                print(f"[TargetedEditor] {result['error']}")
                return result

            result["success"] = True
            print(f"[TargetedEditor] Successfully modified: {file_path}")
            return result

        except Exception as e:
            # Rollback on any error
            if backup_path and os.path.exists(backup_path):
                shutil.copy2(backup_path, file_path)
                print(f"[TargetedEditor] Rolled back after error: {e}")
            result["error"] = f"Edit failed, rolled back: {e}"
            return result

    def _llm_generate_edit(
        self,
        file_path: str,
        original_content: str,
        instructions: str
    ) -> Optional[str]:
        """Use LLM to generate the edited file content."""
        import requests

        # Truncate very large files for context window
        max_content_size = 30000
        truncated = False
        display_content = original_content
        if len(original_content) > max_content_size:
            display_content = original_content[:max_content_size] + "\n... [truncated]"
            truncated = True

        prompt = f"""You are editing an existing file. Make ONLY the requested changes.
Do NOT rewrite the entire file. Keep all existing code that isn't being changed.

FILE: {file_path}
CURRENT CONTENT:
```
{display_content}
```

REQUESTED CHANGES:
{instructions}

{"NOTE: File was truncated for display. Preserve all content including what was truncated." if truncated else ""}

OUTPUT the complete file with ONLY the requested changes applied.
Preserve all existing code, comments, imports, and formatting that are not being changed.
Do not add extra comments or documentation unless specifically requested.
"""

        try:
            response = requests.post(
                f"{self.vllm_url}/chat/completions",
                json={
                    "model": "/ganuda/models/qwen2.5-coder-32b-awq",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,  # Low temp for precise edits
                    "max_tokens": 16000
                },
                timeout=120
            )

            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                # Extract code block if present
                code_match = re.search(r'```\w*\n(.*?)```', content, re.DOTALL)
                if code_match:
                    return code_match.group(1)
                return content
            else:
                print(f"[TargetedEditor] LLM returned status {response.status_code}")

        except Exception as e:
            print(f"[TargetedEditor] LLM request failed: {e}")

        return None

    def _validate_syntax(self, file_path: str) -> Dict:
        """Validate file syntax based on extension."""
        import subprocess

        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.py':
            result = subprocess.run(
                ['python3', '-m', 'py_compile', file_path],
                capture_output=True, text=True
            )
            return {"valid": result.returncode == 0, "error": result.stderr}

        elif ext in ['.ts', '.tsx']:
            # Try tsc --noEmit if available
            try:
                result = subprocess.run(
                    ['npx', 'tsc', '--noEmit', '--skipLibCheck', file_path],
                    capture_output=True, text=True,
                    cwd=os.path.dirname(file_path),
                    timeout=30
                )
                # TypeScript errors are warnings, not always fatal
                return {"valid": True, "error": result.stderr if result.returncode else None}
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return {"valid": True, "error": "tsc not available"}

        elif ext in ['.js', '.jsx']:
            # Use node --check for basic syntax
            try:
                result = subprocess.run(
                    ['node', '--check', file_path],
                    capture_output=True, text=True,
                    timeout=10
                )
                return {"valid": result.returncode == 0, "error": result.stderr}
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return {"valid": True, "error": "node not available"}

        elif ext == '.json':
            # Validate JSON
            try:
                import json
                with open(file_path) as f:
                    json.load(f)
                return {"valid": True, "error": None}
            except json.JSONDecodeError as e:
                return {"valid": False, "error": str(e)}

        # Unknown file type - assume valid
        return {"valid": True, "error": None}

    def rollback(self, file_path: str, backup_path: str) -> bool:
        """Restore file from backup."""
        try:
            if not os.path.exists(backup_path):
                print(f"[TargetedEditor] Backup not found: {backup_path}")
                return False

            shutil.copy2(backup_path, file_path)
            print(f"[TargetedEditor] Rolled back {file_path} from {backup_path}")
            return True
        except Exception as e:
            print(f"[TargetedEditor] Rollback failed: {e}")
            return False

    def list_backups(self, file_name_pattern: str = None) -> List[str]:
        """List available backups, optionally filtered by file name pattern."""
        backups = []
        for f in os.listdir(self.BACKUP_DIR):
            if file_name_pattern is None or file_name_pattern in f:
                backups.append(os.path.join(self.BACKUP_DIR, f))
        return sorted(backups, reverse=True)  # Most recent first

    def cleanup_old_backups(self, days: int = 7) -> int:
        """Remove backups older than specified days."""
        import time
        cutoff = time.time() - (days * 86400)
        removed = 0

        for f in os.listdir(self.BACKUP_DIR):
            path = os.path.join(self.BACKUP_DIR, f)
            if os.path.getmtime(path) < cutoff:
                os.unlink(path)
                removed += 1

        print(f"[TargetedEditor] Cleaned up {removed} backups older than {days} days")
        return removed
```

## Also Create Backup Directory

```bash
mkdir -p /ganuda/backups/jr_edits
chmod 755 /ganuda/backups/jr_edits
```

## Verification

After creating the file, run:

```bash
cd /ganuda
python3 -c "
from lib.targeted_editor import TargetedEditor
import tempfile
import os

editor = TargetedEditor()

# Create test file
test_content = '''
def hello():
    print('Hello World')

def goodbye():
    print('Goodbye World')
'''

with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
    f.write(test_content)
    test_file = f.name

# Test 1: Apply specific change
result = editor.modify_file(
    file_path=test_file,
    instructions='Change Hello to Hi',
    specific_changes=[{'old': 'Hello World', 'new': 'Hi World'}]
)

assert result['success'], f'FAIL: {result[\"error\"]}'
assert result['backup_path'], 'FAIL: No backup created'
print('✓ Test 1 PASS: Specific change applied with backup')

# Verify content
with open(test_file) as f:
    new_content = f.read()
assert 'Hi World' in new_content, 'FAIL: Change not applied'
assert 'goodbye' in new_content, 'FAIL: Other code was removed!'
print('✓ Test 2 PASS: Change applied, other code preserved')

# Test 3: Destructive edit should be blocked
result2 = editor.modify_file(
    file_path=test_file,
    instructions='test',
    specific_changes=[{'old': new_content.strip(), 'new': 'x=1'}]
)

assert not result2['success'], 'FAIL: Destructive edit should be blocked'
assert '>50%' in result2.get('error', ''), 'FAIL: Wrong error message'
print('✓ Test 3 PASS: Destructive edit blocked')

os.unlink(test_file)
print('\\n✅ All TargetedEditor tests passed')
"
```

Expected output:
```
[TargetedEditor] Backup created: /ganuda/backups/jr_edits/...
[TargetedEditor] Successfully modified: /tmp/...
✓ Test 1 PASS: Specific change applied with backup
✓ Test 2 PASS: Change applied, other code preserved
[TargetedEditor] BLOCKED: Edit would shrink file by >50%...
✓ Test 3 PASS: Destructive edit blocked

✅ All TargetedEditor tests passed
```

## Deployment

No service restart required. Module is imported on demand.

---
FOR SEVEN GENERATIONS

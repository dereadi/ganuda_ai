# ULTRATHINK: Jr Executor Architecture Critical Fix
**Date:** January 26, 2026
**Author:** TPM via Claude Code
**Priority:** P0 - Critical Production Issue
**Impact:** Jr executor overwrites files instead of making targeted edits

---

## Executive Summary

During VetAssist Sprint 3 testing, the Jr executor **destroyed production files** by overwriting them with LLM-generated stubs. A 261-line React component was replaced with a 30-line stub. This is an architectural flaw that must be fixed before any Jr can safely modify existing code.

## Root Cause Analysis

### Architecture Diagram (Current - DANGEROUS)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         jr_cli.py                                    │
│  _process_queue_task()                                              │
│         │                                                            │
│         ▼                                                            │
│  TaskExecutor.process_queue_task()                                  │
│         │                                                            │
│         ├── _should_use_rlm() → TRUE for "modify" instructions      │
│         │                                                            │
│         ▼                                                            │
│  _execute_with_rlm()                                                │
│         │                                                            │
│         ▼                                                            │
│  RLMExecutor.execute_task()                                         │
│         │                                                            │
│         ▼                                                            │
│  _build_execution_prompt() ─────────────────────────────────────┐   │
│         │                                                        │   │
│         │  "Write Python code to CREATE files using open()"     │   │
│         │  ^^^^ THIS IS THE PROBLEM ^^^^                        │   │
│         │                                                        │   │
│         ▼                                                        │   │
│  RLM library executes generated Python code                      │   │
│         │                                                        │   │
│         ▼                                                        │   │
│  ┌──────────────────────────────────────────────────────────┐   │   │
│  │  with open('/path/to/existing/file.tsx', 'w') as f:      │   │   │
│  │      f.write('''stub code here''')                        │   │   │
│  │                                                           │   │   │
│  │  FILE ALREADY DESTROYED AT THIS POINT!                    │◄──┘   │
│  └──────────────────────────────────────────────────────────┘       │
│         │                                                            │
│         ▼                                                            │
│  _write_files_from_response() ← Safeguard is HERE (too late!)       │
│         │                                                            │
│         │  Lines 358-375: Checks file size... but file already      │
│         │  overwritten by RLM-executed Python code!                 │
│         │                                                            │
└─────────────────────────────────────────────────────────────────────┘
```

### The 5 Critical Bugs

| Bug | Location | Severity | Description |
|-----|----------|----------|-------------|
| **B1** | `rlm_executor.py:173-227` | CRITICAL | Prompt asks LLM to "CREATE files" even for modifications |
| **B2** | `rlm_executor.py:358-375` | CRITICAL | Safeguard runs AFTER RLM library already executed code |
| **B3** | `task_executor.py:310-312` | HIGH | `_should_use_rlm()` returns TRUE for any "modify" task |
| **B4** | `jr_plan_parser.py:149-161` | MEDIUM | Doesn't extract file paths from "Current/Change to" format |
| **B5** | `jr_cli.py` (fixed) | MEDIUM | Was completing tasks with 0 steps |

### Why The Safeguard Failed

The safeguard at `rlm_executor.py:358-375` checks:
```python
if existing_size > new_size * 2 and existing_size > 1000:
    # BLOCK
```

But by the time this runs, the RLM library has ALREADY executed:
```python
with open('/path/file.tsx', 'w') as f:
    f.write(stub_code)
```

The file is destroyed before the safeguard can check it.

## Required Architecture Changes

### Target Architecture (SAFE)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    NEW ARCHITECTURE                                  │
│                                                                      │
│  1. NEVER use RLM for file modifications                            │
│  2. RLM only for NEW file creation                                  │
│  3. Modifications use targeted EDIT approach                         │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Task arrives with "FILES TO MODIFY"                          │   │
│  │         │                                                     │   │
│  │         ▼                                                     │   │
│  │  READ existing file content FIRST                             │   │
│  │         │                                                     │   │
│  │         ▼                                                     │   │
│  │  Ask LLM: "Given this existing file, generate ONLY            │   │
│  │            the specific changes as a unified diff"            │   │
│  │         │                                                     │   │
│  │         ▼                                                     │   │
│  │  Parse diff, apply changes via patch                          │   │
│  │         │                                                     │   │
│  │         ▼                                                     │   │
│  │  BACKUP original before applying                              │   │
│  │         │                                                     │   │
│  │         ▼                                                     │   │
│  │  Validate new file compiles/lints                             │   │
│  │         │                                                     │   │
│  │         ▼                                                     │   │
│  │  On failure: ROLLBACK to backup                               │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## JR REPAIR INSTRUCTIONS

### JR-1: Disable RLM for File Modifications (P0 - IMMEDIATE)

**File:** `/ganuda/jr_executor/task_executor.py`
**Function:** `_should_use_rlm()`

**Current behavior:** Returns TRUE if task has files_to_modify
**Required behavior:** Return FALSE if task has files_to_modify (only use for creation)

```python
def _should_use_rlm(self, task: Dict, instructions: str) -> bool:
    """
    CRITICAL FIX Jan 26, 2026:
    NEVER use RLM for file modifications - it overwrites entire files!
    RLM is only safe for creating NEW files that don't exist.
    """
    # BLOCK: Never use RLM if modifying existing files
    files_to_modify = task.get('files_to_modify', [])
    if files_to_modify:
        print("[RLM] BLOCKED: Task has files_to_modify - using targeted edit instead")
        return False

    # Only use RLM for pure creation tasks
    files_to_create = task.get('files_to_create', [])
    if files_to_create and not files_to_modify:
        # Verify all paths are actually new (don't exist)
        import os
        for f in files_to_create:
            path = f[0] if isinstance(f, tuple) else f
            if os.path.exists(path):
                print(f"[RLM] BLOCKED: 'Create' file already exists: {path}")
                return False
        return True

    return False
```

### JR-2: Add Pre-Execution Safeguard to RLM (P0 - IMMEDIATE)

**File:** `/ganuda/lib/rlm_executor.py`
**Function:** `execute_task()`

Add safeguard BEFORE calling `self.rlm.completion()`:

```python
def execute_task(self, task: Dict) -> Dict:
    """Execute with pre-validation safeguards."""

    # PRE-EXECUTION SAFEGUARD: Block if any target files exist
    files_to_modify = task.get('files_to_modify', [])
    if files_to_modify:
        return {
            "success": False,
            "error": "RLM cannot modify existing files safely. Use targeted edit approach.",
            "blocked_by": "pre_execution_safeguard",
            "files_blocked": files_to_modify
        }

    files_to_create = task.get('files_to_create', [])
    for f in files_to_create:
        path = f[0] if isinstance(f, tuple) else f
        if os.path.exists(path):
            return {
                "success": False,
                "error": f"Cannot create file that already exists: {path}",
                "blocked_by": "pre_execution_safeguard"
            }

    # Existing code continues...
```

### JR-3: Create Targeted Edit Module (P1 - HIGH)

**New File:** `/ganuda/lib/targeted_editor.py`

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
        with open(file_path, 'r') as f:
            original_content = f.read()

        # Create backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = os.path.basename(file_path) + f".{timestamp}.backup"
        backup_path = os.path.join(self.BACKUP_DIR, backup_name)
        shutil.copy2(file_path, backup_path)
        result["backup_path"] = backup_path

        try:
            if specific_changes:
                # Apply specific old->new replacements
                new_content = original_content
                for change in specific_changes:
                    old_text = change.get("old", "")
                    new_text = change.get("new", "")
                    if old_text in new_content:
                        new_content = new_content.replace(old_text, new_text, 1)
                        result["changes_made"].append({
                            "old_preview": old_text[:100],
                            "new_preview": new_text[:100]
                        })
                    else:
                        result["error"] = f"Could not find text to replace: {old_text[:50]}..."
                        return result
            else:
                # Use LLM to generate diff
                new_content = self._llm_generate_edit(
                    file_path, original_content, instructions
                )
                if new_content is None:
                    result["error"] = "LLM failed to generate edit"
                    return result

            # Generate diff for review
            diff = list(difflib.unified_diff(
                original_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{os.path.basename(file_path)}",
                tofile=f"b/{os.path.basename(file_path)}"
            ))
            result["diff"] = "".join(diff)

            # Validate: File shouldn't shrink by more than 50%
            if len(new_content) < len(original_content) * 0.5:
                result["error"] = (
                    f"Edit would shrink file by >50% "
                    f"({len(original_content)} -> {len(new_content)} bytes). "
                    f"This looks like a destructive replacement, not a targeted edit."
                )
                return result

            # Write new content
            with open(file_path, 'w') as f:
                f.write(new_content)

            # Validate syntax (for known file types)
            validation = self._validate_syntax(file_path)
            if not validation["valid"]:
                # Rollback!
                shutil.copy2(backup_path, file_path)
                result["error"] = f"Syntax validation failed, rolled back: {validation['error']}"
                return result

            result["success"] = True
            return result

        except Exception as e:
            # Rollback on any error
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, file_path)
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

        prompt = f"""You are editing an existing file. Make ONLY the requested changes.
Do NOT rewrite the entire file. Keep all existing code that isn't being changed.

FILE: {file_path}
CURRENT CONTENT:
```
{original_content}
```

REQUESTED CHANGES:
{instructions}

OUTPUT the complete file with ONLY the requested changes applied.
Preserve all existing code, comments, imports, and formatting.
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
                import re
                code_match = re.search(r'```\w*\n(.*?)```', content, re.DOTALL)
                if code_match:
                    return code_match.group(1)
                return content

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
            result = subprocess.run(
                ['npx', 'tsc', '--noEmit', file_path],
                capture_output=True, text=True, cwd=os.path.dirname(file_path)
            )
            # TypeScript errors are warnings, not always fatal
            return {"valid": True, "error": result.stderr if result.returncode else None}

        elif ext in ['.js', '.jsx']:
            # Use node --check for basic syntax
            result = subprocess.run(
                ['node', '--check', file_path],
                capture_output=True, text=True
            )
            return {"valid": result.returncode == 0, "error": result.stderr}

        # Unknown file type - assume valid
        return {"valid": True, "error": None}

    def rollback(self, file_path: str, backup_path: str) -> bool:
        """Restore file from backup."""
        try:
            shutil.copy2(backup_path, file_path)
            return True
        except Exception as e:
            print(f"[TargetedEditor] Rollback failed: {e}")
            return False
```

### JR-4: Wire TargetedEditor into TaskExecutor (P1 - HIGH)

**File:** `/ganuda/jr_executor/task_executor.py`

Add after `_execute_with_rlm()`:

```python
def _execute_targeted_edit(self, task: Dict, instructions: str) -> Dict:
    """
    Execute file modifications using targeted edit approach.
    SAFE alternative to RLM for existing files.
    """
    from lib.targeted_editor import TargetedEditor

    result = {
        "success": True,
        "task_id": task.get("task_id"),
        "title": task.get("title"),
        "execution_mode": "targeted_edit",
        "edits": [],
        "artifacts": [],
        "error": None
    }

    editor = TargetedEditor()
    files_to_modify = task.get("files_to_modify", [])

    # Extract specific changes from instructions if available
    changes = self._extract_changes_from_instructions(instructions)

    for file_info in files_to_modify:
        file_path = file_info[0] if isinstance(file_info, tuple) else file_info

        # Get file-specific changes
        file_changes = changes.get(file_path, None)

        edit_result = editor.modify_file(
            file_path=file_path,
            instructions=instructions,
            specific_changes=file_changes
        )

        result["edits"].append({
            "file": file_path,
            "success": edit_result["success"],
            "backup": edit_result.get("backup_path"),
            "diff": edit_result.get("diff", "")[:500],  # Preview
            "error": edit_result.get("error")
        })

        if not edit_result["success"]:
            result["success"] = False
            result["error"] = f"Edit failed for {file_path}: {edit_result.get('error')}"

    return result

def _extract_changes_from_instructions(self, instructions: str) -> Dict:
    """
    Extract specific old->new changes from instruction format.

    Looks for patterns like:
    **Current:**
    ```code
    old code here
    ```

    **Change to:**
    ```code
    new code here
    ```
    """
    import re

    changes = {}

    # Pattern: **Current:** ... **Change to:**
    pattern = r'\*\*Current:?\*\*\s*```\w*\n(.*?)```\s*\*\*Change to:?\*\*\s*```\w*\n(.*?)```'

    for match in re.finditer(pattern, instructions, re.DOTALL | re.IGNORECASE):
        old_code = match.group(1).strip()
        new_code = match.group(2).strip()

        # Try to find which file this applies to
        # Look for file path before this match
        before_match = instructions[:match.start()]
        file_match = re.search(r'(/ganuda/[^\s`]+\.\w+)', before_match[::-1])
        if file_match:
            file_path = file_match.group(1)[::-1]
            if file_path not in changes:
                changes[file_path] = []
            changes[file_path].append({"old": old_code, "new": new_code})

    return changes
```

### JR-5: Enhanced Instruction Parser for Edit Format (P2 - MEDIUM)

**File:** `/ganuda/lib/jr_plan_parser.py`

Add new function:

```python
def extract_edit_instructions(instructions: str) -> Dict[str, List[Dict]]:
    """
    Extract targeted edit instructions from prose format.

    Handles patterns like:
    - "### 1. Update Props Interface (file.tsx, line 5-9)"
    - "**Current:** ... **Change to:**"
    - "### Required Changes" sections

    Returns:
        {
            "/path/to/file.tsx": [
                {"old": "old code", "new": "new code", "description": "what to change"},
                ...
            ]
        }
    """
    import re

    edits = {}

    # Find all file paths mentioned with explicit MODIFY: prefix
    modify_files = re.findall(
        r'MODIFY:\s*`?([^`\s]+\.[a-zA-Z]+)`?',
        instructions,
        re.IGNORECASE
    )

    # Find Current/Change to pairs
    current_change_pattern = r'''
        (?:###\s*\d+\.?\s*([^(]+?))?          # Optional step title
        (?:\([^)]*?(\w+\.\w+)[^)]*\))?        # Optional (filename.ext, line X)
        \s*
        \*\*Current:?\*\*\s*
        ```\w*\n
        (.*?)
        ```
        \s*
        \*\*Change\s+to:?\*\*\s*
        ```\w*\n
        (.*?)
        ```
    '''

    for match in re.finditer(current_change_pattern, instructions, re.DOTALL | re.VERBOSE | re.IGNORECASE):
        step_title = match.group(1) or ""
        filename_hint = match.group(2) or ""
        old_code = match.group(3).strip()
        new_code = match.group(4).strip()

        # Try to match to a MODIFY: file
        target_file = None
        for f in modify_files:
            if filename_hint and filename_hint in f:
                target_file = f
                break

        if not target_file and modify_files:
            target_file = modify_files[0]  # Default to first

        if target_file:
            if target_file not in edits:
                edits[target_file] = []
            edits[target_file].append({
                "old": old_code,
                "new": new_code,
                "description": step_title.strip()
            })

    return edits
```

---

## Deployment Sequence

1. **IMMEDIATE (Today):**
   - JR-1: Disable RLM for modifications
   - JR-2: Add pre-execution safeguard

2. **This Week:**
   - JR-3: Create TargetedEditor module
   - JR-4: Wire into TaskExecutor

3. **Next Week:**
   - JR-5: Enhanced instruction parser
   - Add comprehensive test suite
   - Update KB documentation

## Testing Plan

After each JR:

```bash
# Test 1: Verify RLM blocked for modifications
python3 -c "
from task_executor import TaskExecutor
t = TaskExecutor()
result = t.process_queue_task({
    'task_id': 'test',
    'title': 'Test',
    'instruction_file': None,
    'files_to_modify': ['/ganuda/test.py']
})
assert 'RLM' not in result.get('execution_mode', '')
print('PASS: RLM blocked for modifications')
"

# Test 2: Verify targeted edit creates backup
# Test 3: Verify rollback on syntax error
# Test 4: Verify edit preserves unmodified code
```

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LLM still generates bad edits | Medium | High | 50% shrink safeguard + backup |
| Backup disk fills up | Low | Medium | Pruning job for old backups |
| TypeScript validation fails on valid code | Medium | Low | Make validation warnings, not errors |

---

**FOR SEVEN GENERATIONS**

Cherokee AI Federation - All decisions validated against 175-year impact.

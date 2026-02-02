# JR-EXECUTOR-WIRE-SEARCH-REPLACE-JAN31-2026

## Metadata
- **Priority:** P0
- **Jr Type:** Engineering
- **Target Node:** sasass2 (192.168.132.200)
- **Category:** Executor Architecture — Wire Search-Replace into Executor
- **Depends On:** JR-EXECUTOR-SEARCH-REPLACE-MODULE-JAN31-2026
- **Council Vote:** ULTRATHINK-EXECUTOR-SEARCH-REPLACE-ARCHITECTURE-JAN31-2026 (7/7 APPROVE)

## Objective

Wire the new `SearchReplaceEditor` module into the existing task executor. This task uses ONLY bash commands with absolute paths — no file write operations that go through the broken edit pipeline.

**CRITICAL: This task uses ONLY bash commands. No `file` type steps. All paths are absolute.**

## Pre-Flight Check

```bash
# Verify the search_replace_editor module exists
python3 -c "
import sys
sys.path.insert(0, '/ganuda/jr_executor')
from search_replace_editor import SearchReplaceEditor
print('OK: SearchReplaceEditor module found')
"
```

```bash
# Verify task_executor.py is intact (should be ~2164 lines)
wc -l /ganuda/jr_executor/task_executor.py
```

```bash
# Create backup before ANY modifications
cp /ganuda/jr_executor/task_executor.py /ganuda/jr_executor/task_executor.py.backup_pre_sr_$(date +%Y%m%d_%H%M%S)
```

## Step 1: Add Import

Add the import for SearchReplaceEditor near the top of task_executor.py, after the existing imports.

```bash
# Find the line number of the last import block (look for "from datetime import")
grep -n "^from datetime import\|^import shutil\|^from typing import" /ganuda/jr_executor/task_executor.py | tail -1
```

```bash
# Add the search_replace_editor import after line with "import shutil"
# Using sed to insert after the shutil import (safe, targeted, one-line addition)
sed -i '/^import shutil$/a\from search_replace_editor import SearchReplaceEditor' /ganuda/jr_executor/task_executor.py
```

```bash
# Verify the import was added
grep -n "SearchReplaceEditor" /ganuda/jr_executor/task_executor.py
```

## Step 2: Add search_replace Step Type to execute() Method

The execute() method has an elif chain for step types. Add `search_replace` after the `rsync` handler.

```bash
# Find the rsync handler line in execute()
grep -n "step_type == 'rsync'" /ganuda/jr_executor/task_executor.py
```

```bash
# Insert the search_replace handler after the rsync elif block
# The pattern: after "exec_result = self._execute_rsync(step)" add the new elif
sed -i "/exec_result = self._execute_rsync(step)/a\\
            elif step_type == 'search_replace':\\
                exec_result = self._execute_search_replace(step)" /ganuda/jr_executor/task_executor.py
```

```bash
# Verify the new step type was added
grep -n "search_replace" /ganuda/jr_executor/task_executor.py
```

## Step 3: Add _execute_search_replace() Method

Add the method that bridges the executor to the SearchReplaceEditor. This goes at the end of the class, before the last method.

```bash
# Find the _verify_step_result method (it's near the end of the file)
grep -n "def _verify_step_result" /ganuda/jr_executor/task_executor.py
```

```bash
# Append the new method BEFORE _verify_step_result using sed
# We insert before the _verify_step_result method definition
sed -i '/def _verify_step_result/i\
\
    def _execute_search_replace(self, step: dict) -> dict:\
        """\
        Execute a search-and-replace file edit using the SearchReplaceEditor module.\
        \
        Council Vote: ULTRATHINK-EXECUTOR-SEARCH-REPLACE-ARCHITECTURE-JAN31-2026\
        \
        Step format:\
            {type: "search_replace", args: {path: str, search: str, replace: str}}\
        """\
        args = step.get("args", {})\
        filepath = args.get("path", "")\
        search_text = args.get("search", "")\
        replace_text = args.get("replace", "")\
        \
        if not filepath or not search_text:\
            return {"success": False, "error": "Missing path or search text in search_replace step"}\
        \
        try:\
            editor = SearchReplaceEditor(\
                allowed_paths=getattr(self, "ALLOWED_FILE_PATHS", ["/ganuda/"]),\
                forbidden_paths=getattr(self, "FORBIDDEN_FILE_PATHS", ["/etc/", "/usr/"])\
            )\
            result = editor.apply_search_replace(filepath, search_text, replace_text)\
            \
            # Audit the operation\
            if hasattr(self, "_audit_file_operation"):\
                self._audit_file_operation(\
                    filepath, "search_replace",\
                    f"success={result['"'"'success'"'"']}, lines_changed={result.get('"'"'lines_changed'"'"', 0)}"\
                )\
            \
            return result\
        except Exception as e:\
            return {"success": False, "error": f"SearchReplace error: {e}"}\
' /ganuda/jr_executor/task_executor.py
```

## Step 4: Add SEARCH/REPLACE Block Parsing to _extract_steps_via_regex()

Add parsing for `<<<<<<< SEARCH ... ======= ... >>>>>>> REPLACE` blocks alongside existing code block parsing.

```bash
# Find the line "Total steps extracted" in _extract_steps_via_regex — we insert before it
grep -n "Total steps extracted" /ganuda/jr_executor/task_executor.py
```

```bash
# Insert search-replace block parsing before the "Total steps extracted" line
sed -i '/\[SmartExtract\] Total steps extracted/i\
\
        # Parse SEARCH/REPLACE blocks (Council Vote: search-replace architecture)\
        sr_pattern = r'"'"'<<<<<<< SEARCH\\n(.*?)\\n=======\\n(.*?)\\n>>>>>>> REPLACE'"'"'\
        for sr_match in re.finditer(sr_pattern, instructions, re.DOTALL):\
            sr_search = sr_match.group(1)\
            sr_replace = sr_match.group(2)\
            sr_start = sr_match.start()\
            \
            # Find filepath from preceding text\
            sr_preceding = instructions[max(0, sr_start-500):sr_start]\
            sr_filepath = None\
            sr_file_patterns = [\
                r'"'"'\\*\\*File:\\*\\*\\s*`([^`]+)`'"'"',\
                r'"'"'File:\\s*`([^`]+)`'"'"',\
                r'"'"'Modify:\\s*`([^`]+)`'"'"',\
                r'"'"'Edit:\\s*`([^`]+)`'"'"',\
                r'"'"'In\\s+`([^`]+)`'"'"',\
            ]\
            for fp_pattern in sr_file_patterns:\
                fp_match = re.search(fp_pattern, sr_preceding)\
                if fp_match:\
                    sr_filepath = fp_match.group(1).strip('"'"'`'"'"').strip()\
                    break\
            \
            if sr_filepath:\
                is_valid, error = self._validate_path(sr_filepath)\
                if is_valid:\
                    steps.append({\
                        '"'"'type'"'"': '"'"'search_replace'"'"',\
                        '"'"'args'"'"': {\
                            '"'"'path'"'"': sr_filepath,\
                            '"'"'search'"'"': sr_search,\
                            '"'"'replace'"'"': sr_replace\
                        }\
                    })\
                    print(f"[SmartExtract] Search-replace step: {sr_filepath} ({len(sr_search)} -> {len(sr_replace)} chars)")\
                else:\
                    print(f"[SmartExtract] Rejected SR path: {sr_filepath} - {error}")\
            else:\
                print(f"[SmartExtract] WARNING: SEARCH/REPLACE block found but no filepath")\
' /ganuda/jr_executor/task_executor.py
```

## Step 5: Syntax Validation

```bash
# Verify the modified file has valid Python syntax
python3 -c "
import py_compile
try:
    py_compile.compile('/ganuda/jr_executor/task_executor.py', doraise=True)
    print('PASS: task_executor.py syntax is valid')
except py_compile.PyCompileError as e:
    print(f'FAIL: Syntax error: {e}')
"
```

## Step 6: Integration Test

```bash
python3 -c "
import sys
sys.path.insert(0, '/ganuda/jr_executor')
sys.path.insert(0, '/ganuda/lib')

# Test 1: Import works
from search_replace_editor import SearchReplaceEditor
print('PASS: SearchReplaceEditor import works')

# Test 2: Parse SEARCH/REPLACE blocks from instruction text
editor = SearchReplaceEditor()
test_instructions = '''
**File:** \`/ganuda/test_dummy.py\`

<<<<<<< SEARCH
def hello():
    return 'world'
=======
def hello():
    return 'universe'
>>>>>>> REPLACE
'''
edits = editor.parse_search_replace_blocks(test_instructions)
assert len(edits) == 1, f'Expected 1 edit, got {len(edits)}'
assert edits[0]['path'] == '/ganuda/test_dummy.py'
assert 'world' in edits[0]['search']
assert 'universe' in edits[0]['replace']
print('PASS: SEARCH/REPLACE block parsing works')

# Test 3: Verify search_replace step type is recognized
# (Check the source code contains the handler)
with open('/ganuda/jr_executor/task_executor.py', 'r') as f:
    source = f.read()
assert 'search_replace' in source, 'search_replace step type not found in executor'
assert '_execute_search_replace' in source, '_execute_search_replace method not found'
assert 'SearchReplaceEditor' in source, 'SearchReplaceEditor import not found'
print('PASS: task_executor.py contains search_replace wiring')

# Test 4: Verify SR block extraction pattern is in regex extractor
assert '<<<<<<< SEARCH' in source, 'SR pattern not found in regex extractor'
print('PASS: SR block parsing added to _extract_steps_via_regex')

print()
print('=== ALL INTEGRATION TESTS PASSED ===')
print('The search-replace editor is wired into the executor.')
print('Jr instructions can now use <<<<<<< SEARCH / ======= / >>>>>>> REPLACE blocks.')
"
```

## Rollback (manual only — do NOT execute automatically)

To undo: find the backup with `ls -la /ganuda/jr_executor/task_executor.py.backup_pre_sr_*` and restore with `cp BACKUP_FILE /ganuda/jr_executor/task_executor.py`

# JR Instruction: Fix RLM File Parser

**Priority**: P1 - Critical
**Assigned To**: Software Engineer Jr.
**Created**: January 21, 2026
**Status**: Ready for Execution

## CRITICAL WARNING - DESTRUCTIVE BUG OBSERVED

On January 21, 2026, the RLM executor **DESTROYED** `/ganuda/lib/rlm_executor.py` (14KB) by overwriting it with a 922-byte partial snippet. This is a CRITICAL bug that must be fixed with safeguards.

**The fix MUST include a safeguard to prevent overwriting existing files with smaller content.**

## Problem Statement

The RLM (Recursive Language Model) executor has TWO critical issues:

### Issue 1: File Parser Fails to Extract Files
The parser in `_write_files_from_response()` fails to extract files from valid LLM output. Tasks complete with "0 artifacts created" even when valid code is generated.

### Issue 2: DESTRUCTIVE OVERWRITES (CRITICAL)
When the parser DOES match, it can overwrite a large existing file with a small code snippet, destroying the original file.

**Example of destruction:**
- Original: `/ganuda/lib/rlm_executor.py` (14,000 bytes)
- LLM generates: Just a method snippet (922 bytes)
- Result: Entire file DESTROYED, replaced with snippet

### Evidence from Logs

```
INFO:rlm_executor:[RLM] Task completed: 0 artifacts created
```

But the actual LLM output contains valid patterns:
```
**CREATE FILE: /ganuda/vetassist/backend/tests/test_config.py**
**CREATE FILE: /ganuda/vetassist/backend/app/core/types.py**
**CREATE FILE: /ganuda/vetassist/backend/app/models/content.py**
```

## Root Cause Analysis

1. **Rich Console Formatting**: RLM library wraps output in box-drawing characters (`│`) which may leak into response_text
2. **Trailing Whitespace**: Paths have trailing whitespace before closing `**` (e.g., `test_config.py**              `)
3. **Regex Too Strict**: Current patterns don't handle variations in formatting
4. **Code Block Variations**: LLM may output code blocks with or without language specifier
5. **NO SAFEGUARD AGAINST DESTRUCTIVE WRITES**: When modifying existing files, there's no check to prevent overwriting with smaller content

## Current Parser (Line 192-257 of /ganuda/lib/rlm_executor.py)

```python
# Pattern 1: **CREATE FILE: path** followed by code block
pattern1 = r'\*\*(?:CREATE|MODIFY)\s+FILE:\s*([^\*\n]+)\*\*\s*```(\w+)?\n(.*?)```'
```

Issue: `([^\*\n]+)` captures everything up to `*` but trailing whitespace before `**` breaks the match.

## Fix Implementation

### File to Modify
`/ganuda/lib/rlm_executor.py`

### Changes Required

1. **Pre-process response text** to remove rich console artifacts
2. **Improve regex patterns** to handle whitespace variations
3. **Add fallback patterns** for alternative formats
4. **Add debug logging** to trace parsing issues
5. **Normalize paths** before writing

### Updated `_write_files_from_response` Method

```python
def _write_files_from_response(self, response_text: str, task: Dict) -> List[Dict]:
    """
    Parse LLM response for code blocks and ACTUALLY write files to disk.

    Fixed Jan 21, 2026 - Improved parsing robustness
    """
    import re
    import os

    artifacts = []
    self.logger.info("[RLM] Parsing response for files to create...")

    # Security: allowed paths
    ALLOWED_PATHS = ['/ganuda/', '/tmp/']

    # Pre-process: Remove rich console box-drawing characters
    # These characters: │ ─ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼ ╭ ╮ ╯ ╰
    clean_text = re.sub(r'[│─┌┐└┘├┤┬┴┼╭╮╯╰]', '', response_text)

    # Pre-process: Normalize whitespace (but preserve code indentation in blocks)
    # Remove trailing whitespace on lines outside code blocks
    lines = clean_text.split('\n')
    clean_lines = []
    in_code_block = False
    for line in lines:
        if '```' in line:
            in_code_block = not in_code_block
            clean_lines.append(line.rstrip())
        elif in_code_block:
            clean_lines.append(line.rstrip())  # Preserve indentation, strip trailing
        else:
            clean_lines.append(line.strip())
    clean_text = '\n'.join(clean_lines)

    self.logger.debug(f"[RLM] Clean text preview: {clean_text[:500]}...")

    # Pattern 1: **CREATE FILE: path** (with flexible whitespace)
    # Captures path, strips whitespace
    pattern1 = r'\*\*(?:CREATE|MODIFY)\s+FILE:\s*([^*\n]+?)\s*\*\*\s*\n*```(\w*)\n(.*?)```'

    # Pattern 2: CREATE FILE: `path` (backtick style)
    pattern2 = r'(?:CREATE|MODIFY)\s+FILE:\s*`([^`]+)`\s*\n*```(\w*)\n(.*?)```'

    # Pattern 3: ### path (markdown header style)
    pattern3 = r'###\s*(/[\w/\.\-_]+\.\w+)\s*\n*```(\w*)\n(.*?)```'

    # Pattern 4: **path** followed by code block (simpler variant)
    pattern4 = r'\*\*(/ganuda/[^\*]+?)\*\*\s*\n*```(\w*)\n(.*?)```'

    # Pattern 5: File: path (plain text style)
    pattern5 = r'(?:File|PATH):\s*(/[\w/\.\-_]+\.\w+)\s*\n*```(\w*)\n(.*?)```'

    all_patterns = [
        (pattern1, "CREATE FILE markdown"),
        (pattern2, "CREATE FILE backtick"),
        (pattern3, "markdown header"),
        (pattern4, "bold path"),
        (pattern5, "plain file path")
    ]

    found_files = set()  # Track to avoid duplicates

    for pattern, pattern_name in all_patterns:
        for match in re.finditer(pattern, clean_text, re.DOTALL | re.IGNORECASE):
            file_path = match.group(1).strip()
            language = match.group(2) or 'python'
            code = match.group(3)

            # Clean up path - remove any remaining formatting
            file_path = file_path.strip('`*').strip()

            # Skip if already processed
            if file_path in found_files:
                continue

            # Security: validate path is in allowed locations
            if not any(file_path.startswith(p) for p in ALLOWED_PATHS):
                self.logger.warning(f"[RLM] Skipping file outside allowed paths: {file_path}")
                continue

            # Skip if code is just a placeholder/comment
            code_stripped = code.strip()
            if len(code_stripped) < 20 or code_stripped.startswith('#') and '\n' not in code_stripped:
                self.logger.warning(f"[RLM] Skipping placeholder code for: {file_path}")
                continue

            found_files.add(file_path)

            # CRITICAL SAFEGUARD: Prevent destructive overwrites
            # If file exists and is LARGER than new content, refuse to overwrite
            if os.path.exists(file_path):
                existing_size = os.path.getsize(file_path)
                new_size = len(code)

                # If existing file is more than 2x the size of new content, BLOCK the write
                if existing_size > new_size * 2 and existing_size > 1000:
                    self.logger.error(
                        f"[RLM] BLOCKED destructive overwrite of {file_path}: "
                        f"existing={existing_size}b, new={new_size}b. "
                        f"Use MODIFY pattern or provide complete file content."
                    )
                    artifacts.append({
                        'type': 'file_blocked',
                        'path': file_path,
                        'reason': f'Would overwrite {existing_size}b file with {new_size}b snippet',
                        'existing_size': existing_size,
                        'new_size': new_size
                    })
                    continue

                # Log warning for any existing file overwrite
                self.logger.warning(
                    f"[RLM] Overwriting existing file {file_path} "
                    f"(existing={existing_size}b, new={new_size}b)"
                )

            # Create directory if needed
            dir_path = os.path.dirname(file_path)
            if dir_path:
                try:
                    os.makedirs(dir_path, exist_ok=True)
                except PermissionError as e:
                    self.logger.error(f"[RLM] Cannot create directory {dir_path}: {e}")
                    continue

            # Write file
            try:
                with open(file_path, 'w') as f:
                    f.write(code)
                artifacts.append({
                    'type': 'file_created',
                    'path': file_path,
                    'size': len(code),
                    'language': language,
                    'pattern_matched': pattern_name
                })
                self.logger.info(f"[RLM] Created file: {file_path} ({len(code)} bytes) via {pattern_name}")
            except Exception as e:
                self.logger.error(f"[RLM] Failed to write {file_path}: {e}")

    if not artifacts:
        self.logger.warning("[RLM] No files extracted! Response preview:")
        self.logger.warning(f"[RLM] {response_text[:1000]}...")

    self.logger.info(f"[RLM] Created {len(artifacts)} file(s) from response")
    return artifacts
```

## Testing

### Test 1: Verify Pattern Matching

```bash
cd /ganuda/lib && python3 -c "
import re

test_text = '''
**CREATE FILE: /ganuda/test/example.py**
\`\`\`python
def hello():
    return 'world'
\`\`\`

**CREATE FILE: /ganuda/test/another.py**
\`\`\`python
class Test:
    pass
\`\`\`
'''

pattern = r'\*\*(?:CREATE|MODIFY)\s+FILE:\s*([^*\n]+?)\s*\*\*\s*\n*\`\`\`(\w*)\n(.*?)\`\`\`'
matches = re.finditer(pattern, test_text, re.DOTALL)
for m in matches:
    print(f'Path: {m.group(1).strip()}')
    print(f'Lang: {m.group(2)}')
    print(f'Code: {m.group(3)[:50]}...')
    print()
"
```

### Test 2: Integration Test

```bash
cd /ganuda/jr_executor && source /home/dereadi/cherokee_venv/bin/activate
python3 -c "
from rlm_executor import RLMExecutor

executor = RLMExecutor()
result = executor.execute_task({
    'task_id': 'test_parser',
    'title': 'Create hello world',
    'instructions': 'Create a simple hello.py file in /tmp/test_rlm/',
    'files_to_create': ['/tmp/test_rlm/hello.py'],
    'files_to_modify': []
})
print(f'Success: {result[\"success\"]}')
print(f'Artifacts: {result[\"artifacts\"]}')
"
ls -la /tmp/test_rlm/ 2>/dev/null || echo "No files created"
```

## Rollback Plan

If the fix causes issues:
```bash
cd /ganuda/lib
git checkout rlm_executor.py
```

## Success Criteria

1. Tasks that generate valid `**CREATE FILE:**` patterns create actual files
2. No regression in existing functionality
3. Debug logging shows which patterns matched
4. Test task creates files in `/tmp/test_rlm/`
5. **CRITICAL**: Destructive overwrites are BLOCKED with clear error message
6. **CRITICAL**: Existing large files are NEVER overwritten with small snippets

## Council Vote Reference

This fix supports the Smart Router + Multi-Pass reasoning initiative (Vote ID: ec3bb922c8104159).

---

*Cherokee AI Federation - For Seven Generations*
*"Code that is written but not saved helps no one."*

# JR Instruction: Enhanced Instruction Parser for Edit Format (P2)

**Priority:** P2 - MEDIUM
**Sprint:** Infrastructure Emergency
**Created:** 2026-01-26
**Author:** TPM via Claude Code
**Depends On:**
- JR-EXECUTOR-P1-WIRE-TARGETED-EDITOR-JAN26-2026.md

## Problem Statement

The Jr instruction parser needs to better extract targeted edit instructions from markdown-formatted JR instructions. Current parser doesn't handle the "Current/Change to" format well.

## Required Changes

MODIFY: `/ganuda/lib/jr_plan_parser.py`

### Add New Function for Edit Extraction

Find the end of the existing functions (after `extract_steps_from_instructions` or similar) and add this new function:

```python
def extract_edit_instructions(instructions: str) -> Dict[str, List[Dict]]:
    """
    Extract targeted edit instructions from prose format.

    Handles patterns like:
    - "MODIFY: `/path/to/file.tsx`"
    - "### 1. Update Props Interface (file.tsx, lines 5-9)"
    - "**Current:** ... **Change to:**"

    Returns:
        {
            "/path/to/file.tsx": [
                {
                    "old": "old code",
                    "new": "new code",
                    "description": "what to change",
                    "line_hint": "5-9"  # optional
                },
                ...
            ]
        }

    Added: January 26, 2026
    """
    import re

    edits = {}

    # Find all file paths mentioned with MODIFY: prefix
    # Support both backtick and non-backtick formats
    # Support bracket paths like [sessionId]
    modify_patterns = [
        r'MODIFY:\s*`([^`]+)`',                    # MODIFY: `/path/file.tsx`
        r'MODIFY:\s*([/\w\.\-_\[\]]+\.\w+)',       # MODIFY: /path/file.tsx
    ]

    modify_files = []
    for pattern in modify_patterns:
        modify_files.extend(re.findall(pattern, instructions, re.IGNORECASE))

    # Deduplicate while preserving order
    seen = set()
    modify_files = [f for f in modify_files if not (f in seen or seen.add(f))]

    # Find Current/Change to pairs with optional step headers
    current_change_pattern = r'''
        (?:###\s*\d+\.?\s*([^\n(]+?))?            # Optional: ### 1. Step Title
        (?:\s*\(([^)]+)\))?                        # Optional: (filename.ext, lines 5-9)
        \s*
        \*\*Current:?\*\*\s*
        (?:<!--[^>]*-->)?                          # Optional HTML comment
        \s*
        ```(?:\w*\n)?                              # Code fence with optional language
        (.*?)
        ```
        \s*
        \*\*Change\s*to:?\*\*\s*
        (?:<!--[^>]*-->)?
        \s*
        ```(?:\w*\n)?
        (.*?)
        ```
    '''

    for match in re.finditer(current_change_pattern, instructions, re.DOTALL | re.VERBOSE | re.IGNORECASE):
        step_title = (match.group(1) or "").strip()
        context_hint = (match.group(2) or "").strip()
        old_code = match.group(3).strip()
        new_code = match.group(4).strip()

        if not old_code:
            continue

        # Extract line hint from context (e.g., "lines 5-9" or "line 42")
        line_hint = None
        line_match = re.search(r'lines?\s*(\d+(?:\s*-\s*\d+)?)', context_hint, re.IGNORECASE)
        if line_match:
            line_hint = line_match.group(1)

        # Extract filename hint from context
        filename_hint = None
        file_match = re.search(r'(\w+\.\w+)', context_hint)
        if file_match:
            filename_hint = file_match.group(1)

        # Find the most recently mentioned MODIFY: file before this match
        before_match = instructions[:match.start()]
        target_file = None

        # First try to match by filename hint
        if filename_hint:
            for f in modify_files:
                if filename_hint in f:
                    target_file = f
                    break

        # If no match, find the last MODIFY: before this position
        if not target_file:
            last_modify_pos = -1
            for f in modify_files:
                pos = before_match.rfind(f)
                if pos > last_modify_pos:
                    last_modify_pos = pos
                    target_file = f

        # Default to first MODIFY: file if no context match
        if not target_file and modify_files:
            target_file = modify_files[0]

        if target_file:
            if target_file not in edits:
                edits[target_file] = []

            edits[target_file].append({
                "old": old_code,
                "new": new_code,
                "description": step_title,
                "line_hint": line_hint
            })

    return edits


def parse_instruction_file_for_edits(file_path: str) -> Dict:
    """
    Parse a JR instruction file and extract all edit information.

    Returns:
        {
            "files_to_modify": ["/path/file1.tsx", "/path/file2.py"],
            "files_to_create": ["/path/new_file.py"],
            "edits": {
                "/path/file1.tsx": [{"old": ..., "new": ..., "description": ...}]
            },
            "raw_instructions": "full file content"
        }

    Added: January 26, 2026
    """
    import re

    result = {
        "files_to_modify": [],
        "files_to_create": [],
        "edits": {},
        "raw_instructions": ""
    }

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"[JrPlanParser] Could not read {file_path}: {e}")
        return result

    result["raw_instructions"] = content

    # Extract MODIFY: files (support bracket paths)
    modify_patterns = [
        r'MODIFY:\s*`([^`]+)`',
        r'MODIFY:\s*([/\w\.\-_\[\]]+\.\w+)',
    ]
    for pattern in modify_patterns:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            path = match.group(1)
            if path not in result["files_to_modify"]:
                result["files_to_modify"].append(path)

    # Extract CREATE: files
    create_patterns = [
        r'CREATE:\s*`([^`]+)`',
        r'CREATE:\s*([/\w\.\-_\[\]]+\.\w+)',
        r'New\s+File:\s*`([^`]+)`',
        r'New\s+File:\s*([/\w\.\-_\[\]]+\.\w+)',
    ]
    for pattern in create_patterns:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            path = match.group(1)
            if path not in result["files_to_create"]:
                result["files_to_create"].append(path)

    # Extract edits
    result["edits"] = extract_edit_instructions(content)

    return result
```

### Update Existing `parse_jr_instruction_file` if Present

If the file has an existing `parse_jr_instruction_file` function, add a call to the new function:

```python
def parse_jr_instruction_file(file_path: str) -> Dict:
    """Parse JR instruction file."""
    # ... existing parsing code ...

    # Add enhanced edit extraction (Jan 26, 2026)
    edit_info = parse_instruction_file_for_edits(file_path)
    result["edits"] = edit_info["edits"]

    # Merge files_to_modify if not already captured
    for f in edit_info["files_to_modify"]:
        if f not in result.get("files_to_modify", []):
            result.setdefault("files_to_modify", []).append(f)

    return result
```

## Verification

After applying these changes, run:

```bash
cd /ganuda
python3 -c "
from lib.jr_plan_parser import extract_edit_instructions, parse_instruction_file_for_edits
import tempfile

# Test 1: Extract edits from markdown
test_instructions = '''
# JR Instruction: Fix Something

MODIFY: \`/ganuda/vetassist/frontend/app/wizard/[sessionId]/page.tsx\`

### 1. Update Props Interface (page.tsx, lines 5-9)

**Current:**
\`\`\`typescript
interface Props {
    name: string;
}
\`\`\`

**Change to:**
\`\`\`typescript
interface Props {
    name: string;
    age: number;
}
\`\`\`

### 2. Add Handler Function

**Current:**
\`\`\`typescript
const handleClick = () => {};
\`\`\`

**Change to:**
\`\`\`typescript
const handleClick = () => {
    console.log(\"clicked\");
};
\`\`\`
'''

edits = extract_edit_instructions(test_instructions)

assert len(edits) == 1, f'FAIL: Expected 1 file, got {len(edits)}'
file_path = list(edits.keys())[0]
assert '[sessionId]' in file_path, f'FAIL: Bracket path not parsed: {file_path}'
assert len(edits[file_path]) == 2, f'FAIL: Expected 2 edits, got {len(edits[file_path])}'
print('✓ Test 1 PASS: Extracted 2 edits from 1 file with bracket path')

# Verify edit content
edit1 = edits[file_path][0]
assert 'name: string' in edit1['old'], 'FAIL: Old code not extracted'
assert 'age: number' in edit1['new'], 'FAIL: New code not extracted'
assert edit1['line_hint'] == '5-9', f'FAIL: Line hint not extracted: {edit1.get(\"line_hint\")}'
print('✓ Test 2 PASS: Edit content correctly extracted')

# Test 3: Parse full instruction file
with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
    f.write(test_instructions)
    temp_file = f.name

result = parse_instruction_file_for_edits(temp_file)

assert len(result['files_to_modify']) == 1, 'FAIL: files_to_modify not extracted'
assert '[sessionId]' in result['files_to_modify'][0], 'FAIL: Bracket path lost'
assert result['edits'], 'FAIL: No edits extracted'
print('✓ Test 3 PASS: Full file parse works')

import os
os.unlink(temp_file)

print('\\n✅ All instruction parser tests passed')
"
```

Expected output:
```
✓ Test 1 PASS: Extracted 2 edits from 1 file with bracket path
✓ Test 2 PASS: Edit content correctly extracted
✓ Test 3 PASS: Full file parse works

✅ All instruction parser tests passed
```

## Deployment

No service restart required - changes take effect on next task execution.

---
FOR SEVEN GENERATIONS

# JR Instruction: Safe Edit Mode for Existing Files

**Task ID:** SAFE-EDIT-001
**Priority:** P0 - Critical Infrastructure
**Type:** implementation
**Research Base:** arXiv:2512.21354, arXiv:2503.09089, Aider SEARCH/REPLACE

---

## Objective

Implement a safe edit mode in the Jr executor that uses SEARCH/REPLACE blocks instead of full file generation when modifying existing files. This prevents the regression we experienced where v1.3 code was overwritten with v1.2.

---

## Problem Statement

Current executor behavior:
```
LLM Input: "Add Triple Ethics to specialist_council.py"
LLM Output: [Complete file with 500 lines]
Result: File overwritten, lost 18KB of existing code
```

Desired behavior:
```
LLM Input: "Add Triple Ethics to specialist_council.py"
LLM Output: SEARCH/REPLACE blocks for specific changes
Result: Only targeted lines modified, rest preserved
```

---

## Implementation

### File 1: `/ganuda/jr_executor/safe_edit.py`

```python
"""
Safe Edit Mode for Jr Executor

Implements SEARCH/REPLACE pattern matching for safe file modifications.
Based on:
- Aider's edit format (aider.chat)
- OpenAI's V4A apply-patch format
- Reflection-Driven Control (arXiv:2512.21354)

For Seven Generations - Don't break what works.
"""

import re
import difflib
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class EditBlock:
    """A single SEARCH/REPLACE edit block."""
    search: str
    replace: str
    context_before: str = ""
    context_after: str = ""


class SafeEditError(Exception):
    """Raised when safe edit cannot be applied."""
    pass


def parse_search_replace_blocks(llm_output: str) -> List[EditBlock]:
    """
    Parse SEARCH/REPLACE blocks from LLM output.

    Format:
    <<<<<<< SEARCH
    [exact code to find]
    =======
    [code to replace with]
    >>>>>>> REPLACE

    Returns list of EditBlock objects.
    """
    blocks = []

    # Pattern for SEARCH/REPLACE blocks
    pattern = r'<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE'
    matches = re.findall(pattern, llm_output, re.DOTALL)

    for search, replace in matches:
        blocks.append(EditBlock(
            search=search.strip(),
            replace=replace.strip()
        ))

    return blocks


def find_best_match(content: str, search: str, threshold: float = 0.8) -> Optional[Tuple[int, int]]:
    """
    Find the best matching location for search text in content.

    Uses fuzzy matching to handle minor whitespace differences.

    Args:
        content: The file content to search in
        search: The text to find
        threshold: Minimum similarity ratio (0.0-1.0)

    Returns:
        Tuple of (start_index, end_index) or None if no match
    """
    # First try exact match
    idx = content.find(search)
    if idx != -1:
        return (idx, idx + len(search))

    # Try with normalized whitespace
    normalized_search = normalize_whitespace(search)
    normalized_content = normalize_whitespace(content)

    idx = normalized_content.find(normalized_search)
    if idx != -1:
        # Map back to original content position
        # This is approximate but usually works
        return find_original_position(content, search, idx)

    # Fuzzy match using difflib
    lines = content.split('\n')
    search_lines = search.split('\n')

    best_ratio = 0
    best_start = -1

    for i in range(len(lines) - len(search_lines) + 1):
        candidate = '\n'.join(lines[i:i + len(search_lines)])
        ratio = difflib.SequenceMatcher(None, search, candidate).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_start = i

    if best_ratio >= threshold:
        start_idx = sum(len(line) + 1 for line in lines[:best_start])
        end_idx = sum(len(line) + 1 for line in lines[:best_start + len(search_lines)]) - 1
        return (start_idx, end_idx)

    return None


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace for fuzzy matching."""
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Strip trailing whitespace from lines
    text = '\n'.join(line.rstrip() for line in text.split('\n'))
    return text


def find_original_position(content: str, search: str, normalized_idx: int) -> Optional[Tuple[int, int]]:
    """Map normalized index back to original content position."""
    # Simplified - just search for the first line
    first_line = search.split('\n')[0].strip()
    for i, line in enumerate(content.split('\n')):
        if first_line in line:
            start = sum(len(l) + 1 for l in content.split('\n')[:i])
            # Estimate end based on search length
            return (start, start + len(search))
    return None


def apply_edit_blocks(content: str, blocks: List[EditBlock]) -> Tuple[str, List[str]]:
    """
    Apply SEARCH/REPLACE blocks to content.

    Args:
        content: Original file content
        blocks: List of EditBlock to apply

    Returns:
        Tuple of (modified_content, list_of_warnings)
    """
    warnings = []
    modified = content

    for i, block in enumerate(blocks):
        match = find_best_match(modified, block.search)

        if match is None:
            warnings.append(f"Block {i+1}: SEARCH text not found, skipping")
            continue

        start, end = match
        modified = modified[:start] + block.replace + modified[end:]

    return modified, warnings


def validate_modification(original: str, modified: str) -> Tuple[bool, str]:
    """
    Validate that modification doesn't regress the code.

    Guards against:
    - Significant size reduction (>20%)
    - Loss of existing functions/classes
    - Version downgrades

    Returns (is_valid, reason)
    """
    # Size check
    if len(modified) < len(original) * 0.8:
        return False, f"Code size reduced from {len(original)} to {len(modified)} bytes (>20% reduction)"

    # Function preservation
    original_funcs = set(re.findall(r'def (\w+)\s*\(', original))
    modified_funcs = set(re.findall(r'def (\w+)\s*\(', modified))
    lost_funcs = original_funcs - modified_funcs

    if lost_funcs:
        return False, f"Would lose functions: {lost_funcs}"

    # Class preservation
    original_classes = set(re.findall(r'class (\w+)\s*[:\(]', original))
    modified_classes = set(re.findall(r'class (\w+)\s*[:\(]', modified))
    lost_classes = original_classes - modified_classes

    if lost_classes:
        return False, f"Would lose classes: {lost_classes}"

    # Version downgrade check
    original_versions = re.findall(r'v(\d+\.\d+)', original)
    modified_versions = re.findall(r'v(\d+\.\d+)', modified)

    if original_versions and modified_versions:
        orig_latest = max(original_versions)
        mod_latest = max(modified_versions)
        if mod_latest < orig_latest:
            return False, f"Version downgrade: {orig_latest} -> {mod_latest}"

    return True, "Validation passed"


def safe_edit_file(filepath: str, llm_output: str) -> Tuple[bool, str]:
    """
    Safely edit a file using SEARCH/REPLACE blocks.

    Args:
        filepath: Path to file to edit
        llm_output: LLM response containing SEARCH/REPLACE blocks

    Returns:
        Tuple of (success, message)
    """
    # Read original content
    try:
        with open(filepath, 'r') as f:
            original = f.read()
    except FileNotFoundError:
        return False, f"File not found: {filepath}"

    # Parse edit blocks
    blocks = parse_search_replace_blocks(llm_output)

    if not blocks:
        return False, "No SEARCH/REPLACE blocks found in LLM output"

    # Apply edits
    modified, warnings = apply_edit_blocks(original, blocks)

    if warnings:
        print(f"[SAFE-EDIT] Warnings: {warnings}")

    # Validate modification
    is_valid, reason = validate_modification(original, modified)

    if not is_valid:
        return False, f"Modification rejected: {reason}"

    # Write modified content
    try:
        with open(filepath, 'w') as f:
            f.write(modified)
        return True, f"Successfully applied {len(blocks)} edit(s) to {filepath}"
    except Exception as e:
        return False, f"Failed to write file: {e}"


# Prompt template for safe edit mode
SAFE_EDIT_PROMPT = """You are modifying an EXISTING file. Do NOT rewrite the entire file.

Use SEARCH/REPLACE blocks to make targeted changes:

<<<<<<< SEARCH
[exact existing code to find - include 2-3 lines of context]
=======
[new code to replace it with]
>>>>>>> REPLACE

RULES:
1. SEARCH block must EXACTLY match existing code (whitespace matters)
2. Include 2-3 lines of unchanged context before/after the change
3. Make MINIMAL changes - preserve everything else
4. Use multiple blocks for multiple changes
5. NEVER replace entire functions/classes unless absolutely necessary

If you cannot find the exact code to change, respond with:
SEARCH_FAILED: [explanation of what you tried to find]

DO NOT generate a complete file. Only output SEARCH/REPLACE blocks.
"""


if __name__ == "__main__":
    # Test
    test_content = '''
def hello():
    print("Hello")

def world():
    print("World")
'''

    test_llm_output = '''
Here's the change:

<<<<<<< SEARCH
def hello():
    print("Hello")
=======
def hello():
    print("Hello, Cherokee!")
>>>>>>> REPLACE
'''

    blocks = parse_search_replace_blocks(test_llm_output)
    print(f"Found {len(blocks)} blocks")

    modified, warnings = apply_edit_blocks(test_content, blocks)
    print(f"Warnings: {warnings}")
    print(f"Modified:\n{modified}")

    is_valid, reason = validate_modification(test_content, modified)
    print(f"Valid: {is_valid}, Reason: {reason}")
```

---

### File 2: Integration in `/ganuda/jr_executor/jr_task_executor.py`

Add to `_execute_code_task()` method:

```python
from safe_edit import safe_edit_file, SAFE_EDIT_PROMPT, parse_search_replace_blocks

def _execute_code_task(self, task: dict) -> Tuple[bool, str]:
    """Execute code task with safe edit mode for existing files."""
    task_content = task['task_content']
    task_id = task['task_id']

    # Detect if this is modifying an existing file
    output_path = self._extract_code_output_path(task_content, language)
    file_exists = output_path and os.path.exists(output_path)

    if file_exists:
        # SAFE EDIT MODE
        print(f"[{self.agent_id}] SAFE EDIT MODE: Modifying existing file {output_path}")

        # Read existing file for context
        with open(output_path, 'r') as f:
            existing_content = f.read()

        # Build prompt for safe editing
        prompt = f"""{SAFE_EDIT_PROMPT}

=== EXISTING FILE: {output_path} ===
{existing_content[:8000]}  # Truncate if too long

=== TASK ===
{task_content}

=== INSTRUCTION FILE ===
{instruction_content if instruction_content else 'None'}

Generate SEARCH/REPLACE blocks to make the required changes.
"""
        # Get LLM response
        llm_response = self._query_llm(prompt)

        # Apply safe edits
        success, message = safe_edit_file(output_path, llm_response)

        if success:
            return True, message
        else:
            # Log failure for reflective memory
            self._log_edit_failure(task_id, output_path, message)
            return False, f"Safe edit failed: {message}"

    else:
        # NEW FILE MODE - existing logic
        # ... (current implementation for new files)
```

---

## Testing

```python
# Test safe edit mode
from jr_executor.safe_edit import safe_edit_file

# Create test file
with open('/tmp/test_edit.py', 'w') as f:
    f.write('''
def greet(name):
    return f"Hello, {name}"

def farewell(name):
    return f"Goodbye, {name}"
''')

# Test edit
llm_output = '''
<<<<<<< SEARCH
def greet(name):
    return f"Hello, {name}"
=======
def greet(name):
    """Greet with Cherokee spirit."""
    return f"Osiyo, {name}"
>>>>>>> REPLACE
'''

success, msg = safe_edit_file('/tmp/test_edit.py', llm_output)
print(f"Success: {success}, Message: {msg}")

# Verify farewell function still exists
with open('/tmp/test_edit.py', 'r') as f:
    content = f.read()
    assert 'farewell' in content  # Preserved!
```

---

## Acceptance Criteria

1. Existing files use SEARCH/REPLACE mode (not full generation)
2. Modification validation rejects regressions
3. Lost functions/classes are detected and blocked
4. Size reduction >20% is blocked
5. New files still use full generation mode
6. Edit failures logged to thermal memory for learning

---

## Cherokee Principle Applied

**Seven Generations:** Don't break what previous generations built.

The safe edit mode ensures that when we improve code, we don't accidentally destroy the work that came before. Each generation builds on the last.

---

## Sources

- [Aider Edit Formats](https://aider.chat/docs/more/edit-formats.html)
- [Reflection-Driven Control (arXiv:2512.21354)](https://arxiv.org/abs/2512.21354)
- [LocAgent (arXiv:2503.09089)](https://arxiv.org/abs/2503.09089)

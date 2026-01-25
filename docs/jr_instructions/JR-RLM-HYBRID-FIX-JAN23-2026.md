# JR: RLM Executor Hybrid Fix - Path Validation & Extraction

**Date:** January 23, 2026
**Priority:** High (P1)
**Type:** Bug Fix + Security Enhancement
**Assigned To:** Software Engineer Jr.
**Council Vote:** 28d18d80e447505f (Hybrid Approach D, 87.3% confidence)

## Background

The RLM executor is failing to create files because Qwen 32B hallucinates placeholder paths like `/path/to/file.js` instead of extracting actual paths from instructions. ATOMIC-formatted tasks work via regex parsing, but open-ended tasks fail.

**Evidence:**
- Tasks 253-255 (ATOMIC format): 2/2 steps succeeded
- Tasks 257-263 (open-ended): 0 artifacts created
- Log shows: `[RLM] Files to create: ['/path/to/sag_camera_ui/src/services/opticNerveService.js']`
- That path doesn't exist in the instruction file - it was hallucinated

## Objective

Implement a hybrid fix with four phases:
1. Path validation (security layer)
2. Enhanced regex extraction (reliability)
3. Strict LLM extraction (accuracy)
4. New extraction order (regex-first)

## Implementation

### Phase 1: Path Validation Function

**File:** `/ganuda/jr_executor/task_executor.py`

Add this validation function and constants near the top of the TaskExecutor class:

```python
# Path validation constants (Crawdad security requirement)
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

def _validate_path(self, path: str) -> tuple:
    """
    Validate a file path before any file operations.

    Security layer per Crawdad's council vote requirement.
    Prevents placeholder paths and directory traversal attacks.

    Args:
        path: The file path to validate

    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if not path:
        return False, "Empty path"

    # Check for placeholder patterns
    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, path, re.IGNORECASE):
            return False, f"Placeholder pattern detected: {pattern}"

    # Require absolute path
    if not path.startswith('/'):
        return False, "Path must be absolute (start with /)"

    # Check allowed directories
    if not any(path.startswith(prefix) for prefix in ALLOWED_PATH_PREFIXES):
        return False, f"Path must be in allowed directories: {ALLOWED_PATH_PREFIXES}"

    # Reject directory traversal
    if '..' in path:
        return False, "Directory traversal (..) not allowed"

    # Reject paths with suspicious characters
    if any(c in path for c in [';', '|', '&', '$', '`', '\n', '\r']):
        return False, "Path contains forbidden characters"

    return True, ""
```

### Phase 2: Enhanced Regex Extraction

**File:** `/ganuda/jr_executor/task_executor.py`

Add enhanced regex patterns and extraction function:

```python
# Enhanced path extraction patterns (ordered by reliability)
PATH_EXTRACTION_PATTERNS = [
    # Explicit ATOMIC markers (highest confidence)
    (r'\*\*File:\*\*\s*[`"]?(/[^\s`"<>\n]+)[`"]?', 'atomic_file_marker'),
    (r'\*\*Path:\*\*\s*[`"]?(/[^\s`"<>\n]+)[`"]?', 'atomic_path_marker'),

    # Create/Write markers
    (r'Create\s+(?:file|directory):\s*[`"]?(/[^\s`"<>\n]+)', 'create_marker'),
    (r'Write\s+to:\s*[`"]?(/[^\s`"<>\n]+)', 'write_marker'),

    # Code block paths with /ganuda/
    (r'```(?:python|bash|sql|yaml|json)?[^`]*?(/ganuda/[\w/.+-]+\.(?:py|md|sql|sh|yaml|json|js|ts|css|html))', 'code_block'),

    # Inline backtick paths
    (r'`(/ganuda/[\w/.+-]+\.(?:py|md|sql|sh|yaml|json|js|ts))`', 'backtick'),

    # Double-quoted paths after file keywords
    (r'(?:file|path|create|write|save|output|modify)[^\n"]*"(/ganuda/[^"\n]+)"', 'keyword_quoted'),

    # Single-quoted paths after file keywords
    (r"(?:file|path|create|write|save|output|modify)[^\n']*'(/ganuda/[^'\n]+)'", 'keyword_single_quoted'),
]

def _extract_paths_via_enhanced_regex(self, instructions: str) -> List[Dict]:
    """
    Extract file paths using enhanced regex patterns.

    Phase 2 of hybrid fix: More reliable than LLM for well-formatted instructions.
    All extracted paths are validated through Phase 1 before returning.

    Args:
        instructions: The Jr instruction markdown text

    Returns:
        List of dicts with 'path', 'source', 'valid' keys
    """
    found = []
    seen = set()

    for pattern, source in PATH_EXTRACTION_PATTERNS:
        try:
            for match in re.finditer(pattern, instructions, re.IGNORECASE | re.MULTILINE):
                # Clean the path
                path = match.group(1).rstrip('.,;:)\'"')

                if path in seen:
                    continue
                seen.add(path)

                # Validate through Phase 1
                is_valid, error = self._validate_path(path)

                if is_valid:
                    found.append({
                        'path': path,
                        'source': source,
                        'valid': True
                    })
                    print(f"[Regex] Valid path from {source}: {path}")
                else:
                    print(f"[Regex] Rejected path: {path} - {error}")

        except re.error as e:
            print(f"[Regex] Pattern error {source}: {e}")

    return found
```

### Phase 3: Strict LLM Extraction Prompt

**File:** `/ganuda/jr_executor/task_executor.py`

Update the LLM extraction to use a strict prompt:

```python
STRICT_PATH_EXTRACTION_PROMPT = """You are extracting file paths from a Jr instruction document.

CRITICAL RULES - FOLLOW EXACTLY:
1. Extract ONLY paths that appear LITERALLY in the instruction text
2. Do NOT generate, guess, or invent paths
3. Do NOT use placeholder paths like /path/to/ or /example/
4. Only return paths starting with /ganuda/, /home/, or /tmp/
5. If you cannot find literal paths in the text, return an empty array

CORRECT EXAMPLES:
---
Input: "Create /ganuda/lib/auth.py with authentication logic"
Output: ["/ganuda/lib/auth.py"]
---
Input: "Build a new service to handle user registration"
Output: []
(No literal path found - return empty, do NOT guess)
---
Input: "Modify /ganuda/sag/app.py and create /ganuda/sag/routes/new.py"
Output: ["/ganuda/sag/app.py", "/ganuda/sag/routes/new.py"]
---
Input: "Create a file at /path/to/service.js"
Output: []
(Reject /path/to/ as placeholder - return empty)
---

INSTRUCTION TO ANALYZE:
{instructions}

Return ONLY a JSON array of literal paths found, nothing else:"""

def _extract_paths_via_strict_llm(self, instructions: str) -> List[Dict]:
    """
    Extract paths using LLM with strict anti-hallucination prompt.

    Phase 3 of hybrid fix: Only used when regex finds no paths.
    All results validated through Phase 1 before returning.

    Args:
        instructions: The Jr instruction markdown text

    Returns:
        List of dicts with 'path', 'source', 'valid' keys
    """
    if not self.llm_reasoner_available:
        return []

    try:
        reasoner = get_reasoner_sync()

        # Truncate instructions if too long (prevent context overflow)
        max_chars = 15000  # ~4K tokens, leave room for prompt
        truncated = instructions[:max_chars]
        if len(instructions) > max_chars:
            truncated += "\n\n[TRUNCATED - extract paths from above only]"

        prompt = STRICT_PATH_EXTRACTION_PROMPT.format(instructions=truncated)

        response = reasoner.query(prompt)

        # Parse JSON response
        # Handle various response formats
        text = response.strip()

        # Find JSON array in response
        start = text.find('[')
        end = text.rfind(']') + 1

        if start >= 0 and end > start:
            json_str = text[start:end]
            paths = json.loads(json_str)
        else:
            print(f"[LLM] No JSON array found in response")
            return []

        # Validate all paths through Phase 1
        found = []
        for path in paths:
            if isinstance(path, str):
                is_valid, error = self._validate_path(path)
                if is_valid:
                    found.append({
                        'path': path,
                        'source': 'llm_strict',
                        'valid': True
                    })
                    print(f"[LLM] Valid path: {path}")
                else:
                    print(f"[LLM] Rejected hallucinated path: {path} - {error}")

        return found

    except json.JSONDecodeError as e:
        print(f"[LLM] JSON parse error: {e}")
        return []
    except Exception as e:
        print(f"[LLM] Extraction error: {e}")
        return []
```

### Phase 4: New Extraction Order (Regex-First)

**File:** `/ganuda/jr_executor/task_executor.py`

Replace the existing `_extract_steps_from_instructions` method:

```python
def _extract_steps_from_instructions(self, instructions: str) -> List[Dict]:
    """
    Extract executable steps from Jr instruction markdown.

    HYBRID APPROACH (Council Vote 28d18d80e447505f):
    1. Try enhanced regex first (more reliable for ATOMIC format)
    2. Fall back to strict LLM only if regex finds nothing
    3. All paths validated before use

    Args:
        instructions: The Jr instruction markdown text

    Returns:
        List of step dicts ready for execution
    """
    # PHASE 2: Try enhanced regex first
    regex_paths = self._extract_paths_via_enhanced_regex(instructions)

    if regex_paths:
        print(f"[Extraction] Regex-first found {len(regex_paths)} valid paths")
        for p in regex_paths:
            print(f"  - {p['path']} (via {p['source']})")
        return self._build_steps_from_paths(regex_paths, instructions)

    # PHASE 3: Fall back to strict LLM only if regex found nothing
    print("[Extraction] No regex matches, trying strict LLM extraction")

    if hasattr(self, 'llm_reasoner_available') and self.llm_reasoner_available:
        try:
            llm_paths = self._extract_paths_via_strict_llm(instructions)

            if llm_paths:
                print(f"[Extraction] LLM found {len(llm_paths)} valid paths")
                return self._build_steps_from_paths(llm_paths, instructions)

        except Exception as e:
            print(f"[Extraction] LLM extraction failed: {e}")

    # No valid paths found - check for SQL/bash steps via legacy regex
    legacy_steps = self._extract_steps_via_regex(instructions)
    if legacy_steps:
        print(f"[Extraction] Legacy regex found {len(legacy_steps)} steps (SQL/bash)")
        return legacy_steps

    print("[Extraction] WARNING: No valid paths or steps extracted from instructions")
    return []

def _build_steps_from_paths(self, paths: List[Dict], instructions: str) -> List[Dict]:
    """
    Build executable steps from validated paths.

    Extracts code content for each path from the instruction text.

    Args:
        paths: List of validated path dicts
        instructions: Original instruction text

    Returns:
        List of step dicts with type, path, content
    """
    steps = []

    for path_info in paths:
        path = path_info['path']

        # Try to extract code content for this path
        content = self._extract_code_for_path(path, instructions)

        if content:
            steps.append({
                'type': 'file',
                'path': path,
                'content': content,
                'mode': 'CREATE' if not os.path.exists(path) else 'MODIFY',
                'source': path_info['source']
            })
        else:
            print(f"[Build] Warning: No code content found for {path}")

    return steps

def _extract_code_for_path(self, path: str, instructions: str) -> Optional[str]:
    """
    Extract the code content associated with a file path.

    Looks for code blocks following the path mention.

    Args:
        path: The file path to find content for
        instructions: The instruction text

    Returns:
        The code content string, or None if not found
    """
    # Pattern: path followed by code block
    # Handles: **File:** /path\n```python\ncode\n```

    escaped_path = re.escape(path)

    patterns = [
        # Path then code block (with optional language)
        rf'{escaped_path}[^\n]*\n+```(?:\w+)?\n(.*?)```',
        # Path in header then code block
        rf'{escaped_path}.*?\n+```(?:\w+)?\n(.*?)```',
    ]

    for pattern in patterns:
        match = re.search(pattern, instructions, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return None
```

### Phase 5: Add Validation to RLM Executor

**File:** `/ganuda/lib/rlm_executor.py`

Add path validation before file operations in the RLM executor:

```python
# Add near top of file
PLACEHOLDER_PATTERNS = [
    r'/path/to/',
    r'/example/',
    r'<[^>]+>',
    r'\$\{[^}]+\}',
    r'\{\{[^}]+\}\}',
    r'/your/',
    r'/my/',
]

ALLOWED_PATH_PREFIXES = ['/ganuda/', '/tmp/', '/home/dereadi/']

def _validate_path(path: str) -> tuple:
    """Validate path before file operations."""
    if not path:
        return False, "Empty path"

    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, path, re.IGNORECASE):
            return False, f"Placeholder: {pattern}"

    if not path.startswith('/'):
        return False, "Not absolute"

    if not any(path.startswith(p) for p in ALLOWED_PATH_PREFIXES):
        return False, "Not in allowed directory"

    if '..' in path:
        return False, "Directory traversal"

    return True, ""

# In the execute() method or file writing section, add:
# Before writing any file:
is_valid, error = _validate_path(file_path)
if not is_valid:
    print(f"[RLM] BLOCKED invalid path: {file_path} - {error}")
    continue  # Skip this file, don't write
```

## Testing

After implementation, run these tests:

### Test 1: Validation Function
```python
# /ganuda/jr_executor/test_path_extraction.py

test_paths = [
    ("/path/to/file.py", False, "placeholder"),
    ("/ganuda/lib/real.py", True, "valid"),
    ("/example/code.js", False, "placeholder"),
    ("../../../etc/passwd", False, "traversal"),
    ("relative/path.py", False, "not absolute"),
    ("/ganuda/lib/${var}.py", False, "variable"),
    ("/etc/passwd", False, "not allowed dir"),
    ("/ganuda/sag/app.py", True, "valid"),
]

for path, expected_valid, description in test_paths:
    is_valid, error = executor._validate_path(path)
    status = "PASS" if is_valid == expected_valid else "FAIL"
    print(f"[{status}] {path}: {description}")
```

### Test 2: Regex Extraction
```python
test_instruction = """
**File:** `/ganuda/lib/module.py`

```python
def hello():
    pass
```

Create file: /ganuda/sag/routes/new.py

Also modify `/ganuda/lib/helper.py`
"""

paths = executor._extract_paths_via_enhanced_regex(test_instruction)
# Expected: 3 paths found
```

### Test 3: Re-run Failed Tasks
```sql
-- Reset tasks for re-testing
UPDATE jr_work_queue
SET status = 'pending',
    result = NULL,
    started_at = NULL,
    completed_at = NULL
WHERE id IN (257, 258, 260, 262, 263);
```

## Verification

- [ ] Path validation rejects all placeholder patterns
- [ ] Enhanced regex extracts paths from ATOMIC format
- [ ] LLM extraction only runs when regex finds nothing
- [ ] All paths validated before file operations
- [ ] Re-run of tasks 257-263 creates actual files

## Council Vote Reference

**Audit Hash:** 28d18d80e447505f
**Recommendation:** Hybrid Approach (D)
**Confidence:** 87.3%
**Key Concerns Addressed:**
- Crawdad: Path validation/sanitization before file ops
- Gecko: Regex-first reduces LLM latency
- Turtle: Sustainable hybrid approach
- Raven: Balanced immediate fix + long-term improvement

## For Seven Generations

This fix ensures reliable Jr task execution for generations to come.
Path validation protects against security vulnerabilities.
The hybrid approach balances reliability with adaptability.

# JR Instruction: RLM Executor File Extraction Fix

**Task ID:** RLM-EXTRACT-001
**Priority:** P1 - Air Gap Critical
**Type:** bugfix
**Assigned:** Software Engineer Jr.

---

## Problem

The RLM Executor marks tasks as complete but doesn't extract files from LLM responses.

Log evidence:
```
WARNING:rlm_executor:[RLM] No files extracted from response (211 chars)
INFO:rlm_executor:[RLM] Created 0 file(s) from response
[RLM] Execution complete. Success: True, Subtasks: 1, Artifacts: 0
```

This breaks air-gapped operation where Jrs must create files autonomously.

---

## Root Cause

The file extraction regex in `rlm_executor.py` doesn't match the LLM's actual output format.

Current extraction looks for specific patterns but LLM outputs vary:
1. Python `with open('path', 'w')` blocks
2. Markdown code blocks with `# filepath:` comments
3. JSON structures like `{"files_created": [...]}`

---

## Fix Required

Update `/ganuda/lib/rlm_executor.py` to handle multiple output formats.

### 1. Add Multi-Format Extraction

```python
def extract_files_from_response(response: str) -> List[Dict]:
    """
    Extract file creation instructions from LLM response.
    Handles multiple output formats.
    """
    files = []

    # Format 1: Python with open() blocks
    python_pattern = r"with open\(['\"](.+?)['\"]\s*,\s*['\"]w['\"]\)\s*as\s*\w+:\s*\n\s*\w+\.write\(['\"\"\"](.+?)['\"\"\"]\)"
    for match in re.finditer(python_pattern, response, re.DOTALL):
        files.append({
            'path': match.group(1),
            'content': match.group(2)
        })

    # Format 2: Markdown code blocks with filepath comment
    md_pattern = r"```(?:python|bash|yaml|json)?\n# (?:filepath|file|path):\s*(.+?)\n(.+?)```"
    for match in re.finditer(md_pattern, response, re.DOTALL | re.IGNORECASE):
        files.append({
            'path': match.group(1).strip(),
            'content': match.group(2)
        })

    # Format 3: SEARCH/REPLACE blocks (Safe Edit format)
    sr_pattern = r"<<<<<<< SEARCH\n(.+?)\n=======\n(.+?)\n>>>>>>> REPLACE"
    # Handle these separately as edits, not new files

    # Format 4: JSON file list
    json_pattern = r'\{"files_created":\s*\[(.+?)\]'
    json_match = re.search(json_pattern, response, re.DOTALL)
    if json_match and not files:
        # Parse JSON file list
        try:
            import json
            file_list = json.loads(f'[{json_match.group(1)}]')
            # These are just paths, content must come from elsewhere
        except:
            pass

    # Format 5: Direct file content with header
    header_pattern = r"# File: (.+?)\n```\n(.+?)```"
    for match in re.finditer(header_pattern, response, re.DOTALL):
        files.append({
            'path': match.group(1).strip(),
            'content': match.group(2)
        })

    return files
```

### 2. Add Fallback Content Extraction

If file paths are found but content isn't in the expected format, search for content blocks:

```python
def extract_content_for_path(response: str, file_path: str) -> Optional[str]:
    """Find content for a file path mentioned in the response."""
    # Look for content after the path is mentioned
    path_escaped = re.escape(file_path)

    patterns = [
        rf"{path_escaped}.*?```(?:\w+)?\n(.+?)```",
        rf"Content for {path_escaped}:\n(.+?)(?=\n\n|\Z)",
        rf"Write to {path_escaped}:\n```\n(.+?)```"
    ]

    for pattern in patterns:
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1)

    return None
```

### 3. Add Logging for Debug

```python
def parse_response_for_files(response: str) -> List[Dict]:
    """Parse response and log extraction attempts."""
    logger.info(f"[RLM] Parsing response ({len(response)} chars)")

    files = extract_files_from_response(response)

    if files:
        logger.info(f"[RLM] Extracted {len(files)} file(s)")
        for f in files:
            logger.debug(f"[RLM]   - {f['path']} ({len(f.get('content', ''))} chars)")
    else:
        logger.warning(f"[RLM] No files extracted. Response preview: {response[:200]}")
        # Log patterns tried for debugging
        logger.debug(f"[RLM] Response contains 'with open': {'with open' in response}")
        logger.debug(f"[RLM] Response contains '```': {'```' in response}")
        logger.debug(f"[RLM] Response contains 'files_created': {'files_created' in response}")

    return files
```

---

## Testing

1. Create test response with each format
2. Verify extraction works for all formats
3. Test with actual Jr task execution
4. Verify files are created on disk

---

## Success Criteria

- [ ] Files extracted from Python `with open()` blocks
- [ ] Files extracted from Markdown code blocks
- [ ] Files extracted from JSON file lists
- [ ] Logging shows extraction attempts
- [ ] Jr tasks create actual files

---

## For Seven Generations

Reliable file creation enables air-gapped operation - essential for secure deployments.

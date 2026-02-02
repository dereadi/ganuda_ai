# JR Instruction: Enhanced Regex Extraction for Partial Edits

**JR ID:** JR-ENHANCED-REGEX-EXTRACTION-JAN27-2026
**Priority:** P1
**Assigned To:** Software Engineer Jr.
**Council Vote:** 8f3a1e9f4b86ded5 (85% confidence)
**Ultrathink:** ULTRATHINK-HYBRID-SMART-EXTRACTION-JAN27-2026.md
**Effort:** Medium (2-3 hours)

---

## Objective

Enhance the regex extraction in `task_executor.py` to detect target files from JR instruction headers and prose, enabling Jrs to apply partial code edits autonomously.

---

## Files Modified

| File | Change |
|------|--------|
| `/ganuda/jr_executor/task_executor.py` | Add smart file extraction methods |

---

## Changes Required

### 1. Add New Method: `_extract_target_file_from_header()`

Add this method after `_validate_path()` (around line 240):

```python
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
        import re

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
```

---

### 2. Add New Method: `_extract_file_from_prose()`

Add this method after `_extract_target_file_from_header()`:

```python
    def _extract_file_from_prose(self, text: str) -> Optional[str]:
        """
        Extract file path from prose text before a code block.

        Looks for patterns like:
        - "Modify `/ganuda/lib/file.py`"
        - "Update `/ganuda/lib/file.py`"
        - "In `/ganuda/lib/file.py`, add:"
        - "to `/ganuda/lib/file.py`:"

        Args:
            text: The prose text before a code block (typically 300 chars)

        Returns:
            File path if found, else None.
        """
        import re

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
```

---

### 3. Enhance `_extract_steps_via_regex()` Method

Find the `_extract_steps_via_regex` method (around line 783) and replace it with this enhanced version:

```python
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

        # Pattern to match code blocks with language hint
        code_block_pattern = r'```(\w+)\n(.*?)```'

        # Find all code blocks
        matches = re.findall(code_block_pattern, instructions, re.DOTALL)

        for lang, content in matches:
            content = content.strip()

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
                # Look for file path in preceding text
                block_start = instructions.find(f'```{lang}\n{content}')
                if block_start == -1:
                    # Try without newline
                    block_start = instructions.find(f'```{lang}')

                filepath = None

                if block_start > 0:
                    # Check preceding 500 chars for file path patterns
                    preceding_text = instructions[max(0, block_start-500):block_start]

                    # Try existing patterns first
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

                    # If no match, try prose extraction
                    if not filepath:
                        filepath = self._extract_file_from_prose(preceding_text)

                # If still no filepath but we have a single target file, use it
                if not filepath and target_file:
                    # Only for Python files modifying the target
                    if lang.lower() == 'python' and target_file.endswith('.py'):
                        filepath = target_file
                        print(f"[SmartExtract] Attributing Python block to target: {filepath}")

                if filepath:
                    # Validate path before adding
                    is_valid, error = self._validate_path(filepath)
                    if is_valid:
                        steps.append({
                            'type': 'file',
                            'args': {
                                'operation': 'write',
                                'path': filepath,
                                'content': content
                            }
                        })
                        print(f"[SmartExtract] Extracted file step: {filepath} ({len(content)} chars)")
                    else:
                        print(f"[SmartExtract] Rejected invalid path: {filepath} - {error}")
                else:
                    print(f"[SmartExtract] Skipping {lang} block - no file path found")

        print(f"[SmartExtract] Total steps extracted: {len(steps)}")
        return steps
```

---

## Verification Steps

1. **Syntax check:**
   ```bash
   cd /ganuda/jr_executor && python3 -m py_compile task_executor.py && echo "Syntax OK"
   ```

2. **Test extraction with sample instruction:**
   ```bash
   cd /ganuda/jr_executor && python3 -c "
   from task_executor import TaskExecutor
   executor = TaskExecutor()

   test_instruction = '''
   ## Files Modified
   | File | Change |
   | \`/tmp/test_smart_extract.py\` | Test file |

   ### Add Function

   \`\`\`python
   def hello():
       return \"world\"
   \`\`\`
   '''

   steps = executor._extract_steps_via_regex(test_instruction)
   print(f'Steps found: {len(steps)}')
   for s in steps:
       print(f'  Type: {s.get(\"type\")}, Path: {s.get(\"args\", {}).get(\"path\", \"N/A\")}')
   "
   ```

3. **Expected output:**
   ```
   [SmartExtract] Found single target file: /tmp/test_smart_extract.py
   [SmartExtract] Attributing Python block to target: /tmp/test_smart_extract.py
   [SmartExtract] Extracted file step: /tmp/test_smart_extract.py (28 chars)
   [SmartExtract] Total steps extracted: 1
   Steps found: 1
     Type: file, Path: /tmp/test_smart_extract.py
   ```

---

## Rollback

If issues occur:
```bash
git -C /ganuda checkout jr_executor/task_executor.py
```

---

FOR SEVEN GENERATIONS

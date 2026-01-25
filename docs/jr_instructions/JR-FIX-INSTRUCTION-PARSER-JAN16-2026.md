# JR Instruction: Fix Instruction Parser for Better Markdown Support

## Overview

The task_executor.py instruction parser has limited pattern matching that misses many valid instruction formats. This causes tasks to be marked "complete" without execution.

## Problem Analysis

Current parser (`_extract_steps_from_instructions` in task_executor.py lines 171-225):
- Only looks for `Create \`path\`` pattern (with backticks) before ```python blocks
- Searches only 200 chars before code block
- Doesn't recognize `Create /path:` format (without backticks)
- Doesn't handle ### Task sections or ## Verification sections

## Solution

Update the file pattern regex to support multiple formats.

Create `/ganuda/jr_executor/task_executor_patch.py`:

```python
#!/usr/bin/env python3
"""
Patch task_executor.py to support more instruction formats.
Cherokee AI Federation - January 2026
"""

import re

TASK_EXECUTOR_PATH = '/ganuda/jr_executor/task_executor.py'

# Read current file
with open(TASK_EXECUTOR_PATH, 'r') as f:
    content = f.read()

# Check if already patched
if 'PATCHED: JAN16-2026' in content:
    print('Already patched')
    exit(0)

# Find the _extract_steps_from_instructions method and replace it
old_method = '''    def _extract_steps_from_instructions(self, instructions: str) -> List[Dict]:
        """
        Extract executable steps from a Jr instruction markdown file.

        Looks for code blocks with action hints:
        - ```sql → SQL action
        - ```bash or ```shell → Bash action
        - ```python with Create `/path/file` → File action

        Returns list of step dicts ready for execute_steps()
        """
        steps = []

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
            elif lang.lower() == 'python':
                # Look for file creation pattern before this code block
                # Pattern: Create `/path/to/file`:
                file_pattern = r"Create\s+`([^`]+)`"

                # Search in the text before this code block
                block_start = instructions.find(f'```{lang}\n{content}')
                if block_start > 0:
                    preceding_text = instructions[max(0, block_start-200):block_start]
                    file_match = re.search(file_pattern, preceding_text)

                    if file_match:
                        filepath = file_match.group(1)
                        steps.append({
                            'type': 'file',
                            'args': {
                                'operation': 'write',
                                'path': filepath,
                                'content': content
                            }
                        })

        return steps'''

new_method = '''    def _extract_steps_from_instructions(self, instructions: str) -> List[Dict]:
        """
        Extract executable steps from a Jr instruction markdown file.
        PATCHED: JAN16-2026 - Extended pattern support

        Looks for code blocks with action hints:
        - ```sql → SQL action
        - ```bash or ```shell → Bash action
        - ```python/bash with Create `/path/file`: → File action
        - Multiple file pattern formats supported

        Returns list of step dicts ready for execute_steps()
        """
        steps = []

        # Pattern to match code blocks with language hint
        code_block_pattern = r'```(\w+)\n(.*?)```'

        # Multiple file creation patterns (expanded support)
        file_patterns = [
            r"Create\s+[`\"']([^`\"']+)[`\"']",           # Create `/path` or Create "/path"
            r"Create\s+(/[^\s:]+)\s*:",                   # Create /path: (no quotes)
            r"File:\s*[`\"']?(/[^\s`\"':]+)[`\"']?",      # File: /path
        ]

        # Find all code blocks
        matches = re.findall(code_block_pattern, instructions, re.DOTALL)

        for lang, code_content in matches:
            code_content = code_content.strip()

            if lang.lower() == 'sql':
                steps.append({
                    'type': 'sql',
                    'command': code_content
                })
            elif lang.lower() in ('bash', 'shell', 'sh'):
                # Check if this bash block is preceded by a Create pattern
                block_start = instructions.find(f'```{lang}\\n{code_content}')
                if block_start == -1:
                    block_start = instructions.find(f'```{lang}')

                filepath = None
                if block_start > 0:
                    preceding_text = instructions[max(0, block_start-300):block_start]
                    for pattern in file_patterns:
                        file_match = re.search(pattern, preceding_text, re.IGNORECASE)
                        if file_match:
                            filepath = file_match.group(1)
                            break

                if filepath:
                    # This is a file creation, not a command
                    steps.append({
                        'type': 'file',
                        'args': {
                            'operation': 'write',
                            'path': filepath,
                            'content': code_content
                        }
                    })
                else:
                    # Regular bash command
                    steps.append({
                        'type': 'bash',
                        'command': code_content
                    })
            elif lang.lower() == 'python':
                # Look for file creation pattern before this code block
                block_start = instructions.find(f'```{lang}\\n{code_content}')
                if block_start == -1:
                    block_start = instructions.find(f'```{lang}')

                filepath = None
                if block_start > 0:
                    preceding_text = instructions[max(0, block_start-300):block_start]
                    for pattern in file_patterns:
                        file_match = re.search(pattern, preceding_text, re.IGNORECASE)
                        if file_match:
                            filepath = file_match.group(1)
                            break

                if filepath:
                    steps.append({
                        'type': 'file',
                        'args': {
                            'operation': 'write',
                            'path': filepath,
                            'content': code_content
                        }
                    })

        return steps'''

if old_method in content:
    content = content.replace(old_method, new_method)
    with open(TASK_EXECUTOR_PATH, 'w') as f:
        f.write(content)
    print('Patch applied successfully')
else:
    print('Could not find exact method to patch - manual review needed')
    print('The method signature may have changed')
```

## Verification

```bash
cd /ganuda/jr_executor && python3 task_executor_patch.py
```

```bash
grep -A5 "PATCHED: JAN16-2026" /ganuda/jr_executor/task_executor.py
```

---

*Cherokee AI Federation - For the Seven Generations*

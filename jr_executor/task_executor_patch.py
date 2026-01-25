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
        -
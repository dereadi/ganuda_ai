#!/usr/bin/env python3
"""
Cherokee IT Jr - Instruction Parser
Parses markdown instruction files into executable steps.

Extracts:
- Code blocks with language tags (python, bash, sql)
- File creation tasks (Create `/path/to/file.py`:)
- Verification commands
- Success criteria

For Seven Generations
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class InstructionStep:
    """A single executable step extracted from instructions"""
    step_type: str  # 'file', 'bash', 'sql', 'verify'
    description: str
    content: str
    target_path: Optional[str] = None
    critical: bool = True


class InstructionParser:
    """
    Parses markdown instruction files into executable steps.

    Recognizes patterns like:
    - Create `/path/file.py`: followed by ```python code block
    - ```bash commands
    - ```sql queries
    - Verification sections with test commands
    """

    # Regex patterns for parsing
    FILE_CREATE_PATTERN = re.compile(
        r"Create\s+[`\"']?(/[^`\"'\s:]+)[`\"']?\s*:?\s*\n+```(\w+)?\n(.*?)```",
        re.DOTALL | re.IGNORECASE
    )

    CODE_BLOCK_PATTERN = re.compile(
        r'```(\w+)?\n(.*?)```',
        re.DOTALL
    )

    TASK_HEADER_PATTERN = re.compile(
        r'###\s+Task\s+(\d+):\s+(.+)',
        re.IGNORECASE
    )

    VERIFY_SECTION_PATTERN = re.compile(
        r'##\s+Verification\s*\n+(.*?)(?=##|---|\Z)',
        re.DOTALL | re.IGNORECASE
    )

    def parse(self, markdown_content: str) -> List[InstructionStep]:
        """Parse markdown content into executable steps"""
        steps = []

        # Extract file creation tasks
        steps.extend(self._extract_file_tasks(markdown_content))

        # Extract verification commands
        steps.extend(self._extract_verification(markdown_content))

        return steps

    def _extract_file_tasks(self, content: str) -> List[InstructionStep]:
        """Extract file creation tasks from markdown"""
        steps = []

        for match in self.FILE_CREATE_PATTERN.finditer(content):
            target_path = match.group(1)
            language = match.group(2) or 'text'
            code_content = match.group(3).strip()

            steps.append(InstructionStep(
                step_type='file',
                description=f'Create {target_path}',
                content=code_content,
                target_path=target_path,
                critical=True
            ))

        return steps

    def _extract_verification(self, content: str) -> List[InstructionStep]:
        """Extract verification commands from markdown"""
        steps = []

        verify_match = self.VERIFY_SECTION_PATTERN.search(content)
        if not verify_match:
            return steps

        verify_content = verify_match.group(1)

        # Find bash code blocks in verification section
        for block_match in self.CODE_BLOCK_PATTERN.finditer(verify_content):
            language = block_match.group(1) or ''
            code = block_match.group(2).strip()

            if language.lower() in ['bash', 'sh', 'shell', '']:
                # Handle different cd patterns:
                # Pattern 1: "cd /path && command" (single line with &&)
                # Pattern 2: "cd /path\ncommand" (multiline)
                # Pattern 3: Just commands (no cd)

                cwd = None
                command = code

                if code.startswith('cd '):
                    # Check for "cd /path && rest" pattern (single line)
                    if ' && ' in code.split('\n')[0]:
                        first_line = code.split('\n')[0]
                        # Split on first ' && '
                        cd_part, rest = first_line.split(' && ', 1)
                        cwd = cd_part.replace('cd ', '').strip()
                        # Remaining command is rest of first line + any other lines
                        other_lines = '\n'.join(code.split('\n')[1:]).strip()
                        if other_lines:
                            command = rest + '\n' + other_lines
                        else:
                            command = rest
                    else:
                        # Multiline: first line is cd, rest is commands
                        lines = code.split('\n')
                        cwd = lines[0].replace('cd ', '').strip()
                        command = '\n'.join(lines[1:]).strip()

                # Only add step if we have a command to run
                if command:
                    step = InstructionStep(
                        step_type='bash',
                        description='Run verification commands',
                        content=command,
                        target_path=cwd,  # Use as cwd (None if no cd)
                        critical=False  # Verification shouldn't stop execution
                    )
                    steps.append(step)

        return steps

    def to_executor_format(self, steps: List[InstructionStep]) -> List[Dict]:
        """Convert InstructionSteps to TaskExecutor format"""
        executor_steps = []

        for step in steps:
            if step.step_type == 'file':
                executor_steps.append({
                    'type': 'file',
                    'description': step.description,
                    'args': {
                        'operation': 'write',
                        'path': step.target_path,
                        'content': step.content,
                        'backup': True
                    },
                    'critical': step.critical
                })

            elif step.step_type == 'bash':
                executor_step = {
                    'type': 'bash',
                    'description': step.description,
                    'command': step.content,
                    'critical': step.critical
                }
                if step.target_path:  # Use as cwd
                    executor_step['cwd'] = step.target_path
                executor_steps.append(executor_step)

            elif step.step_type == 'sql':
                executor_steps.append({
                    'type': 'sql',
                    'description': step.description,
                    'command': step.content,
                    'critical': step.critical
                })

        return executor_steps


def parse_instructions(markdown_content: str) -> List[Dict]:
    """Convenience function to parse markdown to executor format"""
    parser = InstructionParser()
    steps = parser.parse(markdown_content)
    return parser.to_executor_format(steps)


if __name__ == "__main__":
    print("Instruction Parser Self-Test")
    print("=" * 50)

    # Test with sample markdown
    sample = '''
# Test Instructions

## Tasks

### Task 1: Create Test File

Create `/ganuda/jr_executor/test_output.py`:

```python
#!/usr/bin/env python3
print("Hello from test")
```

## Verification

```bash
cd /ganuda/jr_executor
python3 -c "print('Verification passed')"
```
'''

    parser = InstructionParser()
    steps = parser.parse(sample)

    print(f"\nFound {len(steps)} steps:")
    for i, step in enumerate(steps):
        print(f"  {i+1}. [{step.step_type}] {step.description}")
        if step.target_path:
            print(f"      Path: {step.target_path}")

    print("\nExecutor format:")
    executor_steps = parser.to_executor_format(steps)
    for step in executor_steps:
        print(f"  {step.get('type')}: {step.get('description')}")

    print(f"\n{'=' * 50}")
    print("Self-test complete - For Seven Generations")

# JR INSTRUCTIONS: Fix Bash Command Parser Bug
## JR-BUGFIX-BASH-PARSER-DEC17-2025
## December 17, 2025

### OBJECTIVE
Fix bug in instruction_parser.py where `cd /path && command` patterns are incorrectly parsed.

---

## BUG DESCRIPTION

**File:** /ganuda/jr_executor/instruction_parser.py

**Current Behavior:**
When verification section contains:
```bash
cd /ganuda/jr_executor && /home/dereadi/cherokee_venv/bin/python3 thermal_queue.py
```

The parser incorrectly splits on first space after `cd `, resulting in:
- cwd = `/ganuda/jr_executor && /home/dereadi/cherokee_venv/bin/python3 thermal_queue.py`
- command = (empty or malformed)

**Error Message:**
```
[Errno 2] No such file or directory: '/ganuda/jr_executor && ...'
```

---

## TASK 1: Fix the _extract_verification method

**File:** /ganuda/jr_executor/instruction_parser.py

**Find this code block:**
```python
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
                # Check if it's a cd + command pattern
                if code.startswith('cd '):
                    lines = code.split('\n')
                    cwd = lines[0].replace('cd ', '').strip()
                    remaining = '\n'.join(lines[1:]).strip()

                    steps.append(InstructionStep(
                        step_type='bash',
                        description='Run verification commands',
                        content=remaining,
                        target_path=cwd,  # Use as cwd
                        critical=False  # Verification shouldn't stop execution
                    ))
                else:
                    steps.append(InstructionStep(
                        step_type='bash',
                        description='Run verification command',
                        content=code,
                        critical=False
                    ))

        return steps
```

**Replace with:**
```python
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
```

---

## TASK 2: Add unit test for the fix

**File:** /ganuda/jr_executor/test_instruction_parser.py (create new)

```python
#!/usr/bin/env python3
"""Unit tests for instruction_parser.py - especially bash cd && patterns"""

import sys
sys.path.insert(0, '/ganuda/jr_executor')

from instruction_parser import InstructionParser, parse_instructions

def test_cd_and_command():
    """Test 'cd /path && command' pattern"""
    markdown = '''
## Verification

```bash
cd /ganuda/jr_executor && python3 test.py
```
'''
    steps = parse_instructions(markdown)
    assert len(steps) == 1
    step = steps[0]
    assert step['type'] == 'bash'
    assert step['cwd'] == '/ganuda/jr_executor'
    assert step['command'] == 'python3 test.py'
    print("PASS: cd && command pattern")

def test_cd_multiline():
    """Test multiline cd then commands"""
    markdown = '''
## Verification

```bash
cd /tmp
echo "hello"
python3 -c "print('world')"
```
'''
    steps = parse_instructions(markdown)
    assert len(steps) == 1
    step = steps[0]
    assert step['type'] == 'bash'
    assert step['cwd'] == '/tmp'
    assert 'echo' in step['command']
    assert 'python3' in step['command']
    print("PASS: cd multiline pattern")

def test_no_cd():
    """Test commands without cd"""
    markdown = '''
## Verification

```bash
echo "just a command"
```
'''
    steps = parse_instructions(markdown)
    assert len(steps) == 1
    step = steps[0]
    assert step['type'] == 'bash'
    assert step.get('cwd') is None
    assert step['command'] == 'echo "just a command"'
    print("PASS: no cd pattern")

def test_complex_cd_and():
    """Test complex cd && with full path python"""
    markdown = '''
## Verification

```bash
cd /ganuda/jr_executor && /home/dereadi/cherokee_venv/bin/python3 thermal_queue.py
```
'''
    steps = parse_instructions(markdown)
    assert len(steps) == 1
    step = steps[0]
    assert step['type'] == 'bash'
    assert step['cwd'] == '/ganuda/jr_executor'
    assert step['command'] == '/home/dereadi/cherokee_venv/bin/python3 thermal_queue.py'
    print("PASS: complex cd && pattern (the original bug case)")

if __name__ == '__main__':
    print("=" * 60)
    print("Testing instruction_parser.py bash patterns")
    print("=" * 60)

    test_cd_and_command()
    test_cd_multiline()
    test_no_cd()
    test_complex_cd_and()

    print("=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
```

---

## Verification

```bash
cd /ganuda/jr_executor && /home/dereadi/cherokee_venv/bin/python3 test_instruction_parser.py
```

---

## SUCCESS CRITERIA

1. Test script passes all 4 test cases
2. `cd /path && command` correctly splits into cwd=/path, command=command
3. Multiline `cd /path\ncommands` still works
4. Commands without cd work unchanged

---

*Jr Instructions issued: December 17, 2025*
*For Seven Generations - Cherokee AI Federation*

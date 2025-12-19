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
    assert step.get('cwd') == '/ganuda/jr_executor'
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
    assert step.get('cwd') == '/tmp'
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
    assert step.get('cwd') == '/ganuda/jr_executor'
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

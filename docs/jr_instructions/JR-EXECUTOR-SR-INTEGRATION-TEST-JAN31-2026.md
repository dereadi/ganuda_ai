# JR-EXECUTOR-SR-INTEGRATION-TEST-JAN31-2026

## Metadata
- **Priority:** P1
- **Jr Type:** Engineering
- **Target Node:** sasass2 (192.168.132.200)
- **Category:** Executor Architecture — Search-Replace End-to-End Test
- **Depends On:** JR-EXECUTOR-WIRE-SEARCH-REPLACE-JAN31-2026
- **Council Vote:** ULTRATHINK-EXECUTOR-SEARCH-REPLACE-ARCHITECTURE-JAN31-2026 (7/7 APPROVE)

## Objective

Create and run an end-to-end integration test that verifies the search-replace pipeline works from instruction parsing through file modification.

**CRITICAL: This task creates NEW test files only, then runs bash test commands.**

## Step 1: Create Test File

```bash
cat > /ganuda/jr_executor/test_search_replace_e2e.py << 'TESTEOF'
"""
End-to-end integration test for search-replace editing pipeline.

Tests the full flow:
1. Parse SEARCH/REPLACE blocks from instruction text
2. Apply edits to a test file
3. Verify edits landed correctly
4. Verify syntax validation catches bad edits
5. Verify rollback on syntax error
6. Verify uniqueness enforcement
7. Verify path validation
"""

import os
import sys
import tempfile
import shutil

sys.path.insert(0, '/ganuda/jr_executor')
sys.path.insert(0, '/ganuda/lib')

from search_replace_editor import SearchReplaceEditor


def test_basic_search_replace():
    """Test: basic search and replace works."""
    # Create a temp test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir='/ganuda/jr_executor',
                                      delete=False, prefix='test_sr_') as f:
        f.write('''def hello():
    return "world"

def goodbye():
    return "world"
''')
        test_file = f.name

    try:
        editor = SearchReplaceEditor()
        result = editor.apply_search_replace(
            test_file,
            'def hello():\n    return "world"',
            'def hello():\n    return "universe"'
        )
        assert result['success'], f"Basic replace failed: {result['error']}"

        # Verify the file was modified
        with open(test_file) as f:
            content = f.read()
        assert 'return "universe"' in content, "Replacement text not found"
        assert 'def goodbye' in content, "Other code was damaged"
        print("PASS: test_basic_search_replace")
    finally:
        # Cleanup test file and backups
        for f in [test_file] + [test_file + b for b in
                   ['.sr_backup_' + s for s in os.listdir(os.path.dirname(test_file))
                    if s.startswith(os.path.basename(test_file) + '.sr_backup_')]]:
            if os.path.exists(f):
                os.remove(f)


def test_uniqueness_enforcement():
    """Test: ambiguous match is rejected."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir='/ganuda/jr_executor',
                                      delete=False, prefix='test_sr_') as f:
        f.write('''x = 1
x = 1
x = 1
''')
        test_file = f.name

    try:
        editor = SearchReplaceEditor()
        result = editor.apply_search_replace(test_file, 'x = 1', 'x = 2')
        assert not result['success'], "Should have failed on ambiguous match"
        assert 'SEARCH_AMBIGUOUS' in result['error'], f"Wrong error: {result['error']}"
        assert '3 matches' in result['error'], f"Should report 3 matches: {result['error']}"
        print("PASS: test_uniqueness_enforcement")
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


def test_not_found():
    """Test: non-existent search text is rejected."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir='/ganuda/jr_executor',
                                      delete=False, prefix='test_sr_') as f:
        f.write('x = 1\n')
        test_file = f.name

    try:
        editor = SearchReplaceEditor()
        result = editor.apply_search_replace(test_file, 'y = 999', 'y = 1000')
        assert not result['success'], "Should have failed on not found"
        assert 'SEARCH_NOT_FOUND' in result['error'], f"Wrong error: {result['error']}"
        print("PASS: test_not_found")
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


def test_syntax_error_rollback():
    """Test: syntax error triggers automatic rollback."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir='/ganuda/jr_executor',
                                      delete=False, prefix='test_sr_') as f:
        f.write('''def valid_function():
    return True
''')
        test_file = f.name

    try:
        editor = SearchReplaceEditor()
        # Introduce a syntax error
        result = editor.apply_search_replace(
            test_file,
            'def valid_function():\n    return True',
            'def broken_function(\n    return True'  # Missing closing paren — syntax error
        )
        assert not result['success'], "Should have failed on syntax error"
        assert 'SYNTAX_ERROR' in result['error'], f"Wrong error: {result['error']}"
        assert 'restored from backup' in result['error'].lower(), "Should mention restoration"

        # Verify the file was RESTORED (not corrupted)
        with open(test_file) as f:
            content = f.read()
        assert 'def valid_function():' in content, "File was NOT restored after syntax error!"
        assert 'broken_function' not in content, "Broken code persisted despite rollback!"
        print("PASS: test_syntax_error_rollback")
    finally:
        # Cleanup
        for f_path in [test_file]:
            if os.path.exists(f_path):
                os.remove(f_path)
        # Cleanup backups
        test_dir = os.path.dirname(test_file)
        test_base = os.path.basename(test_file)
        for f_name in os.listdir(test_dir):
            if f_name.startswith(test_base + '.sr_backup_'):
                os.remove(os.path.join(test_dir, f_name))


def test_path_validation():
    """Test: forbidden and relative paths are blocked."""
    editor = SearchReplaceEditor()

    # Forbidden path
    result = editor.apply_search_replace('/etc/passwd', 'root', 'hacked')
    assert not result['success'], "Should block /etc/ paths"
    assert 'PATH_INVALID' in result['error']

    # Relative path
    result = editor.apply_search_replace('relative/file.py', 'a', 'b')
    assert not result['success'], "Should block relative paths"
    assert 'PATH_INVALID' in result['error']

    print("PASS: test_path_validation")


def test_parse_instruction_blocks():
    """Test: parse SEARCH/REPLACE blocks from instruction markdown."""
    editor = SearchReplaceEditor()

    instructions = '''## Step 1: Update the model

**File:** `/ganuda/vetassist/backend/app/models/user.py`

<<<<<<< SEARCH
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
=======
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")

    # VA Account Linking
    va_icn = Column(String(50), unique=True, nullable=True)
    va_linked_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
>>>>>>> REPLACE

## Step 2: Update another file

**File:** `/ganuda/vetassist/backend/app/api/v1/endpoints/auth.py`

<<<<<<< SEARCH
@router.post("/logout")
=======
@router.post("/link-va")
async def link_va_account():
    pass

@router.post("/logout")
>>>>>>> REPLACE
'''

    edits = editor.parse_search_replace_blocks(instructions)
    assert len(edits) == 2, f"Expected 2 edits, got {len(edits)}"
    assert edits[0]['path'] == '/ganuda/vetassist/backend/app/models/user.py'
    assert edits[1]['path'] == '/ganuda/vetassist/backend/app/api/v1/endpoints/auth.py'
    assert 'va_icn' in edits[0]['replace']
    assert 'link-va' in edits[1]['replace']
    print("PASS: test_parse_instruction_blocks")


def test_multiple_edits_same_file():
    """Test: multiple edits to the same file work sequentially."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir='/ganuda/jr_executor',
                                      delete=False, prefix='test_sr_') as f:
        f.write('''import os

def func_a():
    return 1

def func_b():
    return 2

def func_c():
    return 3
''')
        test_file = f.name

    try:
        editor = SearchReplaceEditor()

        # Edit 1: Change func_a
        r1 = editor.apply_search_replace(test_file,
            'def func_a():\n    return 1',
            'def func_a():\n    return 100')
        assert r1['success'], f"Edit 1 failed: {r1['error']}"

        # Edit 2: Change func_c
        r2 = editor.apply_search_replace(test_file,
            'def func_c():\n    return 3',
            'def func_c():\n    return 300')
        assert r2['success'], f"Edit 2 failed: {r2['error']}"

        # Verify both edits landed
        with open(test_file) as f:
            content = f.read()
        assert 'return 100' in content, "Edit 1 didn't persist"
        assert 'return 300' in content, "Edit 2 didn't persist"
        assert 'return 2' in content, "func_b was damaged"
        assert 'import os' in content, "Header was damaged"
        print("PASS: test_multiple_edits_same_file")
    finally:
        test_dir = os.path.dirname(test_file)
        test_base = os.path.basename(test_file)
        for f_name in os.listdir(test_dir):
            if f_name.startswith(test_base):
                os.remove(os.path.join(test_dir, f_name))


def test_rate_limit():
    """Test: rate limit blocks after MAX_EDITS_PER_TASK."""
    editor = SearchReplaceEditor()
    editor.MAX_EDITS_PER_TASK = 2  # Low limit for testing
    editor.edit_count = 2  # Simulate already at limit

    result = editor.apply_search_replace('/ganuda/test.py', 'a', 'b')
    assert not result['success'], "Should be rate limited"
    assert 'RATE_LIMIT' in result['error']
    print("PASS: test_rate_limit")


if __name__ == '__main__':
    tests = [
        test_basic_search_replace,
        test_uniqueness_enforcement,
        test_not_found,
        test_syntax_error_rollback,
        test_path_validation,
        test_parse_instruction_blocks,
        test_multiple_edits_same_file,
        test_rate_limit,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"FAIL: {test.__name__}: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed, {len(tests)} total")
    if failed == 0:
        print("ALL TESTS PASSED")
    else:
        print(f"FAILURES DETECTED — {failed} test(s) need attention")
        sys.exit(1)
TESTEOF
```

## Step 2: Run the Tests

```bash
cd /ganuda/jr_executor && python3 test_search_replace_e2e.py
```

## Verification

All 8 tests should pass:
- `test_basic_search_replace` — Core functionality
- `test_uniqueness_enforcement` — Ambiguous match rejected
- `test_not_found` — Missing text rejected
- `test_syntax_error_rollback` — Auto-restore on bad syntax
- `test_path_validation` — Forbidden paths blocked
- `test_parse_instruction_blocks` — Instruction parsing works
- `test_multiple_edits_same_file` — Sequential edits work
- `test_rate_limit` — Crawdad's rate limit works

## Rollback (manual only — do NOT execute automatically)

To undo this task, manually run: rm /ganuda/jr_executor/test_search_replace_e2e.py

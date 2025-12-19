# KB-JR-GUARDRAILS-001: Jr File Editing Guardrails

**Category**: Jr Agent Safety / Code Quality
**Created**: 2025-12-10
**Author**: Claude TPM
**Status**: Issue Identified - Fix Required
**Severity**: Critical

---

## Incident Summary

**Date**: 2025-12-10
**Mission**: JR-RESONANCE-002
**Task**: "Add record_resonance_event() method to JrExecutor class in /ganuda/jr_executor/jr_cli.py"

**What happened**:
- Jr interpreted "Add method" as "Replace entire file with just this method"
- jr_cli.py went from **805 lines → 26 lines**
- All existing code was lost (backup saved automatically)

**Impact**:
- Production jr_cli.py destroyed
- Restored from backup: `jr_cli.py.backup_20251210_191423`

---

## Root Cause Analysis

### The "Stub Code" Problem

From meeting notes (2025-12-10):
> Joe Dorn mentions watching a video about people getting "shenaniganed by Claude" and suggests this may be why the code built so far is mostly "stub code". Darrell Reading describes his method of letting Claude write stub code and then showing it examples of why it's not working to prompt it along.

### Technical Issue

The Jr's `task_executor.py` does not differentiate between:

| Operation | Intent | Current Behavior |
|-----------|--------|------------------|
| **EDIT** | Add/modify within existing file | ❌ Not implemented |
| **REPLACE** | Write completely new file | ✅ This is what happens |
| **APPEND** | Add to end of file | ❌ Not implemented |
| **INSERT** | Add at specific location | ❌ Not implemented |

When Jr receives "Add method to file", it generates the method and **writes it as the entire file content**.

---

## Required Guardrails

### 1. Backup Validation (Before Write)

```python
def safe_write(self, filepath: str, new_content: str) -> bool:
    """Write with safety checks"""

    # Always create timestamped backup
    backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy(filepath, backup_path)

    # Validate backup exists and is readable
    if not os.path.exists(backup_path):
        raise SafetyError("Backup creation failed")

    return True
```

### 2. Size Sanity Check

```python
def validate_write(self, filepath: str, old_content: str, new_content: str) -> bool:
    """Validate write won't destroy content"""

    old_lines = len(old_content.splitlines())
    new_lines = len(new_content.splitlines())

    # Alert if losing more than 50% of content
    if new_lines < old_lines * 0.5:
        raise SafetyError(
            f"Write would reduce file from {old_lines} to {new_lines} lines. "
            f"This looks like a replacement, not an edit. Aborting."
        )

    return True
```

### 3. Edit Mode vs Replace Mode

Tasks should explicitly specify the operation:

```json
{
    "tasks": [
        {
            "action": "EDIT",
            "file": "/ganuda/jr_executor/jr_cli.py",
            "operation": "insert_method",
            "class": "JrExecutor",
            "method_name": "record_resonance_event",
            "method_code": "def record_resonance_event(self, ...):\n    ..."
        }
    ]
}
```

vs

```json
{
    "tasks": [
        {
            "action": "REPLACE",
            "file": "/ganuda/new_file.py",
            "content": "..."
        }
    ]
}
```

### 4. Diff Preview (Future)

Before applying changes, Jr should:
1. Generate a diff
2. Log what will change
3. Optionally require approval for large changes

```python
def preview_changes(self, filepath: str, new_content: str) -> str:
    """Generate diff preview"""
    import difflib

    with open(filepath) as f:
        old_lines = f.readlines()

    new_lines = new_content.splitlines(keepends=True)

    diff = difflib.unified_diff(old_lines, new_lines,
                                 fromfile=f'{filepath} (before)',
                                 tofile=f'{filepath} (after)')

    return ''.join(diff)
```

### 5. Constitutional Check

Add to Jr's constitutional constraints:

```python
CONSTITUTIONAL_RULES = [
    "NEVER reduce a file to less than 50% of its original size without explicit REPLACE instruction",
    "ALWAYS verify backup exists before modifying files",
    "PREFER edit operations over replace operations",
    "REQUIRE human approval for changes affecting more than 100 lines",
]
```

---

## Immediate Mitigation

Until guardrails are implemented:

1. **Manual Review Required**: All Jr file modifications must be reviewed before deployment
2. **Backup Verification**: Confirm backups exist before running Jr missions
3. **Mission Format**: Use explicit "EDIT" vs "REPLACE" in task descriptions
4. **Size Monitoring**: Check file sizes after Jr runs

---

## Implementation Tasks

| Task | Priority | Status |
|------|----------|--------|
| Add size sanity check to task_executor.py | Critical | Pending |
| Implement EDIT vs REPLACE modes | High | Pending |
| Add diff preview logging | Medium | Pending |
| Update mission format specification | Medium | Pending |
| Add constitutional file protection rules | Medium | Pending |

---

## Related

- Kanban: JR-BUGFIX-001
- Meeting notes: Claude "stub code" discussion
- Backup: `/ganuda/jr_executor/jr_cli.py.backup_20251210_191423`

---

## Lessons Learned

1. **LLMs default to replacement**: When asked to "add" something, LLMs often generate just that thing, not the thing integrated into existing code
2. **Explicit instructions help but aren't enough**: Even with "Add to file X", Jr replaced the file
3. **Backups save lives**: The automatic backup feature prevented data loss
4. **Guardrails must be code, not prompts**: Prompt-based instructions aren't reliable enough for destructive operations

---

**For Seven Generations**: Build safety into the system, not just the instructions.

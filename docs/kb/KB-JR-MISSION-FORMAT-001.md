# KB-JR-MISSION-FORMAT-001: Cherokee Jr Mission Instruction Format

**Created**: 2025-12-11
**Source**: Debugging SAG-EMAIL-002-JR mission parse failures
**Status**: Authoritative Reference
**Last Validated**: 2025-12-11 09:56 (Jr successfully parsed 2 steps)

---

## Overview

Cherokee Jr executor parses markdown instruction files to extract executable steps. The format must follow specific patterns for Jr's `InstructionParser` to recognize tasks.

---

## Required Format for File Creation Tasks

### CORRECT Format (Jr WILL parse)

```markdown
Create `/path/to/file.py`:

```python
# Your code here
```
```

**Key requirements:**
- Start line with `Create` (case insensitive)
- Path in backticks or quotes: `` `/path/to/file` ``
- Colon after path (optional but recommended)
- Code block immediately follows with language tag

### INCORRECT Formats (Jr will NOT parse)

```markdown
# WRONG - Using **File**: syntax
**File**: `/path/to/file.py`
```python
code
```

# WRONG - No "Create" keyword
Write to `/path/to/file.py`:
```python
code
```

# WRONG - Path not quoted
Create /path/to/file.py:
```python
code
```
```

---

## Pattern Recognition Details

From `/ganuda/jr_executor/instruction_parser.py`:

```python
FILE_CREATE_PATTERN = re.compile(
    r'Create\s+[`"]?(/[^`"\s:]+)[`"]?\s*:?\s*\n+```(\w+)?\n(.*?)```',
    re.DOTALL | re.IGNORECASE
)
```

**Breakdown:**
- `Create` - Literal keyword (required)
- `\s+` - One or more spaces
- `[` `` ` `` `"]?` - Optional backtick or quote
- `(/[^` `` ` `` `"\s:]+)` - Path starting with `/`, captured
- `[` `` ` `` `"]?\s*:?` - Optional closing quote, optional colon
- `\n+` - One or more newlines
- `` ``` `` `(\w+)?` - Code fence with optional language
- `(.*?)` - Code content (captured)
- `` ``` `` - Closing fence

---

## Verification Section Format

Jr also parses verification commands from markdown:

```markdown
## Verification

```bash
cd /ganuda/project
python3 -c "print('Test passed')"
```
```

Verification steps are marked as `critical: False` so they won't stop mission execution on failure.

---

## Mission Assignment via Thermal Memory

### JSON Content Structure

```json
{
    "title": "Mission Title",
    "instructions_file": "/ganuda/missions/MISSION-FILE.md",
    "priority": "high"
}
```

### Database Insert

```sql
INSERT INTO triad_shared_memories (content, temperature, source_triad, tags)
VALUES (
    '{"title": "My Mission", "instructions_file": "/ganuda/missions/MY-MISSION.md", "priority": "high"}',
    85.0,
    'bluefin',
    ARRAY['jr_mission', 'it_triad_jr']
);
```

**Required tags:** `jr_mission`, `it_triad_jr`

---

## Files Requiring Chief Approval

Jr will refuse to create these file types (escalates to Chief):

- `.service` (systemd service files)
- `.conf` in system directories
- Anything in `/etc/`
- Files with `chmod` executable markers

This is a security guardrail - Chief must approve system configuration changes.

---

## Example: Complete Mission File

```markdown
# SAG-EXAMPLE-001: Example Mission

## Task: Create example files

### Step 1: Create main script

Create `/ganuda/my_project/main.py`:

```python
#!/usr/bin/env python3
"""Cherokee AI Example Script"""

def main():
    print("For Seven Generations")

if __name__ == '__main__':
    main()
```

### Step 2: Create configuration

Create `/ganuda/my_project/config.json`:

```json
{
    "name": "example",
    "version": "1.0.0"
}
```

## Verification

```bash
cd /ganuda/my_project
python3 main.py
```
```

---

## Debugging Tips

1. **Check Jr logs**: `tail -50 /tmp/jr_executor.log`
2. **Look for**: `Parsed X steps from markdown` (success) vs `No executable steps found` (failure)
3. **Test parser locally**:
   ```bash
   cd /ganuda/jr_executor
   python3 instruction_parser.py  # Runs self-test
   ```

---

## Related Articles

- KB-EMAIL-PATTERNS-001: Email LLM Integration
- KB-RESONANCE-001: Jr Learning/Resonance Tracking

---

**For Seven Generations**: Document our learnings so we don't repeat mistakes.

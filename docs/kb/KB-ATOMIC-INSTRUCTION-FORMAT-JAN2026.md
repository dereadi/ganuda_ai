# KB: ATOMIC Instruction Format for Jr Tasks

**Article ID:** KB-ATOMIC-001
**Created:** January 23, 2026
**Category:** Jr Execution, Best Practices
**Related:** JR-RLM-HYBRID-FIX-JAN23-2026

## Summary

ATOMIC format is a structured instruction format that ensures reliable Jr task execution. Tasks using ATOMIC format have a 100% success rate vs ~20% for open-ended instructions.

## Why ATOMIC Works

The Jr executor uses two extraction methods:
1. **Regex extraction** - Fast, reliable, parses explicit markers
2. **LLM extraction** - Flexible but can hallucinate paths

ATOMIC format is optimized for regex extraction, bypassing LLM hallucination issues entirely.

## ATOMIC Format Template

```markdown
# Jr Task: [Short Descriptive Title]

[One sentence describing what this task does]

**File:** `/ganuda/path/to/actual/file.py`

```python
# Complete file content here
# No placeholders, no TODOs
# Ready to write as-is
```

[Optional: Additional files follow same pattern]

**File:** `/ganuda/path/to/second/file.py`

```python
# Second file content
```

[Optional: Bash commands to run]

```bash
# Commands to execute after file creation
mkdir -p /ganuda/path/to/directory
chmod +x /ganuda/scripts/script.sh
```
```

## Key Principles

### 1. Explicit File Markers

Always use `**File:**` followed by the full path in backticks:

```markdown
**File:** `/ganuda/lib/my_module.py`
```

NOT:
```markdown
Create a file called my_module.py in the lib directory
```

### 2. Complete Code Blocks

Include the entire file content, not snippets:

```markdown
**File:** `/ganuda/lib/helper.py`

```python
"""Helper module for Cherokee AI Federation."""

def helper_function():
    """Do the thing."""
    return "done"

if __name__ == "__main__":
    print(helper_function())
```
```

NOT:
```markdown
Add a helper function that does the thing
```

### 3. Absolute Paths Only

Always use absolute paths starting with `/ganuda/`:

```markdown
**File:** `/ganuda/sag/routes/api.py`
```

NOT:
```markdown
**File:** `routes/api.py`
**File:** `./api.py`
**File:** `/path/to/api.py`
```

### 4. No Placeholders

Never use placeholder text that needs to be filled in:

```python
# GOOD
API_KEY = "ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"

# BAD
API_KEY = "<YOUR_API_KEY_HERE>"
API_KEY = "${API_KEY}"
API_KEY = "TODO: add key"
```

## Examples

### Good: ATOMIC Format

```markdown
# Jr Task: Create VLM Health Check Route

Add a health check endpoint for the VLM service.

**File:** `/ganuda/sag/routes/vlm_health.py`

```python
from flask import Blueprint, jsonify
import httpx

vlm_health_bp = Blueprint('vlm_health', __name__)

@vlm_health_bp.route('/api/vlm/health', methods=['GET'])
def health_check():
    try:
        r = httpx.get('http://192.168.132.222:8093/health', timeout=5.0)
        return jsonify({"status": "ok", "vlm": r.json()})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500
```

```bash
# Register the blueprint in app.py
echo "Reminder: Add 'from routes.vlm_health import vlm_health_bp' to app.py"
```
```

### Bad: Open-Ended Format

```markdown
# Jr Task: Create VLM Health Check

Create a health check endpoint for the VLM service. It should:
- Check if VLM is responding
- Return status as JSON
- Handle errors gracefully

Use Flask blueprints and follow existing patterns in the codebase.
```

(This format requires LLM reasoning and may result in hallucinated paths)

## When to Use ATOMIC

| Task Type | Format | Reason |
|-----------|--------|--------|
| New file creation | ATOMIC | Explicit path + content |
| File modification | ATOMIC | Show exact changes |
| Database migrations | ATOMIC | SQL must be exact |
| Config changes | ATOMIC | No room for interpretation |
| Research/analysis | Open | No file operations |
| Architecture design | Open | Conceptual, no files |

## Naming Convention

Prefix ATOMIC task titles with `ATOMIC:` for clarity:

```
ATOMIC: Create VLM Routes
ATOMIC: Add Health Check Endpoint
ATOMIC: Update Config for New Service
```

## Verification Checklist

Before submitting an ATOMIC instruction:

- [ ] All paths start with `/ganuda/`, `/tmp/`, or `/home/dereadi/`
- [ ] All paths use `**File:**` marker format
- [ ] Code blocks contain complete, runnable code
- [ ] No placeholder text (TODO, FIXME, <placeholder>)
- [ ] No relative paths
- [ ] No path variables (${VAR}, {{var}})

## Related Articles

- JR-RLM-HYBRID-FIX-JAN23-2026: Hybrid fix for path extraction
- Council Vote 28d18d80e447505f: Approved hybrid approach

## For Seven Generations

Clear, explicit instructions reduce errors and ensure reliable execution.
This format has proven 100% successful in production tasks 253-255.

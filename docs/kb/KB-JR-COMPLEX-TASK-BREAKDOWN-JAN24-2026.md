# KB Article: Jr System Complex Task Breakdown

**KB ID:** KB-JR-COMPLEX-001
**Date:** January 24, 2026
**Category:** Architecture / Process
**Severity:** Medium (operational improvement)

---

## Problem Statement

Tasks with multiple actions (create file + modify 12 files + cleanup) cause LLM code generation to fail. The LLM attempts to generate all code in one pass, often producing invalid syntax (unterminated strings, incomplete code blocks).

### Example Failure

**Task:** VETASSIST-SEC-001
- Create database_config.py
- Modify 12 files to use new config
- Update .env files
- Clean up backups

**Result:** LLM generates code with syntax errors because it can't fit all changes into a coherent single output.

---

## Root Cause Analysis

1. **Code task type assumption:** Executor assumes code task = single file output
2. **LLM context overload:** Large instruction files (7KB+) overwhelm the model
3. **Multi-file operations:** No mechanism to generate multiple coordinated file changes
4. **Markdown code blocks:** Instructions with embedded code examples confuse output parsing

---

## Solution Patterns

### Pattern 1: Task Decomposition (Recommended)

Break complex tasks into atomic subtasks:

```
# Instead of:
Task: Create config + modify 12 files

# Use:
Task 1: Create database_config.py (file: /path/to/output.py)
Task 2: Update wizard.py to use database_config
Task 3: Update research.py to use database_config
...
Task 13: Update rag_query.py to use database_config
```

### Pattern 2: Implementation Task Type

Use `implementation` task type for research/analysis that doesn't need code output:
- Research existing patterns
- Create documentation
- Generate reports

Reserve `code` task type for single-file generation only.

### Pattern 3: Chicken-and-Egg TPM Override

When Jr system can't fix itself:
1. TPM applies direct fix (per Rule: chicken-and-egg authority)
2. Document in KB article
3. Mark task as completed with `completed_by: 'TPM_direct_fix'`
4. Create follow-up tasks for Jr to learn from

---

## Executor Enhancement Needed

Future improvement to task executor:

```python
def _should_break_down_task(self, content: str) -> bool:
    """Detect if task is too complex for single-pass generation."""
    indicators = [
        len(content) > 5000,
        content.count('```') > 4,  # Multiple code blocks
        'modify' in content.lower() and 'files' in content.lower(),
        re.search(r'\d+ files?', content),  # "12 files"
    ]
    return sum(indicators) >= 2

def _break_down_task(self, task: dict) -> List[dict]:
    """Break complex task into atomic subtasks."""
    # Use LLM to decompose task
    # Return list of simpler tasks
    pass
```

---

## Thermal Memory Entry

```json
{
    "type": "operational_learning",
    "topic": "jr_task_complexity",
    "learning": "Complex tasks (multi-file, 5KB+ instructions, multiple code blocks) need decomposition. Single-pass code generation fails. Use task breakdown or TPM direct fix.",
    "trigger": "VETASSIST-SEC-001 repeated syntax failures",
    "timestamp": "2026-01-24"
}
```

---

## Related Artifacts

- VETASSIST-SEC-001: Fixed via TPM direct creation
- KB-JR-EXECUTOR-INSTR-001: Instruction file reading fix
- `/ganuda/vetassist/backend/app/core/database_config.py`: Created file

---

**FOR SEVEN GENERATIONS** - Know when to delegate and when to act directly.

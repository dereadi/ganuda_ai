# KB Article: Dual-Model Architecture for Jr Task Execution

**KB ID:** KB-DUAL-MODEL-ARCHITECTURE-JAN28-2026
**Created:** January 28, 2026
**Author:** TPM Claude + Infrastructure Team
**Status:** Implemented & Validated

---

## Problem Statement

Jr task execution was failing with "RLM generated response but created 0 files" errors. The root cause was that the single-model approach (Qwen 32B) wasn't consistently outputting code with the `# filepath:` markers needed by the file parser.

## Solution: Dual-Model Architecture

Implemented a two-phase execution model:

```
┌─────────────────────────────────────────────────────────────┐
│                     Jr Task Queue                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              PM Model (Small, Fast)                         │
│              executive_jr (Ollama) → Qwen fallback          │
│                                                             │
│  Tasks:                                                     │
│  - Parse JR instruction markdown                            │
│  - Decompose into executable steps                          │
│  - Generate structured JSON plan                            │
└─────────────────────────┬───────────────────────────────────┘
                          │ Structured plan
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Coder Model (Large, Accurate)                  │
│              Qwen2.5-coder-32B-AWQ (port 8000)              │
│                                                             │
│  Tasks:                                                     │
│  - Generate code with explicit # filepath: markers          │
│  - Format code blocks properly                              │
└─────────────────────────┬───────────────────────────────────┘
                          │ Code with filepath markers
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              File Parser & Writer                           │
│              (Extracts code blocks, writes to disk)         │
└─────────────────────────────────────────────────────────────┘
```

## Files Modified

| File | Changes |
|------|---------|
| `/ganuda/lib/jr_llm_reasoner.py` | Added `get_pm_plan()`, `get_code_for_step()`, `execute_with_dual_model()` |
| `/ganuda/lib/rlm_executor.py` | Added `execute_with_dual_model()`, lowered min file size from 50 to 20 bytes, fixed `/tmp/` path matching |
| `/ganuda/jr_executor/task_executor.py` | Added dual-model as primary execution path in `_execute_with_rlm()` |

## Key Implementation Details

### 1. PM Model Planning (`jr_llm_reasoner.py`)

```python
def get_pm_plan(instruction_content: str) -> dict:
    """Use PM model to parse instructions and create execution plan."""
    # Tries executive_jr first via Ollama
    # Falls back to Qwen 32B if JSON parsing fails
    # Returns structured plan with steps, files_to_create, etc.
```

### 2. Code Generation with Filepath Markers

```python
def get_code_for_step(step: dict, context: str) -> str:
    """Generate code with explicit filepath marker."""
    # Prompts Qwen to output:
    # ```python
    # # filepath: /path/to/file.py
    # <code here>
    # ```
```

### 3. File Parser Patterns

The parser looks for these patterns:
- `File: \`/path/file.py\`` followed by code block
- `# filepath: /path/file.py` inside code block
- `**CREATE FILE: /path/file.py**` followed by code block

### 4. Minimum File Size

Reduced from 50 bytes to 20 bytes to allow small valid files like:
```python
def hello():
    return "Hi!"
```

## Validation Results

Test task `3032917c` completed successfully:
- File created: `/tmp/final_test.py`
- Content: `def validate(): return "Success!"`
- Status: completed

## Known Issues

### Queue Worker Result Metadata

The queue worker (`jr_queue_worker.py`) only saves limited result fields to the database:
- `summary`
- `steps_executed`
- `completed_at`

It drops:
- `execution_mode`
- `files_created`
- `artifacts`
- `plan`

**Fix:** JR-QUEUE-WORKER-RESULT-FIX-JAN28-2026

## Model Endpoints

| Model | URL | Role |
|-------|-----|------|
| executive_jr | http://localhost:11434/api/generate | PM planning (Ollama) |
| Qwen 32B | http://localhost:8000/v1/chat/completions | Code generation (vLLM) |

## Fallback Behavior

1. If executive_jr doesn't return valid JSON → Falls back to Qwen for planning
2. If dual-model fails → Falls back to standard RLM execution
3. If RLMExecutor unavailable → Uses `_fallback_write_files()` manual parser

---

FOR SEVEN GENERATIONS

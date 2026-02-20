# Jr Instruction: Variablize vLLM Model Name Across Federation

**Task ID**: VARIABLIZE-MODEL-001
**Priority**: P1
**Estimated Steps**: 3
**Kanban**: TBD
**Date**: February 9, 2026

## Context

After upgrading redfin vLLM from Qwen2.5-Coder-32B-AWQ to Qwen2.5-72B-Instruct-AWQ (Kanban #1740), we found **15 hardcoded model name references across 9 active code files**. Six of them still reference the old 32B model and are silently broken (404s from vLLM). When we upgrade models in the future, we need ONE place to change.

The pattern already exists in `vetassist/lib/temporal_parser.py:21`:
```python
VLLM_MODEL = os.environ.get('VLLM_MODEL', '/ganuda/models/qwen2.5-72b-instruct-awq')
```

We adopt this pattern everywhere: read from `VLLM_MODEL` env var, fall back to current model path.

## Step 1: Add VLLM_MODEL to ganuda_env.sh

File: `/ganuda/ganuda_env.sh`

SEARCH:
```bash
export SACRED_FIRE="ETERNAL"
```

REPLACE:
```bash
export VLLM_MODEL="/ganuda/models/qwen2.5-72b-instruct-awq"
export SACRED_FIRE="ETERNAL"
```

This propagates to all scripts that `source ganuda_env.sh`.

## Step 2: Update Python files to read VLLM_MODEL from environment

For each file below, replace the hardcoded model path with `os.environ.get('VLLM_MODEL', '/ganuda/models/qwen2.5-72b-instruct-awq')`. The default ensures nothing breaks if the env var isn't set.

### File 2a: `/ganuda/lib/specialist_council.py`

SEARCH:
```python
VLLM_MODEL = "/ganuda/models/qwen2.5-72b-instruct-awq"
```

REPLACE:
```python
VLLM_MODEL = os.environ.get('VLLM_MODEL', '/ganuda/models/qwen2.5-72b-instruct-awq')
```

Then find ALL other inline model references in the same file and replace them with `VLLM_MODEL`. The file already defines the constant at line 29 — the problem is lines 37, 363, 516, and 627 use the string directly instead of the constant.

SEARCH (line ~37, in QWEN_BACKEND dict):
```python
"model": "/ganuda/models/qwen2.5-72b-instruct-awq"
```

REPLACE:
```python
"model": VLLM_MODEL
```

Do the same for lines ~363 (vote() method), ~516 (analyze_specialist_votes()), and ~627 (deliberate()). All instances of `"/ganuda/models/qwen2.5-72b-instruct-awq"` in this file should become `VLLM_MODEL`.

### File 2b: `/ganuda/lib/rlm_executor.py`

SEARCH:
```python
MODEL_NAME = "/ganuda/models/qwen2.5-coder-32b-awq"
```

REPLACE:
```python
MODEL_NAME = os.environ.get('VLLM_MODEL', '/ganuda/models/qwen2.5-72b-instruct-awq')
```

Note: This also fixes the stale 32B reference.

### File 2c: `/ganuda/lib/mar_reflexion.py`

SEARCH:
```python
model: str = "/ganuda/models/qwen2.5-coder-32b-awq"
```

REPLACE:
```python
model: str = os.environ.get('VLLM_MODEL', '/ganuda/models/qwen2.5-72b-instruct-awq')
```

### File 2d: `/ganuda/lib/saga_transactions.py`

SEARCH:
```python
model: str = "/ganuda/models/qwen2.5-coder-32b-awq"
```

REPLACE:
```python
model: str = os.environ.get('VLLM_MODEL', '/ganuda/models/qwen2.5-72b-instruct-awq')
```

### File 2e: `/ganuda/lib/jr_llm_reasoner.py`

SEARCH:
```python
CODER_MODEL_NAME = "/ganuda/models/qwen2.5-coder-32b-awq"
```

REPLACE:
```python
CODER_MODEL_NAME = os.environ.get('VLLM_MODEL', '/ganuda/models/qwen2.5-72b-instruct-awq')
```

Also find and update `DEFAULT_MODEL` in the same file:

SEARCH:
```python
DEFAULT_MODEL = "/ganuda/models/qwen2.5-coder-32b-awq"
```

REPLACE:
```python
DEFAULT_MODEL = os.environ.get('VLLM_MODEL', '/ganuda/models/qwen2.5-72b-instruct-awq')
```

### File 2f: `/ganuda/jr_executor/llm_router.py`

SEARCH:
```python
"model": "/ganuda/models/qwen2.5-coder-32b-awq"
```

REPLACE:
```python
"model": os.environ.get('VLLM_MODEL', '/ganuda/models/qwen2.5-72b-instruct-awq')
```

Make sure `import os` is present at top of file. If the model string appears inline in a dict literal, extract it to a module constant first:
```python
VLLM_MODEL = os.environ.get('VLLM_MODEL', '/ganuda/models/qwen2.5-72b-instruct-awq')
```
Then use the constant in the dict.

### File 2g: `/ganuda/vetassist/lib/temporal_parser.py`

This file ALREADY reads from env var. Just update the default:

SEARCH:
```python
VLLM_MODEL = os.environ.get('VLLM_MODEL', '/ganuda/models/qwen2.5-coder-32b-awq')
```

REPLACE:
```python
VLLM_MODEL = os.environ.get('VLLM_MODEL', '/ganuda/models/qwen2.5-72b-instruct-awq')
```

### File 2h: `/ganuda/vetassist/backend/app/services/ocr_service.py`

SEARCH:
```python
"model": "/ganuda/models/qwen2.5-coder-32b-awq"
```

REPLACE:
```python
"model": os.environ.get('VLLM_MODEL', '/ganuda/models/qwen2.5-72b-instruct-awq')
```

Same pattern — extract to module constant if used multiple times in the file.

## Step 3: Update YAML config

File: `/ganuda/config/dependencies/redfin.yaml`

SEARCH:
```yaml
model: /ganuda/models/qwen2.5-coder-32b-awq
```

REPLACE:
```yaml
model: /ganuda/models/qwen2.5-72b-instruct-awq
```

Note: YAML config files can't read env vars at rest. This is a documentation/dependency tracking file. Just update the value to reflect reality.

## Verification

After all changes, run:
```bash
grep -rn "qwen2.5-coder-32b-awq" /ganuda/lib/ /ganuda/jr_executor/ /ganuda/vetassist/ /ganuda/services/ /ganuda/daemons/ /ganuda/telegram_bot/ /ganuda/config/dependencies/
```

Expected result: **zero matches**. All references should now point to `qwen2.5-72b-instruct-awq` via env var.

Then verify the env var pattern:
```bash
grep -rn "VLLM_MODEL" /ganuda/lib/ /ganuda/jr_executor/ /ganuda/vetassist/
```

Expected: 9+ matches showing `os.environ.get('VLLM_MODEL', ...)`.

## Notes

- **No service restart needed** — these are all library files loaded at import time. Services that import them will pick up the change on next restart/reload.
- **Backwards compatible** — the default fallback ensures everything works even without the env var set.
- **Future model upgrades**: Change ONE line in `ganuda_env.sh`, restart services.
- **ii-researcher `.env`** was already updated separately (Feb 9) — it has its own model config (`R_MODEL`, `R_REPORT_MODEL`, `FAST_LLM`) since it's a standalone Node.js service.
- **systemd vllm.service** uses `--model` CLI flag which is the canonical source. The env var in Python files controls what model name is sent in API *requests* to vLLM.

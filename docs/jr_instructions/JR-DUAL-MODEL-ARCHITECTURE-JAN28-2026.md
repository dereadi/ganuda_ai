# JR Instruction: Dual-Model Architecture for Jr Execution

**JR ID:** JR-DUAL-MODEL-ARCHITECTURE-JAN28-2026
**Priority:** P1
**Assigned To:** Infrastructure Jr. + Software Engineer Jr.
**Related:** ULTRATHINK-COUNCIL-RESEARCH-INTEGRATION-JAN28-2026

---

## Objective

Wire up the intended dual-model architecture where a small "PM" model handles planning/decomposition and the large model (Qwen 32B) handles code execution. Also document and leverage existing models on sasass2.

---

## Current State

### Redfin (192.168.132.223)

| Port | Model | Role | Status |
|------|-------|------|--------|
| 8000 | Qwen2.5-coder-32B-AWQ | Code execution | ✅ Running |
| 8002 | cherokee-constitutional | Small/specialized | ✅ Running (2048 ctx) |
| 8080 | LLM Gateway | Routing | ✅ Running |
| 11434 | Ollama | Multiple models | ✅ Running |

**Ollama Models on Redfin:**
- `executive_jr` - Could be PM model
- `meta_jr`, `conscience_jr` - Specialized roles
- `qwen2.5-coder:14b` - Mid-size coder
- `llama3.1:8b` - General purpose

### Sasass2 (192.168.132.242)

**Status:** Actively running models (needs inventory)

**Action Required:** Document what's running on sasass2

---

## Intended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     JR Task Queue                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              PM Model (Small, Fast)                         │
│              executive_jr or llama3.1:8b                    │
│                                                             │
│  Tasks:                                                     │
│  - Parse JR instruction markdown                            │
│  - Decompose into executable steps                          │
│  - Generate structured JSON plan                            │
│  - Format output for executor                               │
└─────────────────────────┬───────────────────────────────────┘
                          │ Structured plan
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Coder Model (Large, Accurate)                  │
│              Qwen2.5-coder-32B-AWQ (port 8000)              │
│                                                             │
│  Tasks:                                                     │
│  - Generate actual code from plan steps                     │
│  - Format code with filepath markers                        │
│  - Handle complex multi-file changes                        │
└─────────────────────────┬───────────────────────────────────┘
                          │ Code blocks with filepaths
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Task Executor                                   │
│              (Parses and writes files)                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Steps

### Step 1: Inventory Sasass2 Models

SSH to sasass2 and document running models:

```bash
ssh sasass2
# Check MLX models
ls -la /Users/Shared/ganuda/models/

# Check if MLX server running
ps aux | grep mlx

# Check Ollama
curl http://localhost:11434/api/tags | jq '.models[].name'

# Check any vLLM
ps aux | grep vllm
```

Document findings in `/ganuda/docs/kb/KB-SASASS2-MODEL-INVENTORY-JAN28-2026.md`

### Step 2: Configure PM Model in Jr Reasoner

Edit `/ganuda/lib/jr_llm_reasoner.py`:

```python
# Dual-model configuration
PM_MODEL_URL = "http://localhost:11434/api/generate"  # Ollama executive_jr
PM_MODEL_NAME = "executive_jr"

CODER_MODEL_URL = "http://localhost:8000/v1/chat/completions"  # Qwen 32B
CODER_MODEL_NAME = "qwen2.5-coder-32b-awq"

def get_pm_plan(instruction_content: str) -> dict:
    """Use PM model to parse instructions and create execution plan."""
    prompt = f"""You are a Project Manager. Parse this JR instruction and create a structured execution plan.

INSTRUCTION:
{instruction_content}

OUTPUT FORMAT (JSON):
{{
  "title": "task title",
  "steps": [
    {{
      "step_number": 1,
      "action": "create_file" | "edit_file" | "run_command",
      "target": "/path/to/file.py",
      "description": "what to do",
      "code_needed": true | false
    }}
  ]
}}

Return ONLY valid JSON, no explanation."""

    response = requests.post(
        PM_MODEL_URL,
        json={"model": PM_MODEL_NAME, "prompt": prompt, "stream": False},
        timeout=60
    )
    return response.json()


def get_code_for_step(step: dict, context: str) -> str:
    """Use Coder model to generate code for a plan step."""
    prompt = f"""Generate code for this step. Include filepath marker.

STEP: {step['description']}
TARGET: {step['target']}
CONTEXT: {context}

Format your response as:
```python
# filepath: {step['target']}
<your code here>
```"""

    response = requests.post(
        CODER_MODEL_URL,
        json={
            "model": CODER_MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4000
        },
        timeout=120
    )
    return response.json()['choices'][0]['message']['content']
```

### Step 3: Update RLM Executor for Dual-Model

Edit `/ganuda/lib/rlm_executor.py`:

```python
from jr_llm_reasoner import get_pm_plan, get_code_for_step

def execute_with_dual_model(instruction_content: str) -> dict:
    """Execute task using PM + Coder dual-model approach."""

    # Phase 1: PM creates plan
    plan = get_pm_plan(instruction_content)

    artifacts = []

    # Phase 2: Coder generates code for each step
    for step in plan.get('steps', []):
        if step.get('code_needed'):
            code_response = get_code_for_step(step, instruction_content)
            # Parse and write files from code_response
            step_artifacts = parse_and_write_files(code_response)
            artifacts.extend(step_artifacts)

    return {
        'success': len(artifacts) > 0,
        'plan': plan,
        'artifacts': artifacts
    }
```

### Step 4: Add Sasass2 as Inference Target

If sasass2 has capable models (e.g., MLX Qwen), add as fallback:

```python
INFERENCE_ENDPOINTS = [
    ("redfin", "http://192.168.132.223:8000/v1/chat/completions"),
    ("sasass2", "http://192.168.132.242:8000/v1/chat/completions"),  # If running
]

def get_available_endpoint():
    """Find first healthy inference endpoint."""
    for name, url in INFERENCE_ENDPOINTS:
        try:
            r = requests.get(url.replace('/chat/completions', '/models'), timeout=2)
            if r.status_code == 200:
                return url
        except:
            continue
    return INFERENCE_ENDPOINTS[0][1]  # Default to redfin
```

---

## Testing

### Test PM Model Parsing

```bash
curl -X POST http://localhost:11434/api/generate \
  -d '{
    "model": "executive_jr",
    "prompt": "Parse this and return JSON plan: Create a file /ganuda/test.py with hello world",
    "stream": false
  }'
```

### Test Dual-Model Flow

```python
from jr_llm_reasoner import get_pm_plan, get_code_for_step

plan = get_pm_plan("Create /ganuda/lib/test_dual.py with a function that adds two numbers")
print(f"Plan: {plan}")

for step in plan.get('steps', []):
    if step.get('code_needed'):
        code = get_code_for_step(step, "test context")
        print(f"Code for step {step['step_number']}:\n{code}")
```

---

## Model Recommendations

| Role | Recommended Model | Why |
|------|-------------------|-----|
| PM/Planner | executive_jr or llama3.1:8b | Fast, good at structured output |
| Coder | Qwen2.5-coder-32B | Best at code generation |
| Fallback Coder | qwen2.5-coder:14b | When 32B busy/slow |
| Council Specialist | cherokee-constitutional | Domain-trained |

---

## Files to Modify

| File | Action |
|------|--------|
| `/ganuda/lib/jr_llm_reasoner.py` | Add dual-model functions |
| `/ganuda/lib/rlm_executor.py` | Add dual-model execution path |
| `/ganuda/jr_executor/jr_queue_worker.py` | Use dual-model by default |
| `/ganuda/docs/kb/KB-SASASS2-MODEL-INVENTORY-JAN28-2026.md` | CREATE |

---

FOR SEVEN GENERATIONS

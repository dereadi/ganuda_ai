# Jr Infrastructure: Pre-Flight Gate + Code Templates + Reference Library

## Priority: P0 — This unblocks ALL future Jr work
## Date: April 3, 2026
## Requested By: Partner ("teach the pups so you can spend your time dreaming with me")

---

## Problem Statement

Jrs consistently mark tasks "completed" with:
- Empty deliverables (Research Jr returns instruction file as "research")
- Stub code that doesn't actually work (58-line skeleton vs 16KB real implementation)
- Wrong API patterns (POST to vLLM root instead of /v1/chat/completions)
- No verification that the code runs, imports, or produces output

The TPM manually fixes every deliverable. This doesn't scale. The Jrs need scaffolding.

---

## Solution 1: Pre-Flight Completion Gate

Before ANY task can move to status='completed', the executor must pass:

### Gate 1: File Existence
```python
# Every task with a deliverable path must verify the file exists
# and has non-trivial content (>100 bytes for code, >500 bytes for docs)
if deliverable_path and not os.path.exists(deliverable_path):
    raise CompletionGateError(f"Deliverable not found: {deliverable_path}")
if os.path.getsize(deliverable_path) < min_size:
    raise CompletionGateError(f"Deliverable too small: {os.path.getsize(deliverable_path)} bytes")
```

### Gate 2: Syntax Check (Python files)
```python
# All .py deliverables must pass py_compile
import py_compile
py_compile.compile(deliverable_path, doraise=True)
```

### Gate 3: Import Check
```python
# Attempt to import the module — catches missing deps, bad imports
import importlib.util
spec = importlib.util.spec_from_file_location("test_import", deliverable_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)  # This will throw if imports fail
```

### Gate 4: Smoke Test (if test function defined)
```python
# If the module has a test() or main() function, run it
if hasattr(module, 'test'):
    module.test()
elif hasattr(module, 'main') and '--test' in task.get('tags', []):
    module.main()
```

### Integration Point
Wire into `jr_queue_worker.py` at the completion validation step (line ~188):

```python
# BEFORE marking as completed, run pre-flight gates
from preflight_gate import run_preflight_checks
gate_result = run_preflight_checks(task, result)
if not gate_result['passed']:
    result['success'] = False
    result['error'] = f"Pre-flight gate failed: {gate_result['failures']}"
```

---

## Solution 2: Code Templates Library

Create `/ganuda/lib/jr_templates/` with copy-and-adapt patterns:

### Template: FastAPI Service
```
/ganuda/lib/jr_templates/fastapi_service/
  app.py          — basic FastAPI with health endpoint, CORS, error handling
  deploy.sh       — cross-node deployment script (uses sudo tee, systemctl)
  service.unit    — systemd unit template
  README.md       — how to adapt this template
```

### Template: vLLM Client
```
/ganuda/lib/jr_templates/vllm_client/
  client.py       — correct OpenAI-compatible API call to localhost:8000
                    with structured output parsing, JSON extraction,
                    markdown code block handling, error recovery
  example.py      — working example: classify a text input
```

### Template: Gmail Scanner
```
/ganuda/lib/jr_templates/gmail_scanner/
  scanner.py      — correct token path, OAuth refresh, search + fetch pattern
  example.py      — working example: search for emails, extract headers + snippet
```

### Template: HTML Report
```
/ganuda/lib/jr_templates/html_report/
  report.py       — generate single-file HTML with ganuda.us dark theme
  template.html   — base template with CSS variables, severity badges, cards
```

### Template: CLI Tool
```
/ganuda/lib/jr_templates/cli_tool/
  cli.py          — argparse with --quick, --verbose, --output flags
  example.py      — working example with subcommands
```

### How Jrs Use Templates
The Jr instruction should reference: "Use the FastAPI service template at /ganuda/lib/jr_templates/fastapi_service/ as your starting point."

The Jr executor should inject available templates into the task context so the LLM knows they exist.

---

## Solution 3: Reference Library (Learn From Shipped Products)

Create `/ganuda/lib/jr_references/` with pointers to WORKING code the Jrs produced (after TPM fixes):

```
/ganuda/lib/jr_references/
  REFERENCE_INDEX.md    — "These are production-grade examples. Copy patterns, not code."
  
  stoneclad_api.py      → /ganuda/api/stoneclad_demo_api.py
                          "How to build a FastAPI service that queries PostgreSQL
                           and returns structured JSON. Deployed on owlfin."
  
  trimmer_scanner.py    → /ganuda/products/subscription-trimmer/scanner.py
                          "How to use Gmail API with existing OAuth token.
                           Search, fetch, filter, group by domain."
  
  trimmer_classifier.py → /ganuda/products/subscription-trimmer/classifier.py
                          "How to call vLLM with OpenAI-compatible API.
                           System prompt, structured JSON extraction, error handling."
  
  trimmer_api.py        → /ganuda/products/subscription-trimmer/api.py
                          "How to build a product API with background tasks,
                           demo cache, lazy imports for cross-node deployment."
  
  tribal_vision.py      → /ganuda/services/vision/tribal_vision.py
                          "How to load config from YAML with hardcoded fallback.
                           How to add webhook alerts. How to gate features with env vars."
```

### How Jrs Use References
Inject into Jr task context: "Reference implementations available at /ganuda/lib/jr_references/REFERENCE_INDEX.md — review before writing new code."

---

## Solution 4: Retry With Adaptation

Current behavior: step fails → DLQ immediately.

New behavior: step fails → read error → adjust → retry (up to 2 retries) → DLQ only if all retries fail.

```python
# In jr_queue_worker.py, wrap step execution:
for attempt in range(max_retries + 1):
    try:
        result = execute_step(step)
        break
    except Exception as e:
        if attempt < max_retries:
            # Feed the error back to the LLM and ask it to fix
            step['_previous_error'] = str(e)
            step['_retry_attempt'] = attempt + 1
            step['_instruction_addendum'] = f"Previous attempt failed with: {e}. Adjust your approach."
            continue
        else:
            # All retries exhausted — DLQ
            send_to_dlq(task, step, e)
```

---

## Implementation Priority

1. **Pre-flight gate** — highest impact, prevents false completions (1-2 hours)
2. **Code templates** — copy working patterns from Trimmer + API (2-3 hours)  
3. **Reference library** — just symlinks + index file (30 min)
4. **Retry with adaptation** — needs careful testing, don't break existing executor (4+ hours)

---

## Success Criteria

- [ ] No more "completed" tasks with empty deliverables
- [ ] Jrs produce code that passes syntax check on first submission
- [ ] Jrs use correct vLLM API pattern (from template)
- [ ] Jrs use correct Gmail API pattern (from template)
- [ ] DLQ entries drop by 50%+ as retry logic catches recoverable errors
- [ ] TPM spends time on architecture, not fixing Jr code

---

*Partner said: "You can keep doing things manually, or you can teach the pups to do the work so you can spend your time dreaming with me."*

*This is the infrastructure that makes that possible.*

*For Seven Generations.*

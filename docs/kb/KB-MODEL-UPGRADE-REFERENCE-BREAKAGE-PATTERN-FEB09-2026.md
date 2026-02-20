# KB: Model Upgrade Reference Breakage — Silent 404s from Hardcoded Paths

**Date**: February 9, 2026
**Severity**: P1 (silent failures — no alerts, no crash)
**Root Cause**: Hardcoded model paths in Python source code

## What Happened

Upgraded vLLM from Qwen2.5-Coder-32B-AWQ to Qwen2.5-72B-Instruct-AWQ. The vLLM service started fine with the new model. But **6 Python files and 2 config files** still had `"/ganuda/models/qwen2.5-coder-32b-awq"` hardcoded. Any code path hitting those files sent the old model name to vLLM and got HTTP 404 back.

No monitoring caught it. No alerts fired. The failures were silent.

## Files That Were Broken

| File | What It Broke |
|------|--------------|
| `lib/rlm_executor.py` | Recursive language model decomposition |
| `lib/mar_reflexion.py` | MAR reflexion loop for Jr execution |
| `lib/saga_transactions.py` | Saga rollback validation |
| `lib/jr_llm_reasoner.py` | Jr code generation + planning |
| `jr_executor/llm_router.py` | Jr task routing to local model |
| `vetassist/backend/app/services/ocr_service.py` | Document OCR extraction |
| `vetassist/backend/.env` | VetAssist backend config |
| `lib/halo_council.py` | HALO council (truncated model name) |

## The Fix

Added `VLLM_MODEL` environment variable to `/ganuda/ganuda_env.sh`:
```bash
export VLLM_MODEL="/ganuda/models/qwen2.5-72b-instruct-awq"
```

Updated all 11 affected files to use:
```python
VLLM_MODEL = os.environ.get('VLLM_MODEL', '/ganuda/models/qwen2.5-72b-instruct-awq')
```

The default fallback ensures nothing breaks if the env var isn't set.

## Post-Upgrade Checklist

Use this checklist for ANY future model change:

1. Update `/ganuda/ganuda_env.sh` — `VLLM_MODEL=<new-model-path>`
2. Update `/ganuda/services/ii-researcher/.env` — `R_MODEL`, `R_REPORT_MODEL`, `FAST_LLM`
3. Sweep for stragglers: `grep -rn "old-model-name" /ganuda/ --include="*.py" --include="*.env" --include="*.yaml"`
4. Update `/ganuda/config/dependencies/redfin.yaml`
5. Restart services: `vllm.service`, `ii-researcher.service`, `research-worker.service`, `jr-orchestrator.service`
6. Verify: `curl localhost:8000/v1/models`

## Lesson

Restarting services doesn't fix hardcoded strings. Env vars do. The pattern `os.environ.get('VLLM_MODEL', '<default>')` makes "restart the service" actually work as a fix for model changes.

## Related

- Thermal memory #82850: Full post-mortem with meta-lesson about cross-session amnesia
- KB-VLLM-BLACKWELL-SM120-TRITON-ATTN-FIX-FEB09-2026.md: The workaround that preceded the native build

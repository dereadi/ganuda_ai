# Jr Build Instructions: Fix Gateway Model Detection

**Task ID:** JR-GATEWAY-MODEL-001
**Priority:** P1 (Critical - Gateway broken)
**Date:** 2025-12-26
**Author:** TPM
**Source:** Production issue - gateway 500 errors after Qwen deployment

---

## Problem Statement

The LLM Gateway has hardcoded model names that don't match the currently loaded vLLM model.
- Gateway sends: `nvidia/NVIDIA-Nemotron-Nano-9B-v2`
- vLLM has loaded: `/ganuda/models/qwen2.5-coder-32b`
- Result: 404 backend error

---

## Solution: Dynamic Model Detection

Modify the gateway to query vLLM for the currently loaded model instead of using a hardcoded map.

---

## Implementation

### Step 1: Add Model Detection Function

In `/ganuda/services/llm_gateway/gateway.py`, add after the imports:

```python
# Cache for current vLLM model
_current_vllm_model = None
_model_cache_time = 0

async def get_current_vllm_model() -> str:
    """Get the currently loaded model from vLLM, with caching."""
    global _current_vllm_model, _model_cache_time

    # Cache for 60 seconds
    if _current_vllm_model and (time.time() - _model_cache_time) < 60:
        return _current_vllm_model

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{VLLM_BACKEND}/v1/models", timeout=5.0)
            if resp.status_code == 200:
                models = resp.json()
                if models.get("data"):
                    _current_vllm_model = models["data"][0]["id"]
                    _model_cache_time = time.time()
                    return _current_vllm_model
    except Exception:
        pass

    # Fallback if can't detect
    return "nvidia/NVIDIA-Nemotron-Nano-9B-v2"
```

### Step 2: Update chat_completions Endpoint

Replace the model_map logic (around line 619-625) with:

```python
    # Get the actual model loaded in vLLM
    vllm_model = await get_current_vllm_model()
```

Remove or comment out the old model_map code:
```python
    # OLD CODE - REMOVE:
    # model_map = {
    #     "cherokee-council": "nvidia/NVIDIA-Nemotron-Nano-9B-v2",
    #     ...
    # }
    # vllm_model = model_map.get(request.model, "nvidia/NVIDIA-Nemotron-Nano-9B-v2")
```

### Step 3: Update Any Other Hardcoded Model References

Search for other instances of the hardcoded model name:
```bash
grep -n "NVIDIA-Nemotron" /ganuda/services/llm_gateway/gateway.py
```

Update each occurrence to use `get_current_vllm_model()` or just pass through the model from the request.

---

## Quick Manual Fix

For immediate resolution, you can just replace the hardcoded model name:

```bash
sed -i 's|nvidia/NVIDIA-Nemotron-Nano-9B-v2|/ganuda/models/qwen2.5-coder-32b|g' /ganuda/services/llm_gateway/gateway.py
```

Then restart the gateway:
```bash
pkill -f 'uvicorn gateway'
cd /ganuda/services/llm_gateway && nohup /home/dereadi/cherokee_venv/bin/python -m uvicorn gateway:app --host 0.0.0.0 --port 8080 > /var/log/ganuda/gateway.log 2>&1 &
```

---

## Validation

```bash
# Test chat completion
curl -s http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5" \
  -H "Content-Type: application/json" \
  -d '{"model": "auto", "messages": [{"role": "user", "content": "hello"}]}' | jq .
```

---

*For Seven Generations - Cherokee AI Federation*

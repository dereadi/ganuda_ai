# Jr Instruction: Update Gateway + Council Model References for 72B

**Task ID:** VLLM-72B-002
**Priority:** P1
**Assigned To:** Software Engineer Jr.
**Kanban:** #1740
**Date:** February 9, 2026
**Depends On:** VLLM-72B-001 (model download complete)

## Background

The vLLM model on redfin is being upgraded from Qwen2.5-Coder-32B-AWQ to Qwen2.5-72B-Instruct-AWQ (council vote #8485). The model path is hardcoded in gateway.py and specialist_council.py. All references must be updated before the vLLM service is restarted with the new model.

## Edit 1: Update gateway QWEN_MODEL constant

File: `/ganuda/services/llm_gateway/gateway.py`

<<<<<<< SEARCH
QWEN_MODEL = "/ganuda/models/qwen2.5-coder-32b-awq"
=======
QWEN_MODEL = "/ganuda/models/qwen2.5-72b-instruct-awq"
>>>>>>> REPLACE

## Edit 2: Update gateway model map

File: `/ganuda/services/llm_gateway/gateway.py`

<<<<<<< SEARCH
            "cherokee-council": "/ganuda/models/qwen2.5-coder-32b-awq",
            "nemotron-9b": "/ganuda/models/qwen2.5-coder-32b-awq",
            "gpt-3.5-turbo": "/ganuda/models/qwen2.5-coder-32b-awq",
            "gpt-4": "/ganuda/models/qwen2.5-coder-32b-awq",
=======
            "cherokee-council": "/ganuda/models/qwen2.5-72b-instruct-awq",
            "nemotron-9b": "/ganuda/models/qwen2.5-72b-instruct-awq",
            "gpt-3.5-turbo": "/ganuda/models/qwen2.5-72b-instruct-awq",
            "gpt-4": "/ganuda/models/qwen2.5-72b-instruct-awq",
>>>>>>> REPLACE

## Edit 3: Update gateway default model fallback

File: `/ganuda/services/llm_gateway/gateway.py`

<<<<<<< SEARCH
        backend_model = model_map.get(request.model, "/ganuda/models/qwen2.5-coder-32b-awq")
=======
        backend_model = model_map.get(request.model, "/ganuda/models/qwen2.5-72b-instruct-awq")
>>>>>>> REPLACE

## Edit 4: Update specialist_council VLLM_MODEL constant

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
VLLM_MODEL = "/ganuda/models/qwen2.5-coder-32b-awq"
=======
VLLM_MODEL = "/ganuda/models/qwen2.5-72b-instruct-awq"
>>>>>>> REPLACE

## Edit 5: Update specialist_council default config model

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
    "model": "/ganuda/models/qwen2.5-coder-32b-awq",
=======
    "model": "/ganuda/models/qwen2.5-72b-instruct-awq",
>>>>>>> REPLACE

## Edit 6: Update specialist_council vote request model (first instance)

File: `/ganuda/lib/specialist_council.py`

Search for the first specialist vote request block that references the old model around line 363:

<<<<<<< SEARCH
                    "model": "/ganuda/models/qwen2.5-coder-32b-awq",
=======
                    "model": "/ganuda/models/qwen2.5-72b-instruct-awq",
>>>>>>> REPLACE

## Edit 7: Update specialist_council vote request model (second instance)

File: `/ganuda/lib/specialist_council.py`

Search for the second specialist vote request block around line 516:

<<<<<<< SEARCH
                    "model": "/ganuda/models/qwen2.5-coder-32b-awq",
=======
                    "model": "/ganuda/models/qwen2.5-72b-instruct-awq",
>>>>>>> REPLACE

## Edit 8: Update specialist_council vote request model (third instance)

File: `/ganuda/lib/specialist_council.py`

Search for the third specialist vote request block around line 627:

<<<<<<< SEARCH
                    "model": "/ganuda/models/qwen2.5-coder-32b-awq",
=======
                    "model": "/ganuda/models/qwen2.5-72b-instruct-awq",
>>>>>>> REPLACE

## Do NOT

- Do not change port numbers (stays 8000)
- Do not modify the gateway routing logic
- Do not change the specialist council voting algorithm
- Do not remove the model map aliases (cherokee-council, nemotron-9b, etc.)

## Success Criteria

1. All 11 references to `qwen2.5-coder-32b-awq` replaced with `qwen2.5-72b-instruct-awq`
2. Zero references to old model path remain: `grep -r "qwen2.5-coder-32b-awq" gateway.py specialist_council.py` returns empty
3. Python syntax valid in both files
4. Gateway and council can be restarted without import errors

# JR Instruction: Update Stale DeepSeek Model References + Dead File Cleanup

**Task**: Update DeepSeek model string from Qwen-32B to Llama-70B across all files
**Priority**: 7 (HIGH — runtime correctness)
**Sacred Fire**: No
**Assigned Jr**: Software Engineer Jr.
**Use RLM**: false
**TEG Plan**: false

## Context

bmasass was swapped from DeepSeek-R1-Distill-Qwen-32B-4bit to DeepSeek-R1-Distill-Llama-70B-4bit on Feb 23, 2026. Seven locations in the codebase still reference the old model string. Also clean up one dead backup file.

## Changes

### Step 1: Fix specialist_council.py DEEPSEEK_BACKEND

File: `lib/specialist_council.py`

<<<<<<< SEARCH
    "model": "mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit",
=======
    "model": "mlx-community/DeepSeek-R1-Distill-Llama-70B-4bit",
>>>>>>> REPLACE

### Step 2: Fix specialist_council.py comment

File: `lib/specialist_council.py`

<<<<<<< SEARCH
- MLX: DeepSeek-R1-Distill-Qwen-32B-4bit on M4 Max 128GB (~23 tok/sec)
=======
- MLX: DeepSeek-R1-Distill-Llama-70B-4bit on M4 Max 128GB
>>>>>>> REPLACE

### Step 3: Fix composer.py BACKENDS

File: `lib/duplo/composer.py`

<<<<<<< SEARCH
        "model": "mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit",
=======
        "model": "mlx-community/DeepSeek-R1-Distill-Llama-70B-4bit",
>>>>>>> REPLACE

### Step 4: Fix shadow_council_sync.py

File: `daemons/shadow_council_sync.py`

<<<<<<< SEARCH
SHADOW_MODEL = "mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit"
=======
SHADOW_MODEL = "mlx-community/DeepSeek-R1-Distill-Llama-70B-4bit"
>>>>>>> REPLACE

### Step 5: Fix gateway.py DEEPSEEK_MODEL

File: `services/llm_gateway/gateway.py`

<<<<<<< SEARCH
DEEPSEEK_MODEL = "mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit"
=======
DEEPSEEK_MODEL = "mlx-community/DeepSeek-R1-Distill-Llama-70B-4bit"
>>>>>>> REPLACE

### Step 6: Fix gateway.py model listing

File: `services/llm_gateway/gateway.py`

<<<<<<< SEARCH
            {"id": "deepseek-r1-32b", "object": "model", "created": 1738972800, "owned_by": "deepseek", "description": "DeepSeek-R1-Distill-Qwen-32B-4bit (MLX, bmasass)"},
=======
            {"id": "deepseek-r1-70b", "object": "model", "created": 1738972800, "owned_by": "deepseek", "description": "DeepSeek-R1-Distill-Llama-70B-4bit (MLX, bmasass)"},
>>>>>>> REPLACE

### Step 7: Fix gateway.py fallback model

File: `services/llm_gateway/gateway.py`

<<<<<<< SEARCH
        backend_model = "mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit"
=======
        backend_model = "mlx-community/DeepSeek-R1-Distill-Llama-70B-4bit"
>>>>>>> REPLACE

## Notes
- Model was changed on bmasass Feb 23, 2026 per Chief directive #8263b29e for DNA diversity from Qwen primary.
- The gateway model ID changes from "deepseek-r1-32b" to "deepseek-r1-70b" — any scripts referencing the old ID will need updating but none were found in the codebase.
- After this change lands, gateway service on redfin and any daemon using these backends should be restarted. TPM will handle service restarts.

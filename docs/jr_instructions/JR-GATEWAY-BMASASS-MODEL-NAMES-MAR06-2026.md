# Jr Instruction: Gateway Health Endpoint — Update bmasass Model Names

**Task**: Update gateway health check to reflect Qwen3 + Llama on bmasass instead of DeepSeek-R1
**Priority**: 6
**Story Points**: 1

## Context

bmasass was swapped from DeepSeek-R1 to Qwen3-30B-A3B (port 8800) + Llama-3.3-70B (port 8801) on March 6 2026. The gateway health endpoint still reports the old model name.

## Steps

### Step 1: Find and update the health endpoint model name

File: `/ganuda/sag/routes/config_routes.py`

Search for any reference to `DeepSeek-R1` or `reasoning_model` in the health endpoint response and update to reflect the new models.

```text
<<<<<<< SEARCH
"reasoning_model":"mlx-community/DeepSeek-R1-Distill-Llama-70B-4bit"
=======
"reasoning_model":"Qwen/Qwen3-30B-A3B-MLX-4bit"
>>>>>>> REPLACE
```

Note: The exact string may differ. Search for `DeepSeek` in the SAG routes and update ALL references to reflect the current bmasass configuration: Qwen3-30B-A3B on port 8800, Llama-3.3-70B-Instruct on port 8801.

## Verification

1. After edit, restart sag: the health endpoint should show the updated model name
2. `curl -s http://localhost:8080/health | python3 -m json.tool | grep reasoning`

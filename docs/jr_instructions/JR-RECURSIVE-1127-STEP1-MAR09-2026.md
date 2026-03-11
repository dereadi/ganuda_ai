# [RECURSIVE] Gateway Health Endpoint — Update bmasass Model Names - Step 1

**Parent Task**: #1127
**Auto-decomposed**: 2026-03-09T14:21:47.760639
**Original Step Title**: Find and update the health endpoint model name

---

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

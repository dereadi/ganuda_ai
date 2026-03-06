# [RECURSIVE] Update stale DeepSeek model refs Qwen-32B to Llama-70B (7 locations) - Step 6

**Parent Task**: #1066
**Auto-decomposed**: 2026-03-05T10:34:37.247870
**Original Step Title**: Fix gateway.py model listing

---

### Step 6: Fix gateway.py model listing

File: `services/llm_gateway/gateway.py`

<<<<<<< SEARCH
            {"id": "deepseek-r1-32b", "object": "model", "created": 1738972800, "owned_by": "deepseek", "description": "DeepSeek-R1-Distill-Qwen-32B-4bit (MLX, bmasass)"},
=======
            {"id": "deepseek-r1-70b", "object": "model", "created": 1738972800, "owned_by": "deepseek", "description": "DeepSeek-R1-Distill-Llama-70B-4bit (MLX, bmasass)"},
>>>>>>> REPLACE

# [RECURSIVE] Update stale DeepSeek model refs Qwen-32B to Llama-70B (7 locations) - Step 5

**Parent Task**: #1066
**Auto-decomposed**: 2026-03-05T10:34:37.247439
**Original Step Title**: Fix gateway.py DEEPSEEK_MODEL

---

### Step 5: Fix gateway.py DEEPSEEK_MODEL

File: `services/llm_gateway/gateway.py`

<<<<<<< SEARCH
DEEPSEEK_MODEL = "mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit"
=======
DEEPSEEK_MODEL = "mlx-community/DeepSeek-R1-Distill-Llama-70B-4bit"
>>>>>>> REPLACE

# [RECURSIVE] Update stale DeepSeek model refs Qwen-32B to Llama-70B (7 locations) - Step 7

**Parent Task**: #1066
**Auto-decomposed**: 2026-03-05T10:34:37.248472
**Original Step Title**: Fix gateway.py fallback model

---

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

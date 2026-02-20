# KB: Research Pipeline Restoration After 72B Upgrade

**Date**: February 9, 2026
**Services**: ii-researcher, research-worker
**Node**: redfin (192.168.132.223)

## What Happened

After upgrading vLLM to Qwen2.5-72B-Instruct-AWQ, the research pipeline (`/research` command on @ganudabot) was returning failures. The ii-researcher was sending requests with the old model name and getting 404s from vLLM.

## Root Cause

`/ganuda/services/ii-researcher/.env` had three model references pointing to the old model:
```
R_MODEL=/ganuda/models/qwen2.5-coder-32b-awq
R_REPORT_MODEL=/ganuda/models/qwen2.5-coder-32b-awq
FAST_LLM=/ganuda/models/qwen2.5-coder-32b-awq
```

## Fix

Updated `/ganuda/services/ii-researcher/.env`:
```
R_MODEL=/ganuda/models/qwen2.5-72b-instruct-awq
R_REPORT_MODEL=/ganuda/models/qwen2.5-72b-instruct-awq
FAST_LLM=/ganuda/models/qwen2.5-72b-instruct-awq
```

Then restarted both services:
```bash
sudo systemctl restart ii-researcher.service
sudo systemctl restart research-worker.service
```

## Verification

Two research jobs completed successfully on the 72B:
- Filesystem comparison report (354 seconds)
- LLM memory functions research (348 seconds)
- Results in `/ganuda/research/completed/`

## Research Pipeline Architecture

```
Telegram /research → telegram_chief_v3.py
  → build_research_query(question, persona)
  → dispatcher.queue_research()
  → research_worker.py (polls queue, dispatches to ii-researcher)
  → ii-researcher (port 8090, SSE stream) → vLLM (port 8000)
  → response back to Telegram
```

## Note

The ii-researcher `.env` is separate from `ganuda_env.sh` because ii-researcher is a Node.js service with its own environment. It uses `R_MODEL`/`R_REPORT_MODEL`/`FAST_LLM` variable names, not `VLLM_MODEL`. Both must be updated on model changes.

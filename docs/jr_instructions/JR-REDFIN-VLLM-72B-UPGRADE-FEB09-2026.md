# Jr Instruction: Upgrade Redfin vLLM to Qwen2.5-72B-Instruct-AWQ

**Task ID:** VLLM-72B-001
**Priority:** P1
**Assigned To:** Software Engineer Jr.
**Kanban:** #1740
**Date:** February 9, 2026
**Council Vote:** #8485 (consensus: upgrade to 70B at 4-bit)

## Background

Redfin runs an RTX PRO 6000 Blackwell with 96GB VRAM. Currently serving Qwen2.5-Coder-32B-AWQ (~19GB weights, using 85GB with KV cache). Council vote #8485 consensus: upgrade to a 70B model at 4-bit to leverage the full GPU capacity.

**Target model:** `Qwen/Qwen2.5-72B-Instruct-AWQ`
- 73B parameters, 80 layers, 64 attention heads, 8 KV heads
- 4-bit AWQ quantization, 41.6GB on disk (11 safetensors shards)
- ~41GB VRAM for weights → ~40GB remaining for KV cache at 0.85 utilization
- Compatible with vLLM awq_marlin kernel (auto-detected)
- Supports up to 128K context (with YaRN), we'll use 32K default

**Current stack:**
- vLLM v0.15.1
- PyTorch 2.9.1+cu128, CUDA 12.8
- Service: `vllm.service` (systemd)
- Port: 8000

## Step 1: Download model (run while current model still serves)

This is a bash operation. Run as dereadi on redfin. This will take 15-30 minutes depending on bandwidth. The current vLLM keeps serving during download — zero downtime.

```bash
# Download to /ganuda/models/
HF_HOME=/ganuda/home/dereadi/.cache/huggingface \
  /home/dereadi/cherokee_venv/bin/huggingface-cli download \
  Qwen/Qwen2.5-72B-Instruct-AWQ \
  --local-dir /ganuda/models/qwen2.5-72b-instruct-awq \
  --local-dir-use-symlinks False
```

**Verify download:**
```bash
ls -la /ganuda/models/qwen2.5-72b-instruct-awq/
# Should see 11 model-*.safetensors files totaling ~41.6GB
du -sh /ganuda/models/qwen2.5-72b-instruct-awq/
# Should show ~42GB
```

## Step 2: Update vLLM systemd service

File: `/etc/systemd/system/vllm.service`

**NOTE:** This file requires sudo to edit. The Jr executor cannot do this directly. This edit is documented here for ops to apply.

<<<<<<< SEARCH
ExecStart=/home/dereadi/cherokee_venv/bin/python -m vllm.entrypoints.openai.api_server --model /ganuda/models/qwen2.5-coder-32b-awq --port 8000 --quantization awq_marlin --gpu-memory-utilization 0.85 --max-model-len 32000 --max-num-seqs 512 --trust-remote-code
=======
ExecStart=/home/dereadi/cherokee_venv/bin/python -m vllm.entrypoints.openai.api_server --model /ganuda/models/qwen2.5-72b-instruct-awq --port 8000 --quantization awq_marlin --dtype float16 --gpu-memory-utilization 0.85 --max-model-len 32768 --max-num-seqs 256 --trust-remote-code
>>>>>>> REPLACE

**Changes explained:**
- `--model`: Points to new 72B model directory
- `--dtype float16`: Required — AWQ does NOT support bfloat16 in vLLM
- `--max-model-len 32768`: Standard 32K context (can go higher with YaRN config later)
- `--max-num-seqs 256`: Reduced from 512 — larger model needs more KV cache per sequence

## Step 3: Service restart (manual — requires sudo)

```bash
# Brief outage window — Jrs and gateway will see vLLM unavailable for 30-60 seconds
sudo systemctl daemon-reload
sudo systemctl restart vllm.service

# Watch startup logs (model load takes 30-60 seconds)
sudo journalctl -u vllm.service -f --no-pager
```

**Verify service is healthy:**
```bash
# Wait for "Uvicorn running" in logs, then:
curl -s http://localhost:8000/v1/models | python3 -m json.tool
# Should show: Qwen2.5-72B-Instruct-AWQ

curl -s http://localhost:8000/health
# Should return 200

nvidia-smi
# VRAM usage should be ~70-80GB (model weights + KV cache pool)
```

## Step 4: Update gateway model reference

File: `/ganuda/services/llm_gateway/gateway.py`

The gateway references the model name for routing. After the model changes, the `/v1/models` endpoint will return the new model name. Check if the gateway hardcodes the model name anywhere and update if needed.

```bash
grep -n "qwen2.5-coder-32b" /ganuda/services/llm_gateway/gateway.py
grep -n "model" /ganuda/services/llm_gateway/gateway.py | head -20
```

If the gateway auto-discovers models from the vLLM `/v1/models` endpoint, no change needed. If it hardcodes the model name, update accordingly.

## Step 5: Smoke test through gateway

```bash
# Test direct to vLLM
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-72b-instruct-awq",
    "messages": [{"role": "user", "content": "What is 2+2? Reply in one word."}],
    "max_tokens": 10
  }' | python3 -m json.tool

# Test through gateway
curl -s http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5" \
  -d '{
    "model": "qwen2.5-72b-instruct-awq",
    "messages": [{"role": "user", "content": "Write a Python function that checks if a number is prime."}],
    "max_tokens": 200
  }' | python3 -m json.tool
```

## Step 6: Update CMDB

Record the model change in thermal memory:
```sql
INSERT INTO thermal_memory_archive (
    memory_type, original_content, temperature_score, memory_hash
) VALUES (
    'cmdb_entry',
    'CMDB UPDATE: redfin vLLM upgraded from Qwen2.5-Coder-32B-AWQ to Qwen2.5-72B-Instruct-AWQ. GPU: RTX PRO 6000 Blackwell 96GB. VRAM usage: ~70-80GB (model + KV cache). Port 8000. Service: vllm.service. Date: 2026-02-09. Council vote: #8485.',
    0.9,
    md5('cmdb-redfin-vllm-72b-upgrade-feb09-2026')
);
```

## Rollback Plan

If the 72B model causes issues (OOM, slow inference, quality regression):

```bash
# Revert service file to point back to 32B
sudo sed -i 's|qwen2.5-72b-instruct-awq|qwen2.5-coder-32b-awq|' /etc/systemd/system/vllm.service
sudo sed -i 's|--dtype float16 ||' /etc/systemd/system/vllm.service
sudo sed -i 's|--max-num-seqs 256|--max-num-seqs 512|' /etc/systemd/system/vllm.service
sudo systemctl daemon-reload
sudo systemctl restart vllm.service
```

The 32B model files remain on disk at `/ganuda/models/qwen2.5-coder-32b-awq/` — no data is deleted.

## Do NOT

- Do not delete the existing 32B model files (keep for rollback)
- Do not change the port (stays 8000)
- Do not modify gpu-memory-utilization above 0.90 (risk of OOM)
- Do not enable YaRN/long context without separate testing
- Do not restart vLLM during business hours without warning (Jrs depend on it)

## Success Criteria

1. Model downloaded to `/ganuda/models/qwen2.5-72b-instruct-awq/` (~42GB)
2. vLLM service starts and loads model without OOM
3. `/v1/models` returns `qwen2.5-72b-instruct-awq`
4. `/health` returns 200
5. Chat completions work (both code and general queries)
6. VRAM usage 70-85GB (not hitting 96GB ceiling)
7. Gateway routes traffic to new model
8. Jr executor tasks complete successfully with new model
9. CMDB updated with new model info
10. 32B model files preserved for rollback

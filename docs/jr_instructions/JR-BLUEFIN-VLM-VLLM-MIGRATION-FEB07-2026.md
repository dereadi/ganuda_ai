# Jr Instruction: Migrate VLM Optic Nerve from Flask/Transformers to vLLM

**Task ID:** VLM-VLLM-001
**Priority:** P1
**Date:** February 7, 2026
**Node:** bluefin (192.168.132.222)
**Assigned:** Infrastructure Jr + Software Engineer Jr
**Council Vote:** Pending (architecture change)

## Overview

Migrate the Tribal Vision VLM service on bluefin from the current Flask + HuggingFace transformers wrapper to vLLM. This consolidates our inference stack (redfin already runs vLLM) and improves throughput for concurrent camera frame analysis as we scale to 4+ cameras.

## Current Architecture

```
Camera Frames → optic-nerve.service → vlm_api.py (Flask, port 8090)
                                        ↓
                                    Qwen2-VL-7B-Instruct (HF transformers, lazy-loaded)
                                        ↓
                                    RTX 5070 (12GB VRAM)
                                    + Ollama Mistral 7B (~8GB VRAM, IDLE)
```

**Problems:**
1. Ollama is consuming ~8GB VRAM running Mistral 7B with no active purpose
2. Flask/transformers wrapper has no batching - one frame at a time
3. VLM model lazy-loads on first request, causing cold-start latency
4. Inconsistent API: custom Flask endpoints vs OpenAI-compatible on redfin

## Target Architecture

```
Camera Frames → optic-nerve.service → vLLM (port 8090)
                                        ↓
                                    Qwen2-VL-7B-Instruct (vLLM, always loaded)
                                        ↓
                                    RTX 5070 (12GB VRAM, no Ollama)

LLM Gateway (redfin:8080) → /v1/vlm/* → adapter → vLLM /v1/chat/completions
```

## Phase 1: Stop Ollama and Free VRAM

### Step 1.1: Stop Ollama on bluefin

```bash
# Check what Ollama is doing
ollama ps

# Stop Ollama service
sudo systemctl stop ollama
sudo systemctl disable ollama

# Verify VRAM freed
nvidia-smi
```

**Expected:** ~8GB VRAM freed. Only gnome-shell should remain on GPU.

### Step 1.2: Verify no services depend on Ollama

```bash
# Check if anything calls Ollama's API (port 11434)
grep -r "11434\|ollama" /ganuda/services/ /ganuda/lib/ /ganuda/jr_executor/ 2>/dev/null | grep -v __pycache__ | grep -v .backup
```

If any services depend on Ollama, document them for migration. The LLM Gateway routes to redfin's vLLM, not bluefin's Ollama, so this should be safe.

## Phase 2: Install vLLM on Bluefin

### Step 2.1: Install vLLM in the cherokee_venv

```bash
# Activate the existing venv
source /home/dereadi/cherokee_venv/bin/activate

# Install vLLM (requires CUDA 13.0 support)
pip install vllm --upgrade

# Verify installation
python3 -c "import vllm; print(f'vLLM version: {vllm.__version__}')"

# Verify GPU detection
python3 -c "import torch; print(f'CUDA: {torch.cuda.is_available()}, Device: {torch.cuda.get_device_name(0)}')"
```

### Step 2.2: Verify Qwen2-VL Support

```bash
# Check if vLLM supports Qwen2-VL
python3 -c "from vllm import LLM; print('Qwen2-VL supported')"

# Check available quantized models
python3 -c "
from huggingface_hub import list_models
models = list_models(search='Qwen2-VL-7B', sort='downloads')
for m in list(models)[:10]:
    print(f'{m.id} - {m.downloads}')
"
```

### Step 2.3: Determine Quantization Strategy

The RTX 5070 has 12GB VRAM. Qwen2-VL-7B in FP16 needs ~15GB. Options:

**Option A (Preferred):** Use AWQ quantized model
```bash
# If Qwen/Qwen2-VL-7B-Instruct-AWQ exists:
vllm serve Qwen/Qwen2-VL-7B-Instruct-AWQ --port 8090 --max-model-len 4096
```

**Option B:** Use GPTQ quantized model
```bash
vllm serve Qwen/Qwen2-VL-7B-Instruct-GPTQ-Int4 --port 8090 --max-model-len 4096
```

**Option C:** FP16 with aggressive memory limits
```bash
vllm serve Qwen/Qwen2-VL-7B-Instruct --port 8090 --max-model-len 2048 --gpu-memory-utilization 0.90 --dtype float16
```

**Decision criteria:** Use Option A if AWQ model exists, then B, then C. The goal is to fit in 12GB VRAM with room for KV cache.

## Phase 3: Create vLLM Systemd Service

### Step 3.1: Create new service file

**File:** `/etc/systemd/system/vlm-bluefin.service` (replace existing)

```ini
[Unit]
Description=Cherokee AI Federation - Tribal Vision VLM Service (vLLM)
Documentation=https://docs.vllm.ai
After=network.target nvidia-persistenced.service
Wants=nvidia-persistenced.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/services/vision
Environment="PATH=/home/dereadi/cherokee_venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"
Environment="VLLM_WORKER_MULTIPROC_METHOD=spawn"

# Ensure NVIDIA devices exist before starting
ExecStartPre=/usr/bin/nvidia-smi -pm 1

# Use whichever model/quantization works (see Phase 2)
ExecStart=/home/dereadi/cherokee_venv/bin/python3 -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2-VL-7B-Instruct \
    --port 8090 \
    --host 0.0.0.0 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.85 \
    --dtype float16 \
    --trust-remote-code

Restart=on-failure
RestartSec=15
StandardOutput=append:/ganuda/logs/vlm_vllm.log
StandardError=append:/ganuda/logs/vlm_vllm.log

# Resource limits
MemoryMax=16G
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
```

**Note:** Adjust `--model` path based on quantization choice from Phase 2. If using AWQ, add `--quantization awq`. If model is downloaded locally, use the local path.

### Step 3.2: Deploy and start

```bash
sudo systemctl daemon-reload
sudo systemctl restart vlm-bluefin
sudo systemctl status vlm-bluefin

# Wait for model to load (may take 60-120 seconds)
sleep 60

# Verify vLLM is serving
curl -s http://localhost:8090/health
curl -s http://localhost:8090/v1/models | python3 -m json.tool
```

### Step 3.3: Verify VRAM usage

```bash
nvidia-smi
# Expected: Qwen2-VL-7B using ~6-8GB (quantized) or ~12GB (FP16)
# Ollama should NOT be running
```

## Phase 4: Update LLM Gateway VLM Proxy

The gateway on redfin (192.168.132.223) proxies VLM requests from `/v1/vlm/*` to bluefin:8090. Currently it sends to custom Flask endpoints. We need a thin adapter since vLLM uses `/v1/chat/completions`.

### Step 4.1: Create VLM adapter on bluefin

**File:** `/ganuda/services/vision/vlm_vllm_adapter.py`

This adapter sits between the gateway and vLLM, translating the custom `/v1/vlm/describe` format into vLLM's `/v1/chat/completions` format with multimodal content.

```python
"""
VLM vLLM Adapter - Translates custom VLM API to vLLM OpenAI-compatible format.
Runs alongside vLLM on bluefin, proxying requests.
"""
import base64
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
import torch

logger = logging.getLogger(__name__)
app = FastAPI(title="VLM vLLM Adapter")

VLLM_URL = "http://localhost:8090"

class DescribeRequest(BaseModel):
    image_path: str
    camera_id: str = "unknown"

class AnalyzeRequest(BaseModel):
    image_path: str
    camera_id: str = "unknown"
    focus: str = "anomalies"

class AskRequest(BaseModel):
    image_path: str
    question: str
    camera_id: str = "unknown"

def image_to_base64(image_path: str) -> str:
    """Read image file and convert to base64 data URL."""
    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return f"data:image/jpeg;base64,{data}"

async def call_vllm(prompt: str, image_path: str) -> str:
    """Send multimodal request to vLLM."""
    image_url = image_to_base64(image_path)
    payload = {
        "model": "Qwen/Qwen2-VL-7B-Instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_url}},
                    {"type": "text", "text": prompt}
                ]
            }
        ],
        "max_tokens": 512,
        "temperature": 0.3
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{VLLM_URL}/v1/chat/completions", json=payload, timeout=120.0)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        result = resp.json()
        return result["choices"][0]["message"]["content"]

@app.get("/v1/vlm/health")
async def health():
    """Health check - compatible with existing gateway expectations."""
    gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none"
    mem = torch.cuda.get_device_properties(0).total_mem if torch.cuda.is_available() else 0
    # Check vLLM backend
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{VLLM_URL}/health", timeout=5.0)
            vllm_healthy = resp.status_code == 200
    except Exception:
        vllm_healthy = False

    return {
        "status": "healthy" if vllm_healthy else "degraded",
        "service": "vlm",
        "backend": "vllm",
        "node": "bluefin",
        "model": "Qwen/Qwen2-VL-7B-Instruct",
        "model_loaded": vllm_healthy,
        "cuda_available": torch.cuda.is_available(),
        "gpu": {"name": gpu_name, "memory_total": f"{mem / 1e9:.1f}GB"}
    }

@app.post("/v1/vlm/describe")
async def describe(req: DescribeRequest):
    """Describe a camera frame - security-focused."""
    prompt = """Describe this security camera frame. Focus on:
- People: count, appearance, actions
- Vehicles: type, color, movement
- Objects: packages, bags, items of interest
- Anomalies: anything unusual
Provide a concise security-focused description."""
    description = await call_vllm(prompt, req.image_path)
    return {"camera_id": req.camera_id, "description": description, "backend": "vllm"}

@app.post("/v1/vlm/analyze")
async def analyze(req: AnalyzeRequest):
    """Analyze frame for anomalies."""
    prompt = f"Analyze this security camera frame for {req.focus}. Report any concerns."
    analysis = await call_vllm(prompt, req.image_path)
    return {"camera_id": req.camera_id, "analysis": analysis, "focus": req.focus, "backend": "vllm"}

@app.post("/v1/vlm/ask")
async def ask(req: AskRequest):
    """Answer a question about a camera frame."""
    answer = await call_vllm(req.question, req.image_path)
    return {"camera_id": req.camera_id, "answer": answer, "backend": "vllm"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8091)
```

### Step 4.2: Create adapter systemd service

**File:** `/etc/systemd/system/vlm-adapter.service`

```ini
[Unit]
Description=Cherokee AI VLM Adapter (Flask→vLLM translation)
After=vlm-bluefin.service
Requires=vlm-bluefin.service

[Service]
Type=simple
User=dereadi
Environment="PATH=/home/dereadi/cherokee_venv/bin:/usr/bin"
ExecStart=/home/dereadi/cherokee_venv/bin/python3 /ganuda/services/vision/vlm_vllm_adapter.py
Restart=on-failure
RestartSec=10
StandardOutput=append:/ganuda/logs/vlm_adapter.log
StandardError=append:/ganuda/logs/vlm_adapter.log

[Install]
WantedBy=multi-user.target
```

### Step 4.3: Update gateway VLM_BACKEND

On **redfin**, update `/ganuda/services/llm_gateway/gateway.py`:

Change:
```python
VLM_BACKEND = "http://192.168.132.222:8090"
```

To:
```python
VLM_BACKEND = "http://192.168.132.222:8091"  # VLM adapter (translates to vLLM)
```

Then restart the gateway:
```bash
sudo systemctl restart llm-gateway  # or however the gateway is managed
```

## Phase 5: Update Optic Nerve Pipeline

### Step 5.1: Check optic nerve client code

```bash
grep -n "8090\|vlm_api\|vlm/describe" /ganuda/lib/vlm_optic_nerve.py
```

If the optic nerve calls the VLM directly on port 8090, update it to use port 8091 (the adapter) so the API contract is preserved.

### Step 5.2: Restart optic nerve

```bash
sudo systemctl restart optic-nerve
```

## Phase 6: Verification

### Step 6.1: Service health

```bash
# vLLM core
curl -s http://localhost:8090/health
curl -s http://localhost:8090/v1/models | python3 -m json.tool

# Adapter
curl -s http://localhost:8091/v1/vlm/health | python3 -m json.tool

# Gateway (from redfin)
curl -s http://192.168.132.223:8080/health | python3 -m json.tool
# Verify: vlm=healthy, vlm_model=Qwen/Qwen2-VL-7B-Instruct
```

### Step 6.2: End-to-end VLM test

```bash
# Save a test frame from a camera
curl --digest -u admin:jawaseatlasers2 "http://192.168.132.182/cgi-bin/snapshot.cgi" -o /tmp/test_frame.jpg

# Test via adapter
curl -s -X POST http://localhost:8091/v1/vlm/describe \
    -H "Content-Type: application/json" \
    -d '{"image_path": "/tmp/test_frame.jpg", "camera_id": "traffic"}' | python3 -m json.tool
```

### Step 6.3: GPU state

```bash
nvidia-smi
# Expected: vLLM using GPU, Ollama stopped, reasonable VRAM usage
```

## Rollback Plan

If vLLM doesn't work on the RTX 5070 (Blackwell GB205 is very new):

```bash
# Stop vLLM services
sudo systemctl stop vlm-adapter vlm-bluefin

# Restore original Flask VLM
# The original vlm_api.py is still on disk
sudo systemctl start vlm-bluefin  # will use original ExecStart

# Re-enable Ollama if needed
sudo systemctl enable --now ollama
```

## CMDB Update

After successful migration, update thermal memory:
```
Type: cmdb_entry
Summary: bluefin VLM migrated from Flask/transformers to vLLM. Model: Qwen2-VL-7B-Instruct. Port 8090 (vLLM), Port 8091 (adapter). Ollama disabled.
```

## Security Notes

- No credentials change required - VLM endpoints don't use database auth
- The adapter runs on localhost only (0.0.0.0 for adapter is fine since gateway needs access from redfin)
- Image data stays on the local filesystem - base64 encoding is in-memory only
- Crawdad review: No new external network exposure

---
**FOR SEVEN GENERATIONS** - One eye sees, one mind understands.

# Jr Instruction: Deploy VLM Adapter + Update LLM Gateway for vLLM

**Task ID:** GATEWAY-VLM-002
**Priority:** P0 (gateway health check spamming 404s)
**Date:** February 7, 2026
**Nodes:** bluefin (adapter) + redfin (gateway)
**Assigned:** Software Engineer Jr.
**Depends On:** VLM-VLLM-001 (COMPLETED - vLLM running on bluefin:8090)

## Overview

vLLM is now running on bluefin:8090 with Qwen/Qwen2-VL-7B-Instruct-AWQ. But the LLM Gateway on redfin still calls the old custom Flask endpoints (`/v1/vlm/describe`, `/v1/vlm/health`), which return 404 from vLLM.

We need:
1. A thin FastAPI adapter on bluefin (port 8091) that translates the custom VLM API to vLLM's OpenAI-compatible format
2. Gateway update to point VLM_BACKEND to the adapter

The adapter is needed because the VLM endpoints accept `image_path` (local filesystem path on bluefin). The adapter reads the image, base64 encodes it, and sends it to vLLM's `/v1/chat/completions`.

## Part 1: Deploy VLM Adapter on Bluefin

### Step 1.1: Create adapter file

**File:** `/ganuda/services/vision/vlm_vllm_adapter.py`

```python
"""
VLM vLLM Adapter - Translates custom VLM API to vLLM OpenAI-compatible format.
Runs alongside vLLM on bluefin, proxying requests.

Cherokee AI Federation - For Seven Generations
"""
import base64
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
app = FastAPI(title="VLM vLLM Adapter")

VLLM_URL = "http://localhost:8090"
VLLM_MODEL = "Qwen/Qwen2-VL-7B-Instruct-AWQ"


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
    # Detect format from extension
    ext = image_path.rsplit(".", 1)[-1].lower() if "." in image_path else "jpeg"
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif", "webp": "webp"}.get(ext, "jpeg")
    return f"data:image/{mime};base64,{data}"


async def call_vllm(prompt: str, image_path: str) -> str:
    """Send multimodal request to vLLM."""
    image_url = image_to_base64(image_path)
    payload = {
        "model": VLLM_MODEL,
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
        resp = await client.post(
            f"{VLLM_URL}/v1/chat/completions",
            json=payload,
            timeout=120.0
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        result = resp.json()
        return result["choices"][0]["message"]["content"]


@app.get("/v1/vlm/health")
async def health():
    """Health check - compatible with gateway expectations."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{VLLM_URL}/health", timeout=5.0)
            vllm_healthy = resp.status_code == 200
    except Exception:
        vllm_healthy = False

    # Get model info
    model_info = None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{VLLM_URL}/v1/models", timeout=5.0)
            if resp.status_code == 200:
                models = resp.json().get("data", [])
                if models:
                    model_info = models[0]["id"]
    except Exception:
        pass

    return {
        "status": "healthy" if vllm_healthy else "degraded",
        "service": "vlm",
        "backend": "vllm",
        "node": "bluefin",
        "model": model_info or VLLM_MODEL,
        "model_loaded": vllm_healthy,
        "cuda_available": vllm_healthy,
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

### Step 1.2: Install dependencies (if not already present)

```bash
source /home/dereadi/cherokee_venv/bin/activate
pip install fastapi uvicorn httpx
```

These should already be installed. Verify:
```bash
python3 -c "import fastapi, uvicorn, httpx; print('All deps OK')"
```

### Step 1.3: Create adapter systemd service

**File:** `/ganuda/services/vision/vlm-adapter.service`

```ini
[Unit]
Description=Cherokee AI VLM Adapter (custom API to vLLM translation)
After=vlm-bluefin.service
Wants=vlm-bluefin.service

[Service]
Type=simple
User=dereadi
Group=dereadi
Environment="PATH=/home/dereadi/cherokee_venv/bin:/usr/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/home/dereadi/cherokee_venv/bin/python3 /ganuda/services/vision/vlm_vllm_adapter.py
Restart=on-failure
RestartSec=10
StandardOutput=append:/ganuda/logs/vlm_adapter.log
StandardError=append:/ganuda/logs/vlm_adapter.log

[Install]
WantedBy=multi-user.target
```

### Step 1.4: Deploy (requires sudo on bluefin)

```bash
sudo cp /ganuda/services/vision/vlm-adapter.service /etc/systemd/system/vlm-adapter.service
sudo systemctl daemon-reload
sudo systemctl enable vlm-adapter
sudo systemctl start vlm-adapter

# Verify
sleep 3
curl -s http://localhost:8091/v1/vlm/health | python3 -m json.tool
```

Expected output: `{"status": "healthy", "backend": "vllm", "model": "Qwen/Qwen2-VL-7B-Instruct-AWQ", ...}`

## Part 2: Update LLM Gateway on Redfin

### Step 2.1: Update VLM_BACKEND URL

**File:** `/ganuda/services/llm_gateway/gateway.py` (on redfin)

**Find** (line ~223):
```python
VLM_BACKEND = "http://192.168.132.222:8090"  # Bluefin VLM service (RTX 5070)
```

**Replace with:**
```python
VLM_BACKEND = "http://192.168.132.222:8091"  # Bluefin VLM adapter (translates to vLLM on :8090)
```

This is the ONLY change needed in the gateway. The adapter preserves the exact same API contract (`/v1/vlm/describe`, `/v1/vlm/analyze`, `/v1/vlm/ask`, `/v1/vlm/health`) that the gateway expects.

### Step 2.2: Restart gateway

```bash
# On redfin:
sudo systemctl restart llm-gateway
# Verify:
curl -s http://localhost:8080/health | python3 -m json.tool
# vlm should show "healthy"
```

## Part 3: End-to-End Verification

### Step 3.1: Health chain
```bash
# Adapter health (from bluefin)
curl -s http://192.168.132.222:8091/v1/vlm/health | python3 -m json.tool

# Gateway health (from redfin)
curl -s http://192.168.132.223:8080/health | python3 -m json.tool
# Check: vlm = "healthy", vlm_model = "Qwen/Qwen2-VL-7B-Instruct-AWQ"
```

### Step 3.2: VLM inference test
```bash
# Save a test frame
curl --digest -u admin:jawaseatlasers2 "http://192.168.132.182/cgi-bin/snapshot.cgi" -o /ganuda/data/vision/test_frame.jpg

# Test via adapter directly
curl -s -X POST http://localhost:8091/v1/vlm/describe \
    -H "Content-Type: application/json" \
    -d '{"image_path": "/ganuda/data/vision/test_frame.jpg", "camera_id": "traffic"}' | python3 -m json.tool

# Test via gateway (with API key)
curl -s -X POST http://192.168.132.223:8080/v1/vlm/describe \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5" \
    -d '{"image_path": "/ganuda/data/vision/test_frame.jpg", "camera_id": "traffic"}' | python3 -m json.tool
```

## Rollback

If the adapter has issues:
```bash
# On bluefin:
sudo systemctl stop vlm-adapter
# On redfin, revert VLM_BACKEND to :8090 and restart gateway
# Then restore the old Flask VLM service
```

## Architecture After This Change

```
Camera Frames → optic-nerve → adapter (bluefin:8091) → vLLM (bluefin:8090)
                                  ↑
Gateway (redfin:8080) → /v1/vlm/* → adapter → /v1/chat/completions
                                  ↑
Mac nodes → gateway:8080 → adapter → vLLM
```

---
**FOR SEVEN GENERATIONS** - One eye sees, one mind understands.

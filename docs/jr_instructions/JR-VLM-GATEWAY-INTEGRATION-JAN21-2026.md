# JR Instruction: VLM Gateway Integration

**Task ID**: VLM-GW-001
**Priority**: P2 - Medium
**Created**: January 21, 2026
**TPM**: Claude Opus 4.5

## Objective

Add VLM proxy endpoints to the LLM Gateway (redfin:8080) that forward requests to the VLM service on bluefin:8090.

## Background

- VLM service now operational on bluefin with Qwen2-VL-7B
- RTX 5070 with PyTorch 2.11.0 nightly + CUDA 12.8
- Inference time: ~17 seconds per frame
- Endpoint: http://192.168.132.222:8090

## Phase 1: Add VLM Proxy Endpoints

Add to `/ganuda/services/llm_gateway/gateway.py`:

```python
# VLM Configuration
VLM_BACKEND = "http://192.168.132.222:8090"

# VLM Request Models
class VLMDescribeRequest(BaseModel):
    image_path: str
    camera_id: str = "unknown"

class VLMAnalyzeRequest(BaseModel):
    image_path: str
    camera_id: str = "unknown"

class VLMAskRequest(BaseModel):
    image_path: str
    question: str
    camera_id: str = "unknown"


# VLM Proxy Endpoints
@app.post("/v1/vlm/describe")
async def vlm_describe(request: VLMDescribeRequest, api_key: APIKeyInfo = Depends(validate_api_key)):
    """Proxy to bluefin VLM - describe camera frame"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{VLM_BACKEND}/v1/vlm/describe",
                json={"image_path": request.image_path, "camera_id": request.camera_id},
                timeout=120.0
            )
        return response.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="VLM backend timeout")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"VLM backend error: {str(e)}")


@app.post("/v1/vlm/analyze")
async def vlm_analyze(request: VLMAnalyzeRequest, api_key: APIKeyInfo = Depends(validate_api_key)):
    """Proxy to bluefin VLM - analyze for anomalies"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{VLM_BACKEND}/v1/vlm/analyze",
                json={"image_path": request.image_path, "camera_id": request.camera_id},
                timeout=120.0
            )
        return response.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="VLM backend timeout")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"VLM backend error: {str(e)}")


@app.post("/v1/vlm/ask")
async def vlm_ask(request: VLMAskRequest, api_key: APIKeyInfo = Depends(validate_api_key)):
    """Proxy to bluefin VLM - answer question about frame"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{VLM_BACKEND}/v1/vlm/ask",
                json={
                    "image_path": request.image_path,
                    "question": request.question,
                    "camera_id": request.camera_id
                },
                timeout=120.0
            )
        return response.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="VLM backend timeout")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"VLM backend error: {str(e)}")


@app.get("/v1/vlm/health")
async def vlm_health():
    """Check VLM service health on bluefin"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{VLM_BACKEND}/v1/vlm/health", timeout=5.0)
        return response.json()
    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "node": "bluefin"}
```

## Phase 2: Update Health Check

Modify the `/health` endpoint to include VLM status:

```python
# In health_check function, add:
vlm_status = "unhealthy"
try:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{VLM_BACKEND}/v1/vlm/health", timeout=3.0)
        if resp.status_code == 200:
            vlm_data = resp.json()
            vlm_status = "healthy" if vlm_data.get("cuda_available") else "degraded"
except Exception:
    vlm_status = "unreachable"

# Add to components dict:
"vlm": vlm_status,
"vlm_node": "bluefin"
```

## Phase 3: Update Startup Message

Add VLM endpoints to the startup print:

```python
print("VLM: /v1/vlm/describe, /v1/vlm/analyze, /v1/vlm/ask, /v1/vlm/health")
print(f"VLM Backend: {VLM_BACKEND}")
```

## Phase 4: Restart Gateway

After changes:

```bash
sudo systemctl restart llm-gateway.service
# or
sudo systemctl restart cherokee-gateway.service
```

## Testing

```bash
# Health check
curl http://192.168.132.223:8080/v1/vlm/health

# Describe (needs image on bluefin)
curl -X POST http://192.168.132.223:8080/v1/vlm/describe \
  -H "Content-Type: application/json" \
  -d '{"image_path": "/ganuda/data/vision/frames/test.jpg", "camera_id": "test"}'
```

## CMDB Update

After deployment, add to thermal memory:

```sql
INSERT INTO thermal_memory_archive (
  memory_hash, original_content, memory_type, temperature_score, tags
) VALUES (
  md5('vlm-gateway-integration-' || NOW()::text),
  'CMDB: VLM Gateway Integration Complete

Gateway: redfin:8080
VLM Backend: bluefin:8090
Endpoints:
- POST /v1/vlm/describe
- POST /v1/vlm/analyze
- POST /v1/vlm/ask
- GET /v1/vlm/health

Model: Qwen2-VL-7B-Instruct
GPU: RTX 5070 (12GB)
Inference: ~17s per frame',
  'cmdb_update',
  0.85,
  ARRAY['vlm', 'gateway', 'bluefin', 'integration']
);
```

---
*Cherokee AI Federation - For Seven Generations*

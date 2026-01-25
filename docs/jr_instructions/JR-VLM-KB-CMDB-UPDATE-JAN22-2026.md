# JR Instruction: VLM Integration KB Article & CMDB Update

**Task ID**: VLM-KB-001
**Priority**: P3 - Documentation
**Created**: January 22, 2026
**TPM**: Claude Opus 4.5

## Objective

Document the VLM (Vision Language Model) integration completed on January 21-22, 2026, and update the CMDB with current bluefin service configuration.

## Background

Successfully integrated Tribal Vision VLM service:
- **bluefin** hosts VLM service with Qwen2-VL-7B on RTX 5070
- **redfin** LLM Gateway v1.5.0 proxies VLM requests to bluefin
- Inference time: ~17 seconds per frame
- VRAM usage: 8.8GB / 11.5GB

## Phase 1: Create KB Article

Create file: `/ganuda/docs/kb/KB-VLM-TRIBAL-VISION-INTEGRATION-JAN22-2026.md`

```markdown
# KB Article: Tribal Vision VLM Integration

**KB ID**: KB-VLM-001
**Created**: January 22, 2026
**Category**: AI Services / Computer Vision
**Tags**: vlm, bluefin, rtx5070, qwen2-vl, tribal-vision

## Summary

Deployed Vision Language Model (VLM) service on bluefin for security camera frame analysis, integrated with LLM Gateway on redfin.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   SAG UI        │────▶│  LLM Gateway    │────▶│  VLM Service    │
│   (redfin:4000) │     │  (redfin:8080)  │     │  (bluefin:8090) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │                        │
                              │                        ▼
                              │                 ┌─────────────────┐
                              │                 │  RTX 5070 GPU   │
                              │                 │  12GB VRAM      │
                              │                 └─────────────────┘
                              ▼
                        ┌─────────────────┐
                        │  vLLM Service   │
                        │  (redfin:8000)  │
                        └─────────────────┘
```

## Service Details

| Component | Value |
|-----------|-------|
| **Node** | bluefin (192.168.132.222) |
| **Port** | 8090 |
| **Model** | Qwen/Qwen2-VL-7B-Instruct |
| **GPU** | NVIDIA GeForce RTX 5070 |
| **VRAM** | 11.5GB total, ~8.8GB used |
| **PyTorch** | 2.11.0.dev20260121+cu128 (nightly) |
| **CUDA** | 12.8 (required for Blackwell sm_120) |
| **Inference** | ~17 seconds per frame |

## API Endpoints

### Direct (bluefin:8090)
- `POST /v1/vlm/describe` - Describe camera frame
- `POST /v1/vlm/analyze` - Anomaly detection
- `POST /v1/vlm/ask` - Question answering
- `GET /v1/vlm/health` - Health check
- `POST /v1/vlm/unload` - Unload model (free memory)

### Via Gateway (redfin:8080)
Same endpoints, requires API key authentication:
- `POST /v1/vlm/describe`
- `POST /v1/vlm/analyze`
- `POST /v1/vlm/ask`
- `GET /v1/vlm/health`

## Request/Response Examples

### Describe Frame
```bash
curl -X POST http://192.168.132.223:8080/v1/vlm/describe \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ck-your-api-key" \
  -d '{
    "image_path": "/ganuda/data/vision/frames/camera1_20260122_1030.jpg",
    "camera_id": "front_door"
  }'
```

Response:
```json
{
  "success": true,
  "description": "The frame shows a residential front porch. One person visible, adult male, approaching the door carrying a package. No vehicles in frame. Normal delivery activity.",
  "camera_id": "front_door",
  "frame_path": "/ganuda/data/vision/frames/camera1_20260122_1030.jpg",
  "latency_ms": 17234.56
}
```

### Analyze for Anomalies
```bash
curl -X POST http://192.168.132.223:8080/v1/vlm/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ck-your-api-key" \
  -d '{
    "image_path": "/ganuda/data/vision/frames/test.jpg",
    "camera_id": "backyard"
  }'
```

Response:
```json
{
  "success": true,
  "assessment": "normal",
  "reason": "Empty backyard, no unusual activity",
  "confidence": "high",
  "camera_id": "backyard"
}
```

### Ask Question
```bash
curl -X POST http://192.168.132.223:8080/v1/vlm/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ck-your-api-key" \
  -d '{
    "image_path": "/ganuda/data/vision/frames/test.jpg",
    "question": "How many people are in this frame?",
    "camera_id": "lobby"
  }'
```

## Troubleshooting

### Issue: CUDA OOM (Out of Memory)
**Symptom**: `torch.cuda.OutOfMemoryError`
**Cause**: Another service using GPU (e.g., Ollama)
**Solution**:
```bash
# Check GPU usage
nvidia-smi
# Stop competing service
sudo systemctl stop ollama
# Restart VLM
sudo systemctl restart vlm-bluefin.service
```

### Issue: PyTorch sm_120 Not Supported
**Symptom**: `CUDA error: no kernel image is available for execution on the device`
**Cause**: PyTorch stable doesn't support Blackwell (sm_120) yet
**Solution**:
```bash
pip install --pre torch torchvision --index-url https://download.pytorch.org/whl/nightly/cu128
```

### Issue: NVIDIA Driver Mismatch
**Symptom**: `Failed to initialize NVML: Driver/library version mismatch`
**Solution**:
```bash
# Usually fixed by reboot
sudo reboot
# If persists, rebuild DKMS
sudo dkms autoinstall
```

### Issue: Gateway VLM Endpoints Return 404
**Symptom**: `/v1/vlm/*` endpoints not found
**Cause**: Endpoints defined after `if __name__ == "__main__":` in gateway.py
**Solution**: Move endpoint definitions before the `if __name__` block

## Service Management

```bash
# Start VLM service
sudo systemctl start vlm-bluefin.service

# Stop VLM service
sudo systemctl stop vlm-bluefin.service

# Check status
sudo systemctl status vlm-bluefin.service

# View logs
journalctl -u vlm-bluefin.service -f

# Restart LLM Gateway (after changes)
sudo systemctl restart llm-gateway.service
```

## Files

| File | Node | Purpose |
|------|------|---------|
| `/ganuda/services/vision/vlm_service.py` | bluefin | VLM class with model loading |
| `/ganuda/services/vision/vlm_api.py` | bluefin | Flask API endpoints |
| `/etc/systemd/system/vlm-bluefin.service` | bluefin | Systemd unit file |
| `/ganuda/services/llm_gateway/gateway.py` | redfin | Gateway with VLM proxy |
| `/ganuda/scripts/deploy_vlm_bluefin.sh` | bluefin | Deployment script |

## Known Limitations

1. **Single GPU**: Ollama and VLM cannot run simultaneously on bluefin
2. **Inference Time**: ~17 seconds per frame (not real-time)
3. **Local Images Only**: Image path must be accessible on bluefin filesystem
4. **No Streaming**: VLM responses are not streamed

## Future Enhancements

- [ ] Add image upload endpoint (base64 or multipart)
- [ ] Batch processing for multiple frames
- [ ] Model caching/preloading at startup
- [ ] Prometheus metrics integration
- [ ] Alert integration for anomaly detection

---
*Cherokee AI Federation - For Seven Generations*
```

## Phase 2: Update CMDB (Thermal Memory)

Run on bluefin PostgreSQL:

```sql
-- Update bluefin node with VLM service info
INSERT INTO thermal_memory_archive (
  memory_hash,
  original_content,
  memory_type,
  temperature_score,
  created_at,
  sacred_pattern,
  tags
) VALUES (
  md5('cmdb-bluefin-vlm-jan22-2026'),
  'CMDB UPDATE: Bluefin VLM Service Configuration

Node: bluefin (192.168.132.222)
Updated: January 22, 2026

HARDWARE:
- GPU: NVIDIA GeForce RTX 5070 (Blackwell sm_120)
- VRAM: 11.5GB total
- Status: OPERATIONAL

SERVICES:
1. PostgreSQL (zammad_production) - Port 5432
2. VetAssist API - Port 8001
3. VLM Service (NEW) - Port 8090
   - Model: Qwen/Qwen2-VL-7B-Instruct
   - Framework: PyTorch 2.11.0+cu128 (nightly)
   - CUDA: 12.8 (Blackwell support)
   - VRAM Usage: ~8.8GB
   - Systemd: vlm-bluefin.service

INTEGRATIONS:
- LLM Gateway (redfin:8080) proxies to VLM via /v1/vlm/* endpoints
- Gateway version: 1.5.0

NOTES:
- Ollama service stopped to free GPU memory
- PyTorch nightly required for RTX 5070 (sm_120) support
- Inference time ~17 seconds per frame

Cherokee AI Federation - For Seven Generations',
  'cmdb_update',
  0.9,
  NOW(),
  true,
  ARRAY['cmdb', 'bluefin', 'vlm', 'rtx5070', 'qwen2-vl', 'gpu', 'service-config']
);

-- Update LLM Gateway version in CMDB
INSERT INTO thermal_memory_archive (
  memory_hash,
  original_content,
  memory_type,
  temperature_score,
  created_at,
  sacred_pattern,
  tags
) VALUES (
  md5('cmdb-gateway-v1.5-jan22-2026'),
  'CMDB UPDATE: LLM Gateway v1.5.0

Node: redfin (192.168.132.223)
Updated: January 22, 2026
Version: 1.5.0

NEW FEATURES:
- VLM Proxy Endpoints
  - POST /v1/vlm/describe
  - POST /v1/vlm/analyze
  - POST /v1/vlm/ask
  - GET /v1/vlm/health
- VLM health included in /health response
- Audit logging for VLM requests

BACKEND ROUTING:
- vLLM: http://localhost:8000 (text generation)
- VLM: http://192.168.132.222:8090 (vision, bluefin)

CONFIGURATION:
- VLM_BACKEND = "http://192.168.132.222:8090"
- VLM timeout: 120 seconds

Cherokee AI Federation - For Seven Generations',
  'cmdb_update',
  0.85,
  NOW(),
  true,
  ARRAY['cmdb', 'redfin', 'gateway', 'vlm', 'v1.5.0', 'api']
);
```

## Phase 3: Verify Updates

After creating KB and running SQL:

```bash
# Verify KB article exists
ls -la /ganuda/docs/kb/KB-VLM-TRIBAL-VISION-INTEGRATION-JAN22-2026.md

# Verify CMDB entries
psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT memory_hash, memory_type, temperature_score, created_at, tags
FROM thermal_memory_archive
WHERE 'vlm' = ANY(tags)
ORDER BY created_at DESC
LIMIT 5;
"
```

## Acceptance Criteria

- [ ] KB article created at `/ganuda/docs/kb/KB-VLM-TRIBAL-VISION-INTEGRATION-JAN22-2026.md`
- [ ] CMDB updated with bluefin VLM service configuration
- [ ] CMDB updated with LLM Gateway v1.5.0 changes
- [ ] Both entries have appropriate tags for searchability

## Assignment

This task is suitable for:
- **Documentation Jr** - KB article creation
- **Database Jr** - CMDB SQL updates
- **IT Triad Jr** - Verification

---
*Cherokee AI Federation - For Seven Generations*

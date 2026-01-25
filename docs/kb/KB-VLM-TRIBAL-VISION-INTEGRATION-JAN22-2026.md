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

## Related Documents

- JR Instruction: `/ganuda/docs/jr_instructions/JR-VLM-GATEWAY-INTEGRATION-JAN21-2026.md`
- JR Instruction: `/ganuda/docs/jr_instructions/JR-BLUEFIN-GPU-DRIVER-FIX-JAN21-2026.md`
- Deployment Script: `/ganuda/scripts/deploy_vlm_bluefin.sh`
- Diagnostics: `/ganuda/scripts/bluefin_diagnostics.sh`

---
*Cherokee AI Federation - For Seven Generations*

## Systemd Service Configuration (Added Jan 22, 2026)

### Service Installation
```bash
# Service file location
/etc/systemd/system/vlm-bluefin.service

# Management commands
sudo systemctl start vlm-bluefin.service
sudo systemctl stop vlm-bluefin.service
sudo systemctl restart vlm-bluefin.service
sudo systemctl status vlm-bluefin.service

# View logs
journalctl -u vlm-bluefin.service -f
tail -f /ganuda/logs/vlm_api.log
```

### Key Features
- Auto-starts on boot
- Enables NVIDIA persistence mode before starting
- Restarts automatically on failure (10s delay)
- Memory limit: 16GB
- Runs as dereadi user

### Troubleshooting
If service fails to start:
1. Check NVIDIA driver: `nvidia-smi`
2. Check logs: `journalctl -u vlm-bluefin.service -e`
3. Manual start script: `sudo bash /ganuda/scripts/start_vlm_with_gpu.sh`

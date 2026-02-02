# JR Instruction: Qwen 2.5-VL Model Setup

**JR ID:** JR-AI-004
**Priority:** P1
**Sprint:** VetAssist AI Enhancements Phase 2
**Created:** 2026-01-27
**Author:** TPM via Claude Code
**Council Vote:** b942f2dcad0496e1
**Assigned To:** infrastructure_jr
**Effort:** Medium

## Problem Statement

Current OCR pipeline struggles with handwritten annotations, complex tables, and low-quality scans. Research shows Qwen 2.5-VL can achieve near GPT-4o performance on document understanding tasks.

## Gecko's GPU Capacity Concern

Redfin currently runs Qwen 2.5-Coder-32B-AWQ for text generation. Adding a large VL model risks GPU memory exhaustion.

**Council Decision:** Use Qwen 2.5-VL-7B initially (smaller model, fits alongside text model).

## Required Implementation

### 1. Download Model

```bash
# On redfin (192.168.132.223)
cd /ganuda/models

# Download Qwen 2.5-VL-7B-Instruct-AWQ (quantized for efficiency)
huggingface-cli download Qwen/Qwen2.5-VL-7B-Instruct-AWQ --local-dir ./qwen2.5-vl-7b-awq
```

### 2. vLLM Configuration

CREATE: `/ganuda/vetassist/backend/config/vllm_vlm.yaml`

```yaml
# Qwen 2.5-VL Configuration for VetAssist Document Processing
# Council Approved: 2026-01-27

model:
  path: /ganuda/models/qwen2.5-vl-7b-awq
  type: vision-language

server:
  host: 0.0.0.0
  port: 8002  # Separate from text model on 8000

gpu:
  tensor_parallel_size: 1
  gpu_memory_utilization: 0.3  # Reserve memory for text model
  max_model_len: 32768  # Support multi-page documents

features:
  enable_chunked_prefill: true
  max_num_seqs: 4  # Limit concurrent requests
```

### 3. Systemd Service

CREATE: `/etc/systemd/system/vllm-vlm.service`

```ini
[Unit]
Description=vLLM Vision Language Model Server for VetAssist
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/ganuda
Environment="CUDA_VISIBLE_DEVICES=0"
ExecStart=/usr/bin/python3 -m vllm.entrypoints.openai.api_server \
    --model /ganuda/models/qwen2.5-vl-7b-awq \
    --port 8002 \
    --tensor-parallel-size 1 \
    --gpu-memory-utilization 0.3 \
    --max-model-len 32768 \
    --trust-remote-code
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4. Environment Variables

ADD to `/ganuda/vetassist/backend/.env`:

```bash
# Vision Language Model (local vLLM on redfin)
VLLM_VLM_API_URL=http://localhost:8002/v1
VLLM_VLM_MODEL=/ganuda/models/qwen2.5-vl-7b-awq
VLLM_VLM_TIMEOUT=120
```

### 5. GPU Memory Monitoring

CREATE: `/ganuda/vetassist/backend/scripts/gpu_monitor.sh`

```bash
#!/bin/bash
# GPU memory monitoring for dual-model setup
# Alert if combined usage exceeds 80%

THRESHOLD=80
USAGE=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk -F', ' '{printf "%.0f", ($1/$2)*100}')

if [ "$USAGE" -gt "$THRESHOLD" ]; then
    echo "[WARNING] GPU memory usage at ${USAGE}% - exceeds ${THRESHOLD}% threshold"
    # Could add alerting here (telegram, email, etc.)
fi

echo "GPU Memory: ${USAGE}%"
```

## Verification

```bash
# 1. Verify model downloaded
ls -la /ganuda/models/qwen2.5-vl-7b-awq/

# 2. Start VLM service
sudo systemctl daemon-reload
sudo systemctl enable vllm-vlm
sudo systemctl start vllm-vlm

# 3. Check status
sudo systemctl status vllm-vlm

# 4. Test API endpoint
curl http://localhost:8002/v1/models

# 5. Check GPU memory
nvidia-smi

# 6. Test image processing (basic)
curl -X POST http://localhost:8002/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/ganuda/models/qwen2.5-vl-7b-awq",
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "text", "text": "What is in this image?"},
          {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
        ]
      }
    ],
    "max_tokens": 500
  }'
```

## Rollback Plan

If GPU memory issues occur:

```bash
# Stop VLM service to free memory
sudo systemctl stop vllm-vlm

# Restart text model service if affected
sudo systemctl restart vllm
```

## Dependencies

- CUDA 12.x drivers (already on redfin)
- vLLM >= 0.6.0 with vision support
- huggingface-cli for model download

---

FOR SEVEN GENERATIONS

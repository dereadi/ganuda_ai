# JR Instruction: Bluefin GPU Driver Fix & Service Setup

**Task ID**: BLUEFIN-GPU-001
**Priority**: P1 - High
**Created**: January 21, 2026
**TPM**: Claude Opus 4.5
**Node**: bluefin (192.168.132.222)

## Problem

Bluefin has an RTX 5070 GPU installed but nvidia-smi fails with:
```
Failed to initialize NVML: Driver/library version mismatch
NVML library version: 570.211
```

This prevents GPU usage for VLM and other AI services.

## Objective

1. Fix NVIDIA driver/library mismatch
2. Verify GPU is operational
3. Set up bluefin for VLM service
4. Update CMDB with correct hardware info

## Phase 1: Diagnose Driver Issue

### Task 1.1: Check Current State

SSH to bluefin and run:

```bash
# Check kernel module version
cat /proc/driver/nvidia/version

# Check installed NVIDIA packages
dpkg -l | grep -i nvidia

# Check if nvidia module is loaded
lsmod | grep nvidia

# Check kernel version
uname -r

# Check dkms status
dkms status
```

### Task 1.2: Identify Mismatch

Common causes:
- Kernel updated but nvidia-dkms didn't rebuild
- Partial driver update
- Missing dkms rebuild after kernel update

## Phase 2: Fix Driver

### Option A: Reboot First (Simplest)

```bash
# Try reboot first - often resolves mismatch
sudo reboot
```

After reboot, test:
```bash
nvidia-smi
```

If nvidia-smi works, skip to Phase 3.

### Option B: Rebuild DKMS Module

If reboot doesn't work:

```bash
# Get current kernel
KERNEL=$(uname -r)

# Rebuild nvidia module for current kernel
sudo dkms autoinstall

# Or specifically for nvidia
sudo dkms remove nvidia/570.211 --all 2>/dev/null
sudo dkms install nvidia/570.211 -k $KERNEL

# Reload modules
sudo modprobe -r nvidia_drm nvidia_modeset nvidia_uvm nvidia
sudo modprobe nvidia
```

### Option C: Reinstall Driver (If B Fails)

```bash
# Remove existing nvidia packages
sudo apt purge nvidia-* -y
sudo apt autoremove -y

# Add NVIDIA repository if needed
sudo add-apt-repository ppa:graphics-drivers/ppa -y
sudo apt update

# Install latest driver (570 series for 5070)
sudo apt install nvidia-driver-570 nvidia-dkms-570 -y

# Reboot
sudo reboot
```

## Phase 3: Verify GPU

After fix, verify GPU is working:

```bash
# Basic GPU info
nvidia-smi

# Detailed query
nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv

# Test CUDA
python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}')"
```

Expected output for RTX 5070:
- ~12GB VRAM (or 16GB for 5070 Ti)
- Driver 570.x

## Phase 4: Install VLM Dependencies

Once GPU is working:

```bash
# Create or use existing venv
source /home/dereadi/cherokee_venv/bin/activate || python3 -m venv /home/dereadi/cherokee_venv && source /home/dereadi/cherokee_venv/bin/activate

# Install PyTorch with CUDA
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# Install VLM packages
pip install transformers>=4.37.0
pip install accelerate
pip install qwen-vl-utils
pip install Pillow
pip install flask
pip install prometheus_client

# Verify CUDA in PyTorch
python3 -c "import torch; print(f'PyTorch CUDA: {torch.cuda.is_available()}')"
```

## Phase 5: Deploy VLM Service on Bluefin

### Task 5.1: Copy VLM Files

Copy the VLM infrastructure from redfin:

```bash
# Create directory
mkdir -p /ganuda/services/vision

# Copy files (run from redfin or use scp)
scp redfin:/ganuda/services/vision/security_config.py /ganuda/services/vision/
scp redfin:/ganuda/services/vision/vlm_metrics.py /ganuda/services/vision/
scp redfin:/ganuda/services/vision/vlm_logging.py /ganuda/services/vision/
```

### Task 5.2: Create VLM Service

File: `/ganuda/services/vision/vlm_service.py`

```python
"""
Cherokee AI Federation - Tribal Vision VLM Service
Bluefin Node - RTX 5070
"""

import torch
from PIL import Image
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from transformers import Qwen2VLForConditionalGeneration, AutoProcessor

logger = logging.getLogger(__name__)


class TribalVisionVLM:
    """VLM service for Tribal Vision - runs on bluefin RTX 5070."""

    def __init__(self, model_name: str = "Qwen/Qwen2-VL-7B-Instruct"):
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.processor = None
        logger.info(f"VLM initialized for {self.device}")

    def load_model(self):
        if self.model is not None:
            return

        logger.info(f"Loading {self.model_name}...")
        self.processor = AutoProcessor.from_pretrained(self.model_name)
        self.model = Qwen2VLForConditionalGeneration.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        logger.info("VLM model loaded")

    def describe_frame(self, image_path: str, camera_id: str = "unknown") -> Dict[str, Any]:
        self.load_model()
        try:
            image = Image.open(image_path)
            prompt = "Describe this security camera frame. Focus on people, vehicles, and any anomalies."

            messages = [{"role": "user", "content": [{"type": "image", "image": image}, {"type": "text", "text": prompt}]}]
            text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = self.processor(text=[text], images=[image], return_tensors="pt").to(self.device)

            with torch.no_grad():
                outputs = self.model.generate(**inputs, max_new_tokens=200, do_sample=False)

            description = self.processor.decode(outputs[0], skip_special_tokens=True)
            return {"success": True, "description": description, "camera_id": camera_id}
        except Exception as e:
            return {"success": False, "error": str(e)}


_vlm = None

def get_vlm():
    global _vlm
    if _vlm is None:
        _vlm = TribalVisionVLM()
    return _vlm
```

### Task 5.3: Create API Service

File: `/ganuda/services/vision/vlm_api.py`

```python
"""VLM API - Bluefin"""
from flask import Flask, request, jsonify
from vlm_service import get_vlm

app = Flask(__name__)

@app.route('/v1/vlm/describe', methods=['POST'])
def describe():
    data = request.json
    vlm = get_vlm()
    result = vlm.describe_frame(data.get('image_path'), data.get('camera_id', 'unknown'))
    return jsonify(result)

@app.route('/v1/vlm/health', methods=['GET'])
def health():
    import torch
    return jsonify({
        "status": "healthy",
        "node": "bluefin",
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "cuda": torch.cuda.is_available()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8090)
```

### Task 5.4: Create Systemd Service

File: `/etc/systemd/system/vlm-bluefin.service`

```ini
[Unit]
Description=Cherokee AI VLM Service - Bluefin
After=network.target

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda/services/vision
Environment="PATH=/home/dereadi/cherokee_venv/bin"
ExecStart=/home/dereadi/cherokee_venv/bin/python vlm_api.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable vlm-bluefin.service
sudo systemctl start vlm-bluefin.service
sudo systemctl status vlm-bluefin.service
```

## Phase 6: Update CMDB

After successful setup, update thermal memory:

```sql
-- Run on bluefin PostgreSQL
INSERT INTO thermal_memory_archive (
  memory_hash,
  original_content,
  memory_type,
  temperature_score,
  created_at,
  sacred_pattern,
  tags
) VALUES (
  md5('bluefin-gpu-fixed-' || NOW()::text),
  'CMDB UPDATE: Bluefin GPU Fixed

Node: bluefin (192.168.132.222)
GPU: NVIDIA RTX 5070 (~12GB VRAM)
Driver: 570.x
Status: OPERATIONAL

Services Added:
- VLM Service (port 8090)
- Qwen2-VL-7B-Instruct model

Integration:
- VLM API: http://192.168.132.222:8090/v1/vlm/*
- Health: http://192.168.132.222:8090/v1/vlm/health

For Seven Generations.',
  'cmdb_update',
  0.9,
  NOW(),
  true,
  ARRAY['bluefin', 'gpu', 'vlm', 'cmdb', 'rtx5070']
);
```

## Testing Checklist

- [ ] nvidia-smi shows RTX 5070 with ~12GB VRAM
- [ ] PyTorch detects CUDA
- [ ] VLM service starts without errors
- [ ] Health endpoint returns GPU info
- [ ] Test describe endpoint with sample image
- [ ] CMDB updated with correct specs

## Verification Commands

```bash
# GPU working
nvidia-smi

# VLM service running
curl http://localhost:8090/v1/vlm/health

# Test with image
curl -X POST http://localhost:8090/v1/vlm/describe \
  -H "Content-Type: application/json" \
  -d '{"image_path": "/ganuda/data/vision/frames/test.jpg", "camera_id": "test"}'
```

## Rollback

If issues occur:
```bash
sudo systemctl stop vlm-bluefin.service
sudo systemctl disable vlm-bluefin.service
```

## Notes

- RTX 5070 has ~12GB VRAM - can run Qwen2-VL-7B comfortably
- This offloads VLM from redfin, leaving it for text generation
- Bluefin now serves: PostgreSQL + VetAssist API + VLM

---
*Cherokee AI Federation - For Seven Generations*

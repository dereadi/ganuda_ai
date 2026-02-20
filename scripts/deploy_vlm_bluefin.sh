#!/bin/bash
# VLM Service Deployment for Bluefin
# Cherokee AI Federation - January 2026
# Run with: bash /ganuda/scripts/deploy_vlm_bluefin.sh

set -e

echo "=============================================="
echo "VLM Service Deployment - Bluefin RTX 5070"
echo "=============================================="

# Step 1: Create directories
echo ""
echo "=== Step 1: Creating directories ==="
sudo mkdir -p /ganuda/services/vision
sudo mkdir -p /ganuda/data/vision/frames
sudo mkdir -p /ganuda/logs
sudo chown -R dereadi:dereadi /ganuda/services/vision
sudo chown -R dereadi:dereadi /ganuda/data/vision
sudo chown -R dereadi:dereadi /ganuda/logs

# Step 2: Create/activate venv and install dependencies
echo ""
echo "=== Step 2: Installing Python dependencies ==="
if [ ! -d "/home/dereadi/cherokee_venv" ]; then
    python3 -m venv /home/dereadi/cherokee_venv
fi
source /home/dereadi/cherokee_venv/bin/activate

pip install --upgrade pip
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
pip install transformers>=4.37.0
pip install accelerate
pip install qwen-vl-utils
pip install Pillow
pip install flask
pip install prometheus_client

# Verify CUDA
echo ""
echo "=== Verifying CUDA ==="
python3 -c "import torch; print(f'PyTorch CUDA: {torch.cuda.is_available()}'); print(f'Device: {torch.cuda.get_device_name(0)}')"

# Step 3: Create VLM Service
echo ""
echo "=== Step 3: Creating VLM Service ==="
cat > /ganuda/services/vision/vlm_service.py << 'VLMSERVICE'
"""
Cherokee AI Federation - Tribal Vision VLM Service
Bluefin Node - RTX 5070
"""

import torch
from PIL import Image
from pathlib import Path
from typing import Optional, Dict, Any
import logging
import time

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

    def unload_model(self):
        """Unload model to free memory."""
        if self.model is not None:
            del self.model
            del self.processor
            self.model = None
            self.processor = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("VLM unloaded")

    def describe_frame(self, image_path: str, camera_id: str = "unknown") -> Dict[str, Any]:
        """Generate description of a camera frame."""
        self.load_model()
        start_time = time.time()

        try:
            image = Image.open(image_path)
            prompt = """Describe this security camera frame. Focus on:
- People: count, appearance, actions
- Vehicles: type, color, movement
- Objects: packages, bags, items of interest
- Anomalies: anything unusual

Provide a concise security-focused description."""

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image},
                        {"type": "text", "text": prompt}
                    ]
                }
            ]

            text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = self.processor(text=[text], images=[image], return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model.generate(**inputs, max_new_tokens=200, do_sample=False)

            description = self.processor.decode(outputs[0], skip_special_tokens=True)
            if "assistant" in description.lower():
                description = description.split("assistant")[-1].strip()

            latency_ms = (time.time() - start_time) * 1000

            return {
                "success": True,
                "description": description,
                "camera_id": camera_id,
                "frame_path": image_path,
                "latency_ms": round(latency_ms, 2)
            }

        except Exception as e:
            logger.error(f"Error describing frame: {e}")
            return {
                "success": False,
                "error": str(e),
                "camera_id": camera_id
            }

    def analyze_anomaly(self, image_path: str, camera_id: str = "unknown") -> Dict[str, Any]:
        """Analyze if a frame contains anomalies."""
        self.load_model()

        try:
            image = Image.open(image_path)
            prompt = """Analyze this security camera frame for anomalies.

Respond with ONLY a JSON object:
{
  "assessment": "normal" or "concerning" or "critical",
  "reason": "brief explanation",
  "confidence": "high" or "medium" or "low"
}"""

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image},
                        {"type": "text", "text": prompt}
                    ]
                }
            ]

            text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = self.processor(text=[text], images=[image], return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model.generate(**inputs, max_new_tokens=100, do_sample=False)

            response = self.processor.decode(outputs[0], skip_special_tokens=True)

            import json
            try:
                start = response.find("{")
                end = response.rfind("}") + 1
                if start >= 0 and end > start:
                    result = json.loads(response[start:end])
                else:
                    result = {"assessment": "unknown", "reason": response, "confidence": "low"}
            except json.JSONDecodeError:
                result = {"assessment": "unknown", "reason": response, "confidence": "low"}

            return {"success": True, **result, "camera_id": camera_id}

        except Exception as e:
            return {"success": False, "error": str(e), "assessment": "error"}

    def answer_question(self, image_path: str, question: str, camera_id: str = "unknown") -> Dict[str, Any]:
        """Answer a question about a camera frame."""
        self.load_model()

        try:
            image = Image.open(image_path)
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image},
                        {"type": "text", "text": question}
                    ]
                }
            ]

            text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = self.processor(text=[text], images=[image], return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model.generate(**inputs, max_new_tokens=150, do_sample=False)

            answer = self.processor.decode(outputs[0], skip_special_tokens=True)
            if "assistant" in answer.lower():
                answer = answer.split("assistant")[-1].strip()

            return {"success": True, "answer": answer, "question": question, "camera_id": camera_id}

        except Exception as e:
            return {"success": False, "error": str(e)}


_vlm = None

def get_vlm():
    global _vlm
    if _vlm is None:
        _vlm = TribalVisionVLM()
    return _vlm
VLMSERVICE

# Step 4: Create API Service
echo ""
echo "=== Step 4: Creating VLM API ==="
cat > /ganuda/services/vision/vlm_api.py << 'VLMAPI'
"""
Cherokee AI Federation - VLM API Service
Bluefin Node - Port 8090
"""

from flask import Flask, request, jsonify
import torch
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Lazy import to avoid loading model at startup
_vlm = None

def get_vlm():
    global _vlm
    if _vlm is None:
        from vlm_service import TribalVisionVLM
        _vlm = TribalVisionVLM()
    return _vlm

@app.route('/v1/vlm/describe', methods=['POST'])
def describe():
    """Describe a camera frame."""
    data = request.json
    if not data or 'image_path' not in data:
        return jsonify({"error": "image_path required"}), 400

    vlm = get_vlm()
    result = vlm.describe_frame(data['image_path'], data.get('camera_id', 'unknown'))
    return jsonify(result)

@app.route('/v1/vlm/analyze', methods=['POST'])
def analyze():
    """Analyze frame for anomalies."""
    data = request.json
    if not data or 'image_path' not in data:
        return jsonify({"error": "image_path required"}), 400

    vlm = get_vlm()
    result = vlm.analyze_anomaly(data['image_path'], data.get('camera_id', 'unknown'))
    return jsonify(result)

@app.route('/v1/vlm/ask', methods=['POST'])
def ask():
    """Answer a question about a frame."""
    data = request.json
    if not data or 'image_path' not in data or 'question' not in data:
        return jsonify({"error": "image_path and question required"}), 400

    vlm = get_vlm()
    result = vlm.answer_question(data['image_path'], data['question'], data.get('camera_id', 'unknown'))
    return jsonify(result)

@app.route('/v1/vlm/health', methods=['GET'])
def health():
    """Health check endpoint."""
    gpu_info = None
    if torch.cuda.is_available():
        gpu_info = {
            "name": torch.cuda.get_device_name(0),
            "memory_total": f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB",
            "memory_allocated": f"{torch.cuda.memory_allocated(0) / 1024**3:.1f}GB"
        }

    vlm = get_vlm()
    return jsonify({
        "status": "healthy",
        "node": "bluefin",
        "service": "vlm",
        "model": vlm.model_name,
        "model_loaded": vlm.model is not None,
        "cuda_available": torch.cuda.is_available(),
        "gpu": gpu_info
    })

@app.route('/v1/vlm/unload', methods=['POST'])
def unload():
    """Unload model to free GPU memory."""
    vlm = get_vlm()
    vlm.unload_model()
    return jsonify({"status": "model unloaded"})

if __name__ == '__main__':
    logger.info("Starting VLM API on port 8090")
    app.run(host='0.0.0.0', port=8090)
VLMAPI

# Step 5: Create systemd service
echo ""
echo "=== Step 5: Creating systemd service ==="
sudo tee /etc/systemd/system/vlm-bluefin.service > /dev/null << 'SYSTEMD'
[Unit]
Description=Cherokee AI VLM Service - Bluefin RTX 5070
After=network.target

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda/services/vision
Environment="PATH=/home/dereadi/cherokee_venv/bin:/usr/bin"
ExecStart=/home/dereadi/cherokee_venv/bin/python vlm_api.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
SYSTEMD

sudo systemctl daemon-reload
sudo systemctl enable vlm-bluefin.service

echo ""
echo "=============================================="
echo "Deployment Complete!"
echo "=============================================="
echo ""
echo "To start the service:"
echo "  sudo systemctl start vlm-bluefin.service"
echo ""
echo "To check status:"
echo "  sudo systemctl status vlm-bluefin.service"
echo ""
echo "To test (after starting):"
echo "  curl http://localhost:8090/v1/vlm/health"
echo ""
echo "API Endpoints:"
echo "  POST /v1/vlm/describe  - Describe a frame"
echo "  POST /v1/vlm/analyze   - Anomaly detection"
echo "  POST /v1/vlm/ask       - Question answering"
echo "  GET  /v1/vlm/health    - Health check"
echo ""
echo "Note: First request will download Qwen2-VL-7B (~15GB)"
echo "=============================================="

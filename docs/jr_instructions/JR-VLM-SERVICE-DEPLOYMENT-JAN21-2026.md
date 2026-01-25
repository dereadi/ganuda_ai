# JR Instruction: VLM Service Deployment

**Task ID**: VLM-DEPLOY-001
**Priority**: P1 - High
**Created**: January 21, 2026
**TPM**: Claude Opus 4.5

## Objective

Deploy a Vision Language Model service for Tribal Vision camera integration.
Uses the infrastructure already created (security_config.py, vlm_metrics.py, vlm_logging.py).

## Prerequisites Check

The following files should already exist:
- `/ganuda/services/vision/security_config.py`
- `/ganuda/services/vision/vlm_metrics.py`
- `/ganuda/services/vision/vlm_logging.py`

## Phase 1: Install Dependencies

```bash
# Install VLM packages in cherokee_venv
source /home/dereadi/cherokee_venv/bin/activate

pip install qwen-vl-utils
pip install accelerate
pip install transformers>=4.37.0
```

## Phase 2: Create VLM Service

File: `/ganuda/services/vision/vlm_service.py`

```python
"""
Cherokee AI Federation - Tribal Vision VLM Service
Uses Qwen2-VL for camera frame understanding

Integrates with:
- security_config.py (encryption, access control)
- vlm_metrics.py (performance monitoring)
- vlm_logging.py (audit logging)
"""

import torch
from PIL import Image
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from transformers import Qwen2VLForConditionalGeneration, AutoProcessor

# Import our council-approved infrastructure
from security_config import VLMSecurityConfig
from vlm_metrics import VLM_INFERENCE_DURATION, VLM_INFERENCE_COUNT, VLM_ERROR_COUNT, measure_inference
from vlm_logging import VLMAuditLogger

logger = logging.getLogger(__name__)


class TribalVisionVLM:
    """
    VLM service for Tribal Vision camera system.
    Council-approved implementation addressing all specialist concerns.
    """

    def __init__(self, model_name: str = "Qwen/Qwen2-VL-2B-Instruct"):
        """
        Initialize VLM service.

        Args:
            model_name: HuggingFace model ID (default: Qwen2-VL-2B for efficiency)
        """
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.processor = None
        self.audit_logger = VLMAuditLogger()
        self.security = VLMSecurityConfig()

        logger.info(f"Initializing VLM service with {model_name}")

    def load_model(self):
        """Load the VLM model (lazy loading for memory efficiency)."""
        if self.model is not None:
            return

        logger.info(f"Loading {self.model_name}...")

        self.processor = AutoProcessor.from_pretrained(self.model_name)
        self.model = Qwen2VLForConditionalGeneration.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto" if self.device == "cuda" else None
        )

        if self.device == "cpu":
            self.model = self.model.to(self.device)

        logger.info(f"VLM loaded on {self.device}")

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

    @measure_inference
    def describe_frame(self, image_path: str, camera_id: str = "unknown") -> Dict[str, Any]:
        """
        Generate natural language description of a camera frame.

        Args:
            image_path: Path to the image file
            camera_id: Camera identifier for logging

        Returns:
            Dict with description and metadata
        """
        self.load_model()

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
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=200,
                    do_sample=False
                )

            description = self.processor.decode(outputs[0], skip_special_tokens=True)
            # Extract just the assistant's response
            if "assistant" in description.lower():
                description = description.split("assistant")[-1].strip()

            # Log the inference
            self.audit_logger.log_inference(
                camera_id=camera_id,
                inference_type="describe_frame",
                input_frame=image_path,
                output=description,
                confidence=0.9,  # Qwen2-VL doesn't provide confidence
                latency_ms=0  # Will be filled by decorator
            )

            VLM_INFERENCE_COUNT.labels(camera_id=camera_id, inference_type="describe").inc()

            return {
                "success": True,
                "description": description,
                "camera_id": camera_id,
                "frame_path": image_path
            }

        except Exception as e:
            VLM_ERROR_COUNT.labels(error_type=type(e).__name__).inc()
            self.audit_logger.log_error("describe_frame", str(e), {"image_path": image_path})
            return {
                "success": False,
                "error": str(e),
                "camera_id": camera_id
            }

    @measure_inference
    def analyze_anomaly(self, image_path: str, camera_id: str = "unknown") -> Dict[str, Any]:
        """
        Analyze if a frame contains anomalies.

        Returns assessment: normal, concerning, or critical
        """
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
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=100,
                    do_sample=False
                )

            response = self.processor.decode(outputs[0], skip_special_tokens=True)

            # Try to parse JSON from response
            import json
            try:
                # Find JSON in response
                start = response.find("{")
                end = response.rfind("}") + 1
                if start >= 0 and end > start:
                    result = json.loads(response[start:end])
                else:
                    result = {"assessment": "unknown", "reason": response, "confidence": "low"}
            except json.JSONDecodeError:
                result = {"assessment": "unknown", "reason": response, "confidence": "low"}

            VLM_INFERENCE_COUNT.labels(camera_id=camera_id, inference_type="anomaly").inc()

            return {
                "success": True,
                **result,
                "camera_id": camera_id
            }

        except Exception as e:
            VLM_ERROR_COUNT.labels(error_type=type(e).__name__).inc()
            return {
                "success": False,
                "error": str(e),
                "assessment": "error"
            }

    @measure_inference
    def answer_question(self, image_path: str, question: str, camera_id: str = "unknown") -> Dict[str, Any]:
        """
        Answer a natural language question about a camera frame.
        """
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
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=150,
                    do_sample=False
                )

            answer = self.processor.decode(outputs[0], skip_special_tokens=True)
            if "assistant" in answer.lower():
                answer = answer.split("assistant")[-1].strip()

            VLM_INFERENCE_COUNT.labels(camera_id=camera_id, inference_type="question").inc()

            return {
                "success": True,
                "answer": answer,
                "question": question,
                "camera_id": camera_id
            }

        except Exception as e:
            VLM_ERROR_COUNT.labels(error_type=type(e).__name__).inc()
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance for API usage
_vlm_instance: Optional[TribalVisionVLM] = None

def get_vlm_service() -> TribalVisionVLM:
    """Get or create VLM service singleton."""
    global _vlm_instance
    if _vlm_instance is None:
        _vlm_instance = TribalVisionVLM()
    return _vlm_instance
```

## Phase 3: Add API Endpoints

Add to LLM Gateway or create standalone Flask service.

File: `/ganuda/services/vision/vlm_api.py`

```python
"""
VLM API Endpoints for Tribal Vision
"""

from flask import Flask, request, jsonify
from vlm_service import get_vlm_service

app = Flask(__name__)

@app.route('/v1/vlm/describe', methods=['POST'])
def describe_frame():
    """Describe a camera frame."""
    data = request.json
    image_path = data.get('image_path')
    camera_id = data.get('camera_id', 'unknown')

    if not image_path:
        return jsonify({"error": "image_path required"}), 400

    vlm = get_vlm_service()
    result = vlm.describe_frame(image_path, camera_id)
    return jsonify(result)

@app.route('/v1/vlm/analyze', methods=['POST'])
def analyze_anomaly():
    """Analyze frame for anomalies."""
    data = request.json
    image_path = data.get('image_path')
    camera_id = data.get('camera_id', 'unknown')

    if not image_path:
        return jsonify({"error": "image_path required"}), 400

    vlm = get_vlm_service()
    result = vlm.analyze_anomaly(image_path, camera_id)
    return jsonify(result)

@app.route('/v1/vlm/ask', methods=['POST'])
def ask_question():
    """Answer a question about a frame."""
    data = request.json
    image_path = data.get('image_path')
    question = data.get('question')
    camera_id = data.get('camera_id', 'unknown')

    if not image_path or not question:
        return jsonify({"error": "image_path and question required"}), 400

    vlm = get_vlm_service()
    result = vlm.answer_question(image_path, question, camera_id)
    return jsonify(result)

@app.route('/v1/vlm/health', methods=['GET'])
def health():
    """Health check."""
    vlm = get_vlm_service()
    return jsonify({
        "status": "healthy",
        "model": vlm.model_name,
        "loaded": vlm.model is not None,
        "device": vlm.device
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8090)
```

## Phase 4: Systemd Service

File: `/etc/systemd/system/vlm-service.service`

```ini
[Unit]
Description=Cherokee AI Tribal Vision VLM Service
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

## Testing

```bash
# Test describe
curl -X POST http://localhost:8090/v1/vlm/describe \
  -H "Content-Type: application/json" \
  -d '{"image_path": "/ganuda/data/vision/frames/office_pii_20260121_120000.jpg", "camera_id": "office_pii"}'

# Test anomaly
curl -X POST http://localhost:8090/v1/vlm/analyze \
  -H "Content-Type: application/json" \
  -d '{"image_path": "/ganuda/data/vision/frames/traffic_20260121_120000.jpg", "camera_id": "traffic"}'

# Test question
curl -X POST http://localhost:8090/v1/vlm/ask \
  -H "Content-Type: application/json" \
  -d '{"image_path": "/ganuda/data/vision/frames/office_pii_20260121_120000.jpg", "question": "Is there anyone at the door?", "camera_id": "office_pii"}'
```

## Notes

- Using Qwen2-VL-2B for efficiency (fits in ~8GB VRAM)
- Model loads lazily on first request
- Can run alongside vLLM if GPU memory permits
- Alternative: Run on sasass (M1 Max 64GB) for dedicated VLM

---
*Cherokee AI Federation - For Seven Generations*

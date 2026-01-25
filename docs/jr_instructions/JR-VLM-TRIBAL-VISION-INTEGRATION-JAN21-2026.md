# JR Instruction: Vision Language Model Integration for Tribal Vision

**Task ID**: VLM-VISION-001
**Priority**: P1 - High (Council Enhancement)
**Created**: January 21, 2026
**TPM**: Claude Opus 4.5

## Objective

Integrate Vision Language Models (VLMs) into the Tribal Vision system to give the council specialists (Crawdad, Eagle Eye) the ability to understand, describe, and reason about visual information from cameras.

## Research Foundation

Based on cutting-edge AI research:

1. **VERA (CVPR 2025)** - Explainable Video Anomaly Detection via Verbalized Learning
   - Paper: https://arxiv.org/abs/2410.01914
   - Key innovation: Natural language explanations for detected anomalies

2. **AnomalyCLIP** - Object-Agnostic Prompt Learning for Video Anomaly Detection
   - Paper: https://arxiv.org/abs/2310.02835
   - Key innovation: Zero-shot anomaly detection without specific training

3. **VLAVAD** - Vision-Language Model Assisted Video Anomaly Detection
   - Paper: BMVC 2024 Proceedings
   - Key innovation: VLM-generated descriptions for surveillance

4. **Vision-LLM Surveillance Evaluation**
   - Paper: https://arxiv.org/abs/2510.23190
   - Key innovation: Benchmarks for security camera understanding

## Architecture Design

### Phase 1: Local VLM Integration

Use a local VLM that can run on redfin/sasass GPU nodes:

```
Camera Frame → YOLO Detection → VLM Description → Council Specialist
                   ↓                    ↓
            face/vehicle box     "Adult male, dark jacket,
                                  carrying package, walking
                                  toward front door"
```

### Recommended Models (Ranked by Suitability)

1. **LLaVA-1.6 (34B)** - Best quality, needs 48GB+ VRAM
2. **LLaVA-1.5 (13B)** - Good balance, ~28GB VRAM
3. **LLaVA-1.5 (7B)** - Lighter, ~16GB VRAM
4. **MiniCPM-V** - Very efficient, runs on 8GB
5. **Qwen-VL-Chat** - Good for scene understanding

### Phase 2: Implementation Plan

#### 2.1 Create VLM Service

File: `/ganuda/services/vision/vlm_service.py`

```python
"""
Vision Language Model Service for Tribal Vision
Cherokee AI Federation - Council Visual Understanding
"""

import torch
from PIL import Image
from transformers import AutoProcessor, LlavaForConditionalGeneration
import logging

logger = logging.getLogger(__name__)

class TribalVisionVLM:
    """VLM service for camera frame understanding."""

    def __init__(self, model_name: str = "llava-hf/llava-1.5-7b-hf"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.processor = AutoProcessor.from_pretrained(model_name)
        self.model = LlavaForConditionalGeneration.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        logger.info(f"VLM loaded on {self.device}")

    def describe_frame(self, image_path: str, context: str = "") -> str:
        """Generate natural language description of a camera frame."""
        image = Image.open(image_path)

        prompt = f"""<image>
You are a security camera analyst for the Cherokee AI Federation.
Describe what you see in this camera frame. Focus on:
- People: count, appearance, actions, direction of movement
- Vehicles: type, color, license plate if visible
- Objects: packages, bags, tools
- Anomalies: anything unusual or potentially concerning

{f"Additional context: {context}" if context else ""}

Provide a concise but complete description:"""

        inputs = self.processor(text=prompt, images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=200,
            do_sample=False
        )

        description = self.processor.decode(outputs[0], skip_special_tokens=True)
        return description.split("description:")[-1].strip()

    def analyze_anomaly(self, image_path: str, detection_type: str) -> dict:
        """Analyze a detection and determine if it's anomalous."""
        image = Image.open(image_path)

        prompt = f"""<image>
You are analyzing a {detection_type} detection from a security camera.
Evaluate this detection:
1. Is this normal or potentially concerning? Why?
2. What action, if any, should be taken?
3. Confidence level (high/medium/low)?

Respond in JSON format:
{{"assessment": "normal|concerning|critical", "reason": "...", "action": "...", "confidence": "..."}}"""

        inputs = self.processor(text=prompt, images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        outputs = self.model.generate(**inputs, max_new_tokens=150)
        response = self.processor.decode(outputs[0], skip_special_tokens=True)

        # Parse JSON from response
        import json
        try:
            json_str = response.split("{")[-1].split("}")[0]
            return json.loads("{" + json_str + "}")
        except:
            return {"assessment": "unknown", "reason": response, "action": "review", "confidence": "low"}

    def answer_question(self, image_path: str, question: str) -> str:
        """Answer a natural language question about a camera frame."""
        image = Image.open(image_path)

        prompt = f"<image>\n{question}"

        inputs = self.processor(text=prompt, images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        outputs = self.model.generate(**inputs, max_new_tokens=100)
        return self.processor.decode(outputs[0], skip_special_tokens=True)
```

#### 2.2 Integrate with Existing Vision Pipeline

Modify `/ganuda/services/vision/tribal_vision_main.py` to call VLM after detections:

```python
from vlm_service import TribalVisionVLM

class EnhancedVisionProcessor:
    def __init__(self):
        self.vlm = TribalVisionVLM()
        self.detector = YOLODetector()  # existing

    def process_frame(self, frame_path: str, camera_id: str) -> dict:
        # Existing detection
        detections = self.detector.detect(frame_path)

        # VLM enhancement for significant detections
        if detections.get('faces') or detections.get('vehicles'):
            description = self.vlm.describe_frame(
                frame_path,
                context=f"Camera: {camera_id}, Detections: {detections}"
            )

            # Anomaly analysis
            for detection in detections.get('faces', []):
                analysis = self.vlm.analyze_anomaly(
                    detection['crop_path'],
                    'face'
                )
                detection['vlm_analysis'] = analysis

            return {
                'detections': detections,
                'description': description,
                'timestamp': datetime.now().isoformat()
            }

        return {'detections': detections}
```

#### 2.3 Council Specialist Integration

The VLM descriptions feed into council specialists:

- **Crawdad** (Face Detection Specialist): Receives VLM analysis of face detections
- **Eagle Eye** (Vehicle Specialist): Receives VLM descriptions of vehicles
- **New Specialist: "Sharp Eye"**: Could be a VLM-focused specialist for scene understanding

### Phase 3: API Endpoints

Add to SAG interface:

```python
@app.route('/api/cameras/<camera_id>/describe', methods=['POST'])
def api_camera_describe(camera_id):
    """Get VLM description of latest frame."""
    vlm = get_vlm_service()
    frame_path = get_latest_frame(camera_id)
    description = vlm.describe_frame(frame_path)
    return jsonify({'description': description})

@app.route('/api/cameras/<camera_id>/ask', methods=['POST'])
def api_camera_ask(camera_id):
    """Ask a question about camera view."""
    question = request.json.get('question')
    vlm = get_vlm_service()
    frame_path = get_latest_frame(camera_id)
    answer = vlm.answer_question(frame_path, question)
    return jsonify({'answer': answer})
```

### Phase 4: Frontend Integration

Add to camera view:

```html
<div class="vlm-controls">
    <button id="btn-describe" onclick="describeFrame()">Describe Scene</button>
    <input type="text" id="vlm-question" placeholder="Ask about this view...">
    <button id="btn-ask" onclick="askQuestion()">Ask</button>
    <div id="vlm-response" class="vlm-response-box"></div>
</div>
```

## Hardware Requirements

| Model | VRAM Required | Inference Speed | Quality |
|-------|---------------|-----------------|---------|
| LLaVA-7B | 16GB | ~2s/frame | Good |
| LLaVA-13B | 28GB | ~4s/frame | Better |
| MiniCPM-V | 8GB | ~1s/frame | Acceptable |

**Recommended**: Run on redfin (RTX 4090 24GB) or sasass (M4 Max 64GB unified)

## Dependencies

```bash
pip install transformers accelerate pillow torch
pip install llava  # For LLaVA specific features
```

## Testing Checklist

1. [ ] Install VLM model on GPU node
2. [ ] Test frame description accuracy
3. [ ] Test anomaly detection on known scenarios
4. [ ] Measure inference latency
5. [ ] Integrate with council specialist prompts
6. [ ] Test question-answering capability
7. [ ] Verify memory usage under load

## Success Metrics

- VLM can accurately describe camera scenes
- Anomaly detection catches 90%+ of concerning events
- Natural language questions answered correctly
- Latency < 5 seconds per frame analysis
- Council specialists make better decisions with VLM context

## Notes

- Start with MiniCPM-V for initial testing (lower resource usage)
- Consider batch processing for historical analysis
- VLM descriptions should be cached to reduce GPU load
- Privacy consideration: VLM should not store face descriptions permanently

---
*Cherokee AI Federation - For Seven Generations*
*"Teaching the Council to See"*

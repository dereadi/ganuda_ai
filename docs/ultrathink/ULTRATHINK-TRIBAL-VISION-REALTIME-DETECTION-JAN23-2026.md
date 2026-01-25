# ULTRATHINK: Tribal Vision Real-Time Detection Architecture

**Date:** January 23, 2026
**Author:** TPM with Council Deliberation
**Status:** Council Approved (84.5% confidence)
**Council Vote:** Option D - Hybrid (Frigate + YOLO-World)

## Executive Summary

Implement real-time AI object detection for the SAG Cameras page using a **hybrid architecture**: Frigate NVR for motion-triggered detection and camera management, combined with YOLO-World for zero-shot open-vocabulary identification. This enables detecting objects by text prompt (e.g., "FedEx truck", "orange cat") without retraining.

## Research Findings

### GitHub Landscape Analysis

| Project | Stars | Key Feature | Fit for Us |
|---------|-------|-------------|------------|
| **Frigate NVR** | 29.7k | NVR with MQTT, motion-triggered detection | **Excellent** - MQTT already running |
| **YOLO-World** | ~15k | Zero-shot text-prompt detection | **Excellent** - No retraining needed |
| **YOLO26** | New | Edge-optimized, fastest inference | Good - bleeding edge |
| **RF-DETR** | New | Outperforms YOLO26 | Good - Roboflow ecosystem |
| **Ultralytics YOLO** | 52.3k | Comprehensive toolkit | Good - mature |

### Why Hybrid (Option D)?

**Frigate Strengths:**
- Motion-triggered detection reduces GPU load (only process when needed)
- MQTT integration (we have EMQX running on bluefin)
- RTSP re-streaming reduces camera connection overhead
- WebRTC for low-latency viewing
- Recording with retention based on detected objects
- Home Assistant compatible (future integration path)

**YOLO-World Strengths:**
- Zero-shot detection - describe what to find in natural language
- No retraining for new object types
- Can detect "2021 Chevy Silverado", "FedEx delivery truck", "orange tabby cat"
- Combines with existing Qwen2-VL for rich descriptions

**Combined Benefits:**
```
Camera Stream → Frigate (motion detect) → YOLO-World (identify) → Qwen2-VL (describe)
                    ↓                           ↓                       ↓
               MQTT events              Bounding boxes            Natural language
```

## Architecture Design

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SAG UI (redfin:4000)                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                         Cameras Page                                   │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │ │
│  │  │   Traffic    │  │    Office    │  │    Ring      │  Live Feeds    │ │
│  │  │  [WebRTC]    │  │  [WebRTC]    │  │ [On-Demand]  │  via Frigate   │ │
│  │  │   🎯 Car     │  │   🎯 Person  │  │   🎯 Box     │                │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                │ │
│  │                                                                        │ │
│  │  Detection Timeline (MQTT events)                                     │ │
│  │  ┌────────────────────────────────────────────────────────────────┐  │ │
│  │  │ 12:45 🚗 "White Chevrolet Silverado 2500" | Traffic | 98%      │  │ │
│  │  │ 12:31 📦 "FedEx delivery truck" | Traffic | 95%                │  │ │
│  │  │ 12:18 🐱 "Orange tabby cat" | Traffic | 89%                    │  │ │
│  │  └────────────────────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │ MQTT (EMQX)   │               │
                    │ bluefin:1883  │               │
                    └───────────────┼───────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Frigate NVR (bluefin)                               │
│                                                                              │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │ Traffic Camera  │    │  Office Camera  │    │  Ring Doorbell  │        │
│  │ RTSP :554       │    │  RTSP :554      │    │  RTSP :8554     │        │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘        │
│           │                      │                      │                  │
│           └──────────────────────┼──────────────────────┘                  │
│                                  │                                          │
│                    ┌─────────────▼─────────────┐                           │
│                    │     Motion Detection      │                           │
│                    │     (Low overhead)        │                           │
│                    └─────────────┬─────────────┘                           │
│                                  │ Motion region                           │
│                    ┌─────────────▼─────────────┐                           │
│                    │   YOLO-World Detection    │  ◄── Text prompts:       │
│                    │   (Zero-shot, RTX 5070)   │      "delivery truck"    │
│                    │                           │      "person"            │
│                    └─────────────┬─────────────┘      "cat, dog, bird"    │
│                                  │ Detections                              │
│                    ┌─────────────▼─────────────┐                           │
│                    │      Qwen2-VL (VLM)       │                           │
│                    │   Rich description        │                           │
│                    └─────────────┬─────────────┘                           │
│                                  │                                          │
│                    ┌─────────────▼─────────────┐                           │
│                    │      MQTT Publish         │                           │
│                    │  frigate/events           │                           │
│                    │  frigate/+/snapshot       │                           │
│                    └───────────────────────────┘                           │
│                                                                              │
│  Outputs:                                                                   │
│  • WebRTC streams for low-latency viewing                                  │
│  • MQTT events for SAG UI timeline                                         │
│  • Annotated snapshots with bounding boxes                                 │
│  • 24/7 recording with object-based retention                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Implementation Phases

### Phase 1: Frigate Deployment (P1)

Deploy Frigate NVR on bluefin:

```yaml
# /ganuda/services/frigate/config.yml
mqtt:
  host: localhost
  port: 1883

cameras:
  traffic:
    ffmpeg:
      inputs:
        - path: rtsp://admin:jawaseatlasers2@192.168.132.182:554/cam/realmonitor?channel=1&subtype=1
          roles:
            - detect
            - record
    detect:
      width: 1920
      height: 1080
      fps: 5
    objects:
      track:
        - person
        - car
        - truck
        - cat
        - dog
        - bird

  office:
    ffmpeg:
      inputs:
        - path: rtsp://admin:jawaseatlasers2@192.168.132.181:554/cam/realmonitor?channel=1&subtype=0
          roles:
            - detect
    detect:
      width: 1920
      height: 1080
      fps: 5

  ring_doorbell:
    ffmpeg:
      inputs:
        - path: rtsp://ring:tribal_vision_2026@localhost:8554/d436398fc2b8_live
          roles:
            - detect
    detect:
      enabled: false  # On-demand only
```

**Container:**
```bash
podman run -d \
  --name frigate \
  --network host \
  --shm-size=256m \
  -v /ganuda/services/frigate/config.yml:/config/config.yml \
  -v /ganuda/data/frigate:/media/frigate \
  -e FRIGATE_RTSP_PASSWORD="jawaseatlasers2" \
  ghcr.io/blakeblackshear/frigate:stable
```

### Phase 2: YOLO-World Integration (P1)

Replace/augment Frigate's default detector with YOLO-World:

```python
# /ganuda/services/vision/yolo_world_detector.py
from ultralytics import YOLOWorld

class TribalYOLOWorld:
    def __init__(self):
        self.model = YOLOWorld('yolov8l-world.pt')

        # Cherokee tribal prompts
        self.prompts = [
            "person", "car", "truck", "motorcycle", "bicycle",
            "delivery truck", "FedEx truck", "UPS truck", "Amazon van", "USPS truck",
            "cat", "dog", "bird", "squirrel", "deer", "rabbit",
            "package", "box", "suitcase",
            "Chevrolet Silverado", "pickup truck",
        ]
        self.model.set_classes(self.prompts)

    def detect(self, image_path):
        results = self.model(image_path)
        detections = []
        for r in results:
            for box in r.boxes:
                detections.append({
                    "class": self.prompts[int(box.cls)],
                    "confidence": float(box.conf),
                    "bbox": box.xyxy[0].tolist()
                })
        return detections

    def add_prompt(self, prompt):
        """Add custom detection target on-the-fly"""
        if prompt not in self.prompts:
            self.prompts.append(prompt)
            self.model.set_classes(self.prompts)
```

### Phase 3: SAG UI Integration (P2)

**WebSocket for real-time events:**
```javascript
// /ganuda/sag/static/js/cameras-realtime.js
class FrigateEventStream {
    constructor() {
        this.mqtt = new Paho.MQTT.Client("bluefin", 9001, "sag-ui-" + Date.now());
    }

    connect() {
        this.mqtt.connect({
            onSuccess: () => {
                this.mqtt.subscribe("frigate/events");
                this.mqtt.subscribe("frigate/+/snapshot");
            }
        });

        this.mqtt.onMessageArrived = (msg) => {
            const event = JSON.parse(msg.payloadString);
            this.onDetection(event);
        };
    }

    onDetection(event) {
        // Add to timeline
        addTimelineEvent({
            time: new Date(event.after.start_time * 1000).toLocaleTimeString(),
            icon: this.getIcon(event.after.label),
            description: event.after.label,
            camera: event.after.camera,
            confidence: (event.after.top_score * 100).toFixed(0) + '%',
            thumbnail: event.after.thumbnail
        });

        // Update camera overlay
        drawBoundingBox(event.after.camera, event.after.box);
    }

    getIcon(label) {
        const icons = {
            'person': '🚶', 'car': '🚗', 'truck': '🚛',
            'delivery truck': '📦', 'cat': '🐱', 'dog': '🐕',
            'bird': '🐦', 'FedEx truck': '📦', 'UPS truck': '📦'
        };
        return icons[label] || '🎯';
    }
}
```

### Phase 4: VLM Enhancement (P2)

Integrate YOLO-World detections with Qwen2-VL for rich descriptions:

```python
def detect_and_describe(image_path, camera_id):
    # YOLO-World detection
    yolo = get_yolo_world()
    detections = yolo.detect(image_path)

    if not detections:
        return {"detections": [], "description": "No objects detected"}

    # Build context from detections
    detected_objects = [f"{d['class']} ({d['confidence']:.0%})" for d in detections]

    # VLM description with detection context
    vlm = get_vlm()
    prompt = f"""Objects detected: {', '.join(detected_objects)}

Describe the scene in detail. For each detected object:
1. Provide specific identifying details (color, make, markings)
2. What are they doing/their state?
3. Any notable interactions between objects?

Be specific and concise."""

    description = vlm.describe_frame(image_path, camera_id, prompt)

    return {
        "detections": detections,
        "description": description,
        "annotated_image": draw_boxes(image_path, detections)
    }
```

## Hardware Utilization

| Component | Resource | Usage |
|-----------|----------|-------|
| **Frigate** | CPU + minimal GPU | Motion detection, RTSP handling |
| **YOLO-World** | RTX 5070 (16GB) | Object detection ~50ms/frame |
| **Qwen2-VL** | RTX 5070 | Rich descriptions ~2s/request |
| **ring-mqtt** | CPU | Ring cloud bridge |
| **EMQX** | CPU | MQTT message broker |

**Estimated GPU Memory:**
- YOLO-World-L: ~4GB
- Qwen2-VL-7B: ~14GB
- Total: ~18GB (fits in RTX 5070 16GB with offloading)

## Detection Prompts (Cherokee Tribal Vision)

```python
TRIBAL_VISION_PROMPTS = {
    "vehicles": [
        "car", "truck", "pickup truck", "SUV", "van",
        "delivery truck", "FedEx truck", "UPS truck",
        "Amazon van", "USPS truck", "mail truck",
        "motorcycle", "bicycle", "scooter"
    ],
    "people": [
        "person", "mail carrier", "delivery person"
    ],
    "wildlife": [
        "cat", "dog", "bird", "squirrel", "rabbit",
        "deer", "raccoon", "opossum", "fox"
    ],
    "objects": [
        "package", "box", "bag", "suitcase"
    ],
    "calibration": [
        "Chevrolet Silverado", "white pickup truck"
    ]
}
```

## Success Metrics

| Metric | Target |
|--------|--------|
| Detection latency | < 100ms from motion to box |
| VLM description | < 3s for full analysis |
| False positive rate | < 10% |
| Missed detections | < 5% for target objects |
| UI refresh rate | Real-time via WebSocket |
| Storage efficiency | 7-day retention with object filtering |

## Security Considerations

- Frigate runs locally - no cloud dependency for detection
- MQTT on localhost only
- Ring cloud bridge isolated in container
- Camera credentials in environment variables
- Detection events logged to thermal memory

## References

- [Frigate NVR](https://github.com/blakeblackshear/frigate) - 29.7k stars
- [YOLO-World](https://github.com/AILab-CVC/YOLO-World) - Zero-shot detection
- [YOLO26](https://blog.roboflow.com/yolo26/) - Latest YOLO (Jan 2026)
- [RF-DETR](https://blog.roboflow.com/best-object-detection-models/) - YOLO alternative
- KB-RING-DOORBELL-ONDEMAND-STREAMING-JAN23-2026.md

---

**FOR SEVEN GENERATIONS** - The tribe sees all, understands all.

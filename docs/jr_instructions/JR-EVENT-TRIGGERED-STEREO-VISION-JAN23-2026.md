# JR Instruction: Event-Triggered Stereo Vision

**Task ID:** STEREO-TRIGGER-001
**Priority:** P1
**Assigned Node:** bluefin
**Date:** January 23, 2026

## Objective

Enhance the tribal vision system to trigger Ring doorbell stream when Amcrest traffic camera detects motion, enabling stereo depth estimation through triangulation.

## Background

Ring doorbells are **on-demand cameras** - they cannot stream 24/7 without battery drain, overheating, and loss of motion notifications (see KB-RING-DOORBELL-ONDEMAND-STREAMING-JAN23-2026). The solution is event-triggered stereo:

1. Amcrest traffic camera monitors continuously (already running)
2. When motion detected, trigger Ring stream via go2rtc/ring-mqtt
3. Capture synchronized frames from both cameras
4. Perform triangulation for depth estimation
5. Release Ring stream after analysis (~10-60 seconds)

## Architecture

```
Amcrest Traffic (continuous)
         │
         ▼
   Motion Detected ──────────────────────────────┐
         │                                       │
         ▼                                       ▼
  Capture Traffic Frame               Trigger Ring Stream
         │                                       │
         ▼                                       ▼
   Save to /detections/              Capture Ring Frame
         │                                       │
         └───────────────┬───────────────────────┘
                         │
                         ▼
              Stereo Depth Analysis
                         │
                         ▼
              Release Ring Stream
```

## Camera Registry

```python
CAMERAS = {
    "traffic": {
        "url": "rtsp://admin:jawaseatlasers2@192.168.132.182:554/cam/realmonitor?channel=1&subtype=1",
        "type": "outdoor",
        "continuous": True,
        "location": "street_view",
        "height_m": 3.0,  # Estimated pole height
        "fov_h": 90
    },
    "office": {
        "url": "rtsp://admin:jawaseatlasers2@192.168.132.181:554/cam/realmonitor?channel=1&subtype=0",
        "type": "indoor",
        "continuous": True,
        "location": "office",
        "height_m": 1.7
    },
    "doorbell": {
        "url": "rtsp://ring:tribal_vision_2026@localhost:8554/d436398fc2b8_live",
        "type": "outdoor",
        "continuous": False,  # ON-DEMAND ONLY
        "location": "front_door",
        "stereo_pair": "traffic",
        "height_m": 1.1,  # Ring at ~3.5 feet
        "fov_h": 160,  # Wide angle doorbell
        "activation_delay_sec": 3.0  # Cloud latency
    }
}
```

## Implementation Steps

### Step 1: Add Ring Stream Activation Function

Create `/ganuda/lib/tribal_vision/ring_stream.py`:

```python
"""Ring Doorbell On-Demand Stream Manager"""

import httpx
import time
import cv2
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass

@dataclass
class RingStreamConfig:
    rtsp_url: str = "rtsp://ring:tribal_vision_2026@localhost:8554/d436398fc2b8_live"
    activation_timeout: float = 10.0  # Max wait for stream to start
    capture_delay: float = 3.0  # Cloud latency buffer
    max_duration: float = 60.0  # Auto-release after

class RingStream:
    """Manages on-demand Ring doorbell stream lifecycle"""

    def __init__(self, config: RingStreamConfig = None):
        self.config = config or RingStreamConfig()
        self.active = False
        self.start_time = None

    def activate(self) -> bool:
        """Activate Ring stream (triggers cloud connection)"""
        # Simply opening RTSP connection triggers Ring
        cap = cv2.VideoCapture(self.config.rtsp_url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Wait for stream to become available
        start = time.time()
        while time.time() - start < self.config.activation_timeout:
            ret, _ = cap.read()
            if ret:
                cap.release()
                self.active = True
                self.start_time = time.time()
                print(f"[Ring] Stream activated after {time.time()-start:.1f}s")
                return True
            time.sleep(0.5)

        cap.release()
        print("[Ring] Stream activation timeout")
        return False

    def capture_frame(self) -> Optional[cv2.Mat]:
        """Capture single frame from active stream"""
        if not self.active:
            if not self.activate():
                return None

        cap = cv2.VideoCapture(self.config.rtsp_url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Skip buffered frames
        for _ in range(5):
            cap.read()

        ret, frame = cap.read()
        cap.release()

        return frame if ret else None

    def release(self):
        """Release stream (stops cloud connection)"""
        self.active = False
        self.start_time = None
        print("[Ring] Stream released")

    def auto_release_check(self):
        """Auto-release if duration exceeded"""
        if self.active and self.start_time:
            if time.time() - self.start_time > self.config.max_duration:
                print(f"[Ring] Auto-releasing after {self.config.max_duration}s")
                self.release()
```

### Step 2: Update Delivery Watch for Stereo Capture

Modify `/ganuda/lib/tribal_vision/quick_delivery_watch.py`:

```python
# Add imports
from ring_stream import RingStream

# Add Ring stream instance
ring = RingStream()

def capture_stereo_pair():
    """Capture synchronized frames from traffic + Ring cameras"""
    traffic_frame = capture_frame()  # Existing function

    if traffic_frame is None:
        return None, None

    # Activate Ring and capture
    ring_frame = ring.capture_frame()

    return traffic_frame, ring_frame

def analyze_with_stereo(traffic_path, ring_path):
    """Analyze both frames with optional depth estimation"""
    # First, analyze traffic frame (primary)
    traffic_result = analyze_with_vlm(traffic_path)

    # If Ring frame available, do stereo analysis
    if ring_path and ring_path.exists():
        prompt = f"""Compare these two camera views of the same scene.
Traffic camera analysis: {traffic_result.get('description', 'N/A')}

For the Ring doorbell view:
1. Do you see the same objects/vehicles/people?
2. Can you estimate how close they are to the house?
3. Any additional details visible from this angle?"""

        ring_result = analyze_with_vlm(ring_path, prompt)
        return {"traffic": traffic_result, "ring": ring_result, "stereo": True}

    return {"traffic": traffic_result, "stereo": False}

# Update main loop to use stereo capture on motion
def on_motion_detected():
    """Called when motion detected on traffic camera"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    traffic_frame, ring_frame = capture_stereo_pair()

    traffic_path = FRAME_DIR / f"traffic_{timestamp}.jpg"
    ring_path = FRAME_DIR / f"ring_{timestamp}.jpg" if ring_frame is not None else None

    cv2.imwrite(str(traffic_path), traffic_frame)
    if ring_frame is not None:
        cv2.imwrite(str(ring_path), ring_frame)

    result = analyze_with_stereo(traffic_path, ring_path)

    # Auto-release Ring after analysis
    ring.auto_release_check()

    return result
```

### Step 3: Verify MQTT/Ring-mqtt Status

The Ring integration requires:
1. EMQX MQTT broker running on port 1883
2. ring-mqtt container running with host networking

Verification commands:
```bash
# Check MQTT broker
ss -tlnp | grep 1883

# Check ring-mqtt
podman logs ring-mqtt --tail 20

# Test Ring stream
timeout 10 ffprobe rtsp://ring:tribal_vision_2026@localhost:8554/d436398fc2b8_live
```

### Step 4: Create Stereo Service Unit

Create `/ganuda/lib/tribal_vision/stereo_vision_service.py` for systemd:

```python
#!/usr/bin/env python3
"""Stereo Vision Service - Event-triggered Ring + Amcrest"""

import cv2
import time
import signal
import sys
from pathlib import Path
from datetime import datetime
from ring_stream import RingStream
from quick_delivery_watch import (
    capture_frame, detect_motion, analyze_with_vlm,
    VLM_URL, FRAME_DIR, COOLDOWN_SECONDS
)

running = True
ring = RingStream()

def signal_handler(sig, frame):
    global running
    print("\n[Stereo] Shutting down...")
    ring.release()
    running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def main():
    print("[Stereo Vision] Starting event-triggered stereo...")
    print(f"  Traffic camera: continuous monitoring")
    print(f"  Ring doorbell: on-demand activation")
    print(f"  VLM endpoint: {VLM_URL}")

    last_trigger = 0

    while running:
        try:
            frame = capture_frame()
            if frame is None:
                time.sleep(1)
                continue

            if detect_motion(frame):
                now = time.time()
                if now - last_trigger >= COOLDOWN_SECONDS:
                    print(f"\n[Stereo] Motion detected - triggering stereo capture")
                    last_trigger = now

                    # Save traffic frame
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    traffic_path = FRAME_DIR / f"stereo_traffic_{ts}.jpg"
                    cv2.imwrite(str(traffic_path), frame)

                    # Trigger Ring and capture
                    ring_frame = ring.capture_frame()
                    if ring_frame is not None:
                        ring_path = FRAME_DIR / f"stereo_ring_{ts}.jpg"
                        cv2.imwrite(str(ring_path), ring_frame)
                        print(f"[Stereo] Captured pair: {traffic_path.name}, {ring_path.name}")
                    else:
                        print(f"[Stereo] Ring capture failed, traffic only: {traffic_path.name}")

            # Auto-release Ring if idle
            ring.auto_release_check()
            time.sleep(0.1)

        except Exception as e:
            print(f"[Stereo] Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
```

## Verification

```bash
# Test Ring activation
ssh bluefin "cd /ganuda/lib/tribal_vision && python3 -c 'from ring_stream import RingStream; r=RingStream(); print(r.activate())'"

# Check captured stereo pairs
ssh bluefin "ls -la /ganuda/data/vision/frames/stereo_*"

# Monitor stereo service
journalctl --user -f -u stereo-vision
```

## Success Criteria

- [ ] Ring stream activates within 5 seconds of motion detection
- [ ] Stereo frame pairs captured to `/ganuda/data/vision/frames/`
- [ ] Ring stream auto-releases after 60 seconds
- [ ] VLM analyzes both camera views
- [ ] Ring motion notifications still work (not blocked by continuous streaming)

## Ring Stream Timing Reference

| Phase | Duration | Notes |
|-------|----------|-------|
| Activation trigger | ~0.5s | RTSP connection initiated |
| Cloud handshake | 1-3s | Ring cloud routing |
| First frame | 3-4s | Total from trigger |
| Capture window | 10-60s | Configurable |
| Release | ~5s | Stream disconnects |

## Security Notes

- Ring credentials in `/ganuda/services/ring-mqtt/data/`
- RTSP password: tribal_vision_2026
- Token auto-refreshes via ring-mqtt

## References

- KB-RING-DOORBELL-ONDEMAND-STREAMING-JAN23-2026.md
- JR-TRIBAL-VISION-STEREO-HUB-JAN23-2026.md
- ULTRATHINK-TRIBAL-VISION-STEREO-ARCHITECTURE-JAN23-2026.md

---

**FOR SEVEN GENERATIONS** - The tribe now has depth perception.

# JR Instruction: Tribal Vision Alert Service

**Task ID:** TRIBAL-VISION-ALERT-001
**Priority:** P1
**Assigned Node:** bluefin
**Date:** January 23, 2026

## Objective

Build a motion-triggered vision alert service that:
1. Monitors IP cameras for motion using OpenCV background subtraction
2. On motion detection, captures frame and sends to local VLM for analysis
3. Detects delivery trucks (FedEx, UPS, Amazon, USPS) and vehicles
4. Sends Telegram notifications for delivery arrivals
5. Logs events to thermal memory for pattern analysis

**NOTE:** Speed estimation deferred to future phase.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   IP Cameras    │────▶│  Motion Detector │────▶│  VLM Analysis   │
│ 192.168.132.181 │     │  (OpenCV MOG2)   │     │  (Port 8092)    │
│ 192.168.132.182 │     └──────────────────┘     └─────────────────┘
└─────────────────┘              │                        │
                                 │                        ▼
                                 │              ┌─────────────────┐
                                 │              │ Delivery Detect │
                                 │              │ Speed Estimate  │
                                 │              └─────────────────┘
                                 │                        │
                                 ▼                        ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │  Frame Storage  │     │    Telegram     │
                        │ /ganuda/data/   │     │   Notification  │
                        │ vision/frames/  │     └─────────────────┘
                        └─────────────────┘              │
                                                         ▼
                                                ┌─────────────────┐
                                                │ Thermal Memory  │
                                                │  Event Logging  │
                                                └─────────────────┘
```

## Implementation Steps

### Step 1: Create Motion Detector Module

**File:** `/ganuda/lib/tribal_vision/motion_detector.py`

```python
"""
Motion Detector using OpenCV Background Subtraction
Uses MOG2 (Mixture of Gaussians) for robust motion detection
"""

import cv2
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class MotionDetector:
    """Detects motion in video stream using background subtraction."""

    def __init__(
        self,
        camera_url: str,
        camera_id: str,
        min_area: int = 5000,
        cooldown_seconds: int = 10,
        history: int = 500,
        var_threshold: int = 16
    ):
        self.camera_url = camera_url
        self.camera_id = camera_id
        self.min_area = min_area  # Minimum contour area to trigger
        self.cooldown_seconds = cooldown_seconds
        self.last_trigger = None

        # MOG2 Background Subtractor
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=history,
            varThreshold=var_threshold,
            detectShadows=True
        )

        # Frame buffer for speed estimation
        self.frame_buffer = []
        self.buffer_timestamps = []
        self.max_buffer_size = 5

    def _in_cooldown(self) -> bool:
        """Check if we're in cooldown period after last trigger."""
        if self.last_trigger is None:
            return False
        elapsed = (datetime.now() - self.last_trigger).total_seconds()
        return elapsed < self.cooldown_seconds

    def capture_frame(self) -> Optional[np.ndarray]:
        """Capture single frame from camera."""
        cap = cv2.VideoCapture(self.camera_url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        ret, frame = cap.read()
        cap.release()

        if ret:
            return frame
        logger.warning(f"Failed to capture frame from {self.camera_id}")
        return None

    def detect_motion(self, frame: np.ndarray) -> Tuple[bool, float, list]:
        """
        Detect motion in frame.

        Returns:
            (motion_detected, motion_area_percent, bounding_boxes)
        """
        # Apply background subtraction
        fg_mask = self.bg_subtractor.apply(frame)

        # Remove shadows (marked as 127 in MOG2)
        _, fg_mask = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)

        # Morphological operations to reduce noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)

        # Find contours
        contours, _ = cv2.findContours(
            fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Filter by area
        significant_contours = [
            c for c in contours if cv2.contourArea(c) > self.min_area
        ]

        if not significant_contours:
            return False, 0.0, []

        # Calculate total motion area
        total_area = sum(cv2.contourArea(c) for c in significant_contours)
        frame_area = frame.shape[0] * frame.shape[1]
        motion_percent = (total_area / frame_area) * 100

        # Get bounding boxes
        bboxes = [cv2.boundingRect(c) for c in significant_contours]

        return True, motion_percent, bboxes

    def add_to_buffer(self, frame: np.ndarray):
        """Add frame to buffer for speed estimation."""
        now = datetime.now()
        self.frame_buffer.append(frame.copy())
        self.buffer_timestamps.append(now)

        # Keep buffer limited
        while len(self.frame_buffer) > self.max_buffer_size:
            self.frame_buffer.pop(0)
            self.buffer_timestamps.pop(0)

    def get_speed_frames(self) -> list:
        """Get recent frames for speed estimation."""
        return list(zip(self.frame_buffer, self.buffer_timestamps))

    def check_for_motion(self) -> Optional[dict]:
        """
        Main loop iteration: capture frame, check for motion.

        Returns motion event dict if triggered, None otherwise.
        """
        if self._in_cooldown():
            return None

        frame = self.capture_frame()
        if frame is None:
            return None

        # Add to buffer regardless
        self.add_to_buffer(frame)

        motion_detected, motion_percent, bboxes = self.detect_motion(frame)

        if motion_detected and motion_percent > 0.5:  # At least 0.5% of frame
            self.last_trigger = datetime.now()

            return {
                'camera_id': self.camera_id,
                'timestamp': self.last_trigger.isoformat(),
                'motion_percent': round(motion_percent, 2),
                'bounding_boxes': bboxes,
                'frame': frame,
                'speed_frames': self.get_speed_frames()
            }

        return None
```

### Step 2: Create Speed Estimator Module

**File:** `/ganuda/lib/tribal_vision/speed_estimator.py`

```python
"""
Vehicle Speed Estimator using multi-frame displacement tracking.

Calibration required: Set pixels_per_meter based on known reference distances
in the camera's field of view.
"""

import cv2
import numpy as np
from datetime import datetime
from typing import Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)


class SpeedEstimator:
    """Estimates vehicle speed from frame sequence."""

    # Calibration: pixels per meter (adjust based on camera FOV)
    # Default assumes ~20 meters visible width at 704 pixels
    PIXELS_PER_METER = 35.0

    # Speed thresholds (mph)
    SPEED_LIMIT = 25  # Residential
    SPEEDING_THRESHOLD = 35

    def __init__(self, pixels_per_meter: float = None):
        if pixels_per_meter:
            self.pixels_per_meter = pixels_per_meter
        else:
            self.pixels_per_meter = self.PIXELS_PER_METER

    def estimate_speed(
        self,
        frames_with_timestamps: List[Tuple[np.ndarray, datetime]]
    ) -> Optional[dict]:
        """
        Estimate speed from sequence of frames.

        Uses optical flow to track movement between frames.
        """
        if len(frames_with_timestamps) < 2:
            return None

        try:
            # Get first and last frames
            frame1, time1 = frames_with_timestamps[0]
            frame2, time2 = frames_with_timestamps[-1]

            # Convert to grayscale
            gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

            # Calculate optical flow using Farneback
            flow = cv2.calcOpticalFlowFarneback(
                gray1, gray2, None,
                pyr_scale=0.5, levels=3, winsize=15,
                iterations=3, poly_n=5, poly_sigma=1.2, flags=0
            )

            # Get magnitude of flow vectors
            mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])

            # Find region with maximum movement (likely the vehicle)
            # Use 95th percentile to avoid outliers
            max_displacement_pixels = np.percentile(mag, 95)

            # Calculate time difference
            time_diff = (time2 - time1).total_seconds()
            if time_diff <= 0:
                return None

            # Calculate speed
            displacement_meters = max_displacement_pixels / self.pixels_per_meter
            speed_mps = displacement_meters / time_diff
            speed_mph = speed_mps * 2.237  # Convert m/s to mph

            # Classify speed
            if speed_mph > self.SPEEDING_THRESHOLD:
                classification = "SPEEDING"
            elif speed_mph > self.SPEED_LIMIT:
                classification = "above_limit"
            else:
                classification = "normal"

            return {
                'speed_mph': round(speed_mph, 1),
                'speed_mps': round(speed_mps, 2),
                'classification': classification,
                'displacement_pixels': round(max_displacement_pixels, 1),
                'time_window_seconds': round(time_diff, 2),
                'frames_analyzed': len(frames_with_timestamps)
            }

        except Exception as e:
            logger.error(f"Speed estimation failed: {e}")
            return None
```

### Step 3: Create Delivery Detector Module

**File:** `/ganuda/lib/tribal_vision/delivery_detector.py`

```python
"""
Delivery Truck Detector using VLM analysis.

Sends frames to local VLM (Qwen2-VL) for vehicle identification
and delivery company recognition.
"""

import httpx
import json
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DeliveryDetector:
    """Detects delivery trucks using VLM analysis."""

    VLM_URL = "http://localhost:8092"

    DELIVERY_COMPANIES = [
        'amazon', 'fedex', 'ups', 'usps', 'dhl', 'ontrac',
        'lasership', 'usps', 'postal service', 'prime'
    ]

    VEHICLE_PROMPT = """Analyze this security camera image. Focus on any vehicles visible.

For each vehicle, identify:
1. Vehicle type (car, truck, van, SUV, motorcycle, etc.)
2. If it's a delivery vehicle, identify the company (Amazon, FedEx, UPS, USPS, DHL, etc.)
3. Vehicle color
4. Whether the vehicle is parked, stopped, or moving
5. Location in frame (driveway, street, etc.)

If this appears to be a delivery truck at a residence, note "DELIVERY_ALERT: [company name]".

Be concise but thorough."""

    def __init__(self, vlm_url: str = None):
        self.vlm_url = vlm_url or self.VLM_URL

    def analyze_frame(self, frame_path: str, camera_id: str) -> Optional[dict]:
        """
        Send frame to VLM for delivery truck analysis.

        Args:
            frame_path: Path to saved frame image
            camera_id: Camera identifier

        Returns:
            Analysis result dict or None on error
        """
        start = datetime.now()

        try:
            response = httpx.post(
                f"{self.vlm_url}/v1/vlm/describe",
                json={
                    "image_path": frame_path,
                    "prompt": self.VEHICLE_PROMPT,
                    "camera_id": camera_id
                },
                timeout=180.0  # VLM is slow on CPU
            )

            result = response.json()
            latency_ms = (datetime.now() - start).total_seconds() * 1000

            description = result.get('description', '').lower()

            # Check for delivery companies
            detected_company = None
            for company in self.DELIVERY_COMPANIES:
                if company in description:
                    detected_company = company.upper()
                    if company == 'prime':
                        detected_company = 'AMAZON'
                    break

            # Check for delivery alert in VLM response
            is_delivery = 'delivery_alert' in description or detected_company is not None

            return {
                'success': result.get('success', False),
                'camera_id': camera_id,
                'description': result.get('description', ''),
                'is_delivery': is_delivery,
                'delivery_company': detected_company,
                'vlm_latency_ms': latency_ms,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"VLM analysis failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'camera_id': camera_id,
                'timestamp': datetime.now().isoformat()
            }
```

### Step 4: Create Alert Service (Main Daemon)

**File:** `/ganuda/lib/tribal_vision/alert_service.py`

```python
"""
Tribal Vision Alert Service

Main daemon that coordinates motion detection, VLM analysis,
speed estimation, and notifications.
"""

import os
import cv2
import time
import json
import httpx
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from .motion_detector import MotionDetector
from .speed_estimator import SpeedEstimator
from .delivery_detector import DeliveryDetector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TribalVisionAlertService:
    """Main alert service coordinating all vision components."""

    # Camera configuration
    CAMERAS = {
        'office': {
            'url': 'rtsp://192.168.132.181:554/stream1',
            'type': 'indoor',
            'min_motion_area': 8000
        },
        'traffic': {
            'url': 'rtsp://192.168.132.182:554/user=admin_password=_channel=1_stream=0.sdp',
            'type': 'outdoor',
            'min_motion_area': 5000,
            'pixels_per_meter': 35.0  # Calibrate based on known distances
        }
    }

    FRAME_DIR = Path('/ganuda/data/vision/frames')
    EVENT_LOG = Path('/ganuda/data/vision/events.jsonl')

    # Telegram configuration
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '-1001234567890')

    def __init__(self):
        self.detectors = {}
        self.speed_estimators = {}
        self.delivery_detector = DeliveryDetector()

        # Initialize detectors for each camera
        for camera_id, config in self.CAMERAS.items():
            self.detectors[camera_id] = MotionDetector(
                camera_url=config['url'],
                camera_id=camera_id,
                min_area=config.get('min_motion_area', 5000),
                cooldown_seconds=30
            )

            if config['type'] == 'outdoor':
                self.speed_estimators[camera_id] = SpeedEstimator(
                    pixels_per_meter=config.get('pixels_per_meter')
                )

        # Ensure directories exist
        self.FRAME_DIR.mkdir(parents=True, exist_ok=True)

    def save_frame(self, frame, camera_id: str, event_type: str) -> str:
        """Save frame to disk and return path."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{camera_id}_{event_type}_{timestamp}.jpg"
        path = self.FRAME_DIR / filename
        cv2.imwrite(str(path), frame)
        return str(path)

    def log_event(self, event: dict):
        """Append event to JSONL log."""
        with open(self.EVENT_LOG, 'a') as f:
            f.write(json.dumps(event) + '\n')

    def send_telegram_alert(self, message: str, image_path: str = None):
        """Send alert to Telegram."""
        if not self.TELEGRAM_BOT_TOKEN:
            logger.warning("Telegram not configured, skipping notification")
            return

        try:
            if image_path and os.path.exists(image_path):
                # Send photo with caption
                url = f"https://api.telegram.org/bot{self.TELEGRAM_BOT_TOKEN}/sendPhoto"
                with open(image_path, 'rb') as photo:
                    httpx.post(url, data={
                        'chat_id': self.TELEGRAM_CHAT_ID,
                        'caption': message
                    }, files={'photo': photo}, timeout=30.0)
            else:
                # Send text only
                url = f"https://api.telegram.org/bot{self.TELEGRAM_BOT_TOKEN}/sendMessage"
                httpx.post(url, json={
                    'chat_id': self.TELEGRAM_CHAT_ID,
                    'text': message
                }, timeout=30.0)

            logger.info(f"Telegram alert sent: {message[:50]}...")

        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")

    def store_thermal_memory(self, event: dict):
        """Store event in thermal memory for pattern analysis."""
        try:
            # Connect to thermal memory API
            httpx.post(
                "http://localhost:8080/api/memories",
                json={
                    'content': json.dumps(event),
                    'memory_type': 'vision_event',
                    'tags': ['tribal_vision', event.get('camera_id', 'unknown')],
                    'importance': 0.7 if event.get('is_delivery') else 0.3
                },
                timeout=10.0
            )
        except Exception as e:
            logger.debug(f"Thermal memory store skipped: {e}")

    def process_motion_event(self, event: dict):
        """Process a motion detection event."""
        camera_id = event['camera_id']
        frame = event['frame']

        # Save frame
        frame_path = self.save_frame(frame, camera_id, 'motion')
        logger.info(f"Motion detected on {camera_id}, saved to {frame_path}")

        # Speed estimation (outdoor cameras only)
        speed_result = None
        if camera_id in self.speed_estimators:
            speed_result = self.speed_estimators[camera_id].estimate_speed(
                event.get('speed_frames', [])
            )
            if speed_result:
                logger.info(f"Speed estimate: {speed_result['speed_mph']} mph ({speed_result['classification']})")

        # VLM delivery detection
        delivery_result = self.delivery_detector.analyze_frame(frame_path, camera_id)

        # Build event record
        full_event = {
            'type': 'motion',
            'camera_id': camera_id,
            'timestamp': event['timestamp'],
            'motion_percent': event['motion_percent'],
            'frame_path': frame_path,
            'speed': speed_result,
            'delivery': delivery_result,
            'is_delivery': delivery_result.get('is_delivery', False) if delivery_result else False
        }

        # Log event
        self.log_event(full_event)

        # Send alerts
        if delivery_result and delivery_result.get('is_delivery'):
            company = delivery_result.get('delivery_company', 'Unknown')
            message = f"📦 DELIVERY ALERT: {company} truck detected!\n\n{delivery_result.get('description', '')[:200]}"
            self.send_telegram_alert(message, frame_path)
            self.store_thermal_memory(full_event)

        elif speed_result and speed_result.get('classification') == 'SPEEDING':
            message = f"🚗 SPEEDING: {speed_result['speed_mph']} mph detected on {camera_id}"
            self.send_telegram_alert(message, frame_path)
            self.store_thermal_memory(full_event)

    def run(self, poll_interval: float = 1.0):
        """Main run loop."""
        logger.info("Tribal Vision Alert Service starting...")
        logger.info(f"Monitoring {len(self.CAMERAS)} cameras")

        while True:
            for camera_id, detector in self.detectors.items():
                try:
                    motion_event = detector.check_for_motion()

                    if motion_event:
                        self.process_motion_event(motion_event)

                except Exception as e:
                    logger.error(f"Error processing {camera_id}: {e}")

            time.sleep(poll_interval)


def main():
    """Entry point."""
    service = TribalVisionAlertService()
    service.run()


if __name__ == '__main__':
    main()
```

### Step 5: Create Package Init

**File:** `/ganuda/lib/tribal_vision/__init__.py`

```python
"""Tribal Vision - Motion-triggered camera monitoring with VLM analysis."""

from .motion_detector import MotionDetector
from .speed_estimator import SpeedEstimator
from .delivery_detector import DeliveryDetector
from .alert_service import TribalVisionAlertService

__all__ = [
    'MotionDetector',
    'SpeedEstimator',
    'DeliveryDetector',
    'TribalVisionAlertService'
]
```

### Step 6: Create Systemd Service

**File:** `/ganuda/scripts/systemd/tribal-vision.service`

```ini
[Unit]
Description=Tribal Vision Alert Service
After=network.target

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda/lib
ExecStart=/usr/bin/python3 -m tribal_vision.alert_service
Restart=always
RestartSec=10
Environment=PYTHONPATH=/ganuda/lib
Environment=TELEGRAM_BOT_TOKEN=
Environment=TELEGRAM_CHAT_ID=

[Install]
WantedBy=multi-user.target
```

### Step 7: Deployment Commands

```bash
# On bluefin - create directory structure
mkdir -p /ganuda/lib/tribal_vision
mkdir -p /ganuda/data/vision/frames
mkdir -p /ganuda/data/vision/events

# Copy service file
sudo cp /ganuda/scripts/systemd/tribal-vision.service /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable tribal-vision
sudo systemctl start tribal-vision

# Check status
sudo systemctl status tribal-vision
journalctl -u tribal-vision -f
```

## Calibration Notes

### Speed Estimation Calibration

To calibrate `pixels_per_meter` for accurate speed detection:

1. Identify a known distance in the camera frame (e.g., driveway width, distance between fence posts)
2. Capture a frame and measure the pixel distance
3. Calculate: `pixels_per_meter = pixel_distance / actual_meters`

Example:
- Driveway is 12 feet (3.66 meters) wide
- In frame, driveway spans 128 pixels
- `pixels_per_meter = 128 / 3.66 = 35.0`

### Motion Sensitivity Tuning

Adjust `min_area` based on camera resolution and typical object sizes:
- **Traffic cam (704x480)**: 5000 pixels (~1.5% of frame) works well for vehicles
- **Office cam (2960x1668)**: 8000 pixels needed due to higher resolution

## Verification

```bash
# Test motion detection manually
python3 -c "
from tribal_vision import MotionDetector
md = MotionDetector('rtsp://192.168.132.182:554/user=admin_password=_channel=1_stream=0.sdp', 'traffic')
for i in range(10):
    result = md.check_for_motion()
    print(f'Frame {i}: Motion={result is not None}')
    import time; time.sleep(1)
"

# Check event log
tail -f /ganuda/data/vision/events.jsonl
```

## Success Criteria

- [ ] Motion detection triggers on vehicle movement
- [ ] VLM correctly identifies delivery trucks
- [ ] Speed estimation produces reasonable values
- [ ] Telegram notifications arrive for deliveries
- [ ] Events logged to JSONL and thermal memory
- [ ] Service runs stably under systemd

## References

- OpenCV MOG2: https://docs.opencv.org/4.x/d7/d7b/classcv_1_1BackgroundSubtractorMOG2.html
- Optical Flow: https://docs.opencv.org/4.x/d4/dee/tutorial_optical_flow.html
- methylDragon/opencv-motion-detector: https://github.com/methylDragon/opencv-motion-detector

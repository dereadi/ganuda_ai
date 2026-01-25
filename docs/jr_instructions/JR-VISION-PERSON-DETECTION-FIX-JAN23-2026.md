# Jr Instruction: Fix Person Detection + Snow Gauge Tracking

**Task ID:** VISION-PERSON-001
**Priority:** P1
**Date:** January 23, 2026

## Problem Statement

1. **Person detection failing**: User walked in/out and wasn't detected. 323 motion frames today, zero person detections
2. **Snow gauge tracking**: User marked utility box with 6", 12", 15", 18" marks for snow accumulation measurement

## Analysis

Current detection pipeline:
- Traffic camera (192.168.132.182) triggers on motion
- Motion frames sent to YOLO-World (port 8091) for detection
- Only detects vehicles (confidence 0.4-0.5), never persons

Root causes:
1. Traffic camera faces ROAD, not walkway - people walking to door are peripheral
2. Motion detection threshold tuned for vehicle-sized motion, misses pedestrians
3. Single-camera approach misses correlated events

## Part 1: Multi-Camera Person Detection

**Approach**: Correlate motion across traffic + Ring + Office PII cameras

### 1.1 Add Ring to motion pipeline

**File:** `/ganuda/lib/tribal_vision/motion_detector.py`

The Ring doorbell faces the front door - prime location for person detection.

```python
# Add Ring to MOTION_CAMERAS list
MOTION_CAMERAS = {
    'traffic': {
        'rtsp_url': 'rtsp://admin:tribal_vision_2026@192.168.132.182:554/cam/realmonitor?channel=1&subtype=0',
        'motion_threshold': 500,  # Low for vehicles
    },
    'office_pii': {
        'rtsp_url': 'rtsp://admin:tribal_vision_2026@192.168.132.181:554/cam/realmonitor?channel=1&subtype=0',
        'motion_threshold': 200,  # Medium for office area
    },
    'ring_doorbell': {
        'rtsp_url': 'rtsp://ring:tribal_vision_2026@192.168.132.222:8554/d436398fc2b8_live',
        'motion_threshold': 150,  # Sensitive for people at door
        'on_demand': True,  # Ring needs wake-up call first
    },
}
```

### 1.2 Lower person confidence threshold

**File:** `/ganuda/services/vision/yolo_world_service.py`

Add class-specific thresholds:

```python
CLASS_CONFIDENCE_THRESHOLDS = {
    'person': 0.12,      # Very low - want to catch all people
    'human': 0.12,
    'pedestrian': 0.12,
    'car': 0.30,
    'truck': 0.30,
    'default': 0.25,
}

# In detect endpoint, use class-specific threshold
for cls, conf, r in detections:
    threshold = CLASS_CONFIDENCE_THRESHOLDS.get(cls, CLASS_CONFIDENCE_THRESHOLDS['default'])
    if conf >= threshold:
        # Include detection
```

### 1.3 Cross-camera person correlation

When person detected on ANY camera, immediately capture from all cameras:

```python
def on_person_detected(camera_id, detection):
    """Cross-camera capture when person seen anywhere."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for cam_id, cfg in MOTION_CAMERAS.items():
        if cam_id != camera_id:
            frame = capture_frame(cfg['rtsp_url'])
            path = f"/ganuda/data/vision/person_events/{timestamp}_{cam_id}.jpg"
            cv2.imwrite(path, frame)

    # Publish to MQTT for alerts
    mqtt_publish('tribal_vision/person_detected', {
        'camera': camera_id,
        'timestamp': timestamp,
        'detection': detection,
    })
```

---

## Part 2: Snow Gauge Tracking

User marked utility box closest to traffic camera with:
- 6" mark
- 12" mark
- 15" mark
- 18" mark

### 2.1 Document gauge position

Need to identify utility box in daytime frame and record pixel coordinates.

**Manual step**: Get daytime frame, identify utility box bbox

### 2.2 Snow measurement endpoint

**File:** `/ganuda/services/vision/snow_measurement.py`

```python
# Utility box region of interest (from daytime calibration)
SNOW_GAUGE_ROI = {
    'x1': 50,   # Will need calibration
    'y1': 250,
    'x2': 120,
    'y2': 350,
    'marks': {
        6: 320,    # y-coordinate of 6" mark
        12: 290,   # y-coordinate of 12" mark
        15: 275,   # y-coordinate of 15" mark
        18: 260,   # y-coordinate of 18" mark
    }
}

def measure_snow_level(frame):
    """
    Measure snow accumulation using utility box gauge.
    Returns estimated inches based on snow line position.
    """
    roi = frame[SNOW_GAUGE_ROI['y1']:SNOW_GAUGE_ROI['y2'],
                SNOW_GAUGE_ROI['x1']:SNOW_GAUGE_ROI['x2']]

    # Convert to grayscale
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # Find snow line (white-to-dark transition)
    # Snow appears white, marks are dark
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

    # Find topmost white pixel (snow level)
    white_pixels = np.where(thresh > 0)
    if len(white_pixels[0]) == 0:
        return {'snow_inches': 0, 'confidence': 'low'}

    snow_line_y = np.min(white_pixels[0]) + SNOW_GAUGE_ROI['y1']

    # Interpolate between marks
    marks = SNOW_GAUGE_ROI['marks']
    for inches, y_coord in sorted(marks.items(), reverse=True):
        if snow_line_y >= y_coord:
            return {'snow_inches': inches, 'confidence': 'high'}

    return {'snow_inches': 18, 'confidence': 'high'}  # Above 18"
```

### 2.3 Add to timelapse metadata

In `snow_timelapse.py`, add measurement to each frame:

```python
def capture_timelapse_frame(camera_id, frame):
    # ... existing capture code ...

    # If traffic camera, measure snow
    if camera_id == 'traffic':
        snow_data = measure_snow_level(frame)

        # Store in metadata file
        metadata_path = path.with_suffix('.json')
        with open(metadata_path, 'w') as f:
            json.dump({
                'timestamp': ts,
                'snow_inches': snow_data['snow_inches'],
                'confidence': snow_data['confidence'],
            }, f)
```

---

## Testing Checklist

- [ ] Capture daytime frame to calibrate utility box ROI
- [ ] Walk test: Approach front door, verify detection triggers
- [ ] Multi-camera: Person at Ring triggers traffic camera capture
- [ ] Snow measurement: Compare visual to calculated inches
- [ ] MQTT alert fires on person detection

---

## Calibration Data (January 23, 2026)

**Reference image**: `/ganuda/data/vision/calibration/utility_box_reference.png`

The utility box with snow gauge marks is visible on the **LEFT edge** of the traffic camera frame.

Based on detection analysis and visual inspection:
- **Utility box bbox**: approximately [0, 185, 60, 320] (left edge of frame)
- YOLO misidentifies it as "bus" at low confidence

**Calibrated SNOW_GAUGE_ROI**:
```python
SNOW_GAUGE_ROI = {
    'x1': 0,
    'y1': 185,
    'x2': 60,
    'y2': 320,
    'marks': {
        # Y-coordinates of marks (estimate - refine with daylight frame)
        6: 300,    # 6" mark near bottom
        12: 265,   # 12" mark (user confirmed visible at night)
        15: 245,   # 15" mark
        18: 225,   # 18" mark near top
    }
}
```

**Marks on utility box**: 6", 12", 15", 18" - horizontal lines marked by user for snow accumulation measurement.

The 12" mark is clearly visible even in night vision.

---

**FOR SEVEN GENERATIONS** - The snow falls, the cameras watch, the ancestors measure in generations.

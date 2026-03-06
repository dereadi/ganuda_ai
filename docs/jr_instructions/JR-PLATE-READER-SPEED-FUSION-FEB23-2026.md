# Jr Instruction: Plate Reader + Speed Fusion

**Task ID:** PLATE-SPEED
**Kanban:** #1736
**Priority:** 3
**Assigned:** Software Engineer Jr.

---

## Overview

Create a module to fuse PaddleOCR license plate readings with speed detection results, logging speed + plate per vehicle.

---

## Step 1: Create the plate-speed fusion module

Create `/ganuda/services/vision/plate_speed_fusion.py`

```python
"""Plate-Speed Fusion: Combines PaddleOCR plate reads with speed_detector output.
Logs vehicle speed + plate number per detection event."""

import re
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

PLATE_PATTERN = re.compile(r'^[A-Z0-9]{1,8}$')

def normalize_plate(raw_text):
    """Clean OCR output to normalized plate string."""
    cleaned = re.sub(r'[^A-Z0-9]', '', raw_text.upper().strip())
    if PLATE_PATTERN.match(cleaned) and len(cleaned) >= 2:
        return cleaned
    return None

def fuse_detection(speed_event, plate_text):
    """Combine a speed detection event with a plate reading.

    Args:
        speed_event: dict with keys track_id, speed_mph, timestamp, camera
        plate_text: raw OCR text from PaddleOCR

    Returns:
        dict with fused detection record
    """
    plate = normalize_plate(plate_text) if plate_text else None
    record = {
        "track_id": speed_event.get("track_id"),
        "speed_mph": speed_event.get("speed_mph"),
        "plate": plate,
        "plate_confidence": "high" if plate and len(plate) >= 5 else "low",
        "camera": speed_event.get("camera", "unknown"),
        "timestamp": speed_event.get("timestamp", datetime.now().isoformat()),
        "alert": speed_event.get("speed_mph", 0) > 25,
    }
    logger.info(f"Fused: track={record['track_id']} speed={record['speed_mph']} plate={record['plate']}")
    return record

def format_alert(record):
    """Format a speed alert with plate info for Telegram notification."""
    plate_str = record["plate"] if record["plate"] else "UNREADABLE"
    return (
        f"SPEED ALERT: {record['speed_mph']:.1f} mph\n"
        f"Plate: {plate_str} ({record['plate_confidence']})\n"
        f"Camera: {record['camera']}\n"
        f"Track: {record['track_id']}\n"
        f"Time: {record['timestamp']}"
    )

if __name__ == "__main__":
    test_event = {"track_id": 999, "speed_mph": 32.5, "camera": "garage", "timestamp": "2026-02-23T12:00:00"}
    result = fuse_detection(test_event, "ABC-1234")
    print(json.dumps(result, indent=2))
    print()
    print(format_alert(result))
```

---

## Verification

```text
python3 -c "
from plate_speed_fusion import fuse_detection, normalize_plate, format_alert
assert normalize_plate('ABC-1234') == 'ABC1234'
assert normalize_plate('a') is None
event = {'track_id': 1, 'speed_mph': 30.0, 'camera': 'garage'}
r = fuse_detection(event, 'XYZ 789')
print(f'Plate: {r[\"plate\"]}, Alert: {r[\"alert\"]}')
print(format_alert(r))
"
```

# JR Instruction: Tribal Vision Phase 2 - Advanced Camera Intelligence

**Priority**: P2 - Medium
**Assigned To**: Vision Jr. / Software Engineer Jr.
**Created**: January 21, 2026
**Status**: Ready for Execution

## Executive Summary

Enhance the Tribal Vision camera system with Phase 2 features:
1. **DeepSORT** - Multi-object tracking across frames
2. **License Plate Recognition** - Read plates from traffic camera
3. **Vehicle Fingerprinting** - Color, size, make/model estimation
4. **Unknown Vehicle Alerts** - Alert on vehicles not in learned database
5. **SAG Dashboard Integration** - Live camera feeds and alerts in UI

## Current State

### Working Features (Phase 1)
- YOLOv8n object detection
- Two cameras: Office PII (181) and Traffic (182)
- Face detection with MTCNN
- Known face recognition (Darrell enrolled)
- Systemd service running continuously
- Frame capture every 60 seconds

### Service Status
```
Active: active (running) since Mon 2026-01-19
Memory: 6.1G
Captures: office_pii_*.jpg, traffic_*.jpg every 60s
```

## Implementation Tasks

### Task 1: DeepSORT Vehicle Tracking

**Purpose**: Track vehicles across frames to maintain identity over time.

**Install Dependencies**:
```bash
pip install deep-sort-realtime filterpy
```

**New File**: `/ganuda/services/vision/vehicle_tracker.py`

```python
"""
Vehicle Tracker - DeepSORT integration for multi-object tracking.

Tracks vehicles across frames to:
1. Maintain consistent IDs
2. Calculate trajectories
3. Detect stopped/parked vehicles
4. Estimate speed (if calibrated)
"""

from deep_sort_realtime.deepsort_tracker import DeepSort
from typing import Dict, List, Tuple
import numpy as np


class VehicleTracker:
    """
    DeepSORT-based vehicle tracking.
    """

    def __init__(self, max_age: int = 30, n_init: int = 3):
        """
        Initialize tracker.

        Args:
            max_age: Max frames to keep track without detection
            n_init: Min detections before track is confirmed
        """
        self.tracker = DeepSort(
            max_age=max_age,
            n_init=n_init,
            nms_max_overlap=0.5,
            max_cosine_distance=0.4
        )
        self.vehicle_history: Dict[int, List[dict]] = {}

    def update(self, detections: List[dict], frame: np.ndarray) -> List[dict]:
        """
        Update tracker with new detections.

        Args:
            detections: List of {bbox: [x1,y1,x2,y2], confidence, class}
            frame: Current frame for re-identification

        Returns:
            List of tracked objects with persistent IDs
        """
        if not detections:
            return []

        # Format for DeepSORT: [[x1,y1,x2,y2,conf], ...]
        det_array = []
        for det in detections:
            bbox = det['bbox']
            det_array.append([
                bbox[0], bbox[1], bbox[2], bbox[3],
                det['confidence'],
                det['class']
            ])

        # Update tracker
        tracks = self.tracker.update_tracks(det_array, frame=frame)

        # Process tracks
        results = []
        for track in tracks:
            if not track.is_confirmed():
                continue

            track_id = track.track_id
            bbox = track.to_ltrb()  # [left, top, right, bottom]

            # Update history
            if track_id not in self.vehicle_history:
                self.vehicle_history[track_id] = []

            self.vehicle_history[track_id].append({
                'bbox': bbox.tolist(),
                'frame_time': time.time(),
                'centroid': self._get_centroid(bbox)
            })

            results.append({
                'track_id': track_id,
                'bbox': bbox.tolist(),
                'age': track.age,
                'hits': track.hits
            })

        return results

    def _get_centroid(self, bbox: np.ndarray) -> Tuple[float, float]:
        """Calculate bounding box centroid."""
        return (
            (bbox[0] + bbox[2]) / 2,
            (bbox[1] + bbox[3]) / 2
        )

    def get_vehicle_trajectory(self, track_id: int) -> List[Tuple[float, float]]:
        """Get movement trajectory for a tracked vehicle."""
        if track_id not in self.vehicle_history:
            return []
        return [h['centroid'] for h in self.vehicle_history[track_id]]

    def is_stationary(self, track_id: int, threshold: float = 10.0) -> bool:
        """
        Check if vehicle has been stationary.

        Args:
            track_id: Vehicle track ID
            threshold: Max pixel movement to be considered stationary
        """
        trajectory = self.get_vehicle_trajectory(track_id)
        if len(trajectory) < 5:
            return False

        # Check if recent positions are close together
        recent = trajectory[-5:]
        xs = [p[0] for p in recent]
        ys = [p[1] for p in recent]

        return (max(xs) - min(xs)) < threshold and (max(ys) - min(ys)) < threshold
```

### Task 2: License Plate Recognition

**Purpose**: Read license plates from traffic camera for vehicle identification.

**Research**: Based on analysis of proven GitHub implementations:
- [TDiblik/main-gate-alpr](https://github.com/TDiblik/main-gate-alpr) - 95% accuracy with YOLOv8 + Tesseract
- [Roee-BY/ipcams_and_webcams_licence_plate_reader](https://github.com/Roee-BY/ipcams_and_webcams_licence_plate_reader) - MIT license, IP cam focused

**Approach**: Use YOLOv8 (already installed) + Tesseract OCR with contrast enhancement and multi-round filtering.

**Dependencies**:
```bash
# Tesseract OCR (system package)
sudo apt-get install tesseract-ocr tesseract-ocr-eng

# Python packages
pip install pytesseract opencv-python scikit-image
```

**New File**: `/ganuda/services/vision/plate_reader.py`

```python
"""
License Plate Reader - Proven approach from GitHub research.

Based on:
- TDiblik/main-gate-alpr (YOLOv8 + Tesseract, 95% accuracy)
- Roee-BY/ipcams_and_webcams_licence_plate_reader (MIT, IP cam focused)

Uses YOLOv8 for vehicle detection + OpenCV preprocessing + Tesseract OCR.
"""

import cv2
import pytesseract
import numpy as np
from typing import Optional, Tuple, List
from skimage import exposure
from collections import Counter


class PlateReader:
    """
    License plate detection and OCR using proven GitHub approaches.

    Key techniques from research:
    1. Focus on lower 50% of vehicle crop (where plates are)
    2. Contrast enhancement (CLAHE) before OCR
    3. Multi-round filtering for confidence
    4. Character whitelist for plates
    """

    def __init__(self):
        # Tesseract config for license plates
        # -c tessedit_char_whitelist limits to plate characters
        # --psm 7 = single text line, --psm 8 = single word
        self.tesseract_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

        # Multi-round filtering: track recent reads
        self.recent_reads: List[str] = []
        self.max_recent = 5

    def preprocess_plate(self, plate_image: np.ndarray) -> np.ndarray:
        """
        Preprocess plate image for better OCR.

        Techniques from Roee-BY repo:
        - Grayscale conversion
        - Contrast enhancement (CLAHE)
        - Resize for better character recognition
        - Bilateral filter for noise reduction
        """
        # Convert to grayscale
        if len(plate_image.shape) == 3:
            gray = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = plate_image

        # Resize to standard height (better OCR accuracy)
        h, w = gray.shape
        if h < 50:
            scale = 50 / h
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        # CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Bilateral filter - reduce noise while keeping edges
        filtered = cv2.bilateralFilter(enhanced, 11, 17, 17)

        # Threshold to binary
        _, binary = cv2.threshold(filtered, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return binary

    def detect_plate_region(self, vehicle_crop: np.ndarray) -> Optional[np.ndarray]:
        """
        Find license plate region in vehicle crop.

        From TDiblik approach:
        - Focus on lower portion of vehicle
        - Find rectangular contours with plate-like aspect ratio
        - US plates: ~12"x6" = 2:1 ratio
        """
        h, w = vehicle_crop.shape[:2]

        # Focus on lower 50% of vehicle (where plates usually are)
        roi = vehicle_crop[int(h * 0.4):, :]

        # Convert to grayscale
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi

        # Edge detection
        edges = cv2.Canny(gray, 50, 150)

        # Dilate to connect edges
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        edges = cv2.dilate(edges, kernel, iterations=1)

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # Filter for plate-like rectangles
        candidates = []
        for contour in contours:
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)

            if len(approx) >= 4:
                x, y, cw, ch = cv2.boundingRect(contour)

                if ch == 0:
                    continue

                aspect_ratio = cw / ch
                area = cw * ch

                # US plates are roughly 2:1 aspect ratio
                # Filter by size and aspect ratio
                if 1.5 < aspect_ratio < 5.0 and area > 500 and cw > 60:
                    candidates.append((x, y, cw, ch, area))

        if not candidates:
            return None

        # Return largest candidate
        candidates.sort(key=lambda c: c[4], reverse=True)
        x, y, cw, ch, _ = candidates[0]

        # Add padding
        pad = 5
        x = max(0, x - pad)
        y = max(0, y - pad)
        cw = min(roi.shape[1] - x, cw + 2*pad)
        ch = min(roi.shape[0] - y, ch + 2*pad)

        return roi[y:y+ch, x:x+cw]

    def read_plate(self, plate_image: np.ndarray) -> Tuple[str, float]:
        """
        OCR the plate image using Tesseract.

        From TDiblik: multi-round filtering for confidence.
        """
        # Preprocess
        processed = self.preprocess_plate(plate_image)

        # OCR with Tesseract
        text = pytesseract.image_to_string(processed, config=self.tesseract_config)

        # Clean result
        clean = ''.join(c for c in text.upper() if c.isalnum())

        # Filter by length (US plates typically 5-8 chars)
        if len(clean) < 4 or len(clean) > 10:
            return "", 0.0

        # Multi-round confidence: track recent reads
        self.recent_reads.append(clean)
        if len(self.recent_reads) > self.max_recent:
            self.recent_reads.pop(0)

        # Calculate confidence based on consistency
        if len(self.recent_reads) >= 3:
            counter = Counter(self.recent_reads)
            most_common, count = counter.most_common(1)[0]
            confidence = count / len(self.recent_reads)
            return most_common, confidence

        # Single read confidence (lower)
        return clean, 0.5

    def process_vehicle(self, vehicle_crop: np.ndarray) -> Optional[dict]:
        """
        Full pipeline: detect plate region and read it.
        """
        plate_region = self.detect_plate_region(vehicle_crop)
        if plate_region is None:
            return None

        plate_text, confidence = self.read_plate(plate_region)
        if not plate_text or confidence < 0.4:
            return None

        return {
            'plate': plate_text,
            'confidence': confidence,
            'recent_reads': self.recent_reads.copy()
        }

    def reset_tracking(self):
        """Reset multi-round tracking for new vehicle."""
        self.recent_reads = []


# RTSP direct testing (from Roee-BY approach)
def test_rtsp_plate_reading(rtsp_url: str, output_dir: str = '/ganuda/data/vision'):
    """
    Test plate reading directly from RTSP stream.

    Usage:
        test_rtsp_plate_reading('rtsp://admin:pass@192.168.132.182:554/cam/realmonitor?channel=1&subtype=0')
    """
    import os
    from datetime import datetime

    cap = cv2.VideoCapture(rtsp_url)
    reader = PlateReader()

    if not cap.isOpened():
        print(f"Failed to open RTSP stream: {rtsp_url}")
        return

    print(f"Connected to {rtsp_url}")
    frame_count = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break

            frame_count += 1

            # Process every 30th frame (1 per second at 30fps)
            if frame_count % 30 != 0:
                continue

            # Try to read plate from full frame
            result = reader.process_vehicle(frame)

            if result and result['confidence'] > 0.6:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                print(f"[{timestamp}] Plate: {result['plate']} (conf: {result['confidence']:.2f})")

                # Save frame with detection
                output_path = os.path.join(output_dir, f"plate_{result['plate']}_{timestamp}.jpg")
                cv2.imwrite(output_path, frame)
                print(f"  Saved: {output_path}")

                # Reset for next vehicle
                reader.reset_tracking()

            # Break on 'q' key (if running with display)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_rtsp_plate_reading(sys.argv[1])
    else:
        print("Usage: python plate_reader.py <rtsp_url>")
        print("Example: python plate_reader.py 'rtsp://admin:pass@192.168.132.182:554/cam/realmonitor?channel=1&subtype=0'")
```

### Task 3: Vehicle Fingerprinting

**Purpose**: Identify vehicles by visual characteristics when plates aren't readable.

**New File**: `/ganuda/services/vision/vehicle_fingerprint.py`

```python
"""
Vehicle Fingerprinting - Identify vehicles by visual features.

Creates a fingerprint based on:
1. Dominant color
2. Size (relative to frame)
3. Shape features (aspect ratio, contours)
4. Make/model estimation (if model available)
"""

import cv2
import numpy as np
from typing import Dict, Tuple
from sklearn.cluster import KMeans


class VehicleFingerprint:
    """
    Create visual fingerprints for vehicles.
    """

    def __init__(self):
        pass

    def get_dominant_color(self, image: np.ndarray, k: int = 3) -> Tuple[int, int, int]:
        """
        Extract dominant color using K-means clustering.

        Returns:
            RGB tuple of dominant color
        """
        # Resize for speed
        small = cv2.resize(image, (50, 50))
        pixels = small.reshape(-1, 3)

        # K-means clustering
        kmeans = KMeans(n_clusters=k, n_init=10, random_state=42)
        kmeans.fit(pixels)

        # Find largest cluster
        unique, counts = np.unique(kmeans.labels_, return_counts=True)
        dominant_idx = unique[np.argmax(counts)]
        dominant_color = kmeans.cluster_centers_[dominant_idx]

        # Convert BGR to RGB
        return tuple(int(c) for c in dominant_color[::-1])

    def get_color_name(self, rgb: Tuple[int, int, int]) -> str:
        """Map RGB to color name."""
        r, g, b = rgb

        # Simple color classification
        if r > 200 and g > 200 and b > 200:
            return "white"
        elif r < 50 and g < 50 and b < 50:
            return "black"
        elif r > 150 and g < 100 and b < 100:
            return "red"
        elif r < 100 and g < 100 and b > 150:
            return "blue"
        elif r < 100 and g > 150 and b < 100:
            return "green"
        elif r > 150 and g > 150 and b < 100:
            return "yellow"
        elif abs(r - g) < 30 and abs(g - b) < 30:
            if r > 150:
                return "silver"
            else:
                return "gray"
        else:
            return "unknown"

    def get_size_category(self, bbox: list, frame_shape: tuple) -> str:
        """
        Categorize vehicle size relative to frame.
        """
        frame_h, frame_w = frame_shape[:2]
        bbox_w = bbox[2] - bbox[0]
        bbox_h = bbox[3] - bbox[1]

        area_ratio = (bbox_w * bbox_h) / (frame_w * frame_h)

        if area_ratio > 0.15:
            return "large"  # Truck, SUV, close vehicle
        elif area_ratio > 0.05:
            return "medium"  # Sedan, standard car
        else:
            return "small"  # Compact, far vehicle

    def create_fingerprint(self, vehicle_crop: np.ndarray, bbox: list,
                          frame_shape: tuple) -> Dict:
        """
        Create complete vehicle fingerprint.
        """
        color_rgb = self.get_dominant_color(vehicle_crop)
        color_name = self.get_color_name(color_rgb)
        size = self.get_size_category(bbox, frame_shape)

        # Aspect ratio
        bbox_w = bbox[2] - bbox[0]
        bbox_h = bbox[3] - bbox[1]
        aspect_ratio = bbox_w / bbox_h if bbox_h > 0 else 0

        return {
            'color_rgb': color_rgb,
            'color_name': color_name,
            'size': size,
            'aspect_ratio': round(aspect_ratio, 2),
            'fingerprint_hash': self._compute_hash(color_rgb, size, aspect_ratio)
        }

    def _compute_hash(self, color: tuple, size: str, aspect: float) -> str:
        """Create a simple hash for quick matching."""
        return f"{color[0]//25}-{color[1]//25}-{color[2]//25}-{size[0]}-{int(aspect*10)}"

    def match_fingerprint(self, fp1: Dict, fp2: Dict, threshold: float = 0.7) -> float:
        """
        Compare two fingerprints and return similarity score.
        """
        score = 0.0

        # Color similarity (40%)
        c1 = np.array(fp1['color_rgb'])
        c2 = np.array(fp2['color_rgb'])
        color_dist = np.linalg.norm(c1 - c2)
        color_sim = max(0, 1 - color_dist / 441)  # 441 = max RGB distance
        score += 0.4 * color_sim

        # Size match (30%)
        if fp1['size'] == fp2['size']:
            score += 0.3

        # Aspect ratio similarity (30%)
        ar_diff = abs(fp1['aspect_ratio'] - fp2['aspect_ratio'])
        ar_sim = max(0, 1 - ar_diff)
        score += 0.3 * ar_sim

        return score
```

### Task 4: Vehicle Learning Database

**SQL Schema**: `/ganuda/sql/vehicle_learning.sql`

```sql
-- Known vehicles table
CREATE TABLE IF NOT EXISTS known_vehicles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),  -- "Darrell's Truck", "Erika's Car"
    plate VARCHAR(20),
    color VARCHAR(50),
    size VARCHAR(20),
    fingerprint_hash VARCHAR(50),
    fingerprint JSONB,
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW(),
    times_seen INTEGER DEFAULT 1,
    is_household BOOLEAN DEFAULT FALSE,
    notes TEXT
);

-- Vehicle sightings log
CREATE TABLE IF NOT EXISTS vehicle_sightings (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER REFERENCES known_vehicles(id),
    track_id INTEGER,
    plate_read VARCHAR(20),
    confidence FLOAT,
    fingerprint JSONB,
    frame_path VARCHAR(255),
    camera VARCHAR(50),
    seen_at TIMESTAMP DEFAULT NOW()
);

-- Unknown vehicle alerts
CREATE TABLE IF NOT EXISTS vehicle_alerts (
    id SERIAL PRIMARY KEY,
    fingerprint JSONB,
    plate_read VARCHAR(20),
    frame_path VARCHAR(255),
    alert_type VARCHAR(50),  -- 'unknown', 'repeated_unknown', 'suspicious'
    status VARCHAR(20) DEFAULT 'new',  -- 'new', 'reviewed', 'added_known', 'dismissed'
    created_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP,
    reviewed_by VARCHAR(100)
);

-- Index for quick fingerprint matching
CREATE INDEX IF NOT EXISTS idx_vehicles_fingerprint ON known_vehicles(fingerprint_hash);
CREATE INDEX IF NOT EXISTS idx_sightings_vehicle ON vehicle_sightings(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON vehicle_alerts(status);
```

### Task 5: SAG Dashboard Integration

**Add to SAG Interface** - Vision tab:

```
┌─────────────────────────────────────────────────────────────┐
│ Tribal Vision                                    [Refresh]  │
├─────────────────────────────────────────────────────────────┤
│ Office PII (181)        │ Traffic (182)                    │
│ ┌─────────────────────┐ │ ┌─────────────────────┐          │
│ │                     │ │ │                     │          │
│ │   [Live Feed]       │ │ │   [Live Feed]       │          │
│ │   Last: 15s ago     │ │ │   Last: 15s ago     │          │
│ │                     │ │ │                     │          │
│ └─────────────────────┘ │ └─────────────────────┘          │
│ Detected: 1 person      │ Detected: 2 vehicles             │
│ Face: Darrell (87%)     │ Plates: ABC123, ???              │
├─────────────────────────────────────────────────────────────┤
│ Recent Alerts                                               │
│ ─────────────────────────────────────────────────────────── │
│ ⚠️ Unknown vehicle - Silver sedan, no plate read  [Review] │
│ ✓ Known: Darrell's Truck arrived                   2m ago  │
│ ⚠️ Person in PII area                              5m ago  │
├─────────────────────────────────────────────────────────────┤
│ Known Vehicles                           [Add New]          │
│ ─────────────────────────────────────────────────────────── │
│ 🚗 Darrell's Truck  | White | ABC-1234 | Last: Today       │
│ 🚗 Erika's Car      | Blue  | XYZ-5678 | Last: Yesterday   │
│ 🚗 Joe's Vehicle    | Gray  | ???      | Last: 3 days ago  │
└─────────────────────────────────────────────────────────────┘
```

**API Endpoints**:

```python
@app.route('/api/vision/cameras')
def get_cameras():
    """Get camera status and latest frames"""

@app.route('/api/vision/latest/<camera>')
def get_latest_frame(camera):
    """Get latest annotated frame for a camera"""

@app.route('/api/vision/alerts')
def get_alerts():
    """Get recent vehicle/person alerts"""

@app.route('/api/vision/vehicles')
def get_known_vehicles():
    """Get known vehicles database"""

@app.route('/api/vision/vehicles', methods=['POST'])
def add_known_vehicle():
    """Add vehicle to known database"""

@app.route('/api/vision/alerts/<id>/review', methods=['POST'])
def review_alert(id):
    """Mark alert as reviewed, add to known, or dismiss"""
```

### Task 6: Integration with tribal_vision.py

**Modify**: `/ganuda/services/vision/tribal_vision.py`

Add to the main processing loop:

```python
from vehicle_tracker import VehicleTracker
from plate_reader import PlateReader
from vehicle_fingerprint import VehicleFingerprint

class TribalVision:
    def __init__(self, ...):
        # ... existing init ...
        self.vehicle_tracker = VehicleTracker()
        self.plate_reader = PlateReader()
        self.fingerprinter = VehicleFingerprint()

    def process_traffic_frame(self, frame):
        """Enhanced traffic processing with tracking and identification."""
        # YOLOv8 detection
        results = self.model(frame)
        vehicle_detections = self._extract_vehicles(results)

        # Track vehicles across frames
        tracked = self.vehicle_tracker.update(vehicle_detections, frame)

        for track in tracked:
            bbox = track['bbox']
            vehicle_crop = frame[int(bbox[1]):int(bbox[3]), int(bbox[0]):int(bbox[2])]

            # Try plate recognition
            plate_result = self.plate_reader.process_vehicle(vehicle_crop)

            # Create fingerprint
            fingerprint = self.fingerprinter.create_fingerprint(
                vehicle_crop, bbox, frame.shape
            )

            # Check against known vehicles
            is_known = self._check_known_vehicle(plate_result, fingerprint)

            if not is_known:
                self._create_unknown_alert(track, plate_result, fingerprint, frame)
            else:
                self._log_sighting(is_known, track, plate_result)

    def _check_known_vehicle(self, plate_result, fingerprint):
        """Check if vehicle matches known database."""
        # First try plate match
        if plate_result and plate_result['plate']:
            # Query database for plate
            pass

        # Then try fingerprint match
        # Query and compare fingerprints
        pass

    def _create_unknown_alert(self, track, plate, fingerprint, frame):
        """Create alert for unknown vehicle."""
        # Save frame
        # Insert into vehicle_alerts table
        # Optionally notify via Telegram
        pass
```

## Files to Create/Modify

| File | Action |
|------|--------|
| `/ganuda/services/vision/vehicle_tracker.py` | Create |
| `/ganuda/services/vision/plate_reader.py` | Create |
| `/ganuda/services/vision/vehicle_fingerprint.py` | Create |
| `/ganuda/services/vision/tribal_vision.py` | Modify |
| `/ganuda/sql/vehicle_learning.sql` | Create |
| `/ganuda/home/dereadi/sag_unified_interface/templates/vision_tab.html` | Create |
| `/ganuda/home/dereadi/sag_unified_interface/app.py` | Modify |

## Dependencies

```bash
# System packages
sudo apt-get install tesseract-ocr tesseract-ocr-eng

# Python packages
pip install deep-sort-realtime filterpy pytesseract scikit-image scikit-learn
```

## Reference Repositories (MIT License)

| Repo | Use For | Link |
|------|---------|------|
| Roee-BY/ipcams_and_webcams_licence_plate_reader | Plate OCR approach | [GitHub](https://github.com/Roee-BY/ipcams_and_webcams_licence_plate_reader) |
| TDiblik/main-gate-alpr | Multi-round filtering | [GitHub](https://github.com/TDiblik/main-gate-alpr) |
| JoachimVeulemans/license-plate-reader | Simple RTSP integration | [GitHub](https://github.com/JoachimVeulemans/license-plate-reader) |

## Testing

### Test 1: Vehicle Tracking
```python
from vehicle_tracker import VehicleTracker
tracker = VehicleTracker()
# Process multiple frames, verify consistent track IDs
```

### Test 2: Plate Reader
```bash
cd /ganuda/services/vision && python3 -c "
from plate_reader import PlateReader
import cv2
reader = PlateReader()
img = cv2.imread('/ganuda/data/vision/traffic_20260121_150347.jpg')
# Test on recent traffic frame
"
```

### Test 3: Fingerprinting
```python
from vehicle_fingerprint import VehicleFingerprint
fp = VehicleFingerprint()
# Test color detection, size categorization
```

## Success Criteria

- [ ] DeepSORT tracks vehicles across consecutive frames
- [ ] License plates read with >70% accuracy on clear images
- [ ] Vehicle fingerprints match same vehicle across sessions
- [ ] Unknown vehicle alerts generated and stored
- [ ] SAG dashboard shows live camera feeds
- [ ] Known vehicles can be added via UI
- [ ] Alerts can be reviewed and dismissed

---

*Cherokee AI Federation - For Seven Generations*
*"Eagle Eye sees all who approach."*

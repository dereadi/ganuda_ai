# Jr Instruction: Speed Detector + Plate Reader Fusion

**Task ID:** SPEED-PLATE-001
**Priority:** P2
**Assigned To:** Software Engineer Jr.
**Kanban:** #1736
**Date:** February 9, 2026

## Background

The speed detector (`/ganuda/services/vision/speed_detector.py`) is running on the garage camera, tracking vehicles with YOLO and calculating speeds. We need to also read license plates when vehicles are detected, logging speed + plate together.

Existing plate reader: `/ganuda/lib/paddle_plate_reader.py` — `PaddlePlateReader.read_plate(image) -> (plate_text, confidence)`

## Edit 1: Add plate_text and vehicle_type columns to speed detections table

This is a SQL migration. Run on bluefin (192.168.132.222):

```sql
ALTER TABLE stereo_speed_detections ADD COLUMN IF NOT EXISTS plate_text VARCHAR(20);
ALTER TABLE stereo_speed_detections ADD COLUMN IF NOT EXISTS plate_confidence DECIMAL(3,2);
ALTER TABLE stereo_speed_detections ADD COLUMN IF NOT EXISTS vehicle_type VARCHAR(20);
CREATE INDEX IF NOT EXISTS idx_speed_plate ON stereo_speed_detections(plate_text);
```

## Edit 2: Add plate reader import to speed_detector.py

File: `/ganuda/services/vision/speed_detector.py`

<<<<<<< SEARCH
from lib.amcrest_camera import AmcrestCamera
from lib.secrets_loader import get_db_config

# Ultralytics
from ultralytics import YOLO
=======
from lib.amcrest_camera import AmcrestCamera
from lib.secrets_loader import get_db_config

# Plate reader
try:
    from lib.paddle_plate_reader import PaddlePlateReader
    PLATE_READER_AVAILABLE = True
except ImportError:
    PLATE_READER_AVAILABLE = False

# Ultralytics
from ultralytics import YOLO
>>>>>>> REPLACE

## Edit 3: Initialize plate reader in SpeedDetector.__init__

File: `/ganuda/services/vision/speed_detector.py`

<<<<<<< SEARCH
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)
        logger.info(
            f"SpeedDetector initialized: camera={CAMERA_ID}, "
            f"ppm={PIXELS_PER_METER}, alert_threshold={SPEED_ALERT_MPH}mph"
        )
=======
        # Plate reader (optional — degrades gracefully if PaddleOCR unavailable)
        self.plate_reader = None
        if PLATE_READER_AVAILABLE:
            try:
                self.plate_reader = PaddlePlateReader(use_gpu=True)
                logger.info("Plate reader initialized (PaddleOCR)")
            except Exception as e:
                logger.warning(f"Plate reader unavailable: {e}")
        self.plate_cache = {}  # track_id -> best (plate_text, confidence)

        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)
        logger.info(
            f"SpeedDetector initialized: camera={CAMERA_ID}, "
            f"ppm={PIXELS_PER_METER}, alert_threshold={SPEED_ALERT_MPH}mph, "
            f"plate_reader={'active' if self.plate_reader else 'disabled'}"
        )
>>>>>>> REPLACE

## Edit 4: Add plate reading method

File: `/ganuda/services/vision/speed_detector.py`

<<<<<<< SEARCH
    def _log_detection(self, track_id: int, speed_mph: float, bbox, confidence: float):
=======
    def _read_plate(self, frame, bbox, track_id: int) -> tuple:
        """Attempt to read license plate from vehicle bounding box."""
        if not self.plate_reader:
            return "", 0.0

        try:
            # Crop vehicle region from frame with padding
            x1, y1, x2, y2 = [int(v) for v in bbox]
            h, w = frame.shape[:2]
            # Focus on lower portion of vehicle bbox (where plates typically are)
            plate_y1 = y1 + int((y2 - y1) * 0.5)
            # Add horizontal padding
            pad_x = int((x2 - x1) * 0.1)
            crop_x1 = max(0, x1 - pad_x)
            crop_x2 = min(w, x2 + pad_x)
            crop_y1 = max(0, plate_y1)
            crop_y2 = min(h, y2)

            crop = frame[crop_y1:crop_y2, crop_x1:crop_x2]
            if crop.size == 0:
                return "", 0.0

            plate_text, conf = self.plate_reader.read_plate(crop)

            # Keep best reading per track
            if plate_text and conf > 0.5:
                cached = self.plate_cache.get(track_id, ("", 0.0))
                if conf > cached[1]:
                    self.plate_cache[track_id] = (plate_text, conf)
                    logger.info(f"Plate read: track {track_id} = {plate_text} ({conf:.0%})")
                return self.plate_cache.get(track_id, ("", 0.0))

        except Exception as e:
            logger.debug(f"Plate read error: {e}")

        return self.plate_cache.get(track_id, ("", 0.0))

    def _log_detection(self, track_id: int, speed_mph: float, bbox, confidence: float):
>>>>>>> REPLACE

## Edit 5: Update _log_detection to include plate data

File: `/ganuda/services/vision/speed_detector.py`

<<<<<<< SEARCH
    def _log_detection(self, track_id: int, speed_mph: float, bbox, confidence: float):
        """Log speed detection to database."""
        try:
            conn = self._get_db()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO stereo_speed_detections
                    (timestamp, track_id, speed_mph, position_x, position_y,
                     position_z, confidence, camera_pair)
                    VALUES (NOW(), %s, %s, %s, %s, 0, %s, %s)
                """,
                    (
                        track_id,
                        speed_mph,
                        float(bbox[0]),
                        float(bbox[1]),
                        confidence,
                        CAMERA_ID,
                    ),
                )
                conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"DB log error: {e}")
=======
    def _log_detection(self, track_id: int, speed_mph: float, bbox, confidence: float,
                       plate_text: str = "", plate_confidence: float = 0.0,
                       vehicle_type: str = ""):
        """Log speed detection to database with optional plate data."""
        try:
            conn = self._get_db()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO stereo_speed_detections
                    (timestamp, track_id, speed_mph, position_x, position_y,
                     position_z, confidence, camera_pair,
                     plate_text, plate_confidence, vehicle_type)
                    VALUES (NOW(), %s, %s, %s, %s, 0, %s, %s, %s, %s, %s)
                """,
                    (
                        track_id,
                        speed_mph,
                        float(bbox[0]),
                        float(bbox[1]),
                        confidence,
                        CAMERA_ID,
                        plate_text or None,
                        plate_confidence if plate_confidence > 0 else None,
                        vehicle_type or None,
                    ),
                )
                conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"DB log error: {e}")
>>>>>>> REPLACE

## Edit 6: Wire plate reading into the detection loop

File: `/ganuda/services/vision/speed_detector.py`

<<<<<<< SEARCH
                    # Calculate speed
                    speed = self._calculate_speed(track_id)
                    if speed > 2.0:  # Ignore noise below 2 mph
                        self.speeds[track_id] = speed
                        self._log_detection(track_id, speed, bbox, conf)

                        if speed > SPEED_ALERT_MPH:
                            self._log_alert(track_id, speed)
=======
                    # Calculate speed
                    speed = self._calculate_speed(track_id)
                    if speed > 2.0:  # Ignore noise below 2 mph
                        self.speeds[track_id] = speed

                        # Read plate (every 5th detection per track to save CPU)
                        plate_text, plate_conf = "", 0.0
                        positions = self.tracks.get(track_id, [])
                        if len(positions) % 5 == 0:
                            plate_text, plate_conf = self._read_plate(frame, bbox, track_id)
                        else:
                            cached = self.plate_cache.get(track_id, ("", 0.0))
                            plate_text, plate_conf = cached

                        # Get vehicle type from YOLO class
                        cls_id = int(boxes.cls[i])
                        vehicle_type = self.model.names.get(cls_id, "vehicle")

                        self._log_detection(
                            track_id, speed, bbox, conf,
                            plate_text=plate_text,
                            plate_confidence=plate_conf,
                            vehicle_type=vehicle_type
                        )

                        if speed > SPEED_ALERT_MPH:
                            self._log_alert(track_id, speed)
>>>>>>> REPLACE

## Edit 7: Clean up plate cache on track pruning

File: `/ganuda/services/vision/speed_detector.py`

<<<<<<< SEARCH
            for tid in stale:
                del self.tracks[tid]
                self.speeds.pop(tid, None)
=======
            for tid in stale:
                del self.tracks[tid]
                self.speeds.pop(tid, None)
                self.plate_cache.pop(tid, None)
>>>>>>> REPLACE

## Do NOT

- Do not modify paddle_plate_reader.py
- Do not change the camera configuration
- Do not modify the YOLO model or tracking parameters
- Do not add new dependencies (PaddleOCR is already installed)
- Do not remove any existing functionality

## Success Criteria

1. SQL migration adds plate_text, plate_confidence, vehicle_type columns
2. Speed detector imports PaddlePlateReader gracefully (no crash if unavailable)
3. Plate reader initialized on startup (logged in journal)
4. When vehicle tracked with speed > 2mph, plate reading attempted
5. Plate data logged alongside speed in stereo_speed_detections
6. Plate cache keeps best reading per track_id
7. Track pruning also cleans plate cache
8. Python syntax valid after all edits
9. No performance regression (plate read only every 5th detection)

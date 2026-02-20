#!/usr/bin/env python3
"""
Speed Detection Service — Cherokee AI Federation

Uses YOLO object detection + tracking on the garage camera
to estimate vehicle speeds on the cul-de-sac.

Processing: Sub-stream (704x480) for real-time performance.
Detection: YOLOv8 with ByteTrack tracking.
Speed: Pixel displacement over time with perspective calibration.

For Seven Generations — Eyes that measure
"""

import os
import sys
import time
import json
import signal
import logging
import psycopg2
from datetime import datetime
from pathlib import Path

# Ensure imports work
sys.path.insert(0, "/ganuda")
sys.path.insert(0, "/ganuda/lib")

from lib.amcrest_camera import AmcrestCamera
from lib.secrets_loader import get_db_config
from lib.camera_calibration import CameraCalibrator

# Plate reader
try:
    from lib.paddle_plate_reader import PaddlePlateReader
    PLATE_READER_AVAILABLE = True
except ImportError:
    PLATE_READER_AVAILABLE = False

# Ultralytics
from ultralytics import YOLO

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("speed_detector")

# Configuration
CAMERA_ID = os.environ.get("SPEED_CAMERA", "garage")
YOLO_MODEL = "/ganuda/services/vision/yolov8n.pt"
VEHICLE_CLASSES = [2, 3, 5, 7]  # car, motorcycle, bus, truck
SPEED_ALERT_MPH = 25  # residential zone threshold
DETECTION_INTERVAL = 0.1  # seconds between frame processing (10 fps effective)

# Perspective calibration: pixels per meter at road distance
# This must be calibrated after camera installation.
# Approximate for garage cam: road is ~15m away, field of view ~20m wide at 704px
# So ~35 pixels per meter. Adjust after measuring known distances.
PIXELS_PER_METER = float(os.environ.get("SPEED_PPM", "35.0"))
MAX_SPEED_MPH = float(os.environ.get("MAX_SPEED_MPH", "120.0"))  # Reject tracking artifacts above this
FPS_EFFECTIVE = float(os.environ.get("SPEED_FPS", "10.0"))


class SpeedDetector:
    """Monocular speed detection using YOLO tracking."""

    def __init__(self):
        self.camera = AmcrestCamera(CAMERA_ID, stream="sub")
        self.model = YOLO(YOLO_MODEL)
        self.db_config = get_db_config()
        self.calibrator = CameraCalibrator(CAMERA_ID)
        self.running = True
        self.tracks = {}  # track_id -> list of (x_center, y_center, timestamp)
        self.speeds = {}  # track_id -> latest speed in mph
        self.alert_count = 0

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

    def _shutdown(self, signum, frame):
        logger.info("Shutting down speed detector...")
        self.running = False

    def _get_db(self):
        return psycopg2.connect(**self.db_config)

    def _calculate_speed(self, track_id: int) -> float:
        """Calculate speed in mph from tracked positions using calibrated ground distance."""
        positions = self.tracks.get(track_id, [])
        if len(positions) < 3:
            return 0.0

        recent = positions[-5:]
        if len(recent) < 2:
            return 0.0

        dt = recent[-1][2] - recent[0][2]
        if dt < 0.1:
            return 0.0

        # Try calibrated ground distance first
        if self.calibrator.K is not None:
            total_m = 0.0
            for i in range(1, len(recent)):
                d = self.calibrator.ground_distance(
                    (recent[i-1][0], recent[i-1][1]),
                    (recent[i][0], recent[i][1])
                )
                if d is not None:
                    total_m += d
                else:
                    # Fallback to flat PPM for this segment
                    dx = recent[i][0] - recent[i-1][0]
                    dy = recent[i][1] - recent[i-1][1]
                    total_m += (dx**2 + dy**2)**0.5 / PIXELS_PER_METER

            meters_per_sec = total_m / dt
        else:
            # No calibration — use flat PPM (original behavior)
            total_px = 0.0
            for i in range(1, len(recent)):
                dx = recent[i][0] - recent[i-1][0]
                dy = recent[i][1] - recent[i-1][1]
                total_px += (dx**2 + dy**2)**0.5
            meters_per_sec = (total_px / dt) / PIXELS_PER_METER

        mph = meters_per_sec * 2.237
        if mph > MAX_SPEED_MPH:
            logger.warning(f"Track {track_id}: rejected artifact {mph:.1f} mph (>{MAX_SPEED_MPH})")
            return 0.0
        return round(mph, 1)

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

    def _log_alert(self, track_id: int, speed_mph: float):
        """Log speed alert to thermal memory."""
        try:
            conn = self._get_db()
            with conn.cursor() as cur:
                import hashlib

                cur.execute(
                    """
                    INSERT INTO thermal_memory_archive
                    (memory_type, original_content, temperature_score, memory_hash, tags)
                    VALUES ('alert', %s, 0.8, %s, %s)
                    ON CONFLICT (memory_hash) DO NOTHING
                """,
                    (
                        f"SPEED ALERT: Vehicle track {track_id} detected at {speed_mph} mph "
                        f"on {CAMERA_ID} camera (threshold: {SPEED_ALERT_MPH} mph). "
                        f"Timestamp: {datetime.now().isoformat()}",
                        hashlib.md5(
                            f"speed-alert-{track_id}-{datetime.now().strftime('%Y%m%d%H')}".encode()
                        ).hexdigest(),
                        ["speed_alert", "eagle_eye", CAMERA_ID],
                    ),
                )
                conn.commit()
            conn.close()
            self.alert_count += 1
            logger.warning(
                f"SPEED ALERT: Track {track_id} at {speed_mph} mph "
                f"(total alerts: {self.alert_count})"
            )
        except Exception as e:
            logger.error(f"Alert log error: {e}")

    def run(self):
        """Main detection loop."""
        logger.info(f"Starting speed detection on {CAMERA_ID} camera...")
        frame_count = 0
        last_stats = time.time()

        for frame, timestamp in self.camera.stream_frames():
            if not self.running:
                break

            # Throttle to effective FPS
            time.sleep(DETECTION_INTERVAL)

            # Undistort frame before detection (corrects barrel distortion)
            frame = self.calibrator.undistort(frame)

            # Run YOLO with tracking
            results = self.model.track(
                frame,
                persist=True,
                tracker="bytetrack.yaml",
                classes=VEHICLE_CLASSES,
                verbose=False,
            )

            if results and results[0].boxes is not None and results[0].boxes.id is not None:
                boxes = results[0].boxes
                for i, track_id in enumerate(boxes.id.int().tolist()):
                    bbox = boxes.xyxy[i].tolist()
                    conf = float(boxes.conf[i])
                    x_center = (bbox[0] + bbox[2]) / 2
                    y_center = (bbox[1] + bbox[3]) / 2

                    # Update track history
                    if track_id not in self.tracks:
                        self.tracks[track_id] = []
                    self.tracks[track_id].append((x_center, y_center, timestamp))

                    # Keep last 30 positions
                    if len(self.tracks[track_id]) > 30:
                        self.tracks[track_id] = self.tracks[track_id][-30:]

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

            frame_count += 1

            # Stats every 60 seconds
            if time.time() - last_stats > 60:
                active = len(
                    [
                        t
                        for t in self.tracks.values()
                        if t and timestamp - t[-1][2] < 5
                    ]
                )
                logger.info(
                    f"Stats: {frame_count} frames, "
                    f"{active} active tracks, "
                    f"{self.alert_count} alerts"
                )
                last_stats = time.time()

            # Prune old tracks (>30s stale)
            stale = [
                tid
                for tid, positions in self.tracks.items()
                if positions and timestamp - positions[-1][2] > 30
            ]
            for tid in stale:
                del self.tracks[tid]
                self.speeds.pop(tid, None)
                self.plate_cache.pop(tid, None)

        self.camera.release()
        logger.info("Speed detector stopped.")


if __name__ == "__main__":
    detector = SpeedDetector()
    detector.run()

#!/usr/bin/env python3
"""
Tribal Vision - Cherokee AI Federation Camera Intelligence

Monitors IP cameras for:
1. Office PII Security - Detects people entering PII area (Crawdad domain)
2. Traffic Analysis - Identifies and learns vehicles (Eagle Eye domain)

Uses YOLOv8 for object detection, with vehicle tracking over time.

For Seven Generations - Cherokee AI Federation
"""

import os
import sys
import cv2
import json
import time
import logging
import argparse
import psycopg2
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
from collections import defaultdict

# Ultralytics YOLOv8
from ultralytics import YOLO

# Face recognition
import torch
import numpy as np
try:
    from facenet_pytorch import MTCNN, InceptionResnetV1
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False

# Configuration
DB_CONFIG = {
    'host': os.environ.get('CHEROKEE_DB_HOST', '192.168.132.222'),
    'database': os.environ.get('CHEROKEE_DB_NAME', 'zammad_production'),
    'user': os.environ.get('CHEROKEE_DB_USER', 'claude'),
    'password': os.environ.get('CHEROKEE_DB_PASS', '')
}

def get_cam_password(cam_key=None):
    """Get camera password from per-camera env vars (rotated Feb 9, 2026)."""
    env_map = {
        'office_pii': 'CAMERA_OFFICE_PII_PASSWORD',
        'traffic': 'CAMERA_TRAFFIC_PASSWORD',
        'garage': 'CAMERA_GARAGE_PASSWORD',
    }
    if cam_key and cam_key in env_map:
        return os.environ.get(env_map[cam_key], '')
    return os.environ.get('CHEROKEE_DB_PASS', '')

CAMERAS = {
    'office_pii': {
        'name': 'Office PII Monitor',
        'ip': '192.168.132.181',
        'rtsp': f'rtsp://admin:{get_cam_password("office_pii")}@192.168.132.181:554/cam/realmonitor?channel=1&subtype=0',  # Main stream for face recognition
        'purpose': 'security',
        'alert_classes': ['person'],  # Alert on people entering PII area
        'specialist': 'crawdad'
    },
    'traffic': {
        'name': 'Traffic Monitor',
        'ip': '192.168.132.182',
        'rtsp': f'rtsp://admin:{get_cam_password("traffic")}@192.168.132.182:554/cam/realmonitor?channel=1&subtype=1',  # Sub-stream OK for vehicles
        'purpose': 'vehicle_identification',
        'track_classes': ['car', 'truck', 'bus', 'motorcycle'],
        'specialist': 'eagle_eye'
    }
}

# YOLOv8 class names for vehicles and people
VEHICLE_CLASSES = {2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'}
PERSON_CLASS = 0

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('tribal_vision')


class TribalVision:
    """Cherokee AI Federation Vision System"""

    def __init__(self, model_size: str = 'n'):
        """
        Initialize vision system.

        Args:
            model_size: YOLOv8 model size ('n', 's', 'm', 'l', 'x')
        """
        model_path = Path(__file__).parent / f'yolov8{model_size}.pt'
        self.model = YOLO(str(model_path))
        self.conn = None
        self.vehicle_tracker = defaultdict(list)  # Track vehicles over time
        self.output_dir = Path('/ganuda/data/vision')
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Face recognition
        self.known_faces = {}
        self.mtcnn = None
        self.facenet = None
        if FACE_RECOGNITION_AVAILABLE:
            self._init_face_recognition()

    def _init_face_recognition(self):
        """Initialize face recognition models and load known faces."""
        try:
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            # Lower thresholds for better detection at distance
            self.mtcnn = MTCNN(
                keep_all=True,
                device=device,
                thresholds=[0.5, 0.6, 0.6],  # More sensitive than default
                min_face_size=20
            )
            self.facenet = InceptionResnetV1(pretrained='vggface2').eval().to(device)
            self.device = device

            # Load known faces
            known_faces_dir = self.output_dir / 'known_faces'
            if known_faces_dir.exists():
                for f in known_faces_dir.glob('*.json'):
                    with open(f) as fp:
                        identity = json.load(fp)
                        self.known_faces[identity['name']] = np.array(identity['embedding'])
                        logger.info(f"Loaded face identity: {identity['name']}")

            logger.info(f"Face recognition initialized on {device}, {len(self.known_faces)} known faces")
        except Exception as e:
            logger.error(f"Failed to init face recognition: {e}")
            self.mtcnn = None
            self.facenet = None

    def identify_face(self, frame, bbox) -> str:
        """Identify a face in the given bounding box region."""
        if not self.mtcnn or not self.facenet or not self.known_faces:
            return "Unknown"

        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Detect faces in full frame
            faces, probs = self.mtcnn(rgb, return_prob=True)
            if faces is None or len(faces) == 0:
                logger.info("MTCNN: No faces detected in frame")
                return "Unknown"

            logger.info(f"MTCNN found {len(faces)} face(s)")

            # Find the face closest to the person bounding box center
            px1, py1, px2, py2 = [int(c) for c in bbox]
            person_center = ((px1 + px2) / 2, (py1 + py2) / 2)

            # Get face boxes from MTCNN
            face_boxes = self.mtcnn.detect(rgb)[0]
            if face_boxes is None:
                return "Unknown"

            best_face_idx = 0
            best_dist = float('inf')
            for i, fbox in enumerate(face_boxes):
                if fbox is None:
                    continue
                fx1, fy1, fx2, fy2 = fbox
                face_center = ((fx1 + fx2) / 2, (fy1 + fy2) / 2)
                dist = ((face_center[0] - person_center[0])**2 + (face_center[1] - person_center[1])**2)**0.5
                if dist < best_dist:
                    best_dist = dist
                    best_face_idx = i

            face_tensor = faces[best_face_idx].unsqueeze(0).to(self.device)
            with torch.no_grad():
                embedding = self.facenet(face_tensor).cpu().numpy()[0]

            # Compare to known faces (looser threshold)
            best_match = "Unknown"
            best_distance = 1.1  # More lenient threshold

            for name, known_emb in self.known_faces.items():
                distance = np.linalg.norm(embedding - known_emb)
                logger.info(f"Face distance to {name}: {distance:.3f}")
                if distance < best_distance:
                    best_distance = distance
                    best_match = name

            logger.info(f"Face identification result: {best_match}")
            return best_match
        except Exception as e:
            logger.warning(f"Face identification error: {e}")
            return "Unknown"

    def connect_db(self):
        """Connect to Cherokee database."""
        self.conn = psycopg2.connect(**DB_CONFIG)
        return self.conn

    def capture_frame(self, camera_id: str) -> Optional[tuple]:
        """
        Capture a single frame from camera.

        Returns:
            (frame, timestamp) or None on failure
        """
        camera = CAMERAS.get(camera_id)
        if not camera:
            logger.error(f"Unknown camera: {camera_id}")
            return None

        cap = cv2.VideoCapture(camera['rtsp'])
        if not cap.isOpened():
            logger.error(f"Failed to open {camera['name']} at {camera['rtsp']}")
            return None

        ret, frame = cap.read()
        cap.release()

        if not ret:
            logger.error(f"Failed to capture frame from {camera['name']}")
            return None

        return frame, datetime.now()

    def detect_objects(self, frame, camera_id: str) -> Dict:
        """
        Run YOLOv8 detection on frame.

        Returns:
            Detection results with objects, counts, and alerts
        """
        camera = CAMERAS[camera_id]
        results = self.model(frame, verbose=False)[0]

        detections = {
            'camera_id': camera_id,
            'camera_name': camera['name'],
            'timestamp': datetime.now().isoformat(),
            'objects': [],
            'counts': defaultdict(int),
            'alerts': []
        }

        for box in results.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            cls_name = results.names[cls_id]
            bbox = box.xyxy[0].tolist()

            obj = {
                'class': cls_name,
                'confidence': round(conf, 3),
                'bbox': [round(x, 1) for x in bbox]
            }
            detections['objects'].append(obj)
            detections['counts'][cls_name] += 1

            # Security alerts for office camera
            if camera['purpose'] == 'security' and cls_name in camera.get('alert_classes', []):
                # Try to identify the person
                identity = self.identify_face(frame, bbox)
                obj['identity'] = identity

                if identity == "Unknown":
                    alert = {
                        'type': 'SECURITY_ALERT',
                        'specialist': 'crawdad',
                        'message': f"UNKNOWN person detected in PII area!",
                        'confidence': conf,
                        'timestamp': detections['timestamp']
                    }
                    detections['alerts'].append(alert)
                    logger.warning(f"[CRAWDAD ALERT] UNKNOWN person in PII area (conf: {conf:.2f})")
                else:
                    logger.info(f"[CRAWDAD] {identity} detected in office (conf: {conf:.2f})")

            # Vehicle tracking for traffic camera
            if camera['purpose'] == 'vehicle_identification' and cls_name in camera.get('track_classes', []):
                self.track_vehicle(cls_name, conf, bbox)

        detections['counts'] = dict(detections['counts'])
        return detections

    def track_vehicle(self, vehicle_type: str, confidence: float, bbox: List[float]):
        """Track vehicles for identification learning."""
        # Simple tracking by position - more sophisticated tracking would use DeepSORT
        vehicle_id = f"{vehicle_type}_{int(bbox[0])}_{int(bbox[1])}"
        self.vehicle_tracker[vehicle_id].append({
            'type': vehicle_type,
            'confidence': confidence,
            'bbox': bbox,
            'timestamp': datetime.now().isoformat()
        })

    def save_detection(self, frame, detections: Dict, annotate: bool = True):
        """Save detection results and optionally annotated frame."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        camera_id = detections['camera_id']

        # Save annotated frame
        if annotate:
            for obj in detections['objects']:
                bbox = obj['bbox']
                # Show identity if known, otherwise class name
                if obj.get('identity') and obj['identity'] != 'Unknown':
                    label = f"{obj['identity']} {obj['confidence']:.2f}"
                    color = (0, 255, 0)  # Green for known
                elif obj['class'] == 'person':
                    label = f"UNKNOWN {obj['confidence']:.2f}"
                    color = (0, 0, 255)  # Red for unknown person
                else:
                    label = f"{obj['class']} {obj['confidence']:.2f}"
                    color = (255, 165, 0)  # Orange for objects
                cv2.rectangle(frame,
                             (int(bbox[0]), int(bbox[1])),
                             (int(bbox[2]), int(bbox[3])),
                             color, 2)
                cv2.putText(frame, label,
                           (int(bbox[0]), int(bbox[1])-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            frame_path = self.output_dir / f"{camera_id}_{timestamp}.jpg"
            cv2.imwrite(str(frame_path), frame)
            logger.info(f"Saved annotated frame: {frame_path}")

        # Log to database
        if self.conn:
            self.log_detection(detections)

        return detections

    def log_detection(self, detections: Dict):
        """Log detection to thermal memory."""
        content = f"VISION DETECTION [{detections['camera_name']}]: "
        content += f"Detected {len(detections['objects'])} objects. "
        content += f"Counts: {detections['counts']}. "
        if detections['alerts']:
            content += f"ALERTS: {len(detections['alerts'])} security alerts!"

        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO thermal_memory_archive (
                        memory_hash, original_content, current_stage,
                        temperature_score, metadata
                    ) VALUES (
                        md5(%s || NOW()::text),
                        %s,
                        %s,
                        %s,
                        %s
                    )
                """, (
                    content,
                    content,
                    'WHITE_HOT' if detections['alerts'] else 'COOL',
                    85 if detections['alerts'] else 30,
                    json.dumps(detections)
                ))
                self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to log detection: {e}")

    def run_single_capture(self, camera_id: str) -> Dict:
        """Capture and analyze single frame."""
        result = self.capture_frame(camera_id)
        if not result:
            return {'error': f'Failed to capture from {camera_id}'}

        frame, timestamp = result
        detections = self.detect_objects(frame, camera_id)
        return self.save_detection(frame, detections)

    def run_continuous(self, camera_id: str, interval: int = 30):
        """Run continuous monitoring."""
        cameras = ['office_pii', 'traffic'] if camera_id == 'both' else [camera_id]
        logger.info(f"Starting continuous monitoring of {cameras} (interval: {interval}s)")
        self.connect_db()

        while True:
            for cam in cameras:
                try:
                    self.run_single_capture(cam)
                except Exception as e:
                    logger.error(f"Capture error on {cam}: {e}")
            time.sleep(interval)

    def get_vehicle_stats(self) -> Dict:
        """Get vehicle tracking statistics."""
        stats = {
            'total_tracked': len(self.vehicle_tracker),
            'by_type': defaultdict(int),
            'recent': []
        }
        for vid, sightings in self.vehicle_tracker.items():
            vtype = sightings[0]['type']
            stats['by_type'][vtype] += 1
            if len(stats['recent']) < 10:
                stats['recent'].append({
                    'id': vid,
                    'type': vtype,
                    'sightings': len(sightings),
                    'last_seen': sightings[-1]['timestamp']
                })
        stats['by_type'] = dict(stats['by_type'])
        return stats


def main():
    parser = argparse.ArgumentParser(description='Tribal Vision - Cherokee AI Camera Intelligence')
    parser.add_argument('--camera', choices=['office_pii', 'traffic', 'both'], default='both',
                       help='Camera to monitor')
    parser.add_argument('--once', action='store_true', help='Single capture and exit')
    parser.add_argument('--interval', type=int, default=30, help='Seconds between captures')
    parser.add_argument('--model', choices=['n', 's', 'm', 'l', 'x'], default='n',
                       help='YOLOv8 model size')
    args = parser.parse_args()

    vision = TribalVision(model_size=args.model)

    if args.once:
        cameras = ['office_pii', 'traffic'] if args.camera == 'both' else [args.camera]
        for cam in cameras:
            print(f"\n=== Capturing from {CAMERAS[cam]['name']} ===")
            result = vision.run_single_capture(cam)
            print(json.dumps(result, indent=2, default=str))
    else:
        vision.run_continuous(args.camera, args.interval)


if __name__ == '__main__':
    main()

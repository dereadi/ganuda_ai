"""
Enhanced Vision Processor - Unified AI camera processing
Cherokee AI Federation - Tribal Vision System

Integrates:
- InsightFace (SCRFD + ArcFace) for face detection/recognition
- ByteTrack for multi-object tracking
- PaddleOCR for license plate recognition
- LiteIE-inspired low-light enhancement
- Passive liveness detection for anti-spoofing
"""

import cv2
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EnhancedVisionProcessor:
    """Unified camera processor with AI-enhanced detection capabilities"""

    def __init__(self, camera_name: str, config: Optional[Dict] = None):
        self.camera_name = camera_name
        self.config = config or {}
        self.face_detector = None
        self.liveness_detector = None
        self.plate_reader = None
        self.tracker = None
        self.enhancer = None
        self._init_modules()

    def _init_modules(self):
        """Initialize enabled modules with graceful fallbacks"""
        # Low-light enhancement
        try:
            from lowlight_enhancer import LowLightEnhancer
            self.enhancer = LowLightEnhancer(method="adaptive")
            logger.info("LowLightEnhancer loaded")
        except Exception as e:
            logger.warning(f"LowLightEnhancer not available: {e}")

        # Face detection - try InsightFace first, fallback to face_recognition
        try:
            from insightface_detector import InsightFaceDetector
            self.face_detector = InsightFaceDetector()
            logger.info("InsightFaceDetector loaded (SCRFD + ArcFace)")
        except Exception as e:
            logger.warning(f"InsightFaceDetector not available: {e}")
            try:
                from face_recognition_module import FaceRecognizer
                self.face_detector = FaceRecognizer()
                logger.info("Fallback FaceRecognizer loaded")
            except Exception as e2:
                logger.warning(f"No face detector available: {e2}")

        # Face liveness detection
        try:
            from face_liveness import FaceLivenessDetector
            self.liveness_detector = FaceLivenessDetector()
            logger.info("FaceLivenessDetector loaded")
        except Exception as e:
            logger.warning(f"FaceLivenessDetector not available: {e}")

        # License plate reading - try PaddleOCR first, fallback to Tesseract
        try:
            from paddle_plate_reader import PaddlePlateReader
            self.plate_reader = PaddlePlateReader()
            logger.info("PaddlePlateReader loaded (PaddleOCR v3)")
        except Exception as e:
            logger.warning(f"PaddlePlateReader not available: {e}")
            try:
                from plate_reader import PlateReader
                self.plate_reader = PlateReader()
                logger.info("Fallback PlateReader loaded (Tesseract)")
            except Exception as e2:
                logger.warning(f"No plate reader available: {e2}")

        # Object tracking - try ByteTrack first, fallback to centroid
        try:
            from bytetrack_tracker import ByteTracker
            self.tracker = ByteTracker()
            logger.info("ByteTracker loaded")
        except Exception as e:
            logger.warning(f"ByteTracker not available: {e}")
            try:
                from vehicle_tracker import VehicleTracker
                self.tracker = VehicleTracker()
                logger.info("Fallback VehicleTracker loaded")
            except Exception as e2:
                logger.warning(f"No tracker available: {e2}")

    def process_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """Process frame through all enabled modules"""
        results = {
            "camera": self.camera_name,
            "timestamp": datetime.now().isoformat(),
            "enhanced": False,
            "faces": [],
            "plates": [],
            "tracks": [],
            "modules_used": []
        }

        # Step 1: Low-light enhancement if needed
        if self.enhancer:
            frame, was_enhanced = self.enhancer.auto_enhance(frame)
            results["enhanced"] = was_enhanced
            if was_enhanced:
                results["modules_used"].append("lowlight_enhancer")

        # Step 2: Face detection and recognition
        if self.face_detector:
            try:
                faces = self.face_detector.detect_faces(frame)

                # Step 2b: Liveness check for each face
                if self.liveness_detector and faces:
                    for face in faces:
                        bbox = face.get("bbox", [])
                        if len(bbox) >= 4:
                            x1, y1, x2, y2 = [int(v) for v in bbox[:4]]
                            face_crop = frame[max(0,y1):y2, max(0,x1):x2]
                            if face_crop.size > 0:
                                liveness = self.liveness_detector.check_liveness(face_crop)
                                face["liveness"] = liveness

                results["faces"] = faces
                results["modules_used"].append("face_detector")
                if self.liveness_detector:
                    results["modules_used"].append("liveness_detector")
            except Exception as e:
                logger.error(f"Face detection error: {e}")

        # Step 3: License plate reading
        if self.plate_reader:
            try:
                text, conf = self.plate_reader.read_plate(frame)
                if text and conf > 0.5:
                    results["plates"].append({
                        "text": text,
                        "confidence": conf
                    })
                    results["modules_used"].append("plate_reader")
            except Exception as e:
                logger.error(f"Plate reading error: {e}")

        # Step 4: Object tracking
        if self.tracker:
            try:
                # Create detections from faces for tracking
                detections = []
                for f in results["faces"]:
                    bbox = f.get("bbox", [])
                    if len(bbox) >= 4:
                        detections.append({
                            "bbox": bbox[:4],
                            "score": f.get("confidence", 0.5)
                        })

                if hasattr(self.tracker, 'update'):
                    tracks = self.tracker.update(detections)
                    if isinstance(tracks, dict):
                        results["tracks"] = [{"id": k, "centroid": list(v)} for k, v in tracks.items()]
                    else:
                        results["tracks"] = tracks
                    results["modules_used"].append("tracker")
            except Exception as e:
                logger.error(f"Tracking error: {e}")

        return results

    def get_module_status(self) -> Dict[str, bool]:
        """Return status of all modules"""
        return {
            "enhancer": self.enhancer is not None,
            "face_detector": self.face_detector is not None,
            "liveness_detector": self.liveness_detector is not None,
            "plate_reader": self.plate_reader is not None,
            "tracker": self.tracker is not None
        }


# Convenience function for quick testing
def create_processor(camera_name: str = "default") -> EnhancedVisionProcessor:
    """Create an enhanced vision processor with default settings"""
    return EnhancedVisionProcessor(camera_name)

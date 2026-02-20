import cv2
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime

class CameraProcessor:
    """
    A class to handle camera frames with optional features for plate reading, face recognition, and vehicle tracking.

    Attributes:
        camera_name (str): The name of the camera.
        enable_plates (bool): Whether to enable plate reading.
        enable_faces (bool): Whether to enable face recognition.
        enable_tracking (bool): Whether to enable vehicle tracking.
        plate_reader (Optional[PlateReader]): Instance of PlateReader if enabled.
        face_recognizer (Optional[FaceRecognizer]): Instance of FaceRecognizer if enabled.
        vehicle_tracker (Optional[VehicleTracker]): Instance of VehicleTracker if enabled.
    """

    def __init__(self, camera_name: str, enable_plates: bool = True, enable_faces: bool = True, enable_tracking: bool = True):
        self.camera_name = camera_name
        self.enable_plates = enable_plates
        self.enable_faces = enable_faces
        self.enable_tracking = enable_tracking
        self.plate_reader = None
        self.face_recognizer = None
        self.vehicle_tracker = None
        self._init_modules()

    def _init_modules(self):
        """Initialize the modules based on the enabled features."""
        if self.enable_plates:
            from plate_reader import PlateReader
            self.plate_reader = PlateReader()
        if self.enable_faces:
            from face_recognition_module import FaceRecognizer
            self.face_recognizer = FaceRecognizer()
        if self.enable_tracking:
            from vehicle_tracker import VehicleTracker
            self.vehicle_tracker = VehicleTracker()

    def process_frame(self, frame: np.ndarray) -> Dict:
        """
        Process a single frame from the camera.

        Args:
            frame (np.ndarray): The frame to process.

        Returns:
            Dict: A dictionary containing the results of the processing.
        """
        results = {
            "camera": self.camera_name,
            "timestamp": datetime.now().isoformat(),
            "plates": [],
            "faces": [],
            "vehicles": {}
        }
        if self.enable_faces and self.face_recognizer:
            results["faces"] = self.face_recognizer.detect_faces(frame)
        if self.enable_plates and self.plate_reader:
            plate_text, confidence = self.plate_reader.read_plate(frame)
            if plate_text and confidence > 0.6:
                results["plates"].append({"text": plate_text, "confidence": confidence})
        if self.enable_tracking and self.vehicle_tracker:
            rects = []  # Assuming rects should be populated with bounding boxes
            results["vehicles"] = self.vehicle_tracker.update(rects)
        return results
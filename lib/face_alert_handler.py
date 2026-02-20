import json
import os
import cv2
import numpy as np
import requests
from datetime import datetime
from typing import Dict, List, Optional

class FaceAlertHandler:
    """
    Class to handle face detections and send alerts for unknown faces.
    """
    def __init__(self, log_dir: str = "/ganuda/logs/face_detections", webhook_url: Optional[str] = None):
        """
        Initialize the FaceAlertHandler with a log directory and an optional webhook URL.
        
        :param log_dir: Directory to save logs and images of unknown faces.
        :param webhook_url: URL to send alerts via POST request.
        """
        self.log_dir = log_dir
        self.webhook_url = webhook_url
        os.makedirs(log_dir, exist_ok=True)
        self.detection_log: List[Dict] = []
    
    def handle_detection(self, frame: np.ndarray, detections: List[Dict], camera_name: str):
        """
        Handle face detections by logging them and sending alerts for unknown faces.
        
        :param frame: Image frame containing the detected faces.
        :param detections: List of dictionaries with detection details.
        :param camera_name: Name of the camera that captured the frame.
        """
        timestamp = datetime.now()
        for det in detections:
            entry = {"camera": camera_name, "name": det["name"], "bbox": det["bbox"], "timestamp": timestamp.isoformat()}
            self.detection_log.append(entry)
            if det["name"] == "Unknown":
                self._save_unknown_face(frame, det, camera_name, timestamp)
                self._send_alert(entry)
    
    def _save_unknown_face(self, frame: np.ndarray, detection: Dict, camera: str, ts: datetime):
        """
        Save an image of an unknown face.
        
        :param frame: Image frame containing the detected face.
        :param detection: Dictionary with detection details.
        :param camera: Name of the camera that captured the frame.
        :param ts: Timestamp of the detection.
        """
        left, top, right, bottom = detection["bbox"]
        face_img = frame[top:bottom, left:right]
        filename = f"{camera}_{ts.strftime('%Y%m%d_%H%M%S')}_unknown.jpg"
        cv2.imwrite(os.path.join(self.log_dir, filename), face_img)
    
    def _send_alert(self, detection: Dict):
        """
        Send an alert via webhook for an unknown face detection.
        
        :param detection: Dictionary with detection details.
        """
        if self.webhook_url:
            try:
                requests.post(self.webhook_url, json=detection, timeout=5)
            except Exception as e:
                print(f"Failed to send alert: {e}")
    
    def get_recent_detections(self, minutes: int = 60) -> List[Dict]:
        """
        Get recent face detections within a specified time frame.
        
        :param minutes: Number of minutes to look back for recent detections.
        :return: List of recent detection entries.
        """
        cutoff = datetime.now().timestamp() - (minutes * 60)
        return [d for d in self.detection_log if datetime.fromisoformat(d["timestamp"]).timestamp() > cutoff]
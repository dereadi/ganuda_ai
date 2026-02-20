import face_recognition
import numpy as np
import cv2
import os
from typing import List, Dict, Tuple, Optional
from datetime import datetime

class FaceRecognizer:
    """
    A class to handle face detection and recognition.
    
    Attributes:
    - known_faces_dir (str): Directory containing known faces.
    - known_encodings (List[np.ndarray]): Encodings of known faces.
    - known_names (List[str]): Names of known faces.
    """
    
    def __init__(self, known_faces_dir: str = "/ganuda/data/known_faces"):
        """
        Initializes the FaceRecognizer with a directory for known faces.
        
        Args:
        - known_faces_dir (str): Path to the directory containing known faces.
        """
        self.known_faces_dir = known_faces_dir
        self.known_encodings: List[np.ndarray] = []
        self.known_names: List[str] = []
        self.load_known_faces()
    
    def load_known_faces(self):
        """
        Loads known faces from the specified directory.
        """
        if not os.path.exists(self.known_faces_dir):
            os.makedirs(self.known_faces_dir)
            return
        for filename in os.listdir(self.known_faces_dir):
            if filename.endswith((".jpg", ".png")):
                path = os.path.join(self.known_faces_dir, filename)
                image = face_recognition.load_image_file(path)
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    self.known_encodings.append(encodings[0])
                    self.known_names.append(os.path.splitext(filename)[0])
    
    def detect_faces(self, frame: np.ndarray) -> List[Dict]:
        """
        Detects faces in a given frame and returns their bounding boxes and names.
        
        Args:
        - frame (np.ndarray): The frame to detect faces in.
        
        Returns:
        - List[Dict]: A list of dictionaries containing bounding box coordinates, name, and timestamp.
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb_frame, model="hog")
        encodings = face_recognition.face_encodings(rgb_frame, locations)
        results = []
        for (top, right, bottom, left), encoding in zip(locations, encodings):
            name = "Unknown"
            if self.known_encodings:
                matches = face_recognition.compare_faces(self.known_encodings, encoding, tolerance=0.6)
                if True in matches:
                    name = self.known_names[matches.index(True)]
            results.append({"bbox": (left, top, right, bottom), "name": name, "timestamp": datetime.now().isoformat()})
        return results
    
    def add_known_face(self, image: np.ndarray, name: str) -> bool:
        """
        Adds a new known face to the system.
        
        Args:
        - image (np.ndarray): The image of the face to add.
        - name (str): The name of the person in the image.
        
        Returns:
        - bool: True if the face was successfully added, False otherwise.
        """
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb)
        if encodings:
            self.known_encodings.append(encodings[0])
            self.known_names.append(name)
            path = os.path.join(self.known_faces_dir, f"{name}.jpg")
            cv2.imwrite(path, image)
            return True
        return False
import numpy as np
import cv2
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import os

try:
    from insightface.app import FaceAnalysis
    INSIGHTFACE_AVAILABLE = True
except ImportError:
    INSIGHTFACE_AVAILABLE = False

class InsightFaceDetector:
    """High-performance face detection using InsightFace SCRFD + ArcFace"""
    
    def __init__(self, model_name: str = "buffalo_l", ctx_id: int = 0, det_thresh: float = 0.5):
        self.model_name = model_name
        self.ctx_id = ctx_id
        self.det_thresh = det_thresh
        self.app = None
        self.known_embeddings: List[np.ndarray] = []
        self.known_names: List[str] = []
        self._init_model()
    
    def _init_model(self):
        if not INSIGHTFACE_AVAILABLE:
            raise ImportError("insightface not installed. Run: pip install insightface onnxruntime-gpu")
        self.app = FaceAnalysis(name=self.model_name, providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
        self.app.prepare(ctx_id=self.ctx_id, det_thresh=self.det_thresh)
    
    def detect_faces(self, frame: np.ndarray) -> List[Dict]:
        """Detect faces and return bboxes with embeddings"""
        faces = self.app.get(frame)
        results = []
        for face in faces:
            bbox = face.bbox.astype(int).tolist()
            embedding = face.embedding
            name = self._match_face(embedding) if embedding is not None else "Unknown"
            results.append({"bbox": bbox, "name": name, "confidence": float(face.det_score), "embedding": embedding, "timestamp": datetime.now().isoformat()})
        return results
    
    def _match_face(self, embedding: np.ndarray, threshold: float = 0.4) -> str:
        if not self.known_embeddings:
            return "Unknown"
        # Calculate cosine similarity between the embedding and known embeddings
        sims = [np.dot(embedding, known) / (np.linalg.norm(embedding) * np.linalg.norm(known)) for known in self.known_embeddings]
        max_idx = np.argmax(sims)
        return self.known_names[max_idx] if sims[max_idx] > threshold else "Unknown"
    
    def register_face(self, frame: np.ndarray, name: str) -> bool:
        """Register a new face from the given frame with the specified name"""
        faces = self.app.get(frame)
        if faces and faces[0].embedding is not None:
            self.known_embeddings.append(faces[0].embedding)
            self.known_names.append(name)
            return True
        return False
"""
Face Liveness Detector - Anti-spoofing for face recognition
Cherokee AI Federation - Tribal Vision System
"""

import cv2
import numpy as np
from typing import Dict, Tuple, Optional, List


class FaceLivenessDetector:
    """Passive face liveness detection to prevent spoofing attacks"""

    def __init__(self, texture_threshold: float = 0.3, frequency_threshold: float = 0.4):
        self.texture_threshold = texture_threshold
        self.frequency_threshold = frequency_threshold

    def check_liveness(self, face_image: np.ndarray) -> Dict:
        """Run multiple liveness checks and return combined result"""
        texture_score = self._texture_analysis(face_image)
        frequency_score = self._frequency_analysis(face_image)
        color_score = self._color_analysis(face_image)
        edge_score = self._edge_density(face_image)

        # Weighted combination
        combined_score = (
            texture_score * 0.3 +
            frequency_score * 0.3 +
            color_score * 0.2 +
            edge_score * 0.2
        )

        is_live = combined_score > 0.5

        return {
            "is_live": is_live,
            "confidence": combined_score,
            "texture": texture_score,
            "frequency": frequency_score,
            "color": color_score,
            "edge": edge_score
        }

    def _texture_analysis(self, face: np.ndarray) -> float:
        """LBP-based texture analysis - real faces have more texture variation"""
        gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY) if len(face.shape) == 3 else face
        lbp = self._compute_lbp(gray)

        # Calculate histogram entropy
        hist, _ = np.histogram(lbp.ravel(), bins=256, range=(0, 256))
        hist = hist.astype(float) / (hist.sum() + 1e-6)
        entropy = -np.sum(hist * np.log2(hist + 1e-6))

        # Normalize to 0-1 range (max entropy for 256 bins is 8)
        normalized = min(1.0, entropy / 8.0)
        return normalized

    def _compute_lbp(self, gray: np.ndarray, radius: int = 1) -> np.ndarray:
        """Compute Local Binary Pattern"""
        rows, cols = gray.shape
        lbp = np.zeros_like(gray)

        for i in range(radius, rows - radius):
            for j in range(radius, cols - radius):
                center = gray[i, j]
                code = 0
                code |= (gray[i-1, j-1] >= center) << 7
                code |= (gray[i-1, j] >= center) << 6
                code |= (gray[i-1, j+1] >= center) << 5
                code |= (gray[i, j+1] >= center) << 4
                code |= (gray[i+1, j+1] >= center) << 3
                code |= (gray[i+1, j] >= center) << 2
                code |= (gray[i+1, j-1] >= center) << 1
                code |= (gray[i, j-1] >= center) << 0
                lbp[i, j] = code

        return lbp

    def _frequency_analysis(self, face: np.ndarray) -> float:
        """FFT analysis - screens have different frequency patterns"""
        gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY) if len(face.shape) == 3 else face
        gray = cv2.resize(gray, (128, 128))

        f_transform = np.fft.fft2(gray)
        f_shift = np.fft.fftshift(f_transform)
        magnitude = np.abs(f_shift)

        # Compare high vs low frequency components
        high_freq = magnitude[32:96, 32:96]
        low_freq = magnitude[:32, :32]

        ratio = np.mean(high_freq) / (np.mean(low_freq) + 1e-6)
        return min(1.0, ratio / 0.5)

    def _color_analysis(self, face: np.ndarray) -> float:
        """Color distribution analysis - printed/screen faces have different color stats"""
        if len(face.shape) != 3:
            return 0.5

        hsv = cv2.cvtColor(face, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)

        # Real faces have more color variation
        s_std = np.std(s)
        v_std = np.std(v)

        score = min(1.0, (s_std + v_std) / 100.0)
        return score

    def _edge_density(self, face: np.ndarray) -> float:
        """Edge density - real faces have natural edge patterns"""
        gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY) if len(face.shape) == 3 else face
        edges = cv2.Canny(gray, 50, 150)
        density = np.sum(edges > 0) / edges.size
        return min(1.0, density / 0.15)

import cv2
import numpy as np
from typing import Optional, Tuple

class LowLightEnhancer:
    """Low-light image enhancement for night-time camera feeds"""

    def __init__(self, method: str = "clahe", clip_limit: float = 3.0, gamma: float = 1.5):
        self.method = method
        self.clip_limit = clip_limit
        self.gamma = gamma
        self.clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))

    def enhance(self, frame: np.ndarray) -> np.ndarray:
        """Enhance low-light frame using selected method"""
        if self.method == "clahe":
            return self._enhance_clahe(frame)
        elif self.method == "gamma":
            return self._enhance_gamma(frame)
        elif self.method == "retinex":
            return self._enhance_retinex(frame)
        elif self.method == "adaptive":
            return self._enhance_adaptive(frame)
        return frame

    def _enhance_clahe(self, frame: np.ndarray) -> np.ndarray:
        """CLAHE enhancement on LAB color space"""
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l_enhanced = self.clahe.apply(l)
        enhanced_lab = cv2.merge([l_enhanced, a, b])
        return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

    def _enhance_gamma(self, frame: np.ndarray) -> np.ndarray:
        """Gamma correction for brightness adjustment"""
        inv_gamma = 1.0 / self.gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype(np.uint8)
        return cv2.LUT(frame, table)

    def _enhance_retinex(self, frame: np.ndarray) -> np.ndarray:
        """Single-scale Retinex enhancement"""
        frame_float = frame.astype(np.float32) + 1.0
        log_img = np.log(frame_float)
        gaussian = cv2.GaussianBlur(frame_float, (0, 0), 80)
        log_gaussian = np.log(gaussian + 1.0)
        retinex = log_img - log_gaussian
        retinex = (retinex - retinex.min()) / (retinex.max() - retinex.min() + 1e-6) * 255
        return retinex.astype(np.uint8)

    def _enhance_adaptive(self, frame: np.ndarray) -> np.ndarray:
        """Adaptive enhancement based on frame brightness"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        if mean_brightness < 50:
            enhanced = self._enhance_clahe(frame)
            enhanced = self._enhance_gamma(enhanced)
        elif mean_brightness < 100:
            enhanced = self._enhance_clahe(frame)
        else:
            enhanced = frame
        return enhanced

    def is_low_light(self, frame: np.ndarray, threshold: float = 80.0) -> bool:
        """Check if frame needs enhancement"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return np.mean(gray) < threshold

    def auto_enhance(self, frame: np.ndarray) -> Tuple[np.ndarray, bool]:
        """Automatically enhance if needed, return (frame, was_enhanced)"""
        if self.is_low_light(frame):
            return self._enhance_adaptive(frame), True
        return frame, False

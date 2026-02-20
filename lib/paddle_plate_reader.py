"""
PaddleOCR License Plate Reader - High-accuracy plate recognition
Cherokee AI Federation - Tribal Vision System
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import Counter
import re

try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False


class PaddlePlateReader:
    """High-accuracy license plate reader using PaddleOCR v3"""

    def __init__(self, use_gpu: bool = True, lang: str = "en"):
        if not PADDLE_AVAILABLE:
            raise ImportError("paddleocr not installed. Run: pip install paddlepaddle paddleocr")
        self.ocr = PaddleOCR(use_angle_cls=True, lang=lang, use_gpu=use_gpu, show_log=False)
        self.recent_reads: List[str] = []
        self.plate_pattern = re.compile(r"^[A-Z0-9]{5,8}$")

    def preprocess_plate(self, image: np.ndarray) -> np.ndarray:
        """Enhanced preprocessing with CLAHE and bilateral filtering"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        denoised = cv2.bilateralFilter(enhanced, 11, 17, 17)
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        kernel = np.ones((2, 2), np.uint8)
        morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        return cv2.cvtColor(morph, cv2.COLOR_GRAY2BGR)

    def read_plate(self, image: np.ndarray, preprocess: bool = True) -> Tuple[str, float]:
        """Read license plate text with confidence score"""
        if preprocess:
            image = self.preprocess_plate(image)

        result = self.ocr.ocr(image, cls=True)
        if not result or not result[0]:
            return "", 0.0

        texts = []
        for line in result[0]:
            text = line[1][0].upper()
            conf = line[1][1]
            clean = re.sub(r"[^A-Z0-9]", "", text)
            if len(clean) >= 4:
                texts.append((clean, conf))

        if not texts:
            return "", 0.0

        best_text, best_conf = max(texts, key=lambda x: x[1])

        # Multi-round consensus filtering
        self.recent_reads.append(best_text)
        if len(self.recent_reads) > 5:
            self.recent_reads.pop(0)

        if len(self.recent_reads) >= 3:
            counter = Counter(self.recent_reads)
            most_common, count = counter.most_common(1)[0]
            consensus_conf = count / len(self.recent_reads)
            if consensus_conf > 0.5:
                return most_common, max(best_conf, consensus_conf)

        return best_text, best_conf

    def read_multiple_plates(self, image: np.ndarray, plate_boxes: List[List[int]]) -> List[Dict]:
        """Read multiple plates from detected bounding boxes"""
        results = []
        for box in plate_boxes:
            x1, y1, x2, y2 = box
            plate_crop = image[y1:y2, x1:x2]
            if plate_crop.size == 0:
                continue
            text, conf = self.read_plate(plate_crop)
            if text:
                results.append({"bbox": box, "text": text, "confidence": conf})
        return results

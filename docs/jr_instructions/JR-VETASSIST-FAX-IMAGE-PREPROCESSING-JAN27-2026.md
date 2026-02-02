# JR Instruction: Fax-Quality Image Preprocessing

**JR ID:** JR-AI-001
**Priority:** P2 (Elevated to IMMEDIATE by Council)
**Sprint:** VetAssist AI Enhancements Phase 1
**Created:** 2026-01-27
**Author:** TPM via Claude Code
**Council Vote:** b942f2dcad0496e1
**Effort:** Low

## Problem Statement

Research shows a 38.8% F1 score drop when processing fax-distorted documents without preprocessing. VA documents frequently arrive via fax with:
- Skew/rotation
- Noise artifacts
- Low contrast
- Compression artifacts

## Required Implementation

CREATE: `/ganuda/vetassist/backend/app/services/image_preprocessor.py`

```python
"""
Fax-Quality Image Preprocessor for VetAssist.
Council Approved: 2026-01-27 (Vote b942f2dcad0496e1)

Addresses 38.8% F1 drop on fax-distorted documents.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """
    Preprocesses fax-quality images for improved OCR/VLM extraction.

    Pipeline:
    1. Deskew - correct rotation
    2. Denoise - remove fax artifacts
    3. Normalize - improve contrast
    4. Binarize - clean text extraction
    """

    def __init__(self,
                 denoise_strength: int = 10,
                 contrast_clip_limit: float = 2.0,
                 binarize_block_size: int = 11):
        self.denoise_strength = denoise_strength
        self.contrast_clip_limit = contrast_clip_limit
        self.binarize_block_size = binarize_block_size

    def preprocess(self, image_path: str, output_path: Optional[str] = None) -> str:
        """
        Full preprocessing pipeline for a document image.

        Args:
            image_path: Path to input image
            output_path: Optional output path (default: adds _preprocessed suffix)

        Returns:
            Path to preprocessed image
        """
        logger.info(f"[ImagePreprocessor] Processing: {image_path}")

        # Load image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Step 1: Deskew
        gray = self._deskew(gray)

        # Step 2: Denoise
        gray = self._denoise(gray)

        # Step 3: Contrast normalization
        gray = self._normalize_contrast(gray)

        # Step 4: Adaptive binarization
        binary = self._binarize(gray)

        # Save result
        if output_path is None:
            p = Path(image_path)
            output_path = str(p.parent / f"{p.stem}_preprocessed{p.suffix}")

        cv2.imwrite(output_path, binary)
        logger.info(f"[ImagePreprocessor] Saved: {output_path}")

        return output_path

    def _deskew(self, image: np.ndarray) -> np.ndarray:
        """Detect and correct document skew."""
        # Detect edges
        edges = cv2.Canny(image, 50, 150, apertureSize=3)

        # Detect lines using Hough transform
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100,
                                minLineLength=100, maxLineGap=10)

        if lines is None or len(lines) == 0:
            return image

        # Calculate average angle
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
            # Only consider near-horizontal lines
            if abs(angle) < 45:
                angles.append(angle)

        if not angles:
            return image

        median_angle = np.median(angles)

        # Only correct if skew is significant (> 0.5 degrees)
        if abs(median_angle) < 0.5:
            return image

        logger.info(f"[ImagePreprocessor] Deskewing by {median_angle:.2f} degrees")

        # Rotate image
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h),
                                  flags=cv2.INTER_CUBIC,
                                  borderMode=cv2.BORDER_REPLICATE)

        return rotated

    def _denoise(self, image: np.ndarray) -> np.ndarray:
        """Remove fax noise artifacts."""
        # Non-local means denoising (good for fax noise)
        denoised = cv2.fastNlMeansDenoising(
            image,
            h=self.denoise_strength,
            templateWindowSize=7,
            searchWindowSize=21
        )
        return denoised

    def _normalize_contrast(self, image: np.ndarray) -> np.ndarray:
        """Improve contrast using CLAHE."""
        clahe = cv2.createCLAHE(
            clipLimit=self.contrast_clip_limit,
            tileGridSize=(8, 8)
        )
        return clahe.apply(image)

    def _binarize(self, image: np.ndarray) -> np.ndarray:
        """Adaptive thresholding for clean text."""
        # Ensure block size is odd
        block_size = self.binarize_block_size
        if block_size % 2 == 0:
            block_size += 1

        binary = cv2.adaptiveThreshold(
            image,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            block_size,
            2
        )
        return binary

    def get_quality_score(self, image_path: str) -> float:
        """
        Estimate document quality (0-1).
        Low scores indicate fax-quality documents needing preprocessing.
        """
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return 0.0

        # Metrics for quality estimation
        # 1. Contrast (standard deviation)
        contrast = img.std() / 128.0  # Normalize to 0-1

        # 2. Sharpness (Laplacian variance)
        laplacian = cv2.Laplacian(img, cv2.CV_64F)
        sharpness = min(laplacian.var() / 1000.0, 1.0)

        # 3. Noise estimate (high-frequency content)
        blur = cv2.GaussianBlur(img, (5, 5), 0)
        noise = np.abs(img.astype(float) - blur.astype(float)).mean() / 255.0
        noise_score = 1.0 - min(noise * 5, 1.0)  # Less noise = higher score

        # Combined score
        quality = (contrast * 0.3 + sharpness * 0.4 + noise_score * 0.3)
        return min(max(quality, 0.0), 1.0)


# Convenience function for API use
def preprocess_document_image(
    image_path: str,
    output_path: Optional[str] = None,
    quality_threshold: float = 0.6
) -> Tuple[str, bool]:
    """
    Preprocess a document image if quality is below threshold.

    Args:
        image_path: Path to input image
        output_path: Optional output path
        quality_threshold: Skip preprocessing if quality above this

    Returns:
        Tuple of (output_path, was_preprocessed)
    """
    preprocessor = ImagePreprocessor()

    quality = preprocessor.get_quality_score(image_path)
    logger.info(f"[ImagePreprocessor] Quality score: {quality:.2f}")

    if quality >= quality_threshold:
        logger.info(f"[ImagePreprocessor] Quality OK, skipping preprocessing")
        return image_path, False

    output = preprocessor.preprocess(image_path, output_path)
    return output, True
```

## Integration Point

MODIFY: `/ganuda/vetassist/backend/app/services/ocr_service.py`

Add preprocessing call before OCR extraction:

```python
from app.services.image_preprocessor import preprocess_document_image

# In the extract method, before OCR:
preprocessed_path, was_preprocessed = preprocess_document_image(image_path)
if was_preprocessed:
    logger.info(f"Image was preprocessed for better OCR quality")
# Use preprocessed_path for OCR extraction
```

## Verification

```bash
cd /ganuda/vetassist/backend
python3 -c "
from app.services.image_preprocessor import ImagePreprocessor, preprocess_document_image

# Test initialization
preprocessor = ImagePreprocessor()
print('✓ ImagePreprocessor initialized')

# Test quality scoring (will need actual test image)
# quality = preprocessor.get_quality_score('/path/to/test.jpg')

print('✓ All imports and initialization working')
"
```

## Dependencies

Ensure OpenCV is installed:
```bash
pip install opencv-python-headless
```

(Note: opencv-python-headless is preferred for server environments)

---

FOR SEVEN GENERATIONS

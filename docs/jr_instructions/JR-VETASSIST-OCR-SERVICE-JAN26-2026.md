# Jr Instruction: VetAssist OCR Processing Service

**Task ID:** To be assigned
**Jr Type:** Software Engineer Jr.
**Priority:** P1
**Estimated Complexity:** Medium

---

## Objective

Create an OCR processing service that extracts text from veteran documents using Tesseract.

---

## Deliverable

Create file: `/ganuda/vetassist/backend/services/ocr_processor.py`

---

## Requirements

### Class: OCRProcessor

```python
class OCRProcessor:
    """Process document images through Tesseract OCR."""

    def __init__(self):
        """Initialize Tesseract configuration."""
        pass

    def process_pdf(self, pdf_path: str) -> dict:
        """
        Convert PDF to images and OCR each page.

        Returns:
            {
                "pages": [
                    {
                        "page_num": 1,
                        "text": "extracted text...",
                        "confidence": 0.95,
                        "word_confidences": [(word, conf), ...]
                    }
                ],
                "total_pages": int,
                "average_confidence": float
            }
        """
        pass

    def process_image(self, image_path: str) -> dict:
        """
        OCR a single image file (JPG, PNG, TIFF).

        Returns same structure as process_pdf but with single page.
        """
        pass

    def preprocess_image(self, image) -> image:
        """
        Apply preprocessing to improve OCR accuracy:
        - Convert to grayscale
        - Deskew if needed
        - Enhance contrast
        - Remove noise
        """
        pass
```

### Dependencies

```python
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import cv2
import numpy as np
```

### Configuration

- Tesseract path: `/usr/bin/tesseract`
- Language: `eng`
- Page segmentation mode: 3 (fully automatic)
- Output: Text with confidence data

---

## Technical Notes

1. Use `pytesseract.image_to_data()` for word-level confidence
2. PDF conversion uses poppler via `pdf2image`
3. Preprocessing with OpenCV before OCR improves accuracy
4. Return confidence scores for quality gating

---

## Test Cases

1. Process a clear typed PDF - expect > 95% confidence
2. Process a scanned image - expect reasonable text extraction
3. Handle invalid file gracefully - return error dict

---

## Integration Points

- Called by document upload endpoint after file validation
- Output feeds into entity extraction service
- Confidence scores determine if human review needed

---

## Do NOT

- Send documents to external APIs
- Store raw text without encryption path
- Skip confidence scoring

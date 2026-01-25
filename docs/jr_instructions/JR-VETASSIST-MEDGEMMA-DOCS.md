# Jr Instruction: VetAssist MedGemma Medical Document Understanding

## Priority: HIGH
## Estimated Effort: Large
## Category: ML/Document AI

---

## Objective

Integrate Google's MedGemma 1.5 or equivalent medical document understanding model to extract structured evidence from veteran medical records, including diagnoses, treatments, and nexus language for service connection.

---

## Research Basis

- MedGemma 1.5 4B: Medical document understanding, lab report extraction
- Taiwan NHIA: Processed 30,000+ pathology reports
- OscarAI: Vision-based (PDF→Image→GPT) outperforms OCR-based
- MIRAGE: Handles handwritten medical records

Reference: `/ganuda/docs/research/AI-RESEARCH-VETASSIST-ENHANCEMENT-JAN2026.md`

---

## Implementation

### Step 1: Model Selection

**Options (in order of preference):**

1. **MedGemma 1.5 4B** (Google)
   - Best for medical document understanding
   - Requires API access or local deployment
   - HuggingFace: `google/medgemma-1.5-4b-it`

2. **LLaVA-Med** (Microsoft)
   - Open source medical vision-language model
   - Can run locally

3. **GPT-4V with medical prompts** (Fallback)
   - Cloud API
   - General purpose but effective

### Step 2: Document Processing Pipeline

**File:** `/ganuda/vetassist/backend/app/services/medical_document_processor.py`

```python
"""
Medical Document Processing Service
Extracts structured evidence from veteran medical records.

Cherokee AI Federation - For Seven Generations
"""
import os
import io
import base64
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from PIL import Image
import fitz  # PyMuPDF
import httpx

logger = logging.getLogger(__name__)


@dataclass
class DiagnosisEntity:
    """Extracted diagnosis from medical record."""
    condition: str
    icd_code: Optional[str]
    date: Optional[str]
    provider: Optional[str]
    confidence: float


@dataclass
class TreatmentEntity:
    """Extracted treatment information."""
    treatment_type: str
    description: str
    date: Optional[str]
    facility: Optional[str]


@dataclass
class NexusSignal:
    """Service connection language found in document."""
    text: str
    signal_type: str  # direct, aggravation, secondary
    strength: str  # strong, moderate, weak
    context: str


@dataclass
class EvidencePackage:
    """Complete extracted evidence from a document."""
    document_type: str
    diagnoses: List[DiagnosisEntity]
    treatments: List[TreatmentEntity]
    nexus_signals: List[NexusSignal]
    raw_text: str
    page_count: int
    extraction_confidence: float


class MedicalDocumentProcessor:
    """Processes medical documents to extract claim evidence."""

    def __init__(self, model_type: str = "medgemma"):
        self.model_type = model_type
        self._setup_model()

    def _setup_model(self):
        """Initialize the ML model."""
        if self.model_type == "medgemma":
            # MedGemma via HuggingFace or local
            try:
                from transformers import AutoProcessor, AutoModelForVision2Seq
                self.processor = AutoProcessor.from_pretrained("google/medgemma-1.5-4b-it")
                self.model = AutoModelForVision2Seq.from_pretrained("google/medgemma-1.5-4b-it")
                logger.info("[MedDoc] Loaded MedGemma model")
            except Exception as e:
                logger.warning(f"[MedDoc] MedGemma not available, using fallback: {e}")
                self.model_type = "vision_api"
        elif self.model_type == "vision_api":
            # Use vLLM or external API
            self.api_url = os.environ.get("VISION_API_URL", "http://localhost:8000/v1")
            logger.info(f"[MedDoc] Using vision API at {self.api_url}")

    def _pdf_to_images(self, pdf_bytes: bytes) -> List[Image.Image]:
        """Convert PDF pages to images."""
        images = []
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            pix = page.get_pixmap(dpi=150)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)
        doc.close()
        return images

    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64."""
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()

    async def _extract_with_vision(self, image: Image.Image) -> Dict:
        """Extract information from image using vision model."""
        prompt = """Analyze this medical document and extract:
1. All diagnoses with ICD codes if visible
2. Treatment information
3. Any language suggesting service connection (nexus)
4. Provider and facility information
5. Dates of service

Format as JSON with keys: diagnoses, treatments, nexus_signals, metadata"""

        if self.model_type == "medgemma" and hasattr(self, 'model'):
            # Local MedGemma inference
            inputs = self.processor(images=image, text=prompt, return_tensors="pt")
            outputs = self.model.generate(**inputs, max_new_tokens=1000)
            response = self.processor.decode(outputs[0], skip_special_tokens=True)
            return self._parse_extraction(response)
        else:
            # API call
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/chat/completions",
                    json={
                        "model": "vision",
                        "messages": [{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {
                                    "url": f"data:image/png;base64,{self._image_to_base64(image)}"
                                }}
                            ]
                        }],
                        "max_tokens": 1000
                    },
                    timeout=60.0
                )
                result = response.json()
                return self._parse_extraction(result['choices'][0]['message']['content'])

    def _parse_extraction(self, response: str) -> Dict:
        """Parse model response into structured data."""
        import json
        try:
            # Try to extract JSON from response
            json_match = response[response.find('{'):response.rfind('}')+1]
            return json.loads(json_match)
        except:
            # Fallback: return raw text for further processing
            return {"raw_text": response, "parse_failed": True}

    def _identify_nexus_signals(self, text: str) -> List[NexusSignal]:
        """Identify service connection language in text."""
        signals = []

        # Strong nexus language
        strong_patterns = [
            r"at least as likely as not",
            r"more likely than not",
            r"is due to",
            r"is a result of",
            r"caused by.*service",
            r"related to.*military",
        ]

        # Moderate nexus language
        moderate_patterns = [
            r"may be related to",
            r"could be connected to",
            r"possibly due to",
        ]

        # Check patterns
        import re
        for pattern in strong_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                signals.append(NexusSignal(
                    text=match.group(),
                    signal_type="direct",
                    strength="strong",
                    context=text[start:end]
                ))

        for pattern in moderate_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                signals.append(NexusSignal(
                    text=match.group(),
                    signal_type="direct",
                    strength="moderate",
                    context=text[start:end]
                ))

        return signals

    async def process_document(self, document: bytes, filename: str) -> EvidencePackage:
        """
        Process a medical document and extract evidence.

        Args:
            document: Raw document bytes (PDF or image)
            filename: Original filename for type detection

        Returns:
            EvidencePackage with all extracted evidence
        """
        logger.info(f"[MedDoc] Processing document: {filename}")

        # Convert to images
        if filename.lower().endswith('.pdf'):
            images = self._pdf_to_images(document)
        else:
            images = [Image.open(io.BytesIO(document))]

        # Extract from each page
        all_diagnoses = []
        all_treatments = []
        all_nexus = []
        all_text = []

        for i, image in enumerate(images):
            logger.info(f"[MedDoc] Processing page {i+1}/{len(images)}")
            extraction = await self._extract_with_vision(image)

            if extraction.get('diagnoses'):
                all_diagnoses.extend([
                    DiagnosisEntity(
                        condition=d.get('condition', ''),
                        icd_code=d.get('icd_code'),
                        date=d.get('date'),
                        provider=d.get('provider'),
                        confidence=d.get('confidence', 0.8)
                    )
                    for d in extraction['diagnoses']
                ])

            if extraction.get('treatments'):
                all_treatments.extend([
                    TreatmentEntity(
                        treatment_type=t.get('type', 'unknown'),
                        description=t.get('description', ''),
                        date=t.get('date'),
                        facility=t.get('facility')
                    )
                    for t in extraction['treatments']
                ])

            raw_text = extraction.get('raw_text', '')
            all_text.append(raw_text)
            all_nexus.extend(self._identify_nexus_signals(raw_text))

        combined_text = '\n\n'.join(all_text)

        return EvidencePackage(
            document_type=self._detect_document_type(combined_text),
            diagnoses=all_diagnoses,
            treatments=all_treatments,
            nexus_signals=all_nexus,
            raw_text=combined_text,
            page_count=len(images),
            extraction_confidence=0.85 if not any(
                e.confidence < 0.5 for e in all_diagnoses
            ) else 0.6
        )

    def _detect_document_type(self, text: str) -> str:
        """Detect type of medical document."""
        text_lower = text.lower()
        if 'nexus' in text_lower or 'medical opinion' in text_lower:
            return 'nexus_letter'
        elif 'dbq' in text_lower or 'disability benefits questionnaire' in text_lower:
            return 'dbq'
        elif 'discharge' in text_lower or 'dd-214' in text_lower:
            return 'military_record'
        elif 'private' in text_lower and 'treatment' in text_lower:
            return 'private_treatment'
        elif 'va ' in text_lower and ('medical' in text_lower or 'treatment' in text_lower):
            return 'va_treatment'
        else:
            return 'medical_record'


# Convenience function
async def process_medical_document(document: bytes, filename: str) -> Dict:
    """Process a medical document and return evidence."""
    processor = MedicalDocumentProcessor()
    result = await processor.process_document(document, filename)
    return asdict(result)
```

### Step 3: API Endpoint

**File:** `/ganuda/vetassist/backend/app/api/v1/endpoints/documents.py`

```python
"""
Document Processing API Endpoints
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import logging

from app.services.medical_document_processor import process_medical_document

router = APIRouter()
logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB
ALLOWED_TYPES = ['application/pdf', 'image/jpeg', 'image/png', 'image/tiff']


@router.post("/extract")
async def extract_evidence(file: UploadFile = File(...)):
    """
    Extract evidence from a medical document.

    Supports: PDF, JPEG, PNG, TIFF
    Max size: 25MB
    """
    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, f"Unsupported file type: {file.content_type}")

    # Read file
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB")

    # Process document
    try:
        result = await process_medical_document(content, file.filename)
        logger.info(f"[Documents] Processed {file.filename}: {len(result['diagnoses'])} diagnoses found")
        return result
    except Exception as e:
        logger.error(f"[Documents] Processing failed: {e}")
        raise HTTPException(500, "Document processing failed")


@router.post("/batch")
async def batch_extract(files: List[UploadFile] = File(...)):
    """Extract evidence from multiple documents."""
    results = []
    for file in files:
        try:
            content = await file.read()
            result = await process_medical_document(content, file.filename)
            results.append({"filename": file.filename, "evidence": result})
        except Exception as e:
            results.append({"filename": file.filename, "error": str(e)})

    return {"results": results, "total": len(results)}
```

---

## Dependencies

```bash
pip install transformers pillow pymupdf httpx
```

For MedGemma (if running locally):
```bash
pip install torch accelerate
```

---

## Verification

1. Test PDF processing:
```python
from app.services.medical_document_processor import process_medical_document
with open("test_medical_record.pdf", "rb") as f:
    result = await process_medical_document(f.read(), "test.pdf")
print(result)
```

2. Test API endpoint:
```bash
curl -X POST "http://localhost:8001/api/v1/documents/extract" \
  -F "file=@test_medical_record.pdf"
```

---

## Success Criteria

- [ ] Document processing pipeline working
- [ ] Diagnosis extraction accuracy ≥85%
- [ ] Nexus signal detection working
- [ ] PDF and image support
- [ ] API endpoint functional
- [ ] Processing time <60s per document

---

*Cherokee AI Federation - For Seven Generations*

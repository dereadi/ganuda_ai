# JR Instruction: VLM Document Extractor Service

**JR ID:** JR-AI-005
**Priority:** P1
**Sprint:** VetAssist AI Enhancements Phase 2
**Created:** 2026-01-27
**Author:** TPM via Claude Code
**Council Vote:** b942f2dcad0496e1
**Assigned To:** software_jr
**Depends On:** JR-AI-004 (Qwen 2.5-VL Setup)
**Effort:** Medium

## Problem Statement

Current Tesseract OCR pipeline struggles with:
- Handwritten annotations (common in medical records)
- Complex table structures (lab results, medication lists)
- Multi-column layouts (DD-214 forms)
- Low-quality fax scans (common VA documents)

Research shows Qwen 2.5-VL achieves near GPT-4o performance on document understanding with significantly lower cost.

## Required Implementation

### 1. VLM Document Extractor Service

CREATE: `/ganuda/vetassist/backend/app/services/vlm_document_extractor.py`

```python
"""
Vision Language Model Document Extractor for VetAssist.
Council Approved: 2026-01-27 (Vote b942f2dcad0496e1)

Replaces/supplements Tesseract OCR with Qwen 2.5-VL for improved extraction
of complex medical documents.
"""

import base64
import httpx
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
import os

logger = logging.getLogger(__name__)


@dataclass
class DocumentField:
    """Extracted field from a document."""
    field_name: str
    value: str
    confidence: float
    location: Optional[str] = None  # "page 2, top-left"
    field_type: str = "text"  # text, date, number, checkbox


@dataclass
class ExtractionResult:
    """Complete extraction result from a document."""
    document_type: str  # "dd214", "medical_record", "nexus_letter", etc.
    fields: List[DocumentField]
    raw_text: str
    confidence: float
    processing_time_ms: int
    model_used: str


class VLMDocumentExtractor:
    """
    Extracts structured data from document images using Qwen 2.5-VL.
    """

    # Document type prompts for specialized extraction
    PROMPTS = {
        "dd214": '''Extract all information from this DD-214 form. Return JSON with:
{
  "name": "veteran full name",
  "service_number": "...",
  "branch": "...",
  "entry_date": "YYYY-MM-DD",
  "separation_date": "YYYY-MM-DD",
  "rank": "...",
  "mos": "military occupational specialty",
  "decorations": ["list of awards/medals"],
  "service_connected_disabilities": ["if listed"],
  "discharge_type": "honorable/general/etc"
}''',

        "medical_record": '''Extract medical information from this document. Return JSON with:
{
  "document_date": "YYYY-MM-DD",
  "provider": "doctor/facility name",
  "diagnoses": [{"code": "ICD code if shown", "description": "condition"}],
  "symptoms": ["list of symptoms mentioned"],
  "treatments": ["medications or procedures"],
  "notes": "any relevant clinical notes"
}''',

        "nexus_letter": '''Extract information from this nexus letter. Return JSON with:
{
  "author": "provider name and credentials",
  "date": "YYYY-MM-DD",
  "veteran_name": "...",
  "condition": "claimed condition",
  "service_connection_opinion": "at least as likely as not / less likely / etc",
  "rationale": "summary of medical reasoning",
  "evidence_cited": ["documents referenced"]
}''',

        "lab_results": '''Extract lab results from this document. Return JSON with:
{
  "test_date": "YYYY-MM-DD",
  "facility": "...",
  "results": [
    {"test_name": "...", "value": "...", "unit": "...", "reference_range": "...", "flag": "normal/high/low"}
  ]
}''',

        "generic": '''Extract all text and key information from this document. Return JSON with:
{
  "document_type": "your best guess",
  "date": "if visible",
  "title": "document title if any",
  "key_fields": {"field_name": "value"},
  "full_text": "complete text content"
}'''
    }

    def __init__(self):
        self.api_url = os.getenv("VLLM_VLM_API_URL", "http://localhost:8002/v1")
        self.model = os.getenv("VLLM_VLM_MODEL", "/ganuda/models/qwen2.5-vl-7b-awq")
        self.timeout = int(os.getenv("VLLM_VLM_TIMEOUT", "120"))

    def _encode_image(self, image_path: str) -> str:
        """Encode image as base64 for API."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _get_mime_type(self, image_path: str) -> str:
        """Get MIME type from file extension."""
        ext = Path(image_path).suffix.lower()
        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".tiff": "image/tiff",
            ".tif": "image/tiff",
            ".bmp": "image/bmp"
        }
        return mime_map.get(ext, "image/png")

    async def extract(
        self,
        image_path: str,
        document_type: str = "generic",
        additional_context: Optional[str] = None
    ) -> ExtractionResult:
        """
        Extract structured data from a document image.

        Args:
            image_path: Path to document image
            document_type: Type of document for specialized prompts
            additional_context: Any additional context to guide extraction

        Returns:
            ExtractionResult with extracted fields
        """
        import time
        start_time = time.time()

        logger.info(f"[VLMExtractor] Processing: {image_path} as {document_type}")

        # Encode image
        image_b64 = self._encode_image(image_path)
        mime_type = self._get_mime_type(image_path)

        # Build prompt
        base_prompt = self.PROMPTS.get(document_type, self.PROMPTS["generic"])
        if additional_context:
            base_prompt = f"{additional_context}\n\n{base_prompt}"

        # Call VLM API
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": base_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{mime_type};base64,{image_b64}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.1  # Low temp for consistent extraction
                }
            )

            response.raise_for_status()
            result = response.json()

        # Parse response
        content = result["choices"][0]["message"]["content"]
        processing_time = int((time.time() - start_time) * 1000)

        # Extract JSON from response
        extracted_data = self._parse_json_response(content)

        # Convert to fields
        fields = self._data_to_fields(extracted_data)

        # Calculate overall confidence
        confidence = sum(f.confidence for f in fields) / len(fields) if fields else 0.5

        logger.info(f"[VLMExtractor] Extracted {len(fields)} fields in {processing_time}ms")

        return ExtractionResult(
            document_type=document_type,
            fields=fields,
            raw_text=content,
            confidence=confidence,
            processing_time_ms=processing_time,
            model_used="qwen2.5-vl-7b-awq"
        )

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Extract JSON from model response."""
        # Try to find JSON in response
        try:
            # Look for JSON block
            if "```json" in content:
                start = content.index("```json") + 7
                end = content.index("```", start)
                content = content[start:end].strip()
            elif "```" in content:
                start = content.index("```") + 3
                end = content.index("```", start)
                content = content[start:end].strip()

            return json.loads(content)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"[VLMExtractor] Could not parse JSON: {e}")
            return {"raw_content": content}

    def _data_to_fields(self, data: Dict[str, Any], prefix: str = "") -> List[DocumentField]:
        """Convert extracted data dict to list of DocumentField objects."""
        fields = []

        for key, value in data.items():
            field_name = f"{prefix}{key}" if prefix else key

            if isinstance(value, dict):
                # Recurse for nested dicts
                fields.extend(self._data_to_fields(value, f"{field_name}."))
            elif isinstance(value, list):
                # Handle lists
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        fields.extend(self._data_to_fields(item, f"{field_name}[{i}]."))
                    else:
                        fields.append(DocumentField(
                            field_name=f"{field_name}[{i}]",
                            value=str(item),
                            confidence=0.8  # Default confidence for extracted fields
                        ))
            else:
                fields.append(DocumentField(
                    field_name=field_name,
                    value=str(value) if value else "",
                    confidence=0.85 if value else 0.3
                ))

        return fields


# Convenience function for sync code
def extract_document_sync(
    image_path: str,
    document_type: str = "generic"
) -> ExtractionResult:
    """Synchronous wrapper for document extraction."""
    import asyncio
    extractor = VLMDocumentExtractor()
    return asyncio.run(extractor.extract(image_path, document_type))
```

### 2. Integration with Document Processor

MODIFY: `/ganuda/vetassist/backend/app/services/document_processor.py`

Find the document processing method and add VLM extraction as primary path:

```python
from app.services.vlm_document_extractor import VLMDocumentExtractor, extract_document_sync
from app.services.image_preprocessor import preprocess_document_image

class DocumentProcessor:

    async def process_document(self, file_path: str, document_type: str = "generic"):
        # Step 1: Preprocess for fax quality (JR-AI-001)
        preprocessed_path, was_preprocessed = preprocess_document_image(file_path)

        # Step 2: VLM extraction (primary)
        extractor = VLMDocumentExtractor()
        result = await extractor.extract(preprocessed_path, document_type)

        # Step 3: Record audit trail (JR-AI-002/003)
        from app.models.ai_audit import AIAuditEntry, get_audit_service
        audit_entry = AIAuditEntry(
            content_type='document_extraction',
            content_id=f"doc-{Path(file_path).stem}",
            generated_by=result.model_used,
            confidence=result.confidence,
            quality_flags={
                "was_preprocessed": was_preprocessed,
                "document_type": document_type
            },
            processing_time_ms=result.processing_time_ms
        )
        get_audit_service().record(audit_entry)

        return result
```

### 3. API Endpoint Update

MODIFY: `/ganuda/vetassist/backend/app/api/v1/endpoints/documents.py`

Add document type parameter to upload endpoint:

```python
from app.services.vlm_document_extractor import VLMDocumentExtractor

@router.post("/upload")
async def upload_document(
    file: UploadFile,
    document_type: str = Query(default="generic", description="Document type for extraction"),
    session_id: Optional[str] = None
):
    # ... existing upload logic ...

    # Process with VLM
    extractor = VLMDocumentExtractor()
    result = await extractor.extract(saved_path, document_type)

    return {
        "document_id": doc_id,
        "extracted_fields": [f.__dict__ for f in result.fields],
        "confidence": result.confidence,
        "processing_time_ms": result.processing_time_ms
    }
```

## Verification

```bash
cd /ganuda/vetassist/backend

# Test VLM extractor import
python3 -c "
from app.services.vlm_document_extractor import VLMDocumentExtractor
extractor = VLMDocumentExtractor()
print(f'✓ VLMDocumentExtractor initialized')
print(f'  API URL: {extractor.api_url}')
print(f'  Model: {extractor.model}')
print(f'  Timeout: {extractor.timeout}s')
print(f'✓ Document prompts loaded: {list(extractor.PROMPTS.keys())}')
"

# Test with actual document (requires JR-AI-004 complete)
python3 -c "
import asyncio
from app.services.vlm_document_extractor import VLMDocumentExtractor

async def test():
    extractor = VLMDocumentExtractor()
    # Use a test document
    result = await extractor.extract('/ganuda/vetassist/uploads/test_doc.png', 'generic')
    print(f'✓ Extraction completed in {result.processing_time_ms}ms')
    print(f'✓ Fields extracted: {len(result.fields)}')
    print(f'✓ Confidence: {result.confidence:.2f}')

asyncio.run(test())
"
```

## Dependencies

- JR-AI-004 must be complete (VLM model running on port 8002)
- httpx for async HTTP client
- Existing image_preprocessor.py from JR-AI-001

---

FOR SEVEN GENERATIONS

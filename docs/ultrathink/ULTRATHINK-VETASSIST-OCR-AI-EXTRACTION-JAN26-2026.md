# ULTRATHINK: VetAssist Document OCR/AI Extraction

**Date:** 2026-01-26
**Sprint:** VetAssist Sprint 3
**Council Vote:** PROCEED - Hybrid Approach (Local OCR + Local LLM)

---

## Executive Summary

Build a document processing pipeline for VetAssist that:
1. Accepts veteran document uploads (DD-214, medical records, VA letters)
2. Extracts text via local OCR (Tesseract)
3. Identifies entities via local LLM (Qwen 32B)
4. Outputs structured data for the claim wizard

---

## Architecture Decision

### Chosen: Hybrid Local Processing

| Component | Technology | Rationale |
|-----------|------------|-----------|
| OCR | Tesseract 5.x | Local, free, good accuracy on typed docs |
| Pre-processing | OpenCV/Pillow | Deskew, contrast, noise reduction |
| Entity Extraction | Qwen 32B via LLM Gateway | Local, privacy-first, already deployed |
| PII Masking | Presidio | Already integrated in VetAssist |
| Storage | PostgreSQL (goldfin) | PII-isolated database |

### Why Not Cloud APIs?

1. **Privacy**: Veteran documents contain SSN, medical diagnoses, service history
2. **Cost**: Document AI charges per page - veterans may upload hundreds
3. **Sovereignty**: Cherokee AI Federation principle - data stays on our hardware
4. **Existing Infrastructure**: We already have Qwen 32B on redfin

---

## Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                     Document Upload                              │
│                   (PDF, JPG, PNG, TIFF)                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Pre-processing Layer                          │
│  • PDF → Image conversion (pdf2image)                           │
│  • Deskew correction                                            │
│  • Contrast enhancement                                         │
│  • Noise reduction                                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      OCR Layer                                   │
│  • Tesseract 5.x with eng+medical dictionaries                  │
│  • Page-by-page processing                                      │
│  • Confidence scoring per word                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   PII Detection Layer                           │
│  • Presidio scan for SSN, DOB, addresses                        │
│  • Mark PII locations (don't redact yet)                        │
│  • Log PII detection metrics                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Entity Extraction Layer                         │
│  • Qwen 32B via LLM Gateway                                     │
│  • Structured prompt for VA document types                      │
│  • Extract: conditions, dates, ratings, service connection      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Structured Output                              │
│  • JSON schema for claim wizard                                 │
│  • Confidence scores per extraction                             │
│  • Human review flags for low confidence                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Document Types to Support

### Phase 1 (Sprint 3)
| Document | Key Extractions |
|----------|-----------------|
| DD-214 | Service dates, MOS, discharge type, awards |
| VA Rating Decision | Current ratings, conditions, effective dates |
| C&P Exam Results | Diagnoses, severity, examiner findings |

### Phase 2 (Future)
| Document | Key Extractions |
|----------|-----------------|
| Medical Records | Diagnoses, treatment dates, provider notes |
| Buddy Statements | Witness accounts, incident descriptions |
| Service Medical Records | In-service incidents, sick call visits |

---

## Entity Extraction Schema

```json
{
  "document_type": "dd214|va_rating|cp_exam|medical_record",
  "extraction_confidence": 0.0-1.0,
  "service_info": {
    "branch": "string",
    "entry_date": "YYYY-MM-DD",
    "separation_date": "YYYY-MM-DD",
    "discharge_type": "string",
    "mos_codes": ["string"]
  },
  "conditions": [
    {
      "name": "string",
      "icd_code": "string|null",
      "cfr_code": "string|null",
      "current_rating": "integer|null",
      "service_connected": "boolean|null",
      "confidence": 0.0-1.0
    }
  ],
  "dates": [
    {
      "type": "diagnosis|incident|treatment|exam",
      "date": "YYYY-MM-DD",
      "description": "string"
    }
  ],
  "evidence_strength": {
    "nexus_indicators": ["string"],
    "missing_elements": ["string"]
  },
  "pii_detected": {
    "ssn_present": "boolean",
    "dob_present": "boolean",
    "address_present": "boolean"
  },
  "raw_text_hash": "string",
  "pages_processed": "integer"
}
```

---

## Implementation Tasks

### Backend (Software Engineer Jr.)

1. **Document Upload Endpoint**
   - `POST /api/documents/upload`
   - Accept multipart/form-data
   - Validate file types (PDF, JPG, PNG, TIFF)
   - Store original in secure location
   - Return document_id for status polling

2. **OCR Processing Service**
   - `vetassist/backend/services/ocr_processor.py`
   - Tesseract wrapper with pre-processing
   - Page-by-page confidence scoring
   - Queue-based async processing

3. **Entity Extraction Service**
   - `vetassist/backend/services/entity_extractor.py`
   - LLM Gateway integration
   - Document-type-specific prompts
   - Structured output validation

4. **Processing Status Endpoint**
   - `GET /api/documents/{id}/status`
   - Return processing stage and progress
   - WebSocket option for real-time updates

5. **Results Endpoint**
   - `GET /api/documents/{id}/extractions`
   - Return structured extraction data
   - Include confidence scores and review flags

### Frontend (Software Engineer Jr.)

1. **Upload Component**
   - Drag-and-drop file upload
   - Progress indicator
   - File type validation

2. **Processing Status Display**
   - Real-time status updates
   - Stage indicators (uploading → OCR → extracting → complete)

3. **Results Review Interface**
   - Display extracted entities
   - Highlight low-confidence items
   - Allow manual corrections
   - "Add to Claim" button integration

---

## Dependencies to Install

### System Packages (redfin)
```bash
sudo apt install tesseract-ocr tesseract-ocr-eng poppler-utils
```

### Python Packages
```bash
pip install pytesseract pdf2image pillow opencv-python-headless
```

---

## Security Considerations

1. **Document Storage**: Encrypted at rest on goldfin (PII database)
2. **Processing**: All OCR/LLM runs on redfin (no external APIs)
3. **Access Control**: Documents tied to user session
4. **Audit Log**: All document access logged
5. **Retention**: User controls document deletion

---

## Success Metrics

| Metric | Target |
|--------|--------|
| OCR Accuracy (typed docs) | > 95% |
| Entity Extraction Accuracy | > 85% |
| Processing Time (10-page PDF) | < 60 seconds |
| User Correction Rate | < 20% |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Poor OCR on handwritten docs | Display confidence, flag for manual review |
| LLM hallucination on entities | Schema validation, confidence thresholds |
| Large file uploads | Size limits, chunked processing |
| Processing queue backup | Priority queue, status visibility |

---

## Jr Task Breakdown

1. **JR-VETASSIST-OCR-SERVICE-JAN26-2026**: OCR processing service
2. **JR-VETASSIST-ENTITY-EXTRACTOR-JAN26-2026**: LLM entity extraction
3. **JR-VETASSIST-DOCUMENT-UPLOAD-API-JAN26-2026**: Upload endpoint
4. **JR-VETASSIST-DOCUMENT-UI-JAN26-2026**: Frontend upload/review

---

## For Seven Generations

Document processing touches the most sensitive moments in a veteran's life - their service record, their medical history, their disability journey. Every extraction we get right helps a veteran get the benefits they earned. Every error we catch before submission protects them from delay or denial.

We build this with care, not speed. Accuracy matters more than features.

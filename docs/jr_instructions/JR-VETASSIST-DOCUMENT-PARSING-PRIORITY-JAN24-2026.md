# JR Instruction: VetAssist Document Parsing - Sprint 3 Priority

**Task ID:** VETASSIST-DOCPARSE-001
**Priority:** P0 - Council Priority
**Type:** implementation
**Assigned:** Software Engineer Jr.
**Council Vote:** 6-1 (Document parsing is foundational)

---

## Objective

Complete the document processing pipeline for VetAssist, including OCR, temporal extraction, and service period mapping. This is the Council-designated Sprint 3 priority.

---

## Background

Council voted 6-1 that document parsing is the highest priority for Sprint 3:
- "Document parsing is foundational" - Eagle, Beaver
- "Foundational for improving accuracy" - Beaver
- Enables all other features (wizard, nexus letter, VA submission)

---

## Current State

Existing:
- File upload UI (React)
- PII detection (Presidio integration)
- Basic PDF text extraction

Missing:
- OCR for scanned documents
- Temporal era extraction (LLMD-TEMPORAL-001)
- Service period mapping
- Evidence gap detection
- Document classification

---

## Deliverables

### 1. Document Classification
Create `/ganuda/vetassist/lib/document_classifier.py`:

```python
class DocumentType(Enum):
    DD214 = "dd214"                    # Discharge papers
    MEDICAL_RECORD = "medical_record"  # VA/private medical
    BUDDY_STATEMENT = "buddy_statement"
    NEXUS_LETTER = "nexus_letter"
    SERVICE_RECORD = "service_record"  # Military personnel records
    PRESCRIPTION = "prescription"
    AUDIOGRAM = "audiogram"
    XRAY_REPORT = "xray_report"
    UNKNOWN = "unknown"

def classify_document(text: str, filename: str) -> DocumentType:
    """Classify uploaded document by content and filename."""
```

### 2. OCR Pipeline
Create `/ganuda/vetassist/lib/ocr_pipeline.py`:

```python
def extract_text(file_path: str) -> str:
    """
    Extract text from document.
    - PDF: Use existing PyPDF2
    - Images: Use Tesseract OCR
    - Scanned PDFs: Convert to images, then OCR
    """
```

### 3. DD-214 Parser
Create `/ganuda/vetassist/lib/dd214_parser.py`:

```python
@dataclass
class DD214Info:
    service_member_name: str
    branch: str
    entry_date: date
    separation_date: date
    discharge_type: str  # "Honorable", "General", etc.
    mos_codes: List[str]  # Military Occupational Specialties
    decorations: List[str]
    combat_service: bool

def parse_dd214(text: str) -> DD214Info:
    """Extract structured data from DD-214 text."""
```

### 4. Evidence Tracker
Create `/ganuda/vetassist/lib/evidence_tracker.py`:

```python
@dataclass
class EvidenceItem:
    document_type: DocumentType
    file_path: str
    upload_date: datetime
    extracted_dates: List[date]
    conditions_mentioned: List[str]
    service_connection_strength: float  # 0.0-1.0

def analyze_evidence_gaps(
    claimed_conditions: List[str],
    evidence_items: List[EvidenceItem],
    dd214: DD214Info
) -> Dict[str, List[str]]:
    """
    For each claimed condition, identify missing evidence.

    Returns:
        {
            "PTSD": ["nexus_letter", "buddy_statement"],
            "Tinnitus": ["current_audiogram"],
            ...
        }
    """
```

### 5. Integration with Claim Wizard
- After document upload, run classification
- Extract DD-214 if detected, store service dates
- Run temporal extraction on medical records
- Update evidence tracker
- Show evidence gaps in wizard UI

---

## File Structure

```
/ganuda/vetassist/lib/
├── document_classifier.py  # NEW
├── ocr_pipeline.py         # NEW
├── dd214_parser.py         # NEW
├── evidence_tracker.py     # NEW
├── temporal_parser.py      # From LLMD-TEMPORAL-001
└── __init__.py
```

---

## Testing

1. Upload sample DD-214, verify parsing
2. Upload scanned medical record, verify OCR
3. Test document classification accuracy
4. Test evidence gap detection with known gaps
5. Integration test: upload documents, see gaps in wizard

---

## Dependencies

- Tesseract OCR (apt install tesseract-ocr)
- pytesseract Python package
- pdf2image for scanned PDF handling
- Existing: PyPDF2, Presidio

---

## Tribal Awareness

**Benefit Who?** Veterans with scattered documentation
**Benefit How?** Transforms document chaos into organized evidence
**At Whose Expense?** Storage costs for processed documents (acceptable)

**Seven Generations:** Future veterans inherit a system that understands military and medical documents, not just stores them.

---

## Success Criteria

- [ ] DD-214 parsing extracts service dates correctly
- [ ] OCR handles scanned documents
- [ ] Document classification >90% accuracy
- [ ] Evidence gaps correctly identified
- [ ] Wizard displays upload status and gaps

# Jr Instruction: VetAssist Entity Extraction Service

**Task ID:** To be assigned
**Jr Type:** Software Engineer Jr.
**Priority:** P1
**Estimated Complexity:** Medium

---

## Objective

Create an entity extraction service that uses the LLM Gateway to identify structured data from OCR text.

---

## Deliverable

Create file: `/ganuda/vetassist/backend/services/entity_extractor.py`

---

## Requirements

### Class: EntityExtractor

```python
class EntityExtractor:
    """Extract structured entities from document text using LLM."""

    LLM_GATEWAY_URL = "http://192.168.132.223:8080/v1/chat/completions"
    API_KEY = "ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"

    def __init__(self):
        """Initialize extractor with document type prompts."""
        pass

    def extract(self, ocr_text: str, document_type: str = "auto") -> dict:
        """
        Extract entities from OCR text.

        Args:
            ocr_text: Raw text from OCR processor
            document_type: "dd214", "va_rating", "cp_exam", "medical", "auto"

        Returns:
            {
                "document_type": "detected or provided type",
                "extraction_confidence": 0.0-1.0,
                "service_info": {...},
                "conditions": [...],
                "dates": [...],
                "evidence_strength": {...}
            }
        """
        pass

    def detect_document_type(self, ocr_text: str) -> str:
        """Identify document type from text patterns."""
        pass

    def _build_extraction_prompt(self, ocr_text: str, doc_type: str) -> str:
        """Build structured extraction prompt for LLM."""
        pass

    def _parse_llm_response(self, response: str) -> dict:
        """Parse and validate LLM JSON response."""
        pass
```

### Document Type Detection Patterns

```python
DOCUMENT_PATTERNS = {
    "dd214": ["CERTIFICATE OF RELEASE", "DD FORM 214", "ARMED FORCES"],
    "va_rating": ["RATING DECISION", "SERVICE-CONNECTED", "COMBINED EVALUATION"],
    "cp_exam": ["COMPENSATION AND PENSION", "C&P EXAMINATION", "DBQ"],
    "medical": ["PATIENT:", "DIAGNOSIS:", "CHIEF COMPLAINT"]
}
```

### Entity Schema (Output)

```python
ENTITY_SCHEMA = {
    "document_type": str,
    "extraction_confidence": float,
    "service_info": {
        "branch": str,
        "entry_date": str,  # YYYY-MM-DD
        "separation_date": str,
        "discharge_type": str,
        "mos_codes": list
    },
    "conditions": [
        {
            "name": str,
            "icd_code": str | None,
            "cfr_code": str | None,
            "current_rating": int | None,
            "service_connected": bool | None,
            "confidence": float
        }
    ],
    "dates": [
        {
            "type": str,  # diagnosis, incident, treatment, exam
            "date": str,
            "description": str
        }
    ],
    "evidence_strength": {
        "nexus_indicators": list,
        "missing_elements": list
    }
}
```

---

## LLM Prompt Template

```python
EXTRACTION_PROMPT = """You are a VA claims document analyzer. Extract structured information from the following {doc_type} document.

DOCUMENT TEXT:
{ocr_text}

Extract the following information in JSON format:
1. Service information (branch, dates, discharge type, MOS)
2. Medical conditions mentioned (name, ICD code if present, rating if present)
3. Important dates (diagnoses, incidents, treatments)
4. Evidence of service connection (nexus indicators)

Return ONLY valid JSON matching this schema:
{schema}

If information is not found, use null. Include confidence score 0.0-1.0 for each extraction."""
```

---

## Technical Notes

1. Use requests to call LLM Gateway
2. Parse JSON response with error handling
3. Validate against schema before returning
4. Low confidence items should be flagged for review

---

## Integration Points

- Receives OCR text from ocr_processor.py
- Output feeds into claim wizard data population
- Integrates with existing evidence_gap_analyzer.py

---

## Do NOT

- Hallucinate information not in the document
- Skip confidence scoring
- Return unvalidated JSON

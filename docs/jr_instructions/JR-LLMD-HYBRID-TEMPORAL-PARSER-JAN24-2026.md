# JR Instruction: LLMD Hybrid Temporal Parser for VetAssist

**Task ID:** LLMD-TEMPORAL-001
**Priority:** P0 - Council Unanimous
**Type:** implementation
**Assigned:** Software Engineer Jr.
**Council Vote:** 7-0 (Hybrid approach - Qwen MVP, LLMD production)

---

## Objective

Implement temporal parsing for medical records using Qwen 32B with LLMD-inspired prompts for MVP, with architecture ready for LLMD fine-tuning in production.

---

## Background

Council unanimously voted for hybrid approach:
- MVP: Prompt engineering with existing Qwen 32B infrastructure
- Production: Evaluate LLMD-8B fine-tuning for higher accuracy

Reference: arXiv:2410.12860 (LLMD: Interpreting Longitudinal Medical Records)

---

## Deliverables

### 1. Temporal Era Extraction Module
Create `/ganuda/vetassist/lib/temporal_parser.py`:

```python
from dataclasses import dataclass
from typing import List, Optional
from datetime import date

@dataclass
class MedicalEra:
    """A continuous period for a medical condition/treatment."""
    category: str  # "medication", "diagnosis", "treatment", "symptom"
    description: str
    start_date: date
    end_date: Optional[date]
    source_document: str
    confidence: float

@dataclass
class ServicePeriodMapping:
    """Maps medical event to service period."""
    event: MedicalEra
    mapping: str  # "IN_SERVICE", "POST_SERVICE_1YR", "POST_SERVICE", "PRE_SERVICE"
    presumptive: bool  # True if within presumptive period

def extract_temporal_eras(medical_text: str) -> List[MedicalEra]:
    """Extract temporal eras from medical record text."""
    pass

def map_to_service_period(era: MedicalEra, service_start: date, service_end: date) -> ServicePeriodMapping:
    """Map a medical era to veteran's service period."""
    pass
```

### 2. LLMD-Inspired Prompt Template
Create prompts that mirror LLMD's structuring approach:

```python
TEMPORAL_EXTRACTION_PROMPT = '''
Analyze this medical record excerpt and extract temporal information.

For each medical event (diagnosis, medication, treatment, symptom), identify:
1. What: The specific medical finding
2. When: Date or date range (exact or approximate)
3. Category: diagnosis/medication/treatment/symptom
4. Confidence: How certain is the date (exact/approximate/inferred)

Medical Text:
{text}

Output JSON array of events:
[{{"category": "...", "description": "...", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD or null", "confidence": 0.0-1.0}}]
'''
```

### 3. Service Period Mapper
```python
def get_service_connection_status(event_date: date, dd214: DD214Info) -> dict:
    """
    Determine service connection status for a medical event.

    Returns:
        {
            "status": "IN_SERVICE" | "PRESUMPTIVE_1YR" | "POST_SERVICE" | "PRE_SERVICE",
            "days_from_service": int,
            "presumptive_eligible": bool,
            "notes": str
        }
    """
```

### 4. Integration with VetAssist Document Pipeline
- Hook into existing document upload flow
- After PII detection, run temporal extraction
- Store extracted eras in claim context
- Display timeline in wizard

---

## Architecture for LLMD Migration

Design the module so LLMD-8B can replace Qwen:

```python
class TemporalParser(ABC):
    @abstractmethod
    def extract(self, text: str) -> List[MedicalEra]:
        pass

class QwenTemporalParser(TemporalParser):
    """MVP implementation using Qwen 32B."""
    pass

class LLMDTemporalParser(TemporalParser):
    """Production implementation using fine-tuned LLMD-8B."""
    pass
```

---

## Testing

1. Create test medical records with known dates
2. Verify extraction accuracy
3. Test service period mapping with sample DD-214
4. Integration test with document upload

Test cases:
- "Patient diagnosed with PTSD on 2019-08-15"
- "Started Sertraline 50mg, increased to 100mg after 3 months"
- "Tinnitus noted during audiogram at Camp Pendleton"

---

## Tribal Awareness

**Benefit Who?** Veterans proving service-connection
**Benefit How?** Automated timeline extraction from scattered records
**At Whose Expense?** None - this transforms paperwork burden into evidence strength

---

## For Seven Generations

Every veteran's medical journey becomes a clear timeline, not a pile of documents.

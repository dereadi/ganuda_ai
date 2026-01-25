# JR Instruction: LLMD Phase 2 - Temporal Parser Implementation

**Task ID:** LLMD-PHASE2-001
**Priority:** P0 - Council Unanimous
**Type:** implementation
**Assigned:** Software Engineer Jr.
**Depends On:** LLMD-TEMPORAL-001 (completed)

---

## Objective

Implement the temporal parsing functions with Qwen 32B integration for extracting medical timelines from veteran records.

---

## Current State

Phase 1 created scaffolds:
- `/ganuda/vetassist/lib/temporal_parser.py` - Dataclasses and prompt template (working)
- Functions `extract_temporal_eras()` and `map_to_service_period()` are stubs

---

## Deliverables

### 1. Update temporal_parser.py

Replace stub functions with working implementation:

```python
#!/usr/bin/env python3
"""
LLMD-Inspired Temporal Parser for VetAssist

Extracts temporal medical information for service-connection proof.
Reference: arXiv:2410.12860 (LLMD)

For Seven Generations - Cherokee AI Federation
"""

import os
import json
import re
import requests
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple
from datetime import date, datetime, timedelta

# vLLM Configuration
VLLM_URL = os.environ.get('VLLM_URL', 'http://localhost:8000/v1/chat/completions')
VLLM_MODEL = os.environ.get('VLLM_MODEL', '/ganuda/models/qwen2.5-coder-32b-awq')

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
    presumptive: bool
    days_from_separation: Optional[int]

TEMPORAL_EXTRACTION_PROMPT = '''You are a medical record analyst specializing in veteran disability claims.

Analyze this medical record excerpt and extract temporal information.

For each medical event (diagnosis, medication, treatment, symptom), identify:
1. What: The specific medical finding
2. When: Date or date range (exact or approximate)
3. Category: diagnosis/medication/treatment/symptom
4. Confidence: How certain is the date (1.0=exact date stated, 0.7=approximate, 0.5=inferred)

Medical Text:
{text}

Respond with ONLY a JSON array, no other text:
[{{"category": "diagnosis", "description": "PTSD", "start_date": "2019-08-15", "end_date": null, "confidence": 1.0}}]

If no medical events with dates are found, respond with: []
'''

def query_llm(prompt: str, max_tokens: int = 1000) -> str:
    """Query vLLM for temporal extraction."""
    try:
        response = requests.post(
            VLLM_URL,
            json={
                "model": VLLM_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a medical record analyst. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.1  # Low temperature for consistent extraction
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[TemporalParser] LLM query failed: {e}")
        return "[]"

def parse_date(date_str: str) -> Optional[date]:
    """Parse various date formats."""
    if not date_str or date_str == "null":
        return None

    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%Y"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue

    return None

def extract_temporal_eras(medical_text: str, source_document: str = "unknown") -> List[MedicalEra]:
    """
    Extract temporal eras from medical record text using LLMD-style prompting.

    Args:
        medical_text: Raw text from medical record
        source_document: Identifier for the source document

    Returns:
        List of MedicalEra objects with extracted temporal information
    """
    if not medical_text or len(medical_text.strip()) < 10:
        return []

    # Query LLM
    prompt = TEMPORAL_EXTRACTION_PROMPT.format(text=medical_text[:4000])  # Limit context
    response = query_llm(prompt)

    # Parse JSON response
    try:
        # Clean response - remove markdown code blocks if present
        response = response.strip()
        if response.startswith("```"):
            response = re.sub(r'^```json?\n?', '', response)
            response = re.sub(r'\n?```$', '', response)

        events = json.loads(response)
    except json.JSONDecodeError:
        print(f"[TemporalParser] Failed to parse LLM response: {response[:100]}")
        return []

    # Convert to MedicalEra objects
    eras = []
    for event in events:
        try:
            start = parse_date(event.get("start_date"))
            if not start:
                continue  # Skip events without start date

            era = MedicalEra(
                category=event.get("category", "unknown"),
                description=event.get("description", ""),
                start_date=start,
                end_date=parse_date(event.get("end_date")),
                source_document=source_document,
                confidence=float(event.get("confidence", 0.5))
            )
            eras.append(era)
        except Exception as e:
            print(f"[TemporalParser] Error parsing event: {e}")
            continue

    return eras

def map_to_service_period(
    era: MedicalEra,
    service_start: date,
    service_end: date,
    presumptive_days: int = 365
) -> ServicePeriodMapping:
    """
    Map a medical era to veteran's service period.

    Args:
        era: The medical event to map
        service_start: DD-214 entry date
        service_end: DD-214 separation date
        presumptive_days: Days after separation for presumptive conditions (default 1 year)

    Returns:
        ServicePeriodMapping with service connection status
    """
    event_date = era.start_date

    # Calculate days from separation
    days_from_sep = (event_date - service_end).days if event_date > service_end else None

    # Determine mapping
    if event_date < service_start:
        mapping = "PRE_SERVICE"
        presumptive = False
    elif service_start <= event_date <= service_end:
        mapping = "IN_SERVICE"
        presumptive = False
    elif days_from_sep and days_from_sep <= presumptive_days:
        mapping = "POST_SERVICE_1YR"
        presumptive = True
    else:
        mapping = "POST_SERVICE"
        presumptive = False

    return ServicePeriodMapping(
        event=era,
        mapping=mapping,
        presumptive=presumptive,
        days_from_separation=days_from_sep
    )

def analyze_claim_timeline(
    medical_texts: List[Tuple[str, str]],  # (text, document_name)
    service_start: date,
    service_end: date
) -> dict:
    """
    Analyze full claim timeline from multiple documents.

    Returns summary with service connection evidence.
    """
    all_eras = []

    for text, doc_name in medical_texts:
        eras = extract_temporal_eras(text, doc_name)
        all_eras.extend(eras)

    # Sort by date
    all_eras.sort(key=lambda e: e.start_date)

    # Map to service period
    mappings = [map_to_service_period(era, service_start, service_end) for era in all_eras]

    # Summarize
    summary = {
        "total_events": len(mappings),
        "in_service": [m for m in mappings if m.mapping == "IN_SERVICE"],
        "presumptive": [m for m in mappings if m.presumptive],
        "post_service": [m for m in mappings if m.mapping == "POST_SERVICE"],
        "pre_service": [m for m in mappings if m.mapping == "PRE_SERVICE"],
        "timeline": [
            {
                "date": str(m.event.start_date),
                "description": m.event.description,
                "category": m.event.category,
                "service_connection": m.mapping,
                "confidence": m.event.confidence
            }
            for m in mappings
        ]
    }

    return summary


# Self-test
if __name__ == "__main__":
    test_text = """
    Patient was diagnosed with PTSD on August 15, 2019 following combat deployment.
    Started Sertraline 50mg on September 1, 2019.
    Dosage increased to 100mg on December 15, 2019.
    Tinnitus first noted during audiogram at Camp Pendleton on March 3, 2018.
    """

    print("Testing temporal extraction...")
    eras = extract_temporal_eras(test_text, "test_record.pdf")

    for era in eras:
        print(f"  {era.category}: {era.description} ({era.start_date})")

    if eras:
        # Test service mapping
        service_start = date(2016, 6, 1)
        service_end = date(2019, 12, 31)

        print(f"\nService period: {service_start} to {service_end}")
        for era in eras:
            mapping = map_to_service_period(era, service_start, service_end)
            print(f"  {era.description}: {mapping.mapping} (presumptive: {mapping.presumptive})")
```

---

## Testing

1. Run self-test: `python temporal_parser.py`
2. Test with sample medical records
3. Verify date parsing handles various formats
4. Test service period mapping logic
5. Integration test with VetAssist document upload

---

## For Seven Generations

Every veteran's scattered medical history becomes a clear timeline proving their service connection.

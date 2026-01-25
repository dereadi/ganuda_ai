# JR Instruction: VetAssist Phase 2 - Document Parsing Implementation

**Task ID:** VETASSIST-PHASE2-001
**Priority:** P0 - Council Priority
**Type:** implementation
**Assigned:** Software Engineer Jr.
**Depends On:** VETASSIST-DOCPARSE-001 (completed)

---

## Objective

Implement the document parsing functions: document classifier, OCR pipeline, DD-214 parser, and evidence tracker.

---

## Current State

Phase 1 created scaffolds in `/ganuda/vetassist/lib/`:
- `document_classifier.py` - DocumentType enum (working), classify_document() stub
- `ocr_pipeline.py` - Scaffold only
- `dd214_parser.py` - Scaffold only
- `evidence_tracker.py` - Scaffold only

---

## Deliverables

### 1. Update document_classifier.py

```python
#!/usr/bin/env python3
"""
VetAssist Document Classifier

Classifies uploaded documents by type for appropriate processing.

For Seven Generations - Cherokee AI Federation
"""

import re
from enum import Enum
from typing import Tuple

class DocumentType(Enum):
    DD214 = "dd214"
    MEDICAL_RECORD = "medical_record"
    BUDDY_STATEMENT = "buddy_statement"
    NEXUS_LETTER = "nexus_letter"
    SERVICE_RECORD = "service_record"
    PRESCRIPTION = "prescription"
    AUDIOGRAM = "audiogram"
    XRAY_REPORT = "xray_report"
    VA_DECISION = "va_decision"
    UNKNOWN = "unknown"

# Keyword patterns for classification
DOCUMENT_PATTERNS = {
    DocumentType.DD214: [
        r'certificate of release',
        r'dd\s*form\s*214',
        r'dd-214',
        r'separation\s+document',
        r'armed forces of the united states',
        r'discharge\s+or\s+release'
    ],
    DocumentType.NEXUS_LETTER: [
        r'nexus\s+letter',
        r'medical\s+nexus',
        r'more\s+likely\s+than\s+not',
        r'at\s+least\s+as\s+likely',
        r'service.connected',
        r'independent\s+medical\s+opinion'
    ],
    DocumentType.BUDDY_STATEMENT: [
        r'buddy\s+statement',
        r'lay\s+statement',
        r'witness\s+statement',
        r'personally\s+observed',
        r'i\s+served\s+with'
    ],
    DocumentType.AUDIOGRAM: [
        r'audiogram',
        r'hearing\s+test',
        r'pure\s+tone',
        r'speech\s+recognition',
        r'db\s+hl',
        r'threshold'
    ],
    DocumentType.PRESCRIPTION: [
        r'rx\s*:',
        r'prescription',
        r'refills?\s*:',
        r'sig\s*:',
        r'dispense',
        r'pharmacy'
    ],
    DocumentType.VA_DECISION: [
        r'rating\s+decision',
        r'department\s+of\s+veterans\s+affairs',
        r'service.connected\s+disability',
        r'effective\s+date',
        r'combined\s+evaluation'
    ],
    DocumentType.XRAY_REPORT: [
        r'x-ray',
        r'xray',
        r'radiograph',
        r'radiology\s+report',
        r'impression\s*:',
        r'findings\s*:'
    ],
    DocumentType.SERVICE_RECORD: [
        r'military\s+personnel\s+record',
        r'service\s+record',
        r'enlistment',
        r'promotion\s+orders',
        r'duty\s+station'
    ]
}

def classify_document(text: str, filename: str = "") -> Tuple[DocumentType, float]:
    """
    Classify uploaded document by content and filename.

    Args:
        text: Document text content
        filename: Original filename

    Returns:
        Tuple of (DocumentType, confidence_score)
    """
    text_lower = text.lower()
    filename_lower = filename.lower()

    scores = {}

    for doc_type, patterns in DOCUMENT_PATTERNS.items():
        score = 0
        for pattern in patterns:
            matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
            score += matches

        # Boost for filename hints
        type_name = doc_type.value.replace('_', '')
        if type_name in filename_lower.replace('_', '').replace('-', ''):
            score += 5

        if score > 0:
            scores[doc_type] = score

    if not scores:
        # Default to medical record if contains medical terms
        medical_terms = ['diagnosis', 'treatment', 'patient', 'symptoms', 'medication']
        if any(term in text_lower for term in medical_terms):
            return (DocumentType.MEDICAL_RECORD, 0.5)
        return (DocumentType.UNKNOWN, 0.0)

    # Return highest scoring type
    best_type = max(scores, key=scores.get)
    max_score = scores[best_type]

    # Normalize confidence (cap at 1.0)
    confidence = min(1.0, max_score / 10.0)

    return (best_type, confidence)


if __name__ == "__main__":
    # Test classification
    test_cases = [
        ("CERTIFICATE OF RELEASE OR DISCHARGE FROM ACTIVE DUTY DD FORM 214", "dd214.pdf"),
        ("The veteran's PTSD is more likely than not related to combat service", "nexus.pdf"),
        ("I served with SSG Smith and personally observed his hearing loss", "buddy.txt"),
        ("Pure tone audiogram results: 500Hz: 25dB, 1000Hz: 30dB", "hearing_test.pdf"),
    ]

    for text, filename in test_cases:
        doc_type, conf = classify_document(text, filename)
        print(f"{filename}: {doc_type.value} (confidence: {conf:.2f})")
```

### 2. Update ocr_pipeline.py

```python
#!/usr/bin/env python3
"""
VetAssist OCR Pipeline

Extracts text from scanned documents and images.

For Seven Generations - Cherokee AI Federation
"""

import os
import subprocess
from pathlib import Path
from typing import Optional

# Check for Tesseract
TESSERACT_AVAILABLE = subprocess.run(
    ['which', 'tesseract'],
    capture_output=True
).returncode == 0

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF using pdftotext or OCR fallback."""
    try:
        # Try pdftotext first (for text-based PDFs)
        result = subprocess.run(
            ['pdftotext', '-layout', file_path, '-'],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0 and result.stdout.strip():
            text = result.stdout
            # If we got meaningful text, return it
            if len(text.strip()) > 100:
                return text

        # Fall back to OCR for scanned PDFs
        return extract_text_with_ocr(file_path)

    except subprocess.TimeoutExpired:
        return "[Error: PDF extraction timed out]"
    except Exception as e:
        return f"[Error extracting PDF: {e}]"

def extract_text_with_ocr(file_path: str) -> str:
    """Extract text using Tesseract OCR."""
    if not TESSERACT_AVAILABLE:
        return "[Error: Tesseract OCR not installed]"

    try:
        # Convert PDF to images first if needed
        if file_path.lower().endswith('.pdf'):
            # Use pdftoppm to convert PDF to images
            import tempfile
            with tempfile.TemporaryDirectory() as tmpdir:
                # Convert PDF pages to images
                subprocess.run(
                    ['pdftoppm', '-png', file_path, f'{tmpdir}/page'],
                    check=True,
                    timeout=120
                )

                # OCR each page
                texts = []
                for img_file in sorted(Path(tmpdir).glob('*.png')):
                    result = subprocess.run(
                        ['tesseract', str(img_file), 'stdout'],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    if result.returncode == 0:
                        texts.append(result.stdout)

                return '\n\n--- Page Break ---\n\n'.join(texts)
        else:
            # Direct OCR for images
            result = subprocess.run(
                ['tesseract', file_path, 'stdout'],
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.stdout if result.returncode == 0 else f"[OCR Error: {result.stderr}]"

    except subprocess.TimeoutExpired:
        return "[Error: OCR timed out]"
    except Exception as e:
        return f"[Error in OCR: {e}]"

def extract_text(file_path: str) -> str:
    """
    Main entry point: Extract text from any supported document.

    Supports: PDF, PNG, JPG, JPEG, TIFF, BMP
    """
    if not os.path.exists(file_path):
        return f"[Error: File not found: {file_path}]"

    ext = Path(file_path).suffix.lower()

    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
        return extract_text_with_ocr(file_path)
    elif ext == '.txt':
        with open(file_path, 'r', errors='ignore') as f:
            return f.read()
    else:
        return f"[Error: Unsupported file type: {ext}]"


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        text = extract_text(sys.argv[1])
        print(f"Extracted {len(text)} characters")
        print(text[:500] + "..." if len(text) > 500 else text)
    else:
        print("Usage: python ocr_pipeline.py <file_path>")
```

### 3. Update dd214_parser.py

```python
#!/usr/bin/env python3
"""
VetAssist DD-214 Parser

Extracts structured data from DD-214 discharge documents.

For Seven Generations - Cherokee AI Federation
"""

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional

@dataclass
class DD214Info:
    """Structured DD-214 data."""
    service_member_name: str
    branch: str
    entry_date: Optional[date]
    separation_date: Optional[date]
    discharge_type: str
    mos_codes: List[str]
    decorations: List[str]
    combat_service: bool
    grade_rank: str
    total_active_service: str

def parse_date(text: str) -> Optional[date]:
    """Parse date from various DD-214 formats."""
    patterns = [
        (r'(\d{1,2})\s+(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+(\d{4})', '%d %b %Y'),
        (r'(\d{4})(\d{2})(\d{2})', '%Y%m%d'),
        (r'(\d{2})/(\d{2})/(\d{4})', '%m/%d/%Y'),
    ]

    for pattern, fmt in patterns:
        match = re.search(pattern, text.upper())
        if match:
            try:
                if fmt == '%Y%m%d':
                    return datetime.strptime(''.join(match.groups()), fmt).date()
                else:
                    return datetime.strptime(' '.join(match.groups()), fmt).date()
            except ValueError:
                continue
    return None

def extract_field(text: str, patterns: List[str]) -> str:
    """Extract field value using multiple patterns."""
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip()
    return ""

def parse_dd214(text: str) -> DD214Info:
    """
    Extract structured data from DD-214 text.

    Args:
        text: OCR or extracted text from DD-214

    Returns:
        DD214Info with extracted fields
    """
    text_upper = text.upper()

    # Extract name (Box 1)
    name = extract_field(text, [
        r'1\.\s*NAME[^:]*:\s*([A-Z\s,]+)',
        r'NAME\s*\(Last,\s*First,\s*Middle\)\s*:\s*([A-Z\s,]+)',
        r'^([A-Z]+,\s*[A-Z]+(?:\s+[A-Z])?)\s*$'
    ])

    # Extract branch (Box 4)
    branch = extract_field(text_upper, [
        r'BRANCH[:\s]+([A-Z\s]+?)(?:\n|$)',
        r'(ARMY|NAVY|MARINE CORPS|AIR FORCE|COAST GUARD|SPACE FORCE)'
    ])

    # Extract dates
    entry_match = re.search(r'DATE\s+ENTERED.*?(\d{1,2}\s+[A-Z]{3}\s+\d{4}|\d{8})', text_upper)
    sep_match = re.search(r'SEPARATION\s+DATE.*?(\d{1,2}\s+[A-Z]{3}\s+\d{4}|\d{8})', text_upper)

    entry_date = parse_date(entry_match.group(1)) if entry_match else None
    separation_date = parse_date(sep_match.group(1)) if sep_match else None

    # Discharge type (Box 24)
    discharge_patterns = [
        r'CHARACTER\s+OF\s+SERVICE[:\s]+([A-Z\s]+)',
        r'(HONORABLE|GENERAL|OTHER THAN HONORABLE|BAD CONDUCT|DISHONORABLE)'
    ]
    discharge_type = extract_field(text_upper, discharge_patterns) or "UNKNOWN"

    # MOS codes (Box 11)
    mos_matches = re.findall(r'(\d{2}[A-Z]\d{2}|\d{4})', text_upper)
    mos_codes = list(set(mos_matches))[:5]  # Limit to 5

    # Decorations (Box 13)
    decoration_section = re.search(r'DECORATIONS.*?(?=\d{2}\.|$)', text_upper, re.DOTALL)
    decorations = []
    if decoration_section:
        deco_text = decoration_section.group(0)
        # Common decorations
        for deco in ['PURPLE HEART', 'BRONZE STAR', 'COMBAT INFANTRY', 'COMBAT ACTION',
                     'ARMY COMMENDATION', 'NAVY COMMENDATION', 'GOOD CONDUCT']:
            if deco in deco_text:
                decorations.append(deco)

    # Combat service indicators
    combat_indicators = ['COMBAT', 'IMMINENT DANGER', 'HOSTILE FIRE', 'PURPLE HEART']
    combat_service = any(ind in text_upper for ind in combat_indicators)

    # Grade/Rank (Box 4a)
    grade_rank = extract_field(text_upper, [
        r'GRADE.*?RATE.*?:\s*([A-Z0-9\-]+)',
        r'(E-?\d|O-?\d|W-?\d|PVT|PFC|SPC|CPL|SGT|SSG|SFC|MSG|1SG|SGM|CSM|2LT|1LT|CPT|MAJ|LTC|COL)'
    ])

    # Total active service (Box 12)
    service_time = extract_field(text, [
        r'TOTAL\s+ACTIVE\s+SERVICE[:\s]+(\d+\s*YR[S]?\s*\d+\s*MO[S]?\s*\d+\s*DAY[S]?)',
        r'(\d+)\s*YEARS?\s*(\d+)\s*MONTHS?'
    ])

    return DD214Info(
        service_member_name=name,
        branch=branch,
        entry_date=entry_date,
        separation_date=separation_date,
        discharge_type=discharge_type,
        mos_codes=mos_codes,
        decorations=decorations,
        combat_service=combat_service,
        grade_rank=grade_rank,
        total_active_service=service_time
    )


if __name__ == "__main__":
    # Test with sample text
    sample = """
    CERTIFICATE OF RELEASE OR DISCHARGE FROM ACTIVE DUTY
    1. NAME: SMITH, JOHN MICHAEL
    4. GRADE, RATE OR RANK: SGT (E-5)
    BRANCH: ARMY
    DATE ENTERED ACTIVE DUTY: 15 JUN 2015
    SEPARATION DATE: 14 JUN 2019

    11. PRIMARY SPECIALTY: 11B30 INFANTRYMAN

    13. DECORATIONS: PURPLE HEART, COMBAT INFANTRY BADGE,
        ARMY COMMENDATION MEDAL, GOOD CONDUCT MEDAL

    24. CHARACTER OF SERVICE: HONORABLE
    """

    info = parse_dd214(sample)
    print(f"Name: {info.service_member_name}")
    print(f"Branch: {info.branch}")
    print(f"Service: {info.entry_date} to {info.separation_date}")
    print(f"Discharge: {info.discharge_type}")
    print(f"Combat: {info.combat_service}")
    print(f"Decorations: {info.decorations}")
```

### 4. Update evidence_tracker.py

```python
#!/usr/bin/env python3
"""
VetAssist Evidence Tracker

Tracks uploaded evidence and identifies gaps for claim completion.

For Seven Generations - Cherokee AI Federation
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Dict, Optional
from enum import Enum

from document_classifier import DocumentType

@dataclass
class EvidenceItem:
    """A piece of evidence for a claim."""
    document_type: DocumentType
    file_path: str
    upload_date: datetime
    extracted_dates: List[date] = field(default_factory=list)
    conditions_mentioned: List[str] = field(default_factory=list)
    service_connection_strength: float = 0.0  # 0.0-1.0
    in_service_events: bool = False

# Evidence requirements by condition category
EVIDENCE_REQUIREMENTS = {
    "ptsd": {
        "required": [DocumentType.MEDICAL_RECORD, DocumentType.DD214],
        "recommended": [DocumentType.BUDDY_STATEMENT, DocumentType.NEXUS_LETTER],
        "helpful": ["stressor statement", "combat records"]
    },
    "hearing_loss": {
        "required": [DocumentType.AUDIOGRAM, DocumentType.DD214],
        "recommended": [DocumentType.NEXUS_LETTER],
        "helpful": [DocumentType.BUDDY_STATEMENT, "noise exposure documentation"]
    },
    "tinnitus": {
        "required": [DocumentType.MEDICAL_RECORD, DocumentType.DD214],
        "recommended": [DocumentType.BUDDY_STATEMENT, DocumentType.AUDIOGRAM],
        "helpful": [DocumentType.NEXUS_LETTER]
    },
    "back_condition": {
        "required": [DocumentType.MEDICAL_RECORD, DocumentType.DD214],
        "recommended": [DocumentType.NEXUS_LETTER, DocumentType.XRAY_REPORT],
        "helpful": [DocumentType.BUDDY_STATEMENT, "physical therapy records"]
    },
    "tbi": {
        "required": [DocumentType.MEDICAL_RECORD, DocumentType.DD214],
        "recommended": [DocumentType.NEXUS_LETTER],
        "helpful": [DocumentType.BUDDY_STATEMENT, "incident reports", "combat records"]
    },
    "default": {
        "required": [DocumentType.MEDICAL_RECORD, DocumentType.DD214],
        "recommended": [DocumentType.NEXUS_LETTER],
        "helpful": [DocumentType.BUDDY_STATEMENT]
    }
}

def normalize_condition(condition: str) -> str:
    """Normalize condition name for lookup."""
    condition_lower = condition.lower().strip()

    # Map common variations
    mappings = {
        "post traumatic stress": "ptsd",
        "post-traumatic stress": "ptsd",
        "hearing": "hearing_loss",
        "tinnitus": "tinnitus",
        "back": "back_condition",
        "spine": "back_condition",
        "lumbar": "back_condition",
        "traumatic brain": "tbi",
    }

    for key, value in mappings.items():
        if key in condition_lower:
            return value

    return "default"

def analyze_evidence_gaps(
    claimed_conditions: List[str],
    evidence_items: List[EvidenceItem]
) -> Dict[str, Dict[str, List]]:
    """
    For each claimed condition, identify missing evidence.

    Args:
        claimed_conditions: List of conditions being claimed
        evidence_items: List of uploaded evidence

    Returns:
        Dict mapping condition to missing evidence by priority
    """
    # Get document types we have
    available_types = {item.document_type for item in evidence_items}

    gaps = {}

    for condition in claimed_conditions:
        normalized = normalize_condition(condition)
        requirements = EVIDENCE_REQUIREMENTS.get(normalized, EVIDENCE_REQUIREMENTS["default"])

        condition_gaps = {
            "missing_required": [],
            "missing_recommended": [],
            "missing_helpful": []
        }

        # Check required
        for req in requirements["required"]:
            if isinstance(req, DocumentType) and req not in available_types:
                condition_gaps["missing_required"].append(req.value)

        # Check recommended
        for req in requirements["recommended"]:
            if isinstance(req, DocumentType) and req not in available_types:
                condition_gaps["missing_recommended"].append(req.value)
            elif isinstance(req, str):
                condition_gaps["missing_recommended"].append(req)

        # Check helpful
        for req in requirements.get("helpful", []):
            if isinstance(req, DocumentType) and req not in available_types:
                condition_gaps["missing_helpful"].append(req.value)
            elif isinstance(req, str):
                condition_gaps["missing_helpful"].append(req)

        gaps[condition] = condition_gaps

    return gaps

def calculate_claim_strength(
    claimed_conditions: List[str],
    evidence_items: List[EvidenceItem]
) -> Dict[str, float]:
    """
    Calculate evidence strength score for each condition.

    Returns dict mapping condition to strength score (0.0-1.0)
    """
    gaps = analyze_evidence_gaps(claimed_conditions, evidence_items)

    strengths = {}
    for condition, condition_gaps in gaps.items():
        # Start at 1.0, subtract for missing evidence
        score = 1.0

        # Missing required: -0.3 each (max -0.6)
        required_penalty = min(0.6, len(condition_gaps["missing_required"]) * 0.3)
        score -= required_penalty

        # Missing recommended: -0.1 each (max -0.3)
        recommended_penalty = min(0.3, len(condition_gaps["missing_recommended"]) * 0.1)
        score -= recommended_penalty

        # Missing helpful: -0.05 each (max -0.1)
        helpful_penalty = min(0.1, len(condition_gaps["missing_helpful"]) * 0.05)
        score -= helpful_penalty

        strengths[condition] = max(0.0, score)

    return strengths


if __name__ == "__main__":
    # Test
    evidence = [
        EvidenceItem(DocumentType.DD214, "dd214.pdf", datetime.now()),
        EvidenceItem(DocumentType.MEDICAL_RECORD, "va_records.pdf", datetime.now()),
    ]

    conditions = ["PTSD", "Hearing Loss", "Tinnitus"]

    gaps = analyze_evidence_gaps(conditions, evidence)
    strengths = calculate_claim_strength(conditions, evidence)

    for cond in conditions:
        print(f"\n{cond}:")
        print(f"  Strength: {strengths[cond]:.0%}")
        print(f"  Missing Required: {gaps[cond]['missing_required']}")
        print(f"  Missing Recommended: {gaps[cond]['missing_recommended']}")
```

---

## Testing

1. Test document classifier with sample documents
2. Test OCR with scanned PDFs
3. Test DD-214 parser with sample DD-214
4. Test evidence tracker with sample claim

---

## For Seven Generations

A complete evidence picture helps every veteran get the benefits they earned.

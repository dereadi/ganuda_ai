# JR Instruction: VetAssist Integration Part 2 - Document Processor Service

**Task ID:** VETASSIST-INT-PROCESSOR-001
**Priority:** P1
**Type:** backend
**Assigned:** Software Engineer Jr.

---

## Objective

Create the DocumentProcessor service that integrates the Phase 2 parsing modules.

---

## Deliverable

Create this exact file:

File: `/ganuda/vetassist/backend/app/services/document_processor.py`

```python
#!/usr/bin/env python3
"""
VetAssist Document Processor Service

Integrates OCR, classification, and parsing modules for uploaded documents.

For Seven Generations - Cherokee AI Federation
"""

import sys
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add vetassist lib to path
sys.path.insert(0, '/ganuda/vetassist/lib')

from ocr_pipeline import extract_text
from document_classifier import classify_document, DocumentType
from dd214_parser import parse_dd214
from temporal_parser import extract_medical_eras
from evidence_tracker import analyze_evidence_gaps, calculate_claim_strength, EvidenceItem

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Processes uploaded documents through classification and parsing pipeline.
    """

    def process_document(self, file_path: str, mime_type: str) -> Dict[str, Any]:
        """
        Main entry point for document processing.

        Args:
            file_path: Path to uploaded file
            mime_type: MIME type of the file

        Returns:
            {
                'document_type': str,
                'confidence': float,
                'ocr_text': str,
                'parsed_data': dict,
                'status': 'completed' | 'error',
                'error': Optional[str]
            }
        """
        result = {
            'document_type': None,
            'confidence': 0.0,
            'ocr_text': None,
            'parsed_data': {},
            'status': 'processing',
            'error': None
        }

        try:
            # Step 1: Extract text (OCR if needed)
            logger.info(f"[DocProcessor] Extracting text from {file_path}")
            text = extract_text(file_path)

            if text.startswith('[Error'):
                result['status'] = 'error'
                result['error'] = text
                return result

            result['ocr_text'] = text

            # Step 2: Classify document
            logger.info(f"[DocProcessor] Classifying document ({len(text)} chars)")
            doc_type, confidence = classify_document(text)
            result['document_type'] = doc_type.value
            result['confidence'] = confidence

            # Step 3: Type-specific parsing
            if doc_type == DocumentType.DD214:
                logger.info("[DocProcessor] Parsing DD-214")
                dd214_info = parse_dd214(text)
                result['parsed_data'] = {
                    'service_member_name': dd214_info.service_member_name,
                    'branch': dd214_info.branch,
                    'entry_date': str(dd214_info.entry_date) if dd214_info.entry_date else None,
                    'separation_date': str(dd214_info.separation_date) if dd214_info.separation_date else None,
                    'discharge_type': dd214_info.discharge_type,
                    'mos_codes': dd214_info.mos_codes,
                    'decorations': dd214_info.decorations,
                    'combat_service': dd214_info.combat_service,
                    'grade_rank': dd214_info.grade_rank,
                    'total_active_service': dd214_info.total_active_service
                }

            elif doc_type == DocumentType.MEDICAL_RECORD:
                logger.info("[DocProcessor] Extracting medical timeline")
                eras = extract_medical_eras(text)
                result['parsed_data'] = {
                    'medical_events': [
                        {
                            'condition': era.condition,
                            'start_date': str(era.start_date) if era.start_date else None,
                            'end_date': str(era.end_date) if era.end_date else None,
                            'treatment': era.treatment,
                            'provider': era.provider
                        }
                        for era in eras
                    ]
                }

            result['status'] = 'completed'
            logger.info(f"[DocProcessor] Completed: {doc_type.value} ({confidence:.0%})")

        except Exception as e:
            logger.exception(f"[DocProcessor] Error: {e}")
            result['status'] = 'error'
            result['error'] = str(e)

        return result

    def get_evidence_analysis(
        self,
        claimed_conditions: List[str],
        uploaded_documents: List[Dict]
    ) -> Dict[str, Any]:
        """
        Analyze evidence gaps for claimed conditions.

        Args:
            claimed_conditions: List of conditions being claimed
            uploaded_documents: List of docs with document_type field

        Returns:
            {
                'gaps': {condition: {missing_required, missing_recommended, missing_helpful}},
                'claim_strength': {condition: float}
            }
        """
        # Convert to EvidenceItem objects
        evidence_items = []
        for doc in uploaded_documents:
            if doc.get('document_type'):
                try:
                    doc_type = DocumentType(doc['document_type'])
                    evidence_items.append(EvidenceItem(
                        document_type=doc_type,
                        file_path=doc.get('file_path', ''),
                        upload_date=datetime.now()
                    ))
                except ValueError:
                    pass

        gaps = analyze_evidence_gaps(claimed_conditions, evidence_items)
        strengths = calculate_claim_strength(claimed_conditions, evidence_items)

        return {
            'gaps': gaps,
            'claim_strength': strengths
        }


# Singleton instance
_processor = None

def get_processor() -> DocumentProcessor:
    """Get or create DocumentProcessor singleton."""
    global _processor
    if _processor is None:
        _processor = DocumentProcessor()
    return _processor
```

---

## Success Criteria

- File exists at `/ganuda/vetassist/backend/app/services/document_processor.py`
- Imports all Phase 2 modules correctly
- Both main methods implemented

---

## For Seven Generations

Unified document processing transforms chaos into clarity for veterans.

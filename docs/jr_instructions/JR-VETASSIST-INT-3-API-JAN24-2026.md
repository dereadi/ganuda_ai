# JR Instruction: VetAssist Integration Part 3 - Evidence API Endpoints

**Task ID:** VETASSIST-INT-API-001
**Priority:** P1
**Type:** backend
**Assigned:** Software Engineer Jr.

---

## Objective

Create FastAPI endpoints for evidence gap analysis and DD-214 data retrieval.

---

## Deliverable

Create this exact file:

File: `/ganuda/vetassist/backend/app/api/v1/endpoints/evidence.py`

```python
#!/usr/bin/env python3
"""
VetAssist Evidence API Endpoints

Provides evidence gap analysis and DD-214 data for claim wizard.

For Seven Generations - Cherokee AI Federation
"""

import json
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(tags=["evidence"])

# Database connection
def get_db_conn():
    return psycopg2.connect(
        host='goldfin.tail8df74e.ts.net',
        database='vetassist',
        user='vetassist_app',
        password='vetassist_secure_2026'
    )

# Import auth dependency
from .auth import get_current_user


class EvidenceGapResponse(BaseModel):
    condition: str
    missing_required: List[str]
    missing_recommended: List[str]
    missing_helpful: List[str]
    claim_strength: float


class DD214Summary(BaseModel):
    found: bool
    service_member_name: Optional[str] = None
    branch: Optional[str] = None
    entry_date: Optional[str] = None
    separation_date: Optional[str] = None
    discharge_type: Optional[str] = None
    combat_service: Optional[bool] = None
    decorations: Optional[List[str]] = None


@router.get("/sessions/{session_id}/evidence-gaps", response_model=List[EvidenceGapResponse])
def get_evidence_gaps(
    session_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Get evidence gap analysis for a wizard session.

    Returns list of conditions with missing evidence and claim strength.
    """
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get session and verify ownership
            cur.execute("""
                SELECT answers FROM vetassist_wizard_sessions
                WHERE session_id = %s AND veteran_id = %s
            """, (session_id, user_id))
            session = cur.fetchone()

            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

            # Get claimed conditions from answers
            answers = json.loads(session['answers'] or '{}')
            conditions = answers.get('conditions', [])

            if not conditions:
                return []

            # Get uploaded documents with their types
            cur.execute("""
                SELECT d.document_type
                FROM vetassist_documents d
                JOIN vetassist_wizard_files f ON d.id::text = f.file_id
                WHERE f.session_id = %s AND NOT f.deleted
                  AND d.document_type IS NOT NULL
            """, (session_id,))
            docs = cur.fetchall()

        # Import analysis functions
        import sys
        sys.path.insert(0, '/ganuda/vetassist/lib')
        from document_classifier import DocumentType
        from evidence_tracker import EvidenceItem, analyze_evidence_gaps, calculate_claim_strength

        # Build evidence items
        evidence_items = []
        for doc in docs:
            try:
                doc_type = DocumentType(doc['document_type'])
                evidence_items.append(EvidenceItem(
                    document_type=doc_type,
                    file_path='',
                    upload_date=datetime.now()
                ))
            except ValueError:
                pass

        # Analyze gaps
        gaps = analyze_evidence_gaps(conditions, evidence_items)
        strengths = calculate_claim_strength(conditions, evidence_items)

        # Format response
        return [
            EvidenceGapResponse(
                condition=cond,
                missing_required=gaps[cond]['missing_required'],
                missing_recommended=gaps[cond]['missing_recommended'],
                missing_helpful=gaps[cond]['missing_helpful'],
                claim_strength=strengths[cond]
            )
            for cond in conditions
        ]
    finally:
        conn.close()


@router.get("/sessions/{session_id}/dd214-summary", response_model=DD214Summary)
def get_dd214_summary(
    session_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Get parsed DD-214 data for auto-filling service dates.
    """
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Find DD-214 data for this session
            cur.execute("""
                SELECT dd.* FROM vetassist_dd214_data dd
                JOIN vetassist_documents d ON dd.document_id = d.id
                JOIN vetassist_wizard_files f ON d.id::text = f.file_id
                JOIN vetassist_wizard_sessions s ON f.session_id = s.session_id
                WHERE f.session_id = %s AND s.veteran_id = %s
                ORDER BY dd.created_at DESC
                LIMIT 1
            """, (session_id, user_id))
            dd214 = cur.fetchone()

            if not dd214:
                return DD214Summary(found=False)

            return DD214Summary(
                found=True,
                service_member_name=dd214.get('service_member_name'),
                branch=dd214.get('branch'),
                entry_date=str(dd214['entry_date']) if dd214.get('entry_date') else None,
                separation_date=str(dd214['separation_date']) if dd214.get('separation_date') else None,
                discharge_type=dd214.get('discharge_type'),
                combat_service=dd214.get('combat_service'),
                decorations=dd214.get('decorations', [])
            )
    finally:
        conn.close()


@router.get("/documents/{doc_id}/status")
def get_document_status(
    doc_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Get processing status for a document (for polling after upload).
    """
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT document_type, classification_confidence,
                       processing_status, processing_error
                FROM vetassist_documents
                WHERE id = %s
            """, (doc_id,))
            doc = cur.fetchone()

            if not doc:
                raise HTTPException(status_code=404, detail="Document not found")

            return {
                'document_type': doc['document_type'],
                'confidence': doc['classification_confidence'],
                'processing_status': doc['processing_status'],
                'error': doc['processing_error']
            }
    finally:
        conn.close()
```

---

## Success Criteria

- File exists at `/ganuda/vetassist/backend/app/api/v1/endpoints/evidence.py`
- Three endpoints implemented
- Pydantic models defined

---

## For Seven Generations

Clear API contracts enable frontend developers to build intuitive veteran experiences.

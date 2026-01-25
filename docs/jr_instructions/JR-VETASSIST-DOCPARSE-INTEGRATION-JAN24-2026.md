# JR Instruction: VetAssist Document Parsing Integration

**Task ID:** DOCPARSE-INTEGRATION-001
**Priority:** P1 - Sprint 3 Critical
**Type:** integration
**Assigned:** Software Engineer Jr.

---

## Overview

Integrate the Phase 2 document parsing modules with the VetAssist backend API. When a veteran uploads a document, the system should automatically:
1. Classify the document type (DD-214, medical record, buddy statement, etc.)
2. Extract text via OCR if scanned
3. Parse DD-214s for service dates
4. Run temporal extraction on medical records
5. Update evidence gap tracking
6. Return classification results to frontend

---

## Database Schema Changes

### 1. Alter vetassist_documents Table

```sql
-- Add classification and parsing fields
ALTER TABLE vetassist_documents
ADD COLUMN document_type VARCHAR(50),
ADD COLUMN classification_confidence FLOAT DEFAULT 0.0,
ADD COLUMN parsed_data JSONB DEFAULT '{}',
ADD COLUMN ocr_text TEXT,
ADD COLUMN processing_status VARCHAR(20) DEFAULT 'pending',
ADD COLUMN processing_error TEXT;

-- Index for filtering by type
CREATE INDEX idx_vetassist_docs_type ON vetassist_documents(document_type);
```

### 2. Create Evidence Gaps Table

```sql
CREATE TABLE vetassist_evidence_gaps (
    id SERIAL PRIMARY KEY,
    veteran_id VARCHAR(36) NOT NULL,
    session_id VARCHAR(36) NOT NULL,
    condition VARCHAR(100) NOT NULL,
    gap_type VARCHAR(20) NOT NULL, -- 'required', 'recommended', 'helpful'
    missing_evidence VARCHAR(100) NOT NULL,
    resolved_at TIMESTAMP,
    resolved_by_doc_id UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_evidence_gaps_veteran ON vetassist_evidence_gaps(veteran_id);
CREATE INDEX idx_evidence_gaps_session ON vetassist_evidence_gaps(session_id);
```

### 3. Create DD-214 Parsed Data Table

```sql
CREATE TABLE vetassist_dd214_data (
    id SERIAL PRIMARY KEY,
    document_id UUID REFERENCES vetassist_documents(id),
    veteran_id VARCHAR(36) NOT NULL,
    service_member_name VARCHAR(255),
    branch VARCHAR(50),
    entry_date DATE,
    separation_date DATE,
    discharge_type VARCHAR(100),
    mos_codes JSONB DEFAULT '[]',
    decorations JSONB DEFAULT '[]',
    combat_service BOOLEAN DEFAULT FALSE,
    grade_rank VARCHAR(50),
    total_active_service VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_dd214_document ON vetassist_dd214_data(document_id);
```

---

## Backend Changes

### 1. Update VetassistDocument Model

File: `/ganuda/vetassist/backend/app/models.py`

```python
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Float, Text
from sqlalchemy.dialects.postgresql import JSONB

class VetassistDocument(Base):
    __tablename__ = 'vetassist_documents'

    id = Column(PortableUUID(), primary_key=True, default=uuid4)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)

    # New classification fields
    document_type = Column(String(50), nullable=True)
    classification_confidence = Column(Float, default=0.0)
    parsed_data = Column(JSONB, default={})
    ocr_text = Column(Text, nullable=True)
    processing_status = Column(String(20), default='pending')
    processing_error = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, default=False)
```

### 2. Create Document Processing Service

File: `/ganuda/vetassist/backend/app/services/document_processor.py`

```python
import sys
sys.path.insert(0, '/ganuda/vetassist/lib')

from ocr_pipeline import extract_text
from document_classifier import classify_document, DocumentType
from dd214_parser import parse_dd214, DD214Info
from temporal_parser import extract_medical_eras, MedicalEra
from evidence_tracker import analyze_evidence_gaps, calculate_claim_strength, EvidenceItem

from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Processes uploaded documents through classification and parsing pipeline.
    """

    def process_document(self, file_path: str, mime_type: str) -> Dict[str, Any]:
        """
        Main entry point for document processing.

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
            logger.info(f"Extracting text from {file_path}")
            text = extract_text(file_path)

            if text.startswith('[Error'):
                result['status'] = 'error'
                result['error'] = text
                return result

            result['ocr_text'] = text

            # Step 2: Classify document
            logger.info(f"Classifying document ({len(text)} chars)")
            doc_type, confidence = classify_document(text)
            result['document_type'] = doc_type.value
            result['confidence'] = confidence

            # Step 3: Type-specific parsing
            if doc_type == DocumentType.DD214:
                logger.info("Parsing DD-214")
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
                logger.info("Extracting medical timeline")
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

        except Exception as e:
            logger.exception(f"Error processing document: {e}")
            result['status'] = 'error'
            result['error'] = str(e)

        return result

    def update_evidence_gaps(
        self,
        veteran_id: str,
        session_id: str,
        claimed_conditions: List[str],
        evidence_items: List[EvidenceItem]
    ) -> Dict[str, Dict]:
        """
        Analyze evidence gaps for claimed conditions.

        Returns gap analysis and claim strength scores.
        """
        gaps = analyze_evidence_gaps(claimed_conditions, evidence_items)
        strengths = calculate_claim_strength(claimed_conditions, evidence_items)

        return {
            'gaps': gaps,
            'claim_strength': strengths
        }
```

### 3. Update Upload Endpoint

File: `/ganuda/vetassist/backend/app/api/v1/endpoints/workbench_documents.py`

Add processing after upload:

```python
from app.services.document_processor import DocumentProcessor
from fastapi import BackgroundTasks

processor = DocumentProcessor()

@router.post("/workbench/projects/{project_id}/documents", response_model=DocumentResponse)
async def upload_document(
    project_id: int,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # ... existing upload logic ...

    # Queue background processing
    background_tasks.add_task(
        process_document_async,
        document.id,
        storage_path,
        file.content_type
    )

    return DocumentResponse(
        id=str(document.id),
        name=document.name,
        size=document.size,
        mime_type=document.mime_type,
        processing_status='pending'
    )

async def process_document_async(doc_id: str, file_path: str, mime_type: str):
    """Background task to process document."""
    result = processor.process_document(file_path, mime_type)

    # Update document in database
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE vetassist_documents
                SET document_type = %s,
                    classification_confidence = %s,
                    ocr_text = %s,
                    parsed_data = %s,
                    processing_status = %s,
                    processing_error = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (
                result['document_type'],
                result['confidence'],
                result['ocr_text'],
                json.dumps(result['parsed_data']),
                result['status'],
                result['error'],
                doc_id
            ))
            conn.commit()

            # If DD-214, store parsed data
            if result['document_type'] == 'dd214' and result['parsed_data']:
                store_dd214_data(cur, doc_id, result['parsed_data'])
                conn.commit()
    finally:
        conn.close()
```

### 4. Add Evidence Gap Endpoint

File: `/ganuda/vetassist/backend/app/api/v1/endpoints/evidence.py` (new file)

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel

router = APIRouter(tags=["evidence"])

class EvidenceGapResponse(BaseModel):
    condition: str
    missing_required: List[str]
    missing_recommended: List[str]
    missing_helpful: List[str]
    claim_strength: float

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
        # Get session and verify ownership
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
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

            # Get uploaded documents with their types
            cur.execute("""
                SELECT document_type, parsed_data
                FROM vetassist_documents d
                JOIN vetassist_wizard_files f ON d.id = f.document_id
                WHERE f.session_id = %s AND NOT f.deleted
            """, (session_id,))
            docs = cur.fetchall()

        # Build evidence items
        from document_classifier import DocumentType
        from evidence_tracker import EvidenceItem, analyze_evidence_gaps, calculate_claim_strength

        evidence_items = []
        for doc in docs:
            if doc['document_type']:
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


@router.get("/sessions/{session_id}/dd214-summary")
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
            cur.execute("""
                SELECT dd.* FROM vetassist_dd214_data dd
                JOIN vetassist_documents d ON dd.document_id = d.id
                JOIN vetassist_wizard_files f ON d.id = f.document_id
                WHERE f.session_id = %s
                ORDER BY dd.created_at DESC
                LIMIT 1
            """, (session_id,))
            dd214 = cur.fetchone()

            if not dd214:
                return {"found": False}

            return {
                "found": True,
                "service_member_name": dd214['service_member_name'],
                "branch": dd214['branch'],
                "entry_date": dd214['entry_date'],
                "separation_date": dd214['separation_date'],
                "discharge_type": dd214['discharge_type'],
                "combat_service": dd214['combat_service'],
                "decorations": dd214['decorations']
            }
    finally:
        conn.close()
```

---

## Frontend Changes

### 1. Update FileDropZone Component

File: `/ganuda/vetassist/frontend/components/dashboard/FileDropZone.tsx`

Add classification display:

```tsx
interface UploadedFile {
  id: string;
  name: string;
  size: number;
  documentType?: string;
  confidence?: number;
  processingStatus: 'pending' | 'processing' | 'completed' | 'error';
}

// Add polling for processing status
const pollProcessingStatus = async (fileId: string) => {
  const response = await fetch(`/api/v1/documents/${fileId}/status`);
  const data = await response.json();

  if (data.processingStatus === 'completed') {
    // Update file with classification
    setFiles(prev => prev.map(f =>
      f.id === fileId ? { ...f, ...data } : f
    ));
  } else if (data.processingStatus === 'processing' || data.processingStatus === 'pending') {
    // Poll again
    setTimeout(() => pollProcessingStatus(fileId), 2000);
  }
};

// Display classification badge
const getDocTypeBadge = (file: UploadedFile) => {
  if (!file.documentType) return null;

  const labels: Record<string, string> = {
    'dd214': 'DD-214',
    'medical_record': 'Medical Record',
    'buddy_statement': 'Buddy Statement',
    'nexus_letter': 'Nexus Letter',
    'audiogram': 'Audiogram'
  };

  return (
    <span className="doc-type-badge">
      {labels[file.documentType] || file.documentType}
      {file.confidence && ` (${(file.confidence * 100).toFixed(0)}%)`}
    </span>
  );
};
```

### 2. Add Evidence Gap Panel

File: `/ganuda/vetassist/frontend/components/wizard/EvidenceGapPanel.tsx` (new file)

```tsx
import React, { useEffect, useState } from 'react';

interface EvidenceGap {
  condition: string;
  missing_required: string[];
  missing_recommended: string[];
  missing_helpful: string[];
  claim_strength: number;
}

export const EvidenceGapPanel: React.FC<{ sessionId: string }> = ({ sessionId }) => {
  const [gaps, setGaps] = useState<EvidenceGap[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/v1/sessions/${sessionId}/evidence-gaps`)
      .then(res => res.json())
      .then(data => {
        setGaps(data);
        setLoading(false);
      });
  }, [sessionId]);

  if (loading) return <div>Analyzing evidence...</div>;

  return (
    <div className="evidence-gap-panel">
      <h3>Evidence Analysis</h3>
      {gaps.map(gap => (
        <div key={gap.condition} className="condition-card">
          <div className="condition-header">
            <span>{gap.condition}</span>
            <span className={`strength-badge strength-${Math.floor(gap.claim_strength * 10)}`}>
              {(gap.claim_strength * 100).toFixed(0)}% strength
            </span>
          </div>

          {gap.missing_required.length > 0 && (
            <div className="gap-section required">
              <h4>Required (Missing)</h4>
              <ul>
                {gap.missing_required.map(item => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {gap.missing_recommended.length > 0 && (
            <div className="gap-section recommended">
              <h4>Recommended</h4>
              <ul>
                {gap.missing_recommended.map(item => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};
```

---

## Testing

1. Upload a sample DD-214 PDF
2. Verify classification shows "DD-214"
3. Verify parsed fields (name, dates, branch) are extracted
4. Upload a medical record
5. Verify temporal events are extracted
6. Check evidence gap analysis updates

---

## Success Criteria

- [ ] Documents classified within 5 seconds of upload
- [ ] DD-214 service dates auto-populate wizard fields
- [ ] Evidence gaps display for each claimed condition
- [ ] Claim strength score calculated correctly
- [ ] OCR works for scanned documents
- [ ] Background processing doesn't block upload

---

## Dependencies

- Phase 2 modules in `/ganuda/vetassist/lib/`:
  - document_classifier.py
  - dd214_parser.py
  - temporal_parser.py
  - evidence_tracker.py
  - ocr_pipeline.py

---

## For Seven Generations

This integration transforms document chaos into organized evidence, helping veterans prove their service connection with clarity and confidence.

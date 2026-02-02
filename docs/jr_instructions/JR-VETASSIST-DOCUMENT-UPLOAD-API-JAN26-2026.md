# Jr Instruction: VetAssist Document Upload API

**Task ID:** To be assigned
**Jr Type:** Software Engineer Jr.
**Priority:** P1
**Estimated Complexity:** Medium

---

## Objective

Create FastAPI endpoints for document upload, processing status, and extraction results.

---

## Deliverables

1. Add to existing `/ganuda/vetassist/backend/main.py` or create router
2. Create `/ganuda/vetassist/backend/routers/documents.py`

---

## Requirements

### Endpoints

#### 1. Upload Document
```
POST /api/documents/upload
Content-Type: multipart/form-data

Request:
- file: binary (PDF, JPG, PNG, TIFF)
- document_type: string (optional, "dd214", "va_rating", "cp_exam", "medical", "auto")

Response (202 Accepted):
{
    "document_id": "uuid",
    "status": "queued",
    "filename": "original_name.pdf",
    "file_type": "application/pdf",
    "file_size": 1234567,
    "created_at": "2026-01-26T12:00:00Z"
}
```

#### 2. Get Processing Status
```
GET /api/documents/{document_id}/status

Response:
{
    "document_id": "uuid",
    "status": "queued|processing|ocr_complete|extracting|complete|error",
    "progress": 0-100,
    "current_stage": "string",
    "started_at": "timestamp",
    "completed_at": "timestamp|null",
    "error_message": "string|null"
}
```

#### 3. Get Extraction Results
```
GET /api/documents/{document_id}/extractions

Response:
{
    "document_id": "uuid",
    "document_type": "dd214",
    "extraction_confidence": 0.92,
    "service_info": {...},
    "conditions": [...],
    "dates": [...],
    "evidence_strength": {...},
    "ocr_confidence": 0.95,
    "pages_processed": 2,
    "requires_review": false,
    "review_flags": []
}
```

#### 4. Delete Document
```
DELETE /api/documents/{document_id}

Response (204 No Content)
```

---

## File Validation

```python
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".tif"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
```

---

## Database Schema

Add to existing vetassist schema or create:

```sql
CREATE TABLE veteran_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size INTEGER NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    document_type VARCHAR(50),
    status VARCHAR(50) DEFAULT 'queued',
    progress INTEGER DEFAULT 0,
    ocr_text TEXT,
    ocr_confidence FLOAT,
    extractions JSONB,
    extraction_confidence FLOAT,
    requires_review BOOLEAN DEFAULT false,
    review_flags JSONB DEFAULT '[]',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE INDEX idx_veteran_docs_user ON veteran_documents(user_id);
CREATE INDEX idx_veteran_docs_status ON veteran_documents(status);
```

---

## Processing Flow

```python
async def process_document(document_id: str):
    """Background task to process uploaded document."""
    # 1. Update status to "processing"
    # 2. Run OCR processor
    # 3. Update status to "ocr_complete"
    # 4. Run entity extractor
    # 5. Update status to "extracting"
    # 6. Save extractions
    # 7. Determine if review needed
    # 8. Update status to "complete"
```

Use FastAPI BackgroundTasks or existing queue system.

---

## Storage Path

Documents stored at: `/ganuda/vetassist/data/documents/{user_id}/{document_id}.{ext}`

Ensure directory exists before write.

---

## Integration Points

- Import and use `OCRProcessor` from `services/ocr_processor.py`
- Import and use `EntityExtractor` from `services/entity_extractor.py`
- Integrate with existing auth middleware for user_id

---

## Security

- Validate file magic bytes, not just extension
- Sanitize filenames
- Documents accessible only by owning user
- All access logged

---

## Do NOT

- Store documents without user association
- Skip file type validation
- Return full file paths in API responses

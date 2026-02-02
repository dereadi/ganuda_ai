# Jr Instruction: VetAssist Medical Record OCR with docling

**Date:** 2026-01-30
**Priority:** Tier 1 — High Impact
**Council Vote:** `23589699dd7b4a97` (confidence 0.873)
**Assigned To:** Software Engineer Jr.
**Depends On:** Existing document upload endpoints at `/api/documents/`

## Objective

Integrate IBM's `docling` library into VetAssist's document processing pipeline to extract structured content (tables, form fields, text) from uploaded medical records, DD-214s, and C&P exam reports.

## Background

- VetAssist currently accepts document uploads via `/api/documents/upload` but stores files without parsing content
- `docling` (MIT license, 50K GitHub stars) converts PDF/DOCX/images to markdown/JSON with table extraction
- LangChain integration available via `docling-langchain`

## Steps

### Step 1: Install docling in VetAssist backend virtual environment

```bash
cd /ganuda/vetassist/backend
source venv/bin/activate
pip install docling docling-langchain
pip freeze > requirements.txt
```

### Step 2: Create document processing service

**File to create:** `/ganuda/vetassist/backend/app/services/document_processor.py`

This service should:
1. Accept a file path to an uploaded document
2. Use `docling.DocumentConverter` to parse the document
3. Extract:
   - Full text content as markdown
   - Tables as structured data (list of dicts)
   - Form field key-value pairs
4. Return a dict with keys: `text_content`, `tables`, `form_fields`, `page_count`, `processing_time_ms`
5. Handle errors gracefully — return partial results if some pages fail
6. Log processing time with `[DOCLING]` prefix

Reference docling usage:
```python
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("path/to/document.pdf")
markdown = result.document.export_to_markdown()
```

### Step 3: Add document processing endpoint

**File to modify:** `/ganuda/vetassist/backend/app/api/endpoints/documents.py`

Add new endpoint:
```
POST /api/documents/{document_id}/process
```

This endpoint should:
1. Look up the document by ID in the database
2. Verify the file exists on disk
3. Call `document_processor.process()` with the file path
4. Store the extracted content in the `documents` table (add columns: `extracted_text`, `extracted_tables` jsonb, `processed_at` timestamp)
5. Return the processing result
6. Require authentication (existing auth middleware)

### Step 4: Add database migration for extracted content columns

**File to create:** `/ganuda/vetassist/backend/migrations/add_document_extraction_columns.sql`

```sql
ALTER TABLE documents ADD COLUMN IF NOT EXISTS extracted_text TEXT;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS extracted_tables JSONB DEFAULT '[]'::jsonb;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS extracted_form_fields JSONB DEFAULT '{}'::jsonb;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS page_count INTEGER;
```

### Step 5: Auto-process on upload

**File to modify:** `/ganuda/vetassist/backend/app/api/endpoints/documents.py`

Modify the existing `upload_document` endpoint to trigger processing automatically after upload. Use a background task so the upload response is fast:

```python
from fastapi import BackgroundTasks

@router.post("/upload")
async def upload_document(..., background_tasks: BackgroundTasks):
    # ... existing upload logic ...
    background_tasks.add_task(process_document_async, document_id)
    return {"id": document_id, "status": "uploaded", "processing": "queued"}
```

## Security Requirements (Crawdad)

- All document processing happens on-premise (no external API calls)
- PII in extracted text must go through existing Presidio pipeline before storage
- File type validation: only allow PDF, DOCX, PNG, JPG, TIFF
- Max file size: existing upload limit applies (10MB)

## Verification

1. Upload a sample PDF → check that `extracted_text` is populated in documents table
2. Upload a document with tables → verify `extracted_tables` has structured data
3. Upload a non-PDF → verify graceful error handling
4. Check logs for `[DOCLING]` processing time entries

## For Seven Generations

Better document understanding means veterans spend less time manually transcribing their medical records, reducing a key barrier in the disability claims process.

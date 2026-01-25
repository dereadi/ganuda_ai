# JR Instruction: VetAssist Integration Part 1 - Database Schema

**Task ID:** VETASSIST-INT-SCHEMA-001
**Priority:** P1
**Type:** database
**Assigned:** Software Engineer Jr.

---

## Objective

Create SQL migration file to add document classification fields to the vetassist_documents table.

---

## Deliverable

Create this exact file:

File: `/ganuda/vetassist/backend/migrations/001_add_classification_fields.sql`

```sql
-- VetAssist Document Classification Schema Extension
-- Part of Sprint 3 Document Parsing Integration

-- Add classification fields to existing vetassist_documents table
ALTER TABLE vetassist_documents
ADD COLUMN IF NOT EXISTS document_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS classification_confidence FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS parsed_data JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS ocr_text TEXT,
ADD COLUMN IF NOT EXISTS processing_status VARCHAR(20) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS processing_error TEXT;

-- Index for filtering by document type
CREATE INDEX IF NOT EXISTS idx_vetassist_docs_type
ON vetassist_documents(document_type);

-- Index for finding unprocessed documents
CREATE INDEX IF NOT EXISTS idx_vetassist_docs_status
ON vetassist_documents(processing_status);

-- Create evidence gaps tracking table
CREATE TABLE IF NOT EXISTS vetassist_evidence_gaps (
    id SERIAL PRIMARY KEY,
    veteran_id VARCHAR(36) NOT NULL,
    session_id VARCHAR(36) NOT NULL,
    condition VARCHAR(100) NOT NULL,
    gap_type VARCHAR(20) NOT NULL,
    missing_evidence VARCHAR(100) NOT NULL,
    resolved_at TIMESTAMP,
    resolved_by_doc_id UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evidence_gaps_veteran
ON vetassist_evidence_gaps(veteran_id);

CREATE INDEX IF NOT EXISTS idx_evidence_gaps_session
ON vetassist_evidence_gaps(session_id);

-- Create DD-214 parsed data table
CREATE TABLE IF NOT EXISTS vetassist_dd214_data (
    id SERIAL PRIMARY KEY,
    document_id UUID NOT NULL,
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

CREATE UNIQUE INDEX IF NOT EXISTS idx_dd214_document
ON vetassist_dd214_data(document_id);
```

---

## Success Criteria

- File exists at `/ganuda/vetassist/backend/migrations/001_add_classification_fields.sql`
- SQL syntax is valid
- All three tables/alterations included

---

## For Seven Generations

Structured data storage enables veterans to track their evidence systematically.

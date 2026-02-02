# JR Instruction: VetAssist RAG Schema Setup

**JR ID:** JR-RAG-001
**Priority:** P2
**Created:** 2026-01-27
**Author:** TPM via Claude Code
**Council Vote:** 31653da1507b46ec
**Assigned To:** Software Engineer Jr.
**Effort:** Low

## Problem Statement

VetAssist needs a RAG (Retrieval Augmented Generation) system for CFR retrieval. The pgvector extension is installed, but the schema doesn't exist. This blocks the SAC migration from JR-AI-006.

## Required Implementation

### 1. Database Migration

CREATE: `/ganuda/vetassist/backend/migrations/rag_schema.sql`

```sql
-- VetAssist RAG Schema
-- Council Approved: 2026-01-27 (Vote 31653da1507b46ec)
-- Prerequisites: pgvector extension (already installed)

-- Ensure pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Core RAG chunks table
CREATE TABLE IF NOT EXISTS vetassist_rag_chunks (
    id SERIAL PRIMARY KEY,

    -- Source document identification
    source_type VARCHAR(50) NOT NULL,      -- 'cfr', 'va_m21', 'bva_decision'
    source_id VARCHAR(100),                -- '38 CFR 4.71a', 'M21-1.III.iv.4.B'
    source_url TEXT,                       -- Original URL if applicable
    source_title VARCHAR(500),             -- Document/section title

    -- Chunk content
    content TEXT NOT NULL,
    content_hash VARCHAR(64),              -- SHA256 for deduplication
    chunk_index INT DEFAULT 0,             -- Position within source document

    -- CFR-specific metadata
    cfr_title INT,                         -- 38 for VA regulations
    cfr_part VARCHAR(20),                  -- '4', '3', etc.
    cfr_section VARCHAR(50),               -- '4.71a', '3.303', etc.
    cfr_subsection VARCHAR(100),           -- Diagnostic code or subsection

    -- Effective dates (for regulation versioning)
    effective_date DATE,
    superseded_date DATE,

    -- Vector embeddings (MiniLM-L6-v2 = 384 dimensions)
    embedding VECTOR(384),

    -- SAC (Summary Augmented Chunking) columns
    summary TEXT,
    summary_embedding VECTOR(384),
    summary_generated_at TIMESTAMP,
    sac_status VARCHAR(20) DEFAULT 'pending',

    -- Processing metadata
    token_count INT,
    processed_at TIMESTAMP,
    processed_by VARCHAR(100),             -- Which model/pipeline

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for efficient retrieval
-- Vector similarity search (IVFFlat for large datasets)
CREATE INDEX IF NOT EXISTS idx_rag_embedding ON vetassist_rag_chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_rag_summary_embedding ON vetassist_rag_chunks
    USING ivfflat (summary_embedding vector_cosine_ops)
    WITH (lists = 100);

-- Standard indexes
CREATE INDEX IF NOT EXISTS idx_rag_source_type ON vetassist_rag_chunks(source_type);
CREATE INDEX IF NOT EXISTS idx_rag_source_id ON vetassist_rag_chunks(source_id);
CREATE INDEX IF NOT EXISTS idx_rag_cfr_section ON vetassist_rag_chunks(cfr_section);
CREATE INDEX IF NOT EXISTS idx_rag_content_hash ON vetassist_rag_chunks(content_hash);
CREATE INDEX IF NOT EXISTS idx_rag_sac_status ON vetassist_rag_chunks(sac_status);

-- Comments
COMMENT ON TABLE vetassist_rag_chunks IS 'RAG chunks for VetAssist CFR and VA regulation retrieval. Council approved 2026-01-27.';
COMMENT ON COLUMN vetassist_rag_chunks.embedding IS 'MiniLM-L6-v2 embedding (384 dimensions)';
COMMENT ON COLUMN vetassist_rag_chunks.sac_status IS 'SAC processing: pending, processing, complete, error';

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_rag_chunk_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for auto-updating timestamp
DROP TRIGGER IF EXISTS rag_chunk_updated ON vetassist_rag_chunks;
CREATE TRIGGER rag_chunk_updated
    BEFORE UPDATE ON vetassist_rag_chunks
    FOR EACH ROW
    EXECUTE FUNCTION update_rag_chunk_timestamp();
```

### 2. Run Migration

```bash
cd /ganuda/vetassist/backend
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production \
    -f migrations/rag_schema.sql
```

## Verification

```bash
# 1. Verify table exists
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
\\d vetassist_rag_chunks"

# 2. Verify indexes
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'vetassist_rag_chunks';"

# 3. Test vector insert
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
INSERT INTO vetassist_rag_chunks (source_type, source_id, content, cfr_section, embedding)
VALUES ('cfr', '38 CFR 4.71a', 'Test chunk for PTSD rating criteria', '4.71a',
        (SELECT array_agg(random())::vector(384) FROM generate_series(1, 384)))
RETURNING id, source_id;"

# 4. Test vector search
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT id, source_id,
       embedding <=> (SELECT embedding FROM vetassist_rag_chunks WHERE id = 1) as distance
FROM vetassist_rag_chunks
ORDER BY distance
LIMIT 5;"
```

---

FOR SEVEN GENERATIONS

# JR Instruction: A-MEM Medical Entities Schema

**Task ID:** JR-AMEM-MEDICAL-SCHEMA-001
**Priority:** P0 (Phase 0 - Foundation)
**Type:** database
**Assigned:** Infrastructure Jr.
**Estimated Complexity:** Low

---

## Objective

Create the database schema for storing LLMD-style medical entities in the vetassist_pii database. This prepares the foundation for medical entity extraction without deploying any new models yet.

**Philosophy:** Build the house before moving in the furniture.

---

## Context

When we add medical entity extraction (Phase 1), we need somewhere to store:
- Extracted medical conditions, medications, procedures
- Temporal information (dates, durations)
- Links to source documents
- Service connection chains

This schema prepares that storage.

---

## Database Target

**Host:** 192.168.132.222 (bluefin)
**Database:** vetassist_pii
**User:** claude

---

## Schema Definition

```sql
-- Medical Entity Types Enum
CREATE TYPE medical_entity_type AS ENUM (
    'CONDITION',       -- Diagnosis, symptom, disease
    'MEDICATION',      -- Drug name, dosage, frequency
    'PROCEDURE',       -- Surgery, treatment, therapy
    'DATE',            -- Service date, onset date, diagnosis date
    'BODY_PART',       -- Anatomical reference
    'PROVIDER',        -- Doctor, facility, VA center
    'MILITARY_EVENT',  -- Deployment, combat, injury event
    'LAB_RESULT',      -- Test result, vital sign
    'DISABILITY_RATING' -- Existing VA rating reference
);

-- Main Medical Entities Table
CREATE TABLE IF NOT EXISTS medical_entities (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    session_id UUID,  -- VetAssist session if applicable

    -- Entity details
    entity_type medical_entity_type NOT NULL,
    entity_text VARCHAR(500) NOT NULL,  -- Original text span
    normalized_text VARCHAR(500),       -- Standardized form (ICD-10, RxNorm, etc.)
    confidence FLOAT DEFAULT 1.0,       -- Extraction confidence (0-1)

    -- Position in document
    start_offset INTEGER,
    end_offset INTEGER,
    page_number INTEGER,

    -- Temporal information
    entity_date DATE,                   -- If entity has associated date
    date_precision VARCHAR(20),         -- 'exact', 'month', 'year', 'approximate'

    -- Service connection relevance
    service_connection_relevant BOOLEAN DEFAULT FALSE,
    military_service_period VARCHAR(100),  -- e.g., "2003-2007 Iraq"

    -- Linking
    linked_entity_id INTEGER REFERENCES medical_entities(id),
    link_type VARCHAR(50),              -- 'causes', 'treats', 'aggravates', 'during'

    -- A-MEM integration
    amem_memory_id INTEGER,             -- Link to A-MEM memory if created
    temperature_score FLOAT DEFAULT 50.0,

    -- Audit
    extracted_by VARCHAR(100) DEFAULT 'llmd_hybrid',
    extraction_model VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Service Connection Timeline Table
CREATE TABLE IF NOT EXISTS service_connection_timeline (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL,
    veteran_id INTEGER,

    -- Timeline metadata
    timeline_name VARCHAR(200),
    condition_claimed VARCHAR(500),     -- The condition being claimed
    service_period_start DATE,
    service_period_end DATE,

    -- Timeline events (JSON array for flexibility)
    events JSONB DEFAULT '[]'::jsonb,
    /*
    Event structure:
    {
        "date": "2005-03-15",
        "type": "military_event|diagnosis|treatment|aggravation",
        "description": "...",
        "entity_ids": [1, 2, 3],
        "confidence": 0.85
    }
    */

    -- Analysis results
    nexus_strength FLOAT,               -- 0-1 strength of service connection
    gap_analysis JSONB,                 -- Missing evidence identified
    recommendation TEXT,

    -- Council review
    council_reviewed BOOLEAN DEFAULT FALSE,
    council_confidence FLOAT,
    council_verdict VARCHAR(50),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_medical_entities_document ON medical_entities(document_id);
CREATE INDEX IF NOT EXISTS idx_medical_entities_session ON medical_entities(session_id);
CREATE INDEX IF NOT EXISTS idx_medical_entities_type ON medical_entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_medical_entities_date ON medical_entities(entity_date);
CREATE INDEX IF NOT EXISTS idx_medical_entities_service_relevant ON medical_entities(service_connection_relevant) WHERE service_connection_relevant = TRUE;

CREATE INDEX IF NOT EXISTS idx_timeline_session ON service_connection_timeline(session_id);
CREATE INDEX IF NOT EXISTS idx_timeline_condition ON service_connection_timeline(condition_claimed);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_medical_entities_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER medical_entities_update_timestamp
    BEFORE UPDATE ON medical_entities
    FOR EACH ROW
    EXECUTE FUNCTION update_medical_entities_timestamp();

CREATE TRIGGER timeline_update_timestamp
    BEFORE UPDATE ON service_connection_timeline
    FOR EACH ROW
    EXECUTE FUNCTION update_medical_entities_timestamp();

-- Comments for documentation
COMMENT ON TABLE medical_entities IS 'LLMD-style medical entity extraction results for VetAssist documents';
COMMENT ON TABLE service_connection_timeline IS 'Temporal chains linking military service to medical conditions';
COMMENT ON COLUMN medical_entities.normalized_text IS 'Standardized terminology (ICD-10, RxNorm, SNOMED) when available';
COMMENT ON COLUMN medical_entities.confidence IS 'Extraction confidence from LLMD hybrid model (0-1)';
COMMENT ON COLUMN service_connection_timeline.nexus_strength IS 'Computed strength of service connection evidence (0-1)';
```

---

## Execution

### On bluefin (192.168.132.222):

```bash
psql -h localhost -U claude -d vetassist_pii -f /ganuda/sql/medical_entities_schema.sql
```

### Or via Python:

```python
import psycopg2

conn = psycopg2.connect(
    host='192.168.132.222',
    database='vetassist_pii',
    user='claude',
    password='jawaseatlasers2'
)

with open('/ganuda/sql/medical_entities_schema.sql', 'r') as f:
    sql = f.read()

with conn.cursor() as cur:
    cur.execute(sql)
    conn.commit()

conn.close()
print("Schema created successfully")
```

---

## Verification

```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('medical_entities', 'service_connection_timeline');

-- Check enum type
SELECT enumlabel FROM pg_enum
WHERE enumtypid = 'medical_entity_type'::regtype;

-- Check indexes
SELECT indexname FROM pg_indexes
WHERE tablename IN ('medical_entities', 'service_connection_timeline');
```

---

## Success Criteria

- [ ] medical_entity_type enum created
- [ ] medical_entities table created with all columns
- [ ] service_connection_timeline table created
- [ ] All indexes created
- [ ] Triggers for updated_at working
- [ ] No errors in execution

---

## Deliverables

1. SQL file at `/ganuda/sql/medical_entities_schema.sql`
2. Schema deployed to vetassist_pii database
3. Verification queries pass

---

## Notes

- This schema supports LLMD-style extraction but doesn't require LLMD model
- We can populate manually or with Qwen prompting before full LLMD integration
- confidence field will be crucial for AUQ integration
- Temperature score links to A-MEM thermal memory system

---

## For Seven Generations

This schema will hold the medical histories of veterans and their families. Design it with respect - every row represents someone's health journey and their service to our nation.

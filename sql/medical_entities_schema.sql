-- Medical Entities Schema for VetAssist
-- Part of LLMD+AUQ Cautious Enhancement Integration
-- Created: 2026-01-25

-- Medical Entity Types Enum (safe creation)
DO $$ BEGIN
    CREATE TYPE medical_entity_type AS ENUM (
        'CONDITION',
        'MEDICATION',
        'PROCEDURE',
        'DATE',
        'BODY_PART',
        'PROVIDER',
        'MILITARY_EVENT',
        'LAB_RESULT',
        'DISABILITY_RATING'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Main Medical Entities Table
CREATE TABLE IF NOT EXISTS medical_entities (
    id SERIAL PRIMARY KEY,
    document_id INTEGER,  -- Optional reference to documents table
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
-- Migration: Thermal Relationships Phase 1
-- Council Approved: 2291748d1afc2ca9
-- Date: January 22, 2026

BEGIN;

-- Core relationships table
CREATE TABLE IF NOT EXISTS thermal_relationships (
    id SERIAL PRIMARY KEY,
    
    -- Source can be a memory OR another relationship
    source_memory_id INT REFERENCES thermal_memory_archive(id) ON DELETE CASCADE,
    source_relationship_id INT REFERENCES thermal_relationships(id) ON DELETE CASCADE,
    
    -- Relationship type (near, inside, caused_by, learned_from, if_then, etc.)
    relationship_type VARCHAR(50) NOT NULL,
    
    -- Target can be a memory OR another relationship  
    target_memory_id INT REFERENCES thermal_memory_archive(id) ON DELETE CASCADE,
    target_relationship_id INT REFERENCES thermal_relationships(id) ON DELETE CASCADE,
    
    -- Confidence and provenance
    confidence FLOAT DEFAULT 1.0 CHECK (confidence >= 0 AND confidence <= 1),
    provenance VARCHAR(100),
    
    -- Temporal validity
    valid_from TIMESTAMP DEFAULT NOW(),
    valid_until TIMESTAMP,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Ensure at least one source and one target
    CONSTRAINT valid_source CHECK (
        source_memory_id IS NOT NULL OR source_relationship_id IS NOT NULL
    ),
    CONSTRAINT valid_target CHECK (
        target_memory_id IS NOT NULL OR target_relationship_id IS NOT NULL
    )
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_thermal_rel_source_memory ON thermal_relationships(source_memory_id);
CREATE INDEX IF NOT EXISTS idx_thermal_rel_target_memory ON thermal_relationships(target_memory_id);
CREATE INDEX IF NOT EXISTS idx_thermal_rel_source_rel ON thermal_relationships(source_relationship_id);
CREATE INDEX IF NOT EXISTS idx_thermal_rel_target_rel ON thermal_relationships(target_relationship_id);
CREATE INDEX IF NOT EXISTS idx_thermal_rel_type ON thermal_relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_thermal_rel_valid ON thermal_relationships(valid_from, valid_until);
CREATE INDEX IF NOT EXISTS idx_thermal_rel_provenance ON thermal_relationships(provenance);

-- View for active relationships
CREATE OR REPLACE VIEW active_thermal_relationships AS
SELECT * FROM thermal_relationships
WHERE valid_until IS NULL OR valid_until > NOW();

-- Function to create a relationship
CREATE OR REPLACE FUNCTION create_thermal_relationship(
    p_source_memory_id INT DEFAULT NULL,
    p_source_relationship_id INT DEFAULT NULL,
    p_relationship_type VARCHAR(50) DEFAULT 'related_to',
    p_target_memory_id INT DEFAULT NULL,
    p_target_relationship_id INT DEFAULT NULL,
    p_confidence FLOAT DEFAULT 1.0,
    p_provenance VARCHAR(100) DEFAULT 'user',
    p_metadata JSONB DEFAULT '{}'
) RETURNS INT AS $$
DECLARE
    new_id INT;
BEGIN
    INSERT INTO thermal_relationships (
        source_memory_id, source_relationship_id,
        relationship_type,
        target_memory_id, target_relationship_id,
        confidence, provenance, metadata
    ) VALUES (
        p_source_memory_id, p_source_relationship_id,
        p_relationship_type,
        p_target_memory_id, p_target_relationship_id,
        p_confidence, p_provenance, p_metadata
    ) RETURNING id INTO new_id;
    
    RETURN new_id;
END;
$$ LANGUAGE plpgsql;

-- Function to invalidate a relationship (soft delete)
CREATE OR REPLACE FUNCTION invalidate_thermal_relationship(p_id INT)
RETURNS VOID AS $$
BEGIN
    UPDATE thermal_relationships 
    SET valid_until = NOW()
    WHERE id = p_id AND valid_until IS NULL;
END;
$$ LANGUAGE plpgsql;

COMMIT;

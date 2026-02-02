-- Migration: Thermal Clauses Phase 2
-- Part of Relationships-as-Things implementation
-- Date: January 22, 2026

BEGIN;

-- Clauses table - relates multiple relationships with logic
CREATE TABLE IF NOT EXISTS thermal_clauses (
    id SERIAL PRIMARY KEY,
    
    -- Clause type: if_then, and, or, not, when, unless
    clause_type VARCHAR(20) NOT NULL,
    
    -- Human-readable name for the clause
    name VARCHAR(255),
    
    -- Description of what this clause does
    description TEXT,
    
    -- Condition relationships (evaluated for truth)
    condition_relationship_ids INT[],
    
    -- Action relationships (activated when conditions met)
    action_relationship_ids INT[],
    
    -- For nested clauses
    parent_clause_id INT REFERENCES thermal_clauses(id),
    child_clause_ids INT[],
    
    -- Evaluation state
    last_evaluated TIMESTAMP,
    evaluation_result BOOLEAN,
    evaluation_context JSONB DEFAULT '{}',
    
    -- Activation settings
    is_active BOOLEAN DEFAULT true,
    priority INT DEFAULT 5,
    
    -- Temporal validity
    valid_from TIMESTAMP DEFAULT NOW(),
    valid_until TIMESTAMP,
    
    -- Metadata
    provenance VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_thermal_clauses_type ON thermal_clauses(clause_type);
CREATE INDEX IF NOT EXISTS idx_thermal_clauses_active ON thermal_clauses(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_thermal_clauses_parent ON thermal_clauses(parent_clause_id);
CREATE INDEX IF NOT EXISTS idx_thermal_clauses_priority ON thermal_clauses(priority);
CREATE INDEX IF NOT EXISTS idx_thermal_clauses_conditions ON thermal_clauses USING GIN(condition_relationship_ids);
CREATE INDEX IF NOT EXISTS idx_thermal_clauses_actions ON thermal_clauses USING GIN(action_relationship_ids);

-- View for active clauses
CREATE OR REPLACE VIEW active_thermal_clauses AS
SELECT * FROM thermal_clauses
WHERE is_active = true 
  AND (valid_until IS NULL OR valid_until > NOW());

-- Function to create an IF-THEN clause
CREATE OR REPLACE FUNCTION create_if_then_clause(
    p_name VARCHAR(255),
    p_condition_ids INT[],
    p_action_ids INT[],
    p_description TEXT DEFAULT NULL,
    p_provenance VARCHAR(100) DEFAULT 'user'
) RETURNS INT AS $$
DECLARE
    new_id INT;
BEGIN
    INSERT INTO thermal_clauses (
        clause_type, name, description,
        condition_relationship_ids, action_relationship_ids,
        provenance
    ) VALUES (
        'if_then', p_name, p_description,
        p_condition_ids, p_action_ids,
        p_provenance
    ) RETURNING id INTO new_id;
    
    RETURN new_id;
END;
$$ LANGUAGE plpgsql;

-- Function to evaluate a clause
CREATE OR REPLACE FUNCTION evaluate_clause(p_clause_id INT)
RETURNS BOOLEAN AS $$
DECLARE
    v_clause thermal_clauses%ROWTYPE;
    v_condition_met BOOLEAN := true;
    v_rel_id INT;
BEGIN
    SELECT * INTO v_clause FROM thermal_clauses WHERE id = p_clause_id;
    
    IF v_clause.clause_type = 'if_then' THEN
        FOREACH v_rel_id IN ARRAY v_clause.condition_relationship_ids
        LOOP
            IF NOT EXISTS (
                SELECT 1 FROM active_thermal_relationships 
                WHERE id = v_rel_id
            ) THEN
                v_condition_met := false;
                EXIT;
            END IF;
        END LOOP;
    END IF;
    
    UPDATE thermal_clauses 
    SET last_evaluated = NOW(),
        evaluation_result = v_condition_met,
        updated_at = NOW()
    WHERE id = p_clause_id;
    
    RETURN v_condition_met;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update timestamp
CREATE OR REPLACE FUNCTION update_thermal_clauses_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS thermal_clauses_update_timestamp ON thermal_clauses;
CREATE TRIGGER thermal_clauses_update_timestamp
    BEFORE UPDATE ON thermal_clauses
    FOR EACH ROW
    EXECUTE FUNCTION update_thermal_clauses_timestamp();

COMMIT;

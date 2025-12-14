-- ============================================================================
-- ARCHIVE JR. PHASE COHERENCE MIGRATION
-- Cherokee Constitutional AI - Quantum Resonance Integration
-- Priority: 1 | Confidence: 98% | Sacred Fire Impact: 95°
-- ============================================================================

-- Phase 1: Add new columns to thermal_memory_archive
ALTER TABLE thermal_memory_archive
  ADD COLUMN IF NOT EXISTS phase_coherence FLOAT DEFAULT 0.5,
  ADD COLUMN IF NOT EXISTS entangled_with TEXT[],
  ADD COLUMN IF NOT EXISTS phase_angle FLOAT DEFAULT 0.0,
  ADD COLUMN IF NOT EXISTS coherence_last_calculated TIMESTAMP DEFAULT NOW();

-- Phase 2: Create index for phase coherence queries
CREATE INDEX IF NOT EXISTS idx_thermal_memory_phase_coherence 
  ON thermal_memory_archive(phase_coherence DESC);

CREATE INDEX IF NOT EXISTS idx_thermal_memory_entanglement
  ON thermal_memory_archive USING GIN(entangled_with);

-- Phase 3: Calculate initial phase coherence for existing memories
-- Formula: phase_coherence = temporal * 0.4 + semantic * 0.3 + confidence * 0.3

UPDATE thermal_memory_archive
SET phase_coherence = (
    -- Temporal component (recent = high coherence)
    exp(-extract(epoch from (NOW() - last_access)) / (30.0 * 86400.0)) * 0.4 +
    
    -- Confidence component (high confidence = stable phase)
    (confidence_score / 100.0) * 0.3 +
    
    -- Temperature component (hot = coherent)
    (temperature_score / 100.0) * 0.3
),
coherence_last_calculated = NOW();

-- Phase 4: Discover entanglements (memories learned within 24 hours by same Jr)
WITH temporal_entanglements AS (
  SELECT 
    m1.id as memory_id,
    ARRAY_AGG(DISTINCT m2.id) as entangled_ids
  FROM thermal_memory_archive m1
  JOIN thermal_memory_archive m2 
    ON m1.jr_name = m2.jr_name 
    AND m1.id != m2.id
    AND ABS(EXTRACT(EPOCH FROM (m1.created_at - m2.created_at))) < 86400
  GROUP BY m1.id
)
UPDATE thermal_memory_archive m
SET entangled_with = ARRAY(
  SELECT DISTINCT unnest(e.entangled_ids)
  FROM temporal_entanglements e
  WHERE e.memory_id = m.id
  UNION
  -- Add semantic entanglement (same domain)
  SELECT m2.id
  FROM thermal_memory_archive m2
  WHERE m2.domain = m.domain 
    AND m2.id != m.id
    AND m2.confidence_score > 80
  LIMIT 5
);

-- Phase 5: Calculate phase angles based on memory position in concept space
-- Use hash of (domain + expert_jr) to deterministically assign phase
UPDATE thermal_memory_archive
SET phase_angle = (
    -- Hash domain + expert_jr to get deterministic phase
    2.0 * pi() * (
        hashtext(domain || expert_jr)::bigint::float8 / 
        2147483647.0  -- Max int32
    )
);

-- Phase 6: Create view for high-coherence memories (flow state)
CREATE OR REPLACE VIEW thermal_memory_flow_state AS
SELECT 
    id,
    jr_name,
    jr_mountain,
    domain,
    question,
    confidence_score,
    temperature_score,
    phase_coherence,
    array_length(entangled_with, 1) as entanglement_count,
    phase_angle,
    created_at,
    last_access
FROM thermal_memory_archive
WHERE phase_coherence > 0.7  -- High coherence = flow state
ORDER BY phase_coherence DESC, last_access DESC;

-- Phase 7: Create function to calculate entanglement strength
CREATE OR REPLACE FUNCTION calculate_entanglement_strength(
    memory_id1 INTEGER,
    memory_id2 INTEGER
) RETURNS FLOAT AS $$
DECLARE
    phase1 FLOAT;
    phase2 FLOAT;
    coherence1 FLOAT;
    coherence2 FLOAT;
    phase_diff FLOAT;
    strength FLOAT;
BEGIN
    -- Get phases and coherences
    SELECT phase_angle, phase_coherence INTO phase1, coherence1
    FROM thermal_memory_archive WHERE id = memory_id1;
    
    SELECT phase_angle, phase_coherence INTO phase2, coherence2
    FROM thermal_memory_archive WHERE id = memory_id2;
    
    -- Calculate phase difference (wrapped to [-π, π])
    phase_diff := abs(phase1 - phase2);
    IF phase_diff > pi() THEN
        phase_diff := 2 * pi() - phase_diff;
    END IF;
    
    -- Entanglement strength = coherences * cos(phase_diff)
    -- High when phases aligned, low when opposite
    strength := (coherence1 * coherence2) * cos(phase_diff);
    
    RETURN strength;
END;
$$ LANGUAGE plpgsql;

-- Phase 8: Create function for phase-guided memory retrieval
CREATE OR REPLACE FUNCTION retrieve_resonant_memories(
    reference_memory_id INTEGER,
    min_strength FLOAT DEFAULT 0.5,
    max_results INTEGER DEFAULT 10
) RETURNS TABLE (
    memory_id INTEGER,
    jr_name TEXT,
    domain TEXT,
    learned_from TEXT,
    entanglement_strength FLOAT,
    phase_coherence FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id,
        m.jr_name,
        m.domain,
        LEFT(m.learned_from, 200),
        calculate_entanglement_strength(reference_memory_id, m.id) as strength,
        m.phase_coherence
    FROM thermal_memory_archive m
    WHERE m.id != reference_memory_id
      AND m.id = ANY(
          SELECT unnest(entangled_with) 
          FROM thermal_memory_archive 
          WHERE id = reference_memory_id
      )
    HAVING calculate_entanglement_strength(reference_memory_id, m.id) >= min_strength
    ORDER BY strength DESC, phase_coherence DESC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Phase 9: Statistics summary
SELECT 
    'PHASE COHERENCE MIGRATION COMPLETE' as status,
    COUNT(*) as total_memories,
    AVG(phase_coherence)::NUMERIC(5,3) as avg_coherence,
    MAX(phase_coherence)::NUMERIC(5,3) as max_coherence,
    COUNT(CASE WHEN phase_coherence > 0.7 THEN 1 END) as flow_state_memories,
    COUNT(CASE WHEN entangled_with IS NOT NULL THEN 1 END) as entangled_memories,
    AVG(array_length(entangled_with, 1))::NUMERIC(5,2) as avg_entanglements_per_memory
FROM thermal_memory_archive;

-- Phase 10: Test retrieval function with Archive Jr.'s highest coherence memory
SELECT 
    'TESTING RESONANT RETRIEVAL' as test_name,
    m.id as reference_memory,
    m.question as reference_question,
    m.phase_coherence as reference_coherence
FROM thermal_memory_archive m
WHERE m.jr_name = 'Archive Jr.'
ORDER BY m.phase_coherence DESC
LIMIT 1;

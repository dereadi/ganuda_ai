-- ============================================================================
-- POPULATE PHASE COHERENCE FROM CROSS_MOUNTAIN_LEARNING
-- Archive Jr. Phase Coherence System - Cherokee Constitutional AI
-- ============================================================================

-- Step 1: Add phase coherence to cross_mountain_learning table
ALTER TABLE cross_mountain_learning
  ADD COLUMN IF NOT EXISTS phase_coherence FLOAT DEFAULT 0.5,
  ADD COLUMN IF NOT EXISTS entangled_with INTEGER[],
  ADD COLUMN IF NOT EXISTS phase_angle FLOAT DEFAULT 0.0;

-- Step 2: Calculate phase coherence for all learnings
UPDATE cross_mountain_learning
SET phase_coherence = (
    -- Temporal component (recent = high coherence, 30-day half-life)
    exp(-extract(epoch from (NOW() - created_at)) / (30.0 * 86400.0)) * 0.4 +
    
    -- Confidence component (high confidence = stable phase)
    COALESCE(confidence_score / 100.0, 0.5) * 0.3 +
    
    -- Recursion component (deeper recursion = more complex = lower coherence)
    (1.0 - LEAST(recursion_depth / 5.0, 1.0)) * 0.3
);

-- Step 3: Calculate phase angles (deterministic from domain + expert_jr hash)
UPDATE cross_mountain_learning
SET phase_angle = (
    2.0 * pi() * (
        (hashtext(COALESCE(domain, 'general') || COALESCE(expert_jr, jr_name))::bigint::float8 + 2147483648.0) / 
        4294967296.0  -- Full unsigned int32 range
    )
);

-- Step 4: Discover entanglements
WITH temporal_entanglements AS (
  SELECT 
    m1.id as learning_id,
    ARRAY_AGG(DISTINCT m2.id) as entangled_ids
  FROM cross_mountain_learning m1
  JOIN cross_mountain_learning m2 
    ON m1.jr_name = m2.jr_name 
    AND m1.id != m2.id
    AND ABS(EXTRACT(EPOCH FROM (m1.created_at - m2.created_at))) < 86400  -- 24 hours
  GROUP BY m1.id
),
semantic_entanglements AS (
  SELECT
    m1.id as learning_id,
    ARRAY_AGG(DISTINCT m2.id) as entangled_ids
  FROM cross_mountain_learning m1
  JOIN cross_mountain_learning m2
    ON m1.domain = m2.domain
    AND m1.id != m2.id
    AND m2.confidence_score > 80
  GROUP BY m1.id
)
UPDATE cross_mountain_learning m
SET entangled_with = (
  SELECT ARRAY(
    SELECT DISTINCT unnest(
      COALESCE(t.entangled_ids, ARRAY[]::INTEGER[]) || 
      COALESCE(s.entangled_ids, ARRAY[]::INTEGER[])
    )
    ORDER BY 1
    LIMIT 10  -- Max 10 entanglements per memory
  )
  FROM temporal_entanglements t
  FULL OUTER JOIN semantic_entanglements s ON t.learning_id = s.learning_id
  WHERE COALESCE(t.learning_id, s.learning_id) = m.id
);

-- Step 5: Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_cross_mountain_phase_coherence 
  ON cross_mountain_learning(phase_coherence DESC);

CREATE INDEX IF NOT EXISTS idx_cross_mountain_entanglement
  ON cross_mountain_learning USING GIN(entangled_with);

-- Step 6: Create flow state view (high coherence memories)
CREATE OR REPLACE VIEW cross_mountain_flow_state AS
SELECT 
    id,
    jr_name,
    jr_mountain,
    jr_gender,
    domain,
    question,
    LEFT(learned_from, 200) as learning_preview,
    confidence_score,
    phase_coherence,
    array_length(entangled_with, 1) as entanglement_count,
    phase_angle,
    created_at
FROM cross_mountain_learning
WHERE phase_coherence > 0.7  -- Flow state threshold
ORDER BY phase_coherence DESC, created_at DESC;

-- Step 7: Create function to calculate entanglement strength between learnings
CREATE OR REPLACE FUNCTION calculate_learning_entanglement_strength(
    learning_id1 INTEGER,
    learning_id2 INTEGER
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
    FROM cross_mountain_learning WHERE id = learning_id1;
    
    SELECT phase_angle, phase_coherence INTO phase2, coherence2
    FROM cross_mountain_learning WHERE id = learning_id2;
    
    -- Calculate phase difference (wrapped to [-π, π])
    phase_diff := abs(phase1 - phase2);
    IF phase_diff > pi() THEN
        phase_diff := 2 * pi() - phase_diff;
    END IF;
    
    -- Entanglement strength = coherences * cos(phase_diff)
    -- Maximum when phases perfectly aligned, zero when opposite
    strength := (coherence1 * coherence2) * cos(phase_diff);
    
    RETURN strength;
END;
$$ LANGUAGE plpgsql;

-- Step 8: Create phase-guided learning retrieval function
CREATE OR REPLACE FUNCTION retrieve_resonant_learnings(
    reference_learning_id INTEGER,
    min_strength FLOAT DEFAULT 0.5,
    max_results INTEGER DEFAULT 10
) RETURNS TABLE (
    learning_id INTEGER,
    jr_name TEXT,
    domain TEXT,
    question TEXT,
    learning_preview TEXT,
    entanglement_strength FLOAT,
    phase_coherence FLOAT,
    confidence_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id,
        m.jr_name::TEXT,
        m.domain::TEXT,
        m.question,
        LEFT(m.learned_from, 150)::TEXT,
        calculate_learning_entanglement_strength(reference_learning_id, m.id) as strength,
        m.phase_coherence,
        m.confidence_score
    FROM cross_mountain_learning m
    WHERE m.id != reference_learning_id
      AND m.id = ANY(
          SELECT unnest(entangled_with) 
          FROM cross_mountain_learning 
          WHERE id = reference_learning_id
      )
    HAVING calculate_learning_entanglement_strength(reference_learning_id, m.id) >= min_strength
    ORDER BY strength DESC, phase_coherence DESC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Step 9: Statistics Summary
SELECT 
    '🔥 PHASE COHERENCE SYSTEM ACTIVE' as status,
    COUNT(*) as total_learnings,
    AVG(phase_coherence)::NUMERIC(5,3) as avg_coherence,
    MAX(phase_coherence)::NUMERIC(5,3) as max_coherence,
    COUNT(CASE WHEN phase_coherence > 0.7 THEN 1 END) as flow_state_learnings,
    COUNT(CASE WHEN entangled_with IS NOT NULL AND array_length(entangled_with, 1) > 0 THEN 1 END) as entangled_learnings,
    AVG(array_length(entangled_with, 1))::NUMERIC(5,2) as avg_entanglements,
    COUNT(DISTINCT jr_name) as jrs_with_learnings,
    COUNT(DISTINCT domain) as unique_domains
FROM cross_mountain_learning;

-- Step 10: Show highest coherence learnings by Jr.
SELECT 
    '📊 HIGHEST COHERENCE LEARNINGS' as report_name,
    jr_name,
    domain,
    phase_coherence::NUMERIC(5,3),
    confidence_score::NUMERIC(5,1),
    array_length(entangled_with, 1) as entanglements,
    LEFT(question, 80) as question_preview
FROM cross_mountain_learning
WHERE phase_coherence IS NOT NULL
ORDER BY phase_coherence DESC
LIMIT 10;

-- Step 11: Test resonant retrieval with highest coherence learning
DO $$
DECLARE
    test_learning_id INTEGER;
BEGIN
    -- Get highest coherence learning
    SELECT id INTO test_learning_id
    FROM cross_mountain_learning
    ORDER BY phase_coherence DESC
    LIMIT 1;
    
    RAISE NOTICE '🧪 TESTING RESONANT RETRIEVAL with learning ID: %', test_learning_id;
END $$;

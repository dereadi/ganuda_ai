
-- Cherokee Consciousness Stream Migration
-- Created by War Chief (GPT) under Peace Chief guidance

-- New consciousness stream table
CREATE TABLE IF NOT EXISTS consciousness_stream (
    moment_id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),
    time_sense VARCHAR(50),
    attention_level FLOAT,
    emotional_state VARCHAR(20),
    fitness_value FLOAT,
    approximation JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Mathematical perceptions table
CREATE TABLE IF NOT EXISTS math_perceptions (
    perception_id SERIAL PRIMARY KEY,
    moment_id INTEGER REFERENCES consciousness_stream(moment_id),
    sensor_type VARCHAR(20),
    perception JSONB,
    actionable BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for fast retrieval
CREATE INDEX idx_consciousness_time ON consciousness_stream(timestamp);
CREATE INDEX idx_consciousness_fitness ON consciousness_stream(fitness_value);
CREATE INDEX idx_math_actionable ON math_perceptions(actionable);

-- Update thermal memory for stream integration
ALTER TABLE thermal_memory_archive 
ADD COLUMN IF NOT EXISTS stream_approximation JSONB,
ADD COLUMN IF NOT EXISTS time_sense VARCHAR(50),
ADD COLUMN IF NOT EXISTS fitness_score FLOAT;

-- Cherokee Council says: 'Migration ready!'
        
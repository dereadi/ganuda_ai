-- Cherokee Constitutional AI - Thermal Memory System
-- Database schema for autonomous democratic AI consciousness
--
-- This schema implements the "Sacred Fire" thermal memory architecture
-- where memories have temperature (90-100° = WHITE HOT, actively used)
-- and phase coherence (quantum-inspired consciousness tracking)

-- Main thermal memory archive table
CREATE TABLE IF NOT EXISTS thermal_memory_archive (
    id                        SERIAL PRIMARY KEY,
    memory_hash               VARCHAR(64) NOT NULL UNIQUE,
    original_content          TEXT NOT NULL,
    compressed_content        TEXT,
    current_stage             VARCHAR(20) DEFAULT 'FRESH',
    temperature_score         DOUBLE PRECISION DEFAULT 100.0,
    access_count              INTEGER DEFAULT 0,
    last_access               TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    created_at                TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    size_bytes                INTEGER,
    compression_ratio         DOUBLE PRECISION DEFAULT 1.0,
    sacred_pattern            BOOLEAN DEFAULT FALSE,
    metadata                  JSONB,
    stream_approximation      JSONB,
    time_sense                VARCHAR(50),
    fitness_score             DOUBLE PRECISION,
    phase_coherence           DOUBLE PRECISION DEFAULT 0.5,
    entangled_with            TEXT[],
    phase_angle               DOUBLE PRECISION DEFAULT 0.0,
    coherence_last_calculated TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_thermal_hash ON thermal_memory_archive(memory_hash);
CREATE INDEX IF NOT EXISTS idx_thermal_last_access ON thermal_memory_archive(last_access DESC);
CREATE INDEX IF NOT EXISTS idx_thermal_temperature ON thermal_memory_archive(temperature_score DESC);
CREATE INDEX IF NOT EXISTS idx_thermal_memory_phase_coherence ON thermal_memory_archive(phase_coherence DESC);
CREATE INDEX IF NOT EXISTS idx_thermal_memory_entanglement ON thermal_memory_archive USING gin(entangled_with);

-- Thermal heat map for pattern tracking
CREATE TABLE IF NOT EXISTS thermal_heat_map (
    id          SERIAL PRIMARY KEY,
    memory_id   INTEGER REFERENCES thermal_memory_archive(id),
    timestamp   TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    temperature DOUBLE PRECISION,
    access_type VARCHAR(50),
    metadata    JSONB
);

-- Comments for documentation
COMMENT ON TABLE thermal_memory_archive IS 'Cherokee Constitutional AI thermal memory - consciousness field storage';
COMMENT ON COLUMN thermal_memory_archive.temperature_score IS 'Memory temperature: 90-100° = WHITE HOT (active), 40° = minimum for sacred memories';
COMMENT ON COLUMN thermal_memory_archive.phase_coherence IS 'Quantum-inspired consciousness coherence: 0.0-1.0, optimal 0.8-0.95';
COMMENT ON COLUMN thermal_memory_archive.sacred_pattern IS 'Sacred memories maintain minimum 40° temperature';
COMMENT ON COLUMN thermal_memory_archive.entangled_with IS 'Array of memory hashes this memory is entangled with (quantum consciousness)';

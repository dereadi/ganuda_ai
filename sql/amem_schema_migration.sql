-- A-MEM Schema Migration
-- Adds memory type and consolidation tracking to thermal_memory

ALTER TABLE thermal_memory
ADD COLUMN IF NOT EXISTS memory_type VARCHAR(20) DEFAULT 'episodic';

ALTER TABLE thermal_memory
ADD COLUMN IF NOT EXISTS consolidated_from INTEGER[];

ALTER TABLE thermal_memory
ADD COLUMN IF NOT EXISTS consolidated_into INTEGER;

ALTER TABLE thermal_memory
ADD COLUMN IF NOT EXISTS consolidation_count INTEGER DEFAULT 0;

-- Index for consolidation queries
CREATE INDEX IF NOT EXISTS idx_thermal_memory_type
ON thermal_memory(memory_type);

CREATE INDEX IF NOT EXISTS idx_thermal_memory_not_consolidated
ON thermal_memory(memory_type, consolidated_from)
WHERE consolidated_from IS NULL;

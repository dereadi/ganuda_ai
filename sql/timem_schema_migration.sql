
-- TiMem Schema Migration for thermal_memory_archive
-- Cherokee AI Federation - January 2026

BEGIN;

-- Add Temporal Memory Tree columns
ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS parent_memory_id INTEGER REFERENCES thermal_memory_archive(memory_id),
ADD COLUMN IF NOT EXISTS stage INTEGER,
ADD COLUMN IF NOT EXISTS consolidated BOOLEAN DEFAULT FALSE;

-- Create index on parent_memory_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_parent_memory_id ON thermal_memory_archive(parent_memory_id);

COMMIT;


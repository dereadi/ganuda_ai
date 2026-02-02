-- VetAssist Scratchpads Table Migration
-- JR: JR-VETASSIST-SCRATCHPAD-SAVE-FIX-JAN27-2026
-- Date: 2026-01-27
-- Cherokee AI Federation - For Seven Generations

-- Create scratchpads table if not exists
CREATE TABLE IF NOT EXISTS vetassist_scratchpads (
    id SERIAL PRIMARY KEY,
    veteran_id VARCHAR(128) NOT NULL UNIQUE,
    content TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create index on veteran_id for fast lookups
CREATE INDEX IF NOT EXISTS idx_vetassist_scratchpads_veteran_id
ON vetassist_scratchpads(veteran_id);

-- Add comment for documentation
COMMENT ON TABLE vetassist_scratchpads IS 'VetAssist user scratchpad/notes storage - auto-saved from frontend';

-- Alter table to add updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to update updated_at column on row update
CREATE TRIGGER update_vetassist_scratchpads_updated_at
BEFORE UPDATE ON vetassist_scratchpads
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Verify creation
SELECT 'vetassist_scratchpads table ready' AS status;
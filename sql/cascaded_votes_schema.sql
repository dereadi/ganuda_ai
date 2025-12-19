-- Cascaded Council Vote Schema Updates
-- December 17, 2025

-- Add cascaded vote tracking columns to council_votes
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS vote_mode VARCHAR(20) DEFAULT 'parallel';
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS stages_completed INTEGER;
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS blocked_by VARCHAR(50);
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS blocked_at_stage INTEGER;
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS grpo_rankings JSONB;

-- Index for mode-based queries
CREATE INDEX IF NOT EXISTS idx_council_votes_mode ON council_votes(vote_mode);
CREATE INDEX IF NOT EXISTS idx_council_votes_blocked ON council_votes(blocked_by) WHERE blocked_by IS NOT NULL;

-- Add comment
COMMENT ON COLUMN council_votes.vote_mode IS 'parallel (default) or cascaded';
COMMENT ON COLUMN council_votes.stages_completed IS 'Number of cascade stages completed (1-5)';
COMMENT ON COLUMN council_votes.blocked_by IS 'Specialist that blocked the request (if any)';

SELECT 'Cascaded vote schema updates applied' as result;
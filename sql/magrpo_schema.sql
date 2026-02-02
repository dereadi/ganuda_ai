-- MAGRPO Multi-Agent Cooperation Schema
-- Cherokee AI Federation - For Seven Generations
-- Created: January 27, 2026

-- Track Jr participation in tasks
CREATE TABLE IF NOT EXISTS magrpo_task_participation (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(64) NOT NULL,
    jr_type VARCHAR(50) NOT NULL,
    joined_at TIMESTAMP DEFAULT NOW(),
    contribution_score FLOAT,
    handoff_from VARCHAR(50),
    handoff_to VARCHAR(50),
    context_preserved_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Unique constraint to prevent duplicate registrations
CREATE UNIQUE INDEX IF NOT EXISTS idx_magrpo_participation_unique
ON magrpo_task_participation(task_id, jr_type, joined_at);

-- Index for fast task lookups
CREATE INDEX IF NOT EXISTS idx_magrpo_task_id
ON magrpo_task_participation(task_id);

-- Index for Jr stats queries
CREATE INDEX IF NOT EXISTS idx_magrpo_jr_type
ON magrpo_task_participation(jr_type, joined_at);

-- Aggregated cooperation metrics (computed periodically)
CREATE TABLE IF NOT EXISTS magrpo_cooperation_metrics (
    id SERIAL PRIMARY KEY,
    jr_type VARCHAR(50) NOT NULL,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    tasks_participated INT DEFAULT 0,
    handoffs_sent INT DEFAULT 0,
    handoffs_received INT DEFAULT 0,
    avg_context_preservation FLOAT,
    cooperation_score FLOAT,
    group_reward_total FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Unique constraint for period aggregation
CREATE UNIQUE INDEX IF NOT EXISTS idx_magrpo_metrics_unique
ON magrpo_cooperation_metrics(jr_type, period_start);

-- Comments for documentation
COMMENT ON TABLE magrpo_task_participation IS 'MAGRPO: Tracks Jr participation in multi-agent tasks';
COMMENT ON TABLE magrpo_cooperation_metrics IS 'MAGRPO: Aggregated cooperation statistics by Jr';

-- Verify creation
SELECT 'MAGRPO schema created successfully' AS status;
